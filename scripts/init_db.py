#!/usr/bin/env python3
"""
Initialize database schema
Run this after setting up your Supabase connection
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import get_database
from src.utils.logging import setup_logging

logger = setup_logging("init_db")


async def init_database():
    """Initialize database schema"""
    try:
        db = get_database()
        await db.initialize()
        logger.info("Database initialized successfully!")
        
        # Add some sample knowledge articles
        logger.info("Adding sample knowledge articles...")
        
        await db.add_knowledge_article(
            "akrin-about",
            "About AKRIN",
            "AKRIN is a leading IT services company providing comprehensive technology solutions including IT support, cloud services, cybersecurity, and AI automation.",
            "company",
            "manual"
        )
        
        await db.add_knowledge_article(
            "akrin-services",
            "Our Services",
            "We offer: Managed IT Support, Cloud Solutions, Cybersecurity, Network Infrastructure, AI Automation, Web Development, and IT Consulting.",
            "services",
            "manual"
        )
        
        await db.add_knowledge_article(
            "akrin-contact",
            "Contact Information",
            "Contact us at: support@akrin.com | Phone: 1-800-AKRIN-IT | Business Hours: Monday-Friday 9AM-6PM EST",
            "contact",
            "manual"
        )
        
        logger.info("Sample knowledge articles added!")
        
        # Get stats
        stats = await db.get_conversation_stats()
        logger.info(f"Database stats: {stats}")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        # Close connections if using PostgreSQL
        if hasattr(db, 'close'):
            await db.close()


if __name__ == "__main__":
    asyncio.run(init_database())