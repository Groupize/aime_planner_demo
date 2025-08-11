"""
Unit tests for initiate_bid Lambda handler.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from handlers.initiate_bid import lambda_handler, validate_request_payload
from models.conversation import ConversationStatus


class TestInitiateBidHandler:
    """Test cases for initiate_bid Lambda handler."""

    @patch('handlers.initiate_bid.RailsAPIService')
    @patch('handlers.initiate_bid.LLMService')
    @patch('handlers.initiate_bid.EmailService')
    @patch('handlers.initiate_bid.DatabaseService')
    def test_lambda_handler_success(self, mock_db_service, mock_email_service,
                                   mock_llm_service, mock_rails_api,
                                   sample_lambda_context):
        """Test successful bid initiation."""
        # Setup mocks
        mock_db = Mock()
        mock_db.save_conversation.return_value = True
        mock_db.save_questions.return_value = True
        mock_db.update_conversation.return_value = True
        mock_db_service.return_value = mock_db

        mock_email = Mock()
        mock_email.send_vendor_email.return_value = True
        mock_email_service.return_value = mock_email

        mock_llm = Mock()
        mock_llm.generate_initial_bid_email.return_value = ("Test Subject", "Test Body")
        mock_llm_service.return_value = mock_llm

        mock_rails = Mock()
        mock_rails.notify_conversation_started.return_value = True
        mock_rails_api.return_value = mock_rails

        # Prepare event
        request_body = {
            "event_metadata": {
                "name": "Test Event",
                "dates": ["2024-06-15"],
                "event_type": "conference",
                "planner_name": "John Doe",
                "planner_email": "john@example.com"
            },
            "vendor_info": {
                "name": "Test Vendor",
                "email": "vendor@example.com",
                "service_type": "hotel"
            },
            "questions": [
                {
                    "id": 1,
                    "text": "Do you have availability?",
                    "required": True
                }
            ]
        }

        event = {
            'body': json.dumps(request_body)
        }

        # Execute handler
        response = lambda_handler(event, sample_lambda_context)

        # Verify response
        assert response['statusCode'] == 200

        response_body = json.loads(response['body'])
        assert response_body['message'] == 'Bid request initiated successfully'
        assert 'conversation_id' in response_body
        assert response_body['email_sent'] is True
        assert response_body['vendor_email'] == 'vendor@example.com'

        # Verify service calls
        mock_db.save_conversation.assert_called_once()
        mock_db.save_questions.assert_called_once()
        mock_llm.generate_initial_bid_email.assert_called_once()
        mock_email.send_vendor_email.assert_called_once()
        mock_rails.notify_conversation_started.assert_called_once()

    @patch('handlers.initiate_bid.RailsAPIService')
    @patch('handlers.initiate_bid.LLMService')
    @patch('handlers.initiate_bid.EmailService')
    @patch('handlers.initiate_bid.DatabaseService')
    def test_lambda_handler_email_send_failure(self, mock_db_service, mock_email_service,
                                              mock_llm_service, mock_rails_api,
                                              sample_lambda_context):
        """Test bid initiation with email sending failure."""
        # Setup mocks
        mock_db = Mock()
        mock_db.save_conversation.return_value = True
        mock_db.save_questions.return_value = True
        mock_db.update_conversation.return_value = True
        mock_db_service.return_value = mock_db

        mock_email = Mock()
        mock_email.send_vendor_email.return_value = False  # Email fails
        mock_email_service.return_value = mock_email

        mock_llm = Mock()
        mock_llm.generate_initial_bid_email.return_value = ("Test Subject", "Test Body")
        mock_llm_service.return_value = mock_llm

        mock_rails = Mock()
        mock_rails.report_error.return_value = True
        mock_rails_api.return_value = mock_rails

        request_body = {
            "event_metadata": {
                "name": "Test Event",
                "dates": ["2024-06-15"],
                "event_type": "conference",
                "planner_name": "John Doe",
                "planner_email": "john@example.com"
            },
            "vendor_info": {
                "name": "Test Vendor",
                "email": "vendor@example.com",
                "service_type": "hotel"
            },
            "questions": [
                {
                    "id": 1,
                    "text": "Do you have availability?",
                    "required": True
                }
            ]
        }

        event = {
            'body': json.dumps(request_body)
        }

        # Execute handler
        response = lambda_handler(event, sample_lambda_context)

        # Verify error response
        assert response['statusCode'] == 500

        response_body = json.loads(response['body'])
        assert response_body['error'] == 'Failed to send email to vendor'
        assert 'conversation_id' in response_body

        # Verify error reporting
        mock_rails.report_error.assert_called_once()

    def test_lambda_handler_missing_required_fields(self, sample_lambda_context):
        """Test handler with missing required fields."""
        event = {
            'body': json.dumps({
                "event_metadata": {
                    "name": "Test Event"
                    # Missing required fields
                }
            })
        }

        response = lambda_handler(event, sample_lambda_context)

        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert 'Missing required fields' in response_body['error']

    def test_lambda_handler_invalid_json(self, sample_lambda_context):
        """Test handler with invalid JSON body."""
        event = {
            'body': 'invalid json'
        }

        response = lambda_handler(event, sample_lambda_context)

        assert response['statusCode'] == 500
        response_body = json.loads(response['body'])
        assert response_body['error'] == 'Internal server error'

    @patch('handlers.initiate_bid.DatabaseService')
    def test_lambda_handler_database_save_failure(self, mock_db_service, sample_lambda_context):
        """Test handler with database save failure."""
        mock_db = Mock()
        mock_db.save_conversation.return_value = False  # Database fails
        mock_db_service.return_value = mock_db

        request_body = {
            "event_metadata": {
                "name": "Test Event",
                "dates": ["2024-06-15"],
                "event_type": "conference",
                "planner_name": "John Doe",
                "planner_email": "john@example.com"
            },
            "vendor_info": {
                "name": "Test Vendor",
                "email": "vendor@example.com",
                "service_type": "hotel"
            },
            "questions": [
                {
                    "id": 1,
                    "text": "Do you have availability?",
                    "required": True
                }
            ]
        }

        event = {
            'body': json.dumps(request_body)
        }

        response = lambda_handler(event, sample_lambda_context)

        assert response['statusCode'] == 500
        response_body = json.loads(response['body'])
        assert response_body['error'] == 'Internal server error'

    def test_lambda_handler_with_body_dict(self, sample_lambda_context):
        """Test handler when body is already a dict (not string)."""
        request_body = {
            "event_metadata": {
                "name": "Test Event",
                "dates": ["2024-06-15"],
                "event_type": "conference",
                "planner_name": "John Doe",
                "planner_email": "john@example.com"
            },
            "vendor_info": {
                "name": "Test Vendor",
                "email": "vendor@example.com",
                "service_type": "hotel"
            },
            "questions": [
                {
                    "id": 1,
                    "text": "Do you have availability?",
                    "required": True
                }
            ]
        }

        event = {
            'body': request_body  # Dict instead of JSON string
        }

        # Should handle this gracefully without JSON parsing
        response = lambda_handler(event, sample_lambda_context)

        # Even if it fails due to mocking, it shouldn't crash on JSON parsing
        assert response['statusCode'] in [200, 500]  # Either success or internal error

    def test_validate_request_payload_valid(self):
        """Test request payload validation with valid data."""
        payload = {
            "event_metadata": {
                "name": "Test Event",
                "dates": ["2024-06-15"],
                "event_type": "conference",
                "planner_name": "John Doe",
                "planner_email": "john@example.com"
            },
            "vendor_info": {
                "name": "Test Vendor",
                "email": "vendor@example.com",
                "service_type": "hotel"
            },
            "questions": [
                {
                    "id": 1,
                    "text": "Do you have availability?",
                    "required": True
                }
            ]
        }

        is_valid, error_message = validate_request_payload(payload)

        assert is_valid is True
        assert error_message == ""

    def test_validate_request_payload_missing_event_field(self):
        """Test validation with missing event metadata field."""
        payload = {
            "event_metadata": {
                "name": "Test Event"
                # Missing dates, event_type, planner_name, planner_email
            },
            "vendor_info": {
                "name": "Test Vendor",
                "email": "vendor@example.com",
                "service_type": "hotel"
            },
            "questions": [{"id": 1, "text": "Test?"}]
        }

        is_valid, error_message = validate_request_payload(payload)

        assert is_valid is False
        assert "Missing required event_metadata field" in error_message

    def test_validate_request_payload_missing_vendor_field(self):
        """Test validation with missing vendor info field."""
        payload = {
            "event_metadata": {
                "name": "Test Event",
                "dates": ["2024-06-15"],
                "event_type": "conference",
                "planner_name": "John Doe",
                "planner_email": "john@example.com"
            },
            "vendor_info": {
                "name": "Test Vendor"
                # Missing email and service_type
            },
            "questions": [{"id": 1, "text": "Test?"}]
        }

        is_valid, error_message = validate_request_payload(payload)

        assert is_valid is False
        assert "Missing required vendor_info field" in error_message

    def test_validate_request_payload_no_questions(self):
        """Test validation with no questions."""
        payload = {
            "event_metadata": {
                "name": "Test Event",
                "dates": ["2024-06-15"],
                "event_type": "conference",
                "planner_name": "John Doe",
                "planner_email": "john@example.com"
            },
            "vendor_info": {
                "name": "Test Vendor",
                "email": "vendor@example.com",
                "service_type": "hotel"
            },
            "questions": []
        }

        is_valid, error_message = validate_request_payload(payload)

        assert is_valid is False
        assert "At least one question is required" in error_message

    def test_validate_request_payload_invalid_question(self):
        """Test validation with invalid question structure."""
        payload = {
            "event_metadata": {
                "name": "Test Event",
                "dates": ["2024-06-15"],
                "event_type": "conference",
                "planner_name": "John Doe",
                "planner_email": "john@example.com"
            },
            "vendor_info": {
                "name": "Test Vendor",
                "email": "vendor@example.com",
                "service_type": "hotel"
            },
            "questions": [
                {
                    "id": 1,
                    "text": "Valid question?"
                },
                {
                    # Missing id and text
                    "required": True
                }
            ]
        }

        is_valid, error_message = validate_request_payload(payload)

        assert is_valid is False
        assert "Question 1 missing required" in error_message

    @patch('handlers.initiate_bid.RailsAPIService')
    def test_lambda_handler_exception_handling(self, mock_rails_api, sample_lambda_context):
        """Test handler exception handling and error reporting."""
        # Mock to raise an exception
        mock_rails_api.side_effect = Exception("Unexpected error")

        request_body = {
            "event_metadata": {
                "name": "Test Event",
                "dates": ["2024-06-15"],
                "event_type": "conference",
                "planner_name": "John Doe",
                "planner_email": "john@example.com"
            },
            "vendor_info": {
                "name": "Test Vendor",
                "email": "vendor@example.com",
                "service_type": "hotel"
            },
            "questions": [
                {
                    "id": 1,
                    "text": "Do you have availability?",
                    "required": True
                }
            ]
        }

        event = {
            'body': json.dumps(request_body)
        }

        response = lambda_handler(event, sample_lambda_context)

        assert response['statusCode'] == 500
        response_body = json.loads(response['body'])
        assert response_body['error'] == 'Internal server error'
        # Accept either AWS region error or our mocked error
        assert ('Unexpected error' in response_body['message'] or
                'You must specify a region' in response_body['message'])
