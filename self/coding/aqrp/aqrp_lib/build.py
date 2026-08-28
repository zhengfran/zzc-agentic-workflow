"""Building AQRP: full images, and incremental devshell builds.

Both halves run inside the workspace's container. The BitBake environment is
initialised once and then reused: regenerating it would discard local.conf,
bblayers.conf, and devtool's workspace layer between builds.

MACHINE comes from the variant table, never a constant -- build-aqrp.sh hardcoded
`qnx8qam8775-som`, which is why it could not build qnx7 at all.
"""

import shutil

from . import container, log
from .errors import WorkspaceError
from .workspace import DISTRO

IMAGE_TARGETS = ("system-deployment", "base-qnx-image")

# Yocto's env scripts are not nounset-safe, hence `set -Ee -o pipefail` and no `set -u`.
_FULL_BUILD = r"""
set -Ee -o pipefail
distro="$1"; machine="$2"; target="$3"; shift 3
# Remaining args are setup_buildenv.py "-a LAYER" pairs (qnx7 needs a guest layer).
extra_layers=("$@")

if [[ ! -f ./workdir/conf/bblayers.conf ||
      ! -f ./workdir/conf/local.conf ||
      ! -e ./workdir/conf/site.conf ]]; then
    printf 'Initializing build environment in ./workdir (machine %s)\n' "$machine"
    ./meta-distro-common/scripts/setup_buildenv.py -d "$distro" -b ./workdir -m "$machine" \
        "${extra_layers[@]}"
else
    printf 'Reusing existing build configuration in ./workdir\n'
fi

source poky/oe-init-build-env ./workdir
printf 'Running: bitbake %s\n' "$target"
bitbake "$target"
"""

_DEVSHELL_BUILD = r"""
set -Ee -o pipefail
distro="$1"; machine="$2"; recipe="$3"; subdir="$4"; command="$5"
status=/tmp/aqrp_devshell.status
config=/tmp/aqrp_devshell.conf
trap 'rm -f "$status" "$config"' EXIT

# Run one command inside the recipe's devshell. $1 = subdir (relative to the devshell's
# cwd), $2 = shell command. The devshell is driven non-interactively by overriding
# OE_TERMINAL; success is signalled through a status file because the terminal wrapper's
# own exit code does not propagate the inner command's.
run_devshell() {
    rm -f "$status"
    cat > "$config" <<CONF
OE_TERMINAL = "custom"
OE_TERMINAL_CUSTOMCMD = "{command}"
DEVSHELL:forcevariable = "bash --rcfile \${BASHRC} -i -c 'set -e; cd $1; $2; printf success > $status'"
CONF
    printf '>>> devshell: %s   (in %s)\n' "$2" "$1"
    bitbake -R "$config" -c devshell "$recipe"
    if [[ "$(cat "$status" 2>/dev/null)" != "success" ]]; then
        printf 'Error: "%s" did not complete successfully in %s\n' "$2" "$1" >&2
        exit 1
    fi
}

if [[ ! -f ./workdir/conf/bblayers.conf ||
      ! -f ./workdir/conf/local.conf ||
      ! -e ./workdir/conf/site.conf ]]; then
    printf 'Initializing build environment in ./workdir (machine %s)\n' "$machine"
    ./meta-distro-common/scripts/setup_buildenv.py -d "$distro" -b ./workdir -m "$machine"
else
    printf 'Reusing existing build configuration in ./workdir\n'
fi

source poky/oe-init-build-env ./workdir
# NB every path below is relative to the BUILD dir: oe-init-build-env just cd'd into
# ./workdir. Using ./workdir/... here silently never matches.

# The devshell make builds in-tree under the recipe's ${S}, which for an unmodified recipe
# is a work directory wiped on re-unpack. `devtool modify` repoints ${S} at
# workspace/sources/<recipe>, a git checkout that persists -- which is what the deploy
# stage's artifact paths expect. A freshly synced tree has no workspace at all.
if [ ! -d "./workspace/sources/${recipe}" ]; then
    printf 'No devtool workspace for %s -- creating one (devtool modify)\n' "$recipe"
    devtool modify "$recipe"
fi

# A devtool workspace holds source but no generated artifacts, so building one
# subdirectory alone fails on missing aggregated headers: AMSS/inc/aosal_error.h and its
# ~160 siblings come from the recipe's TOP-LEVEL make, not the subdirectory's Makefile.
#
# Populate them by running that top-level make THROUGH THE DEVSHELL, not via
# `bitbake <recipe>`. Two reasons:
#   * bitbake pulls in the whole dependency graph, and on qnx7 that breaks -- ethphy.bb
#     declares do_install[depends] += "qnx-sa8255p-bsp-sdk:do_patch", and devtool modify
#     removes do_patch. qnx8 has no ethphy recipe, which is why it never hit this.
#   * the recipe's do_compile opens with `make clean`, which would wipe the incremental
#     state on every build. Skipping it is the point.
# Tracked by our own marker: AMSS/inc exists either way (8 files fresh, 167 populated),
# so counting files would be fragile. Delete the marker to force repopulation.
marker="./workspace/.aqrp-bsp-populated-${recipe}"
if [ ! -f "$marker" ]; then
    printf 'Workspace not yet populated: running the top-level make once.\n'
    printf 'This is slow. Later --in builds skip it and are incremental.\n'
    run_devshell "." "source_env; make gen_uid_gid_macro install"
    touch "$marker"
else
    printf 'Workspace already populated for %s\n' "$recipe"
fi

run_devshell "$subdir" "$command"
"""


