"""Domain-specific exceptions for N-AutoLab."""


class NautolabError(Exception):
    """Base class for expected N-AutoLab domain errors."""


class InvalidIdentifierError(NautolabError):
    """Raised when a stable domain identifier is not valid."""


class DuplicateResourceError(NautolabError):
    """Raised when a registry already contains the requested identifier."""


class ResourceNotFoundError(NautolabError):
    """Raised when a required registry resource does not exist."""


class InvalidCapacityError(NautolabError):
    """Raised when a station capacity is not a non-negative integer."""


class StationOccupiedError(NautolabError):
    """Raised when a station cannot accept another sample."""


class StationDisabledError(NautolabError):
    """Raised when placement is requested at a disabled station."""


class LocationMismatchError(NautolabError):
    """Raised when sample location and station occupancy do not agree."""


class InvalidActionError(NautolabError):
    """Raised when an action declaration is internally invalid."""


class InvalidRecipeError(NautolabError):
    """Raised when a recipe or recipe step is internally invalid."""


class ConfigurationError(NautolabError):
    """Raised when a laboratory configuration cannot form valid domain state."""
