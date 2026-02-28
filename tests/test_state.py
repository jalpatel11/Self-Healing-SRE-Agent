"""Tests for state.py — SREAgentState and create_initial_state."""
from state import create_initial_state


def test_initial_state_uses_utc_aware_datetime():
    """error_timestamp must be timezone-aware ISO 8601 string ending with +00:00."""
    state = create_initial_state("Test error occurred")
    ts = state["error_timestamp"]
    assert ts.endswith("+00:00"), (
        f"Timestamp must be UTC-aware ISO format (ends with +00:00), got: {ts!r}"
    )


def test_initial_state_message_content():
    """The error message is stored as the first message's content."""
    msg = "KeyError in /api/data"
    state = create_initial_state(msg)
    assert state["messages"][0].content == msg


def test_initial_state_defaults():
    """All default fields are initialised correctly."""
    state = create_initial_state("some error")
    assert state["iteration_count"] == 0
    assert state["pr_url"] == ""
    assert state["pr_status"] == "pending"
    assert state["root_cause_identified"] is False
    assert state["fix_validated"] is False
    assert state["validation_errors"] == []
    assert state["error_logs"] == ""
