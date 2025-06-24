#!/bin/bash

# AKRIN AI Chatbot Setup Script
# This script sets up the development environment

set -e

echo "🚀 AKRIN AI Chatbot - Development Environment Setup"
echo "=================================================="

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi
echo "✅ Python version: $python_version"

# Check Node.js
echo "📌 Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed. Please install Node.js 18+"
    exit 1
fi
node_version=$(node --version)
echo "✅ Node.js version: $node_version"

# Check Docker
echo "📌 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed. Please install Docker"
    exit 1
fi
echo "✅ Docker is installed"

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Download spaCy language model
echo "📦 Downloading spaCy language model..."
python -m spacy download en_core_web_md

# Create necessary directories
echo "📁 Creating additional directories..."
mkdir -p logs
mkdir -p data/knowledge_base
mkdir -p data/models
mkdir -p data/uploads
mkdir -p static/js
mkdir -p static/css
mkdir -p templates

# Copy environment file
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your API keys and configuration"
else
    echo "✅ .env file already exists"
fi

# Initialize git hooks (if in git repo)
if [ -d .git ]; then
    echo "📌 Setting up git hooks..."
    pip install pre-commit
    pre-commit install
fi

# Create initial package.json for frontend dependencies
echo "📦 Creating package.json..."
cat > package.json << 'EOF'
{
  "name": "akrin-ai-chatbot",
  "version": "1.0.0",
  "description": "AKRIN AI Customer Service Chatbot",
  "scripts": {
    "dev": "webpack serve --mode development",
    "build": "webpack --mode production",
    "test": "jest",
    "lint": "eslint src/ui/**/*.js"
  },
  "dependencies": {
    "axios": "^1.6.0",
    "socket.io-client": "^4.5.4"
  },
  "devDependencies": {
    "@babel/core": "^7.23.0",
    "@babel/preset-env": "^7.23.0",
    "babel-loader": "^9.1.3",
    "css-loader": "^6.8.1",
    "eslint": "^8.52.0",
    "jest": "^29.7.0",
    "style-loader": "^3.3.3",
    "webpack": "^5.89.0",
    "webpack-cli": "^5.1.4",
    "webpack-dev-server": "^4.15.1"
  }
}
EOF

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Create initial database schema
echo "📊 Creating database schema script..."
cat > scripts/init_db.py << 'EOF'
#!/usr/bin/env python3
"""Initialize database schema for AKRIN AI Chatbot"""

import asyncio
import os
from dotenv import load_dotenv
import asyncpg
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

async def init_postgres():
    """Initialize PostgreSQL schema"""
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB')
    )
    
    # Create tables
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            external_id VARCHAR(255) UNIQUE,
            email VARCHAR(255),
            name VARCHAR(255),
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            user_id INTEGER REFERENCES users(id),
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            status VARCHAR(50) DEFAULT 'active',
            metadata JSONB
        );
        
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER REFERENCES conversations(id),
            role VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            intent VARCHAR(100),
            confidence FLOAT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
    ''')
    
    await conn.close()
    print("✅ PostgreSQL schema initialized")

async def init_mongodb():
    """Initialize MongoDB collections and indexes"""
    client = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = client.akrin_chatbot
    
    # Create collections with validation
    try:
        await db.create_collection("knowledge_articles", validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["title", "content", "category", "embedding"],
                "properties": {
                    "title": {"bsonType": "string"},
                    "content": {"bsonType": "string"},
                    "category": {"bsonType": "string"},
                    "embedding": {"bsonType": "array"},
                    "metadata": {"bsonType": "object"}
                }
            }
        })
    except:
        pass  # Collection already exists
    
    # Create indexes
    await db.knowledge_articles.create_index("category")
    await db.knowledge_articles.create_index([("title", "text"), ("content", "text")])
    
    print("✅ MongoDB collections initialized")

async def main():
    """Run all initialization tasks"""
    await init_postgres()
    await init_mongodb()

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x scripts/init_db.py

# Success message
echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your API keys and configuration"
echo "2. Start Docker services: make docker-up"
echo "3. Initialize database: python scripts/init_db.py"
echo "4. Run development server: make dev"
echo ""
echo "For more information, see docs/README.md"