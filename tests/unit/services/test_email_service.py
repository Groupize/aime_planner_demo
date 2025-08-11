"""
Unit tests for email service.
"""

import json
import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from services.email_service import EmailService


class TestEmailService:
    """Test cases for EmailService."""

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_init_success(self, mock_boto3, mock_sendgrid_class):
        """Test successful email service initialization."""
        mock_sendgrid_client = Mock()
        mock_sendgrid_class.return_value = mock_sendgrid_client

        mock_ses_client = Mock()
        mock_boto3.client.return_value = mock_ses_client

        email_service = EmailService()

        assert email_service.sendgrid_client == mock_sendgrid_client
        assert email_service.ses_client == mock_ses_client
        assert email_service.environment == 'testing'
        assert email_service.from_email == 'aime-testing@groupize.com'
        assert 'aime-testing+{conversation_id}@groupize.com' in email_service.reply_to_base

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_init_missing_sendgrid_key(self, mock_boto3, mock_sendgrid_class):
        """Test initialization failure with missing SendGrid API key."""
        import os
        old_key = os.environ.pop('SENDGRID_API_KEY', None)

        try:
            with pytest.raises(ValueError, match="SendGrid API key must be set"):
                EmailService()
        finally:
            if old_key:
                os.environ['SENDGRID_API_KEY'] = old_key

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_send_vendor_email_success(self, mock_boto3, mock_sendgrid_class):
        """Test successful vendor email sending."""
        mock_sendgrid_client = Mock()
        mock_sendgrid_class.return_value = mock_sendgrid_client

        # Mock successful SendGrid response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_sendgrid_client.send.return_value = mock_response

        email_service = EmailService()
        result = email_service.send_vendor_email(
            to_email="vendor@example.com",
            subject="Test Subject",
            body="Test email body",
            conversation_id="test-conv-id",
            planner_name="John Doe"
        )

        assert result is True
        mock_sendgrid_client.send.assert_called_once()

        # We can't easily test the Mail object structure due to SendGrid's internal implementation
        # The important thing is that the method returns True when SendGrid returns 202

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_send_vendor_email_sendgrid_error(self, mock_boto3, mock_sendgrid_class):
        """Test vendor email sending with SendGrid error."""
        mock_sendgrid_client = Mock()
        mock_sendgrid_class.return_value = mock_sendgrid_client

        # Mock SendGrid error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.body = "Bad Request"
        mock_sendgrid_client.send.return_value = mock_response

        email_service = EmailService()
        result = email_service.send_vendor_email(
            to_email="vendor@example.com",
            subject="Test Subject",
            body="Test email body",
            conversation_id="test-conv-id",
            planner_name="John Doe"
        )

        assert result is False

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_send_vendor_email_exception(self, mock_boto3, mock_sendgrid_class):
        """Test vendor email sending with exception."""
        mock_sendgrid_client = Mock()
        mock_sendgrid_class.return_value = mock_sendgrid_client

        # Mock SendGrid exception
        mock_sendgrid_client.send.side_effect = Exception("Network error")

        email_service = EmailService()
        result = email_service.send_vendor_email(
            to_email="vendor@example.com",
            subject="Test Subject",
            body="Test email body",
            conversation_id="test-conv-id",
            planner_name="John Doe"
        )

        assert result is False

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_parse_inbound_email_success(self, mock_boto3, mock_sendgrid_class, sample_sns_email_event):
        """Test successful inbound email parsing."""
        email_service = EmailService()
        result = email_service.parse_inbound_email(sample_sns_email_event['Records'][0]['Sns'])

        assert result is not None
        assert result['conversation_id'] == 'test-conversation-id'
        assert result['from_email'] == 'vendor@example.com'
        assert result['subject'] == 'Re: Test Subject'
        assert result['timestamp'] == '2024-01-01T12:00:00.000Z'
        assert result['message_id'] == 'test-message-id'

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_parse_inbound_email_no_conversation_id(self, mock_boto3, mock_sendgrid_class):
        """Test inbound email parsing with no conversation ID."""
        sns_message = {
            'Message': json.dumps({
                'mail': {
                    'commonHeaders': {
                        'to': ['noreply@groupize.com'],  # No conversation ID
                        'from': ['vendor@example.com'],
                        'subject': 'Test Subject'
                    },
                    'timestamp': '2024-01-01T12:00:00.000Z',
                    'messageId': 'test-message-id'
                }
            })
        }

        email_service = EmailService()
        result = email_service.parse_inbound_email(sns_message)

        assert result is None

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_parse_inbound_email_no_mail_object(self, mock_boto3, mock_sendgrid_class):
        """Test inbound email parsing with no mail object."""
        sns_message = {
            'Message': json.dumps({
                'invalid': 'structure'
            })
        }

        email_service = EmailService()
        result = email_service.parse_inbound_email(sns_message)

        assert result is None

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_parse_inbound_email_exception(self, mock_boto3, mock_sendgrid_class):
        """Test inbound email parsing with exception."""
        sns_message = {
            'Message': 'invalid json'
        }

        email_service = EmailService()
        result = email_service.parse_inbound_email(sns_message)

        assert result is None

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_extract_email_body(self, mock_boto3, mock_sendgrid_class):
        """Test email body extraction."""
        email_service = EmailService()

        # Test content with quoted text
        content = """This is the main response.

More content here.

> On Jan 1, 2024, at 12:00 PM, sender@example.com wrote:
> This is quoted text that should be removed.
> More quoted text.

Another line after quoted text."""

        result = email_service._extract_email_body(content)

        assert "This is the main response." in result
        assert "More content here." in result
        # The > quoted lines should be removed
        lines = result.split('\n')
        assert not any(line.strip().startswith('>') for line in lines)
        # Since there's no "On...@" pattern, the method should include the final line
        # The current implementation only breaks on "On...@" signature patterns
        assert "Another line after quoted text." in result

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_extract_email_body_simple(self, mock_boto3, mock_sendgrid_class):
        """Test email body extraction with simple content."""
        email_service = EmailService()

        content = "Simple email response without quoted text."
        result = email_service._extract_email_body(content)

        assert result == "Simple email response without quoted text."

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_extract_email_body_exception(self, mock_boto3, mock_sendgrid_class):
        """Test email body extraction with exception."""
        email_service = EmailService()

        # This should not raise an exception
        result = email_service._extract_email_body(None)

        assert result is None

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_verify_ses_domain_success(self, mock_boto3, mock_sendgrid_class):
        """Test successful SES domain verification."""
        mock_ses_client = Mock()
        mock_boto3.client.return_value = mock_ses_client

        mock_ses_client.verify_domain_identity.return_value = {'VerificationToken': 'token123'}

        email_service = EmailService()
        result = email_service.verify_ses_domain('example.com')

        assert result is True
        mock_ses_client.verify_domain_identity.assert_called_once_with(Domain='example.com')

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_verify_ses_domain_error(self, mock_boto3, mock_sendgrid_class):
        """Test SES domain verification with error."""
        mock_ses_client = Mock()
        mock_boto3.client.return_value = mock_ses_client

        mock_ses_client.verify_domain_identity.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid domain'}},
            'VerifyDomainIdentity'
        )

        email_service = EmailService()
        result = email_service.verify_ses_domain('example.com')

        assert result is False

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_setup_ses_receipt_rule_success(self, mock_boto3, mock_sendgrid_class):
        """Test successful SES receipt rule setup."""
        mock_ses_client = Mock()
        mock_boto3.client.return_value = mock_ses_client

        email_service = EmailService()
        result = email_service.setup_ses_receipt_rule(
            rule_set_name='test-rules',
            rule_name='test-rule',
            recipients=['test@example.com'],
            sns_topic_arn='arn:aws:sns:us-east-1:123456789012:test-topic'
        )

        assert result is True
        mock_ses_client.create_receipt_rule.assert_called_once()

        # Verify rule structure
        call_args = mock_ses_client.create_receipt_rule.call_args
        assert call_args[1]['RuleSetName'] == 'test-rules'
        assert call_args[1]['Rule']['Name'] == 'test-rule'
        assert call_args[1]['Rule']['Recipients'] == ['test@example.com']
        assert call_args[1]['Rule']['Enabled'] is True

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_setup_ses_receipt_rule_error(self, mock_boto3, mock_sendgrid_class):
        """Test SES receipt rule setup with error."""
        mock_ses_client = Mock()
        mock_boto3.client.return_value = mock_ses_client

        mock_ses_client.create_receipt_rule.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Rule error'}},
            'CreateReceiptRule'
        )

        email_service = EmailService()
        result = email_service.setup_ses_receipt_rule(
            rule_set_name='test-rules',
            rule_name='test-rule',
            recipients=['test@example.com'],
            sns_topic_arn='arn:aws:sns:us-east-1:123456789012:test-topic'
        )

        assert result is False

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_get_email_status(self, mock_boto3, mock_sendgrid_class):
        """Test email status retrieval (should return None for SendGrid)."""
        email_service = EmailService()
        result = email_service.get_email_status('test-message-id')

        # Should return None since we're using SendGrid
        assert result is None

    @patch('services.email_service.SendGridAPIClient')
    @patch('services.email_service.boto3')
    def test_conversation_id_extraction_regex(self, mock_boto3, mock_sendgrid_class):
        """Test conversation ID extraction from email addresses."""
        email_service = EmailService()

        test_cases = [
            ('aime-testing+conv-123@groupize.com', 'conv-123'),
            ('aime-production+long-conversation-id-456@groupize.com', 'long-conversation-id-456'),
            ('aime-staging+uuid-abc-def-123@groupize.com', 'uuid-abc-def-123'),
            ('noreply@groupize.com', None),
            ('aime-testing@groupize.com', None)  # No plus sign
        ]

        for email_addr, expected_conv_id in test_cases:
            # Create mock SNS message
            sns_message = {
                'Message': json.dumps({
                    'mail': {
                        'commonHeaders': {
                            'to': [email_addr],
                            'from': ['vendor@example.com'],
                            'subject': 'Test'
                        },
                        'timestamp': '2024-01-01T12:00:00.000Z',
                        'messageId': 'test-id'
                    }
                })
            }

            result = email_service.parse_inbound_email(sns_message)

            if expected_conv_id:
                assert result is not None
                assert result['conversation_id'] == expected_conv_id
            else:
                assert result is None
