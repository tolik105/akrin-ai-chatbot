"""
In-memory cache implementation
Replaces Redis for development - no external service required!
"""

import asyncio
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import json
from collections import OrderedDict
import pickle

from src.utils.logging import setup_logging

logger = setup_logging("akrin.cache")


class CacheItem:
    """Single cache item with expiration"""
    
    def __init__(self, value: Any, ttl: Optional[int] = None):
        self.value = value
        self.created_at = datetime.utcnow()
        self.ttl = ttl  # Time to live in seconds
    
    def is_expired(self) -> bool:
        """Check if item has expired"""
        if self.ttl is None:
            return False
        
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl


class InMemoryCache:
    """In-memory cache with TTL support"""
    
    def __init__(self, max_size: int = 10000):
        self.cache: OrderedDict[str, CacheItem] = OrderedDict()
        self.max_size = max_size
        self._lock = asyncio.Lock()
        self._cleanup_task = None
        
    async def start(self):
        """Start background cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())
            logger.info("In-memory cache started")
    
    async def stop(self):
        """Stop background cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("In-memory cache stopped")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            if key in self.cache:
                item = self.cache[key]
                if not item.is_expired():
                    # Move to end (LRU)
                    self.cache.move_to_end(key)
                    return item.value
                else:
                    # Remove expired item
                    del self.cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional TTL (in seconds)"""
        async with self._lock:
            # Remove oldest items if at capacity
            while len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            
            self.cache[key] = CacheItem(value, ttl)
            # Move to end (most recently used)
            self.cache.move_to_end(key)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        async with self._lock:
            if key in self.cache:
                item = self.cache[key]
                if not item.is_expired():
                    return True
                else:
                    del self.cache[key]
            return False
    
    async def clear(self):
        """Clear all cache entries"""
        async with self._lock:
            self.cache.clear()
            logger.info("Cache cleared")
    
    async def size(self) -> int:
        """Get current cache size"""
        async with self._lock:
            return len(self.cache)
    
    async def _cleanup_expired(self):
        """Background task to clean up expired items"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                async with self._lock:
                    expired_keys = []
                    for key, item in self.cache.items():
                        if item.is_expired():
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        del self.cache[key]
                    
                    if expired_keys:
                        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")


class SessionStore:
    """Simple session storage using in-memory cache"""
    
    def __init__(self, cache: InMemoryCache):
        self.cache = cache
        self.session_prefix = "session:"
        self.default_ttl = 3600  # 1 hour
    
    async def get(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        key = f"{self.session_prefix}{session_id}"
        data = await self.cache.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def set(self, session_id: str, data: Dict, ttl: Optional[int] = None):
        """Set session data"""
        key = f"{self.session_prefix}{session_id}"
        ttl = ttl or self.default_ttl
        await self.cache.set(key, json.dumps(data), ttl)
    
    async def delete(self, session_id: str):
        """Delete session"""
        key = f"{self.session_prefix}{session_id}"
        await self.cache.delete(key)
    
    async def exists(self, session_id: str) -> bool:
        """Check if session exists"""
        key = f"{self.session_prefix}{session_id}"
        return await self.cache.exists(key)


class RateLimiter:
    """Simple rate limiter using in-memory cache"""
    
    def __init__(self, cache: InMemoryCache):
        self.cache = cache
        self.limiter_prefix = "rate_limit:"
    
    async def is_allowed(self, 
                        identifier: str, 
                        max_requests: int, 
                        window_seconds: int) -> bool:
        """Check if request is allowed under rate limit"""
        key = f"{self.limiter_prefix}{identifier}:{window_seconds}"
        
        # Get current count
        current = await self.cache.get(key)
        if current is None:
            # First request in window
            await self.cache.set(key, 1, ttl=window_seconds)
            return True
        
        current_count = int(current)
        if current_count >= max_requests:
            return False
        
        # Increment counter
        await self.cache.set(key, current_count + 1, ttl=window_seconds)
        return True
    
    async def get_remaining(self, 
                           identifier: str, 
                           max_requests: int, 
                           window_seconds: int) -> int:
        """Get remaining requests in window"""
        key = f"{self.limiter_prefix}{identifier}:{window_seconds}"
        current = await self.cache.get(key)
        
        if current is None:
            return max_requests
        
        return max(0, max_requests - int(current))


# Singleton instances
_cache_instance = None
_session_store_instance = None
_rate_limiter_instance = None


def get_cache() -> InMemoryCache:
    """Get singleton cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = InMemoryCache()
    return _cache_instance


def get_session_store() -> SessionStore:
    """Get singleton session store instance"""
    global _session_store_instance
    if _session_store_instance is None:
        _session_store_instance = SessionStore(get_cache())
    return _session_store_instance


def get_rate_limiter() -> RateLimiter:
    """Get singleton rate limiter instance"""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter(get_cache())
    return _rate_limiter_instance