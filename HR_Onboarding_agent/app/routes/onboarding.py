"""HR Onboarding Routes"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from ..schemas import AgentRequest, OnboardingResponse, Employee, OnboardingChecklist
from ..services.onboarding_service import OnboardingService, format_date_human_readable, parse_date_to_iso
import re
from datetime import datetime

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
agent_router = APIRouter(prefix="/agent", tags=["agent"])

def _parse_employee_request(request_text: str) -> Dict[str, Any]:
    """Parse natural language request to extract employee info"""
    result = {
        "action": None,
        "employee_id": None,
        "employee_name": None,
        "email": None,
        "department": None,
        "role": None,
        "start_date": None,
        "project": None
    }
    
    request_lower = request_text.lower()
    
    # Detect action
    if any(word in request_lower for word in ["onboard", "start", "new employee", "hire"]):
        result["action"] = "create_onboarding"
    elif any(word in request_lower for word in ["status", "check", "progress"]):
        result["action"] = "get_status"
    elif any(word in request_lower for word in ["complete", "finish", "done", "mark"]):
        result["action"] = "complete_task"
    elif any(word in request_lower for word in ["report", "summary", "analytics"]):
        result["action"] = "get_report"
    elif any(word in request_lower for word in ["mentor", "assign", "buddy"]):
        result["action"] = "get_mentorship"
    
    # Extract employee ID pattern (EMP-001, etc)
    emp_id_match = re.search(r'EMP-\d{3}', request_text)
    if emp_id_match:
        result["employee_id"] = emp_id_match.group()
    
    # Extract email (with or without "email:" prefix)
    email_match = re.search(r'(?:email[:\s]+)?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', request_text)
    if email_match:
        result["email"] = email_match.group(1)
    
    # Extract employee name - look for names before "as", "email", "for"
    name_patterns = [
        r'(?:onboard|hire)\s+([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+(?:email|as|for)|$)',  # Match any case
        r'(?:onboard|hire)\s+([A-Za-z\s]+?)(?:\s+as\s)',  # Before "as"
    ]
    for pattern in name_patterns:
        name_match = re.search(pattern, request_text, re.IGNORECASE)  # Added re.IGNORECASE
        if name_match:
            result["employee_name"] = name_match.group(1).strip()
            break
    
    # Extract role - capture everything after "as a" or "as"
    role_match = re.search(r'\s+as\s+(?:a\s+)?(.+?)(?:\s+for|\s+at|$)', request_text)
    if role_match:
        result["role"] = role_match.group(1).strip()
    
    # Extract department from role or keywords
    departments = ["engineering", "sales", "hr", "finance", "marketing", "operations", "ai", "ml", "data science", "aiml"]
    for dept in departments:
        if dept in request_lower:
            if dept in ["ai", "ml", "aiml"]:
                result["department"] = "Engineering"
            else:
                result["department"] = dept.capitalize()
            break
    
    # Extract project
    project_match = re.search(r'for\s+(?:the\s+)?(.+?)(?:,|\s+starts?|$)', request_text)
    if project_match:
        result["project"] = project_match.group(1).strip()
    
    # Extract start date (more flexible patterns)
    date_patterns = [
        r'(?:starts?|start)\s+(?:at\s+)?(?:on\s+)?(\d{1,2}-\d{1,2}-\d{4})',  # 16-04-2026 or at 16-04-2026
        r'(?:starts?|start)\s+(?:at\s+)?(?:on\s+)?(\d{4}-\d{2}-\d{2})',      # 2026-04-16
        r'(?:starts?|start)\s+(?:at\s+)?(?:on\s+)?(\w+\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?)',  # April 16th, 2026 or April 16th
        r'(?:starts?|start)\s+(?:at\s+)?(?:on\s+)?(\d{1,2}\s+(?:April|May|June|July|August|September|October|November|December))',    # 16 April
    ]
    for pattern in date_patterns:
        date_match = re.search(pattern, request_text, re.IGNORECASE)
        if date_match:
            result["start_date"] = date_match.group(1).strip()
            break
    
    # If no date found, use default (tomorrow)
    if not result["start_date"]:
        from datetime import datetime, timedelta
        tomorrow = datetime.now() + timedelta(days=1)
        result["start_date"] = tomorrow.strftime("%Y-%m-%d")
    
    return result


@router.get("/employees")
async def get_all_employees(status: Optional[str] = None):
    """Get all employees, optionally filtered by status"""
    employees = OnboardingService.get_pending_employees() if status == "pending" else OnboardingService.get_pending_employees()
    return {
        "status": "success",
        "employees": employees,
        "count": len(employees)
    }

@router.get("/employee/{employee_id}")
async def get_employee(employee_id: str):
    """Get employee details"""
    status = OnboardingService.get_onboarding_status(employee_id)
    if not status:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {
        "status": "success",
        "employee": status
    }

@router.post("/checklist/{employee_id}")
async def create_checklist(employee_id: str):
    """Create onboarding checklist for employee"""
    checklist = OnboardingService.create_onboarding_checklist(employee_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {
        "status": "success",
        "checklist": checklist
    }

@router.post("/complete-task")
async def complete_task(employee_id: str, task_id: str):
    """Mark task as completed"""
    result = OnboardingService.complete_onboarding_task(employee_id, task_id)
    return {
        "status": "success" if result.get("success") else "error",
        "result": result
    }

@router.get("/report")
async def get_report():
    """Get onboarding report"""
    report = OnboardingService.generate_onboarding_report()
    return {
        "status": "success",
        "report": report
    }

@router.get("/mentorship/{employee_id}")
async def get_mentorship(employee_id: str):
    """Get mentorship assignments for employee"""
    assignments = OnboardingService.get_mentorship_assignments(employee_id)
    if not assignments:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {
        "status": "success",
        "mentorship": assignments
    }

@agent_router.post("/orchestrate")
async def orchestrate_onboarding(request: AgentRequest) -> OnboardingResponse:
    """
    Main MCP orchestration endpoint for HR onboarding
    Parses natural language and executes onboarding workflows
    """
    
    parsed = _parse_employee_request(request.user_request)
    action = parsed.get("action") or "create_onboarding"
    employee_id = parsed.get("employee_id")
    employee_name = parsed.get("employee_name")
    email = parsed.get("email")
    department = parsed.get("department", "Engineering")
    role = parsed.get("role", "Software Engineer")
    start_date = parsed.get("start_date", "2026-04-16")
    project = parsed.get("project", "AI Project")
    
    try:
        if action == "create_onboarding":
            # If we have employee name and not ID, create new employee
            if not employee_id and employee_name:
                # Parse start date from various formats to YYYY-MM-DD
                start_date = parse_date_to_iso(start_date)
                
                # Create new employee
                employee_id = OnboardingService.create_new_employee(
                    name=employee_name,
                    email=email or f"{employee_name.lower().replace(' ', '.')}@company.com",
                    department=department,
                    role=role,
                    start_date=start_date,
                    project=project
                )
            elif not employee_id:
                # Fall back to first pending employee if no name provided
                pending = OnboardingService.get_pending_employees()
                if pending:
                    employee_id = pending[0]["id"]
                else:
                    return OnboardingResponse(
                        status="error",
                        decision="no_pending_employees",
                        next_steps=["No employees pending onboarding"],
                        recommendations=["Create a new employee record"]
                    )
            
            checklist = OnboardingService.create_onboarding_checklist(employee_id)
            employee = OnboardingService.get_onboarding_status(employee_id)
            
            # Generate mentorship assignments
            mentorship = OnboardingService.get_mentorship_assignments(employee_id)
            
            return OnboardingResponse(
                status="success",
                decision="onboarding_checklist_created",
                employee_data=employee,
                checklist=checklist,
                next_steps=[
                    f"IT Account Setup (Due: {checklist['tasks'][0]['due_date']})",
                    "Schedule Welcome Meeting",
                    "Assign Mentor",
                    "Complete Compliance Training"
                ],
                scheduled_meetings=[
                    {
                        "meeting": "Welcome Meeting with Manager",
                        "attendees": [mentorship["manager_name"]],
                        "suggested_time": "2026-04-15 10:00 AM",
                        "duration": "1 hour"
                    },
                    {
                        "meeting": "Team Introduction",
                        "suggested_time": "2026-04-16 02:00 PM",
                        "duration": "1 hour"
                    }
                ],
                recommendations=[
                    f"Employee will be fully onboarded by {checklist['estimated_completion_date']}",
                    f"Assign mentor from {checklist['tasks'][0]['assigned_to']}",
                    "Schedule all meetings in advance"
                ]
            )
        
        elif action == "get_status":
            if not employee_id:
                pending = OnboardingService.get_pending_employees()
                return OnboardingResponse(
                    status="success",
                    decision="pending_employees_list",
                    next_steps=[f"EMP-{emp['id']} - {emp['name']} ({emp['role']})" for emp in pending],
                    recommendations=["Query specific employee ID for details"]
                )
            
            status = OnboardingService.get_onboarding_status(employee_id)
            if not status:
                return OnboardingResponse(
                    status="error",
                    decision="employee_not_found",
                    next_steps=["Check employee ID"],
                    recommendations=["Use correct employee ID format (EMP-XXX)"]
                )
            
            return OnboardingResponse(
                status="success",
                decision="onboarding_status",
                employee_data=status,
                next_steps=[
                    f"Completed: {status['completed_tasks']} tasks",
                    f"Pending: {status['pending_tasks']} tasks",
                    f"Progress: {status['progress_percentage']:.1f}%"
                ],
                recommendations=[
                    "Follow up on pending tasks",
                    "Schedule overdue task completions" if status['overdue_tasks'] > 0 else "On track for completion"
                ]
            )
        
        elif action == "get_report":
            report = OnboardingService.generate_onboarding_report()
            return OnboardingResponse(
                status="success",
                decision="onboarding_report",
                next_steps=[
                    f"Total Employees: {report['total_employees']}",
                    f"Active: {report['active_employees']}",
                    f"Pending Onboarding: {report['pending_onboarding']}"
                ],
                recommendations=[
                    "Prioritize employees nearing onboarding completion",
                    f"Focus on {report['pending_onboarding']} pending onboardings"
                ]
            )
        
        elif action == "get_mentorship":
            if not employee_id:
                pending = OnboardingService.get_pending_employees()
                if pending:
                    employee_id = pending[0]["id"]
                else:
                    return OnboardingResponse(
                        status="error",
                        decision="no_employees",
                        next_steps=["No employees found"],
                        recommendations=[]
                    )
            
            mentorship = OnboardingService.get_mentorship_assignments(employee_id)
            return OnboardingResponse(
                status="success",
                decision="mentorship_assigned",
                next_steps=[
                    f"Primary Manager: {m['mentor_name']} ({m['role']})" 
                    for m in mentorship.get("mentor_assignments", [])
                ],
                recommendations=[
                    "Notify mentors of their assignments",
                    "Schedule mentorship kick-off meeting"
                ]
            )
        
        return OnboardingResponse(
            status="success",
            decision="onboarding_status",
            next_steps=["Onboarding workflow executed"],
            recommendations=[]
        )
    
    except Exception as e:
        return OnboardingResponse(
            status="error",
            decision="orchestration_failed",
            next_steps=[f"Error: {str(e)}"],
            recommendations=["Check request format and employee data"]
        )
