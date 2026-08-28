"""Exception types for the aqrp toolchain.

Every failure the CLI reports deliberately goes through one of these, so `cli.main`
can turn them into a clean one-line message instead of a traceback. Anything that
escapes as a bare exception is a bug in this package, not a user error.
"""


class AqrpError(Exception):
    """Base for every expected failure."""


class PreflightError(AqrpError):
    """A required dependency or external tool is missing."""


class ConfigError(AqrpError):
    """The workspace registry is missing, malformed, or self-contradictory."""


class WorkspaceError(AqrpError):
    """A workspace was not found, or its path is not an AQRP checkout."""


class VariantMismatch(AqrpError):
    """The registry and the tree on disk disagree about what a checkout is.

    Deliberately unrecoverable: there is no `--force`. A mismatch means nobody knows
    which SoC a build would target, and every stage is unsafe under that ambiguity.
    The fix is `aqrp workspace redetect <name>`.
    """
