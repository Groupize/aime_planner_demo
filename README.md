# AIME Planner Chatbot

A serverless chatbot application for automated event service negotiations, built with AWS Lambda, SendGrid, and OpenAI.

## Overview

This application acts as an intelligent intermediary between event planners and vendors (hotels, restaurants, caterers, etc.) to negotiate pricing and availability. It:

1. **Receives bid requests** from a Rails API with event details and vendor questions
2. **Sends professional emails** to vendors using AI-generated content
3. **Processes vendor responses** using LLM parsing to extract answers
4. **Manages follow-up conversations** until all required questions are answered
5. **Reports results** back to the Rails API

## Architecture

```
Rails API → API Gateway → Lambda (Initiate Bid) → SendGrid → Vendor
                                     ↓
                              DynamoDB (State)
                                     ↓
Vendor → SendGrid Parse → SES → SNS → Lambda (Process Email) → Rails API
```

### Core Components

- **AWS Lambda Functions**: `initiate_bid`, `process_email`
- **DynamoDB**: Conversation and question state management
- **API Gateway**: REST API for Rails integration
- **SES + SNS**: Inbound email processing pipeline
- **SendGrid**: Outbound email delivery
- **OpenAI**: Email generation and response parsing

## Prerequisites

- Python 3.11+
- AWS CLI configured with appropriate profiles
- AWS SAM CLI
- Docker and Docker Compose (for local development)
- OpenAI API key
- SendGrid API key

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd aime_planner_demo

# Create environment file
cp env.example .env
# Edit .env with your actual API keys
```

### 2. Local Development with LocalStack

```bash
# Start local environment
./scripts/local-setup.sh

# This will:
# - Start LocalStack
# - Create DynamoDB tables
# - Deploy Lambda functions locally
# - Set up local email processing
```

### 3. Deploy to Testing Environment

```bash
# Deploy to testing
./scripts/deploy.sh testing

# Deploy to staging
./scripts/deploy.sh staging

# Deploy to production (requires confirmation)
./scripts/deploy.sh production
```

## Environment Configuration

### AWS Profiles

Configure three AWS CLI profiles:

```bash
# Testing environment
aws configure --profile groupize-testing

# Staging environment
aws configure --profile groupize-staging

# Production environment
aws configure --profile groupize-production
```

### Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# API Keys (required)
OPENAI_API_KEY=sk-...
SENDGRID_API_KEY=SG...
RAILS_API_KEY=your_rails_api_key

# Rails API URLs (environment-specific)
RAILS_API_BASE_URL=https://api-testing.groupize.com  # testing
RAILS_API_BASE_URL=https://api-staging.groupize.com  # staging
RAILS_API_BASE_URL=https://api.groupize.com          # production
```

## API Usage

### Initiate Bid Request

**Endpoint**: `POST /initiate-bid`

**Request Body**:
```json
{
  "event_metadata": {
    "name": "Annual Company Retreat",
    "dates": ["2024-06-15", "2024-06-16"],
    "event_type": "corporate retreat",
    "planner_name": "Jane Smith",
    "planner_email": "jane.smith@company.com",
    "planner_phone": "+1-555-123-4567"
  },
  "vendor_info": {
    "name": "Mountain View Resort",
    "email": "sales@mountainviewresort.com",
    "service_type": "hotel"
  },
  "questions": [
    {
      "id": 1,
      "text": "Do you have availability for our dates?",
      "required": true
    },
    {
      "id": 2,
      "text": "What is your rate per room per night?",
      "required": true,
      "options": ["Standard Room", "Deluxe Room", "Suite"]
    }
  ],
  "callback_data": {
    "rails_request_id": "req_123",
    "planner_id": 456
  }
}
```

**Response**:
```json
{
  "message": "Bid request initiated successfully",
  "conversation_id": "uuid-string",
  "email_sent": true,
  "vendor_email": "sales@mountainviewresort.com",
  "questions_count": 2
}
```

## Email Processing Flow

### 1. Initial Email Generation

The LLM generates a professional, conversational email that:
- Introduces the planner and event
- Asks all questions naturally
- Maintains a semi-casual, professional tone
- Includes clear call-to-action

### 2. Vendor Response Processing

Incoming emails are:
- Parsed via SendGrid inbound parse webhook
- Routed through SES → SNS → Lambda
- Analyzed by LLM to extract answers
- Matched to original questions by ID

### 3. Follow-up Management

The system automatically:
- Identifies unanswered required questions
- Generates appropriate follow-up emails
- Manages up to 4 attempts per conversation
- Escalates to Rails API when complete

## Local Development

### Starting LocalStack

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f localstack

