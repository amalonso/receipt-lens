#!/bin/bash
# Script to run complete test suite: unit, integration, and E2E tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}  Receipt Lens - Complete Test Suite${NC}"
echo -e "${BLUE}==================================================${NC}"
echo

# Track failures
UNIT_FAILED=0
E2E_FAILED=0

# 1. Run unit tests
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Step 1/2: Running Unit Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo

pytest tests/ \
    -m "not e2e" \
    --cov=backend \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-report=json \
    -v \
    --tb=short || UNIT_FAILED=1

if [ $UNIT_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Unit tests passed${NC}"
else
    echo -e "${RED}✗ Unit tests failed${NC}"
fi

echo
echo

# 2. Run E2E tests
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Step 2/2: Running E2E Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo

# Check if test environment is running
if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Test environment is already running${NC}"
    echo
else
    echo -e "${YELLOW}Test environment not running. Starting it...${NC}"
    ./scripts/start_test_env.sh || {
        echo -e "${RED}Failed to start test environment${NC}"
        E2E_FAILED=1
    }
fi

if [ $E2E_FAILED -eq 0 ]; then
    ./scripts/run_e2e_tests.sh || E2E_FAILED=1
fi

echo
echo

# Summary
echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}  Test Suite Summary${NC}"
echo -e "${BLUE}==================================================${NC}"
echo

if [ $UNIT_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Unit Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Unit Tests: FAILED${NC}"
fi

if [ $E2E_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ E2E Tests: PASSED${NC}"
else
    echo -e "${RED}✗ E2E Tests: FAILED${NC}"
fi

echo

# Overall result
if [ $UNIT_FAILED -eq 0 ] && [ $E2E_FAILED -eq 0 ]; then
    echo -e "${GREEN}==================================================${NC}"
    echo -e "${GREEN}  ✓✓✓ ALL TESTS PASSED! ✓✓✓${NC}"
    echo -e "${GREEN}==================================================${NC}"
    exit 0
else
    echo -e "${RED}==================================================${NC}"
    echo -e "${RED}  ✗ SOME TESTS FAILED${NC}"
    echo -e "${RED}==================================================${NC}"
    exit 1
fi
