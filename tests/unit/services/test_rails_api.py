"""
Unit tests for Rails API service.
"""

from unittest.mock import Mock, patch
import requests

from services.rails_api import RailsAPIService


class TestRailsAPIService:
    """Test cases for RailsAPIService."""

    @patch('services.rails_api.requests.Session')
    def test_init_success(self, mock_session_class, mock_requests_session):
        """Test successful Rails API service initialization."""
        mock_session_class.return_value = mock_requests_session

        rails_api = RailsAPIService()

        assert rails_api.base_url == 'https://api-testing.example.com'
        assert rails_api.api_key == 'test-api-key'
        assert rails_api.session == mock_requests_session

        # Verify session configuration
        mock_requests_session.headers.update.assert_called_once()
        headers = mock_requests_session.headers.update.call_args[0][0]
        assert headers['Content-Type'] == 'application/json'
        assert headers['Authorization'] == 'Bearer test-api-key'
        assert 'AIME-Planner-Chatbot' in headers['User-Agent']

    @patch('services.rails_api.requests.Session')
    def test_init_missing_env_vars(self, mock_session_class):
        """Test initialization failure with missing environment variables."""
        import os
        old_url = os.environ.pop('RAILS_API_BASE_URL', None)

        try:
            with pytest.raises(ValueError, match="Rails API base URL and key must be set"):
                RailsAPIService()
        finally:
            if old_url:
                os.environ['RAILS_API_BASE_URL'] = old_url

    @patch('services.rails_api.requests.Session')
    def test_send_conversation_update_success(self, mock_session_class, mock_requests_session):
        """Test successful conversation update sending."""
        mock_session_class.return_value = mock_requests_session

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests_session.post.return_value = mock_response

        rails_api = RailsAPIService()
        result = rails_api.send_conversation_update(
            conversation_id='test-conv-id',
            status='in_progress',
            questions_answered=[{'id': 1, 'answer': 'Yes', 'answered': True}],
            is_final=False,
            raw_email_content='Raw email content'
        )

        assert result is True
        mock_requests_session.post.assert_called_once()

        # Verify the request
        call_args = mock_requests_session.post.call_args
        assert 'conversation_updates' in call_args[0][0]

        payload = call_args[1]['json']
        assert payload['conversation_id'] == 'test-conv-id'
        assert payload['status'] == 'in_progress'
        assert payload['is_final'] is False
        assert payload['raw_email_content'] == 'Raw email content'
        assert 'timestamp' in payload

    @patch('services.rails_api.requests.Session')
    def test_send_conversation_update_api_error(self, mock_session_class, mock_requests_session):
        """Test conversation update with API error response."""
        mock_session_class.return_value = mock_requests_session

        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_requests_session.post.return_value = mock_response

        rails_api = RailsAPIService()
        result = rails_api.send_conversation_update(
            conversation_id='test-conv-id',
            status='failed',
            questions_answered=[]
        )

        assert result is False

    @patch('services.rails_api.requests.Session')
    def test_send_conversation_update_network_error(self, mock_session_class, mock_requests_session):
        """Test conversation update with network error."""
        mock_session_class.return_value = mock_requests_session

        # Mock network error
        mock_requests_session.post.side_effect = requests.exceptions.RequestException("Network error")

        rails_api = RailsAPIService()
        result = rails_api.send_conversation_update(
            conversation_id='test-conv-id',
            status='failed',
            questions_answered=[]
        )

        assert result is False

    @patch('services.rails_api.requests.Session')
    def test_get_conversation_context_success(self, mock_session_class, mock_requests_session):
        """Test successful conversation context retrieval."""
        mock_session_class.return_value = mock_requests_session

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'conversation_id': 'test-conv-id',
            'additional_context': 'Some context data'
        }
        mock_requests_session.get.return_value = mock_response

        rails_api = RailsAPIService()
        result = rails_api.get_conversation_context('test-conv-id')

        assert result is not None
        assert result['conversation_id'] == 'test-conv-id'
        assert result['additional_context'] == 'Some context data'

        # Verify the request
        mock_requests_session.get.assert_called_once()
        call_args = mock_requests_session.get.call_args
        assert 'conversations/test-conv-id' in call_args[0][0]

    @patch('services.rails_api.requests.Session')
    def test_get_conversation_context_not_found(self, mock_session_class, mock_requests_session):
        """Test conversation context retrieval when not found."""
        mock_session_class.return_value = mock_requests_session

        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_requests_session.get.return_value = mock_response

        rails_api = RailsAPIService()
        result = rails_api.get_conversation_context('nonexistent-id')

        assert result is None

    @patch('services.rails_api.requests.Session')
    def test_get_conversation_context_error(self, mock_session_class, mock_requests_session):
        """Test conversation context retrieval with error."""
        mock_session_class.return_value = mock_requests_session

        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_requests_session.get.return_value = mock_response

        rails_api = RailsAPIService()
        result = rails_api.get_conversation_context('test-conv-id')

        assert result is None

    @patch('services.rails_api.requests.Session')
    def test_notify_conversation_started_success(self, mock_session_class, mock_requests_session):
        """Test successful conversation started notification."""
        mock_session_class.return_value = mock_requests_session

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_requests_session.post.return_value = mock_response

        rails_api = RailsAPIService()
        result = rails_api.notify_conversation_started(
            conversation_id='test-conv-id',
            vendor_email='vendor@example.com',
            initial_email_sent=True
        )

        assert result is True
        mock_requests_session.post.assert_called_once()

        # Verify the request
        call_args = mock_requests_session.post.call_args
        assert 'conversations/test-conv-id/started' in call_args[0][0]

        payload = call_args[1]['json']
        assert payload['conversation_id'] == 'test-conv-id'
        assert payload['vendor_email'] == 'vendor@example.com'
        assert payload['initial_email_sent'] is True

    @patch('services.rails_api.requests.Session')
    def test_notify_conversation_completed_success(self, mock_session_class, mock_requests_session):
        """Test successful conversation completed notification."""
        mock_session_class.return_value = mock_requests_session

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests_session.post.return_value = mock_response

        rails_api = RailsAPIService()
        result = rails_api.notify_conversation_completed(
            conversation_id='test-conv-id',
            final_status='completed',
            all_answers=[{'id': 1, 'answer': 'Yes'}],
            attempt_count=2
        )

        assert result is True
        mock_requests_session.post.assert_called_once()

        # Verify the request
        call_args = mock_requests_session.post.call_args
        assert 'conversations/test-conv-id/completed' in call_args[0][0]

        payload = call_args[1]['json']
        assert payload['final_status'] == 'completed'
        assert payload['attempt_count'] == 2

    @patch('services.rails_api.requests.Session')
    def test_report_error_success(self, mock_session_class, mock_requests_session):
        """Test successful error reporting."""
        mock_session_class.return_value = mock_requests_session

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_requests_session.post.return_value = mock_response

        rails_api = RailsAPIService()
        result = rails_api.report_error(
            conversation_id='test-conv-id',
            error_type='api_error',
            error_message='Test error message',
            context={'additional': 'context'}
        )

        assert result is True
        mock_requests_session.post.assert_called_once()

        # Verify the request
        call_args = mock_requests_session.post.call_args
        assert 'errors' in call_args[0][0]

        payload = call_args[1]['json']
        assert payload['conversation_id'] == 'test-conv-id'
        assert payload['error_type'] == 'api_error'
        assert payload['error_message'] == 'Test error message'
        assert payload['context']['additional'] == 'context'

    @patch('services.rails_api.requests.Session')
    def test_validate_api_connection_success(self, mock_session_class, mock_requests_session):
        """Test successful API connection validation."""
        mock_session_class.return_value = mock_requests_session

        # Mock successful health check response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests_session.get.return_value = mock_response

        rails_api = RailsAPIService()
        result = rails_api.validate_api_connection()

        assert result is True
        mock_requests_session.get.assert_called_once()

        # Verify the request
        call_args = mock_requests_session.get.call_args
        assert 'health' in call_args[0][0]
        assert call_args[1]['timeout'] == 10

    @patch('services.rails_api.requests.Session')
    def test_validate_api_connection_failure(self, mock_session_class, mock_requests_session):
        """Test API connection validation failure."""
        mock_session_class.return_value = mock_requests_session

        # Mock failed health check response
        mock_response = Mock()
        mock_response.status_code = 503
        mock_requests_session.get.return_value = mock_response

        rails_api = RailsAPIService()
        result = rails_api.validate_api_connection()

        assert result is False

    @patch('services.rails_api.requests.Session')
    def test_validate_api_connection_timeout(self, mock_session_class, mock_requests_session):
        """Test API connection validation with timeout."""
        mock_session_class.return_value = mock_requests_session

        # Mock timeout
        mock_requests_session.get.side_effect = requests.exceptions.Timeout("Timeout")

        rails_api = RailsAPIService()
        result = rails_api.validate_api_connection()

        assert result is False

    def test_get_current_timestamp(self):
        """Test current timestamp generation."""
        rails_api = RailsAPIService.__new__(RailsAPIService)  # Create without __init__

        timestamp = rails_api._get_current_timestamp()

        assert isinstance(timestamp, str)
        assert timestamp.endswith('Z')
        assert 'T' in timestamp  # ISO format

        # Verify it's a valid datetime format
                parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed, datetime)

    def test_format_questions_for_rails_with_objects(self, sample_questions):
        """Test formatting Question objects for Rails API."""
        rails_api = RailsAPIService.__new__(RailsAPIService)  # Create without __init__

        # Update one question with an answer
        sample_questions[0].answer = "Yes, available"
        sample_questions[0].answered = True

        formatted = rails_api.format_questions_for_rails(sample_questions)

        assert len(formatted) == len(sample_questions)

        # Check first question (answered)
        assert formatted[0]['id'] == 1
        assert formatted[0]['text'] == "Do you have availability for our dates?"
        assert formatted[0]['answer'] == "Yes, available"
        assert formatted[0]['answered'] is True
        assert formatted[0]['required'] is True

        # Check second question (not answered)
        assert formatted[1]['id'] == 2
        assert formatted[1]['answered'] is False
        assert formatted[1]['required'] is True

    def test_format_questions_for_rails_with_dicts(self):
        """Test formatting question dictionaries for Rails API."""
        rails_api = RailsAPIService.__new__(RailsAPIService)  # Create without __init__

        question_dicts = [
            {
                'id': 1,
                'text': 'Test question?',
                'answer': 'Test answer',
                'answered': True,
                'required': False
            },
            {
                'id': 2,
                'text': 'Another question?',
                'required': True
            }
        ]

        formatted = rails_api.format_questions_for_rails(question_dicts)

        assert len(formatted) == 2
        assert formatted[0]['id'] == 1
        assert formatted[0]['answer'] == 'Test answer'
        assert formatted[0]['answered'] is True
        assert formatted[1]['answered'] is False  # Default value

    @patch('services.rails_api.requests.Session')
    def test_retry_configuration(self, mock_session_class, mock_requests_session):
        """Test that retry strategy is properly configured."""
        mock_session_class.return_value = mock_requests_session

        rails_api = RailsAPIService()

        # Verify session mount calls were made for retry configuration
        assert mock_requests_session.mount.call_count == 2

        # Verify mount calls
        calls = mock_requests_session.mount.call_args_list
        assert calls[0][0][0] == "http://"
        assert calls[1][0][0] == "https://"

    @patch('services.rails_api.requests.Session')
    def test_request_timeout_configuration(self, mock_session_class, mock_requests_session):
        """Test that requests include proper timeout values."""
        mock_session_class.return_value = mock_requests_session

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_requests_session.post.return_value = mock_response
        mock_requests_session.get.return_value = mock_response

        rails_api = RailsAPIService()

        # Test various methods to ensure timeout is set
        rails_api.send_conversation_update('test', 'status', [])
        rails_api.get_conversation_context('test')
        rails_api.validate_api_connection()

        # Verify timeout was included in calls
        for call in mock_requests_session.post.call_args_list:
            assert call[1]['timeout'] == 30

        for call in mock_requests_session.get.call_args_list:
            if 'health' in call[0][0]:
                assert call[1]['timeout'] == 10  # Health check has shorter timeout
            else:
                assert call[1]['timeout'] == 30
