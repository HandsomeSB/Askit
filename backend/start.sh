#!/bin/bash

# Script to set up and start the askit backend application

# Colors for better output formatting
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
  print_status "Creating Python virtual environment..."
  python3 -m venv venv
  if [ $? -ne 0 ]; then
    print_error "Failed to create virtual environment. Make sure python3-venv is installed."
    exit 1
  fi
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install or update dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
  print_error "Failed to install dependencies."
  exit 1
fi

# Check for Google credentials
if [ ! -f "credentials.json" ]; then
  print_warning "Google API credentials.json file not found."
  print_warning "You need to create a project in Google Cloud Console and download credentials."
  print_warning "Visit: https://console.cloud.google.com/apis/credentials"
  print_warning "Please place the credentials.json file in this directory."
  exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
  print_warning ".env file not found. Creating a template .env file..."
  cat > .env << 'EOF'
# OpenAI API Key
OPENAI_API_KEY=

# Session secret for FastAPI
SESSION_SECRET_KEY=

# Storage and persistence settings
STORAGE_DIR=./storage

# Debug settings
DEBUG=True
EOF
  print_warning "Please edit the .env file with your API keys and settings."
  exit 1
fi

# Create storage directory if it doesn't exist
if [ ! -d "storage" ]; then
  print_status "Creating storage directory..."
  mkdir -p storage
fi

# Start the application
print_status "Starting the application..."
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
