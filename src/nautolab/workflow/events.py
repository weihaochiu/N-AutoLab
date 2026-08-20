"""Typed, observer-only workflow events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable


@dataclass(frozen=True, slots=True)
class Event:
    workflow_id: str | None = None
    step_id: str | None = None
    message: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def category(self) -> str:
        return "WORKFLOW"


class WorkflowStarted(Event):
    """A workflow entered RUNNING."""
class WorkflowCompleted(Event):
    """A workflow completed all resolved steps."""
class WorkflowFailed(Event):
    """A workflow stopped on a visible failure."""
class WorkflowPaused(Event):
    """A workflow paused at a safe step boundary."""
class WorkflowPauseRequested(Event):
    """An operator requested boundary-safe pause during a running step."""
class WorkflowResumed(Event):
    """A paused workflow resumed."""
class WorkflowAborted(Event):
    """A workflow aborted before another step began."""
class StepStarted(Event):
    """One resolved step entered RUNNING."""
class StepCompleted(Event):
    """One resolved step completed."""
class StepFailed(Event):
    """One resolved step failed."""
class PreflightFailed(Event):
    @property
    def category(self) -> str: return "SAFETY"


class SampleMoved(Event):
    @property
    def category(self) -> str: return "SAMPLE"


class ResourceResolved(Event):
    @property
    def category(self) -> str: return "RESOURCE"


class SimulationTransportStarted(Event):
    @property
    def category(self) -> str: return "SIMULATION"


class SimulationTransportCompleted(Event):
    @property
    def category(self) -> str: return "SIMULATION"


@dataclass(frozen=True, slots=True)
class SubscriberError:
    event: Event
    subscriber_name: str
    error: str


class EventBus:
    """Deliver events while preserving authoritative domain transitions."""

    def __init__(self) -> None:
        self._subscribers: list[Callable[[Event], None]] = []
        self.events: list[Event] = []
        self.subscriber_errors: list[SubscriberError] = []

    def subscribe(self, subscriber: Callable[[Event], None]) -> Callable[[], None]:
        self._subscribers.append(subscriber)
        def unsubscribe() -> None:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)
        return unsubscribe

    def publish(self, event: Event) -> None:
        self.events.append(event)
        for subscriber in tuple(self._subscribers):
            try:
                subscriber(event)
            except Exception as exc:
                name = getattr(subscriber, "__qualname__", repr(subscriber))
                self.subscriber_errors.append(SubscriberError(event, name, repr(exc)))
