from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AgentMetrics(BaseModel):
    agent_name: str
    requests_processed: int
    avg_response_time: float
    success_rate: float
    last_updated: Optional[str] = None

class SystemMetrics(BaseModel):
    total_agents: int
    active_agents: int
    total_requests: int
    total_response_time: Optional[float] = 0.0
    system_health: str

class DashboardData(BaseModel):
    timestamp: str
    agent_metrics: List[AgentMetrics]
    system_metrics: SystemMetrics
    top_agents: Optional[List[str]] = []
    alerts: Optional[List[str]] = []

class AgentRequest(BaseModel):
    user_request: str
    intent: str
    context: Optional[Dict[str, Any]] = None

class AnalyticsResponse(BaseModel):
    status: str
    decision: str
    metrics: Optional[Dict[str, Any]] = None
    dashboard: Optional[DashboardData] = None
    insights: List[str] = []
    recommendations: List[str] = []
    agent_performance: Optional[Dict] = None
    trends: Optional[Dict] = None
