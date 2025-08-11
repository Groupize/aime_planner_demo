"""
Unit tests for process_email Lambda handler.
"""

import json
from unittest.mock import Mock, patch

from handlers.process_email import lambda_handler, process_single_email_record
from models.conversation import ConversationStatus, send_follow_up_email


class TestProcessEmailHandler:
    """Test cases for process_email Lambda handler."""

    @patch('handlers.process_email.RailsAPIService')
    @patch('handlers.process_email.LLMService')
    @patch('handlers.process_email.EmailService')
    @patch('handlers.process_email.DatabaseService')
    def test_lambda_handler_success(self, mock_db_service, mock_email_service,
                                   mock_llm_service, mock_rails_api,
                                   sample_sns_email_event, sample_lambda_context):
        """Test successful email processing."""
        # Setup mocks
        mock_db = Mock()
        mock_conversation = Mock()
        mock_conversation.status = ConversationStatus.IN_PROGRESS
        mock_conversation.conversation_id = 'test-conversation-id'
        mock_conversation.attempt_count = 1
        mock_conversation.max_attempts = 4
        mock_conversation.questions = []
        mock_conversation.get_unanswered_required_questions.return_value = []
        mock_conversation.get_answered_questions.return_value = []
        mock_conversation.add_email_exchange = Mock()
        mock_conversation.update_question_answer.return_value = True

        mock_db.get_conversation.return_value = mock_conversation
        mock_db.update_conversation.return_value = True
        mock_db_service.return_value = mock_db

        mock_email = Mock()
        mock_email.parse_inbound_email.return_value = {
            'conversation_id': 'test-conversation-id',
            'from_email': 'vendor@example.com',
            'subject': 'Re: Test Subject',
            'body': 'Test response from vendor'
        }
        mock_email_service.return_value = mock_email

        mock_llm = Mock()
        mock_llm.parse_vendor_response.return_value = [(1, 'Yes, available')]
        mock_llm_service.return_value = mock_llm

        mock_rails = Mock()
        mock_rails.send_conversation_update.return_value = True
        mock_rails.notify_conversation_completed.return_value = True
        mock_rails.format_questions_for_rails.return_value = []
        mock_rails_api.return_value = mock_rails

        # Execute handler
        response = lambda_handler(sample_sns_email_event, sample_lambda_context)

        # Verify response
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['message'] == 'Email processing completed'
        assert len(response_body['results']) == 1
        assert response_body['results'][0]['status'] == 'success'

        # Verify service calls
        mock_email.parse_inbound_email.assert_called_once()
        mock_db.get_conversation.assert_called_once()
        mock_llm.parse_vendor_response.assert_called_once()

    def test_lambda_handler_no_records(self, sample_lambda_context):
        """Test handler with no SNS records."""
        event = {'Records': []}

        response = lambda_handler(event, sample_lambda_context)

        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['message'] == 'No records to process'

    def test_lambda_handler_missing_records(self, sample_lambda_context):
        """Test handler with missing Records key."""
        event = {}

        response = lambda_handler(event, sample_lambda_context)

        assert response['statusCode'] == 200

    @patch('handlers.process_email.process_single_email_record')
    def test_lambda_handler_with_exception(self, mock_process_record, sample_sns_email_event, sample_lambda_context):
        """Test handler with exception in processing."""
        mock_process_record.side_effect = Exception("Processing error")

        response = lambda_handler(sample_sns_email_event, sample_lambda_context)

        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert len(response_body['results']) == 1
        assert response_body['results'][0]['status'] == 'error'

    @patch('handlers.process_email.RailsAPIService')
    @patch('handlers.process_email.LLMService')
    @patch('handlers.process_email.EmailService')
    @patch('handlers.process_email.DatabaseService')
    def test_process_single_email_record_success(self, mock_db_service, mock_email_service,
                                                 mock_llm_service, mock_rails_api):
        """Test successful single email record processing."""
        # Setup mocks
        mock_db = Mock()
        mock_conversation = Mock()
        mock_conversation.status = ConversationStatus.IN_PROGRESS
        mock_conversation.conversation_id = 'test-conversation-id'
        mock_conversation.attempt_count = 1
        mock_conversation.max_attempts = 4
        mock_conversation.questions = []
        mock_conversation.get_unanswered_required_questions.return_value = []
        mock_conversation.get_answered_questions.return_value = []
        mock_conversation.add_email_exchange = Mock()
        mock_conversation.update_question_answer.return_value = True

        mock_db.get_conversation.return_value = mock_conversation
        mock_db.update_conversation.return_value = True
        mock_db_service.return_value = mock_db

        mock_email = Mock()
        mock_email.parse_inbound_email.return_value = {
            'conversation_id': 'test-conversation-id',
            'from_email': 'vendor@example.com',
            'subject': 'Re: Test Subject',
            'body': 'Test response from vendor'
        }
        mock_email_service.return_value = mock_email

        mock_llm = Mock()
        mock_llm.parse_vendor_response.return_value = [(1, 'Yes, available')]
        mock_llm_service.return_value = mock_llm

        mock_rails = Mock()
        mock_rails.send_conversation_update.return_value = True
        mock_rails.format_questions_for_rails.return_value = []
        mock_rails_api.return_value = mock_rails

        # Test record
        record = {
            'Sns': {
                'Message': json.dumps({
                    'mail': {
                        'commonHeaders': {
                            'to': ['aime-testing+test-conversation-id@groupize.com'],
                            'from': ['vendor@example.com'],
                            'subject': 'Re: Test Subject'
                        },
                        'timestamp': '2024-01-01T12:00:00.000Z',
                        'messageId': 'test-message-id'
                    },
                    'content': 'Test response from vendor'
                })
            }
        }

        result = process_single_email_record(record)

        assert result['status'] == 'success'
        assert result['conversation_id'] == 'test-conversation-id'
        assert result['questions_answered'] == 1

    @patch('handlers.process_email.EmailService')
    def test_process_single_email_record_parse_failure(self, mock_email_service):
        """Test email record processing with parse failure."""
        mock_email = Mock()
        mock_email.parse_inbound_email.return_value = None
        mock_email_service.return_value = mock_email

        record = {'Sns': {'Message': 'invalid'}}

        result = process_single_email_record(record)

        assert result['status'] == 'error'
        assert 'Failed to parse email data' in result['error']

    @patch('handlers.process_email.EmailService')
    @patch('handlers.process_email.DatabaseService')
    def test_process_single_email_record_conversation_not_found(self, mock_db_service, mock_email_service):
        """Test email processing when conversation not found."""
        mock_email = Mock()
        mock_email.parse_inbound_email.return_value = {
            'conversation_id': 'nonexistent-id',
            'body': 'Test'
        }
        mock_email_service.return_value = mock_email

        mock_db = Mock()
        mock_db.get_conversation.return_value = None
        mock_db_service.return_value = mock_db

        record = {'Sns': {}}

        result = process_single_email_record(record)

        assert result['status'] == 'error'
        assert 'not found' in result['error']

    @patch('handlers.process_email.RailsAPIService')
    @patch('handlers.process_email.LLMService')
    @patch('handlers.process_email.EmailService')
    @patch('handlers.process_email.DatabaseService')
    def test_process_single_email_record_completed_conversation(self, mock_db_service, mock_email_service,
                                                               mock_llm_service, mock_rails_api):
        """Test processing email for already completed conversation."""
        mock_email = Mock()
        mock_email.parse_inbound_email.return_value = {
            'conversation_id': 'test-conversation-id',
            'body': 'Test'
        }
        mock_email_service.return_value = mock_email

        mock_conversation = Mock()
        mock_conversation.status = ConversationStatus.COMPLETED
        mock_conversation.conversation_id = 'test-conversation-id'

        mock_db = Mock()
        mock_db.get_conversation.return_value = mock_conversation
        mock_db_service.return_value = mock_db

        record = {'Sns': {}}

        result = process_single_email_record(record)

        assert result['status'] == 'ignored'
        assert 'already' in result['reason'] and 'completed' in result['reason']

    @patch('handlers.process_email.RailsAPIService')
    @patch('handlers.process_email.LLMService')
    @patch('handlers.process_email.EmailService')
    @patch('handlers.process_email.DatabaseService')
    @patch('handlers.process_email.send_follow_up_email')
    def test_process_single_email_record_with_follow_up(self, mock_send_follow_up, mock_db_service,
                                                       mock_email_service, mock_llm_service, mock_rails_api):
        """Test email processing that triggers follow-up."""
        # Setup mocks
        mock_db = Mock()
        mock_conversation = Mock()
        mock_conversation.status = ConversationStatus.IN_PROGRESS
        mock_conversation.conversation_id = 'test-conversation-id'
        mock_conversation.attempt_count = 1
        mock_conversation.max_attempts = 4
        mock_conversation.add_email_exchange = Mock()
        mock_conversation.update_question_answer.return_value = True

        # Mock unanswered required questions to trigger follow-up
        mock_unanswered_question = Mock()
        mock_unanswered_question.required = True
        mock_conversation.get_unanswered_required_questions.return_value = [mock_unanswered_question]
        mock_conversation.get_answered_questions.return_value = []

        mock_db.get_conversation.return_value = mock_conversation
        mock_db.update_conversation.return_value = True
        mock_db_service.return_value = mock_db

        mock_email = Mock()
        mock_email.parse_inbound_email.return_value = {
            'conversation_id': 'test-conversation-id',
            'body': 'Partial response'
        }
        mock_email_service.return_value = mock_email

        mock_llm = Mock()
        mock_llm.parse_vendor_response.return_value = [(1, 'Partial answer')]
        mock_llm_service.return_value = mock_llm

        mock_rails = Mock()
        mock_rails.send_conversation_update.return_value = True
        mock_rails.format_questions_for_rails.return_value = []
        mock_rails_api.return_value = mock_rails

        # Mock successful follow-up
        mock_send_follow_up.return_value = True

        record = {'Sns': {}}

        result = process_single_email_record(record)

        assert result['status'] == 'success'
        assert result['follow_up_sent'] is True
        assert mock_conversation.attempt_count == 2  # Should be incremented
        mock_send_follow_up.assert_called_once()

    @patch('handlers.process_email.RailsAPIService')
    @patch('handlers.process_email.LLMService')
    @patch('handlers.process_email.EmailService')
    @patch('handlers.process_email.DatabaseService')
    def test_process_single_email_record_max_attempts_reached(self, mock_db_service, mock_email_service,
                                                             mock_llm_service, mock_rails_api):
        """Test email processing when max attempts are reached."""
        mock_db = Mock()
        mock_conversation = Mock()
        mock_conversation.status = ConversationStatus.IN_PROGRESS
        mock_conversation.conversation_id = 'test-conversation-id'
        mock_conversation.attempt_count = 4  # Max attempts reached
        mock_conversation.max_attempts = 4
        mock_conversation.add_email_exchange = Mock()
        mock_conversation.update_question_answer.return_value = True

        # Still have unanswered questions but max attempts reached
        mock_unanswered_question = Mock()
        mock_unanswered_question.required = True
        mock_conversation.get_unanswered_required_questions.return_value = [mock_unanswered_question]
        mock_conversation.get_answered_questions.return_value = []

        mock_db.get_conversation.return_value = mock_conversation
        mock_db.update_conversation.return_value = True
        mock_db_service.return_value = mock_db

        mock_email = Mock()
        mock_email.parse_inbound_email.return_value = {
            'conversation_id': 'test-conversation-id',
            'body': 'Final response'
        }
        mock_email_service.return_value = mock_email

        mock_llm = Mock()
        mock_llm.parse_vendor_response.return_value = []
        mock_llm_service.return_value = mock_llm

        mock_rails = Mock()
        mock_rails.send_conversation_update.return_value = True
        mock_rails.notify_conversation_completed.return_value = True
        mock_rails.format_questions_for_rails.return_value = []
        mock_rails_api.return_value = mock_rails

        record = {'Sns': {}}

        result = process_single_email_record(record)

        assert result['status'] == 'success'
        assert result['conversation_status'] == 'completed'
        assert result['follow_up_sent'] is False
        mock_rails.notify_conversation_completed.assert_called_once()

    @patch('handlers.process_email.LLMService')
    @patch('handlers.process_email.EmailService')
    def test_send_follow_up_email_success(self, mock_email_service, mock_llm_service, sample_conversation):
        """Test successful follow-up email sending."""
        mock_llm = Mock()
        mock_llm.generate_follow_up_email.return_value = ("Follow-up Subject", "Follow-up Body")
        mock_llm_service.return_value = mock_llm

        mock_email = Mock()
        mock_email.send_vendor_email.return_value = True
        mock_email_service.return_value = mock_email

        unanswered_questions = [q for q in sample_conversation.questions if q.required and not q.answered]

        result = send_follow_up_email(sample_conversation, unanswered_questions, mock_llm, mock_email)

        assert result is True
        mock_llm.generate_follow_up_email.assert_called_once()
        mock_email.send_vendor_email.assert_called_once()

        # Verify email was recorded
        assert len(sample_conversation.email_exchanges) > 0

    @patch('handlers.process_email.LLMService')
    @patch('handlers.process_email.EmailService')
    def test_send_follow_up_email_send_failure(self, mock_email_service, mock_llm_service, sample_conversation):
        """Test follow-up email sending failure."""
        mock_llm = Mock()
        mock_llm.generate_follow_up_email.return_value = ("Follow-up Subject", "Follow-up Body")
        mock_llm_service.return_value = mock_llm

        mock_email = Mock()
        mock_email.send_vendor_email.return_value = False  # Send fails
        mock_email_service.return_value = mock_email

        unanswered_questions = [q for q in sample_conversation.questions if q.required and not q.answered]

        result = send_follow_up_email(sample_conversation, unanswered_questions, mock_llm, mock_email)

        assert result is False

    @patch('handlers.process_email.LLMService')
    @patch('handlers.process_email.EmailService')
    def test_send_follow_up_email_exception(self, mock_email_service, mock_llm_service, sample_conversation):
        """Test follow-up email with exception."""
        mock_llm = Mock()
        mock_llm.generate_follow_up_email.side_effect = Exception("LLM Error")
        mock_llm_service.return_value = mock_llm

        unanswered_questions = [q for q in sample_conversation.questions if q.required and not q.answered]

        result = send_follow_up_email(sample_conversation, unanswered_questions, mock_llm, None)

        assert result is False

    @patch('handlers.process_email.RailsAPIService')
    @patch('handlers.process_email.LLMService')
    @patch('handlers.process_email.EmailService')
    @patch('handlers.process_email.DatabaseService')
    def test_process_single_email_record_exception_handling(self, mock_db_service, mock_email_service,
                                                           mock_llm_service, mock_rails_api):
        """Test exception handling in email processing."""
        mock_email = Mock()
        mock_email.parse_inbound_email.return_value = {
            'conversation_id': 'test-conversation-id',
            'body': 'Test'
        }
        mock_email_service.return_value = mock_email

        mock_conversation = Mock()
        mock_conversation.conversation_id = 'test-conversation-id'
        mock_conversation.status = ConversationStatus.IN_PROGRESS

        mock_db = Mock()
        mock_db.get_conversation.return_value = mock_conversation
        mock_db.update_conversation.return_value = True
        mock_db_service.return_value = mock_db

        # Mock LLM to raise exception
        mock_llm = Mock()
        mock_llm.parse_vendor_response.side_effect = Exception("LLM Error")
        mock_llm_service.return_value = mock_llm

        mock_rails = Mock()
        mock_rails.report_error.return_value = True
        mock_rails_api.return_value = mock_rails

        record = {'Sns': {}}

        result = process_single_email_record(record)

        assert result['status'] == 'error'
        assert 'LLM Error' in result['error']

        # Verify conversation was marked as failed
        assert mock_conversation.status == ConversationStatus.FAILED
        mock_rails.report_error.assert_called_once()
