#!/bin/bash

# KSTAR MCP PoC v2 - Automated Installation Script
# This script is designed for first-time users of the project

set -e  # Exit on error

echo "🚀 Starting KSTAR MCP PoC v2 installation..."
echo "================================================"

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}📁 Working directory: $SCRIPT_DIR${NC}"

# Check Python version
echo -e "${BLUE}🐍 Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed.${NC}"
    echo "   Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✅ Found Python $PYTHON_VERSION${NC}"

# Create virtual environment
echo -e "${BLUE}🔧 Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${BLUE}📦 Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${BLUE}📚 Installing Python packages...${NC}"
pip install -r requirements.txt

# Create environment configuration file
echo -e "${BLUE}⚙️  Creating environment configuration file...${NC}"
if [ ! -f ".env" ]; then
    cp config.env.example .env
    echo -e "${GREEN}✅ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Please add your OpenAI API key to .env file!${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists.${NC}"
fi

# Make main.py executable
chmod +x main.py

echo ""
echo "================================================"
echo -e "${GREEN}🎉 Installation completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Set up OpenAI API key (optional):"
echo "   nano .env"
echo "   # OPENAI_API_KEY=your_api_key_here"
echo ""
echo "2. Run the application:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "3. Open web browser:"
echo "   http://localhost:8000"
echo ""
echo -e "${YELLOW}💡 Tip: Demo mode works without API key!${NC}"
echo "================================================"


