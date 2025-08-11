#!/bin/bash

# Deployment script for AIME Planner Chatbot
# Usage: ./scripts/deploy.sh [testing|staging|production]

set -e

ENVIRONMENT=${1:-testing}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Deploying AIME Planner to $ENVIRONMENT environment..."

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(testing|staging|production)$ ]]; then
    echo "❌ Error: Environment must be 'testing', 'staging', or 'production'"
    exit 1
fi

# Check if we're deploying to production and confirm
if [[ "$ENVIRONMENT" == "production" ]]; then
    read -p "⚠️  You are about to deploy to PRODUCTION. Are you sure? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
fi

# Check required tools
command -v sam >/dev/null 2>&1 || { echo "❌ AWS SAM CLI is required but not installed."; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI is required but not installed."; exit 1; }

# Set AWS profile based on environment
case $ENVIRONMENT in
    testing)
        export AWS_PROFILE=groupize-testing
        ;;
    staging)
        export AWS_PROFILE=groupize-staging
        ;;
    production)
        export AWS_PROFILE=groupize-production
        ;;
esac

echo "📋 Using AWS profile: $AWS_PROFILE"

# Verify AWS credentials
echo "🔐 Verifying AWS credentials..."
aws sts get-caller-identity > /dev/null || {
    echo "❌ AWS credentials not configured for profile $AWS_PROFILE"
    exit 1
}

# Change to project directory
cd "$PROJECT_ROOT"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Validate SAM template
echo "✅ Validating SAM template..."
sam validate

# Build the application
echo "🔨 Building SAM application..."
sam build

# Deploy with the specified environment configuration
echo "🚀 Deploying to $ENVIRONMENT..."

if [[ "$ENVIRONMENT" == "testing" ]]; then
    # For testing, we might want to skip confirmation
    sam deploy --config-env "$ENVIRONMENT" --no-confirm-changeset
else
    # For staging and production, require confirmation
    sam deploy --config-env "$ENVIRONMENT"
fi

# Get the API Gateway URL
echo "📡 Getting API Gateway URL..."
STACK_NAME="aime-planner-$ENVIRONMENT"
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text)

echo ""
echo "✅ Deployment completed successfully!"
echo "🌐 API Gateway URL: $API_URL"
echo "📊 Stack: $STACK_NAME"
echo "🔧 Environment: $ENVIRONMENT"
echo ""
echo "Next steps:"
echo "1. Test the API endpoint: $API_URL/initiate-bid"
echo "2. Configure SendGrid inbound parse webhook"
echo "3. Set up SES domain verification and receipt rules"
echo ""