def build_image(workspace, target="system-deployment", reconfigure=False):
    if target not in IMAGE_TARGETS:
        raise WorkspaceError(
            "unsupported build target {!r} (expected one of {})".format(
                target, ", ".join(IMAGE_TARGETS)))

    required = ("meta-distro-common/scripts/setup_buildenv.py", "poky/oe-init-build-env")
    for relative in required:
        if not (workspace.path / relative).exists() and not log.dry_run():
            raise WorkspaceError(
                "{} is not an AQRP checkout; missing {}".format(
                    workspace.path, relative))

    if reconfigure:
        # setup_buildenv.py only runs when workdir/conf is absent, so a changed MACHINE
        # or layer set would otherwise be silently ignored on an existing tree.
        conf = workspace.build_dir / "conf"
        if conf.is_dir():
            log.action("remove {} to force reconfiguration".format(conf))
            if not log.dry_run():
                shutil.rmtree(str(conf))

    log.step("build {} for {} ({}, machine {})".format(
        target, workspace.name, workspace.sw_variant, workspace.machine))
    layer_args = []
    for layer in workspace.extra_layers:
        layer_args += ["-a", layer]
    if layer_args:
        log.say("Extra layers: {}".format(" ".join(workspace.extra_layers)))
    container.run_script(
        workspace, _FULL_BUILD,
        [DISTRO, workspace.machine, target] + layer_args)
    log.ok("build completed: {}".format(target))
    return 0


def build_incremental(workspace, subdir, command="make"):
    """An in-tree `make` inside the BSP SDK devshell.

    The recipe is never a parameter: every tree has exactly one devtool source, already
    known as workspace.bsp_recipe.

    NB this builds IN-TREE under build/qnx/... and does NOT run hinstall, so install/
    and BSP-compiled/ stay stale. Read artifacts from the build tree, never install/.
    """
    log.step("incremental build: {} in {} ({})".format(
        command, subdir, workspace.bsp_recipe))
    if not workspace.devtool_sources.is_dir():
        log.say("No devtool workspace at {}".format(workspace.devtool_sources))
        log.say("It will be created with `devtool modify {}`, followed by a one-time"
                .format(workspace.bsp_recipe))
        log.say("full build of that recipe to populate generated headers. This first")
        log.say("run is slow; later --in builds reuse the workspace and are fast.")
    container.run_script(
        workspace, _DEVSHELL_BUILD,
        [DISTRO, workspace.machine, workspace.bsp_recipe, subdir, command])
    log.ok("incremental build completed: {}".format(subdir))
    return 0
