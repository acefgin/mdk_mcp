#!/bin/bash

# qPCR Assistant - Interactive Mode Launcher
# This script starts the qPCR Assistant in interactive mode

set -e

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║               qPCR ASSISTANT - Interactive Mode Launcher                ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if .env file exists
if [ ! -f "autogen_app/.env" ]; then
    echo "❌ ERROR: autogen_app/.env file not found!"
    echo ""
    echo "Please create autogen_app/.env with your OpenAI API key:"
    echo "  echo 'OPENAI_API_KEY=sk-your-key' > autogen_app/.env"
    echo ""
    exit 1
fi

# Check if OPENAI_API_KEY is set in .env
if ! grep -q "OPENAI_API_KEY=" autogen_app/.env; then
    echo "❌ ERROR: OPENAI_API_KEY not found in autogen_app/.env"
    echo ""
    echo "Please add your OpenAI API key to autogen_app/.env:"
    echo "  echo 'OPENAI_API_KEY=sk-your-key' >> autogen_app/.env"
    echo ""
    exit 1
fi

echo "✓ Environment configuration found"
echo ""

# Check if containers are running
if docker ps | grep -q "qpcr-assistant"; then
    echo "⚠️  qPCR Assistant container is already running"
    echo ""
    echo "What would you like to do?"
    echo "  1) Attach to existing session"
    echo "  2) Restart with fresh build"
    echo "  3) Exit"
    echo ""
    read -p "Enter your choice (1/2/3): " choice

    case "$choice" in
        1)
            echo ""
            echo "Connecting to qPCR Assistant..."
            echo "Press Ctrl+D or type 'exit' to quit"
            echo "Press Ctrl+C to interrupt workflow"
            echo ""
            sleep 1
            # Connect with proper TTY and readline support
            docker exec -it qpcr-assistant bash -c "
stty sane 2>/dev/null || true
export TERM=xterm-256color
cd /app && python3 -c 'from qpcr_assistant import interactive_mode; interactive_mode()'
"
            exit 0
            ;;
        2)
            echo ""
            echo "🔄 Restarting with fresh build..."
            echo "   • Stopping containers..."
            docker compose -f docker-compose.autogen.yml down
            echo "   • Starting fresh build..."
            # Continue to the main startup flow below
            ;;
        3)
            echo ""
            echo "Exiting. Use 'docker attach qpcr-assistant' to connect later."
            echo ""
            exit 0
            ;;
        *)
            echo ""
            echo "Invalid choice. Exiting."
            echo "Use 'docker attach qpcr-assistant' to connect to the running instance."
            echo ""
            exit 1
            ;;
    esac
fi

# Start containers
echo "🚀 Starting qPCR Assistant system..."
echo ""
echo "   • Building containers..."
docker compose -f docker-compose.autogen.yml up --build -d

echo ""
echo "   • Waiting for containers to be ready..."
sleep 5

# Check if containers started successfully
if ! docker ps | grep -q "qpcr-assistant"; then
    echo ""
    echo "❌ ERROR: Failed to start qPCR Assistant"
    echo ""
    echo "Check logs with: docker logs qpcr-assistant"
    exit 1
fi

if ! docker ps | grep -q "ndiag-database-server"; then
    echo ""
    echo "❌ ERROR: Failed to start database server"
    echo ""
    echo "Check logs with: docker logs ndiag-database-server"
    exit 1
fi

echo "   ✓ Containers started successfully"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "🎉 qPCR Assistant is ready!"
echo ""
echo "Connecting to interactive session..."
echo ""
echo "📝 Quick Tips:"
echo "   • Type your qPCR design request naturally"
echo "   • Use 'help' for examples"
echo "   • Use 'logs' to view task history"
echo "   • Press Ctrl+D or type 'exit' to quit"
echo "   • Press Ctrl+C to interrupt workflow"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
sleep 2

# Connect with proper TTY support for readline/backspace
# Using bash ensures proper terminal handling
docker exec -it qpcr-assistant bash -c "
# Set terminal to proper state
stty sane 2>/dev/null || true
export TERM=xterm-256color

# Start interactive mode with Python
cd /app && python3 -c 'from qpcr_assistant import interactive_mode; interactive_mode()'
"

# If user detaches or exits
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Session ended."
echo ""
echo "To reconnect: docker attach qpcr-assistant"
echo "To stop: docker compose -f docker-compose.autogen.yml down"
echo "To view logs: docker logs qpcr-assistant"
echo ""
echo "All task logs are saved in: ./results/"
echo ""
