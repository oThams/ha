#!/bin/bash

# Script to start Home Assistant with Intuis custom component for testing

set -e

echo "🏠 Starting Home Assistant with Intuis custom component..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed!"
    echo "Please install docker-compose and try again."
    exit 1
fi

# Create config directory if it doesn't exist
if [ ! -d "config" ]; then
    echo "📁 Creating config directory..."
    mkdir -p config
fi

# Stop and remove existing container if it exists
if docker ps -a | grep -q homeassistant-intuis-test; then
    echo "🛑 Stopping existing container..."
    docker-compose down
fi

# Build and start the container
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting Home Assistant..."
docker-compose up -d

echo ""
echo "✅ Home Assistant is starting!"
echo ""
echo "📍 Access Home Assistant at: http://localhost:8123"
echo ""
echo "⏱️  Please wait 30-60 seconds for Home Assistant to fully start."
echo ""
echo "📋 Useful commands:"
echo "  - View logs:        docker-compose logs -f"
echo "  - Stop container:   docker-compose down"
echo "  - Restart:          docker-compose restart"
echo "  - Enter container:  docker-compose exec homeassistant bash"
echo ""
echo "🔧 To configure Intuis:"
echo "  1. Go to http://localhost:8123"
echo "  2. Complete the onboarding"
echo "  3. Go to Configuration → Integrations"
echo "  4. Click '+ ADD INTEGRATION'"
echo "  5. Search for 'Intuis Connect with Netatmo'"
echo ""

# Show logs
echo "📄 Showing logs (Ctrl+C to stop viewing logs, container will continue running):"
echo ""
docker-compose logs -f
