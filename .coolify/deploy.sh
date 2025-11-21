#!/bin/bash

echo "Starting deployment..."

# Build and start containers
docker-compose up -d --build

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
sleep 10

# Initialize prompts in MongoDB
docker-compose exec -T api python scripts/init_prompts.py

echo "Deployment completed successfully!"
