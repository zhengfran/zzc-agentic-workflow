"""Workspaces: named AQRP checkouts, and everything derived from one.

A **workspace** is a named checkout. Its name *is* its identity, not a lookup key over
its properties: two trees can share every property and still be different workspaces
(`aqrp_qnx8_hdk3` and `aqrp_prefot` are both qnx8 on `pt/preFOT`). The name is also the
only way to override a misleading directory name, because Yocto bakes absolute paths
into sstate, stamps, and the devtool workspace -- renaming a checkout is not survivable.

Only three fields are stored: name, path, sw_variant. Everything else is derived, and
the split is deliberate:

  * `branch` changes under you on `repo init -b`, so a stored copy would be a lie.
  * `machine`, `bsp_recipe`, and friends are pure functions of `sw_variant`, so they
    live in VARIANTS rather than being repeated per workspace.
  * `sw_variant` is stored *because* it never changes for a given tree, which makes it
    the only thing capable of catching a path that points at the wrong checkout.
"""

import os
import re
import subprocess
from pathlib import Path

import yaml

from .errors import ConfigError, VariantMismatch, WorkspaceError

# Identical across every variant, so not variant data -- just constants. Putting them
# in VARIANTS would imply a variability that does not exist.
DISTRO = "base-qnx"
DOCKER_IMAGE = "i-st-pd-docker-v.eu.artifactory.automotive.cloud/oe:devenv-1.0"

MANIFEST_REMOTE = "git@github-ix.int.automotive-wan.com:sw-foundation-assets"

VARIANTS = {
    "qnx7": {
        "machine": "qnx7qam8255-som",
        "manifest_repo": "manifests-denali.git",
        "default_branch": "denali-5.0-beta",
        # NB: NOT the qnx8 set. checkout-source.sh hardcoded the qnx8 groups, which
        # would have synced the wrong projects for qnx7.
        "groups": "qnx,platform-linux",
        "bsp_recipe": "qnx-sa8255p-bsp-sdk",
        # The SA8255 BSP SDK refuses to compile without a guest: its layer.conf is what
        # appends android-guest/linux-guest to DISTRO_FEATURES, and qnx-sa8255p-bsp-sdk
        # bbfatals with "No guest defined" when neither is present. Android is what the
        # previous checkout used (its workdir held Denali_Android_Guest). Swap to
        # meta-linux-guest here to build the Linux-guest variant instead -- note that
        # changing it invalidates sstate.
        "extra_layers": ["meta-android-guest"],
    },
    "qnx8": {
        "machine": "qnx8qam8775-som",
        "manifest_repo": "manifests-qcoos.git",
        "default_branch": "qcoos-1.0-int",
        "groups": "integration,embedded,platform-linux",
        "bsp_recipe": "qnx-sa8775p-bsp-sdk",
        # qnx8 needs no guest layer: the SA8775 BSP has no such requirement.
        "extra_layers": [],
    },
}

# Every tree that setup_buildenv.py can configure offers exactly one real machine, so
# MACHINE identifies the variant unambiguously.
MACHINE_TO_VARIANT = {v["machine"]: name for name, v in VARIANTS.items()}
MANIFEST_TO_VARIANT = {v["manifest_repo"]: name for name, v in VARIANTS.items()}

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "workspaces.yaml"
REGISTRY_VERSION = 1


