"""Station registry."""

from nautolab.core import Station

from ._registry import ResourceRegistry


class StationRegistry(ResourceRegistry[Station]):
    """Authoritative lookup collection for stations."""

    resource_label = "station"
