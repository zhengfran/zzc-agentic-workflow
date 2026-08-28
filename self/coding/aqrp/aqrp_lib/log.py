"""Progress output.

Printed with flush=True throughout: builds and flashes run for minutes to hours, and
buffered output makes a working command look hung.
"""

import sys

_DRY_RUN = False


def set_dry_run(enabled):
    """Arm dry-run globally, so the lowest-level callers can guard themselves.

    Deliberately module state rather than a threaded-through parameter: every remote
    call, docker exec, and file write must honour it, and an argument that must reach
    all of them is an argument someone eventually forgets to pass.
    """
    global _DRY_RUN
    _DRY_RUN = enabled


def dry_run():
    return _DRY_RUN


def say(message):
    print(message, flush=True)


def step(message):
    print("\n==> {}".format(message), flush=True)


def ok(message):
    print("    ok  {}".format(message), flush=True)


def warn(message):
    print("    !!  {}".format(message), file=sys.stderr, flush=True)


def action(message):
    """Report something that changes state, or would have under --dry-run."""
    print("{}{}".format("[dry-run] " if _DRY_RUN else "+ ", message), flush=True)
