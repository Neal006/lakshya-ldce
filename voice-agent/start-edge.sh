#!/bin/bash
# start-edge.sh - Start system in edge/offline mode
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  SOLV.ai Voice - EDGE MODE (Offline)"
echo "=========================================="
echo ""

# Pull Ollama model before starting
echo "Setting up Ollama (pulling phi3.5 model)..."
docker-compose -f docker-compose.edge.yml up -d ollama
sleep 10
until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "  Waiting for Ollama..."
    sleep 5
done
docker exec solv-ollama ollama pull phi3.5:latest 2>/dev/null || echo "  Model pull may need manual setup"

echo ""
echo "Starting all services in offline mode..."
docker-compose -f docker-compose.edge.yml up -d

echo ""
echo "Waiting for services..."
sleep 15

echo ""
echo "=========================================="
echo "  System Ready (EDGE MODE)"
echo "=========================================="
echo "  STT:           http://localhost:8001/health"
echo "  Classifier:    http://localhost:8002/health"
echo "  Backend:       http://localhost:8000/docs"
echo "  Dashboard:     http://localhost:8000/dashboard"
echo "  Orchestrator:  http://localhost:8003/health"
echo "  Ollama LLM:    http://localhost:11434"
echo ""
echo "  Mode: OFFLINE (all local, no cloud APIs)"
echo "  LLM: Ollama (phi3.5:latest)"
echo "  TTS: Piper (local)"
echo "=========================================="