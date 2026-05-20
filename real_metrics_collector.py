"""
Real Metrics Collector - Tracks ACTUAL agent performance data
Collects real request data: success/failure, response times, errors
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class RealMetricsCollector:
    """Collects REAL metrics from actual agent requests"""
    
    def __init__(self, metrics_file: str = "real_agent_metrics.json", 
                 logs_file: str = "agent_request_logs.jsonl"):
        self.metrics_file = metrics_file
        self.logs_file = logs_file
        self.init_files()
    
    def init_files(self):
        """Initialize metrics and logs files with all 6 agents"""
        if not os.path.exists(self.metrics_file):
            default_metrics = {
                "Support Agent": {
                    "agent_id": "support_001",
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_time": 0,
                    "requests": [],
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                },
                "HR Onboarding Agent": {
                    "agent_id": "hr_001",
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_time": 0,
                    "requests": [],
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                },
                "Meeting Calendar Agent": {
                    "agent_id": "meeting_001",
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_time": 0,
                    "requests": [],
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                },
                "Project Management Agent": {
                    "agent_id": "project_001",
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_time": 0,
                    "requests": [],
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                },
                "Document Review Agent": {
                    "agent_id": "document_001",
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_time": 0,
                    "requests": [],
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                },
                "Analytics Agent": {
                    "agent_id": "analytics_001",
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_time": 0,
                    "requests": [],
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                },
                "Email Agent": {
                    "agent_id": "email_001",
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_time": 0,
                    "requests": [],
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
            }
            with open(self.metrics_file, 'w') as f:
                json.dump(default_metrics, f, indent=2)
        
        if not os.path.exists(self.logs_file):
            open(self.logs_file, 'a').close()
    
    def record_request(self, agent_name: str, query: str, success: bool, 
                      response_time: float, error: Optional[str] = None):
        """Record a REAL request from an agent"""
        
        try:
            # Load current metrics
            with open(self.metrics_file, 'r') as f:
                metrics = json.load(f)
            
            if agent_name not in metrics:
                metrics[agent_name] = {
                    "agent_id": f"{agent_name.lower().replace(' ', '_')}_001",
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_time": 0,
                    "requests": [],
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
            
            # Update metrics
            metrics[agent_name]["total"] += 1
            if success:
                metrics[agent_name]["successful"] += 1
            else:
                metrics[agent_name]["failed"] += 1
            
            metrics[agent_name]["total_time"] += response_time
            metrics[agent_name]["last_updated"] = datetime.now().isoformat()
            
            # Keep last 100 requests for this agent
            request_log = {
                "timestamp": datetime.now().isoformat(),
                "query": query[:150] if query else "N/A",
                "success": success,
                "response_time": round(response_time, 3),
                "error": error
            }
            metrics[agent_name]["requests"].append(request_log)
            metrics[agent_name]["requests"] = metrics[agent_name]["requests"][-100:]
            
            # Save metrics
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            # Append to logs file (for audit trail)
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "agent": agent_name,
                "query": query[:150] if query else "N/A",
                "success": success,
                "response_time": round(response_time, 3),
                "error": error
            }
            with open(self.logs_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
        
        except Exception as e:
            print(f"Error recording metric: {str(e)}")
    
    def get_agent_metrics(self, agent_name: str) -> Optional[Dict]:
        """Get REAL metrics for a specific agent"""
        try:
            with open(self.metrics_file, 'r') as f:
                metrics = json.load(f)
            
            if agent_name not in metrics:
                return None
            
            agent_data = metrics[agent_name]
            total = agent_data["total"]
            successful = agent_data["successful"]
            
            # Calculate accuracy
            accuracy = (successful / total * 100) if total > 0 else 0
            
            # Calculate average response time
            avg_response_time = (agent_data["total_time"] / total) if total > 0 else 0
            
            return {
                "agent_name": agent_name,
                "agent_id": agent_data.get("agent_id", "unknown"),
                "total_requests": total,
                "successful_requests": successful,
                "failed_requests": agent_data["failed"],
                "accuracy_percent": round(accuracy, 2),
                "avg_response_time": round(avg_response_time, 3),
                "total_time": round(agent_data["total_time"], 3),
                "recent_requests": agent_data["requests"][-5:],
                "created_at": agent_data.get("created_at"),
                "last_updated": agent_data.get("last_updated")
            }
        except Exception as e:
            print(f"Error getting agent metrics: {str(e)}")
            return None
    
    def get_all_metrics(self) -> List[Dict]:
        """Get REAL metrics for all agents"""
        try:
            with open(self.metrics_file, 'r') as f:
                metrics = json.load(f)
            
            all_metrics = []
            for agent_name in sorted(metrics.keys()):
                agent_data = metrics[agent_name]
                total = agent_data["total"]
                successful = agent_data["successful"]
                
                # Calculate accuracy
                accuracy = (successful / total * 100) if total > 0 else 0
                
                # Calculate average response time
                avg_response_time = (agent_data["total_time"] / total) if total > 0 else 0
                
                all_metrics.append({
                    "agent_name": agent_name,
                    "agent_id": agent_data.get("agent_id", "unknown"),
                    "total_requests": total,
                    "successful_requests": successful,
                    "failed_requests": agent_data["failed"],
                    "accuracy_percent": round(accuracy, 2),
                    "avg_response_time": round(avg_response_time, 3)
                })
            
            return all_metrics
        except Exception as e:
            print(f"Error getting all metrics: {str(e)}")
            return []
    
    def get_summary_report(self) -> Dict:
        """Get comprehensive summary report"""
        try:
            all_metrics = self.get_all_metrics()
            
            total_requests = sum(m["total_requests"] for m in all_metrics)
            total_successful = sum(m["successful_requests"] for m in all_metrics)
            total_failed = sum(m["failed_requests"] for m in all_metrics)
            
            overall_accuracy = (total_successful / total_requests * 100) if total_requests > 0 else 0
            
            # Find best and worst agents
            best_agent = max(all_metrics, key=lambda x: x["accuracy_percent"]) if all_metrics else None
            worst_agent = min(all_metrics, key=lambda x: x["accuracy_percent"]) if all_metrics else None
            fastest_agent = min(all_metrics, key=lambda x: x["avg_response_time"]) if all_metrics else None
            slowest_agent = max(all_metrics, key=lambda x: x["avg_response_time"]) if all_metrics else None
            
            return {
                "total_requests": total_requests,
                "total_successful": total_successful,
                "total_failed": total_failed,
                "overall_accuracy_percent": round(overall_accuracy, 2),
                "best_accuracy_agent": best_agent["agent_name"] if best_agent else "N/A",
                "best_accuracy_score": best_agent["accuracy_percent"] if best_agent else 0,
                "worst_accuracy_agent": worst_agent["agent_name"] if worst_agent else "N/A",
                "worst_accuracy_score": worst_agent["accuracy_percent"] if worst_agent else 0,
                "fastest_agent": fastest_agent["agent_name"] if fastest_agent else "N/A",
                "fastest_time": fastest_agent["avg_response_time"] if fastest_agent else 0,
                "slowest_agent": slowest_agent["agent_name"] if slowest_agent else "N/A",
                "slowest_time": slowest_agent["avg_response_time"] if slowest_agent else 0,
                "agents": all_metrics,
                "report_generated": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error generating summary report: {str(e)}")
            return {"error": str(e)}
    
    def get_system_insights(self) -> List[str]:
        """Generate insights from real metrics data"""
        try:
            summary = self.get_summary_report()
            insights = []
            
            if summary.get("total_requests", 0) == 0:
                insights.append("📊 No requests recorded yet. Start making requests to see metrics.")
                return insights
            
            # Overall system health
            overall_accuracy = summary.get("overall_accuracy_percent", 0)
            if overall_accuracy >= 95:
                insights.append(f"✅ System performing excellently: {overall_accuracy:.1f}% accuracy")
            elif overall_accuracy >= 90:
                insights.append(f"✅ System performing well: {overall_accuracy:.1f}% accuracy")
            elif overall_accuracy >= 85:
                insights.append(f"⚠️ System acceptable: {overall_accuracy:.1f}% accuracy (monitor closely)")
            else:
                insights.append(f"🚨 System needs attention: {overall_accuracy:.1f}% accuracy")
            
            # Agent-specific insights
            for agent in summary.get("agents", []):
                if agent["accuracy_percent"] < 85:
                    insights.append(f"⚠️ {agent['agent_name']}: Low accuracy ({agent['accuracy_percent']:.1f}%)")
                if agent["avg_response_time"] > 2.0:
                    insights.append(f"⏱️ {agent['agent_name']}: High response time ({agent['avg_response_time']:.2f}s)")
            
            # Request volume
            total_reqs = summary.get("total_requests", 0)
            if total_reqs > 0:
                insights.append(f"📈 {total_reqs} requests processed today")
            
            return insights if insights else ["✅ All systems operating normally"]
        
        except Exception as e:
            return [f"Error generating insights: {str(e)}"]
    
    def reset_metrics(self, agent_name: Optional[str] = None):
        """Reset metrics for specific agent or all agents"""
        try:
            with open(self.metrics_file, 'r') as f:
                metrics = json.load(f)
            
            if agent_name:
                if agent_name in metrics:
                    metrics[agent_name]["total"] = 0
                    metrics[agent_name]["successful"] = 0
                    metrics[agent_name]["failed"] = 0
                    metrics[agent_name]["total_time"] = 0
                    metrics[agent_name]["requests"] = []
            else:
                for agent in metrics:
                    metrics[agent]["total"] = 0
                    metrics[agent]["successful"] = 0
                    metrics[agent]["failed"] = 0
                    metrics[agent]["total_time"] = 0
                    metrics[agent]["requests"] = []
            
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error resetting metrics: {str(e)}")
            return False


# Global instance
metrics_collector = RealMetricsCollector()
