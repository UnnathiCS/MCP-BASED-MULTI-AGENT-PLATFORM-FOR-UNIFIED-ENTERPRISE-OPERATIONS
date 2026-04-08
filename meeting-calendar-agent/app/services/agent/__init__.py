"""Agent-related services and models.

This package will host the AI agent logic for Phase-2 and beyond.  It is
kept separate from the existing meeting service APIs to allow clean
separation between external HTTP schemas and internal decision-making
contracts.  Future MCP integration will interact with the types defined
here.
"""

from .contracts import AgentRequest, AgentDecision, ConflictDetail

__all__ = ["AgentRequest", "AgentDecision", "ConflictDetail"]
