from __future__ import annotations

import pytest

from nautolab.core import InvalidWorkflowTransitionError, WorkflowStatus
from nautolab.workflow.events import Event, EventBus
from nautolab.workflow.model import Workflow


def test_workflow_lifecycle_rejects_out_of_order_transition() -> None:
    workflow = Workflow("workflow_1", "recipe_1", "Recipe", [])
    with pytest.raises(InvalidWorkflowTransitionError):
        workflow.transition(WorkflowStatus.RUNNING)
    workflow.transition(WorkflowStatus.VALIDATED)
    workflow.transition(WorkflowStatus.READY)
    workflow.transition(WorkflowStatus.RUNNING)
    workflow.transition(WorkflowStatus.COMPLETED)


def test_subscriber_failure_is_captured_and_other_subscribers_run() -> None:
    bus = EventBus(); received = []
    def broken(_event: Event) -> None: raise RuntimeError("presentation failed")
    bus.subscribe(broken); bus.subscribe(received.append)
    event = Event(message="authoritative")
    bus.publish(event)
    assert received == [event]
    assert bus.events == [event]
    assert "presentation failed" in bus.subscriber_errors[0].error
