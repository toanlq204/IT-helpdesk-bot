import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryLoggingService:
    """Service for logging user queries, responses, and feedback for learning loop"""

    def __init__(self, storage_path: str = "storage/logs"):
        """Initialize query logging service"""
        self.storage_path = storage_path
        self.query_logs_file = os.path.join(storage_path, "query_logs.json")
        self.feedback_queue_file = os.path.join(
            storage_path, "feedback_queue.json")

        # Ensure storage directory exists
        os.makedirs(storage_path, exist_ok=True)

        # Initialize log files if they don't exist
        self._init_log_files()

        logger.info("Query logging service initialized")

    def _init_log_files(self):
        """Initialize log files if they don't exist"""
        if not os.path.exists(self.query_logs_file):
            with open(self.query_logs_file, 'w', encoding='utf-8') as f:
                json.dump({"logs": []}, f, indent=2)

        if not os.path.exists(self.feedback_queue_file):
            with open(self.feedback_queue_file, 'w', encoding='utf-8') as f:
                json.dump({"feedback_items": []}, f, indent=2)

    def log_query(self,
                  user_question: str,
                  retrieved_docs: List[Dict[str, Any]],
                  distances: List[float],
                  answer: str,
                  confidence_level: str,
                  conversation_id: Optional[str] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log a user query and its response"""
        try:
            log_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()

            # Extract document IDs and metadata from retrieved docs
            doc_ids = []
            doc_titles = []
            doc_tags = []

            for doc in retrieved_docs:
                doc_ids.append(doc.get("id", "unknown"))
                if "metadata" in doc:
                    doc_titles.append(doc["metadata"].get("title", ""))
                    doc_tags.extend(doc["metadata"].get("tags", []))

            log_entry = {
                "log_id": log_id,
                "timestamp": timestamp,
                "user_question": user_question,
                "retrieved_doc_ids": doc_ids,
                "retrieved_doc_titles": doc_titles,
                "retrieved_doc_tags": list(set(doc_tags)),  # Remove duplicates
                "distances": distances,
                "top_distance": distances[0] if distances else 1.0,
                "confidence_level": confidence_level,
                "answer": answer,
                "conversation_id": conversation_id,
                "feedback_status": "pending",  # pending, correct, incorrect
                "metadata": metadata or {}
            }

            # Load existing logs
            with open(self.query_logs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Add new log entry
            data["logs"].append(log_entry)

            # Keep only last 1000 logs to prevent file from growing too large
            if len(data["logs"]) > 1000:
                data["logs"] = data["logs"][-1000:]

            # Save updated logs
            with open(self.query_logs_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Logged query: {log_id}")
            return log_id

        except Exception as e:
            logger.error(f"Failed to log query: {str(e)}")
            return ""

    def record_feedback(self, log_id: str, feedback: str, user_comment: Optional[str] = None) -> bool:
        """Record user feedback for a logged query"""
        try:
            # Valid feedback types
            valid_feedback = ["correct", "incorrect",
                              "partially_correct", "unclear"]
            if feedback not in valid_feedback:
                logger.error(f"Invalid feedback type: {feedback}")
                return False

            # Update the original log
            updated = self._update_log_feedback(log_id, feedback)

            # If feedback is negative, add to feedback queue for admin review
            if feedback in ["incorrect", "partially_correct", "unclear"]:
                self._add_to_feedback_queue(log_id, feedback, user_comment)

            logger.info(f"Recorded feedback for log {log_id}: {feedback}")
            return updated

        except Exception as e:
            logger.error(f"Failed to record feedback: {str(e)}")
            return False

    def _update_log_feedback(self, log_id: str, feedback: str) -> bool:
        """Update feedback status in the original log"""
        try:
            with open(self.query_logs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Find and update the log entry
            for log_entry in data["logs"]:
                if log_entry["log_id"] == log_id:
                    log_entry["feedback_status"] = feedback
                    log_entry["feedback_timestamp"] = datetime.now().isoformat()
                    break
            else:
                logger.error(f"Log ID not found: {log_id}")
                return False

            # Save updated logs
            with open(self.query_logs_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error(f"Failed to update log feedback: {str(e)}")
            return False

    def _add_to_feedback_queue(self, log_id: str, feedback: str, user_comment: Optional[str] = None):
        """Add negative feedback to queue for admin review"""
        try:
            # Get the original log entry
            log_entry = self.get_log_by_id(log_id)
            if not log_entry:
                return

            feedback_item = {
                "feedback_id": str(uuid.uuid4()),
                "log_id": log_id,
                "timestamp": datetime.now().isoformat(),
                "feedback_type": feedback,
                "user_comment": user_comment,
                "status": "pending_review",  # pending_review, reviewed, resolved
                "original_query": log_entry.get("user_question", ""),
                "original_answer": log_entry.get("answer", ""),
                "confidence_level": log_entry.get("confidence_level", "unknown"),
                "retrieved_docs": log_entry.get("retrieved_doc_titles", []),
                "suggested_actions": self._suggest_actions(feedback, log_entry)
            }

            # Load feedback queue
            with open(self.feedback_queue_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Add feedback item
            data["feedback_items"].append(feedback_item)

            # Save updated queue
            with open(self.feedback_queue_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(
                f"Added feedback to queue: {feedback_item['feedback_id']}")

        except Exception as e:
            logger.error(f"Failed to add to feedback queue: {str(e)}")

    def _suggest_actions(self, feedback: str, log_entry: Dict[str, Any]) -> List[str]:
        """Suggest actions based on feedback type and log data"""
        suggestions = []
        confidence = log_entry.get("confidence_level", "unknown")
        top_distance = log_entry.get("top_distance", 1.0)

        if feedback == "incorrect":
            suggestions.append(
                "Review and update knowledge base with correct information")
            suggestions.append("Check if query requires new FAQ entry")
            if confidence == "high":
                suggestions.append(
                    "High confidence but incorrect - review document relevance")

        elif feedback == "partially_correct":
            suggestions.append(
                "Enhance existing FAQ with more complete information")
            suggestions.append("Consider adding related sub-topics")

        elif feedback == "unclear":
            suggestions.append("Improve answer clarity and structure")
            suggestions.append("Add more specific examples or steps")

        if top_distance > 0.3:
            suggestions.append("Consider adding new FAQ for this topic area")

        return suggestions

    def get_log_by_id(self, log_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific log entry by ID"""
        try:
            with open(self.query_logs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for log_entry in data["logs"]:
                if log_entry["log_id"] == log_id:
                    return log_entry

            return None

        except Exception as e:
            logger.error(f"Failed to get log by ID: {str(e)}")
            return None

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent log entries"""
        try:
            with open(self.query_logs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Return most recent logs
            logs = data.get("logs", [])
            return logs[-limit:] if len(logs) > limit else logs

        except Exception as e:
            logger.error(f"Failed to get recent logs: {str(e)}")
            return []

    def get_feedback_queue(self, status: str = "pending_review") -> List[Dict[str, Any]]:
        """Get feedback items from queue"""
        try:
            with open(self.feedback_queue_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            feedback_items = data.get("feedback_items", [])

            if status == "all":
                return feedback_items
            else:
                return [item for item in feedback_items if item.get("status") == status]

        except Exception as e:
            logger.error(f"Failed to get feedback queue: {str(e)}")
            return []

    def update_feedback_status(self, feedback_id: str, status: str, admin_notes: Optional[str] = None) -> bool:
        """Update feedback item status (for admin use)"""
        try:
            valid_statuses = ["pending_review", "reviewed", "resolved"]
            if status not in valid_statuses:
                return False

            with open(self.feedback_queue_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Find and update feedback item
            for item in data["feedback_items"]:
                if item["feedback_id"] == feedback_id:
                    item["status"] = status
                    item["admin_notes"] = admin_notes
                    item["updated_timestamp"] = datetime.now().isoformat()
                    break
            else:
                return False

            with open(self.feedback_queue_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error(f"Failed to update feedback status: {str(e)}")
            return False

    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics from logs"""
        try:
            with open(self.query_logs_file, 'r', encoding='utf-8') as f:
                logs_data = json.load(f)

            with open(self.feedback_queue_file, 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)

            logs = logs_data.get("logs", [])
            feedback_items = feedback_data.get("feedback_items", [])

            # Calculate statistics
            total_queries = len(logs)
            confidence_stats = {}
            feedback_stats = {}

            for log in logs:
                # Confidence level stats
                confidence = log.get("confidence_level", "unknown")
                confidence_stats[confidence] = confidence_stats.get(
                    confidence, 0) + 1

                # Feedback stats
                feedback = log.get("feedback_status", "pending")
                feedback_stats[feedback] = feedback_stats.get(feedback, 0) + 1

            return {
                "total_queries": total_queries,
                "confidence_distribution": confidence_stats,
                "feedback_distribution": feedback_stats,
                "pending_feedback_reviews": len([item for item in feedback_items if item.get("status") == "pending_review"]),
                "average_confidence_score": sum(1 - log.get("top_distance", 1.0) for log in logs) / max(total_queries, 1)
            }

        except Exception as e:
            logger.error(f"Failed to get analytics: {str(e)}")
            return {}


# Global instance
query_logger = QueryLoggingService()
