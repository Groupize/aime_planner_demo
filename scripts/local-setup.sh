#!/bin/bash

# Local development setup script for AIME Planner Chatbot
# This script sets up LocalStack and prepares the local environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🏠 Setting up AIME Planner local development environment..."

# Check required tools
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed."; exit 1; }
command -v sam >/dev/null 2>&1 || { echo "❌ AWS SAM CLI is required but not installed."; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI is required but not installed."; exit 1; }

# Change to project directory
cd "$PROJECT_ROOT"

# Create .env file if it doesn't exist
if [[ ! -f ".env" ]]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your actual API keys before running the application"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Start LocalStack
echo "🐳 Starting LocalStack..."
docker-compose up -d localstack

# Wait for LocalStack to be ready
echo "⏳ Waiting for LocalStack to be ready..."
timeout=60
while ! curl -s http://localhost:4566/health > /dev/null; do
    sleep 2
    timeout=$((timeout - 2))
    if [[ $timeout -le 0 ]]; then
        echo "❌ LocalStack failed to start within 60 seconds"
        exit 1
    fi
done

echo "✅ LocalStack is ready!"

# Build SAM application
echo "🔨 Building SAM application..."
sam build

# Deploy to LocalStack
echo "🚀 Deploying to LocalStack..."
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

sam deploy \
    --config-env testing \
    --parameter-overrides \
        RailsApiBaseUrl=http://localhost:3000 \
        RailsApiKey=test-key \
        OpenAIApiKey=test-openai-key \
        SendGridApiKey=test-sendgrid-key \
    --resolve-s3 \
    --s3-bucket aime-planner-testing-deployments \
    --s3-prefix aime-planner-local \
    --region us-east-1 \
    --no-confirm-changeset \
    --endpoint-url http://localhost:4566

echo ""
echo "✅ Local development environment is ready!"
echo ""
echo "🔗 Available endpoints:"
echo "  LocalStack Dashboard: http://localhost:4566"
echo "  API Gateway: http://localhost:4566/restapis/{api-id}/testing/_user_request_"
echo "  DynamoDB: http://localhost:4566"
echo ""
echo "🛠️  Useful commands:"
echo "  View logs: docker-compose logs -f localstack"
echo "  Stop LocalStack: docker-compose down"
echo "  Restart LocalStack: docker-compose restart localstack"
echo "  Test API: curl -X POST http://localhost:4566/restapis/{api-id}/testing/_user_request_/initiate-bid"
echo ""
echo "📖 Next steps:"
echo "1. Edit .env file with your actual API keys"
echo "2. Test the initiate-bid endpoint"
echo "3. Set up email forwarding for testing"
echo ""
