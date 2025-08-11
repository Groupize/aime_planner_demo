#!/bin/bash

# Test runner script for AIME Planner
# Runs all unit tests and generates coverage report

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🧪 Running AIME Planner Test Suite"
echo "=" * 40

cd "$PROJECT_ROOT"

# Install test dependencies if not already installed
echo "📦 Ensuring test dependencies are installed..."
pip install pytest pytest-cov coverage

echo ""
echo "🏃 Running unit tests..."

# Run tests with coverage
python -m pytest tests/unit/ \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    -v \
    --tb=short

echo ""
echo "📊 Test Results Summary:"
echo "- Unit tests completed"
echo "- Coverage report generated in htmlcov/"
echo ""
echo "✅ All tests completed!"
