"""Print the Phase 1A demo configuration without accessing hardware."""

from __future__ import annotations

from pathlib import Path

from nautolab.resources.config_loader import load_lab_config


def main() -> None:
    """Load and display the portable demo lab state."""
    repository_root = Path(__file__).resolve().parents[1]
    state = load_lab_config(repository_root / "config" / "demo_lab.yaml")

    print("N-AutoLab")
    print("Phase 1A.1 -- Station Instance + Slot Resource Hierarchy")
    print()
    print("Stations:")
    for station in state.stations.list_all():
        print(
            f"{station.display_name} [{station.id}] "
            f"({state.station_occupancy(station.id)}/"
            f"{state.station_total_capacity(station.id)})"
        )
        for slot in state.slots.list_by_station(station.id):
            occupants = ", ".join(slot.occupant_ids) or "EMPTY"
            print(f"  {slot.display_name:<10} {occupants}")
        print()
    print("Devices:")
    for device in state.devices.list_all():
        print(
            f"  {device.id}: {device.implementation_state.value} / "
            f"{device.connection_state.value}"
        )
    print("Samples:")
    for sample in state.samples.list_all():
        print(f"  {sample.id}: slot={sample.current_location}, status={sample.status.value}")
    print()
    print("Runtime GUI: Not implemented")
    print("Hardware access: Disabled")
    print("No workflow was executed.")


if __name__ == "__main__":
    main()
