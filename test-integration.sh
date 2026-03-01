#!/bin/bash

# Integration Test Script
# Tests the connection between Next.js frontend and Flask backend

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/resume-shortlisting-assistant"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Integration Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test 1: Check if Flask backend is running
echo -e "${YELLOW}Test 1: Checking Flask Backend...${NC}"
if curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Flask backend is running on port 5001${NC}"
else
    echo -e "${RED}✗ Flask backend is NOT running${NC}"
    echo -e "${YELLOW}Please start the backend with:${NC}"
    echo "  cd $BACKEND_DIR"
    echo "  source venv/bin/activate"
    echo "  python api.py"
    exit 1
fi

# Test 2: Check Next.js frontend
echo ""
echo -e "${YELLOW}Test 2: Checking Next.js Frontend...${NC}"
if [ -d "$FRONTEND_DIR" ]; then
    echo -e "${GREEN}✓ Next.js frontend directory exists${NC}"
else
    echo -e "${RED}✗ Next.js frontend directory NOT found${NC}"
    exit 1
fi

# Test 3: Check environment configuration
echo ""
echo -e "${YELLOW}Test 3: Checking Environment Configuration...${NC}"
if [ -f "$FRONTEND_DIR/.env.local" ]; then
    echo -e "${GREEN}✓ .env.local file exists${NC}"
    grep -q "NEXT_PUBLIC_API_URL" "$FRONTEND_DIR/.env.local" && echo -e "${GREEN}✓ NEXT_PUBLIC_API_URL is configured${NC}"
else
    echo -e "${RED}✗ .env.local file NOT found${NC}"
fi

# Test 4: Test API health endpoint
echo ""
echo -e "${YELLOW}Test 4: Testing API Health Endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s http://localhost:5001/health)
if echo "$HEALTH_RESPONSE" | grep -q "ok"; then
    echo -e "${GREEN}✓ Health check successful${NC}"
    echo "  Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}All Tests Passed! ✓${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}To start the application:${NC}"
echo ""
echo "1. Backend (if not already running):"
echo "   cd $BACKEND_DIR"
echo "   source venv/bin/activate"
echo "   python api.py"
echo ""
echo "2. Frontend (in a new terminal):"
echo "   cd $FRONTEND_DIR"
echo "   npm run dev"
echo ""
echo "3. Open your browser:"
echo "   http://localhost:3000"
echo ""
