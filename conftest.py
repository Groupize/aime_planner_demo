"""
Pytest configuration and shared fixtures for AIME Planner tests.
"""

import os
import sys
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up test environment variables
os.environ['ENVIRONMENT'] = 'testing'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'fake-access-key'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'fake-secret-key'
os.environ['RAILS_API_BASE_URL'] = 'https://api-testing.example.com'
os.environ['RAILS_API_KEY'] = 'test-api-key'
os.environ['OPENAI_API_KEY'] = 'test-openai-key'
os.environ['SENDGRID_API_KEY'] = 'test-sendgrid-key'
os.environ['CONVERSATION_TABLE_NAME'] = 'test-conversations'
os.environ['QUESTIONS_TABLE_NAME'] = 'test-questions'

from models.conversation import (
    Conversation, Question, EventMetadata, VendorInfo,
    ConversationStatus, EmailExchange
)


@pytest.fixture
def sample_event_metadata():
    """Sample event metadata for testing."""
    return EventMetadata(
        name="Annual Company Retreat 2024",
        dates=["2024-06-15", "2024-06-16"],
        event_type="corporate retreat",
        planner_name="Sarah Johnson",
        planner_email="sarah.johnson@techcorp.com",
        planner_phone="+1-555-123-4567"
    )


@pytest.fixture
def sample_vendor_info():
    """Sample vendor info for testing."""
    return VendorInfo(
        name="Mountain View Resort",
        email="sales@mountainviewresort.com",
        service_type="hotel"
    )


@pytest.fixture
def sample_questions():
    """Sample questions for testing."""
    return [
        Question(
            id=1,
            text="Do you have availability for our dates?",
            required=True
        ),
        Question(
            id=2,
            text="What is your rate per room per night?",
            required=True,
            options=["Standard Room", "Deluxe Room", "Suite"]
        ),
        Question(
            id=3,
            text="Do you offer shuttle service?",
            required=False
        )
    ]


@pytest.fixture
def sample_conversation(sample_event_metadata, sample_vendor_info, sample_questions):
    """Sample conversation for testing."""
    return Conversation(
        event_metadata=sample_event_metadata,
        vendor_info=sample_vendor_info,
        questions=sample_questions
    )


@pytest.fixture
def answered_conversation(sample_conversation):
    """Sample conversation with some answered questions."""
    conv = sample_conversation.model_copy(deep=True)
    conv.update_question_answer(1, "Yes, we have availability")
    conv.update_question_answer(3, "No shuttle service available")
    return conv


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table for testing."""
    table = Mock()
    table.put_item = Mock(return_value=True)
    table.get_item = Mock(return_value={'Item': {}})
    table.update_item = Mock(return_value=True)
    table.delete_item = Mock(return_value=True)
    table.scan = Mock(return_value={'Items': []})
    table.query = Mock(return_value={'Items': []})
    table.batch_writer = Mock()
    return table


@pytest.fixture
def mock_dynamodb_resource(mock_dynamodb_table):
    """Mock DynamoDB resource for testing."""
    resource = Mock()
    resource.Table = Mock(return_value=mock_dynamodb_table)
    return resource


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = Mock()

    # Mock chat completion response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = '{"subject": "Test Subject", "body": "Test Body"}'

    client.chat.completions.create = Mock(return_value=mock_response)
    return client


@pytest.fixture
def mock_sendgrid_client():
    """Mock SendGrid client for testing."""
    client = Mock()

    # Mock successful send response
    mock_response = Mock()
    mock_response.status_code = 202
    mock_response.body = ""
    mock_response.headers = {}

    client.send = Mock(return_value=mock_response)
    return client


@pytest.fixture
def mock_requests_session():
    """Mock requests session for testing."""
    session = Mock()

    # Mock successful API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = Mock(return_value={"status": "success"})
    mock_response.text = "Success"

    session.post = Mock(return_value=mock_response)
    session.get = Mock(return_value=mock_response)
    session.put = Mock(return_value=mock_response)

    return session


@pytest.fixture
def sample_sns_email_event():
    """Sample SNS email event for testing."""
    return {
        "Records": [
            {
                "Sns": {
                    "Message": '{"mail": {"commonHeaders": {"to": ["aime-testing+test-conversation-id@groupize.com"], "from": ["vendor@example.com"], "subject": "Re: Test Subject"}, "timestamp": "2024-01-01T12:00:00.000Z", "messageId": "test-message-id"}, "content": "This is a test email response from vendor."}'
                }
            }
        ]
    }


@pytest.fixture
def sample_lambda_context():
    """Sample Lambda context for testing."""
    context = Mock()
    context.function_name = "test-function"
    context.function_version = "1"
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
    context.memory_limit_in_mb = 512
    context.remaining_time_in_millis = Mock(return_value=30000)
    context.aws_request_id = "test-request-id"
    return context


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean up environment after each test."""
    yield
    # Reset any global state if needed
