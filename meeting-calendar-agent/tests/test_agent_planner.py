from __future__ import annotations
from unittest.mock import patch
import json

from app.services.agent.planner import plan
from app.services.agent.contracts import AgentRequest, ConflictDetail


def test_plan_supported_intent_with_json_output():
    req = AgentRequest(
        intent="schedule_meeting",
        availability={"primary": {"busy": []}},
        conflicts=[ConflictDetail(type="POLICY", severity="low", explanation="outside hours")],
        urgency=2.0,
    )
    with patch("app.services.agent.planner._ask_model", return_value='{"action":"suggest_slots","reason":"ok","data":{}}'):
        result = plan(req)
    assert isinstance(result, dict)
    assert result["action"] == "suggest_slots"
    assert result["reason"] == "ok"


def test_plan_unsupported_intent():
    req = AgentRequest(intent="do_nothing")
    result = plan(req)
    assert result["action"] == "request_approval"
    assert "unsupported" in result["reason"]


def test_plan_model_failure_fallback():
    req = AgentRequest(intent="schedule_meeting")
    with patch("app.services.agent.planner._ask_model", return_value="not valid json"):
        result = plan(req)
    assert result["action"] == "request_approval"
    assert result["reason"] == "fallback"


def test_build_planner_prompt_contents():
    input_data = {"intent": "schedule_meeting", "availability": {}, "conflicts": [], "urgency": 1.0}
    from app.services.agent.planner import build_planner_prompt

    prompt = build_planner_prompt(input_data)
    assert "OUTPUT JSON ONLY" in prompt
    assert "Example output schema" in prompt
    assert "If unsure" in prompt
    assert "HARD conflicts" in prompt
    assert json.dumps(input_data) in prompt
