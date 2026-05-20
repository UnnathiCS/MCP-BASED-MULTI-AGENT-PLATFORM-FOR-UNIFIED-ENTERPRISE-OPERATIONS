from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class Milestone(BaseModel):
    id: str
    name: str
    due_date: str
    status: str  # on_track, at_risk, completed
    completion_percentage: float
    dependencies: List[str] = []

class TeamMember(BaseModel):
    id: str
    name: str
    email: str
    role: str
    allocation_percentage: float

class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = "Project description not available"
    manager_id: Optional[str] = None
    status: str = "planning"  # planning, active, on_hold, completed
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: Optional[float] = 0.0
    team_members: List[str] = []
    milestones: List[Milestone] = []
    progress_percentage: Optional[float] = 0.0

class AgentRequest(BaseModel):
    user_request: str
    intent: str
    context: Optional[Dict[str, Any]] = None

class ProjectResponse(BaseModel):
    status: str
    decision: str
    project_data: Optional[Project] = None
    projects_list: Optional[List[Project]] = None
    milestone_updates: Optional[List[Dict]] = None
    resource_allocation: Optional[Dict] = None
    risk_assessment: Optional[Dict] = None
    next_steps: List[str]
    recommendations: List[str] = []
    scheduled_meetings: List[Dict[str, Any]] = []
