"""
Complete example: Agent Registry System demonstration.

Shows:
1. Initialize registry with pre-configured agents
2. Programmatic agent registration
3. Capability-based discovery
4. Health checking
5. Schema validation
6. Statistics and monitoring
7. Adding new agent types
"""

import json
from mcp.agent_registry import AgentRegistry
from mcp.agent_registration_api import AgentRegistrationAPI
from mcp.registry_config import get_default_registry_config
from mcp.models import AgentRecord
from mcp.agent_schemas import validate_input, get_agent_input_schema, get_agent_output_schema


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_1_initialize_registry():
    """Demo 1: Initialize registry with pre-configured agents."""
    print_section("Demo 1: Initialize Registry with Pre-Configured Agents")

    # Create registry
    registry = AgentRegistry()

    # Load default agents from config
    config = get_default_registry_config()
    for agent_dict in config.get("agents", {}).values():
        agent = AgentRecord.from_dict(agent_dict)
        registry.register_agent(agent)

    print(f"\n✅ Loaded {len(registry.agents)} pre-configured agents:")
    for agent_id, agent in registry.agents.items():
        print(f"\n   {agent.name}")
        print(f"   ID: {agent_id}")
        print(f"   Endpoint: {agent.endpoint}")
        print(f"   Status: {agent.status}")
        print(f"   Priority: {agent.priority}")
        print(f"   Capabilities: {len(agent.capabilities)}")
        for cap in agent.capabilities:
            print(f"     - {cap.action}: {cap.description}")

    return registry


def demo_2_agent_registration_api(registry):
    """Demo 2: Use AgentRegistrationAPI for registration and discovery."""
    print_section("Demo 2: Agent Registration API")

    api = AgentRegistrationAPI(registry)

    # 2a: Register a new agent
    print("\n📝 Registering new 'Analytics Agent'...")
    success, message = api.register_agent(
        agent_id="analytics-agent",
        name="Analytics Agent",
        endpoint="http://127.0.0.1:8003",
        capabilities=[
            {
                "action": "analytics.query",
                "description": "Query analytics database",
                "sample_inputs": ["How many users last week?", "Top features used"],
                "required_fields": ["text"],
            },
            {
                "action": "analytics.report",
                "description": "Generate analytics report",
                "sample_inputs": ["Monthly usage report"],
                "required_fields": ["report_type"],
            },
        ],
        metadata={
            "cost_estimate": 0.25,
            "team": "analytics",
            "region": "us-west-2",
        },
        priority=60,
    )
    print(f"   {message}")

    # 2b: Find agents by capability
    print("\n🔍 Finding agents that can perform 'document.review'...")
    agents = api.find_agents_by_capability("document.review")
    print(f"   Found {len(agents)} agent(s):")
    for agent in agents:
        print(f"   - {agent.name} (priority: {agent.priority})")

    print("\n🔍 Finding agents that can perform 'analytics.query'...")
    agents = api.find_agents_by_capability("analytics.query")
    print(f"   Found {len(agents)} agent(s):")
    for agent in agents:
        print(f"   - {agent.name} (priority: {agent.priority})")

    # 2c: Find agents by name substring
    print("\n🔍 Finding agents with 'support' in name...")
    agents = api.find_agents_by_name("support")
    print(f"   Found {len(agents)} agent(s):")
    for agent in agents:
        print(f"   - {agent.name}")

    return api


def demo_3_list_all_capabilities(api):
    """Demo 3: List all capabilities across all agents."""
    print_section("Demo 3: List All Capabilities")

    capabilities = api.list_all_capabilities()

    print(f"\n📚 Available capabilities ({len(capabilities)} total):\n")
    for action, agents in sorted(capabilities.items()):
        print(f"   {action}:")
        for agent_info in agents:
            print(f"     └─ {agent_info['agent_name']} (priority: {agent_info['priority']})")


def demo_4_agent_health(api):
    """Demo 4: Check agent health."""
    print_section("Demo 4: Agent Health Checking")

    # Check all agents
    print("\n🏥 Checking health of all agents...\n")
    results = api.health_check_all()

    for agent_id, is_healthy in results.items():
        status = "🟢 ONLINE" if is_healthy else "🔴 OFFLINE"
        print(f"   {status}  {agent_id}")


