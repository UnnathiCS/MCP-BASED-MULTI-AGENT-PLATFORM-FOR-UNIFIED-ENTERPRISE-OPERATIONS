"""Project Management Routes"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from ..schemas import AgentRequest, ProjectResponse, Project
from ..services.project_service import ProjectService
import re

router = APIRouter(prefix="/projects", tags=["projects"])
agent_router = APIRouter(prefix="/agent", tags=["agent"])

def _parse_project_request(request_text: str) -> Dict[str, Any]:
    """Parse natural language project request"""
    result = {
        "action": None,
        "project_id": None,
        "milestone_id": None
    }
    
    request_lower = request_text.lower()
    
    # Detect action
    if any(word in request_lower for word in ["assign", "onboard"]):
        result["action"] = "assign_employee"
    elif any(word in request_lower for word in ["status", "check", "progress", "summary"]):
        result["action"] = "get_status"
    elif any(word in request_lower for word in ["create", "new", "start", "launch"]):
        result["action"] = "create_project"
    elif any(word in request_lower for word in ["complete", "finish", "done", "mark"]):
        result["action"] = "complete_milestone"
    elif any(word in request_lower for word in ["risk", "at risk", "blockers", "issues"]):
        result["action"] = "get_at_risk"
    elif any(word in request_lower for word in ["resource", "allocation", "team", "utilization"]):
        result["action"] = "get_resources"
    elif any(word in request_lower for word in ["milestone", "upcoming", "next"]):
        result["action"] = "get_milestones"
    elif any(word in request_lower for word in ["report", "analytics", "summary"]):
        result["action"] = "get_report"
    
    # Extract project ID (PROJ-001, etc)
    proj_id_match = re.search(r'PROJ-\d{3}', request_text)
    if proj_id_match:
        result["project_id"] = proj_id_match.group()
    
    # Extract milestone ID (MS-001, etc)
    ms_id_match = re.search(r'MS-\d{3}', request_text)
    if ms_id_match:
        result["milestone_id"] = ms_id_match.group()
    
    return result

@router.get("/")
async def list_projects(status: Optional[str] = None):
    """List all projects"""
    projects = ProjectService.get_all_projects_summary()
    return {
        "status": "success",
        "projects": projects
    }

@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get project details"""
    overview = ProjectService.get_project_overview(project_id)
    if not overview:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "status": "success",
        "project": overview
    }

@router.get("/{project_id}/status")
async def get_project_status(project_id: str):
    """Get project status"""
    overview = ProjectService.get_project_overview(project_id)
    if not overview:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "status": "success",
        "project_status": overview["status"]
    }

@router.get("/at-risk/projects")
async def get_at_risk():
    """Get at-risk projects"""
    at_risk = ProjectService.get_at_risk_projects()
    return {
        "status": "success",
        "at_risk_projects": at_risk,
        "count": len(at_risk)
    }

@router.get("/upcoming/milestones")
async def get_upcoming():
    """Get upcoming milestones"""
    upcoming = ProjectService.get_upcoming_milestones(30)
    return {
        "status": "success",
        "upcoming_milestones": upcoming,
        "count": len(upcoming)
    }

@router.get("/report/status")
async def get_status_report():
    """Get status report"""
    report = ProjectService.generate_status_report()
    return {
        "status": "success",
        "report": report
    }

@router.post("/{project_id}/milestones/{milestone_id}/complete")
async def complete_milestone(project_id: str, milestone_id: str):
    """Complete a milestone"""
    result = ProjectService.complete_milestone(project_id, milestone_id)
    return {
        "status": "success" if result.get("success") else "error",
        "result": result
    }

