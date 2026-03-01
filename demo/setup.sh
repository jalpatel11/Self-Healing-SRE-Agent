#!/bin/bash
# Setup script for Self-Healing SRE Agent

echo "🤖 Self-Healing SRE Agent - Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Found Python $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "⚠️  Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✅ pip upgraded"
echo ""

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys!"
    echo ""
else
    echo "⚠️  .env file already exists (not overwritten)"
    echo ""
fi

# Make scripts executable
echo "Making scripts executable..."
chmod +x setup.sh
chmod +x run.sh
chmod +x main.py
chmod +x ui.py
echo "✅ Scripts are now executable"
echo ""

# Summary
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys:"
echo "   - OPENAI_API_KEY or ANTHROPIC_API_KEY (required)"
echo "   - LANGCHAIN_API_KEY (recommended for tracing)"
echo "   - GITHUB_TOKEN (optional, for real PRs)"
echo ""
echo "2. Start the FastAPI app:"
echo "   ./run.sh app"
echo ""
echo "3. In another terminal, run the Streamlit UI:"
echo "   ./run.sh ui"
echo ""
echo "4. Or run the command-line version:"
echo "   ./run.sh main"
echo ""
echo "📚 See README.md for detailed instructions"
echo ""
