#!/bin/bash

# Test technical test generation endpoint

echo "Testing technical test generation..."

curl -X POST http://localhost:9000/generate-technical-test \
  -H "Content-Type: application/json" \
  -d '{
    "profession": "Desarrollador Full Stack",
    "technologies": "React, Node.js, Express, MongoDB, TypeScript",
    "experience": "3 años desarrollando aplicaciones web escalables",
    "education": "Ingeniería de Sistemas"
  }' | jq .

echo ""
echo "Test completed!"
