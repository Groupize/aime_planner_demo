#!/bin/bash

# LocalStack initialization script for AIME Planner resources
echo "Setting up AIME Planner resources in LocalStack..."

# Wait for LocalStack to be ready
sleep 5

# Set AWS CLI to use LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:4566

# Create DynamoDB tables
echo "Creating DynamoDB tables..."

# Conversations table
aws dynamodb create-table \
    --table-name testing-aime-conversations \
    --attribute-definitions \
        AttributeName=conversation_id,AttributeType=S \
        AttributeName=created_at,AttributeType=S \
    --key-schema \
        AttributeName=conversation_id,KeyType=HASH \
    --global-secondary-indexes \
        IndexName=CreatedAtIndex,KeySchema=[{AttributeName=created_at,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --endpoint-url=http://localhost:4566

# Questions table
aws dynamodb create-table \
    --table-name testing-aime-questions \
    --attribute-definitions \
        AttributeName=conversation_id,AttributeType=S \
        AttributeName=question_id,AttributeType=N \
    --key-schema \
        AttributeName=conversation_id,KeyType=HASH \
        AttributeName=question_id,KeyType=RANGE \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --endpoint-url=http://localhost:4566

# Create SNS topic for email processing
echo "Creating SNS topic..."
aws sns create-topic \
    --name testing-aime-email-processing \
    --endpoint-url=http://localhost:4566

# Create S3 bucket for SAM artifacts
echo "Creating S3 bucket for deployments..."
aws s3 mb s3://aime-planner-testing-deployments \
    --endpoint-url=http://localhost:4566

# Set up SES domain verification (mock)
echo "Setting up SES domain..."
aws ses verify-domain-identity \
    --domain groupize.com \
    --endpoint-url=http://localhost:4566

# Create SES receipt rule set
aws ses create-receipt-rule-set \
    --rule-set-name testing-aime-email-rules \
    --endpoint-url=http://localhost:4566

# Set as active rule set
aws ses set-active-receipt-rule-set \
    --rule-set-name testing-aime-email-rules \
    --endpoint-url=http://localhost:4566

echo "LocalStack setup completed!"
echo "You can now deploy your SAM application with:"
echo "  sam build && sam deploy --config-env testing"
