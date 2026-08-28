"""Initialise and sync an AQRP source checkout.

`repo` runs on the host, not in the container: it needs the developer's SSH agent and
git credentials to reach the internal manifest remote.

Manifest URL, default branch, and **groups** all come from the variant table. The last
matters: checkout-source.sh hardcoded the qnx8 group set
(`integration,embedded,platform-linux`), which would have synced the wrong projects for
qnx7, whose set is `qnx,platform-linux`.
"""

import os
import subprocess
from pathlib import Path

from . import log
from .errors import PreflightError, WorkspaceError
from .workspace import Registry, Workspace, VARIANTS, detect_branch


def preflight():
    from shutil import which
    if which("repo") is None:
        raise PreflightError("the repo tool is not available in PATH")


def _run(argv, cwd):
    log.action("{}  (in {})".format(" ".join(argv), cwd))
    if log.dry_run():
        return
    result = subprocess.run(argv, cwd=str(cwd), check=False)
    if result.returncode != 0:
        raise WorkspaceError(
            "{} failed with exit status {}".format(argv[0], result.returncode))


def checkout(name, path=None, variant=None, branch=None, jobs=None):
    """Init + sync a checkout, registering it on success.

    Two entry shapes, because a workspace can already be registered and its tree gone
    (a deleted checkout being restored):

      * unregistered name -> path and variant are required; registered on success
      * registered name   -> path and variant come from the registry
    """
    registry = Registry.load()
    existing = None
    if name in registry.names():
        existing = registry.get(name)
        if path and Path(os.path.expanduser(path)) != existing.path:
            raise WorkspaceError(
                "workspace {!r} is already registered at {}; pass a different name or "
                "remove it first".format(name, existing.path))
        if variant and variant != existing.sw_variant:
            raise WorkspaceError(
                "workspace {!r} is registered as {}, not {}".format(
                    name, existing.sw_variant, variant))
        workspace = existing
    else:
        if not path or not variant:
            raise WorkspaceError(
                "{!r} is not registered: pass --path DIR and --variant {{{}}}".format(
                    name, "|".join(sorted(VARIANTS))))
        workspace = Workspace(name, path, variant)

    branch = branch or workspace.default_branch
    destination = workspace.path

    log.step("checkout {} ({})".format(name, workspace.sw_variant))
    log.say("Manifest:    {}".format(workspace.manifest_url))
    log.say("Branch:      {}".format(branch))
    log.say("Groups:      {}".format(workspace.groups))
    log.say("Destination: {}".format(destination))

    if not log.dry_run():
        destination.mkdir(parents=True, exist_ok=True)

    _run(["repo", "init", "-u", workspace.manifest_url, "-b", branch,
          "-g", workspace.groups], cwd=destination)

    sync = ["repo", "sync", "-c"]
    if jobs:
        sync += ["-j", str(jobs)]
    _run(sync, cwd=destination)

    if log.dry_run():
        log.ok("dry run complete; nothing was checked out")
        return 0

    # Register only on success, so every record describes a real tree -- the invariant
    # the hard-refuse mismatch policy depends on.
    workspace.validate()
    if existing is None:
        registry.add(workspace)
        registry.save()
        log.ok("registered {} -> {}".format(name, destination))
    else:
        log.ok("refreshed {} -> {}".format(name, destination))
    log.ok("branch on disk: {}".format(detect_branch(destination)))
    return 0
