#!/bin/bash

# AI Resume Shortlisting Assistant - Quick Start Script
# This script starts both the Flask API server and the Next.js frontend

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/resume-shortlisting-assistant"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AI Resume Shortlisting Assistant${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if user wants to run Streamlit or Next.js
echo -e "${YELLOW}Choose frontend:${NC}"
echo "1) Streamlit (Python)"
echo "2) Next.js (React/TypeScript)"
read -p "Enter choice (1 or 2): " choice

case $choice in
  1)
    echo -e "${GREEN}Starting Streamlit frontend...${NC}"
    cd "$BACKEND_DIR"
    source venv/bin/activate
    streamlit run app.py
    ;;
  2)
    echo -e "${GREEN}Starting Flask API server and Next.js frontend...${NC}"

    # Start Flask API in background
    cd "$BACKEND_DIR"
    source venv/bin/activate
    echo -e "${YELLOW}Starting Flask API on port 5001...${NC}"
    python api.py &
    API_PID=$!
    echo -e "${GREEN}Flask API started with PID: $API_PID${NC}"

    # Wait a moment for API to start
    sleep 2

    # Start Next.js
    cd "$FRONTEND_DIR"
    echo -e "${YELLOW}Starting Next.js on port 3000...${NC}"
    npm run dev

    # Cleanup: Kill API process when Next.js exits
    kill $API_PID 2>/dev/null || true
    ;;
  *)
    echo -e "${RED}Invalid choice. Exiting.${NC}"
    exit 1
    ;;
esac