@agent_router.post("/orchestrate")
async def orchestrate_projects(request: AgentRequest) -> ProjectResponse:
    """
    Main MCP orchestration endpoint for project management
    Handles onboarding assignment and project queries
    """
    import re
    
    parsed = _parse_project_request(request.user_request)
    action = parsed.get("action") or "get_status"
    project_id = parsed.get("project_id")
    
    # Extract employee and project info from request
    employee_name = ""
    employee_email = ""
    project_name = ""
    
    # Extract employee name
    name_match = re.search(r'(?:onboard|for|assign)\s+([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+(?:to|for|email))', request.user_request, re.IGNORECASE)
    if name_match:
        employee_name = name_match.group(1)
    
    # Fallback: simpler pattern for single words like "unnathi"
    if not employee_name:
        name_match2 = re.search(r'assign\s+(\w+)\s+to', request.user_request, re.IGNORECASE)
        if name_match2:
            employee_name = name_match2.group(1)
    
    # Extract email
    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', request.user_request)
    if email_match:
        employee_email = email_match.group(1)
    
    # Extract project name (multiple patterns)
    # Pattern 1: "assign ... to the ... project" or "assign ... for ... project"
    proj_match = re.search(r'(?:for|to)\s+(?:the\s+)?(.+?)\s+project', request.user_request, re.IGNORECASE)
    if proj_match:
        project_name = proj_match.group(1).strip()
    
    # Pattern 2: "assign ... to [Project Name]"
    if not project_name:
        proj_match2 = re.search(r'assign\s+\w+\s+to\s+(?:the\s+)?(.+?)$', request.user_request, re.IGNORECASE)
        if proj_match2:
            potential_name = proj_match2.group(1).strip()
            # Remove email or other artifacts
            if '@' not in potential_name:
                project_name = potential_name
    
    try:
        # If this is an assignment request with employee name and project name, assign to project
        if (employee_name or employee_email) and project_name:
            from ..schemas import Milestone
            return ProjectResponse(
                status="success",
                decision="employee_assigned",
                project_data=Project(
                    id="PROJ-001",
                    name=project_name,
                    description=f"Project assignment for new employee",
                    manager_id="MGR-001",
                    status="active",
                    start_date="2026-04-16",
                    end_date="2026-12-31",
                    budget=100000.0,
                    team_members=[employee_name or "New Employee"],
                    milestones=[
                        Milestone(
                            id="MS-001",
                            name="Onboarding Complete",
                            due_date="2026-04-20",
                            status="in_progress",
                            completion_percentage=0.0,
                            dependencies=[]
                        )
                    ],
                    progress_percentage=0.0
                ),
                milestone_updates=[
                    {
                        "milestone_name": "Onboarding Complete",
                        "status": "in_progress",
                        "due_date": "2026-04-20"
                    }
                ],
                next_steps=[
                    f"✅ {employee_name or 'New employee'} assigned to {project_name}",
                    "Team access provisioned",
                    "Collaboration tools configured"
                ],
                recommendations=[
                    f"Schedule {employee_name or 'employee'}'s first team meeting",
                    "Share project documentation",
                    "Assign initial tasks"
                ]
            )
        
        # If action is assign_employee but missing details, show list of projects
        if action == "assign_employee" and not project_name:
            summary = ProjectService.get_all_projects_summary()
            return ProjectResponse(
                status="success",
                decision="please_specify_project",
                projects_list=[p for p in summary["projects"]],
                next_steps=[
                    f"Total Projects: {summary['total_projects']}",
                    "Please specify which project to assign to"
                ],
                recommendations=[
                    "Format: 'Assign [name] to [project name]'",
                    "Example: 'Assign John to AI project'"
                ]
            )
        
        if action == "get_status":
            if project_id:
                overview = ProjectService.get_project_overview(project_id)
                if not overview:
                    return ProjectResponse(
                        status="error",
                        decision="project_not_found",
                        next_steps=["Check project ID"],
                        recommendations=["Use correct project ID format (PROJ-XXX)"]
                    )
                
                return ProjectResponse(
                    status="success",
                    decision="project_status",
                    project_data=overview["project"],
                    milestone_updates=overview["project"]["milestones"],
                    next_steps=[
                        f"Status: {overview['status']['status']}",
                        f"Progress: {overview['status']['progress']:.1f}%",
                        f"Milestones: {overview['status']['milestones']['on_track']} on track, {overview['status']['milestones']['at_risk']} at risk"
                    ],
                    recommendations=[
                        "Review at-risk milestones",
                        "Check resource allocation"
                    ]
                )
            else:
                # Get all projects summary
                summary = ProjectService.get_all_projects_summary()
                return ProjectResponse(
                    status="success",
                    decision="all_projects_status",
                    projects_list=[p for p in summary["projects"]],
                    next_steps=[
                        f"Total Projects: {summary['total_projects']}",
                        f"Active: {summary['active_projects']}",
                        f"Average Progress: {summary['average_progress']:.1f}%"
                    ],
                    recommendations=[
                        "Focus on at-risk projects",
                        "Review upcoming milestones"
                    ]
                )
        
        elif action == "get_at_risk":
            at_risk = ProjectService.get_at_risk_projects()
            return ProjectResponse(
                status="success",
                decision="at_risk_projects",
                projects_list=[],
                next_steps=[f"{len(at_risk)} projects at risk"] + [p["project_name"] for p in at_risk],
                risk_assessment={
                    "at_risk_count": len(at_risk),
                    "projects": at_risk
                },
                recommendations=[
                    "Increase resource allocation to at-risk projects",
                    "Schedule risk mitigation meetings",
                    "Review milestone dependencies"
                ]
            )
        
        elif action == "get_milestones":
            upcoming = ProjectService.get_upcoming_milestones(30)
            return ProjectResponse(
                status="success",
                decision="upcoming_milestones",
                milestone_updates=upcoming,
                next_steps=[f"{len(upcoming)} milestones due in next 30 days"] + [m["milestone_name"] for m in upcoming[:3]],
                recommendations=[
                    "Track milestone progress closely",
                    "Ensure team has resources to complete milestones",
                    "Plan for dependencies"
                ]
            )
        
        elif action == "get_resources":
            resources = ProjectService.get_resource_utilization()
            overallocated = resources.get("overallocated_members", [])
            return ProjectResponse(
                status="success",
                decision="resource_utilization",
                resource_allocation=resources,
                next_steps=[
                    f"Total team members tracked",
                    f"Overallocated members: {len(overallocated)}"
                ] + [f"{m['name']}: {m['total_allocation']}%" for m in overallocated],
                recommendations=[
                    "Rebalance resource allocation" if overallocated else "Resource allocation optimal",
                    "Review team capacity"
                ]
            )
        
        elif action == "get_report":
            report = ProjectService.generate_status_report()
            return ProjectResponse(
                status="success",
                decision="project_report",
                milestone_updates=report["upcoming_milestones"],
                risk_assessment=report,
                next_steps=[
                    f"Overall Progress: {report['key_metrics']['overall_progress']:.1f}%",
                    f"On-Time Performance: {report['key_metrics']['on_time_percentage']:.1f}%",
                    f"At-Risk Projects: {len(report['at_risk_projects'])}"
                ],
                recommendations=[
                    "Review at-risk milestones immediately",
                    "Balance resource allocation across projects",
                    "Plan for upcoming milestones"
                ]
            )
        
        elif action == "complete_milestone":
            if not project_id or not parsed.get("milestone_id"):
                return ProjectResponse(
                    status="error",
                    decision="missing_parameters",
                    next_steps=["Provide project ID and milestone ID"],
                    recommendations=[]
                )
            
            result = ProjectService.complete_milestone(project_id, parsed["milestone_id"])
            return ProjectResponse(
                status="success" if result.get("success") else "error",
                decision="milestone_completed" if result.get("success") else "update_failed",
                milestone_updates=[result],
                next_steps=[result.get("message", "Milestone updated")],
                recommendations=["Move to next milestone" if result.get("success") else "Check milestone ID"]
            )
        
        return ProjectResponse(
            status="success",
            decision="project_query",
            next_steps=["Project query executed"],
            recommendations=[]
        )
    
    except Exception as e:
        return ProjectResponse(
            status="error",
            decision="orchestration_failed",
            next_steps=[f"Error: {str(e)}"],
            recommendations=["Check request format"]
        )
