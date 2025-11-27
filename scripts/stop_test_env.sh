#!/bin/bash
# Script to stop the test environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}  Stopping Test Environment${NC}"
echo -e "${BLUE}==================================================${NC}"
echo

echo -e "${YELLOW}Stopping containers...${NC}"
docker compose -f docker-compose.test.yml down

echo
echo -e "${GREEN}✓ Test environment stopped${NC}"
echo

# Ask if user wants to remove volumes
read -p "$(echo -e ${YELLOW}Remove test database volumes? [y/N]: ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Removing volumes...${NC}"
    docker compose -f docker-compose.test.yml down -v
    echo -e "${GREEN}✓ Volumes removed${NC}"
fi

echo
echo -e "${GREEN}Done!${NC}"
