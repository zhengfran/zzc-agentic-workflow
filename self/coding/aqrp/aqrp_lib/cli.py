"""Argument parsing and dispatch.

Only the `workspace` command group exists so far. The stage commands (checkout, build,
flash, shell, logs, push, reboot, deploy, all) attach to the same parser as they land.

Two global conventions every stage inherits:

  -w NAME / --path DIR   workspace selection, kept as two distinct flags
  --dry-run              armed globally before any command runs, so the lowest-level
                         caller guards itself rather than every stage remembering to
"""

import argparse
import os
import sys

from . import build as build_mod
from . import checkout as checkout_mod
from . import container, log, workspace
from .errors import AqrpError, PreflightError


def preflight():
    """Fail on a missing dependency now, not at step 1 of a three-hour flash."""
    missing = []
    try:
        import yaml  # noqa: F401
    except ImportError:
        missing.append("PyYAML")
    try:
        import paramiko  # noqa: F401
    except ImportError:
        missing.append("paramiko")
    if missing:
        raise PreflightError(
            "missing required module(s): {}\n"
            "Install with: python3 -m pip install --user {}\n"
            "Note this package targets python3.8, which is where paramiko is "
            "installed on this machine.".format(", ".join(missing), " ".join(missing))
        )


def add_workspace_selector(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-w", "--workspace", metavar="NAME",
                       help="registered workspace to operate on")
    group.add_argument("--path", metavar="DIR",
                       help="operate on an unregistered checkout at DIR")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="aqrp",
        description="Check out, build, flash, and deploy AQRP across QNX7/QNX8 and HDK2/HDK3.",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="print what would happen without doing it")
    subparsers = parser.add_subparsers(dest="command")

    ws = subparsers.add_parser("workspace", help="manage the workspace registry")
    ws_sub = ws.add_subparsers(dest="workspace_command")

    add = ws_sub.add_parser("add", help="register an existing checkout")
    add.add_argument("name")
    add.add_argument("path")
    add.add_argument("--variant", choices=sorted(workspace.VARIANTS),
                     help="declare the SW variant instead of detecting it")

    ws_sub.add_parser("list", help="list registered workspaces")

    remove = ws_sub.add_parser("remove", help="unregister a workspace")
    remove.add_argument("name")

    redetect = ws_sub.add_parser(
        "redetect", help="re-derive sw_variant from the tree (the fix for a mismatch)")
    redetect.add_argument("name")

    show = ws_sub.add_parser("show", help="print every derived value for a workspace")
    show.add_argument("name")

    co = subparsers.add_parser("checkout", help="init and sync a source checkout")
    co.add_argument("name", help="workspace name (registered on success if new)")
    co.add_argument("--path", help="destination directory (required if unregistered)")
    co.add_argument("--variant", choices=sorted(workspace.VARIANTS),
                    help="SW variant (required if unregistered)")
    co.add_argument("--branch", help="manifest branch (default: the variant's)")
    co.add_argument("-j", "--jobs", type=int, help="parallel repo sync jobs")

    bd = subparsers.add_parser("build", help="build an image, or an incremental subdir")
    add_workspace_selector(bd)
    bd.add_argument("target", nargs="?", default="system-deployment",
                    choices=build_mod.IMAGE_TARGETS,
                    help="image target (ignored when --in is given)")
    bd.add_argument("--in", dest="subdir", metavar="SUBDIR",
                    help="incremental devshell build of this BSP SDK subdirectory")
    bd.add_argument("--reconfigure", action="store_true",
                    help="regenerate workdir/conf (needed if MACHINE or layers changed)")
    bd.add_argument("--run", default="make", metavar="CMD",
                    help="command to run in SUBDIR (default: make)")

    return parser


def cmd_workspace_add(args):
    registry = workspace.Registry.load()
    variant = args.variant
    if variant is None:
        variant, branch = workspace.detect(args.path)
        log.say("Detected {} (branch {})".format(variant, branch or "unknown"))
    entry = workspace.Workspace(args.name, args.path, variant)
    entry.validate()
    registry.add(entry)
    registry.save()
    log.ok("registered {} -> {}".format(entry.name, entry.path))
    return 0


def cmd_workspace_list(args):
    registry = workspace.Registry.load()
    if not registry.records:
        log.say("No workspaces registered. Add one with: aqrp workspace add NAME PATH")
        return 0
    width = max(len(w.name) for w in registry.records)
    for entry in registry.records:
        try:
            branch = entry.branch or "?"
        except AqrpError:
            branch = "?"
        log.say("{:<{w}}  {:<5}  {:<18}  {}".format(
            entry.name, entry.sw_variant, branch, entry.path, w=width))
    return 0


def cmd_workspace_remove(args):
    registry = workspace.Registry.load()
    registry.remove(args.name)
    registry.save()
    log.ok("unregistered {}".format(args.name))
    return 0


def cmd_workspace_redetect(args):
    registry = workspace.Registry.load()
    entry = registry.get(args.name)
    variant, branch = workspace.detect(entry.path)
    if variant == entry.sw_variant:
        log.ok("{} is already correct: {} (branch {})".format(
            entry.name, variant, branch or "unknown"))
        return 0
    log.say("{}: {} -> {}".format(entry.name, entry.sw_variant, variant))
    entry.sw_variant = variant
    registry.save()
    log.ok("updated {}".format(entry.name))
    return 0


def cmd_workspace_show(args):
    entry = workspace.Registry.load().get(args.name)
    width = max(len(label) for label, _ in entry.describe())
    for label, value in entry.describe():
        log.say("{:<{w}}  {}".format(label, value, w=width))
    # Reported after the values, so a mismatch is visible alongside what caused it.
    try:
        entry.validate()
    except AqrpError as error:
        log.warn(str(error))
        return 1
    return 0


def cmd_checkout(args):
    checkout_mod.preflight()
    return checkout_mod.checkout(
        args.name, path=args.path, variant=args.variant,
        branch=args.branch, jobs=args.jobs)


def cmd_build(args):
    container.preflight()
    ws = workspace.resolve(name=args.workspace, path=args.path)
    if args.subdir:
        return build_mod.build_incremental(ws, args.subdir, args.run)
    return build_mod.build_image(ws, args.target, reconfigure=args.reconfigure)


DISPATCH = {
    ("workspace", "add"): cmd_workspace_add,
    ("workspace", "list"): cmd_workspace_list,
    ("workspace", "remove"): cmd_workspace_remove,
    ("workspace", "redetect"): cmd_workspace_redetect,
    ("workspace", "show"): cmd_workspace_show,
    ("checkout", None): cmd_checkout,
    ("build", None): cmd_build,
}


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 2
    if args.command == "workspace" and not args.workspace_command:
        parser.parse_args([args.command, "--help"])
        return 2

    log.set_dry_run(args.dry_run)

    handler = DISPATCH.get((args.command, getattr(args, "workspace_command", None)))
    if handler is None:
        parser.error("unhandled command: {}".format(args.command))

    try:
        preflight()
        return handler(args)
    except AqrpError as error:
        print("error: {}".format(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130
    except BrokenPipeError:
        # `aqrp workspace show x | head` closes the pipe early. Point stdout at
        # devnull so the interpreter's shutdown flush does not raise a second time
        # and print "Exception ignored in ...". SIGPIPE is deliberately NOT reset to
        # SIG_DFL: paramiko writes to sockets, and a default SIGPIPE would kill a
        # flash mid-operation instead of raising something catchable.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 141
