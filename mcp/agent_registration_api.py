"""
Agent Registration API for dynamic agent discovery and management.

Agents can self-register or be discovered via registry.

Features:
- Push registration: Agents call /agents/register endpoint
- Pull discovery: MCP queries agent /health endpoint
- Capability matching: Find agents by action/capability
- Health monitoring: Track agent availability
- Extensibility: Easy to add new agent types
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import requests
from .models import AgentRecord, Capability
from .agent_schemas import (
    get_agent_input_schema,
    get_agent_output_schema,
)

logger = logging.getLogger(__name__)


class AgentRegistrationAPI:
    """
    API for agent registration and discovery.
    
    Handles:
    - Agent self-registration
    - Capability declaration
    - Health checks
    - Metadata updates
    - Agent deletion/deregistration
    """

    def __init__(self, registry):
        """
        Initialize registration API with a registry backend.
        
        Args:
            registry: AgentRegistry instance
        """
        self.registry = registry
        self.health_check_interval = timedelta(minutes=5)
        self.last_health_check = {}

    def register_agent(
        self,
        agent_id: str,
        name: str,
        endpoint: str,
        capabilities: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        sla: Optional[Dict[str, Any]] = None,
        auth: Optional[Dict[str, Any]] = None,
        allowed_tenants: Optional[List[str]] = None,
        priority: int = 50,
    ) -> Tuple[bool, str]:
        """
        Register a new agent or update existing registration.

        Args:
            agent_id: Unique agent identifier
            name: Human-readable agent name
            endpoint: Base URL for agent API
            capabilities: List of capability dicts with 'action', 'description'
            metadata: Agent metadata (cost, team, region, etc.)
            sla: Service level agreements (timeout, concurrency)
            auth: Authentication details (type, token_id)
            allowed_tenants: List of allowed tenants (default ["*"])
            priority: Agent priority (0-100)

        Returns:
            (success, message)
        """
        try:
            # Convert capability dicts to Capability objects
            cap_objects = []
            for cap in capabilities:
                cap_objects.append(
                    Capability(
                        action=cap.get("action", ""),
                        description=cap.get("description", ""),
                        sample_inputs=cap.get("sample_inputs", []),
                        required_fields=cap.get("required_fields", []),
                    )
                )

            # Create agent record
            agent_record = AgentRecord(
                agent_id=agent_id,
                name=name,
                endpoint=endpoint,
                capabilities=cap_objects,
                allowed_tenants=allowed_tenants or ["*"],
                status="discovered",
                sla=sla or {"timeout_ms": 30000, "concurrency_limit": 10},
                auth=auth or {},
                priority=priority,
                metadata=metadata or {},
            )

            # Register in registry
            success = self.registry.register_agent(agent_record)
            if success:
                logger.info(f"✅ Registered agent: {agent_id}")
                return True, f"Agent {agent_id} registered successfully"
            else:
                return False, f"Failed to register agent {agent_id}"

        except Exception as e:
            logger.error(f"❌ Error registering agent {agent_id}: {e}")
            return False, f"Registration error: {str(e)}"

    def deregister_agent(self, agent_id: str) -> Tuple[bool, str]:
        """
        Remove an agent from the registry.

        Args:
            agent_id: Agent to remove

        Returns:
            (success, message)
        """
        try:
            if agent_id in self.registry.agents:
                del self.registry.agents[agent_id]
                # Remove from capability index
                for action, agent_ids in self.registry.capability_index.items():
                    if agent_id in agent_ids:
                        agent_ids.remove(agent_id)
                logger.info(f"✅ Deregistered agent: {agent_id}")
                return True, f"Agent {agent_id} deregistered"
            else:
                return False, f"Agent {agent_id} not found"
        except Exception as e:
            logger.error(f"❌ Error deregistering agent: {e}")
            return False, str(e)

    def check_agent_health(self, agent_id: str) -> Tuple[bool, str]:
        """
        Check if an agent is healthy by calling its /health endpoint.

        Args:
            agent_id: Agent to check

        Returns:
            (is_healthy, status_message)
        """
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return False, f"Agent {agent_id} not found"

        try:
            url = f"{agent.endpoint}{agent.health_check_path}"
            response = requests.get(url, timeout=5)
            is_healthy = response.status_code == 200
            status = response.json().get("status", "unknown") if is_healthy else "offline"

            # Update registry
            self.registry.update_agent_health(agent_id, is_healthy)

            message = f"Agent {agent_id} is {status}"
            if is_healthy:
                logger.debug(f"✅ {message}")
            else:
                logger.warning(f"⚠️ {message}")

            return is_healthy, message

        except requests.exceptions.Timeout:
            self.registry.update_agent_health(agent_id, False, "Health check timeout")
            logger.warning(f"⚠️ Health check timeout for {agent_id}")
            return False, f"Health check timeout for {agent_id}"
        except Exception as e:
            self.registry.update_agent_health(agent_id, False, str(e))
            logger.error(f"❌ Health check failed for {agent_id}: {e}")
            return False, f"Health check failed: {str(e)}"

    def health_check_all(self) -> Dict[str, bool]:
        """
        Check health of all agents.

        Returns:
            Dict mapping agent_id -> is_healthy
        """
        results = {}
        for agent_id in self.registry.agents.keys():
            is_healthy, _ = self.check_agent_health(agent_id)
            results[agent_id] = is_healthy
        return results

    def find_agents_by_capability(self, action: str) -> List[AgentRecord]:
        """
        Find all agents that support a given action/capability.

        Args:
            action: Action name (e.g., 'document.review')

        Returns:
            List of matching agents, sorted by priority
        """
        agents = self.registry.get_agents_by_action(action)
        return sorted(agents, key=lambda a: a.priority, reverse=True)

    def find_agents_by_name(self, name_substr: str) -> List[AgentRecord]:
        """
        Find agents by name substring.

        Args:
            name_substr: Substring to search for

        Returns:
            List of matching agents
        """
        return [
            agent
            for agent in self.registry.agents.values()
            if name_substr.lower() in agent.name.lower()
        ]

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent info dict, or None if not found
        """
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return None

        # Get schemas for each capability
        capabilities_with_schemas = []
        for cap in agent.capabilities:
            cap_dict = {
                "action": cap.action,
                "description": cap.description,
                "sample_inputs": cap.sample_inputs,
                "required_fields": cap.required_fields,
            }
            # Add input/output schemas if defined
            input_schema = get_agent_input_schema(cap.action)
            output_schema = get_agent_output_schema(cap.action)
            if input_schema:
                cap_dict["input_schema"] = input_schema.to_dict()
            if output_schema:
                cap_dict["output_schema"] = output_schema.to_dict()
            capabilities_with_schemas.append(cap_dict)

        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "endpoint": agent.endpoint,
            "status": agent.status,
            "priority": agent.priority,
            "version": agent.version,
            "capabilities": capabilities_with_schemas,
            "sla": agent.sla,
            "metadata": agent.metadata,
            "health": {
                "status": agent.status,
                "error_count": agent.error_count,
                "success_count": agent.success_count,
                "last_check": agent.last_healthcheck,
            },
        }

    def list_all_agents(self) -> List[Dict[str, Any]]:
        """
        List all registered agents with their details.

        Returns:
            List of agent info dicts
        """
        return [self.get_agent_info(agent_id) for agent_id in self.registry.agents.keys()]

    def list_all_capabilities(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List all capabilities available across all agents.

        Returns:
            Dict mapping action -> list of agents supporting it
        """
        result = {}
        for action, agent_ids in self.registry.capability_index.items():
            result[action] = [
                {
                    "agent_id": aid,
                    "agent_name": self.registry.agents[aid].name,
                    "priority": self.registry.agents[aid].priority,
                }
                for aid in agent_ids
                if aid in self.registry.agents
            ]
        return result

    def update_agent_metadata(
        self, agent_id: str, metadata: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Update agent metadata (cost, team, region, etc.).

        Args:
            agent_id: Agent to update
            metadata: New metadata dict

        Returns:
            (success, message)
        """
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return False, f"Agent {agent_id} not found"

        try:
            agent.metadata.update(metadata)
            logger.info(f"✅ Updated metadata for {agent_id}")
            return True, f"Metadata updated for {agent_id}"
        except Exception as e:
            logger.error(f"❌ Error updating metadata: {e}")
            return False, str(e)

    def get_agent_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about registered agents.

        Returns:
            Statistics dict
        """
        agents = self.registry.agents.values()
        online_agents = [a for a in agents if a.status == "registered"]
        degraded_agents = [a for a in agents if a.status == "degraded"]

        return {
            "total_agents": len(agents),
            "online_agents": len(online_agents),
            "degraded_agents": len(degraded_agents),
            "offline_agents": len(agents) - len(online_agents) - len(degraded_agents),
            "total_capabilities": len(self.registry.capability_index),
            "total_requests": sum(a.success_count for a in agents),
            "total_errors": sum(a.error_count for a in agents),
            "agents": {
                a.agent_id: {
                    "status": a.status,
                    "success_count": a.success_count,
                    "error_count": a.error_count,
                    "success_rate": (
                        a.success_count / (a.success_count + a.error_count)
                        if (a.success_count + a.error_count) > 0
                        else 0
                    ),
                }
                for a in agents
            },
        }
