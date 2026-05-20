"""HR Onboarding Service - orchestrates onboarding workflow"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .dummy_db import db
from ..schemas import OnboardingTask, OnboardingChecklist


def format_date_human_readable(date_str: str) -> str:
    """Convert YYYY-MM-DD format to 'Month Dth, Year' format (e.g., 'April 16th, 2026')"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        day = date_obj.day
        # Add ordinal suffix (st, nd, rd, th)
        if day in [1, 21, 31]:
            suffix = "st"
        elif day in [2, 22]:
            suffix = "nd"
        elif day in [3, 23]:
            suffix = "rd"
        else:
            suffix = "th"
        return date_obj.strftime(f"%B {day}{suffix}, %Y")
    except:
        return date_str  # Return original if parsing fails


def parse_date_to_iso(date_str: str) -> str:
    """
    Convert various date formats to YYYY-MM-DD ISO format.
    Handles: DD-MM-YYYY, YYYY-MM-DD, "April 16th, 2026", "April 16th", etc.
    """
    import re
    
    if not date_str:
        # Return tomorrow's date if no date provided
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Already in YYYY-MM-DD format
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # DD-MM-YYYY format (16-04-2026)
    dmy_match = re.match(r'^(\d{1,2})-(\d{1,2})-(\d{4})$', date_str)
    if dmy_match:
        day, month, year = dmy_match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # Human-readable format: "April 16th, 2026" or "April 16th" or "April 16"
    month_names = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    # Try to match Month Day, Year format
    month_day_year = re.match(r'^([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?$', date_str.strip())
    if month_day_year:
        month_str, day, year = month_day_year.groups()
        month_num = month_names.get(month_str.lower())
        if month_num:
            year = year or datetime.now().year
            return f"{year}-{month_num:02d}-{int(day):02d}"
    
    # Fallback: return tomorrow
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


