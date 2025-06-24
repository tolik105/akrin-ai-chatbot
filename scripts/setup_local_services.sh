#!/bin/bash

# Setup script for running services without Docker
# This script helps install and configure services locally

set -e

echo "🚀 AKRIN AI Chatbot - Local Services Setup (No Docker)"
echo "===================================================="

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

echo "📌 Detected OS: $OS"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Homebrew on macOS if not present
if [[ "$OS" == "macos" ]] && ! command_exists brew; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# PostgreSQL Installation
echo ""
echo "📊 PostgreSQL Setup"
echo "=================="

if command_exists psql; then
    echo "✅ PostgreSQL is already installed"
else
    echo "📦 Installing PostgreSQL..."
    if [[ "$OS" == "macos" ]]; then
        brew install postgresql@15
        brew services start postgresql@15
    else
        sudo apt-get update
        sudo apt-get install -y postgresql postgresql-contrib
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    fi
fi

# Create database and user
echo "📌 Setting up PostgreSQL database..."
if [[ "$OS" == "macos" ]]; then
    createdb akrin_chatbot 2>/dev/null || echo "Database already exists"
else
    sudo -u postgres createdb akrin_chatbot 2>/dev/null || echo "Database already exists"
    sudo -u postgres psql -c "CREATE USER chatbot_user WITH PASSWORD 'akrin_secure_password_2024';" 2>/dev/null || echo "User already exists"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE akrin_chatbot TO chatbot_user;" 2>/dev/null || echo "Privileges already granted"
fi

# Redis Installation
echo ""
echo "🔴 Redis Setup"
echo "============="

if command_exists redis-server; then
    echo "✅ Redis is already installed"
else
    echo "📦 Installing Redis..."
    if [[ "$OS" == "macos" ]]; then
        brew install redis
        brew services start redis
    else
        sudo apt-get install -y redis-server
        sudo systemctl start redis-server
        sudo systemctl enable redis-server
    fi
fi

# MongoDB Installation (Optional - for development)
echo ""
echo "🍃 MongoDB Setup (Optional)"
echo "========================="

if command_exists mongod; then
    echo "✅ MongoDB is already installed"
else
    echo "📦 MongoDB is optional. To install:"
    if [[ "$OS" == "macos" ]]; then
        echo "   brew tap mongodb/brew"
        echo "   brew install mongodb-community"
        echo "   brew services start mongodb-community"
    else
        echo "   Follow instructions at: https://docs.mongodb.com/manual/administration/install-on-linux/"
    fi
fi

# Create directories for data
echo ""
echo "📁 Creating data directories..."
mkdir -p ~/akrin_chatbot_data/{postgres,redis,logs}

# Generate systemd service files for Linux
if [[ "$OS" == "linux" ]]; then
    echo ""
    echo "📝 Creating systemd service files..."
    
    # PostgreSQL is already managed by systemd
    # Redis is already managed by systemd
    
    echo "✅ Services are managed by systemd"
    echo "   Use: sudo systemctl {start|stop|status} {postgresql|redis-server}"
fi

# Generate launchd plist files for macOS
if [[ "$OS" == "macos" ]]; then
    echo ""
    echo "📝 Services on macOS are managed by brew services"
    echo "   Use: brew services {start|stop|status} {postgresql@15|redis}"
fi

# Create a simple process manager script
cat > start_services.sh << 'EOF'
#!/bin/bash

# Simple script to start all services

echo "🚀 Starting AKRIN Chatbot Services..."

# Check and start PostgreSQL
if command -v pg_ctl >/dev/null 2>&1; then
    if ! pg_isready >/dev/null 2>&1; then
        echo "Starting PostgreSQL..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew services start postgresql@15
        else
            sudo systemctl start postgresql
        fi
    else
        echo "PostgreSQL is already running"
    fi
fi

# Check and start Redis
if command -v redis-cli >/dev/null 2>&1; then
    if ! redis-cli ping >/dev/null 2>&1; then
        echo "Starting Redis..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew services start redis
        else
            sudo systemctl start redis-server
        fi
    else
        echo "Redis is already running"
    fi
fi

echo "✅ All services started!"
echo ""
echo "To start the chatbot API:"
echo "  source venv/bin/activate"
echo "  python -m uvicorn src.api.main:app --reload"
EOF

chmod +x start_services.sh

# Create a stop script
cat > stop_services.sh << 'EOF'
#!/bin/bash

# Simple script to stop all services

echo "🛑 Stopping AKRIN Chatbot Services..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    brew services stop postgresql@15
    brew services stop redis
else
    sudo systemctl stop postgresql
    sudo systemctl stop redis-server
fi

echo "✅ All services stopped!"
EOF

chmod +x stop_services.sh

# Success message
echo ""
echo "✅ Local services setup completed!"
echo ""
echo "📋 Summary:"
echo "  - PostgreSQL: Database for structured data"
echo "  - Redis: Caching and session storage"
echo "  - MongoDB: Optional (not required with Pinecone)"
echo ""
echo "🚀 Quick Start:"
echo "  1. Start services: ./start_services.sh"
echo "  2. Activate Python env: source venv/bin/activate"
echo "  3. Run the API: python -m uvicorn src.api.main:app --reload"
echo ""
echo "🛑 To stop services: ./stop_services.sh"
echo ""
echo "💡 Note: Since you're using Pinecone for vector storage,"
echo "   you don't need a local vector database!"