import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import uuid
from services.chroma_service import chroma_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FAQManagementService:
    """Service for managing FAQ operations: add, update, delete, and re-indexing"""

    def __init__(self, audit_log_path: str = "storage/logs/faq_audit.json"):
        """Initialize FAQ management service"""
        self.audit_log_path = audit_log_path
        self.changes_count = 0  # Track changes for re-indexing
        self.reindex_threshold = 10  # Re-index after 10 changes

        # Ensure audit log directory exists
        os.makedirs(os.path.dirname(audit_log_path), exist_ok=True)

        # Initialize audit log file
        self._init_audit_log()

        logger.info("FAQ management service initialized")

    def _init_audit_log(self):
        """Initialize audit log file if it doesn't exist"""
        if not os.path.exists(self.audit_log_path):
            with open(self.audit_log_path, 'w', encoding='utf-8') as f:
                json.dump({"operations": [], "metadata": {
                          "created": datetime.now().isoformat()}}, f, indent=2)

    def _log_operation(self, operation: str, faq_id: str, details: Dict[str, Any]):
        """Log FAQ operation for audit trail"""
        try:
            audit_entry = {
                "operation_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "faq_id": faq_id,
                "details": details,
                "admin_user": details.get("admin_user", "system")
            }

            # Load existing audit log
            with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                audit_data = json.load(f)

            # Add new operation
            audit_data["operations"].append(audit_entry)

            # Keep only last 1000 operations
            if len(audit_data["operations"]) > 1000:
                audit_data["operations"] = audit_data["operations"][-1000:]

            # Save updated audit log
            with open(self.audit_log_path, 'w', encoding='utf-8') as f:
                json.dump(audit_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Logged {operation} operation for FAQ {faq_id}")

        except Exception as e:
            logger.error(f"Failed to log operation: {str(e)}")

    def add_faq(self, title: str, text: str, tags: List[str] = None, faq_id: str = None, admin_user: str = "admin") -> Dict[str, Any]:
        """Add a new FAQ to the collection"""
        try:
            # Generate ID if not provided
            if not faq_id:
                faq_id = f"faq_{uuid.uuid4().hex[:8]}"

            # Validate input
            if not title.strip() or not text.strip():
                return {"success": False, "error": "Title and text cannot be empty"}

            # Check if FAQ with this ID already exists
            try:
                existing_stats = chroma_service.get_collection_stats()
                # We can't easily check for existing ID in ChromaDB, so we'll proceed
                # In a production system, you'd maintain a separate ID registry
            except Exception:
                pass

            # Add FAQ using ChromaService
            success = chroma_service.add_faq(faq_id, title, text, tags or [])

            if success:
                # Log the operation
                self._log_operation("add", faq_id, {
                    "title": title,
                    "text_length": len(text),
                    "tags": tags or [],
                    "admin_user": admin_user
                })

                # Increment changes counter
                self.changes_count += 1

                # Check if re-indexing is needed
                reindex_needed = self.changes_count >= self.reindex_threshold

                return {
                    "success": True,
                    "faq_id": faq_id,
                    "message": "FAQ added successfully",
                    "reindex_recommended": reindex_needed
                }
            else:
                return {"success": False, "error": "Failed to add FAQ to ChromaDB"}

        except Exception as e:
            logger.error(f"Failed to add FAQ: {str(e)}")
            return {"success": False, "error": str(e)}

    def update_faq(self, faq_id: str, title: str, text: str, tags: List[str] = None, admin_user: str = "admin") -> Dict[str, Any]:
        """Update an existing FAQ (delete then add again)"""
        try:
            # Validate input
            if not title.strip() or not text.strip():
                return {"success": False, "error": "Title and text cannot be empty"}

            # Get original FAQ for audit log (if possible)
            original_data = {
                "note": "Original data not retrievable from ChromaDB"}

            # Delete existing FAQ
            delete_success = chroma_service.delete_faq(faq_id)

            if not delete_success:
                return {"success": False, "error": "Failed to delete existing FAQ"}

            # Add updated FAQ
            add_success = chroma_service.add_faq(
                faq_id, title, text, tags or [])

            if add_success:
                # Log the operation
                self._log_operation("update", faq_id, {
                    "new_title": title,
                    "new_text_length": len(text),
                    "new_tags": tags or [],
                    "original_data": original_data,
                    "admin_user": admin_user
                })

                # Increment changes counter
                self.changes_count += 1

                # Check if re-indexing is needed
                reindex_needed = self.changes_count >= self.reindex_threshold

                return {
                    "success": True,
                    "faq_id": faq_id,
                    "message": "FAQ updated successfully",
                    "reindex_recommended": reindex_needed
                }
            else:
                # Try to restore original if possible
                logger.error(
                    f"Failed to add updated FAQ {faq_id} - data may be lost")
                return {"success": False, "error": "Failed to add updated FAQ - data may be lost"}

        except Exception as e:
            logger.error(f"Failed to update FAQ: {str(e)}")
            return {"success": False, "error": str(e)}

    def delete_faq(self, faq_id: str, admin_user: str = "admin") -> Dict[str, Any]:
        """Delete an FAQ from the collection"""
        try:
            # Get FAQ data for audit log (if possible)
            faq_data = {
                "note": "FAQ data not retrievable from ChromaDB before deletion"}

            # Delete FAQ using ChromaService
            success = chroma_service.delete_faq(faq_id)

            if success:
                # Log the operation
                self._log_operation("delete", faq_id, {
                    "deleted_data": faq_data,
                    "admin_user": admin_user
                })

                # Increment changes counter
                self.changes_count += 1

                # Check if re-indexing is needed
                reindex_needed = self.changes_count >= self.reindex_threshold

                return {
                    "success": True,
                    "faq_id": faq_id,
                    "message": "FAQ deleted successfully",
                    "reindex_recommended": reindex_needed
                }
            else:
                return {"success": False, "error": "Failed to delete FAQ from ChromaDB"}

        except Exception as e:
            logger.error(f"Failed to delete FAQ: {str(e)}")
            return {"success": False, "error": str(e)}

    def bulk_add_faqs(self, faqs: List[Dict[str, Any]], admin_user: str = "admin") -> Dict[str, Any]:
        """Add multiple FAQs in bulk"""
        try:
            results = []
            successful_adds = 0

            for faq in faqs:
                faq_id = faq.get("id") or f"faq_{uuid.uuid4().hex[:8]}"
                title = faq.get("title", "")
                text = faq.get("text", "")
                tags = faq.get("tags", [])

                result = self.add_faq(title, text, tags, faq_id, admin_user)
                results.append({"faq_id": faq_id, "result": result})

                if result["success"]:
                    successful_adds += 1

            return {
                "success": True,
                "total_processed": len(faqs),
                "successful_adds": successful_adds,
                "failed_adds": len(faqs) - successful_adds,
                "results": results,
                "reindex_recommended": self.changes_count >= self.reindex_threshold
            }

        except Exception as e:
            logger.error(f"Failed bulk add operation: {str(e)}")
            return {"success": False, "error": str(e)}

    def reindex_collection(self, admin_user: str = "admin") -> Dict[str, Any]:
        """Trigger collection re-indexing (ChromaDB handles this automatically, but we can reset our counter)"""
        try:
            # Get current collection stats
            stats = chroma_service.get_collection_stats()

            # Reset changes counter
            old_changes_count = self.changes_count
            self.changes_count = 0

            # Log the re-indexing operation
            self._log_operation("reindex", "collection", {
                "collection_stats": stats,
                "changes_since_last_reindex": old_changes_count,
                "admin_user": admin_user
            })

            logger.info("Collection re-indexing completed (counter reset)")

            return {
                "success": True,
                "message": "Collection re-indexing completed",
                "collection_stats": stats,
                "changes_processed": old_changes_count
            }

        except Exception as e:
            logger.error(f"Failed to re-index collection: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_collection_status(self) -> Dict[str, Any]:
        """Get current collection status and management info"""
        try:
            # Get ChromaDB stats
            chroma_stats = chroma_service.get_collection_stats()

            # Get audit log summary
            audit_summary = self._get_audit_summary()

            return {
                "collection_stats": chroma_stats,
                "management_stats": {
                    "changes_since_reindex": self.changes_count,
                    "reindex_threshold": self.reindex_threshold,
                    "reindex_recommended": self.changes_count >= self.reindex_threshold
                },
                "audit_summary": audit_summary
            }

        except Exception as e:
            logger.error(f"Failed to get collection status: {str(e)}")
            return {"error": str(e)}

    def _get_audit_summary(self) -> Dict[str, Any]:
        """Get summary of recent audit operations"""
        try:
            with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                audit_data = json.load(f)

            operations = audit_data.get("operations", [])

            # Count operations by type
            operation_counts = {}
            recent_operations = []

            for op in operations[-50:]:  # Last 50 operations
                op_type = op.get("operation", "unknown")
                operation_counts[op_type] = operation_counts.get(
                    op_type, 0) + 1
                recent_operations.append({
                    "timestamp": op.get("timestamp"),
                    "operation": op_type,
                    "faq_id": op.get("faq_id"),
                    "admin_user": op.get("details", {}).get("admin_user", "unknown")
                })

            return {
                "total_operations": len(operations),
                "operation_counts": operation_counts,
                # Last 10 for summary
                "recent_operations": recent_operations[-10:]
            }

        except Exception as e:
            logger.error(f"Failed to get audit summary: {str(e)}")
            return {"error": str(e)}

    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        try:
            with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                audit_data = json.load(f)

            operations = audit_data.get("operations", [])
            return operations[-limit:] if len(operations) > limit else operations

        except Exception as e:
            logger.error(f"Failed to get audit log: {str(e)}")
            return []

    def export_faqs(self) -> Dict[str, Any]:
        """Export current FAQ collection (note: ChromaDB doesn't easily support full export)"""
        try:
            # This is a limitation of ChromaDB - we can't easily export all FAQs
            # In a production system, you'd maintain a separate database for this
            stats = chroma_service.get_collection_stats()

            return {
                "success": True,
                "message": "FAQ export completed (limited by ChromaDB capabilities)",
                "collection_stats": stats,
                "note": "For full export capability, consider maintaining a separate FAQ database"
            }

        except Exception as e:
            logger.error(f"Failed to export FAQs: {str(e)}")
            return {"success": False, "error": str(e)}


# Global instance
faq_manager = FAQManagementService()