class OnboardingService:
    """Handles all onboarding logic"""
    
    @staticmethod
    def create_new_employee(name: str, email: str, department: str, role: str, start_date: str, project: str = None) -> str:
        """Create a new employee from parsed request and return employee ID"""
        return db.create_employee(name, email, department, role, start_date, project)
    
    @staticmethod
    def create_onboarding_checklist(employee_id: str) -> Optional[Dict]:
        """Create onboarding checklist for new employee"""
        employee = db.get_employee(employee_id)
        if not employee:
            return None
        
        # Get role-specific template
        role_key = employee["role"].split()[0].lower()
        tasks_template = db.get_onboarding_template(role_key)
        
        # Create tasks with due dates
        start_date = datetime.strptime(employee["start_date"], "%Y-%m-%d")
        tasks = []
        
        for template_task in tasks_template:
            due_date = start_date + timedelta(days=template_task["days_to_complete"])
            task = {
                "id": template_task["id"],
                "name": template_task["name"],
                "description": template_task["description"],
                "due_date": due_date.strftime("%Y-%m-%d"),
                "status": "pending",
                "assigned_to": template_task["assigned_to"]
            }
            tasks.append(task)
        
        # Calculate progress
        completed = len([t for t in tasks if t["status"] == "completed"])
        total = len(tasks)
        progress = (completed / total * 100) if total > 0 else 0
        
        # Estimate completion date
        all_due_dates = [datetime.strptime(t["due_date"], "%Y-%m-%d") for t in tasks]
        estimated_completion = max(all_due_dates).strftime("%Y-%m-%d")
        
        return {
            "employee_id": employee_id,
            "employee_name": employee["name"],
            "department": employee["department"],
            "role": employee["role"],
            "start_date": format_date_human_readable(employee["start_date"]),
            "tasks": [{**task, "due_date": format_date_human_readable(task["due_date"])} for task in tasks],
            "progress_percentage": progress,
            "estimated_completion_date": format_date_human_readable(estimated_completion)
        }
    
    @staticmethod
    def get_onboarding_status(employee_id: str) -> Optional[Dict]:
        """Get current onboarding status for employee"""
        employee = db.get_employee(employee_id)
        if not employee:
            return None
        
        checklist = OnboardingService.create_onboarding_checklist(employee_id)
        if not checklist:
            return None
        
        # Get actual status from DB
        status_record = db.get_onboarding_checklist(employee_id)
        if status_record:
            completed_count = len(status_record["completed_tasks"])
            pending_count = len(status_record["pending_tasks"])
            overdue_count = len(status_record["overdue_tasks"])
        else:
            completed_count = 0
            pending_count = len(checklist["tasks"])
            overdue_count = 0
        
        # Return dict compatible with Employee schema (using field names from schema)
        return {
            "id": employee_id,
            "name": employee["name"],
            "email": employee["email"],
            "department": employee["department"],
            "role": employee["role"],
            "start_date": employee["start_date"],
            "manager_id": employee.get("manager_id"),
            "status": employee["status"]
        }
    
    @staticmethod
    def complete_onboarding_task(employee_id: str, task_id: str) -> Dict:
        """Mark onboarding task as completed"""
        success = db.complete_task(employee_id, task_id)
        
        if success:
            # Check if all tasks completed
            status = OnboardingService.get_onboarding_status(employee_id)
            if status["pending_tasks"] == 0 and status["overdue_tasks"] == 0:
                db.update_employee_status(employee_id, "active")
                return {
                    "success": True,
                    "message": f"Task {task_id} completed. Onboarding finished!",
                    "employee_status": "active"
                }
            return {
                "success": True,
                "message": f"Task {task_id} completed",
                "remaining_tasks": status["pending_tasks"]
            }
        
        return {
            "success": False,
            "message": f"Could not complete task {task_id}"
        }
    
    @staticmethod
    def get_pending_employees() -> List[Dict]:
        """Get all employees pending onboarding"""
        return db.get_all_employees(status="pending_onboarding")
    
    @staticmethod
    def generate_onboarding_report() -> Dict:
        """Generate onboarding status report"""
        all_employees = db.get_all_employees()
        pending = db.get_all_employees(status="pending_onboarding")
        active = db.get_all_employees(status="active")
        
        report = {
            "total_employees": len(all_employees),
            "active_employees": len(active),
            "pending_onboarding": len(pending),
            "pending_list": [{"id": e["id"], "name": e["name"], "role": e["role"]} for e in pending],
            "departments": {}
        }
        
        # Group by department
        for emp in all_employees:
            dept = emp["department"]
            if dept not in report["departments"]:
                report["departments"][dept] = {
                    "total": 0,
                    "active": 0,
                    "pending": 0
                }
            report["departments"][dept]["total"] += 1
            if emp["status"] == "active":
                report["departments"][dept]["active"] += 1
            else:
                report["departments"][dept]["pending"] += 1
        
        return report
    
    @staticmethod
    def get_mentorship_assignments(employee_id: str) -> Dict:
        """Get mentor assignments for new employee"""
        employee = db.get_employee(employee_id)
        if not employee:
            return {}
        
        manager = db.get_employee(employee["manager_id"])
        
        return {
            "employee_id": employee_id,
            "employee_name": employee["name"],
            "manager_id": manager["id"],
            "manager_name": manager["name"],
            "mentor_assignments": [
                {
                    "mentor_id": manager["id"],
                    "mentor_name": manager["name"],
                    "role": "Primary Manager",
                    "frequency": "Daily"
                },
                {
                    "mentor_id": "TECH-LEAD",
                    "mentor_name": "Technical Lead (TBD)",
                    "role": "Technical Mentor",
                    "frequency": "3x per week"
                }
            ],
            "training_schedule": [
                {
                    "week": 1,
                    "focus": "IT Setup & Team Introduction",
                    "hours": 8
                },
                {
                    "week": 2,
                    "focus": "Role-specific training",
                    "hours": 12
                },
                {
                    "week": 3,
                    "focus": "Process & tools training",
                    "hours": 10
                },
                {
                    "week": 4,
                    "focus": "First tasks & integration",
                    "hours": 20
                }
            ]
        }