class Workspace(object):
    """One named checkout, plus everything derived from it."""

    def __init__(self, name, path, sw_variant):
        if sw_variant not in VARIANTS:
            raise ConfigError(
                "workspace {!r}: unknown sw_variant {!r} (expected one of {})".format(
                    name, sw_variant, ", ".join(sorted(VARIANTS))
                )
            )
        self.name = name
        self.raw_path = path
        self.path = Path(os.path.expanduser(path))
        self.sw_variant = sw_variant

    # -- derived from the variant table ------------------------------------------
    @property
    def _variant(self):
        return VARIANTS[self.sw_variant]

    @property
    def machine(self):
        return self._variant["machine"]

    @property
    def bsp_recipe(self):
        return self._variant["bsp_recipe"]

    @property
    def groups(self):
        return self._variant["groups"]

    @property
    def extra_layers(self):
        return self._variant.get("extra_layers", [])

    @property
    def manifest_url(self):
        return "{}/{}".format(MANIFEST_REMOTE, self._variant["manifest_repo"])

    @property
    def default_branch(self):
        return self._variant["default_branch"]

    @property
    def container(self):
        # Docker names must match [a-zA-Z0-9][a-zA-Z0-9_.-]*, so sanitise rather than
        # trusting the workspace name. An ad-hoc --path workspace in particular has a
        # generated name that would otherwise produce an unusable container.
        safe = re.sub(r"[^A-Za-z0-9_.-]", "-", self.name)
        return "aqrp-{}".format(safe)

    @property
    def build_dir(self):
        return self.path / "workdir"

    @property
    def devtool_sources(self):
        return self.build_dir / "workspace" / "sources" / self.bsp_recipe

    # -- derived from the tree on disk -------------------------------------------
    @property
    def branch(self):
        """Always read live: `repo init -b` changes it without touching the registry."""
        return detect_branch(self.path)

    def validate(self):
        """Refuse to operate when the registry and the disk disagree.

        Two independent checks, because they fail in different ways:

          1. declared sw_variant vs the manifest the tree was actually inited from
          2. the tree's own internal consistency -- a stale workdir/conf/local.conf
             surviving a re-init onto a different manifest would otherwise produce a
             clean build against the wrong SoC
        """
        if not self.path.is_dir():
            raise WorkspaceError(
                "workspace {!r}: path does not exist: {}".format(self.name, self.path)
            )
        if not (self.path / ".repo").is_dir():
            raise WorkspaceError(
                "workspace {!r}: not a repo checkout (no .repo): {}".format(
                    self.name, self.path
                )
            )

        detected = detect_variant_from_manifest(self.path)
        if detected is not None and detected != self.sw_variant:
            raise VariantMismatch(
                "workspace {!r} declares sw_variant {!r} (in {})\n"
                "but {} was inited from {} which is {!r}.\n"
                "Fix with: aqrp workspace redetect {}".format(
                    self.name, self.sw_variant, REGISTRY_PATH,
                    self.path, self.path / ".repo/manifests.git", detected,
                    self.name,
                )
            )

        machine = read_local_conf_machine(self.path)
        if machine is not None and MACHINE_TO_VARIANT.get(machine) != self.sw_variant:
            raise VariantMismatch(
                "workspace {!r} is {!r}, but {}\n"
                "sets MACHINE = {!r}, which belongs to {!r}.\n"
                "The tree is internally inconsistent -- most likely a stale workdir/\n"
                "survived a re-init onto a different manifest. Remove workdir/conf and\n"
                "let the build stage regenerate it.".format(
                    self.name, self.sw_variant,
                    self.path / "workdir/conf/local.conf",
                    machine, MACHINE_TO_VARIANT.get(machine, "no known variant"),
                )
            )

    def describe(self):
        """Every derived value, for `aqrp workspace show`.

        The debugging surface for the whole derivation chain: with most of what drives
        a build being derived rather than stored, this is the only way to ask the tool
        what it thinks before it acts on it.
        """
        try:
            branch = self.branch or "(unknown)"
        except WorkspaceError:
            branch = "(unreadable)"
        machine_on_disk = read_local_conf_machine(self.path)
        return [
            ("name", self.name),
            ("path", str(self.path)),
            ("sw_variant", self.sw_variant),
            ("branch", branch),
            ("machine", self.machine),
            ("machine on disk", machine_on_disk or "(not configured yet)"),
            ("distro", DISTRO),
            ("bsp_recipe", self.bsp_recipe),
            ("groups", self.groups),
            ("extra_layers", ", ".join(self.extra_layers) or "(none)"),
            ("manifest_url", self.manifest_url),
            ("container", self.container),
            ("docker_image", DOCKER_IMAGE),
            ("build_dir", str(self.build_dir)),
            ("devtool_sources", str(self.devtool_sources)),
        ]


# -- detection -------------------------------------------------------------------
def _git_config(git_dir, key):
    try:
        out = subprocess.run(
            ["git", "--git-dir", str(git_dir), "config", "--get", key],
            check=False, capture_output=True, text=True,
        )
    except FileNotFoundError:
        raise WorkspaceError("git is not available in PATH")
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def detect_variant_from_manifest(path):
    """Identify the SW variant from `.repo/manifests.git`.

    Preferred over local.conf's MACHINE because `.repo` exists from `repo init`
    onwards, long before setup_buildenv.py creates workdir/conf -- so this works on a
    freshly synced tree that has never been built.
    """
    url = _git_config(Path(path) / ".repo/manifests.git", "remote.origin.url")
    if not url:
        return None
    for repo, variant in MANIFEST_TO_VARIANT.items():
        if url.endswith(repo):
            return variant
    return None


def detect_branch(path):
    """The manifest branch this tree was inited on."""
    ref = _git_config(Path(path) / ".repo/manifests.git", "branch.default.merge")
    if not ref:
        return None
    return ref.split("refs/heads/", 1)[-1]


