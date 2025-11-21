#!/bin/bash

# Startup script para Azure App Service
# Instala FFmpeg y ejecuta la aplicación

echo "Installing FFmpeg..."
apt-get update
apt-get install -y ffmpeg

echo "Starting application..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000
