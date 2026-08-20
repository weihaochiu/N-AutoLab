"""Station-instance registry."""

from nautolab.core import Station
from nautolab.core._validation import validate_identifier

from ._registry import ResourceRegistry


class StationRegistry(ResourceRegistry[Station]):
    """Authoritative lookup collection for stations."""

    resource_label = "station"

    def list_all(self) -> tuple[Station, ...]:
        """Return station instances in canonical-id order."""
        return tuple(sorted(self._items.values(), key=lambda station: station.id))

    def list_by_type(self, station_type: str) -> tuple[Station, ...]:
        """Return one station type in deterministic canonical-id order."""
        station_type = validate_identifier(station_type, field_name="station_type")
        return tuple(
            station
            for station in self.list_all()
            if station.station_type == station_type
        )
