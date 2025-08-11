# GitHub Actions CI/CD Documentation

## Overview

This document describes the GitHub Actions workflows for the AIME Planner project, providing automated testing, building, and deployment across multiple environments.

## Workflow Architecture

### Branch-Based Deployment Strategy

| Branch | Environment | Trigger | Purpose |
|--------|-------------|---------|---------|
| `develop` | Testing | Push | Development integration and testing |
| `staging` | Staging | Push | Pre-production validation |
| `main` | Production | Push | Live production deployment |

### Workflows

1. **Continuous Integration** (`ci.yml`) - Runs on all PRs and pushes
2. **Deploy Testing** (`deploy-testing.yml`) - Deploys to testing environment
3. **Deploy Staging** (`deploy-staging.yml`) - Deploys to staging environment
4. **Deploy Production** (`deploy-production.yml`) - Deploys to production environment

## Workflow Details

### 1. Continuous Integration (`ci.yml`)

**Triggers:**
- Pull requests to `develop`, `staging`, `main`
- Pushes to `develop`, `staging`, `main`
- Manual dispatch

**Jobs:**
- **test**: Runs unit tests with coverage
- **validate-sam**: Validates AWS SAM template
- **security-scan**: Security vulnerability scanning (PR only)

**Features:**
- Python dependency caching
- Code linting with flake8
- 80% coverage requirement
- Codecov integration
- Security scanning with Safety, Bandit, TruffleHog

### 2. Deploy Testing (`deploy-testing.yml`)

**Triggers:**
- Push to `develop` branch
- Manual dispatch

**Environment:** `testing`

**Steps:**
1. Checkout and setup Python
2. Install dependencies and run tests
3. Setup AWS SAM CLI
4. Configure AWS credentials for testing
5. Validate and build SAM application
6. Deploy to testing environment
7. Run integration tests
8. Notify deployment status

### 3. Deploy Staging (`deploy-staging.yml`)

**Triggers:**
- Push to `staging` branch
- Manual dispatch

**Environment:** `staging`

**Steps:**
1. Checkout and setup Python
2. Install dependencies and run tests
3. Setup AWS SAM CLI
4. Configure AWS credentials for staging
5. Validate and build SAM application
6. Deploy to staging environment
7. Run smoke tests
8. Notify deployment status

### 4. Deploy Production (`deploy-production.yml`)

**Triggers:**
- Push to `main` branch
- Manual dispatch

**Environment:** `production`

**Steps:**
1. Checkout and setup Python
2. Install dependencies and run comprehensive tests
3. Setup AWS SAM CLI
4. Configure AWS credentials for production
5. Validate and build SAM application
6. Deploy to production environment (with approval)
7. Run production health checks
8. Create deployment tag
9. Notify deployment status

## Required GitHub Secrets

### AWS Credentials (per environment)

**Testing Environment:**
- `TESTING_AWS_ACCESS_KEY_ID`
- `TESTING_AWS_SECRET_ACCESS_KEY`

**Staging Environment:**
- `STAGING_AWS_ACCESS_KEY_ID`
- `STAGING_AWS_SECRET_ACCESS_KEY`

**Production Environment:**
- `PRODUCTION_AWS_ACCESS_KEY_ID`
- `PRODUCTION_AWS_SECRET_ACCESS_KEY`

### API Keys (shared across environments)

- `OPENAI_API_KEY` - OpenAI API access
- `SENDGRID_API_KEY` - SendGrid email service

### Rails API Configuration (per environment)

**Testing:**
- `TESTING_RAILS_API_BASE_URL`
- `TESTING_RAILS_API_KEY`

**Staging:**
- `STAGING_RAILS_API_BASE_URL`
- `STAGING_RAILS_API_KEY`

**Production:**
- `PRODUCTION_RAILS_API_BASE_URL`
- `PRODUCTION_RAILS_API_KEY`

## GitHub Environments

