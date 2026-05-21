"""
Agent Registry: stores and manages agent metadata and capabilities.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import AgentRecord, Capability

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Central registry for all agents.
    
    Responsibilities:
    - Store agent metadata and capabilities
    - Track agent health and metrics
    - Provide semantic/capability-based agent lookup
    - Support both push (agent-initiated) and pull (MCP-initiated) registration
    """

    def __init__(self):
        self.agents: Dict[str, AgentRecord] = {}
        self.capability_index: Dict[str, List[str]] = {}  # action -> [agent_ids]

    def register_agent(self, agent_record: AgentRecord) -> bool:
        """Register or update an agent."""
        try:
            self.agents[agent_record.agent_id] = agent_record
            # Index capabilities
            for cap in agent_record.capabilities:
                if cap.action not in self.capability_index:
                    self.capability_index[cap.action] = []
                if agent_record.agent_id not in self.capability_index[cap.action]:
                    self.capability_index[cap.action].append(agent_record.agent_id)
            logger.info(f"Registered agent: {agent_record.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            return False

    def get_agent(self, agent_id: str) -> Optional[AgentRecord]:
        """Fetch an agent by ID."""
        return self.agents.get(agent_id)

    def get_agents_by_action(self, action: str) -> List[AgentRecord]:
        """Find all agents that support a given action."""
        agent_ids = self.capability_index.get(action, [])
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]

    def list_agents(self, status_filter: Optional[str] = None) -> List[AgentRecord]:
        """List all agents, optionally filtered by status."""
        agents = list(self.agents.values())
        if status_filter:
            agents = [a for a in agents if a.status == status_filter]
        return agents

    def update_agent_health(self, agent_id: str, is_healthy: bool, error_msg: str = ""):
        """Update agent health status."""
        agent = self.agents.get(agent_id)
        if agent:
            if is_healthy:
                agent.status = "registered"
                agent.error_count = 0
                agent.success_count += 1
            else:
                agent.error_count += 1
                if agent.error_count >= 3:
                    agent.status = "degraded"
                    logger.warning(f"Agent {agent_id} degraded after {agent.error_count} errors")
            agent.last_healthcheck = datetime.utcnow().isoformat()
            logger.debug(f"Updated health for {agent_id}: {agent.status}")

    def get_capability_embeddings(self, agent_id: str) -> Dict[str, List[float]]:
        """Get embeddings for all capabilities of an agent (for semantic matching)."""
        agent = self.agents.get(agent_id)
        if not agent:
            return {}
        return {cap.action: cap.embedding for cap in agent.capabilities if cap.embedding}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize registry to dict."""
        return {
            "agents": {aid: agent.to_dict() for aid, agent in self.agents.items()},
            "capability_index": self.capability_index,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AgentRegistry":
        """Deserialize registry from dict."""
        registry = AgentRegistry()
        for agent_dict in data.get("agents", {}).values():
            agent = AgentRecord.from_dict(agent_dict)
            registry.register_agent(agent)
        return registry

    def load_from_json_file(self, filepath: str) -> bool:
        """Load registry from JSON file."""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            registry = self.from_dict(data)
            self.agents = registry.agents
            self.capability_index = registry.capability_index
            logger.info(f"Loaded registry from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load registry from {filepath}: {e}")
            return False

    def save_to_json_file(self, filepath: str) -> bool:
        """Save registry to JSON file."""
        try:
            with open(filepath, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.info(f"Saved registry to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save registry to {filepath}: {e}")
            return False


    @staticmethod
    def from_config(config: Dict[str, Any]) -> "AgentRegistry":
        registry = AgentRegistry()
        agents = config.get("agents", {})
        for agent_id, agent_dict in agents.items():
            try:
                agent = AgentRecord.from_dict(agent_dict)
                registry.register_agent(agent)
            except Exception as e:
                logger.warning(f"Failed to load agent {agent_id} from config: {e}")
        return registry
