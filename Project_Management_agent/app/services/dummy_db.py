"""Dummy Project Database"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class DummyProjectDatabase:
    """Mock project management database"""
    
    def __init__(self):
        self.projects = self._init_projects()
        self.team_members = self._init_team_members()
        self.resource_allocation = self._init_resources()
    
    def _init_projects(self) -> Dict[str, Dict]:
        """Initialize dummy projects"""
        return {
            "PROJ-001": {
                "id": "PROJ-001",
                "name": "Q2 Mobile App Launch",
                "description": "Launch new mobile application for iOS and Android",
                "manager_id": "MGR-001",
                "status": "active",
                "start_date": "2026-04-01",
                "end_date": "2026-06-30",
                "budget": 250000,
                "team_members": ["EMP-001", "EMP-005", "EMP-006"],
                "milestones": [
                    {
                        "id": "MS-001",
                        "name": "Design Complete",
                        "due_date": "2026-04-30",
                        "status": "on_track",
                        "completion_percentage": 85.0,
                        "dependencies": []
                    },
                    {
                        "id": "MS-002",
                        "name": "Development Sprint 1",
                        "due_date": "2026-05-15",
                        "status": "on_track",
                        "completion_percentage": 40.0,
                        "dependencies": ["MS-001"]
                    },
                    {
                        "id": "MS-003",
                        "name": "QA & Testing",
                        "due_date": "2026-06-15",
                        "status": "at_risk",
                        "completion_percentage": 0.0,
                        "dependencies": ["MS-002"]
                    },
                    {
                        "id": "MS-004",
                        "name": "App Store Release",
                        "due_date": "2026-06-30",
                        "status": "on_track",
                        "completion_percentage": 0.0,
                        "dependencies": ["MS-003"]
                    }
                ],
                "progress_percentage": 31.25
            },
            "PROJ-002": {
                "id": "PROJ-002",
                "name": "Cloud Migration Initiative",
                "description": "Migrate legacy systems to cloud infrastructure",
                "manager_id": "MGR-004",
                "status": "active",
                "start_date": "2026-03-15",
                "end_date": "2026-07-31",
                "budget": 400000,
                "team_members": ["EMP-001", "EMP-007", "EMP-008"],
                "milestones": [
                    {
                        "id": "MS-005",
                        "name": "Infrastructure Setup",
                        "due_date": "2026-04-30",
                        "status": "completed",
                        "completion_percentage": 100.0,
                        "dependencies": []
                    },
                    {
                        "id": "MS-006",
                        "name": "Phase 1 Migration",
                        "due_date": "2026-05-31",
                        "status": "on_track",
                        "completion_percentage": 60.0,
                        "dependencies": ["MS-005"]
                    },
                    {
                        "id": "MS-007",
                        "name": "Phase 2 Migration",
                        "due_date": "2026-06-30",
                        "status": "at_risk",
                        "completion_percentage": 10.0,
                        "dependencies": ["MS-006"]
                    },
                    {
                        "id": "MS-008",
                        "name": "Cutover & Verification",
                        "due_date": "2026-07-31",
                        "status": "on_track",
                        "completion_percentage": 0.0,
                        "dependencies": ["MS-007"]
                    }
                ],
                "progress_percentage": 42.5
            },
            "PROJ-003": {
                "id": "PROJ-003",
                "name": "Customer Portal Redesign",
                "description": "Redesign customer-facing portal for better UX",
                "manager_id": "MGR-002",
                "status": "planning",
                "start_date": "2026-05-01",
                "end_date": "2026-08-31",
                "budget": 150000,
                "team_members": ["EMP-009", "EMP-010"],
                "milestones": [
                    {
                        "id": "MS-009",
                        "name": "Requirements & Design",
                        "due_date": "2026-05-31",
                        "status": "on_track",
                        "completion_percentage": 0.0,
                        "dependencies": []
                    },
                    {
                        "id": "MS-010",
                        "name": "Development",
                        "due_date": "2026-07-31",
                        "status": "on_track",
                        "completion_percentage": 0.0,
                        "dependencies": ["MS-009"]
                    },
                    {
                        "id": "MS-011",
                        "name": "Launch",
                        "due_date": "2026-08-31",
                        "status": "on_track",
                        "completion_percentage": 0.0,
                        "dependencies": ["MS-010"]
                    }
                ],
                "progress_percentage": 0.0
            }
        }
    
    def _init_team_members(self) -> Dict[str, Dict]:
        """Initialize team member data"""
        return {
            "EMP-001": {"id": "EMP-001", "name": "Alice Johnson", "email": "alice@company.com", "role": "Senior Engineer", "skills": ["Python", "React", "DevOps"]},
            "EMP-005": {"id": "EMP-005", "name": "Emma Wilson", "email": "emma@company.com", "role": "UI/UX Designer", "skills": ["Figma", "Design", "UX Research"]},
            "EMP-006": {"id": "EMP-006", "name": "Frank Brown", "email": "frank@company.com", "role": "QA Engineer", "skills": ["Testing", "Automation", "Reports"]},
            "EMP-007": {"id": "EMP-007", "name": "Grace Lee", "email": "grace@company.com", "role": "DevOps Engineer", "skills": ["AWS", "Kubernetes", "Infrastructure"]},
            "EMP-008": {"id": "EMP-008", "name": "Henry Zhang", "email": "henry@company.com", "role": "Backend Engineer", "skills": ["Java", "Microservices", "Databases"]},
            "EMP-009": {"id": "EMP-009", "name": "Iris Martinez", "email": "iris@company.com", "role": "Frontend Developer", "skills": ["React", "Vue", "CSS"]},
            "EMP-010": {"id": "EMP-010", "name": "Jack Anderson", "email": "jack@company.com", "role": "Product Manager", "skills": ["Requirements", "Analytics", "Prioritization"]},
            "MGR-001": {"id": "MGR-001", "name": "John Manager", "email": "john@company.com", "role": "Engineering Manager", "skills": ["Leadership", "Planning"]},
            "MGR-002": {"id": "MGR-002", "name": "Sarah Leader", "email": "sarah@company.com", "role": "Sales Manager", "skills": ["Management", "Strategy"]},
            "MGR-004": {"id": "MGR-004", "name": "Lisa Director", "email": "lisa@company.com", "role": "Infrastructure Director", "skills": ["Architecture", "Cloud"]},
        }
    
    def _init_resources(self) -> Dict[str, Dict]:
        """Initialize resource allocation"""
        return {
            "PROJ-001": {
                "total_allocated": 300,  # hours/week
                "team_allocation": {
                    "EMP-001": 40,  # 100% on this project
                    "EMP-005": 30,
                    "EMP-006": 25
                }
            },
            "PROJ-002": {
                "total_allocated": 280,
                "team_allocation": {
                    "EMP-001": 20,
                    "EMP-007": 40,
                    "EMP-008": 40
                }
            }
        }
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project by ID"""
        return self.projects.get(project_id)
    
    def get_all_projects(self, status: Optional[str] = None) -> List[Dict]:
        """Get all projects, optionally filtered by status"""
        if status:
            return [p for p in self.projects.values() if p["status"] == status]
        return list(self.projects.values())
    
    def get_project_status(self, project_id: str) -> Optional[Dict]:
        """Get detailed project status"""
        project = self.get_project(project_id)
        if not project:
            return None
        
        on_track = sum(1 for m in project["milestones"] if m["status"] == "on_track")
        at_risk = sum(1 for m in project["milestones"] if m["status"] == "at_risk")
        completed = sum(1 for m in project["milestones"] if m["status"] == "completed")
        
        return {
            "project_id": project_id,
            "name": project["name"],
            "status": project["status"],
            "progress": project["progress_percentage"],
            "milestones": {
                "on_track": on_track,
                "at_risk": at_risk,
                "completed": completed,
                "total": len(project["milestones"])
            },
            "team_size": len(project["team_members"]),
            "budget_allocated": project["budget"]
        }
    
    def update_milestone(self, project_id: str, milestone_id: str, status: str, completion: float) -> bool:
        """Update milestone status"""
        if project_id in self.projects:
            for milestone in self.projects[project_id]["milestones"]:
                if milestone["id"] == milestone_id:
                    milestone["status"] = status
                    milestone["completion_percentage"] = completion
                    return True
        return False
    
    def get_team_member(self, emp_id: str) -> Optional[Dict]:
        """Get team member details"""
        return self.team_members.get(emp_id)
    
    def get_project_team(self, project_id: str) -> List[Dict]:
        """Get team members for a project"""
        project = self.get_project(project_id)
        if not project:
            return []
        
        team = []
        for emp_id in project["team_members"]:
            member = self.get_team_member(emp_id)
            if member:
                team.append(member)
        return team

# Singleton instance
db = DummyProjectDatabase()
