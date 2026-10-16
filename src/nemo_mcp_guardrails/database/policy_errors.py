"""Controlled failures for unavailable or invalid enforcement policies."""


class PolicyLoadError(RuntimeError):
    """Stop runtime construction when mandatory policies cannot be loaded."""
