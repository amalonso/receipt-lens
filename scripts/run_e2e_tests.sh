#!/bin/bash
# Script to run E2E tests with Playwright

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}  Receipt Lens - E2E Test Runner${NC}"
echo -e "${BLUE}==================================================${NC}"
echo

# Configuration
E2E_BASE_URL="${E2E_BASE_URL:-http://localhost:8001}"
E2E_HEADLESS="${E2E_HEADLESS:-true}"
BROWSER="${BROWSER:-chromium}"  # chromium, firefox, or webkit

# Check if test environment is running
echo -e "${YELLOW}Checking if test environment is running...${NC}"
if ! curl -s "$E2E_BASE_URL/api/health" > /dev/null 2>&1; then
    echo -e "${RED}Error: Test backend is not responding at $E2E_BASE_URL${NC}"
    echo -e "${YELLOW}Please start the test environment first:${NC}"
    echo -e "  ${GREEN}./scripts/start_test_env.sh${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Test environment is running${NC}"
echo

# Install Playwright browsers if needed
echo -e "${YELLOW}Ensuring Playwright browsers are installed...${NC}"
python -m playwright install "$BROWSER" || {
    echo -e "${RED}Failed to install Playwright browser${NC}"
    exit 1
}
echo -e "${GREEN}✓ Playwright browsers ready${NC}"
echo

# Run E2E tests
echo -e "${BLUE}Running E2E tests with $BROWSER browser...${NC}"
echo

# Export environment variables
export E2E_BASE_URL
export E2E_HEADLESS

# Run pytest with E2E markers
pytest tests/e2e/ \
    --browser="$BROWSER" \
    --headed=$([ "$E2E_HEADLESS" = "false" ] && echo "true" || echo "false") \
    --screenshot=only-on-failure \
    --video=retain-on-failure \
    --output=test-results \
    -v \
    --tb=short \
    -m e2e \
    "$@"

TEST_EXIT_CODE=$?

echo
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}==================================================${NC}"
    echo -e "${GREEN}  ✓ All E2E tests passed!${NC}"
    echo -e "${GREEN}==================================================${NC}"
else
    echo -e "${RED}==================================================${NC}"
    echo -e "${RED}  ✗ Some E2E tests failed${NC}"
    echo -e "${RED}==================================================${NC}"
    echo -e "${YELLOW}Check test-results/ directory for screenshots and videos${NC}"
fi

exit $TEST_EXIT_CODE