def demo_5_agent_details(api):
    """Demo 5: Get detailed agent information."""
    print_section("Demo 5: Detailed Agent Information")

    agent_id = "document-review-agent"
    print(f"\n📋 Details for '{agent_id}':\n")

    info = api.get_agent_info(agent_id)
    if not info:
        print(f"   Agent {agent_id} not found")
        return

    print(f"   Name: {info['name']}")
    print(f"   Endpoint: {info['endpoint']}")
    print(f"   Status: {info['status']}")
    print(f"   Priority: {info['priority']}")
    print(f"   Version: {info['version']}")

    print(f"\n   🎯 Capabilities:")
    for cap in info['capabilities']:
        print(f"\n      {cap['action']}")
        print(f"      Description: {cap['description']}")
        if cap.get('sample_inputs'):
            print(f"      Sample inputs: {', '.join(cap['sample_inputs'][:2])}")
        if cap.get('required_fields'):
            print(f"      Required fields: {', '.join(cap['required_fields'])}")

    print(f"\n   ⚙️  SLA:")
    for key, value in info['sla'].items():
        print(f"      {key}: {value}")

    print(f"\n   📊 Health:")
    for key, value in info['health'].items():
        print(f"      {key}: {value}")


def demo_6_list_all_agents(api):
    """Demo 6: List all registered agents."""
    print_section("Demo 6: List All Agents")

    agents = api.list_all_agents()

    print(f"\n📦 Registered agents ({len(agents)} total):\n")
    for i, agent in enumerate(agents, 1):
        print(f"   {i}. {agent['name']}")
        print(f"      ID: {agent['agent_id']}")
        print(f"      Endpoint: {agent['endpoint']}")
        print(f"      Status: {agent['status']}")
        print(f"      Capabilities: {len(agent['capabilities'])}")
        print()


def demo_7_input_validation():
    """Demo 7: Input schema validation."""
    print_section("Demo 7: Input Schema Validation")

    # Test case 1: Valid input
    print("\n✅ Test 1: Valid input for 'document.review'")
    payload = {
        "text": "Please review this contract for compliance",
        "review_type": "compliance",
    }
    is_valid, errors = validate_input("document.review", payload)
    print(f"   Validation result: {is_valid}")
    if errors:
        print(f"   Errors: {errors}")

    # Test case 2: Missing required field
    print("\n❌ Test 2: Missing required field 'text'")
    payload = {"review_type": "compliance"}
    is_valid, errors = validate_input("document.review", payload)
    print(f"   Validation result: {is_valid}")
    if errors:
        for error in errors:
            print(f"   - {error}")

    # Test case 3: Wrong field type
    print("\n❌ Test 3: Wrong field type (text should be string, not integer)")
    payload = {"text": 123}
    is_valid, errors = validate_input("document.review", payload)
    print(f"   Validation result: {is_valid}")
    if errors:
        for error in errors:
            print(f"   - {error}")

    # Test case 4: Valid IT support request
    print("\n✅ Test 4: Valid input for 'it.support.text'")
    payload = {
        "text": "My VPN is not working",
        "category_hint": "Network",
    }
    is_valid, errors = validate_input("it.support.text", payload)
    print(f"   Validation result: {is_valid}")
    if errors:
        print(f"   Errors: {errors}")


def demo_8_schema_inspection():
    """Demo 8: Inspect input/output schemas."""
    print_section("Demo 8: Schema Inspection")

    # Get document review input schema
    print("\n📋 Input Schema for 'document.review':\n")
    input_schema = get_agent_input_schema("document.review")
    if input_schema:
        schema_dict = input_schema.to_dict()
        print(f"   Required fields: {schema_dict['required_fields']}")
        print(f"\n   Field definitions:")
        for field_name, field_def in schema_dict['schema'].items():
            print(f"     {field_name}:")
            print(f"       Type: {field_def['type']}")
            print(f"       Description: {field_def['description']}")

    # Get document review output schema
    print("\n📋 Output Schema for 'document.review':\n")
    output_schema = get_agent_output_schema("document.review")
    if output_schema:
        schema_dict = output_schema.to_dict()
        print(f"   Status codes:")
        for code, desc in schema_dict['status_codes'].items():
            print(f"     {code}: {desc}")
        print(f"\n   Response fields:")
        for field_name in list(schema_dict['schema'].keys())[:3]:
            field_def = schema_dict['schema'][field_name]
            print(f"     {field_name}: {field_def['type']} - {field_def['description']}")


