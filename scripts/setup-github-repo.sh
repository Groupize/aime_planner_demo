#!/bin/bash

# GitHub Repository Setup Script for AIME Planner
# This script initializes the repository and pushes it to GitHub

set -e

REPO_NAME="aime_planner_demo"
ORG_NAME="Groupize"
REPO_URL="git@github.com:${ORG_NAME}/${REPO_NAME}.git"

echo "🚀 Setting up GitHub repository for AIME Planner"
echo "=" * 50
echo "Repository: ${ORG_NAME}/${REPO_NAME}"
echo "URL: ${REPO_URL}"
echo ""

# Check if we're in the right directory
if [[ "$(basename $(pwd))" != "$REPO_NAME" ]]; then
    echo "❌ Error: This script should be run from the $REPO_NAME directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Check if GitHub CLI is available
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo "Please install it from: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated with GitHub CLI
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI."
    echo "Please run: gh auth login"
    exit 1
fi

# Check SSH access to GitHub
echo "🔑 Checking SSH access to GitHub..."
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "✅ SSH access to GitHub confirmed"
elif ssh -T git@github.com 2>&1 | grep -q "Permission denied"; then
    echo "❌ SSH key not configured for GitHub"
    echo "Please set up SSH key authentication:"
    echo "1. Generate SSH key: ssh-keygen -t ed25519 -C \"your_email@example.com\""
    echo "2. Add to ssh-agent: ssh-add ~/.ssh/id_ed25519"
    echo "3. Add public key to GitHub: https://github.com/settings/keys"
    exit 1
else
    echo "⚠️  Could not verify SSH access to GitHub"
    echo "Proceeding anyway, but you may need to set up SSH keys if push fails"
fi

echo "✅ Prerequisites check passed"
echo ""

# Initialize git repository if not already initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "📦 Git repository already exists"
fi

# Set default branch to main
echo "🌿 Setting default branch to main..."
git checkout -b main 2>/dev/null || git checkout main

# Add all files to staging
echo "📁 Adding files to Git..."
git add .

# Check if there are any changes to commit
if git diff --staged --quiet; then
    echo "⚠️  No changes to commit"
else
    # Create initial commit
    echo "💾 Creating initial commit..."
    git commit -m "Initial commit: AIME Planner chatbot application

- Complete AWS Lambda-based chatbot for vendor negotiations
- Automated email processing with LLM integration
- Multi-environment deployment with AWS SAM
- Comprehensive unit test suite (98 tests, 85% coverage)
- GitHub Actions CI/CD pipeline (temporarily disabled)
- LocalStack development environment
- Complete documentation and setup scripts

Features:
- OpenAI LLM for email generation and parsing
- SendGrid email service integration
- DynamoDB conversation state management
- Rails API integration for callbacks
- Professional email communication with vendors
- Multi-attempt conversation flow with business logic"

    echo "✅ Initial commit created"
fi

# Create repository on GitHub
echo "🌐 Creating repository on GitHub..."
if gh repo create "${ORG_NAME}/${REPO_NAME}" \
    --public \
    --description "AI-powered chatbot for negotiating vendor pricing via email communication" \
    --homepage "https://github.com/${ORG_NAME}/${REPO_NAME}" \
    --clone=false; then
    echo "✅ Repository created on GitHub"
else
    echo "⚠️  Repository might already exist on GitHub"
fi

# Add remote origin
echo "🔗 Adding remote origin..."
if git remote get-url origin &> /dev/null; then
    echo "⚠️  Remote origin already exists, updating..."
    git remote set-url origin "$REPO_URL"
else
    git remote add origin "$REPO_URL"
fi
echo "✅ Remote origin configured"

# Push to GitHub
echo "⬆️  Pushing to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "🎉 Repository successfully created and pushed to GitHub!"
echo ""
echo "📋 Repository Details:"
echo "   Organization: ${ORG_NAME}"
echo "   Repository: ${REPO_NAME}"
echo "   SSH URL: ${REPO_URL}"
echo "   HTTPS URL: https://github.com/${ORG_NAME}/${REPO_NAME}"
echo "   Branch: main"
echo ""
echo "🔧 Next Steps:"
echo "1. Set up GitHub environments (testing, staging, production)"
echo "2. Configure repository secrets using: ./scripts/setup-github-secrets.sh"
echo "3. Enable deployment workflows when ready"
echo "4. Review and customize branch protection rules"
echo ""
echo "📚 Documentation:"
echo "- README.md - Project overview and setup"
echo "- docs/github-actions.md - CI/CD pipeline documentation"
echo "- scripts/setup-github-environments.md - Environment setup guide"
echo ""
echo "✅ GitHub repository setup complete!"
