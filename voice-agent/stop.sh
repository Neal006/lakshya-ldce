#!/bin/bash
# stop.sh - Stop all services
cd "$(dirname "${BASH_SOURCE[0]}")"
echo "Stopping all services..."
docker-compose down
echo "All services stopped."