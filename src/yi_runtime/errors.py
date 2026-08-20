class YIError(Exception):
    """Base error for expected runtime failures."""


class ManifestError(YIError):
    """Manifest structure or routing is invalid."""


class PackageError(YIError):
    """The .yios container is malformed or has failed integrity checks."""


class StateError(YIError):
    """Project state cannot be validated or loaded."""
