#!/bin/bash
# Script to start the test environment with Docker Compose

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}  Receipt Lens - Test Environment Startup${NC}"
echo -e "${BLUE}==================================================${NC}"
echo

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo -e "${YELLOW}Creating minimal .env for testing...${NC}"
    cat > .env.test << EOF
# Test Environment Configuration
POSTGRES_PASSWORD=test_password_12345
JWT_SECRET_KEY=test_jwt_secret_key_do_not_use_in_production
TEST_VISION_PROVIDER=ocrspace
OCRSPACE_API_KEY=helloworld
EOF
    echo -e "${GREEN}✓ Created .env.test${NC}"
    ENV_FILE=".env.test"
else
    ENV_FILE=".env"
    echo -e "${GREEN}✓ Using existing .env file${NC}"
fi

# Stop any running test containers
echo -e "${YELLOW}Stopping any existing test containers...${NC}"
docker compose -f docker-compose.test.yml down -v 2>/dev/null || true
echo -e "${GREEN}✓ Cleaned up old containers${NC}"
echo

# Start test environment
echo -e "${BLUE}Starting test environment...${NC}"
echo -e "${YELLOW}This may take a minute for the first run...${NC}"
echo

# Use the env file
if [ "$ENV_FILE" = ".env.test" ]; then
    docker compose -f docker-compose.test.yml --env-file .env.test up -d
else
    docker compose -f docker-compose.test.yml up -d
fi

# Wait for services to be healthy
echo
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"

# Wait for database
echo -ne "${YELLOW}  → Database: ${NC}"
timeout=60
counter=0
until docker compose -f docker-compose.test.yml exec -T db-test pg_isready -U test_user -d receipt_lens_test > /dev/null 2>&1; do
    sleep 1
    counter=$((counter + 1))
    if [ $counter -ge $timeout ]; then
        echo -e "${RED}FAILED${NC}"
        echo -e "${RED}Database did not become ready in time${NC}"
        exit 1
    fi
done
echo -e "${GREEN}READY${NC}"

# Wait for backend
echo -ne "${YELLOW}  → Backend: ${NC}"
counter=0
until curl -s http://localhost:8001/api/health > /dev/null 2>&1; do
    sleep 1
    counter=$((counter + 1))
    if [ $counter -ge $timeout ]; then
        echo -e "${RED}FAILED${NC}"
        echo -e "${RED}Backend did not become ready in time${NC}"
        docker compose -f docker-compose.test.yml logs backend-test
        exit 1
    fi
done
echo -e "${GREEN}READY${NC}"

echo
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}  ✓ Test environment is running!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo
echo -e "${BLUE}Services:${NC}"
echo -e "  Backend:  ${GREEN}http://localhost:8001${NC}"
echo -e "  Database: ${GREEN}localhost:5433${NC}"
echo
echo -e "${BLUE}You can now run tests:${NC}"
echo -e "  ${GREEN}./scripts/run_e2e_tests.sh${NC}          - Run E2E tests"
echo -e "  ${GREEN}pytest tests/unit/${NC}                  - Run unit tests"
echo -e "  ${GREEN}pytest tests/integration/${NC}           - Run integration tests"
echo
echo -e "${BLUE}To view logs:${NC}"
echo -e "  ${GREEN}docker compose -f docker-compose.test.yml logs -f${NC}"
echo
echo -e "${BLUE}To stop the environment:${NC}"
echo -e "  ${GREEN}./scripts/stop_test_env.sh${NC}"
echo
