#!/bin/bash

echo "🔧 Starting RabbitMQ..."
docker rm -f rabbitmq 2>/dev/null
docker run -d --hostname rabbitmq --name rabbitmq \
  -p 5672:5672 -p 15672:15672 \
  rabbitmq:3-management

echo "🐳 Building PV Simulator image..."
docker build -t pv-simulator .

echo "🚀 Running PV Simulator..."
docker run --rm --name pv-sim \
  -e RABBITMQ_HOST=host.docker.internal \
  pv-simulator