def read_local_conf_machine(path):
    """MACHINE from workdir/conf/local.conf, or None if the tree is unconfigured."""
    conf = Path(path) / "workdir" / "conf" / "local.conf"
    if not conf.is_file():
        return None
    for line in conf.read_text(errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("MACHINE") and "=" in stripped:
            return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def detect(path):
    """Best-effort (sw_variant, branch) for an arbitrary directory."""
    path = Path(os.path.expanduser(str(path)))
    variant = detect_variant_from_manifest(path)
    if variant is None:
        machine = read_local_conf_machine(path)
        variant = MACHINE_TO_VARIANT.get(machine) if machine else None
    if variant is None:
        raise WorkspaceError(
            "cannot determine the SW variant of {}\n"
            "Neither .repo/manifests.git nor workdir/conf/local.conf identified it.\n"
            "Pass --variant explicitly.".format(path)
        )
    return variant, detect_branch(path)


# -- registry --------------------------------------------------------------------
class Registry(object):
    """The workspaces.yaml file: a version key and a list of records."""

    def __init__(self, records, path=REGISTRY_PATH):
        self.records = records
        self.path = path

    @classmethod
    def load(cls, path=REGISTRY_PATH):
        path = Path(path)
        if not path.is_file():
            return cls([], path)
        try:
            data = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError as error:
            raise ConfigError("{} is not valid YAML: {}".format(path, error))
        if not isinstance(data, dict):
            raise ConfigError("{}: expected a mapping at the top level".format(path))

        version = data.get("version")
        if version != REGISTRY_VERSION:
            raise ConfigError(
                "{}: unsupported version {!r} (this build understands {})".format(
                    path, version, REGISTRY_VERSION
                )
            )

        raw = data.get("workspaces") or []
        if not isinstance(raw, list):
            raise ConfigError("{}: 'workspaces' must be a list".format(path))

        records, seen = [], set()
        for entry in raw:
            if not isinstance(entry, dict):
                raise ConfigError("{}: every workspace must be a mapping".format(path))
            missing = {"name", "path", "sw_variant"} - set(entry)
            if missing:
                raise ConfigError(
                    "{}: workspace {!r} is missing {}".format(
                        path, entry.get("name", "<unnamed>"), ", ".join(sorted(missing))
                    )
                )
            name = entry["name"]
            # A list does not structurally prevent duplicates, and name is identity --
            # so a duplicate is a corrupt file, not something to merge.
            if name in seen:
                raise ConfigError(
                    "{}: duplicate workspace name {!r}. Names are identities; "
                    "remove one.".format(path, name)
                )
            seen.add(name)
            records.append(Workspace(name, entry["path"], entry["sw_variant"]))
        return cls(records, path)

    def save(self):
        from . import log

        payload = {
            "version": REGISTRY_VERSION,
            "workspaces": [
                {"name": w.name, "path": w.raw_path, "sw_variant": w.sw_variant}
                for w in self.records
            ],
        }
        log.action("write {}".format(self.path))
        if log.dry_run():
            return
        self.path.write_text(
            "# aqrp workspace registry -- machine-local, gitignored.\n"
            "# Managed by `aqrp workspace add|remove|redetect`.\n"
            + yaml.safe_dump(payload, sort_keys=False, default_flow_style=False)
        )

    def names(self):
        return [w.name for w in self.records]

    def get(self, name):
        for record in self.records:
            if record.name == name:
                return record
        raise WorkspaceError(
            "no workspace named {!r}. Known: {}".format(
                name, ", ".join(self.names()) or "(none registered)"
            )
        )

    def add(self, workspace):
        if workspace.name in self.names():
            raise WorkspaceError(
                "workspace {!r} already exists; remove it first".format(workspace.name)
            )
        self.records.append(workspace)

    def remove(self, name):
        self.get(name)
        self.records = [w for w in self.records if w.name != name]


def resolve(name=None, path=None, variant=None):
    """Turn `-w NAME` or `--path DIR` into a validated Workspace.

    Two separate flags on purpose. Overloading one to mean both a name and a path is
    the ambiguity AQRP_SOURCE_DIR created, where retargeting one derived path left the
    others pointing at the old tree. There is no cwd inference either: an operation
    against the wrong 378 GB checkout should require having typed its name.
    """
    if name and path:
        raise WorkspaceError("pass either -w NAME or --path DIR, not both")
    if name:
        workspace = Registry.load().get(name)
        workspace.validate()
        return workspace
    if path:
        detected_variant, _ = detect(path) if variant is None else (variant, None)
        # Named after the directory so the derived container name is stable and
        # meaningful across repeated ad-hoc runs against the same tree.
        basename = Path(os.path.expanduser(str(path))).resolve().name
        workspace = Workspace("adhoc-{}".format(basename), str(path), detected_variant)
        workspace.validate()
        return workspace
    raise WorkspaceError("no workspace selected: pass -w NAME or --path DIR")
