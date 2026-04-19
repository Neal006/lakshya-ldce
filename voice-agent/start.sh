#!/bin/bash
# start.sh - Start all services for SOLV.ai Voice Complaint System
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  SOLV.ai Voice Complaint System"
echo "=========================================="
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠ No .env file found. Copy .env.example to .env and fill in your values."
    echo "  cp .env.example .env"
    echo ""
fi

# Start all services
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to be healthy..."
echo ""

# Wait for services
MAX_WAIT=120
WAITED=0

check_service() {
    local name=$1
    local url=$2
    local max_wait=${3:-$MAX_WAIT}
    local waited=0
    
    echo -n "  Waiting for $name..."
    while [ $waited -lt $max_wait ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo " OK"
            return 0
        fi
        sleep 3
        waited=$((waited + 3))
        echo -n "."
    done
    echo " FAILED"
    return 1
}

check_service "STT" "http://localhost:8001/health" 180
check_service "Classifier" "http://localhost:8002/health" 180
check_service "Backend" "http://localhost:8000/health"
check_service "Orchestrator" "http://localhost:8003/health"

# Setup Ollama model
echo ""
echo "Setting up Ollama (downloading model, ~1GB)..."
until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "  Waiting for Ollama..."
    sleep 3
done

docker exec solv-ollama ollama pull qwen2.5:1.5b 2>/dev/null || echo "  (Ollama pull may need manual setup)"

echo ""
echo "=========================================="
echo "  System Ready!"
echo "=========================================="
echo "  STT Service:       http://localhost:8001/health"
echo "  Classifier Service: http://localhost:8002/health"
echo "  Backend API:        http://localhost:8000/docs"
echo "  Dashboard:          http://localhost:8000/dashboard"
echo "  Orchestrator:       http://localhost:8003/health"
echo "  Ollama LLM:         http://localhost:11434"
echo ""
echo "  Twilio webhook:     https://your-server.com/twilio/voice"
echo "  Test endpoint:      http://localhost:8003/test/pipeline"
echo "=========================================="