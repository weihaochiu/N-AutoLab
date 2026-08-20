"""Domain-specific exceptions for N-AutoLab."""


class NautolabError(Exception):
    """Base class for expected N-AutoLab domain errors."""


class InvalidIdentifierError(NautolabError):
    """Raised when a stable domain identifier is not valid."""


class DuplicateResourceError(NautolabError):
    """Raised when a registry already contains the requested identifier."""


class ResourceNotFoundError(NautolabError):
    """Raised when a required registry resource does not exist."""


class ResourceInUseError(NautolabError):
    """Raised when destructive removal would leave a dangling relationship."""


class InvalidCapacityError(NautolabError):
    """Raised when a sample-holding resource capacity is invalid."""


class InvalidBooleanError(NautolabError):
    """Raised when a Boolean domain field receives a non-Boolean value."""


class DuplicateSlotIndexError(NautolabError):
    """Raised when one station has more than one slot with the same index."""


class StationOccupiedError(NautolabError):
    """Raised when a slot cannot accept another sample."""


class StationDisabledError(NautolabError):
    """Raised when placement is requested at a disabled station."""


class SlotDisabledError(NautolabError):
    """Raised when placement is requested at a disabled station slot."""


class LocationMismatchError(NautolabError):
    """Raised when sample location and exact-slot occupancy do not agree."""


class InvalidActionError(NautolabError):
    """Raised when an action declaration is internally invalid."""


class InvalidRecipeError(NautolabError):
    """Raised when a recipe or recipe step is internally invalid."""


class ConfigurationError(NautolabError):
    """Raised when a laboratory configuration cannot form valid domain state."""


class ResourceResolutionError(NautolabError):
    """Raised when destination intent cannot resolve to an available exact slot."""


class InvalidWorkflowTransitionError(NautolabError):
    """Raised when workflow lifecycle state would move out of order."""


class PreflightError(NautolabError):
    """Raised when execution is attempted after a failed preflight."""


class SimulationTransportError(NautolabError):
    """Raised when a simulated transfer cannot preserve canonical state."""


class SimulationAbortRequested(NautolabError):
    """Internal control signal for interruptible simulation-only playback."""
