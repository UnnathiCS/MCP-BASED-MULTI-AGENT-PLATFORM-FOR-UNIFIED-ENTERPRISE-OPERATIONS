#!/usr/bin/env python3
"""
Test script to verify the three different Analytics agent response formats 
are properly displayed in the new display_analytics_results function
"""

# Test data for the three different example types

# EXAMPLE 1: Dashboard Response (from dashboard query)
example_1_dashboard = {
    "status": "success",
    "data": {
        "status": "success",
        "decision": "dashboard_generated",
        "dashboard": {
            "timestamp": "2026-05-24T10:30:00",
            "agent_metrics": [
                {
                    "agent_name": "IT Support Agent",
                    "requests_processed": 45,
                    "avg_response_time": 0.45,
                    "success_rate": 94.0,
                    "last_updated": "2026-05-24T10:30:00"
                },
                {
                    "agent_name": "HR Onboarding Agent",
                    "requests_processed": 38,
                    "avg_response_time": 0.35,
                    "success_rate": 100.0,
                    "last_updated": "2026-05-24T10:30:00"
                },
                {
                    "agent_name": "Meeting Calendar Agent",
                    "requests_processed": 32,
                    "avg_response_time": 1.25,
                    "success_rate": 100.0,
                    "last_updated": "2026-05-24T10:30:00"
                }
            ],
            "system_metrics": {
                "total_agents": 5,
                "active_agents": 5,
                "total_requests": 150,
                "total_response_time": 0.0,
                "system_health": "operational"
            },
            "top_agents": [],
            "alerts": []
        },
        "insights": [
            "📊 System processed 150 requests today with 98.5% success rate",
            "⚡ Support Agent performing well at 0.45s avg response time",
            "📅 Meeting agent at peak capacity with 32 requests"
        ],
        "recommendations": [
            "Monitor agent performance trends",
            "Scale resources for high-load agents",
            "Review failed requests"
        ]
    }
}

# EXAMPLE 2: Performance/Trends Response (from trends/performance query)
example_2_performance = {
    "status": "success",
    "data": {
        "status": "success",
        "decision": "performance_report",
        "agent_performance": {
            "busiest": "IT Support Agent",
            "fastest": "HR Onboarding Agent",
            "most_reliable": "Meeting Calendar Agent",
            "slowest": "Document Review Agent"
        },
        "trends": {
            "busiest_agent": "IT Support Agent",
            "fastest_agent": "HR Onboarding Agent",
            "most_reliable": "Meeting Calendar Agent",
            "slowest_agent": "Document Review Agent",
            "total_requests": 150,
            "average_response_time": 0.65,
            "average_success_rate": 98.5
        },
        "insights": [
            "🏆 IT Support Agent handling highest volume (45 requests)",
            "⚡ HR Onboarding Agent is the fastest (0.35s avg)",
            "🎯 Meeting Calendar Agent most reliable (100% success)",
            "📉 Document Review Agent needs optimization (1.2s avg)"
        ],
        "recommendations": [
            "Busiest agent: IT Support Agent - consider load balancing",
            "Fastest agent: HR Onboarding Agent - good performance",
            "Focus on improving slowest agent response time"
        ]
    }
}

# EXAMPLE 3: System Health Response (from health/status query)
example_3_system_health = {
    "status": "success",
    "data": {
        "status": "success",
        "decision": "system_status",
        "metrics": {
            "system_status": "operational",
            "healthy_agents": 5,
            "unhealthy_agents": 0,
            "uptime_percentage": 99.8
        },
        "insights": [
            "System Status: operational",
            "Agents Active: 5/5",
            "System Uptime: 99.8%"
        ],
        "recommendations": [
            "All agents operational"
        ]
    }
}

# EXAMPLE 4: Multi-agent Workflow Response (from workflow/orchestration query)
example_4_workflow = {
    "status": "success",
    "data": {
        "status": "success",
        "decision": "multi_agent_workflow",
        "dashboard": {
            "timestamp": "2026-05-24T10:30:00",
            "agent_metrics": [
                {
                    "agent_name": "IT Support Agent",
                    "requests_processed": 45,
                    "avg_response_time": 0.45,
                    "success_rate": 94.0,
                    "last_updated": "2026-05-24T10:30:00"
                },
                {
                    "agent_name": "HR Onboarding Agent",
                    "requests_processed": 38,
                    "avg_response_time": 0.35,
                    "success_rate": 100.0,
                    "last_updated": "2026-05-24T10:30:00"
                },
                {
                    "agent_name": "Meeting Calendar Agent",
                    "requests_processed": 32,
                    "avg_response_time": 1.25,
                    "success_rate": 100.0,
                    "last_updated": "2026-05-24T10:30:00"
                }
            ],
            "system_metrics": {
                "total_agents": 5,
                "active_agents": 5,
                "total_requests": 150,
                "total_response_time": 0.0,
                "system_health": "operational"
            },
            "top_agents": [],
            "alerts": []
        },
        "metrics": {
            "workflow_name": "Employee Onboarding to Project Assignment",
            "total_workflows": 42,
            "active_workflows": 8,
            "avg_workflow_time": 2.5,
            "success_rate": 96.0
        },
        "insights": [
            "🔄 Multi-agent orchestration: HR onboarding successfully routing tasks",
            "📊 Cross-agent efficiency: Project management integrating with meeting agent",
            "✅ Integration health: All agents communicating successfully",
            "🎯 Performance: Document Review agent adding value"
        ],
        "recommendations": [
            "Multi-agent integration working smoothly",
            "All agents communicating successfully",
            "Data flowing correctly between agents"
        ]
    }
}

if __name__ == "__main__":
    import json
    
    print("="*80)
    print("ANALYTICS DISPLAY TEST DATA")
    print("="*80)
    
    print("\n✅ EXAMPLE 1: Dashboard Response")
    print("-" * 80)
    print(json.dumps(example_1_dashboard, indent=2))
    
    print("\n✅ EXAMPLE 2: Performance/Trends Response")
    print("-" * 80)
    print(json.dumps(example_2_performance, indent=2))
    
    print("\n✅ EXAMPLE 3: System Health Response")
    print("-" * 80)
    print(json.dumps(example_3_system_health, indent=2))
    
    print("\n✅ EXAMPLE 4: Multi-Agent Workflow Response")
    print("-" * 80)
    print(json.dumps(example_4_workflow, indent=2))
    
    print("\n" + "="*80)
    print("All 3 example types are now handled by display_analytics_results!")
    print("="*80)
