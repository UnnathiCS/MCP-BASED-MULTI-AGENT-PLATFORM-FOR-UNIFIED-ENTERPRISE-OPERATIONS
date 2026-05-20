from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class OnboardingTask(BaseModel):
    id: str
    name: str
    description: str
    due_date: str
    status: str  # pending, completed, overdue
    assigned_to: Optional[str] = None

class Employee(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    manager_id: Optional[str] = None
    status: Optional[str] = None  # active, pending_onboarding, completed_onboarding

class OnboardingChecklist(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    role: str
    start_date: str
    tasks: List[OnboardingTask]
    progress_percentage: float
    estimated_completion_date: str

class AgentRequest(BaseModel):
    user_request: str
    intent: str
    context: Optional[Dict[str, Any]] = None

class OnboardingResponse(BaseModel):
    status: str
    decision: str
    employee_data: Optional[Employee] = None
    checklist: Optional[OnboardingChecklist] = None
    next_steps: List[str]
    scheduled_meetings: List[Dict[str, Any]] = []
    recommendations: List[str] = []
