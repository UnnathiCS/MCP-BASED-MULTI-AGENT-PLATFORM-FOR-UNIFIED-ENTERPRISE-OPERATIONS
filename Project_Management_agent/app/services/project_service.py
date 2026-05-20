"""Project Management Service"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .dummy_db import db

class ProjectService:
    """Handles all project management logic"""
    
    @staticmethod
    def get_project_overview(project_id: str) -> Optional[Dict]:
        """Get complete project overview"""
        project = db.get_project(project_id)
        if not project:
            return None
        
        status = db.get_project_status(project_id)
        team = db.get_project_team(project_id)
        
        return {
            "project": project,
            "status": status,
            "team": team,
            "next_milestone": next((m for m in project["milestones"] if m["status"] != "completed"), None)
        }
    
    @staticmethod
    def get_all_projects_summary() -> Dict:
        """Get summary of all projects"""
        all_projects = db.get_all_projects()
        
        active = [p for p in all_projects if p["status"] == "active"]
        planning = [p for p in all_projects if p["status"] == "planning"]
        completed = [p for p in all_projects if p["status"] == "completed"]
        
        total_budget = sum(p["budget"] for p in all_projects)
        avg_progress = sum(p["progress_percentage"] for p in all_projects) / len(all_projects) if all_projects else 0
        
        return {
            "total_projects": len(all_projects),
            "active_projects": len(active),
            "planning_projects": len(planning),
            "completed_projects": len(completed),
            "total_budget": total_budget,
            "average_progress": avg_progress,
            "projects": [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "status": p["status"],
                    "progress": p["progress_percentage"],
                    "team_size": len(p["team_members"])
                }
                for p in all_projects
            ]
        }
    
    @staticmethod
    def get_at_risk_projects() -> List[Dict]:
        """Get projects with at-risk milestones"""
        all_projects = db.get_all_projects()
        at_risk_projects = []
        
        for project in all_projects:
            at_risk_milestones = [m for m in project["milestones"] if m["status"] == "at_risk"]
            if at_risk_milestones:
                at_risk_projects.append({
                    "project_id": project["id"],
                    "project_name": project["name"],
                    "status": project["status"],
                    "at_risk_count": len(at_risk_milestones),
                    "at_risk_milestones": at_risk_milestones,
                    "manager_id": project["manager_id"],
                    "recommended_actions": [
                        "Increase resource allocation",
                        "Review milestone dependencies",
                        "Identify blockers and risks"
                    ]
                })
        
        return at_risk_projects
    
    @staticmethod
    def get_upcoming_milestones(days: int = 30) -> List[Dict]:
        """Get milestones due within specified days"""
        all_projects = db.get_all_projects()
        upcoming = []
        current_date = datetime.strptime("2026-04-15", "%Y-%m-%d")  # Use today's date
        cutoff_date = current_date + timedelta(days=days)
        
        for project in all_projects:
            for milestone in project["milestones"]:
                if milestone["status"] != "completed":
                    due = datetime.strptime(milestone["due_date"], "%Y-%m-%d")
                    if current_date <= due <= cutoff_date:
                        upcoming.append({
                            "project_id": project["id"],
                            "project_name": project["name"],
                            "milestone_id": milestone["id"],
                            "milestone_name": milestone["name"],
                            "due_date": milestone["due_date"],
                            "days_until_due": (due - current_date).days,
                            "completion": milestone["completion_percentage"],
                            "status": milestone["status"]
                        })
        
        return sorted(upcoming, key=lambda x: x["days_until_due"])
    
    @staticmethod
    def get_resource_utilization() -> Dict:
        """Get team resource utilization"""
        all_projects = db.get_all_projects()
        utilization = {}
        
        for project in all_projects:
            team = db.get_project_team(project["id"])
            for member in team:
                if member["id"] not in utilization:
                    utilization[member["id"]] = {
                        "name": member["name"],
                        "projects": [],
                        "total_allocation": 0
                    }
                
                allocation = db.resource_allocation.get(project["id"], {}).get("team_allocation", {}).get(member["id"], 0)
                if allocation > 0:
                    utilization[member["id"]]["projects"].append({
                        "project_id": project["id"],
                        "project_name": project["name"],
                        "allocation": allocation
                    })
                    utilization[member["id"]]["total_allocation"] += allocation
        
        return {
            "team_utilization": utilization,
            "overallocated_members": [
                {
                    "member_id": emp_id,
                    "name": data["name"],
                    "total_allocation": data["total_allocation"],
                    "projects": data["projects"]
                }
                for emp_id, data in utilization.items()
                if data["total_allocation"] > 100
            ]
        }
    
    @staticmethod
    def complete_milestone(project_id: str, milestone_id: str) -> Dict:
        """Mark milestone as completed"""
        success = db.update_milestone(project_id, milestone_id, "completed", 100.0)
        
        if success:
            project = db.get_project(project_id)
            return {
                "success": True,
                "message": f"Milestone {milestone_id} marked as completed",
                "project_id": project_id,
                "next_milestone": next(
                    (m for m in project["milestones"] if m["status"] != "completed"),
                    None
                )
            }
        
        return {"success": False, "message": "Could not update milestone"}
    
    @staticmethod
    def update_milestone_status(project_id: str, milestone_id: str, status: str, completion: float) -> Dict:
        """Update milestone status and completion"""
        success = db.update_milestone(project_id, milestone_id, status, completion)
        
        if success:
            return {
                "success": True,
                "message": f"Milestone updated: {status} ({completion}%)",
                "project_id": project_id
            }
        
        return {"success": False, "message": "Could not update milestone"}
    
    @staticmethod
    def generate_status_report() -> Dict:
        """Generate comprehensive project status report"""
        summary = ProjectService.get_all_projects_summary()
        at_risk = ProjectService.get_at_risk_projects()
        upcoming = ProjectService.get_upcoming_milestones(30)
        resources = ProjectService.get_resource_utilization()
        
        return {
            "report_date": "2026-04-15",
            "summary": summary,
            "at_risk_projects": at_risk,
            "upcoming_milestones": upcoming,
            "resource_utilization": resources,
            "key_metrics": {
                "overall_progress": summary["average_progress"],
                "on_time_percentage": (1 - len(at_risk) / summary["total_projects"] * 100) if summary["total_projects"] > 0 else 100,
                "resource_efficiency": 85.5
            }
        }
