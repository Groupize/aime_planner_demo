# AIME Planner Project Structure

```
aime_planner_demo/
├── README.md                     # Complete setup and usage documentation
├── template.yaml                 # AWS SAM CloudFormation template
├── samconfig.toml               # SAM deployment configuration for all environments
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # LocalStack development environment
├── .gitignore                  # Git ignore patterns
├── env.example                 # Environment variables template
│
├── src/                        # Source code
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   └── conversation.py     # Conversation, Question, EventMetadata models
│   │
│   ├── services/               # Business logic services
│   │   ├── __init__.py
│   │   ├── database.py         # DynamoDB operations
│   │   ├── email_service.py    # SendGrid/SES email handling
│   │   ├── llm_service.py      # OpenAI integration for email generation
│   │   └── rails_api.py        # Rails backend communication
│   │
│   └── handlers/               # Lambda function handlers
│       ├── __init__.py
│       ├── initiate_bid.py     # Initial bid request handler
│       └── process_email.py    # Inbound email processing handler
│
├── scripts/                    # Deployment and utility scripts
│   ├── deploy.sh              # Multi-environment deployment script
│   ├── local-setup.sh         # LocalStack setup script
│   └── test-local.sh          # Local testing script
│
├── localstack-setup/          # LocalStack initialization
│   └── 01-setup-resources.sh  # DynamoDB tables and AWS resource setup
│
├── test-data/                 # Sample test data
│   ├── sample-request.json    # Hotel booking test data
│   └── restaurant-request.json # Restaurant booking test data
│
└── docs/                      # Additional documentation
    └── sendgrid-setup.md      # Detailed SendGrid configuration guide
```

## Key Components

### AWS Infrastructure (template.yaml)
- **Lambda Functions**: `InitiateBidFunction`, `ProcessEmailFunction`
- **DynamoDB Tables**: Conversations and Questions storage
- **API Gateway**: REST API for Rails integration
- **SES + SNS**: Email receiving pipeline
- **IAM Roles**: Proper permissions for all services

### Core Models (src/models/)
- **Conversation**: Complete conversation state management
- **Question**: Individual question tracking with answers
- **EventMetadata**: Event planning details
- **VendorInfo**: Vendor contact information

### Business Services (src/services/)
- **DatabaseService**: DynamoDB CRUD operations
- **EmailService**: SendGrid sending + SES receiving
- **LLMService**: OpenAI email generation and parsing
- **RailsAPIService**: Backend communication with retry logic

### Lambda Handlers (src/handlers/)
- **initiate_bid**: Processes Rails API requests, generates initial emails
- **process_email**: Handles vendor responses, manages follow-up conversations

### Development Tools
- **LocalStack**: Complete local AWS environment simulation
- **Docker Compose**: Containerized development setup
- **SAM CLI**: Serverless application deployment
- **Test Scripts**: Automated local testing

## Data Flow

```
1. Rails API Request → API Gateway → InitiateBidFunction
   ├── Save conversation to DynamoDB
   ├── Generate email with OpenAI
   ├── Send email via SendGrid
   └── Notify Rails API of status

2. Vendor Email Response → SendGrid Parse → SES → SNS → ProcessEmailFunction
   ├── Parse response with OpenAI
   ├── Update conversation state
   ├── Generate follow-up if needed
   ├── Send follow-up via SendGrid
   └── Update Rails API with results
```

## Environment Support

### Testing Environment
- Stack: `aime-planner-testing`
- Profile: `groupize-testing`
- Domain: `aime-testing@groupize.com`
- API: `https://api-testing.groupize.com`

### Staging Environment
- Stack: `aime-planner-staging`
- Profile: `groupize-staging`
- Domain: `aime-staging@groupize.com`
- API: `https://api-staging.groupize.com`

### Production Environment
- Stack: `aime-planner-production`
- Profile: `groupize-production`
- Domain: `aime-production@groupize.com`
- API: `https://api.groupize.com`

## Quick Start Commands

```bash
# Local development
./scripts/local-setup.sh
./scripts/test-local.sh

# Deploy to testing
./scripts/deploy.sh testing

# Deploy to staging
./scripts/deploy.sh staging

# Deploy to production
./scripts/deploy.sh production
```

## Configuration Requirements

1. **AWS CLI Profiles**: Set up three profiles for different environments
2. **API Keys**: OpenAI, SendGrid, Rails API keys in environment variables
3. **Domain Setup**: Configure MX records for email receiving
4. **SendGrid**: Inbound parse webhook configuration

## Monitoring and Debugging

- **CloudWatch Logs**: `/aws/lambda/{environment}-aime-*`
- **DynamoDB**: Conversation and question state
- **SendGrid**: Email delivery and parse webhook monitoring
- **API Gateway**: Request/response logging

## Security Features

- **Environment Isolation**: Separate AWS accounts and stacks
- **API Key Management**: Secure parameter storage
- **Email Security**: SPF/DKIM/MX record configuration
- **IAM Permissions**: Least privilege access policies
