"""
Input/Output schema definitions for agent capabilities.

Agents declare their input requirements and output contracts via JSON schemas.
MCP uses these to validate requests and responses for type safety and documentation.
"""

from typing import Dict, Any, List, Literal, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class JsonSchema:
    """
    Simplified JSON Schema for agent input/output validation.
    
    Supports basic types: string, number, integer, boolean, array, object
    """
    type: Literal["string", "number", "integer", "boolean", "array", "object"]
    description: str = ""
    required: bool = False
    enum: List[Any] = None
    min_items: int = None
    max_items: int = None
    min_length: int = None
    max_length: int = None
    pattern: str = None
    properties: Dict[str, "JsonSchema"] = None
    items: "JsonSchema" = None
    default: Any = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON Schema-compatible dict."""
        result = {
            "type": self.type,
            "description": self.description,
        }
        if self.required:
            result["required"] = True
        if self.enum:
            result["enum"] = self.enum
        if self.min_items is not None:
            result["minItems"] = self.min_items
        if self.max_items is not None:
            result["maxItems"] = self.max_items
        if self.min_length is not None:
            result["minLength"] = self.min_length
        if self.max_length is not None:
            result["maxLength"] = self.max_length
        if self.pattern:
            result["pattern"] = self.pattern
        if self.properties:
            result["properties"] = {k: v.to_dict() for k, v in self.properties.items()}
        if self.items:
            result["items"] = self.items.to_dict()
        if self.default is not None:
            result["default"] = self.default
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JsonSchema":
        """Create JsonSchema from dict."""
        properties = data.get("properties")
        if properties:
            properties = {k: cls.from_dict(v) for k, v in properties.items()}
        items = data.get("items")
        if items:
            items = cls.from_dict(items)
        return cls(
            type=data.get("type", "object"),
            description=data.get("description", ""),
            required=data.get("required", False),
            enum=data.get("enum"),
            min_items=data.get("minItems"),
            max_items=data.get("maxItems"),
            min_length=data.get("minLength"),
            max_length=data.get("maxLength"),
            pattern=data.get("pattern"),
            properties=properties,
            items=items,
            default=data.get("default"),
        )


@dataclass
class InputSchema:
    """
    Defines the input contract for an agent capability.
    
    Example: document.review capability expects text and attachments.
    """
    action: str
    required_fields: List[str]
    schema: Dict[str, JsonSchema]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "required_fields": self.required_fields,
            "schema": {k: v.to_dict() for k, v in self.schema.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InputSchema":
        schema = {k: JsonSchema.from_dict(v) for k, v in data.get("schema", {}).items()}
        return cls(
            action=data.get("action", ""),
            required_fields=data.get("required_fields", []),
            schema=schema,
        )


@dataclass
class OutputSchema:
    """
    Defines the output contract for an agent capability.
    
    Example: document.review returns status, risk_score, clauses, suggestions.
    """
    action: str
    status_codes: Dict[int, str]  # e.g., {200: "Success", 400: "Invalid request"}
    schema: Dict[str, JsonSchema]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "status_codes": self.status_codes,
            "schema": {k: v.to_dict() for k, v in self.schema.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OutputSchema":
        schema = {k: JsonSchema.from_dict(v) for k, v in data.get("schema", {}).items()}
        return cls(
            action=data.get("action", ""),
            status_codes=data.get("status_codes", {200: "Success"}),
            schema=schema,
        )


# ============================================================================
# SCHEMA DEFINITIONS FOR DOCUMENT REVIEW AGENT
# ============================================================================

DOCUMENT_REVIEW_INPUT_SCHEMA = InputSchema(
    action="document.review",
    required_fields=["text"],
    schema={
        "text": JsonSchema(
            type="string",
            description="Document text to review",
            required=True,
            min_length=10,
            max_length=50000,
        ),
        "attachments": JsonSchema(
            type="array",
            description="File attachments (PDFs, docx)",
            required=False,
            items=JsonSchema(
                type="object",
                description="File attachment",
                properties={
                    "filename": JsonSchema(type="string", description="Filename"),
                    "content_type": JsonSchema(type="string", description="MIME type"),
                    "size_bytes": JsonSchema(type="integer", description="File size"),
                },
            ),
        ),
        "review_type": JsonSchema(
            type="string",
            description="Type of review",
            required=False,
            enum=["full", "quick", "compliance"],
            default="full",
        ),
    },
)

DOCUMENT_REVIEW_OUTPUT_SCHEMA = OutputSchema(
    action="document.review",
    status_codes={
        200: "Document reviewed successfully",
        400: "Invalid document format",
        500: "Processing error",
    },
    schema={
        "status": JsonSchema(
            type="string",
            description="Review status",
            enum=["success", "error"],
        ),
        "risk_score": JsonSchema(
            type="number",
            description="Overall risk score (0-100)",
        ),
        "risk_level": JsonSchema(
            type="string",
            description="Risk classification",
            enum=["Low", "Moderate", "High", "Critical"],
        ),
        "clauses": JsonSchema(
            type="array",
            description="Detected clauses",
            items=JsonSchema(
                type="object",
                properties={
                    "name": JsonSchema(type="string", description="Clause name"),
                    "status": JsonSchema(
                        type="string",
                        description="Clause status",
                        enum=["Present", "Missing", "Partial"],
                    ),
                    "coverage": JsonSchema(
                        type="string",
                        description="Coverage indicator",
                        enum=["✔", "⚠", "✖"],
                    ),
                },
            ),
        ),
        "suggestions": JsonSchema(
            type="array",
            description="Risk mitigation suggestions",
            items=JsonSchema(
                type="object",
                properties={
                    "clause": JsonSchema(type="string"),
                    "suggestion": JsonSchema(type="string"),
                    "priority": JsonSchema(type="string", enum=["low", "medium", "high"]),
                },
            ),
        ),
    },
)

# ============================================================================
# SCHEMA DEFINITIONS FOR SUPPORT AGENT
# ============================================================================

IT_SUPPORT_TEXT_INPUT_SCHEMA = InputSchema(
    action="it.support.text",
    required_fields=["text"],
    schema={
        "text": JsonSchema(
            type="string",
            description="Support request text",
            required=True,
            min_length=5,
            max_length=5000,
        ),
        "category_hint": JsonSchema(
            type="string",
            description="Optional category hint",
            required=False,
            enum=["Network", "Email", "Access", "Hardware", "Security", "General"],
        ),
    },
)

IT_SUPPORT_TEXT_OUTPUT_SCHEMA = OutputSchema(
    action="it.support.text",
    status_codes={
        200: "Request processed successfully",
        400: "Invalid request",
        500: "Processing error",
    },
    schema={
        "status": JsonSchema(
            type="string",
            description="Processing status",
            enum=["ok", "error"],
        ),
        "decision": JsonSchema(
            type="string",
            description="Support decision",
            enum=["auto_resolved", "escalated", "ticket_created"],
        ),
        "category": JsonSchema(
            type="string",
            description="Detected category",
            enum=["Network", "Email", "Access", "Hardware", "Security", "General"],
        ),
        "priority": JsonSchema(
            type="string",
            description="Ticket priority",
            enum=["low", "medium", "high", "critical"],
        ),
        "answer": JsonSchema(
            type="string",
            description="Resolution or response",
        ),
        "ticket_id": JsonSchema(
            type="string",
            description="Created ticket ID (if escalated)",
        ),
    },
)

IT_SUPPORT_VOICE_INPUT_SCHEMA = InputSchema(
    action="it.support.voice",
    required_fields=["audio_file"],
    schema={
        "audio_file": JsonSchema(
            type="object",
            description="Audio file",
            required=True,
            properties={
                "filename": JsonSchema(type="string", description="Filename"),
                "content_type": JsonSchema(
                    type="string",
                    description="Audio MIME type",
                    enum=["audio/wav", "audio/mp3", "audio/ogg"],
                ),
                "size_bytes": JsonSchema(type="integer", description="File size"),
            },
        ),
        "language": JsonSchema(
            type="string",
            description="Audio language",
            default="en",
        ),
    },
)

IT_SUPPORT_VOICE_OUTPUT_SCHEMA = OutputSchema(
    action="it.support.voice",
    status_codes={
        200: "Voice request processed",
        400: "Invalid audio",
        500: "Processing error",
    },
    schema={
        "status": JsonSchema(type="string", description="Processing status", enum=["ok", "error"]),
        "transcription": JsonSchema(type="string", description="Transcribed text"),
        "decision": JsonSchema(type="string", description="Support decision"),
        "answer": JsonSchema(type="string", description="Resolution"),
    },
)


def get_agent_input_schema(action: str) -> Optional[InputSchema]:
    """Get input schema for a given action."""
    schemas = {
        "document.review": DOCUMENT_REVIEW_INPUT_SCHEMA,
        "it.support.text": IT_SUPPORT_TEXT_INPUT_SCHEMA,
        "it.support.voice": IT_SUPPORT_VOICE_INPUT_SCHEMA,
    }
    return schemas.get(action)


def get_agent_output_schema(action: str) -> Optional[OutputSchema]:
    """Get output schema for a given action."""
    schemas = {
        "document.review": DOCUMENT_REVIEW_OUTPUT_SCHEMA,
        "it.support.text": IT_SUPPORT_TEXT_OUTPUT_SCHEMA,
        "it.support.voice": IT_SUPPORT_VOICE_OUTPUT_SCHEMA,
    }
    return schemas.get(action)


def validate_input(action: str, payload: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate input payload against schema.
    
    Returns: (is_valid, error_messages)
    """
    schema = get_agent_input_schema(action)
    if not schema:
        return False, [f"No schema defined for action: {action}"]

    errors = []

    # Check required fields
    for field in schema.required_fields:
        if field not in payload:
            errors.append(f"Missing required field: {field}")

    # Check field types (basic)
    for field, field_schema in schema.schema.items():
        if field not in payload:
            continue
        value = payload[field]
        if field_schema.type == "string" and not isinstance(value, str):
            errors.append(f"Field '{field}' must be string, got {type(value).__name__}")
        elif field_schema.type == "integer" and not isinstance(value, int):
            errors.append(f"Field '{field}' must be integer, got {type(value).__name__}")
        elif field_schema.type == "number" and not isinstance(value, (int, float)):
            errors.append(f"Field '{field}' must be number, got {type(value).__name__}")
        elif field_schema.type == "array" and not isinstance(value, list):
            errors.append(f"Field '{field}' must be array, got {type(value).__name__}")

    return len(errors) == 0, errors
