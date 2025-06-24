"""
PostgreSQL database implementation for production with Supabase
"""

import json
from datetime import datetime
from typing import List, Dict, Optional, Any
import asyncio
from contextlib import asynccontextmanager
import asyncpg
from asyncpg import Pool
import os

from src.utils.logging import setup_logging

logger = setup_logging("akrin.postgres")


class PostgresDatabase:
    """PostgreSQL database for production with Supabase"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self._pool: Optional[Pool] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection pool and schema"""
        if self._initialized:
            return
            
        # Create connection pool
        self._pool = await asyncpg.create_pool(
            self.database_url,
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        
        # Initialize schema
        async with self._pool.acquire() as conn:
            # Create users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    external_id TEXT UNIQUE,
                    email TEXT,
                    name TEXT,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create conversations table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER REFERENCES users(id),
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    metadata JSONB DEFAULT '{}'
                )
            """)
            
            # Create messages table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id INTEGER REFERENCES conversations(id),
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    intent TEXT,
                    confidence REAL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create knowledge_articles table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_articles (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT,
                    source TEXT,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_articles(category)")
            
            # Create full-text search index for knowledge articles
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_search 
                ON knowledge_articles 
                USING GIN (to_tsvector('english', title || ' ' || content))
            """)
            
        self._initialized = True
        logger.info("PostgreSQL database initialized with Supabase")
    
    async def close(self):
        """Close database connection pool"""
        if self._pool:
            await self._pool.close()
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self._initialized:
            await self.initialize()
        async with self._pool.acquire() as conn:
            yield conn
    
    # User methods
    async def create_user(self, external_id: str, email: Optional[str] = None, 
                         name: Optional[str] = None, metadata: Optional[Dict] = None) -> int:
        """Create a new user"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                """INSERT INTO users (external_id, email, name, metadata) 
                   VALUES ($1, $2, $3, $4)
                   RETURNING id""",
                external_id, email, name, json.dumps(metadata or {})
            )
            return row['id']
    
    async def get_user_by_external_id(self, external_id: str) -> Optional[Dict]:
        """Get user by external ID"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE external_id = $1", external_id
            )
            return dict(row) if row else None
    
    # Conversation methods
    async def create_conversation(self, session_id: str, user_id: Optional[int] = None,
                                 metadata: Optional[Dict] = None) -> int:
        """Create a new conversation"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                """INSERT INTO conversations (session_id, user_id, metadata) 
                   VALUES ($1, $2, $3)
                   RETURNING id""",
                session_id, user_id, json.dumps(metadata or {})
            )
            return row['id']
    
    async def get_conversation_by_session(self, session_id: str) -> Optional[Dict]:
        """Get conversation by session ID"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM conversations WHERE session_id = $1", session_id
            )
            return dict(row) if row else None
    
    async def update_conversation_status(self, session_id: str, status: str):
        """Update conversation status"""
        async with self.get_connection() as conn:
            await conn.execute(
                """UPDATE conversations 
                   SET status = $1, ended_at = CURRENT_TIMESTAMP 
                   WHERE session_id = $2""",
                status, session_id
            )
    
    # Message methods
    async def add_message(self, conversation_id: int, role: str, content: str,
                         intent: Optional[str] = None, confidence: Optional[float] = None,
                         metadata: Optional[Dict] = None) -> int:
        """Add a message to conversation"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                """INSERT INTO messages 
                   (conversation_id, role, content, intent, confidence, metadata) 
                   VALUES ($1, $2, $3, $4, $5, $6)
                   RETURNING id""",
                conversation_id, role, content, intent, confidence, 
                json.dumps(metadata or {})
            )
            return row['id']
    
    async def get_conversation_messages(self, conversation_id: int) -> List[Dict]:
        """Get all messages for a conversation"""
        async with self.get_connection() as conn:
            rows = await conn.fetch(
                """SELECT * FROM messages 
                   WHERE conversation_id = $1 
                   ORDER BY created_at ASC""",
                conversation_id
            )
            return [dict(row) for row in rows]
    
    # Knowledge article methods
    async def add_knowledge_article(self, article_id: str, title: str, content: str,
                                   category: str, source: str = "manual",
                                   metadata: Optional[Dict] = None) -> str:
        """Add a knowledge article"""
        async with self.get_connection() as conn:
            await conn.execute(
                """INSERT INTO knowledge_articles 
                   (id, title, content, category, source, metadata) 
                   VALUES ($1, $2, $3, $4, $5, $6)
                   ON CONFLICT (id) DO UPDATE SET
                   title = $2, content = $3, category = $4, 
                   source = $5, metadata = $6, updated_at = CURRENT_TIMESTAMP""",
                article_id, title, content, category, source, 
                json.dumps(metadata or {})
            )
            return article_id
    
    async def get_knowledge_article(self, article_id: str) -> Optional[Dict]:
        """Get a knowledge article by ID"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM knowledge_articles WHERE id = $1", article_id
            )
            return dict(row) if row else None
    
    async def search_knowledge_articles(self, query: str, category: Optional[str] = None,
                                       limit: int = 10) -> List[Dict]:
        """Full-text search for knowledge articles using PostgreSQL"""
        async with self.get_connection() as conn:
            if category:
                rows = await conn.fetch(
                    """SELECT * FROM knowledge_articles 
                       WHERE category = $1 AND 
                       to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', $2)
                       ORDER BY ts_rank(to_tsvector('english', title || ' ' || content), 
                                       plainto_tsquery('english', $2)) DESC
                       LIMIT $3""",
                    category, query, limit
                )
            else:
                rows = await conn.fetch(
                    """SELECT * FROM knowledge_articles 
                       WHERE to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', $1)
                       ORDER BY ts_rank(to_tsvector('english', title || ' ' || content), 
                                       plainto_tsquery('english', $1)) DESC
                       LIMIT $2""",
                    query, limit
                )
            return [dict(row) for row in rows]
    
    # Analytics methods
    async def get_conversation_stats(self, start_date: Optional[str] = None) -> Dict:
        """Get conversation statistics"""
        async with self.get_connection() as conn:
            # Total conversations
            total = await conn.fetchval("SELECT COUNT(*) FROM conversations")
            
            # Active conversations
            active = await conn.fetchval(
                "SELECT COUNT(*) FROM conversations WHERE status = 'active'"
            )
            
            # Average messages per conversation
            avg_messages = await conn.fetchval("""
                SELECT AVG(msg_count)::float FROM (
                    SELECT COUNT(*) as msg_count 
                    FROM messages 
                    GROUP BY conversation_id
                ) sub
            """) or 0
            
            return {
                'total_conversations': total,
                'active_conversations': active,
                'avg_messages_per_conversation': round(avg_messages, 2)
            }


# Singleton instance
_db_instance = None


def get_postgres_db() -> PostgresDatabase:
    """Get singleton PostgreSQL database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = PostgresDatabase()
    return _db_instance