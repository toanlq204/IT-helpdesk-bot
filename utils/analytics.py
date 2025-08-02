"""
Analytics and monitoring module for IT Helpdesk Chatbot
Tracks usage patterns, performance metrics, and user satisfaction
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, Counter


class HelpdeskAnalytics:
    """Analytics engine for helpdesk chatbot performance and usage"""

    def __init__(self, log_file: str = "logs/analytics.json"):
        self.log_file = log_file
        self.session_data = {}
        self.ensure_log_directory()

    def ensure_log_directory(self):
        """Create logs directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def log_interaction(self, session_id: str, event_type: str, data: Dict):
        """Log user interaction for analytics"""
        timestamp = datetime.now().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "session_id": session_id,
            "event_type": event_type,
            "data": data
        }

        # Append to log file
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Analytics logging error: {e}")

    def log_user_query(self, session_id: str, query: str, intent: str = None):
        """Log user query and detected intent"""
        self.log_interaction(session_id, "user_query", {
            "query": query[:100],  # Truncate for privacy
            "query_length": len(query),
            "intent": intent
        })

    def log_function_call(self, session_id: str, function_name: str, success: bool, response_time: float):
        """Log function call performance"""
        self.log_interaction(session_id, "function_call", {
            "function_name": function_name,
            "success": success,
            "response_time_ms": response_time * 1000
        })

    def log_user_satisfaction(self, session_id: str, rating: int, feedback: str = None):
        """Log user satisfaction rating"""
        self.log_interaction(session_id, "satisfaction", {
            "rating": rating,
            "feedback": feedback[:200] if feedback else None
        })

    def log_escalation(self, session_id: str, ticket_id: str, reason: str):
        """Log ticket escalation event"""
        self.log_interaction(session_id, "escalation", {
            "ticket_id": ticket_id,
            "reason": reason
        })

    def get_usage_stats(self, days: int = 7) -> Dict:
        """Get usage statistics for the last N days"""
        stats = {
            "total_sessions": 0,
            "total_queries": 0,
            "avg_session_length": 0,
            "popular_functions": Counter(),
            "common_intents": Counter(),
            "satisfaction_ratings": [],
            "escalation_rate": 0
        }

        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            with open(self.log_file, "r") as f:
                sessions = defaultdict(list)

                for line in f:
                    try:
                        entry = json.loads(line)
                        entry_date = datetime.fromisoformat(entry["timestamp"])

                        if entry_date >= cutoff_date:
                            session_id = entry["session_id"]
                            sessions[session_id].append(entry)

                            if entry["event_type"] == "user_query":
                                stats["total_queries"] += 1
                                if entry["data"].get("intent"):
                                    stats["common_intents"][entry["data"]
                                                            ["intent"]] += 1

                            elif entry["event_type"] == "function_call":
                                stats["popular_functions"][entry["data"]
                                                           ["function_name"]] += 1

                            elif entry["event_type"] == "satisfaction":
                                stats["satisfaction_ratings"].append(
                                    entry["data"]["rating"])

                    except json.JSONDecodeError:
                        continue

                stats["total_sessions"] = len(sessions)

                # Calculate average session length
                if sessions:
                    session_lengths = []
                    for session_events in sessions.values():
                        if len(session_events) > 1:
                            start = datetime.fromisoformat(
                                session_events[0]["timestamp"])
                            end = datetime.fromisoformat(
                                session_events[-1]["timestamp"])
                            length = (end - start).total_seconds() / \
                                60  # minutes
                            session_lengths.append(length)

                    if session_lengths:
                        stats["avg_session_length"] = sum(
                            session_lengths) / len(session_lengths)

        except FileNotFoundError:
            pass  # No analytics data yet

        return stats

    def generate_report(self, days: int = 7) -> str:
        """Generate human-readable analytics report"""
        stats = self.get_usage_stats(days)

        report = f"""
📊 IT HELPDESK ANALYTICS REPORT
Period: Last {days} days
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 USAGE METRICS:
• Total Sessions: {stats['total_sessions']}
• Total Queries: {stats['total_queries']}
• Average Session Length: {stats['avg_session_length']:.1f} minutes
• Queries per Session: {stats['total_queries'] / max(stats['total_sessions'], 1):.1f}

🔧 POPULAR FUNCTIONS:
"""

        for func, count in stats['popular_functions'].most_common(5):
            report += f"• {func}: {count} calls\n"

        report += "\n🎯 COMMON INTENTS:\n"
        for intent, count in stats['common_intents'].most_common(5):
            report += f"• {intent}: {count} queries\n"

        if stats['satisfaction_ratings']:
            avg_rating = sum(stats['satisfaction_ratings']) / \
                len(stats['satisfaction_ratings'])
            report += f"\n😊 USER SATISFACTION:\n"
            report += f"• Average Rating: {avg_rating:.1f}/5\n"
            report += f"• Total Ratings: {len(stats['satisfaction_ratings'])}\n"

        return report


class PerformanceMonitor:
    """Monitor system performance and response times"""

    def __init__(self):
        self.metrics = defaultdict(list)

    def record_response_time(self, operation: str, time_ms: float):
        """Record response time for an operation"""
        self.metrics[f"{operation}_response_time"].append(time_ms)

    def record_error(self, operation: str, error_type: str):
        """Record an error occurrence"""
        self.metrics[f"{operation}_errors"].append(error_type)

    def get_performance_summary(self) -> Dict:
        """Get performance metrics summary"""
        summary = {}

        for metric_name, values in self.metrics.items():
            if "response_time" in metric_name:
                summary[metric_name] = {
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
            elif "errors" in metric_name:
                summary[metric_name] = {
                    "count": len(values),
                    "types": Counter(values)
                }

        return summary


# Global analytics instances
analytics = HelpdeskAnalytics()
performance_monitor = PerformanceMonitor()


def track_user_interaction(func):
    """Decorator to automatically track function calls"""
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = str(e)
            success = False

        end_time = time.time()
        response_time = end_time - start_time

        # Log to analytics
        performance_monitor.record_response_time(
            func.__name__, response_time * 1000)

        if not success:
            performance_monitor.record_error(func.__name__, type(e).__name__)

        return result

    return wrapper
