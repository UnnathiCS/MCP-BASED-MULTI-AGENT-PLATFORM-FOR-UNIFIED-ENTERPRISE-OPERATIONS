"""
Example agent registry configuration for the MCP system.

This defines the agents in your current system:
- Document Review Agent
- Customer Support Agent

To use: load this JSON into the AgentRegistry or define agents programmatically.
"""

import json
from typing import Dict, Any

# Agent registry configuration as dict (can be saved to JSON)
AGENT_REGISTRY_CONFIG: Dict[str, Any] = {
    "agents": {
        "document-review-agent": {
            "agent_id": "document-review-agent",
            "name": "Document Review Agent",
            "endpoint": "http://127.0.0.1:8001",
            "capabilities": [
                {
                    "action": "document.review",
                    "description": "Reviews uploaded PDFs for compliance risk, clause analysis, and suggestions",
                    "sample_inputs": ["Please review this contract", "Analyze document for risks"],
                    "required_fields": ["text", "attachments"]
                },
                {
                    "action": "document.analyze",
                    "description": "Extract and summarize document information",
                    "sample_inputs": ["Summarize the key points", "What are the main clauses?"],
                    "required_fields": ["text"]
                }
            ],
            "allowed_tenants": ["*"],
            "status": "registered",
            "sla": {
                "timeout_ms": 60000,
                "concurrency_limit": 5
            },
            "health_check_path": "/health",
            "auth": {
                "type": "bearer",
                "token_id": "mcp-service-account"
            },
            "priority": 80,
            "version": "1.0.0",
            "metadata": {
                "cost_estimate": 0.50,
                "region": "us-east-1",
                "team": "compliance"
            }
        },
        "support-agent": {
            "agent_id": "support-agent",
            "name": "Enterprise IT Support Agent",
            "endpoint": "http://127.0.0.1:8000",
            "capabilities": [
                {
                    "action": "it.support.text",
                    "description": "Text-based IT support ticket triage and auto-resolution",
                    "sample_inputs": ["My password reset request", "VPN not working", "How do I enable MFA?"],
                    "required_fields": ["text"]
                },
                {
                    "action": "it.support.voice",
                    "description": "Voice-based IT support using ASR transcription",
                    "sample_inputs": [],
                    "required_fields": ["audio_file"]
                },
                {
                    "action": "it.support.ticket",
                    "description": "Create or escalate support tickets",
                    "sample_inputs": ["Create a P1 incident ticket"],
                    "required_fields": ["text"]
                }
            ],
            "allowed_tenants": ["*"],
            "status": "registered",
            "sla": {
                "timeout_ms": 30000,
                "concurrency_limit": 10
            },
            "health_check_path": "/health",
            "auth": {
                "type": "bearer",
                "token_id": "mcp-service-account"
            },
            "priority": 70,
            "version": "1.0.0",
            "metadata": {
                "cost_estimate": 0.10,
                "region": "us-east-1",
                "team": "support"
            }
        }
    },
    "capability_index": {
        "document.review": ["document-review-agent"],
        "document.analyze": ["document-review-agent"],
        "it.support.text": ["support-agent"],
        "it.support.voice": ["support-agent"],
        "it.support.ticket": ["support-agent"]
    }
}


def get_default_registry_config() -> Dict[str, Any]:
    """Return the default agent registry configuration."""
    return AGENT_REGISTRY_CONFIG


def save_registry_to_file(filepath: str) -> bool:
    """Save the registry configuration to a JSON file."""
    try:
        with open(filepath, "w") as f:
            json.dump(AGENT_REGISTRY_CONFIG, f, indent=2)
        print(f"Saved registry to {filepath}")
        return True
    except Exception as e:
        print(f"Failed to save registry: {e}")
        return False


def load_registry_from_file(filepath: str) -> Dict[str, Any]:
    """Load registry configuration from a JSON file."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load registry: {e}")
        return {}
