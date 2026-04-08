from __future__ import annotations
import json
from typing import Any, Dict, Optional

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    _transformers_available = True
except ImportError:  # pragma: no cover - transformers not installed in test env
    _transformers_available = False

from app.services.agent.contracts import AgentRequest

# load transformer pipeline as a singleton
_pipeline: Optional[Any] = None

def _get_pipeline() -> Any:
    global _pipeline
    if not _transformers_available:
        raise RuntimeError("transformers not available")
    if _pipeline is None:
        tokenizer = AutoTokenizer.from_pretrained("mistralai/mistral-small")
        model = AutoModelForCausalLM.from_pretrained("mistralai/mistral-small")
        device = 0 if torch.cuda.is_available() else -1
        _pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device=device,
            temperature=0,
            max_new_tokens=256,
        )
    return _pipeline


def _ask_model(prompt: str) -> str:
    if not _transformers_available:
        return "{\"action\": \"request_approval\", \"reason\": \"no_model\", \"data\": {}}"
    try:
        gen = _get_pipeline()(prompt)
        # pipeline returns list of dicts with 'generated_text'
        return gen[0]["generated_text"].strip()
    except Exception:
        # fallback deterministic string
        return "{\"action\": \"request_approval\", \"reason\": \"model_error\", \"data\": {}}"


def build_planner_prompt(input_data: Dict[str, Any]) -> str:
    """Constructs the prompt given structured input.

    The prompt enforces strict JSON output and includes a schema example
    and failure instructions.  Designed to stay under 500 tokens.
    """
    schema_example = {
        "action": "suggest_slots",  # or create_meeting or request_approval
        "reason": "explanation of decision",
        "data": {},
    }
    return (
        "You are a deterministic meeting planner.\n"
        "OUTPUT JSON ONLY. Do not include any text outside the JSON.\n"
        "Given the following input, choose an action.\n"
        "If unsure about the best slot, return suggest_slots.\n"
        "If there are HARD conflicts, return request_approval.\n"
        "Example output schema:\n"
        f"{json.dumps(schema_example)}\n"
        f"Input: {json.dumps(input_data)}\n"
    )


def plan(request: AgentRequest) -> Dict[str, Any]:
    """Determine an action given structured input.

    Input must include:
      - intent
      - availability (dict)
      - conflicts (list)
      - urgency (float)

    The LLM is prompted to return **strict JSON only** with keys:
    ``action`` ("suggest_slots"|"create_meeting"|"request_approval"),
    ``reason`` and ``data``.  If the model fails or returns invalid JSON,
    we use a deterministic fallback.
    """
    # only schedule_meeting is currently supported
    if request.intent != "schedule_meeting":
        return {"action": "request_approval", "reason": "unsupported_intent", "data": {}}

    payload = {
        "intent": request.intent,
        "availability": request.availability or {},
        "conflicts": [c.dict() for c in (request.conflicts or [])],
        "urgency": request.urgency or 1.0,
    }

    prompt = build_planner_prompt(payload)

    raw = _ask_model(prompt)
    try:
        result = json.loads(raw)
    except Exception:
        # fallback decision
        result = {"action": "request_approval", "reason": "fallback", "data": {}}
    # enforce allowed actions
    if result.get("action") not in ["suggest_slots", "create_meeting", "request_approval"]:
        result = {"action": "request_approval", "reason": "invalid_action", "data": {}}
    return result
