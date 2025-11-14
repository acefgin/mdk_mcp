#!/bin/bash

# qPCR Assistant - Interactive Mode Launcher
# This script sets up permissions and starts the qPCR Assistant in interactive mode

set -e

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║               qPCR ASSISTANT - Interactive Mode Launcher                 ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Step 1: Set up environment
# ============================================================================
echo "🔧 Setting up environment..."
echo ""

# Set environment variables
export AUTOGEN_MAX_ROUNDS=50
export LOG_LEVEL=INFO

echo "   • AUTOGEN_MAX_ROUNDS=$AUTOGEN_MAX_ROUNDS"

# Create results directory (permissions handled by container entrypoints)
mkdir -p ./results/sequences

echo "   ✓ Environment configured"
echo ""

# ============================================================================
# Step 2: Check environment configuration
# ============================================================================
echo "🔍 Checking environment configuration..."
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

echo "   ✓ Environment configuration found"
echo ""

# ============================================================================
# Step 3: Check and manage existing containers
# ============================================================================
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
cd /app && python3 -c 'from main import interactive_mode; interactive_mode()'
"
            exit 0
            ;;
        2)
            echo ""
            echo "🔄 Restarting with fresh build..."
            echo "   • Stopping containers..."
            docker compose -f docker-compose.autogen.yml down
            echo "   ✓ Containers stopped"
            echo ""
            # Continue to the main startup flow below
            ;;
        3)
            echo ""
            echo "Exiting. Container is still running."
            echo "To connect later: ./scripts/utils/start_interactive.sh"
            echo "To stop: docker compose -f docker-compose.autogen.yml down"
            echo ""
            exit 0
            ;;
        *)
            echo ""
            echo "Invalid choice. Exiting."
            echo ""
            exit 1
            ;;
    esac
fi

# ============================================================================
# Step 4: Start containers with proper permissions
# ============================================================================
echo "🚀 Starting qPCR Assistant system..."
echo ""
echo "   • Building containers (may take a few minutes on first run)..."
docker compose -f docker-compose.autogen.yml up --build -d

echo "   ✓ Containers building and starting..."
echo ""
echo "   • Waiting for services to initialize..."
sleep 5

# Verify containers started successfully
echo "   • Verifying container status..."
FAILED=0

if ! docker ps | grep -q "qpcr-assistant"; then
    echo ""
    echo "   ❌ ERROR: qPCR Assistant container failed to start"
    echo "   Check logs with: docker logs qpcr-assistant"
    FAILED=1
fi

if ! docker ps | grep -q "ndiag-database-server"; then
    echo ""
    echo "   ❌ ERROR: Database server failed to start"
    echo "   Check logs with: docker logs ndiag-database-server"
    FAILED=1
fi

if ! docker ps | grep -q "ndiag-processing-server"; then
    echo ""
    echo "   ❌ ERROR: Processing server failed to start"
    echo "   Check logs with: docker logs ndiag-processing-server"
    FAILED=1
fi

if ! docker ps | grep -q "ndiag-alignment-server"; then
    echo ""
    echo "   ❌ ERROR: Alignment server failed to start"
    echo "   Check logs with: docker logs ndiag-alignment-server"
    FAILED=1
fi

if [ $FAILED -eq 1 ]; then
    echo ""
    echo "   To see all logs: docker compose -f docker-compose.autogen.yml logs"
    exit 1
fi

echo "   ✓ All containers started successfully"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "🎉 qPCR Assistant is ready!"
echo ""
echo "📊 System Status:"
echo "   ✓ Containers using entrypoint-based permission management"
echo "   ✓ MAX_ROUNDS=$AUTOGEN_MAX_ROUNDS (full workflow supported)"
echo "   ✓ Results directory: ./results/ (auto-configured permissions)"
echo ""
echo "Connecting to interactive session..."
echo ""
echo "📝 Quick Tips:"
echo "   • Type your qPCR design request naturally"
echo "   • Use 'help' for examples and usage information"
echo "   • Use 'logs' to view task history"
echo "   • Press Ctrl+D or type 'exit' to quit"
echo "   • Press Ctrl+C to interrupt running workflow"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
sleep 2

# Connect with proper TTY support for readline/backspace
# Using bash ensures proper terminal handling
docker exec -it qpcr-assistant bash -c "
# Set terminal to proper state
stty sane 2>/dev/null || true
export TERM=xterm-256color

# Start interactive mode with Python
cd /app && python3 -c 'from main import interactive_mode; interactive_mode()'
"

# If user detaches or exits
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Session ended."
echo ""
echo "📋 Available Commands:"
echo "   Reconnect:    ./scripts/utils/start_interactive.sh"
echo "   Stop all:     docker compose -f docker-compose.autogen.yml down"
echo "   View logs:    docker logs qpcr-assistant"
echo "   Enter shell:  docker exec -it qpcr-assistant bash"
echo ""
echo "📁 All task logs saved in: ./results/"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
