"""Configurable, interruptible wall-clock playback for simulation demos."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from nautolab.core import SimulationAbortRequested


@dataclass(frozen=True, slots=True)
class SimulationPlayback:
    """Map virtual duration to optional accelerated wall-clock observation."""

    multiplier: float | None = None
    poll_interval_seconds: float = 0.05

    SPEEDS = {"Instant": None, "20×": 20.0, "10×": 10.0, "5×": 5.0, "1×": 1.0}

    def __post_init__(self) -> None:
        if self.multiplier is not None and self.multiplier <= 0:
            raise ValueError("playback multiplier must be positive or None for Instant")
        if self.poll_interval_seconds <= 0:
            raise ValueError("poll interval must be positive")

    @classmethod
    def from_label(cls, label: str) -> "SimulationPlayback":
        try:
            return cls(cls.SPEEDS[label])
        except KeyError as exc:
            raise ValueError(f"unknown simulation speed {label!r}") from exc

    @property
    def label(self) -> str:
        return next(label for label, value in self.SPEEDS.items() if value == self.multiplier)

    def wall_duration(self, simulated_duration_seconds: float) -> float:
        if simulated_duration_seconds < 0:
            raise ValueError("simulated duration must be non-negative")
        return 0.0 if self.multiplier is None else simulated_duration_seconds / self.multiplier

    def wait(
        self,
        simulated_duration_seconds: float,
        abort_requested: Callable[[], bool],
    ) -> None:
        remaining = self.wall_duration(simulated_duration_seconds)
        if remaining == 0:
            if abort_requested():
                raise SimulationAbortRequested("simulation abort requested")
            return
        deadline = time.monotonic() + remaining
        while True:
            if abort_requested():
                raise SimulationAbortRequested("simulation abort requested during playback")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            time.sleep(min(self.poll_interval_seconds, remaining))
