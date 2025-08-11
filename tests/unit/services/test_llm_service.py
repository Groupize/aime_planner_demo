"""
Unit tests for LLM service.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from services.llm_service import LLMService
from models.conversation import Question


class TestLLMService:
    """Test cases for LLMService."""

    @patch('services.llm_service.OpenAI')
    def test_init_success(self, mock_openai_class, mock_openai_client):
        """Test successful LLM service initialization."""
        mock_openai_class.return_value = mock_openai_client

        llm_service = LLMService()

        assert llm_service.client == mock_openai_client
        assert llm_service.model == "gpt-4-turbo-preview"
        mock_openai_class.assert_called_once_with(api_key='test-openai-key')

    @patch('services.llm_service.OpenAI')
    def test_init_missing_api_key(self, mock_openai_class):
        """Test initialization failure with missing API key."""
        import os
        old_key = os.environ.pop('OPENAI_API_KEY', None)

        try:
            with pytest.raises(ValueError, match="OpenAI API key must be set"):
                LLMService()
        finally:
            if old_key:
                os.environ['OPENAI_API_KEY'] = old_key

    @patch('services.llm_service.OpenAI')
    def test_generate_initial_bid_email_success(self, mock_openai_class, mock_openai_client, sample_conversation):
        """Test successful initial bid email generation."""
        mock_openai_class.return_value = mock_openai_client

        # Mock successful OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "subject": "Pricing Inquiry for Annual Company Retreat 2024",
            "body": "Hi Mountain View Resort,\n\nI hope this email finds you well..."
        })

        mock_openai_client.chat.completions.create.return_value = mock_response

        llm_service = LLMService()
        subject, body = llm_service.generate_initial_bid_email(sample_conversation)

        assert subject == "Pricing Inquiry for Annual Company Retreat 2024"
        assert "Hi Mountain View Resort" in body

        # Verify OpenAI was called with correct parameters
        mock_openai_client.chat.completions.create.assert_called_once()
        call_args = mock_openai_client.chat.completions.create.call_args

        assert call_args[1]['model'] == "gpt-4-turbo-preview"
        assert call_args[1]['temperature'] == 0.7
        assert call_args[1]['max_tokens'] == 1500
        assert len(call_args[1]['messages']) == 2
        assert call_args[1]['messages'][0]['role'] == 'system'
        assert call_args[1]['messages'][1]['role'] == 'user'

    @patch('services.llm_service.OpenAI')
    def test_generate_initial_bid_email_api_error(self, mock_openai_class, mock_openai_client, sample_conversation):
        """Test initial bid email generation with API error."""
        mock_openai_class.return_value = mock_openai_client

        # Mock OpenAI API error
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        llm_service = LLMService()
        subject, body = llm_service.generate_initial_bid_email(sample_conversation)

        # Should fall back to template
        assert "Pricing Inquiry" in subject
        assert sample_conversation.event_metadata.name in subject
        assert sample_conversation.vendor_info.name in body
        assert sample_conversation.event_metadata.planner_name in body

    @patch('services.llm_service.OpenAI')
    def test_generate_initial_bid_email_invalid_json(self, mock_openai_class, mock_openai_client, sample_conversation):
        """Test initial bid email generation with invalid JSON response."""
        mock_openai_class.return_value = mock_openai_client

        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Invalid JSON response"

        mock_openai_client.chat.completions.create.return_value = mock_response

        llm_service = LLMService()
        subject, body = llm_service.generate_initial_bid_email(sample_conversation)

        # Should fall back to template
        assert "Pricing Inquiry" in subject
        assert sample_conversation.vendor_info.name in body

    @patch('services.llm_service.OpenAI')
    def test_parse_vendor_response_success(self, mock_openai_class, mock_openai_client, sample_questions):
        """Test successful vendor response parsing."""
        mock_openai_class.return_value = mock_openai_client

        # Mock successful parsing response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps([
            {"question_id": 1, "answer": "Yes, we have availability for those dates"},
            {"question_id": 2, "answer": "Standard rooms are $150 per night"}
        ])

        mock_openai_client.chat.completions.create.return_value = mock_response

        llm_service = LLMService()
        email_body = "Yes, we have availability for June 15-16. Standard rooms are $150 per night."
        answers = llm_service.parse_vendor_response(email_body, sample_questions)

        assert len(answers) == 2
        assert answers[0] == (1, "Yes, we have availability for those dates")
        assert answers[1] == (2, "Standard rooms are $150 per night")

        # Verify OpenAI was called correctly
        mock_openai_client.chat.completions.create.assert_called_once()
        call_args = mock_openai_client.chat.completions.create.call_args

        assert call_args[1]['model'] == "gpt-4-turbo-preview"
        assert call_args[1]['temperature'] == 0.3
        assert call_args[1]['max_tokens'] == 1000

    @patch('services.llm_service.OpenAI')
    def test_parse_vendor_response_api_error(self, mock_openai_class, mock_openai_client, sample_questions):
        """Test vendor response parsing with API error."""
        mock_openai_class.return_value = mock_openai_client

        # Mock API error
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        llm_service = LLMService()
        email_body = "Test email body"
        answers = llm_service.parse_vendor_response(email_body, sample_questions)

        assert answers == []

    @patch('services.llm_service.OpenAI')
    def test_parse_vendor_response_invalid_json(self, mock_openai_class, mock_openai_client, sample_questions):
        """Test vendor response parsing with invalid JSON."""
        mock_openai_class.return_value = mock_openai_client

        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Invalid JSON"

        mock_openai_client.chat.completions.create.return_value = mock_response

        llm_service = LLMService()
        email_body = "Test email body"
        answers = llm_service.parse_vendor_response(email_body, sample_questions)

        assert answers == []

    @patch('services.llm_service.OpenAI')
    def test_generate_follow_up_email_success(self, mock_openai_class, mock_openai_client, sample_conversation):
        """Test successful follow-up email generation."""
        mock_openai_class.return_value = mock_openai_client

        # Add some email history
        sample_conversation.add_email_exchange(
            direction="outbound",
            subject="Initial Inquiry",
            body="Initial email body"
        )
        sample_conversation.add_email_exchange(
            direction="inbound",
            subject="Re: Initial Inquiry",
            body="Partial response from vendor"
        )

        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "subject": "Follow-up: Additional Information Needed",
            "body": "Thank you for your response. We still need a few more details..."
        })

        mock_openai_client.chat.completions.create.return_value = mock_response

        llm_service = LLMService()
        unanswered_questions = [q for q in sample_conversation.questions if q.required and not q.answered]
        subject, body = llm_service.generate_follow_up_email(sample_conversation, unanswered_questions)

        assert subject == "Follow-up: Additional Information Needed"
        assert "Thank you for your response" in body

        # Verify OpenAI call
        mock_openai_client.chat.completions.create.assert_called_once()
        call_args = mock_openai_client.chat.completions.create.call_args

        assert call_args[1]['temperature'] == 0.7
        assert call_args[1]['max_tokens'] == 1000

    @patch('services.llm_service.OpenAI')
    def test_generate_follow_up_email_api_error(self, mock_openai_class, mock_openai_client, sample_conversation):
        """Test follow-up email generation with API error."""
        mock_openai_class.return_value = mock_openai_client

        # Mock API error
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        llm_service = LLMService()
        unanswered_questions = [q for q in sample_conversation.questions if q.required and not q.answered]
        subject, body = llm_service.generate_follow_up_email(sample_conversation, unanswered_questions)

        # Should fall back to template
        assert "Follow-up" in subject
        assert sample_conversation.event_metadata.name in subject
        assert sample_conversation.vendor_info.name in body

    def test_format_questions_for_email(self, sample_questions):
        """Test formatting questions for email inclusion."""
        llm_service = LLMService.__new__(LLMService)  # Create without __init__

        formatted = llm_service._format_questions_for_email(sample_questions)

        assert "1. Do you have availability for our dates? (Required)" in formatted
        assert "2. What is your rate per room per night? (Required)" in formatted
        assert "Options: Standard Room, Deluxe Room, Suite" in formatted
        assert "3. Do you offer shuttle service?" in formatted
        assert "(Required)" not in formatted.split('\n')[-1]  # Last question not required

    def test_format_questions_for_parsing(self, sample_questions):
        """Test formatting questions for parsing context."""
        llm_service = LLMService.__new__(LLMService)  # Create without __init__

        formatted = llm_service._format_questions_for_parsing(sample_questions)

        assert "ID 1: Do you have availability for our dates?" in formatted
        assert "ID 2: What is your rate per room per night?" in formatted
        assert "(Options: Standard Room, Deluxe Room, Suite)" in formatted
        assert "ID 3: Do you offer shuttle service?" in formatted

    def test_generate_fallback_initial_email(self, sample_conversation):
        """Test fallback initial email generation."""
        llm_service = LLMService.__new__(LLMService)  # Create without __init__

        subject, body = llm_service._generate_fallback_initial_email(sample_conversation)

        assert sample_conversation.event_metadata.name in subject
        assert sample_conversation.event_metadata.event_type in subject
        assert sample_conversation.vendor_info.name in body
        assert sample_conversation.event_metadata.planner_name in body
        assert sample_conversation.event_metadata.planner_email in body

        # Check that questions are included
        for question in sample_conversation.questions:
            assert question.text in body

    def test_generate_fallback_followup_email(self, sample_conversation):
        """Test fallback follow-up email generation."""
        llm_service = LLMService.__new__(LLMService)  # Create without __init__

        unanswered = [q for q in sample_conversation.questions if q.required and not q.answered]
        subject, body = llm_service._generate_fallback_followup_email(sample_conversation, unanswered)

        assert "Follow-up" in subject
        assert sample_conversation.event_metadata.name in subject
        assert sample_conversation.vendor_info.name in body
        assert sample_conversation.event_metadata.planner_name in body

        # Check that unanswered questions are included
        for question in unanswered:
            assert question.text in body
