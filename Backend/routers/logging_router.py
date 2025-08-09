from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from services.query_logging_service import query_logger
from datetime import datetime

router = APIRouter()

# Feedback models


class FeedbackRequest(BaseModel):
    log_id: str
    feedback: str  # correct, incorrect, partially_correct, unclear
    user_comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    success: bool
    message: str


class AdminFeedbackUpdate(BaseModel):
    feedback_id: str
    status: str  # pending_review, reviewed, resolved
    admin_notes: Optional[str] = None

# User feedback endpoints


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback_request: FeedbackRequest):
    """Submit user feedback for a query response"""
    try:
        success = query_logger.record_feedback(
            log_id=feedback_request.log_id,
            feedback=feedback_request.feedback,
            user_comment=feedback_request.user_comment
        )

        if success:
            return FeedbackResponse(
                success=True,
                message="Feedback recorded successfully"
            )
        else:
            return FeedbackResponse(
                success=False,
                message="Failed to record feedback"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/recent")
async def get_recent_logs(limit: int = Query(50, ge=1, le=100)):
    """Get recent query logs (admin use)"""
    try:
        logs = query_logger.get_recent_logs(limit=limit)
        return {"logs": logs, "count": len(logs)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{log_id}")
async def get_log_by_id(log_id: str):
    """Get a specific log entry by ID"""
    try:
        log_entry = query_logger.get_log_by_id(log_id)

        if log_entry:
            return log_entry
        else:
            raise HTTPException(status_code=404, detail="Log entry not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/queue")
async def get_feedback_queue(status: str = Query("pending_review")):
    """Get feedback queue for admin review"""
    try:
        feedback_items = query_logger.get_feedback_queue(status=status)
        return {
            "feedback_items": feedback_items,
            "count": len(feedback_items),
            "status_filter": status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/feedback/admin")
async def update_feedback_status(update_request: AdminFeedbackUpdate):
    """Update feedback item status (admin use)"""
    try:
        success = query_logger.update_feedback_status(
            feedback_id=update_request.feedback_id,
            status=update_request.status,
            admin_notes=update_request.admin_notes
        )

        if success:
            return {"success": True, "message": "Feedback status updated"}
        else:
            raise HTTPException(
                status_code=404, detail="Feedback item not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_analytics():
    """Get query and feedback analytics"""
    try:
        analytics = query_logger.get_analytics()
        return analytics

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/summary")
async def get_analytics_summary():
    """Get summarized analytics for dashboard"""
    try:
        analytics = query_logger.get_analytics()

        # Calculate key metrics
        total_queries = analytics.get("total_queries", 0)
        feedback_dist = analytics.get("feedback_distribution", {})
        confidence_dist = analytics.get("confidence_distribution", {})

        # Success rate (correct feedback / total feedback given)
        total_feedback = sum(feedback_dist.values()) - \
            feedback_dist.get("pending", 0)
        correct_feedback = feedback_dist.get("correct", 0)
        success_rate = (correct_feedback / max(total_feedback, 1)) * 100

        # High confidence queries
        high_confidence_count = confidence_dist.get("high", 0)
        high_confidence_rate = (
            high_confidence_count / max(total_queries, 1)) * 100

        summary = {
            "total_queries": total_queries,
            "success_rate": round(success_rate, 2),
            "high_confidence_rate": round(high_confidence_rate, 2),
            "pending_reviews": analytics.get("pending_feedback_reviews", 0),
            "average_confidence": round(analytics.get("average_confidence_score", 0), 3),
            "needs_attention": feedback_dist.get("incorrect", 0) + feedback_dist.get("unclear", 0)
        }

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
