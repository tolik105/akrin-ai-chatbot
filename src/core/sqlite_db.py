"""
SQLite database implementation for development
No external database service required!
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
import asyncio
from contextlib import asynccontextmanager
import aiosqlite

from src.utils.logging import setup_logging

logger = setup_logging("akrin.sqlite")


class SQLiteDatabase:
    """SQLite database for development - no Docker required"""
    
    def __init__(self, db_path: str = "./akrin_chatbot.db"):
        self.db_path = db_path
        self._initialized = False
    
    async def initialize(self):
        """Initialize database schema"""
        if self._initialized:
            return
            
        async with aiosqlite.connect(self.db_path) as db:
            # Enable foreign keys
            await db.execute("PRAGMA foreign_keys = ON")
            
            # Create users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_id TEXT UNIQUE,
                    email TEXT,
                    name TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create conversations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER REFERENCES users(id),
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    metadata TEXT
                )
            """)
            
            # Create messages table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER REFERENCES conversations(id),
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    intent TEXT,
                    confidence REAL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create knowledge_articles table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_articles (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT,
                    source TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            await db.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_articles(category)")
            
            await db.commit()
            
        self._initialized = True
        logger.info(f"SQLite database initialized at {self.db_path}")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection"""
        await self.initialize()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db
    
    # User methods
    async def create_user(self, external_id: str, email: Optional[str] = None, 
                         name: Optional[str] = None, metadata: Optional[Dict] = None) -> int:
        """Create a new user"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                """INSERT INTO users (external_id, email, name, metadata) 
                   VALUES (?, ?, ?, ?)""",
                (external_id, email, name, json.dumps(metadata or {}))
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_user_by_external_id(self, external_id: str) -> Optional[Dict]:
        """Get user by external ID"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM users WHERE external_id = ?", (external_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    # Conversation methods
    async def create_conversation(self, session_id: str, user_id: Optional[int] = None,
                                 metadata: Optional[Dict] = None) -> int:
        """Create a new conversation"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                """INSERT INTO conversations (session_id, user_id, metadata) 
                   VALUES (?, ?, ?)""",
                (session_id, user_id, json.dumps(metadata or {}))
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_conversation_by_session(self, session_id: str) -> Optional[Dict]:
        """Get conversation by session ID"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM conversations WHERE session_id = ?", (session_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def update_conversation_status(self, session_id: str, status: str):
        """Update conversation status"""
        async with self.get_connection() as db:
            await db.execute(
                """UPDATE conversations 
                   SET status = ?, ended_at = CURRENT_TIMESTAMP 
                   WHERE session_id = ?""",
                (status, session_id)
            )
            await db.commit()
    
    # Message methods
    async def add_message(self, conversation_id: int, role: str, content: str,
                         intent: Optional[str] = None, confidence: Optional[float] = None,
                         metadata: Optional[Dict] = None) -> int:
        """Add a message to conversation"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                """INSERT INTO messages 
                   (conversation_id, role, content, intent, confidence, metadata) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (conversation_id, role, content, intent, confidence, 
                 json.dumps(metadata or {}))
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_conversation_messages(self, conversation_id: int) -> List[Dict]:
        """Get all messages for a conversation"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                """SELECT * FROM messages 
                   WHERE conversation_id = ? 
                   ORDER BY created_at ASC""",
                (conversation_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Knowledge article methods
    async def add_knowledge_article(self, article_id: str, title: str, content: str,
                                   category: str, source: str = "manual",
                                   metadata: Optional[Dict] = None) -> str:
        """Add a knowledge article"""
        async with self.get_connection() as db:
            await db.execute(
                """INSERT OR REPLACE INTO knowledge_articles 
                   (id, title, content, category, source, metadata) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (article_id, title, content, category, source, 
                 json.dumps(metadata or {}))
            )
            await db.commit()
            return article_id
    
    async def get_knowledge_article(self, article_id: str) -> Optional[Dict]:
        """Get a knowledge article by ID"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM knowledge_articles WHERE id = ?", (article_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def search_knowledge_articles(self, query: str, category: Optional[str] = None,
                                       limit: int = 10) -> List[Dict]:
        """Simple text search for knowledge articles"""
        async with self.get_connection() as db:
            if category:
                cursor = await db.execute(
                    """SELECT * FROM knowledge_articles 
                       WHERE category = ? AND (
                           title LIKE ? OR content LIKE ?
                       ) LIMIT ?""",
                    (category, f"%{query}%", f"%{query}%", limit)
                )
            else:
                cursor = await db.execute(
                    """SELECT * FROM knowledge_articles 
                       WHERE title LIKE ? OR content LIKE ? 
                       LIMIT ?""",
                    (f"%{query}%", f"%{query}%", limit)
                )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Analytics methods
    async def get_conversation_stats(self, start_date: Optional[str] = None) -> Dict:
        """Get conversation statistics"""
        async with self.get_connection() as db:
            # Total conversations
            cursor = await db.execute("SELECT COUNT(*) as total FROM conversations")
            total = (await cursor.fetchone())['total']
            
            # Active conversations
            cursor = await db.execute(
                "SELECT COUNT(*) as active FROM conversations WHERE status = 'active'"
            )
            active = (await cursor.fetchone())['active']
            
            # Average messages per conversation
            cursor = await db.execute("""
                SELECT AVG(msg_count) as avg_messages FROM (
                    SELECT COUNT(*) as msg_count 
                    FROM messages 
                    GROUP BY conversation_id
                )
            """)
            avg_messages = (await cursor.fetchone())['avg_messages'] or 0
            
            return {
                'total_conversations': total,
                'active_conversations': active,
                'avg_messages_per_conversation': round(avg_messages, 2)
            }


# Singleton instance
_db_instance = None


def get_sqlite_db() -> SQLiteDatabase:
    """Get singleton SQLite database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SQLiteDatabase()
    return _db_instance