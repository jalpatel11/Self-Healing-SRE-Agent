#!/bin/bash
# Run script for Self-Healing SRE Agent

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

case "$1" in
    "app")
        echo "🚀 Starting FastAPI application..."
        python app.py
        ;;
    "ui")
        echo "🎨 Starting Streamlit UI..."
        streamlit run ui.py
        ;;
    "main")
        echo "🤖 Running Self-Healing Agent (CLI)..."
        python main.py
        ;;
    "test")
        echo "🧪 Testing FastAPI bug trigger..."
        python test_app.py
        ;;
    "graph")
        echo "📊 Visualizing graph structure..."
        python graph.py
        ;;
    *)
        echo "Self-Healing SRE Agent - Run Script"
        echo ""
        echo "Usage: ./run.sh [command]"
        echo ""
        echo "Commands:"
        echo "  app    - Start FastAPI application (port 8000)"
        echo "  ui     - Start Streamlit UI (port 8501)"
        echo "  main   - Run CLI version of the agent"
        echo "  test   - Test the bug trigger"
        echo "  graph  - Visualize the LangGraph structure"
        echo ""
        echo "Example:"
        echo "  ./run.sh app     # Start the FastAPI app"
        echo "  ./run.sh ui      # Start the Streamlit UI"
        echo ""
        exit 1
        ;;
esac
