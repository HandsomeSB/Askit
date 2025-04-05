#!/bin/bash
# run.sh - Script to run both backend and frontend

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is required but not installed. Please install Node.js and try again."
    exit 1
fi

# Function to handle clean exit
cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up trap for clean exit
trap cleanup SIGINT SIGTERM

# Configuration
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Create .env file for frontend if it doesn't exist
if [ ! -f "$FRONTEND_DIR/.env.local" ]; then
    echo "Creating .env.local file for frontend..."
    echo "API_URL=http://localhost:$BACKEND_PORT" > "$FRONTEND_DIR/.env.local"
fi

# Start backend
echo "Starting backend on port $BACKEND_PORT..."
cd "$BACKEND_DIR" || exit 1
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate || source venv/Scripts/activate

# Install backend dependencies if needed
if [ ! -d "venv/lib/python3.8" ] && [ ! -d "venv/Lib/site-packages" ]; then
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
fi

# Start backend server
python app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 3

# Start frontend
echo "Starting frontend on port $FRONTEND_PORT..."
cd "$FRONTEND_DIR" || exit 1

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend server
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Services are running!"
echo "Backend: http://localhost:$BACKEND_PORT"
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo "Press Ctrl+C to stop all services."

# Wait for child processes
wait