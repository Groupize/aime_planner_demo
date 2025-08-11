#!/bin/bash

# GitHub Actions Secrets Setup Script
# This script helps you set up the required secrets for GitHub Actions deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔐 GitHub Actions Secrets Setup for AIME Planner"
echo "=" * 50

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo "Please install it from: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI."
    echo "Please run: gh auth login"
    exit 1
fi

cd "$PROJECT_ROOT"

# Get repository information
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "📍 Repository: $REPO"
echo ""

echo "This script will help you set up the following secrets:"
echo ""
echo "🏗️  AWS Credentials (per environment):"
echo "   - TESTING_AWS_ACCESS_KEY_ID"
echo "   - TESTING_AWS_SECRET_ACCESS_KEY"
echo "   - STAGING_AWS_ACCESS_KEY_ID"
echo "   - STAGING_AWS_SECRET_ACCESS_KEY"
echo "   - PRODUCTION_AWS_ACCESS_KEY_ID"
echo "   - PRODUCTION_AWS_SECRET_ACCESS_KEY"
echo ""
echo "🔑 API Keys (shared):"
echo "   - OPENAI_API_KEY"
echo "   - SENDGRID_API_KEY"
echo ""
echo "🌐 Rails API Configuration (per environment):"
echo "   - TESTING_RAILS_API_BASE_URL"
echo "   - TESTING_RAILS_API_KEY"
echo "   - STAGING_RAILS_API_BASE_URL"
echo "   - STAGING_RAILS_API_KEY"
echo "   - PRODUCTION_RAILS_API_BASE_URL"
echo "   - PRODUCTION_RAILS_API_KEY"
echo ""

read -p "Do you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 0
fi

# Function to set a secret
set_secret() {
    local secret_name="$1"
    local description="$2"

    echo ""
    echo "🔐 Setting up: $secret_name"
    echo "Description: $description"

    # Check if secret already exists
    if gh secret list | grep -q "^$secret_name"; then
        read -p "Secret '$secret_name' already exists. Overwrite? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Skipped $secret_name"
            return
        fi
    fi

    read -s -p "Enter value for $secret_name: " secret_value
    echo

    if [ -z "$secret_value" ]; then
        echo "⚠️  Empty value, skipping $secret_name"
        return
    fi

    if gh secret set "$secret_name" --body "$secret_value"; then
        echo "✅ Set $secret_name"
    else
        echo "❌ Failed to set $secret_name"
    fi
}

echo ""
echo "🚀 Starting secret setup..."

# AWS Credentials
echo ""
echo "=== AWS Credentials ==="

set_secret "TESTING_AWS_ACCESS_KEY_ID" "AWS Access Key ID for testing environment"
set_secret "TESTING_AWS_SECRET_ACCESS_KEY" "AWS Secret Access Key for testing environment"

set_secret "STAGING_AWS_ACCESS_KEY_ID" "AWS Access Key ID for staging environment"
set_secret "STAGING_AWS_SECRET_ACCESS_KEY" "AWS Secret Access Key for staging environment"

set_secret "PRODUCTION_AWS_ACCESS_KEY_ID" "AWS Access Key ID for production environment"
set_secret "PRODUCTION_AWS_SECRET_ACCESS_KEY" "AWS Secret Access Key for production environment"

# API Keys
echo ""
echo "=== API Keys ==="

set_secret "OPENAI_API_KEY" "OpenAI API key for LLM services"
set_secret "SENDGRID_API_KEY" "SendGrid API key for email services"

# Rails API Configuration
echo ""
echo "=== Rails API Configuration ==="

set_secret "TESTING_RAILS_API_BASE_URL" "Rails API base URL for testing (e.g., https://api-testing.example.com)"
set_secret "TESTING_RAILS_API_KEY" "Rails API key for testing environment"

set_secret "STAGING_RAILS_API_BASE_URL" "Rails API base URL for staging (e.g., https://api-staging.example.com)"
set_secret "STAGING_RAILS_API_KEY" "Rails API key for staging environment"

set_secret "PRODUCTION_RAILS_API_BASE_URL" "Rails API base URL for production (e.g., https://api.example.com)"
set_secret "PRODUCTION_RAILS_API_KEY" "Rails API key for production environment"

echo ""
echo "🎉 Secret setup completed!"
echo ""

# Show summary of set secrets
echo "📋 Summary of configured secrets:"
gh secret list

echo ""
echo "🔍 Next steps:"
echo "1. Set up GitHub environments (testing, staging, production)"
echo "2. Configure environment protection rules"
echo "3. Test the deployment workflows"
echo "4. Review the documentation: docs/github-actions.md"
echo ""
echo "✅ GitHub Actions secrets setup complete!"
