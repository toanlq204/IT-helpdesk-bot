from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from services.faq_management_service import faq_manager
from services.chroma_service import chroma_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/faqs", tags=["FAQ Management"])

# Pydantic models for request/response


class FAQCreate(BaseModel):
    title: str
    text: str
    tags: Optional[List[str]] = []
    faq_id: Optional[str] = None


class FAQUpdate(BaseModel):
    title: str
    text: str
    tags: Optional[List[str]] = []


class FAQBulkCreate(BaseModel):
    faqs: List[Dict[str, Any]]


class AdminAction(BaseModel):
    admin_user: str = "admin"


@router.post("/add")
async def add_faq(faq: FAQCreate, admin_user: str = Query("admin", description="Admin user identifier")):
    """Add a new FAQ to the collection"""
    try:
        logger.info(f"Adding new FAQ by admin: {admin_user}")

        result = faq_manager.add_faq(
            title=faq.title,
            text=faq.text,
            tags=faq.tags or [],
            faq_id=faq.faq_id,
            admin_user=admin_user
        )

        if result["success"]:
            return {
                "success": True,
                "data": result,
                "message": "FAQ added successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=result.get(
                "error", "Failed to add FAQ"))

    except Exception as e:
        logger.error(f"Error adding FAQ: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update/{faq_id}")
async def update_faq(faq_id: str, faq: FAQUpdate, admin_user: str = Query("admin", description="Admin user identifier")):
    """Update an existing FAQ (delete then add again)"""
    try:
        logger.info(f"Updating FAQ {faq_id} by admin: {admin_user}")

        result = faq_manager.update_faq(
            faq_id=faq_id,
            title=faq.title,
            text=faq.text,
            tags=faq.tags or [],
            admin_user=admin_user
        )

        if result["success"]:
            return {
                "success": True,
                "data": result,
                "message": "FAQ updated successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=result.get(
                "error", "Failed to update FAQ"))

    except Exception as e:
        logger.error(f"Error updating FAQ: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{faq_id}")
async def delete_faq(faq_id: str, admin_user: str = Query("admin", description="Admin user identifier")):
    """Delete an FAQ from the collection"""
    try:
        logger.info(f"Deleting FAQ {faq_id} by admin: {admin_user}")

        result = faq_manager.delete_faq(
            faq_id=faq_id,
            admin_user=admin_user
        )

        if result["success"]:
            return {
                "success": True,
                "data": result,
                "message": "FAQ deleted successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=result.get(
                "error", "Failed to delete FAQ"))

    except Exception as e:
        logger.error(f"Error deleting FAQ: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-add")
async def bulk_add_faqs(bulk_data: FAQBulkCreate, admin_user: str = Query("admin", description="Admin user identifier")):
    """Add multiple FAQs in bulk"""
    try:
        logger.info(
            f"Bulk adding {len(bulk_data.faqs)} FAQs by admin: {admin_user}")

        result = faq_manager.bulk_add_faqs(
            faqs=bulk_data.faqs,
            admin_user=admin_user
        )

        return {
            "success": True,
            "data": result,
            "message": f"Bulk add completed: {result['successful_adds']}/{result['total_processed']} successful"
        }

    except Exception as e:
        logger.error(f"Error in bulk add: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex")
async def reindex_collection(admin_user: str = Query("admin", description="Admin user identifier")):
    """Trigger collection re-indexing"""
    try:
        logger.info(f"Re-indexing collection by admin: {admin_user}")

        result = faq_manager.reindex_collection(admin_user=admin_user)

        if result["success"]:
            return {
                "success": True,
                "data": result,
                "message": "Collection re-indexing completed"
            }
        else:
            raise HTTPException(status_code=400, detail=result.get(
                "error", "Failed to re-index collection"))

    except Exception as e:
        logger.error(f"Error re-indexing collection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_collection_status():
    """Get current collection status and management information"""
    try:
        logger.info("Getting collection status")

        status = faq_manager.get_collection_status()

        return {
            "success": True,
            "data": status,
            "message": "Collection status retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Error getting collection status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-log")
async def get_audit_log(limit: int = Query(50, description="Number of recent audit entries to retrieve")):
    """Get audit log of FAQ operations"""
    try:
        logger.info(f"Getting audit log (limit: {limit})")

        audit_entries = faq_manager.get_audit_log(limit=limit)

        return {
            "success": True,
            "data": {
                "entries": audit_entries,
                "total_retrieved": len(audit_entries)
            },
            "message": "Audit log retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Error getting audit log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_faqs():
    """Export current FAQ collection"""
    try:
        logger.info("Exporting FAQ collection")

        result = faq_manager.export_faqs()

        return {
            "success": True,
            "data": result,
            "message": "FAQ export completed"
        }

    except Exception as e:
        logger.error(f"Error exporting FAQs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_faqs_admin(
    query: str = Query(..., description="Search query"),
    n_results: int = Query(10, description="Number of results to return"),
    filter_tags: Optional[List[str]] = Query(
        None, description="Tags to filter by")
):
    """Search FAQs (admin view with additional details)"""
    try:
        logger.info(f"Admin FAQ search: {query}")

        results = chroma_service.search_faqs(
            query=query,
            n_results=n_results,
            filter_tags=filter_tags
        )

        # Add admin-specific details
        enhanced_results = []
        for result in results:
            enhanced_result = result.copy()
            # Convert back to distance
            enhanced_result["distance"] = 1 - result["similarity_score"]
            enhanced_result["admin_details"] = {
                "text_length": len(result.get("document", "")),
                "tag_count": len(result.get("tags", [])),
                "metadata_keys": list(result.get("metadata", {}).keys())
            }
            enhanced_results.append(enhanced_result)

        return {
            "success": True,
            "data": {
                "results": enhanced_results,
                "query": query,
                "total_found": len(enhanced_results)
            },
            "message": "Admin FAQ search completed"
        }

    except Exception as e:
        logger.error(f"Error in admin FAQ search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collection-stats")
async def get_detailed_collection_stats():
    """Get detailed collection statistics"""
    try:
        logger.info("Getting detailed collection stats")

        # Get basic stats from ChromaService
        basic_stats = chroma_service.get_collection_stats()

        # Get management stats from FAQ manager
        management_status = faq_manager.get_collection_status()

        # Combine all stats
        detailed_stats = {
            "chroma_stats": basic_stats,
            "management_stats": management_status.get("management_stats", {}),
            "audit_summary": management_status.get("audit_summary", {}),
            "system_health": {
                "collection_healthy": basic_stats.get("status") == "healthy",
                "reindex_needed": management_status.get("management_stats", {}).get("reindex_recommended", False),
                "total_operations": management_status.get("audit_summary", {}).get("total_operations", 0)
            }
        }

        return {
            "success": True,
            "data": detailed_stats,
            "message": "Detailed collection statistics retrieved"
        }

    except Exception as e:
        logger.error(f"Error getting detailed stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
