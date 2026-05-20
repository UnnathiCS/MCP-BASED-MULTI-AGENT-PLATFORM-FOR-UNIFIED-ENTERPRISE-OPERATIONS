"""Dummy HR database with mock employee and department data"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

class DummyHRDatabase:
    """Mock HR database for university project"""
    
    def __init__(self):
        self.employees = self._init_employees()
        self.departments = self._init_departments()
        self.onboarding_templates = self._init_onboarding_templates()
        self.onboarding_status = self._init_onboarding_status()
    
    def _init_employees(self) -> Dict[str, Dict]:
        """Initialize dummy employee database"""
        return {
            "EMP-001": {
                "id": "EMP-001",
                "name": "Alice Johnson",
                "email": "alice.johnson@company.com",
                "department": "Engineering",
                "role": "Senior Software Engineer",
                "start_date": "2026-04-15",
                "manager_id": "MGR-001",
                "status": "pending_onboarding"
            },
            "EMP-002": {
                "id": "EMP-002",
                "name": "Bob Smith",
                "email": "bob.smith@company.com",
                "department": "Sales",
                "role": "Sales Executive",
                "start_date": "2026-04-20",
                "manager_id": "MGR-002",
                "status": "pending_onboarding"
            },
            "EMP-003": {
                "id": "EMP-003",
                "name": "Carol Davis",
                "email": "carol.davis@company.com",
                "department": "HR",
                "role": "HR Specialist",
                "start_date": "2026-04-10",
                "manager_id": "MGR-003",
                "status": "active"
            },
            "EMP-004": {
                "id": "EMP-004",
                "name": "David Wilson",
                "email": "david.wilson@company.com",
                "department": "Finance",
                "role": "Financial Analyst",
                "start_date": "2026-04-08",
                "manager_id": "MGR-003",
                "status": "active"
            },
            "MGR-001": {
                "id": "MGR-001",
                "name": "John Manager",
                "email": "john.manager@company.com",
                "department": "Engineering",
                "role": "Engineering Manager",
                "start_date": "2024-01-01",
                "manager_id": "DIR-001",
                "status": "active"
            },
            "MGR-002": {
                "id": "MGR-002",
                "name": "Sarah Leader",
                "email": "sarah.leader@company.com",
                "department": "Sales",
                "role": "Sales Manager",
                "start_date": "2024-02-01",
                "manager_id": "DIR-001",
                "status": "active"
            },
            "MGR-003": {
                "id": "MGR-003",
                "name": "Mike Director",
                "email": "mike.director@company.com",
                "department": "HR",
                "role": "HR Director",
                "start_date": "2023-01-01",
                "manager_id": "CEO",
                "status": "active"
            }
        }
    
    def _init_departments(self) -> Dict[str, Dict]:
        """Initialize dummy department data"""
        return {
            "ENG": {
                "id": "ENG",
                "name": "Engineering",
                "head_id": "MGR-001",
                "budget": 500000,
                "team_size": 15
            },
            "SAL": {
                "id": "SAL",
                "name": "Sales",
                "head_id": "MGR-002",
                "budget": 300000,
                "team_size": 10
            },
            "HR": {
                "id": "HR",
                "name": "Human Resources",
                "head_id": "MGR-003",
                "budget": 150000,
                "team_size": 5
            },
            "FIN": {
                "id": "FIN",
                "name": "Finance",
                "head_id": "MGR-003",
                "budget": 200000,
                "team_size": 8
            }
        }
    
    def _init_onboarding_templates(self) -> Dict[str, List[Dict]]:
        """Initialize onboarding task templates by role"""
        return {
            "default": [
                {
                    "id": "TASK-001",
                    "name": "IT Account Setup",
                    "description": "Create email, laptop, VPN access, development tools",
                    "days_to_complete": 1,
                    "assigned_to": "IT-TEAM"
                },
                {
                    "id": "TASK-002",
                    "name": "Welcome Meeting",
                    "description": "Meet with manager and team",
                    "days_to_complete": 0,
                    "assigned_to": "MANAGER"
                },
                {
                    "id": "TASK-003",
                    "name": "Compliance Training",
                    "description": "Complete compliance and security training",
                    "days_to_complete": 1,
                    "assigned_to": "SELF"
                },
                {
                    "id": "TASK-004",
                    "name": "Office Tour",
                    "description": "Tour office, meet team members",
                    "days_to_complete": 0,
                    "assigned_to": "HR"
                },
                {
                    "id": "TASK-005",
                    "name": "Role Orientation",
                    "description": "Learn about role, responsibilities, and team processes",
                    "days_to_complete": 2,
                    "assigned_to": "MANAGER"
                }
            ],
            "engineer": [
                {
                    "id": "TASK-ENG-001",
                    "name": "Repository Access",
                    "description": "Setup Git access, clone repositories, configure development environment",
                    "days_to_complete": 1,
                    "assigned_to": "TECH-LEAD"
                },
                {
                    "id": "TASK-ENG-002",
                    "name": "Code Review Training",
                    "description": "Learn team code review standards and processes",
                    "days_to_complete": 1,
                    "assigned_to": "TECH-LEAD"
                },
                {
                    "id": "TASK-ENG-003",
                    "name": "First Task Assignment",
                    "description": "Get assigned first small task to get familiar with workflow",
                    "days_to_complete": 3,
                    "assigned_to": "TECH-LEAD"
                }
            ],
            "sales": [
                {
                    "id": "TASK-SAL-001",
                    "name": "Product Training",
                    "description": "Learn company products, features, pricing",
                    "days_to_complete": 2,
                    "assigned_to": "SALES-TEAM"
                },
                {
                    "id": "TASK-SAL-002",
                    "name": "CRM Setup",
                    "description": "Setup CRM access, learn system",
                    "days_to_complete": 1,
                    "assigned_to": "SALES-OPS"
                },
                {
                    "id": "TASK-SAL-003",
                    "name": "Sales Process Training",
                    "description": "Learn sales process, quota, commission structure",
                    "days_to_complete": 2,
                    "assigned_to": "MANAGER"
                }
            ]
        }
    
    def _init_onboarding_status(self) -> Dict[str, Dict]:
        """Initialize onboarding status tracking"""
        return {
            "EMP-001": {
                "employee_id": "EMP-001",
                "completed_tasks": ["TASK-001", "TASK-002"],
                "pending_tasks": ["TASK-003", "TASK-004", "TASK-005", "TASK-ENG-001", "TASK-ENG-002", "TASK-ENG-003"],
                "overdue_tasks": [],
                "start_date": "2026-04-15",
                "estimated_completion": "2026-04-22"
            },
            "EMP-002": {
                "employee_id": "EMP-002",
                "completed_tasks": [],
                "pending_tasks": ["TASK-001", "TASK-002", "TASK-003", "TASK-004", "TASK-005", "TASK-SAL-001", "TASK-SAL-002", "TASK-SAL-003"],
                "overdue_tasks": [],
                "start_date": "2026-04-20",
                "estimated_completion": "2026-04-29"
            }
        }
    
    def get_employee(self, employee_id: str) -> Optional[Dict]:
        """Get employee by ID"""
        return self.employees.get(employee_id)
    
    def create_employee(self, name: str, email: str, department: str, role: str, start_date: str, project: str = None) -> str:
        """Create a new employee dynamically and return employee ID"""
        # Generate next employee ID
        emp_ids = [int(e_id.split('-')[1]) for e_id in self.employees.keys() if e_id.startswith('EMP-')]
        next_id = max(emp_ids) + 1 if emp_ids else 1
        employee_id = f"EMP-{next_id:03d}"
        
        # Create employee record
        employee = {
            "id": employee_id,
            "name": name,
            "email": email,
            "department": department,
            "role": role,
            "start_date": start_date,
            "manager_id": "MGR-001",  # Default manager
            "status": "pending_onboarding",
            "project": project
        }
        
        self.employees[employee_id] = employee
        
        # Initialize onboarding status
        self.onboarding_status[employee_id] = {
            "employee_id": employee_id,
            "completed_tasks": [],
            "pending_tasks": ["TASK-001", "TASK-002", "TASK-003", "TASK-004", "TASK-005"],
            "overdue_tasks": []
        }
        
        return employee_id
    
    def get_all_employees(self, status: Optional[str] = None) -> List[Dict]:
        """Get all employees, optionally filtered by status"""
        if status:
            return [e for e in self.employees.values() if e["status"] == status]
        return list(self.employees.values())
    
    def get_onboarding_checklist(self, employee_id: str) -> Optional[Dict]:
        """Get onboarding status for employee"""
        return self.onboarding_status.get(employee_id)
    
    def get_onboarding_template(self, role: str) -> List[Dict]:
        """Get onboarding template tasks for a role"""
        templates = self.onboarding_templates.get(role.lower(), self.onboarding_templates["default"])
        return templates + self.onboarding_templates["default"]
    
    def complete_task(self, employee_id: str, task_id: str) -> bool:
        """Mark a task as completed"""
        if employee_id in self.onboarding_status:
            status = self.onboarding_status[employee_id]
            if task_id in status["pending_tasks"]:
                status["pending_tasks"].remove(task_id)
                status["completed_tasks"].append(task_id)
                return True
        return False
    
    def update_employee_status(self, employee_id: str, new_status: str) -> bool:
        """Update employee status"""
        if employee_id in self.employees:
            self.employees[employee_id]["status"] = new_status
            return True
        return False
    
    def get_department(self, dept_id: str) -> Optional[Dict]:
        """Get department by ID"""
        return self.departments.get(dept_id)
    
    def get_all_departments(self) -> List[Dict]:
        """Get all departments"""
        return list(self.departments.values())

# Singleton instance
db = DummyHRDatabase()