# Stop services
docker-compose down
```

### Testing the API

```bash
# Test initiate-bid endpoint
curl -X POST http://localhost:4566/restapis/{api-id}/testing/_user_request_/initiate-bid \
  -H "Content-Type: application/json" \
  -d @test-data/sample-request.json
```

### Monitoring DynamoDB

```bash
# List tables
aws dynamodb list-tables --endpoint-url http://localhost:4566

# Scan conversations
aws dynamodb scan \
  --table-name testing-aime-conversations \
  --endpoint-url http://localhost:4566
```

## Deployment

### Automated GitHub Actions Deployment

The project includes automated CI/CD pipelines that deploy to different environments based on branch pushes:

- **Push to `develop`** → Deploys to **Testing** environment
- **Push to `staging`** → Deploys to **Staging** environment
- **Push to `main`** → Deploys to **Production** environment (with approval)

#### Setting Up GitHub Actions

1. **Configure Secrets**: Run the setup script to configure required secrets
   ```bash
   ./scripts/setup-github-secrets.sh
   ```

2. **Set Up Environments**: Follow the guide to create GitHub environments
   ```bash
   # View the setup guide
   cat scripts/setup-github-environments.md
   ```

3. **Deploy**: Push to the appropriate branch
   ```bash
   # Deploy to testing
   git push origin develop

   # Deploy to staging
   git push origin staging

   # Deploy to production (requires approval)
   git push origin main
   ```

For detailed information, see [GitHub Actions Documentation](docs/github-actions.md).

> **Note**: Deployment workflows are currently disabled. Run `./scripts/enable-deployments.sh` when ready to activate automatic deployments.

### Manual Production Deployment

#### Prerequisites

1. **Domain Setup**: Configure `groupize.com` domain in SES
2. **SendGrid Integration**: Set up inbound parse webhook
3. **Rails API**: Ensure callback endpoints are implemented
4. **Monitoring**: Set up CloudWatch alerts

#### Manual Deployment Steps

```bash
# 1. Validate configuration
sam validate

# 2. Deploy to staging first
./scripts/deploy.sh staging

# 3. Test staging thoroughly
# 4. Deploy to production
./scripts/deploy.sh production
```

### Post-Deployment Configuration

1. **SES Domain Verification**:
   ```bash
   aws ses verify-domain-identity --domain groupize.com
   # Add TXT record to DNS
   ```

2. **SendGrid Inbound Parse**:
   - URL: `https://{api-gateway-url}/process-email`
   - Domain: `aime-{environment}@groupize.com`

3. **Rails API Integration**:
   - Configure callback URLs
   - Set up API authentication
   - Test end-to-end flow

## Monitoring and Troubleshooting

### CloudWatch Logs

```bash
# View Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/testing-aime"

# Tail logs
aws logs tail /aws/lambda/testing-aime-initiate-bid --follow
```

### DynamoDB Monitoring

```bash
# Check conversation status
aws dynamodb scan \
  --table-name testing-aime-conversations \
  --filter-expression "#status = :status" \
  --expression-attribute-names '{"#status": "status"}' \
  --expression-attribute-values '{":status": {"S": "failed"}}'
```

### Common Issues

1. **Email Delivery Failures**:
   - Check SendGrid API key and domain setup
   - Verify sender reputation
   - Review bounce/spam reports

2. **LLM Parsing Errors**:
   - Check OpenAI API key and quota
   - Review prompt engineering
   - Validate input data format

3. **Database Connection Issues**:
   - Verify IAM permissions
   - Check DynamoDB table configuration
   - Monitor read/write capacity

## Security Considerations

### API Keys
- Store in AWS Parameter Store or Secrets Manager
- Rotate regularly
- Use least-privilege access

### Email Security
- Implement SPF/DKIM records
- Monitor for abuse
- Rate limit conversations per vendor

### Data Privacy
- Encrypt sensitive data at rest
- Implement data retention policies
- Log access for audit trails

## Future Enhancements

- **Voice Integration**: Text-to-speech for phone calls
- **Multi-language Support**: International vendor communication
- **Advanced Analytics**: Negotiation success metrics
- **Integration Testing**: Automated end-to-end tests
- **Performance Optimization**: Conversation caching

## Support

For questions or issues:
1. Check CloudWatch logs for error details
2. Review DynamoDB conversation state
3. Test individual components in isolation
4. Contact the development team with relevant logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test locally with LocalStack
4. Deploy to testing environment
5. Submit pull request with tests

---

**Environment URLs**:
- Testing: `https://{api-id}.execute-api.us-east-1.amazonaws.com/testing`
- Staging: `https://{api-id}.execute-api.us-east-1.amazonaws.com/staging`
- Production: `https://{api-id}.execute-api.us-east-1.amazonaws.com/production`
