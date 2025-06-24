# AKRIN AI Chatbot - Quick Start Guide

## Prerequisites

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- Git

## Installation

### 1. Clone the Repository

```bash
cd /Users/roma/Downloads/AKRIN-team/akrin-ai-chatbot
```

### 2. Run Setup Script

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Download spaCy language models
- Create necessary directories
- Copy `.env.example` to `.env`

### 3. Configure Environment

Edit `.env` file with your API keys:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here

# Database passwords
POSTGRES_PASSWORD=secure_password_here
JWT_SECRET_KEY=your_very_secure_secret_key_here
```

### 4. Start Infrastructure

```bash
# Start all Docker services
make docker-up

# Or start specific services
docker-compose up -d postgres mongodb redis
```

### 5. Initialize Database

```bash
# Activate virtual environment
source venv/bin/activate

# Run database initialization
python scripts/init_db.py
```

### 6. Start Development Server

```bash
# Using Make
make dev

# Or directly
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Verify Installation

### 1. Check API Health

```bash
# Basic health check
curl http://localhost:8000/api/health

# Detailed health check
curl http://localhost:8000/api/health/detailed
```

### 2. Access API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### 3. Run Tests

```bash
# Run all tests
make test

# Or with pytest directly
pytest tests/ -v
```

## Quick API Test

### Send a Chat Message

```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I need help with my password",
    "session_id": "test-session-001"
  }'
```

### Create Knowledge Article

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/articles \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Password Reset Guide",
    "content": "To reset your password, follow these steps...",
    "category": "authentication",
    "tags": ["password", "reset", "security"]
  }'
```

## Development Workflow

### 1. Code Formatting

```bash
make format
```

### 2. Linting

```bash
make lint
```

### 3. Monitoring

```bash
# View logs
make docker-logs

# Access monitoring dashboards
make monitor
```

This opens:
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Kibana: http://localhost:5601

## Common Issues

### 1. Port Already in Use

If port 8000 is already in use:

```bash
# Find process using port
lsof -i :8000

# Or use a different port
uvicorn src.api.main:app --port 8001
```

### 2. Database Connection Failed

Check Docker services are running:

```bash
docker-compose ps
```

Ensure `.env` has correct database credentials.

### 3. Missing Dependencies

```bash
# Reinstall dependencies
pip install -r requirements.txt

# For spaCy model
python -m spacy download en_core_web_md
```

## Next Steps

1. **Seed Knowledge Base**: Add initial content to the knowledge base
2. **Configure Integrations**: Set up CRM and ticketing system connections
3. **Train NLU Models**: Improve intent recognition with custom training data
4. **Deploy Web Widget**: Integrate the chat widget into your website

For detailed documentation, see:
- [Architecture Guide](ARCHITECTURE.md)
- [API Reference](API_REFERENCE.md)
- [Deployment Guide](DEPLOYMENT.md)