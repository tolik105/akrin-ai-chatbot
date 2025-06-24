"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import asyncio
import aioredis
import asyncpg
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

from src.core.config import settings
from src.utils.logging import setup_logging

router = APIRouter()
logger = setup_logging("akrin.health")


async def check_postgres() -> Dict[str, Any]:
    """Check PostgreSQL connectivity"""
    try:
        conn = await asyncpg.connect(settings.postgres_url)
        await conn.fetchval("SELECT 1")
        await conn.close()
        return {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}


async def check_mongodb() -> Dict[str, Any]:
    """Check MongoDB connectivity"""
    try:
        client = AsyncIOMotorClient(settings.mongodb_uri)
        await client.admin.command('ping')
        return {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        logger.error(f"MongoDB health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}


async def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        redis = await aioredis.from_url(settings.redis_url)
        await redis.ping()
        await redis.close()
        return {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AKRIN AI Chatbot",
        "version": "1.0.0"
    }


@router.get("/live")
async def liveness_probe():
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@router.get("/ready")
async def readiness_probe():
    """Kubernetes readiness probe"""
    # Check all dependencies
    checks = await asyncio.gather(
        check_postgres(),
        check_mongodb(),
        check_redis(),
        return_exceptions=True
    )
    
    # Determine overall health
    all_healthy = all(
        isinstance(check, dict) and check.get("status") == "healthy"
        for check in checks
    )
    
    response = {
        "status": "ready" if all_healthy else "not_ready",
        "checks": {
            "postgres": checks[0] if isinstance(checks[0], dict) else {"status": "error", "error": str(checks[0])},
            "mongodb": checks[1] if isinstance(checks[1], dict) else {"status": "error", "error": str(checks[1])},
            "redis": checks[2] if isinstance(checks[2], dict) else {"status": "error", "error": str(checks[2])}
        }
    }
    
    return response


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with all components"""
    
    # Run all checks in parallel
    postgres_task = check_postgres()
    mongodb_task = check_mongodb()
    redis_task = check_redis()
    
    postgres_health, mongodb_health, redis_health = await asyncio.gather(
        postgres_task, mongodb_task, redis_task
    )
    
    # Check API keys
    api_keys_configured = {
        "openai": bool(settings.openai_api_key),
        "anthropic": bool(settings.anthropic_api_key),
        "google_ai": bool(settings.google_ai_api_key),
        "pinecone": bool(settings.pinecone_api_key)
    }
    
    # Feature flags
    features = {
        "human_handoff": settings.enable_human_handoff,
        "voice_support": settings.enable_voice_support,
        "analytics": settings.enable_analytics
    }
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.app_env,
        "components": {
            "postgres": postgres_health,
            "mongodb": mongodb_health,
            "redis": redis_health,
            "api_keys": api_keys_configured,
            "features": features
        },
        "configuration": {
            "max_conversation_turns": settings.max_conversation_turns,
            "rate_limits": {
                "per_minute": settings.rate_limit_requests_per_minute,
                "per_hour": settings.rate_limit_requests_per_hour
            }
        }
    }