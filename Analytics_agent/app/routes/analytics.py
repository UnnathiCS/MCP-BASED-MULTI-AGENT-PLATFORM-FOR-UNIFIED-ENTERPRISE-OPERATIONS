"""Analytics Routes"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from ..schemas import AgentRequest, AnalyticsResponse
from ..services.analytics_service import AnalyticsService
import asyncio

router = APIRouter(prefix="/analytics", tags=["analytics"])
agent_router = APIRouter(prefix="/agent", tags=["agent"])

@router.get("/health")
async def health_check():
    """Check health of all agents"""
    overview = AnalyticsService.get_system_overview()
    return {
        "status": "success",
        "system": overview
    }

@router.get("/dashboard")
async def get_dashboard():
    """Get main dashboard"""
    dashboard = AnalyticsService.get_dashboard_data()
    return {
        "status": "success",
        "dashboard": dashboard
    }

@router.get("/agents")
async def get_agent_stats():
    """Get statistics for all agents"""
    stats = AnalyticsService.collect_agent_stats()
    return {
        "status": "success",
        "agents": stats
    }

@router.get("/insights")
async def get_insights():
    """Get system insights"""
    insights = AnalyticsService.generate_insights()
    return {
        "status": "success",
        "insights": insights
    }

@router.get("/trends")
async def get_trends():
    """Get performance trends"""
    trends = AnalyticsService.get_performance_trends()
    return {
        "status": "success",
        "trends": trends
    }

@router.get("/multi-agent-workflow")
async def get_workflow():
    """Get multi-agent workflow metrics"""
    workflow = AnalyticsService.query_multi_agent_workflow()
    return {
        "status": "success",
        "workflow": workflow
    }

@agent_router.post("/orchestrate")
async def orchestrate_analytics(request: AgentRequest) -> AnalyticsResponse:
    """
    Main MCP orchestration endpoint for analytics
    Aggregates and analyzes metrics from all agents
    """
    
    request_lower = request.user_request.lower()
    
    try:
        if any(word in request_lower for word in ["dashboard", "overview", "summary"]):
            dashboard = AnalyticsService.get_dashboard_data()
            insights = AnalyticsService.generate_insights()
            
            return AnalyticsResponse(
                status="success",
                decision="dashboard_generated",
                dashboard={
                    "timestamp": dashboard["timestamp"],
                    "agent_metrics": [
                        {
                            "agent_name": m["agent_name"],
                            "requests_processed": m["requests_processed"],
                            "avg_response_time": m["avg_response_time"],
                            "success_rate": m["success_rate"],
                            "last_updated": m["last_updated"]
                        }
                        for m in dashboard["agent_metrics"]
                    ],
                    "system_metrics": {
                        "total_agents": dashboard["system_metrics"]["total_agents"],
                        "active_agents": dashboard["system_metrics"]["active_agents"],
                        "total_requests": dashboard["system_metrics"]["total_requests"],
                        "system_health": dashboard["system_metrics"]["system_health"]
                    }
                },
                insights=insights,
                recommendations=[
                    "Monitor agent performance trends",
                    "Scale resources for high-load agents",
                    "Review failed requests"
                ]
            )
        
        elif any(word in request_lower for word in ["performance", "trends", "metrics"]):
            trends = AnalyticsService.get_performance_trends()
            stats = AnalyticsService.collect_agent_stats()
            
            return AnalyticsResponse(
                status="success",
                decision="performance_report",
                agent_performance={
                    "busiest": trends["busiest_agent"],
                    "fastest": trends["fastest_agent"],
                    "most_reliable": trends["most_reliable"],
                    "slowest": trends["slowest_agent"]
                },
                trends=trends,
                insights=AnalyticsService.generate_insights(),
                recommendations=[
                    f"Busiest agent: {trends['busiest_agent']} - consider load balancing",
                    f"Fastest agent: {trends['fastest_agent']} - good performance",
                    "Focus on improving slowest agent response time"
                ]
            )
        
        elif any(word in request_lower for word in ["workflow", "multi-agent", "orchestration", "integration"]):
            workflow = AnalyticsService.query_multi_agent_workflow()
            multi_insights = AnalyticsService.get_multi_agent_insights()
            
            return AnalyticsResponse(
                status="success",
                decision="multi_agent_workflow",
                metrics=workflow,
                insights=multi_insights,
                recommendations=[
                    "Multi-agent integration working smoothly",
                    "All agents communicating successfully",
                    "Data flowing correctly between agents",
                    "Consider adding more workflows for other use cases"
                ]
            )
        
        elif any(word in request_lower for word in ["health", "status", "system"]):
            system = AnalyticsService.get_system_overview()
            stats = AnalyticsService.collect_agent_stats()
            
            return AnalyticsResponse(
                status="success",
                decision="system_status",
                metrics=system,
                insights=[
                    f"System Status: {system['system_status']}",
                    f"Agents Active: {system['healthy_agents']}/{system['total_agents']}",
                    f"System Uptime: {system['uptime_percentage']:.1f}%"
                ],
                recommendations=[
                    "All agents operational" if system["unhealthy_agents"] == 0 else "Check unhealthy agents"
                ]
            )
        
        else:
            # Default: return full dashboard
            dashboard = AnalyticsService.get_dashboard_data()
            return AnalyticsResponse(
                status="success",
                decision="analytics_query",
                metrics=dashboard,
                insights=AnalyticsService.generate_insights(),
                recommendations=[
                    "Review dashboard for system overview",
                    "Check performance trends"
                ]
            )
    
    except Exception as e:
        return AnalyticsResponse(
            status="error",
            decision="analytics_failed",
            insights=[f"Error: {str(e)}"],
            recommendations=["Check request format"]
        )
