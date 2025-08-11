#!/bin/bash

# Test script for local AIME Planner development
# Tests the initiate-bid endpoint with sample data

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🧪 Testing AIME Planner local deployment..."

# Check if LocalStack is running
if ! curl -s http://localhost:4566/health > /dev/null; then
    echo "❌ LocalStack is not running. Please run './scripts/local-setup.sh' first."
    exit 1
fi

cd "$PROJECT_ROOT"

# Set LocalStack environment
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Get the API Gateway ID from CloudFormation stack
echo "🔍 Finding API Gateway endpoint..."
STACK_NAME="aime-planner-testing"

API_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --endpoint-url http://localhost:4566 \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text 2>/dev/null | sed 's|.*restapis/||;s|/testing.*||' || echo "")

if [[ -z "$API_ID" ]]; then
    echo "❌ Could not find API Gateway ID. Make sure the stack is deployed."
    echo "💡 Try running: ./scripts/local-setup.sh"
    exit 1
fi

API_ENDPOINT="http://localhost:4566/restapis/$API_ID/testing/_user_request_"

echo "📡 API Endpoint: $API_ENDPOINT"

# Test 1: Hotel booking request
echo ""
echo "🏨 Testing hotel booking request..."
RESPONSE=$(curl -s -X POST "$API_ENDPOINT/initiate-bid" \
    -H "Content-Type: application/json" \
    -d @test-data/sample-request.json \
    -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "Response Status: $HTTP_STATUS"
echo "Response Body: $BODY"

if [[ "$HTTP_STATUS" -eq 200 ]]; then
    echo "✅ Hotel booking test passed!"
    CONVERSATION_ID=$(echo "$BODY" | grep -o '"conversation_id":"[^"]*"' | cut -d'"' -f4)
    echo "📋 Conversation ID: $CONVERSATION_ID"
else
    echo "❌ Hotel booking test failed!"
fi

# Test 2: Restaurant booking request
echo ""
echo "🍽️  Testing restaurant booking request..."
RESPONSE=$(curl -s -X POST "$API_ENDPOINT/initiate-bid" \
    -H "Content-Type: application/json" \
    -d @test-data/restaurant-request.json \
    -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "Response Status: $HTTP_STATUS"
echo "Response Body: $BODY"

if [[ "$HTTP_STATUS" -eq 200 ]]; then
    echo "✅ Restaurant booking test passed!"
    CONVERSATION_ID=$(echo "$BODY" | grep -o '"conversation_id":"[^"]*"' | cut -d'"' -f4)
    echo "📋 Conversation ID: $CONVERSATION_ID"
else
    echo "❌ Restaurant booking test failed!"
fi

# Test 3: Check DynamoDB records
echo ""
echo "💾 Checking DynamoDB conversations..."
CONVERSATIONS=$(aws dynamodb scan \
    --table-name testing-aime-conversations \
    --endpoint-url http://localhost:4566 \
    --query 'Items[].{ID:conversation_id.S,Status:status.S,Vendor:vendor_info.M.name.S}' \
    --output table 2>/dev/null || echo "Failed to scan DynamoDB")

echo "$CONVERSATIONS"

# Test 4: Invalid request
echo ""
echo "❌ Testing invalid request..."
RESPONSE=$(curl -s -X POST "$API_ENDPOINT/initiate-bid" \
    -H "Content-Type: application/json" \
    -d '{"invalid": "request"}' \
    -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)

if [[ "$HTTP_STATUS" -eq 400 ]]; then
    echo "✅ Invalid request properly rejected!"
else
    echo "❌ Invalid request test failed - should return 400"
fi

echo ""
echo "🎉 Testing completed!"
echo ""
echo "📊 Next steps:"
echo "1. Check Lambda logs: docker-compose logs localstack | grep lambda"
echo "2. View DynamoDB data: aws dynamodb scan --table-name testing-aime-conversations --endpoint-url http://localhost:4566"
echo "3. Test email processing with mock vendor responses"
echo ""
