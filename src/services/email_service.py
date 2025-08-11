"""
Email service for sending emails via SendGrid and handling SES/SNS integration.
"""

import os
import json
import re
from typing import Optional, Dict, Any
import boto3
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, CustomArg
from botocore.exceptions import ClientError


class EmailService:
    """Service for email operations."""

    def __init__(self):
        """Initialize the email service."""
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        self.environment = os.environ.get('ENVIRONMENT', 'testing')

        if not self.sendgrid_api_key:
            raise ValueError("SendGrid API key must be set in environment variables")

        self.sendgrid_client = SendGridAPIClient(api_key=self.sendgrid_api_key)

        # Check if we're running against LocalStack
        endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        if endpoint_url:
            self.ses_client = boto3.client('ses', endpoint_url=endpoint_url)
        else:
            self.ses_client = boto3.client('ses')

        # Email configuration
        self.from_email = f"aime-{self.environment}@groupize.com"
        self.reply_to_base = f"aime-{self.environment}+{{conversation_id}}@groupize.com"

    def send_vendor_email(self, to_email: str, subject: str, body: str,
                         conversation_id: str, planner_name: str) -> bool:
        """Send email to vendor using SendGrid."""
        try:
            # Create reply-to address that includes conversation ID
            reply_to_email = self.reply_to_base.format(conversation_id=conversation_id)

            from_email_obj = Email(self.from_email, planner_name)
            to_email_obj = To(to_email)
            content = Content("text/plain", body)

            mail = Mail(
                from_email=from_email_obj,
                to_emails=to_email_obj,
                subject=subject,
                plain_text_content=content
            )

            # Set reply-to header
            mail.reply_to = Email(reply_to_email)

            # Add custom headers for tracking using CustomArg objects
            mail.add_custom_arg(CustomArg('conversation_id', conversation_id))
            mail.add_custom_arg(CustomArg('environment', self.environment))
            mail.add_custom_arg(CustomArg('system', 'aime-planner'))

            response = self.sendgrid_client.send(mail)

            if response.status_code in [200, 202]:
                print(f"Email sent successfully to {to_email} for conversation {conversation_id}")
                return True
            else:
                print(f"SendGrid error: {response.status_code} - {response.body}")
                return False

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def parse_inbound_email(self, sns_message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse inbound email from SNS/SES notification."""
        try:
            # Parse SNS message
            if 'Message' in sns_message:
                message = json.loads(sns_message['Message'])
            else:
                message = sns_message

            # Extract email content from SES mail object
            if 'mail' not in message:
                print("No mail object in SNS message")
                return None

            mail_obj = message['mail']

            # Get conversation ID from recipient email
            recipients = mail_obj.get('commonHeaders', {}).get('to', [])
            conversation_id = None

            for recipient in recipients:
                match = re.search(r'aime-[^+]+\+([^@]+)@', recipient)
                if match:
                    conversation_id = match.group(1)
                    break

            if not conversation_id:
                print("Could not extract conversation ID from recipient email")
                return None

            # Extract email details
            common_headers = mail_obj.get('commonHeaders', {})

            result = {
                'conversation_id': conversation_id,
                'from_email': common_headers.get('from', [''])[0],
                'subject': common_headers.get('subject', ''),
                'timestamp': mail_obj.get('timestamp'),
                'message_id': mail_obj.get('messageId'),
                'body': None  # Will be extracted from content
            }

            # Extract email body from content
            if 'content' in message:
                # This would need to be enhanced based on SES content structure
                # For now, we'll assume the content is in the message
                result['body'] = self._extract_email_body(message.get('content', ''))

            return result

        except Exception as e:
            print(f"Error parsing inbound email: {e}")
            return None

    def _extract_email_body(self, content: str) -> str:
        """Extract plain text body from email content."""
        try:
            # This is a simplified extraction - in practice, you'd want
            # more sophisticated email parsing (e.g., using email.parser)

            if not content:
                return None

            # Remove quoted text (lines starting with >)
            lines = content.split('\n')
            clean_lines = []

            for line in lines:
                stripped = line.strip()
                # Skip lines starting with > (quoted text)
                if stripped.startswith('>'):
                    continue
                # Break on lines that look like email signature start
                elif stripped.startswith('On ') and '@' in stripped:
                    break
                else:
                    clean_lines.append(line)

            return '\n'.join(clean_lines).strip()

        except Exception as e:
            print(f"Error extracting email body: {e}")
            return content

    def verify_ses_domain(self, domain: str) -> bool:
        """Verify domain with SES for email receiving."""
        try:
            response = self.ses_client.verify_domain_identity(Domain=domain)
            print(f"Domain verification initiated for {domain}")
            return True
        except ClientError as e:
            print(f"Error verifying domain: {e}")
            return False

    def setup_ses_receipt_rule(self, rule_set_name: str, rule_name: str,
                              recipients: list, sns_topic_arn: str) -> bool:
        """Set up SES receipt rule for inbound email processing."""
        try:
            # Create receipt rule
            rule = {
                'Name': rule_name,
                'Enabled': True,
                'Recipients': recipients,
                'Actions': [
                    {
                        'SNSAction': {
                            'TopicArn': sns_topic_arn,
                            'Encoding': 'UTF-8'
                        }
                    }
                ]
            }

            self.ses_client.create_receipt_rule(
                RuleSetName=rule_set_name,
                Rule=rule
            )

            print(f"SES receipt rule created: {rule_name}")
            return True

        except ClientError as e:
            print(f"Error creating SES receipt rule: {e}")
            return False

    def get_email_status(self, message_id: str) -> Optional[str]:
        """Get delivery status of sent email (if using SES for sending)."""
        try:
            # This would require SES configuration event publishing
            # For now, we'll return None as we're using SendGrid
            return None
        except Exception as e:
            print(f"Error getting email status: {e}")
            return None
