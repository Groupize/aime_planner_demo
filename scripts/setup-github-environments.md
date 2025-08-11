# Setting Up GitHub Environments

This guide will help you set up GitHub environments for the AIME Planner project to enable automated deployments with proper protection rules.

## Step 1: Create Environments

1. Go to your GitHub repository
2. Navigate to **Settings** → **Environments**
3. Click **New environment**
4. Create three environments:
   - `testing`
   - `staging`
   - `production`

## Step 2: Configure Environment Protection Rules

### Testing Environment

**Purpose**: Rapid development testing and integration

**Protection Rules**: None (automatic deployment)
- ✅ Allow automatic deployment
- ❌ No required reviewers
- ❌ No wait timer

**Configuration**:
- No protection rules needed
- Deployments trigger automatically on push to `develop`

### Staging Environment

**Purpose**: Pre-production validation and stakeholder review

**Protection Rules**: Light protection
- ✅ Optional: Required reviewers (1 person)
- ✅ Optional: Wait timer (5 minutes)
- ✅ Restrict to `staging` branch

**Configuration**:
1. **Required reviewers**: Add 1 team member (optional)
2. **Wait timer**: 5 minutes (optional)
3. **Deployment branches**:
   - Selected branches: `staging`

### Production Environment

**Purpose**: Live production system

**Protection Rules**: Strict protection
- ✅ **Required reviewers** (minimum 2)
- ✅ **Wait timer** (10 minutes)
- ✅ **Restrict to main branch**
- ✅ **Prevent self-review**

**Configuration**:
1. **Required reviewers**:
   - Add at least 2 team members
   - Check "Prevent self-review"
2. **Wait timer**: 10 minutes
3. **Deployment branches**:
   - Selected branches: `main`

## Step 3: Configure Environment Secrets

Each environment can have its own secrets that override repository secrets.

### Testing Environment Secrets
```
# No environment-specific secrets needed
# Uses repository-level secrets with TESTING_ prefix
```

### Staging Environment Secrets
```
# No environment-specific secrets needed
# Uses repository-level secrets with STAGING_ prefix
```

### Production Environment Secrets
```
# No environment-specific secrets needed
# Uses repository-level secrets with PRODUCTION_ prefix
```

## Step 4: Verify Environment Setup

1. **Check environments exist**:
   - Go to Settings → Environments
   - Verify all three environments are listed

2. **Test protection rules**:
   - Try to manually trigger a production deployment
   - Verify it requires approval

3. **Verify branch restrictions**:
   - Ensure production only deploys from `main`
   - Ensure staging only deploys from `staging`

## Step 5: Set Up Reviewers

### Adding Reviewers

1. Go to each environment settings
2. Click **Add required reviewers**
3. Add team members or teams
4. Configure review requirements

### Reviewer Best Practices

**Testing**: No reviewers needed
**Staging**: 1 reviewer (optional, for visibility)
**Production**: 2+ reviewers (required)

### Reviewer Guidelines

**Review Checklist**:
- [ ] Are tests passing?
- [ ] Is the change properly tested?
- [ ] Are there any breaking changes?
- [ ] Is documentation updated?
- [ ] Are database migrations safe?
- [ ] Are environment variables updated?

## Complete Setup Verification

Run this checklist to ensure everything is configured correctly:

### Repository Setup
- [ ] All workflow files exist in `.github/workflows/`
- [ ] Repository secrets are configured
- [ ] SAM configuration is valid

### Environment Setup
- [ ] Testing environment exists (no protection)
- [ ] Staging environment exists (light protection)
- [ ] Production environment exists (strict protection)
- [ ] Branch restrictions are configured
- [ ] Required reviewers are added

### Deployment Testing
- [ ] Push to `develop` triggers testing deployment
- [ ] Push to `staging` triggers staging deployment
- [ ] Push to `main` requires approval for production
- [ ] Manual workflows can be triggered
- [ ] Deployment status is reported correctly

## Troubleshooting

### Common Issues

**Environment not found**:
- Verify environment name matches workflow file
- Check spelling and capitalization

**Missing reviewers**:
- Add users as repository collaborators first
- Use team names for organization repositories

**Failed deployments**:
- Check AWS credentials are valid
- Verify SAM template syntax
- Review CloudFormation stack status

**Permission denied**:
- Check GitHub token permissions
- Verify repository access for reviewers
- Ensure AWS IAM permissions are correct

### Support Resources

- [GitHub Environments Documentation](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [Environment Protection Rules](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment#environment-protection-rules)
- [Required Reviewers](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment#required-reviewers)
