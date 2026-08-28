"""The OE devenv Docker container that BitBake runs inside.

One container per workspace, named `aqrp-<workspace>`. Ported from build-aqrp.sh, whose
hard-won requirements are preserved deliberately:

  * `--init` is mandatory. Without an init process to reap them, orphaned BitBake
    children accumulate as zombies until the container is unusable. A container found
    without it is refused rather than silently reused.
  * The image is checked on reuse. A container built from a different image would
    produce confusing failures deep inside a build.
  * $HOME is bind-mounted whole, so every checkout under it is visible; --workdir is
    set per exec rather than baked in.
"""

import getpass
import grp
import os
import subprocess
from pathlib import Path

from . import log
from .errors import PreflightError, WorkspaceError
from .workspace import DOCKER_IMAGE


def _docker(args, **kwargs):
    try:
        return subprocess.run(["docker"] + args, **kwargs)
    except FileNotFoundError:
        raise PreflightError("docker is not available in PATH")


def _inspect(name, fmt):
    result = _docker(
        ["container", "inspect", "--format", fmt, name],
        check=False, capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def preflight():
    result = _docker(["info"], check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise PreflightError("cannot communicate with the Docker daemon")


def _env_args():
    return [
        "--user", "{}:{}".format(os.getuid(), os.getgid()),
        "--env", "HOME={}".format(Path.home()),
        "--env", "USER_NAME={}".format(getpass.getuser()),
        "--env", "GROUP_NAME={}".format(grp.getgrgid(os.getgid()).gr_name),
    ]


def ensure(workspace):
    """Create, restart, or reuse the workspace's container. Returns its name."""
    name = workspace.container

    if log.dry_run():
        log.action("ensure container {} ({})".format(name, DOCKER_IMAGE))
        return name

    image = _inspect(name, "{{.Config.Image}}")
    if image is None:
        log.action("create container {} from {}".format(name, DOCKER_IMAGE))
        _docker([
            "run", "--detach", "--init", "--name", name,
        ] + _env_args() + [
            "--volume", "{h}:{h}".format(h=Path.home()),
            "--volume", "/srv:/srv",
            "--workdir", str(workspace.path),
            DOCKER_IMAGE, "sleep", "infinity",
        ], check=True, capture_output=True, text=True)
    else:
        if image != DOCKER_IMAGE:
            raise WorkspaceError(
                "container {} uses image {}, expected {}.\n"
                "Remove it (docker rm -f {}) or rename the workspace.".format(
                    name, image, DOCKER_IMAGE, name)
            )
        if _inspect(name, "{{json .HostConfig.Init}}") != "true":
            raise WorkspaceError(
                "container {} was created without Docker --init.\n"
                "Without an init process, orphaned BitBake children accumulate as "
                "zombies. Recreate it:\n  docker rm -f {}".format(name, name)
            )
        if _inspect(name, "{{.State.Running}}") == "true":
            log.say("Reusing running container: {}".format(name))
        else:
            log.action("start container {}".format(name))
            _docker(["start", name], check=True, capture_output=True, text=True)

    if _inspect(name, "{{.State.Running}}") != "true":
        raise WorkspaceError("container {} did not remain running".format(name))
    return name


def run_script(workspace, script, script_args=(), workdir=None, check=True):
    """Run a bash script inside the workspace's container.

    Yocto's environment scripts are not nounset-safe, so callers use `set -Ee -o
    pipefail` rather than `set -u`.
    """
    name = ensure(workspace)
    workdir = str(workdir or workspace.path)
    argv = (
        ["exec"] + _env_args() + ["--workdir", workdir, name,
         "bash", "-c", script, "bash"] + [str(a) for a in script_args]
    )
    log.action("docker exec {} (workdir {})".format(name, workdir))
    if log.dry_run():
        log.say("--- script ---\n{}\n--- end ---".format(script.strip()))
        return 0
    result = _docker(argv, check=False)
    if check and result.returncode != 0:
        raise WorkspaceError(
            "container command failed with exit status {}".format(result.returncode))
    return result.returncode
