"""Station-instance registry."""

from nautolab.core import ResourceInUseError, Station
from nautolab.core._validation import validate_identifier

from ._registry import ResourceRegistry


class StationRegistry(ResourceRegistry[Station]):
    """Authoritative lookup collection for stations."""

    resource_label = "station"

    def __init__(self) -> None:
        super().__init__()
        self._relational_removal_managed = False

    def remove(self, resource_id: str) -> Station:
        """Remove directly only when the registry is not owned by LabState."""
        if self._relational_removal_managed:
            self.get(resource_id)
            raise ResourceInUseError(
                f"cannot directly remove station {resource_id!r} from managed lab state; "
                "use LabState.remove_station_resource()"
            )
        return super().remove(resource_id)

    def _manage_relational_removal(self) -> None:
        """Require LabState to validate child-slot relationships before removal."""
        self._relational_removal_managed = True

    def _remove_from_lab_state(self, resource_id: str) -> Station:
        """Remove after LabState has proven the station has no child slots."""
        return super().remove(resource_id)

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