def demo_9_statistics(api):
    """Demo 9: Agent statistics and monitoring."""
    print_section("Demo 9: Statistics & Monitoring")

    stats = api.get_agent_statistics()

    print(f"\n📊 Registry Statistics:\n")
    print(f"   Total agents: {stats['total_agents']}")
    print(f"   Online agents: {stats['online_agents']}")
    print(f"   Degraded agents: {stats['degraded_agents']}")
    print(f"   Offline agents: {stats['offline_agents']}")
    print(f"   Total capabilities: {stats['total_capabilities']}")
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Total errors: {stats['total_errors']}")

    if stats['total_requests'] > 0:
        success_rate = (stats['total_requests'] - stats['total_errors']) / stats['total_requests']
        print(f"   Overall success rate: {success_rate:.1%}")

    print(f"\n   Per-Agent Statistics:")
    for agent_id, agent_stats in stats['agents'].items():
        print(f"\n   {agent_id}:")
        print(f"     Status: {agent_stats['status']}")
        print(f"     Success rate: {agent_stats['success_rate']:.1%}")
        print(f"     Successes: {agent_stats['success_count']}")
        print(f"     Errors: {agent_stats['error_count']}")


def demo_10_metadata_update(api):
    """Demo 10: Update agent metadata."""
    print_section("Demo 10: Update Agent Metadata")

    print("\n📝 Updating metadata for 'support-agent'...\n")

    new_metadata = {
        "sla_violation_count": 2,
        "last_maintenance": "2026-03-30T10:00:00Z",
        "regions": ["us-east-1", "us-west-2", "eu-west-1"],
    }

    success, message = api.update_agent_metadata("support-agent", new_metadata)
    print(f"   {message}")

    # Show updated metadata
    info = api.get_agent_info("support-agent")
    print(f"\n   Updated metadata:")
    for key, value in info['metadata'].items():
        print(f"     {key}: {value}")


def demo_11_agent_capabilities_example(api):
    """Demo 11: Demonstrate capability matching in action."""
    print_section("Demo 11: Capability Matching Example")

    # Scenario: Different requests matched to different agents
    scenarios = [
        ("Please review this NDA for data protection clauses", "document.review"),
        ("My password isn't working", "it.support.text"),
        ("I need help with Excel", "it.support.text"),
        ("Analyze this contract", "document.analyze"),
    ]

    print("\n🎯 Request-to-Agent Matching:\n")
    for request_text, expected_action in scenarios:
        print(f"   Request: \"{request_text}\"")
        print(f"   Intent: {expected_action}")

        agents = api.find_agents_by_capability(expected_action)
        if agents:
            selected = agents[0]  # Highest priority
            print(f"   Selected: {selected.name} (priority: {selected.priority})")
        else:
            print(f"   Selected: NO AGENT AVAILABLE")
        print()


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  AGENT REGISTRY SYSTEM: COMPLETE DEMONSTRATION".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    # Run demos
    registry = demo_1_initialize_registry()
    api = demo_2_agent_registration_api(registry)
    demo_3_list_all_capabilities(api)
    demo_4_agent_health(api)
    demo_5_agent_details(api)
    demo_6_list_all_agents(api)
    demo_7_input_validation()
    demo_8_schema_inspection()
    demo_9_statistics(api)
    demo_10_metadata_update(api)
    demo_11_agent_capabilities_example(api)

    # Summary
    print_section("Summary")
    print("""
✅ Agent Registry System Features Demonstrated:

1. ✓ Initialize registry with pre-configured agents
2. ✓ Programmatic agent registration
3. ✓ List all capabilities across agents
4. ✓ Health checking and monitoring
5. ✓ Get detailed agent information
6. ✓ Find agents by capability (capability-based routing)
7. ✓ Input schema validation
8. ✓ Schema inspection and documentation
9. ✓ Statistics and metrics collection
10. ✓ Agent metadata updates
11. ✓ Capability matching in action

The Agent Registry System is now:
  🎯 Ready for intelligent agent discovery
  🎯 Prepared for capability-based routing
  🎯 Equipped with schema validation
  🎯 Able to track health and performance
  🎯 Extensible for new agent types

Next steps:
  1. Integrate into MCP decision engine
  2. Update agent endpoints with /invoke
  3. Deploy agents with /health endpoints
  4. Monitor statistics in production

""")


if __name__ == "__main__":
    main()
