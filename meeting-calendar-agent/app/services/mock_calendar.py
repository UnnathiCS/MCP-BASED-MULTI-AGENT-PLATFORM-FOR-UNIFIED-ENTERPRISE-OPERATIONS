#!/usr/bin/env python3
"""
Mock In-Memory Calendar Storage
Simulates Google Calendar for demo purposes without needing credentials
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

class MockCalendarStore:
    """Simple in-memory calendar storage for demo/testing"""
    
    def __init__(self):
        self.meetings: List[Dict[str, Any]] = []
        self.attendee_availability: Dict[str, List[Dict]] = {}
        self.meeting_id_counter = 1000
    
    def create_meeting(self, 
                       title: str,
                       start_time: datetime,
                       end_time: datetime,
                       attendees: List[str],
                       location: Optional[str] = None,
                       description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new meeting"""
        meeting_id = f"mtg-{self.meeting_id_counter}"
        self.meeting_id_counter += 1
        
        meeting = {
            "id": meeting_id,
            "title": title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "attendees": attendees,
            "location": location or "Virtual Meeting",
            "description": description or "",
            "status": "confirmed",
            "created_at": datetime.now().isoformat(),
            "hangout_link": f"https://meet.google.com/{meeting_id}"
        }
        
        self.meetings.append(meeting)
        print(f"✓ Meeting created: {title} ({meeting_id})")
        return meeting
    
    def get_conflicts(self, 
                     start_time: datetime,
                     end_time: datetime,
                     attendees: List[str]) -> List[Dict[str, Any]]:
        """Check for scheduling conflicts"""
        conflicts = []
        
        for meeting in self.meetings:
            mtg_start = datetime.fromisoformat(meeting["start_time"])
            mtg_end = datetime.fromisoformat(meeting["end_time"])
            
            # Check if times overlap
            if not (end_time <= mtg_start or start_time >= mtg_end):
                # Check if any attendees match
                conflicting_attendees = set(attendees) & set(meeting["attendees"])
                if conflicting_attendees:
                    conflicts.append({
                        "meeting_id": meeting["id"],
                        "title": meeting["title"],
                        "time": f"{mtg_start.strftime('%Y-%m-%d %H:%M')} - {mtg_end.strftime('%H:%M')}",
                        "attendees": list(conflicting_attendees),
                        "severity": "high"
                    })
        
        return conflicts
    
    def find_available_slots(self,
                           start_date: datetime,
                           end_date: datetime,
                           duration_minutes: int,
                           attendees: List[str],
                           preferred_hour: int = 10) -> List[Dict[str, str]]:
        """Find available time slots"""
        available_slots = []
        current = start_date.replace(hour=preferred_hour, minute=0)
        
        while current < end_date:
            slot_end = current + timedelta(minutes=duration_minutes)
            
            # Check if slot is available
            conflicts = self.get_conflicts(current, slot_end, attendees)
            if not conflicts and current.hour >= 9 and current.hour < 18:  # Business hours
                available_slots.append({
                    "time": current.isoformat(),
                    "duration_minutes": duration_minutes,
                    "attendees_available": attendees
                })
            
            current += timedelta(minutes=30)
        
        return available_slots
    
    def list_meetings(self, attendee: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all meetings, optionally filtered by attendee"""
        if attendee:
            return [m for m in self.meetings if attendee in m["attendees"]]
        return self.meetings
    
    def get_meeting(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific meeting"""
        for meeting in self.meetings:
            if meeting["id"] == meeting_id:
                return meeting
        return None
    
    def update_meeting(self, meeting_id: str, **updates) -> Optional[Dict[str, Any]]:
        """Update a meeting"""
        meeting = self.get_meeting(meeting_id)
        if meeting:
            meeting.update(updates)
            meeting["updated_at"] = datetime.now().isoformat()
            return meeting
        return None
    
    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete a meeting"""
        for i, meeting in enumerate(self.meetings):
            if meeting["id"] == meeting_id:
                self.meetings.pop(i)
                print(f"✓ Meeting deleted: {meeting_id}")
                return True
        return False
    
    def to_json(self) -> str:
        """Export calendar as JSON"""
        return json.dumps(self.meetings, indent=2, default=str)
    
    def print_calendar(self):
        """Print calendar in human-readable format"""
        print("\n" + "=" * 80)
        print("📅 MOCK CALENDAR")
        print("=" * 80)
        
        if not self.meetings:
            print("No meetings scheduled")
            return
        
        # Sort by start time
        sorted_meetings = sorted(self.meetings, 
                                key=lambda m: m["start_time"])
        
        for meeting in sorted_meetings:
            start = datetime.fromisoformat(meeting["start_time"])
            end = datetime.fromisoformat(meeting["end_time"])
            
            print(f"\n📌 {meeting['title']} ({meeting['id']})")
            print(f"   Time: {start.strftime('%a, %b %d %Y %H:%M')} - {end.strftime('%H:%M')}")
            print(f"   Attendees: {', '.join(meeting['attendees']) or 'None'}")
            print(f"   Location: {meeting['location']}")
            if meeting.get('hangout_link'):
                print(f"   Meet: {meeting['hangout_link']}")
            print(f"   Status: {meeting['status']}")
        
        print("\n" + "=" * 80)


# Global instance for the meeting agent to use
_calendar_store = None

def get_calendar_store() -> MockCalendarStore:
    """Get or create the global calendar store"""
    global _calendar_store
    if _calendar_store is None:
        _calendar_store = MockCalendarStore()
    return _calendar_store


# Example usage
if __name__ == "__main__":
    cal = MockCalendarStore()
    
    # Create some sample meetings
    print("\n🔧 Creating sample meetings...\n")
    
    now = datetime.now()
    next_monday = now + timedelta(days=(7 - now.weekday()))  # Next Monday
    
    # Meeting 1: Team Sync
    cal.create_meeting(
        title="Team Sync",
        start_time=next_monday.replace(hour=14, minute=0),
        end_time=next_monday.replace(hour=15, minute=0),
        attendees=["alice@example.com", "bob@example.com"],
        location="Conference Room A"
    )
    
    # Meeting 2: Q1 Planning
    cal.create_meeting(
        title="Q1 Planning",
        start_time=datetime(2026, 4, 15, 14, 0),
        end_time=datetime(2026, 4, 15, 15, 0),
        attendees=["unnathics.btech23@rvu.edu.in", "alice@example.com"],
        description="Q1 goals and planning"
    )
    
    # Meeting 3: Weekly Standup
    cal.create_meeting(
        title="Weekly Standup",
        start_time=next_monday.replace(hour=10, minute=0),
        end_time=next_monday.replace(hour=10, minute=30),
        attendees=["alice@example.com", "bob@example.com", "charlie@example.com"]
    )
    
    # Print calendar
    cal.print_calendar()
    
    # Check for conflicts
    print("\n🔍 Checking for conflicts on Q1 Planning meeting date...")
    conflicts = cal.get_conflicts(
        datetime(2026, 4, 15, 14, 0),
        datetime(2026, 4, 15, 15, 0),
        ["unnathics.btech23@rvu.edu.in", "alice@example.com"]
    )
    
    if conflicts:
        print(f"⚠️ Found {len(conflicts)} conflict(s):")
        for c in conflicts:
            print(f"   - {c['title']}: {c['attendees']}")
    else:
        print("✓ No conflicts found")
    
    # Find available slots
    print("\n📅 Finding available slots for next week...")
    slots = cal.find_available_slots(
        next_monday,
        next_monday + timedelta(days=5),
        duration_minutes=60,
        attendees=["alice@example.com", "bob@example.com"]
    )
    
    print(f"Found {len(slots)} available 1-hour slots:")
    for slot in slots[:5]:  # Show first 5
        slot_time = datetime.fromisoformat(slot["time"])
        print(f"   ✓ {slot_time.strftime('%a %H:%M')}")
    
    # Export as JSON
    print("\n📤 Calendar exported as JSON:")
    print(cal.to_json())
