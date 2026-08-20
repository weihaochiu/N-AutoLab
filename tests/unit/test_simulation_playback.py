import pytest

from nautolab.core import SimulationAbortRequested
from nautolab.simulation import SimulationPlayback


@pytest.mark.parametrize(
    ("label", "duration", "expected"),
    [
        ("Instant", 30, 0),
        ("20×", 30, 1.5),
        ("10×", 30, 3),
        ("5×", 30, 6),
        ("1×", 30, 30),
    ],
)
def test_simulation_speed_conversion(label: str, duration: float, expected: float) -> None:
    playback = SimulationPlayback.from_label(label)
    assert playback.wall_duration(duration) == expected
    assert playback.label == label


def test_instant_playback_still_honors_existing_abort() -> None:
    with pytest.raises(SimulationAbortRequested):
        SimulationPlayback.from_label("Instant").wait(1000, lambda: True)