### Setting Up Environments

1. Go to repository **Settings** → **Environments**
2. Create environments: `testing`, `staging`, `production`
3. Configure protection rules for each environment

### Environment Protection Rules

**Testing:**
- No protection rules (automatic deployment)

**Staging:**
- Optional: Required reviewers
- Optional: Wait timer (e.g., 5 minutes)

**Production:**
- **Required reviewers** (at least 2)
- **Wait timer** (e.g., 10 minutes for review)
- **Restrict to main branch only**

## Deployment Process

### Development Flow

1. **Feature Development**
   ```bash
   git checkout -b feature/new-feature
   # Make changes
   git push origin feature/new-feature
   # Create PR to develop
   ```

2. **Testing Environment**
   ```bash
   git checkout develop
   git merge feature/new-feature
   git push origin develop
   # Triggers automatic deployment to testing
   ```

3. **Staging Environment**
   ```bash
   git checkout staging
   git merge develop
   git push origin staging
   # Triggers automatic deployment to staging
   ```

4. **Production Environment**
   ```bash
   git checkout main
   git merge staging
   git push origin main
   # Triggers deployment to production (with approval)
   ```

### Manual Deployment

All workflows support manual triggering:

1. Go to **Actions** tab in GitHub
2. Select the desired workflow
3. Click **Run workflow**
4. Choose branch and environment
5. Click **Run workflow**

## Monitoring and Notifications

### Deployment Status

Each workflow provides clear status notifications:
- ✅ Successful deployment
- ❌ Failed deployment
- 🚀 Production deployment started
- 🎉 Production deployment complete

### Logs and Debugging

1. **View workflow runs**: Actions tab → Select workflow
2. **Check logs**: Click on workflow run → Expand job steps
3. **Download artifacts**: Test results, coverage reports
4. **Re-run jobs**: Click "Re-run jobs" button

### Common Issues

**Deploy Failures:**
- Check AWS credentials are valid
- Verify SAM template syntax
- Ensure environment secrets are set
- Check CloudFormation stack limits

**Test Failures:**
- Review test output in logs
- Check environment variable configuration
- Verify test dependencies are installed

## Security Considerations

### Secrets Management

- **Never commit secrets** to repository
- Use **GitHub Secrets** for sensitive data
- **Rotate credentials** regularly
- **Principle of least privilege** for AWS IAM

### Access Control

- **Branch protection rules** on main/staging
- **Required reviews** for production deployments
- **Environment-specific secrets** isolation
- **Audit logs** for deployment activities

### Security Scanning

- **Dependency vulnerabilities** (Safety)
- **Static code analysis** (Bandit)
- **Secret scanning** (TruffleHog)
- **Coverage enforcement** (80% minimum)

## Customization

### Adding New Environments

1. Create new environment in GitHub
2. Add AWS credentials as secrets
3. Create new workflow file
4. Update SAM configuration
5. Add environment-specific parameters

### Modifying Deployment Steps

1. Edit workflow YAML files
2. Add/remove steps as needed
3. Update environment variables
4. Test with manual dispatch
5. Commit changes

### Integration with External Services

- **Slack notifications**: Add webhook steps
- **Email alerts**: Configure SendGrid notifications
- **Monitoring**: Add health check endpoints
- **Rollback**: Implement automated rollback procedures

## Troubleshooting

### Common Commands

```bash
# Local SAM validation
sam validate

# Local SAM build
sam build --use-container

# Local testing
python -m pytest tests/unit/

# Check workflow syntax
github-actions-validator .github/workflows/
```

### Useful Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS SAM CLI Reference](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-command-reference.html)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)

## Best Practices

1. **Test locally** before pushing
2. **Use pull requests** for all changes
3. **Review deployment logs** after each deployment
4. **Monitor application health** post-deployment
5. **Keep secrets updated** and secure
6. **Document any manual steps** required
7. **Maintain environment parity** across testing/staging/production
