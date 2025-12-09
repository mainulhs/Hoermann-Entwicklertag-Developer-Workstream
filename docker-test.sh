#!/bin/bash

echo "=== Docker Build Test ==="
echo "Building Docker image..."
docker build -t industrial-monitoring .

echo ""
echo "=== Docker Run Test ==="
echo "Starting container..."
docker run -d -p 5000:5000 --name industrial-monitoring-test industrial-monitoring

echo ""
echo "Waiting for container to start..."
sleep 5

echo ""
echo "Testing application..."
curl -f http://localhost:5000/ || echo "Application not responding"

echo ""
echo "Stopping test container..."
docker stop industrial-monitoring-test
docker rm industrial-monitoring-test

echo ""
echo "=== Docker Compose Test ==="
echo "Starting with docker-compose..."
docker-compose up -d

echo "Application should be available at: http://localhost:5000"
echo "To stop: docker-compose down"