#!/bin/bash
# Linux Setup Script for Sync Cut
# This script installs dependencies and sets up the environment

set -e

echo "Setting up Sync Cut on Linux..."
echo "================================"

# Check if running as root for apt commands
if [[ $EUID -eq 0 ]]; then
   echo "Please don't run this script as root. Use sudo when prompted."
   exit 1
fi

# Update package list
echo "Updating package list..."
sudo apt update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-flask \
    python3-flask-socketio \
    python3-pydub \
    python3-yaml \
    python3-requests \
    python3-websocket \
    python3-numpy \
    ffmpeg

echo "System dependencies installed successfully!"

# Create workspace directories
echo "Creating workspace directories..."
mkdir -p workspace/{models,logs,upload,tmp,status}

# Create config.yaml if it doesn't exist
if [ ! -f "config.yaml" ]; then
    echo "Creating config.yaml from example..."
    cp config.yaml.example config.yaml 2>/dev/null || cp config.yaml.example config.yaml || echo "Config file already exists"
fi

# Test the installation
echo "Testing installation..."
if PYTHONPATH=/usr/lib/python3/dist-packages python3 test_functionality.py; then
    echo ""
    echo "✅ Setup completed successfully!"
    echo ""
    echo "To start Sync Cut:"
    echo "  PYTHONPATH=/usr/lib/python3/dist-packages python3 start_server.py"
    echo ""
    echo "Or create a simple alias:"
    echo "  echo 'alias sync-cut=\"cd $(pwd) && PYTHONPATH=/usr/lib/python3/dist-packages python3 start_server.py\"' >> ~/.bashrc"
    echo ""
    echo "Then access: http://localhost:7000"
    echo ""
    echo "Optional: For Whisper support, run:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install openai-whisper torch torchaudio"
else
    echo "❌ Setup failed. Please check the error messages above."
    exit 1
fi