#!/bin/bash

# Script to re-enable GitHub Actions deployment workflows
# Run this when you're ready to activate automatic deployments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Enabling GitHub Actions Deployment Workflows"
echo "=" * 50

cd "$PROJECT_ROOT"

# Function to enable deployment triggers in a workflow file
enable_workflow() {
    local workflow_file="$1"
    local branch_name="$2"

    echo "🔧 Enabling $workflow_file for $branch_name branch..."

    # Replace commented push triggers with active ones
    sed -i.bak "s/  # push:/  push:/" "$workflow_file"
    sed -i.bak "s/  #   branches: \[ $branch_name \]/    branches: [ $branch_name ]/" "$workflow_file"

    # Remove backup file
    rm -f "${workflow_file}.bak"

    echo "✅ Enabled $workflow_file"
}

# Enable each deployment workflow
enable_workflow ".github/workflows/deploy-testing.yml" "develop"
enable_workflow ".github/workflows/deploy-staging.yml" "staging"
enable_workflow ".github/workflows/deploy-production.yml" "main"

echo ""
echo "🎉 All deployment workflows have been enabled!"
echo ""
echo "📋 Active Deployment Triggers:"
echo "   develop → Testing Environment (automatic)"
echo "   staging → Staging Environment (automatic)"
echo "   main    → Production Environment (requires approval)"
echo ""
echo "⚠️  Important: Before pushing, ensure you have:"
echo "1. ✅ GitHub environments configured (testing, staging, production)"
echo "2. ✅ Repository secrets set up"
echo "3. ✅ AWS credentials configured for each environment"
echo "4. ✅ Required reviewers added for production environment"
echo ""
echo "🚦 To commit and deploy the changes:"
echo "   git add .github/workflows/"
echo "   git commit -m 'Enable GitHub Actions deployment workflows'"
echo "   git push origin main"
echo ""
echo "✅ Deployment workflows are now ready to use!"
