"""Custom exceptions for the NuVo SDK."""


class NuVoException(Exception):
    """Base exception for all NuVo SDK errors."""
    pass


class ConnectionError(NuVoException):
    """Raised when connection to device fails or is lost."""
    pass


class ProtocolError(NuVoException):
    """Raised when protocol parsing or communication fails."""
    pass


class CommandError(NuVoException):
    """Raised when a command fails to execute."""
    pass
