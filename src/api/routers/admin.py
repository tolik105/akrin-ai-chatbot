"""
Admin API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import jwt

from src.core.config import settings
from src.utils.logging import security_logger as logger

router = APIRouter()
security = HTTPBearer()


class AdminUser(BaseModel):
    """Admin user model"""
    username: str
    email: str
    role: str
    created_at: datetime


class SystemConfig(BaseModel):
    """System configuration model"""
    feature_flags: Dict[str, bool]
    rate_limits: Dict[str, int]
    llm_settings: Dict[str, Any]


class AnalyticsReport(BaseModel):
    """Analytics report model"""
    period: str
    total_conversations: int
    total_messages: int
    resolution_rate: float
    avg_response_time_ms: float
    human_handoff_rate: float
    top_intents: List[Dict[str, Any]]
    user_satisfaction: Optional[float] = None


def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin JWT token"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check if user has admin role
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
            
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/config", response_model=SystemConfig)
async def get_system_config(admin=Depends(verify_admin_token)):
    """
    Get current system configuration
    """
    try:
        config = SystemConfig(
            feature_flags={
                "human_handoff": settings.enable_human_handoff,
                "voice_support": settings.enable_voice_support,
                "analytics": settings.enable_analytics
            },
            rate_limits={
                "per_minute": settings.rate_limit_requests_per_minute,
                "per_hour": settings.rate_limit_requests_per_hour
            },
            llm_settings={
                "model": settings.default_llm_model,
                "temperature": settings.llm_temperature,
                "max_tokens": settings.llm_max_tokens
            }
        )
        
        logger.info(f"Admin {admin['username']} accessed system config")
        
        return config
        
    except Exception as e:
        logger.error(f"Error fetching config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch configuration")


@router.put("/config")
async def update_system_config(
    config: SystemConfig,
    admin=Depends(verify_admin_token)
):
    """
    Update system configuration
    """
    try:
        # TODO: Implement configuration update
        # TODO: Trigger configuration reload across services
        
        logger.info(f"Admin {admin['username']} updated system config")
        
        return {"status": "updated", "config": config}
        
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update configuration")


@router.get("/analytics", response_model=AnalyticsReport)
async def get_analytics(
    period: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    admin=Depends(verify_admin_token)
):
    """
    Get analytics report for specified period
    """
    try:
        # Calculate time range
        now = datetime.utcnow()
        period_map = {
            "1h": timedelta(hours=1),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        start_time = now - period_map[period]
        
        # TODO: Implement actual analytics queries
        
        # Mock data for now
        report = AnalyticsReport(
            period=period,
            total_conversations=1234,
            total_messages=5678,
            resolution_rate=0.65,
            avg_response_time_ms=450.5,
            human_handoff_rate=0.15,
            top_intents=[
                {"intent": "tech_support", "count": 234, "percentage": 0.35},
                {"intent": "password_reset", "count": 156, "percentage": 0.23},
                {"intent": "billing_inquiry", "count": 89, "percentage": 0.13}
            ],
            user_satisfaction=4.2
        )
        
        logger.info(f"Admin {admin['username']} accessed analytics for period {period}")
        
        return report
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")


@router.get("/conversations")
async def list_conversations(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin=Depends(verify_admin_token)
):
    """
    List conversations with optional filtering
    """
    try:
        # TODO: Implement database query
        
        logger.info(f"Admin {admin['username']} listed conversations")
        
        return {
            "conversations": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list conversations")


@router.get("/conversations/{conversation_id}")
async def get_conversation_details(
    conversation_id: str,
    admin=Depends(verify_admin_token)
):
    """
    Get detailed conversation transcript
    """
    try:
        # TODO: Implement database query
        
        logger.info(f"Admin {admin['username']} accessed conversation {conversation_id}")
        
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    except Exception as e:
        logger.error(f"Error fetching conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversation")


@router.post("/broadcast")
async def send_broadcast_message(
    message: Dict[str, str],
    admin=Depends(verify_admin_token)
):
    """
    Send broadcast message to active conversations
    """
    try:
        # TODO: Implement broadcast functionality
        
        logger.info(f"Admin {admin['username']} sent broadcast message")
        
        return {
            "status": "broadcast_sent",
            "recipients": 0,
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Error sending broadcast: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send broadcast")


@router.post("/model/reload")
async def reload_models(admin=Depends(verify_admin_token)):
    """
    Trigger model reload across services
    """
    try:
        # TODO: Implement model reload mechanism
        
        logger.info(f"Admin {admin['username']} triggered model reload")
        
        return {
            "status": "reload_initiated",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error reloading models: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reload models")


@router.post("/cache/clear")
async def clear_cache(
    cache_type: str = Query(..., regex="^(all|knowledge|conversations|redis)$"),
    admin=Depends(verify_admin_token)
):
    """
    Clear specified cache
    """
    try:
        # TODO: Implement cache clearing
        
        logger.info(f"Admin {admin['username']} cleared {cache_type} cache")
        
        return {
            "status": "cache_cleared",
            "cache_type": cache_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/logs")
async def get_recent_logs(
    level: Optional[str] = Query(None, regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    service: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    admin=Depends(verify_admin_token)
):
    """
    Get recent application logs
    """
    try:
        # TODO: Implement log retrieval from Elasticsearch
        
        logger.info(f"Admin {admin['username']} accessed logs")
        
        return {
            "logs": [],
            "total": 0,
            "filters": {
                "level": level,
                "service": service
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch logs")