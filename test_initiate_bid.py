#!/usr/bin/env python3
"""
Test script for the initiate_bid lambda function.
This runs the function directly in the current environment.
"""

import json
import os
import sys

import boto3

# Set environment variables for testing
os.environ.update({
    'ENVIRONMENT': 'testing',
    'RAILS_API_BASE_URL': 'http://localhost:3000',
    'RAILS_API_KEY': 'test-key',
    'OPENAI_API_KEY': 'test-openai-key',
    'SENDGRID_API_KEY': 'test-sendgrid-key',
    'CONVERSATION_TABLE_NAME': 'testing-aime-conversations',
    'QUESTIONS_TABLE_NAME': 'testing-aime-questions',
    'AWS_ACCESS_KEY_ID': 'test',
    'AWS_SECRET_ACCESS_KEY': 'test',
    'AWS_DEFAULT_REGION': 'us-east-1',
    'AWS_ENDPOINT_URL': 'http://localhost:4566',
    'LOCALSTACK_HOSTNAME': 'localhost'
})

# Configure boto3 to use LocalStack
boto3.setup_default_session(
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name='us-east-1'
)

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the handler
from handlers.initiate_bid import lambda_handler

def main():
    """Test the initiate_bid function with sample data."""

    # Load test data
    with open('test-data/sample-request.json', 'r') as f:
        body_data = json.load(f)

    # Create test event
    event = {
        'httpMethod': 'POST',
        'path': '/initiate-bid',
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body_data)
    }

    # Mock context
    class MockContext:
        def __init__(self):
            self.function_name = 'testing-aime-initiate-bid'
            self.memory_limit_in_mb = 512
            self.invoked_function_arn = 'arn:aws:lambda:us-east-1:000000000000:function:testing-aime-initiate-bid'
            self.aws_request_id = 'test-request-id'

    context = MockContext()

    print("🧪 Testing initiate_bid function...")
    print(f"📧 Vendor email: {body_data['vendor_info']['email']}")
    print(f"📋 Event: {body_data['event_metadata']['name']}")
    print(f"❓ Questions: {len(body_data['questions'])}")
    print()

    try:
        # Call the lambda handler
        result = lambda_handler(event, context)

        print("✅ Function executed successfully!")
        print(f"Status Code: {result['statusCode']}")

        # Parse response body
        if 'body' in result:
            response_body = json.loads(result['body'])
            print(f"Response: {json.dumps(response_body, indent=2)}")

            if result['statusCode'] == 200:
                print("🎉 Test PASSED - Bid initiation successful!")
            else:
                print("❌ Test FAILED - Non-200 status code")

    except Exception as e:
        print(f"❌ Test FAILED with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
