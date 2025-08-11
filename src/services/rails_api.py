"""
Rails API service for communicating with the Ruby on Rails backend.
"""

import os
import json
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RailsAPIService:
    """Service for communicating with Rails backend API."""

    def __init__(self):
        """Initialize the Rails API service."""
        self.base_url = os.environ.get('RAILS_API_BASE_URL')
        self.api_key = os.environ.get('RAILS_API_KEY')

        if not self.base_url or not self.api_key:
            raise ValueError("Rails API base URL and key must be set in environment variables")

        # Set up session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'AIME-Planner-Chatbot/1.0'
        })

    def send_conversation_update(self, conversation_id: str,
                               status: str,
                               questions_answered: List[Dict[str, Any]],
                               is_final: bool = False,
                               raw_email_content: Optional[str] = None) -> bool:
        """Send conversation update back to Rails API."""
        try:
            payload = {
                'conversation_id': conversation_id,
                'status': status,
                'questions_answered': questions_answered,
                'is_final': is_final,
                'timestamp': self._get_current_timestamp(),
                'raw_email_content': raw_email_content
            }

            endpoint = f"{self.base_url}/api/v1/chatbot/conversation_updates"

            response = self.session.post(endpoint, json=payload, timeout=30)

            if response.status_code in [200, 201, 202]:
                print(f"Successfully sent update for conversation {conversation_id}")
                return True
            else:
                print(f"Rails API error: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error sending conversation update: {e}")
            return False

    def get_conversation_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get additional context for a conversation from Rails API."""
        try:
            endpoint = f"{self.base_url}/api/v1/chatbot/conversations/{conversation_id}"

            response = self.session.get(endpoint, timeout=30)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"Conversation {conversation_id} not found in Rails API")
                return None
            else:
                print(f"Rails API error: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error getting conversation context: {e}")
            return None

    def notify_conversation_started(self, conversation_id: str,
                                  vendor_email: str,
                                  initial_email_sent: bool) -> bool:
        """Notify Rails API that a conversation has been initiated."""
        try:
            payload = {
                'conversation_id': conversation_id,
                'vendor_email': vendor_email,
                'initial_email_sent': initial_email_sent,
                'timestamp': self._get_current_timestamp()
            }

            endpoint = f"{self.base_url}/api/v1/chatbot/conversations/{conversation_id}/started"

            response = self.session.post(endpoint, json=payload, timeout=30)

            if response.status_code in [200, 201, 202]:
                print(f"Successfully notified Rails API of conversation start: {conversation_id}")
                return True
            else:
                print(f"Rails API error: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error notifying conversation start: {e}")
            return False

    def notify_conversation_completed(self, conversation_id: str,
                                    final_status: str,
                                    all_answers: List[Dict[str, Any]],
                                    attempt_count: int) -> bool:
        """Notify Rails API that a conversation has been completed."""
        try:
            payload = {
                'conversation_id': conversation_id,
                'final_status': final_status,
                'all_answers': all_answers,
                'attempt_count': attempt_count,
                'completed_at': self._get_current_timestamp()
            }

            endpoint = f"{self.base_url}/api/v1/chatbot/conversations/{conversation_id}/completed"

            response = self.session.post(endpoint, json=payload, timeout=30)

            if response.status_code in [200, 201, 202]:
                print(f"Successfully notified Rails API of conversation completion: {conversation_id}")
                return True
            else:
                print(f"Rails API error: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error notifying conversation completion: {e}")
            return False

    def report_error(self, conversation_id: str, error_type: str,
                    error_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Report an error to Rails API for monitoring."""
        try:
            payload = {
                'conversation_id': conversation_id,
                'error_type': error_type,
                'error_message': error_message,
                'context': context or {},
                'timestamp': self._get_current_timestamp()
            }

            endpoint = f"{self.base_url}/api/v1/chatbot/errors"

            response = self.session.post(endpoint, json=payload, timeout=30)

            if response.status_code in [200, 201, 202]:
                print(f"Successfully reported error for conversation {conversation_id}")
                return True
            else:
                print(f"Rails API error reporting error: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error reporting error to Rails API: {e}")
            return False

    def validate_api_connection(self) -> bool:
        """Validate connection to Rails API."""
        try:
            endpoint = f"{self.base_url}/api/v1/health"

            response = self.session.get(endpoint, timeout=10)

            if response.status_code == 200:
                print("Rails API connection validated successfully")
                return True
            else:
                print(f"Rails API health check failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error validating Rails API connection: {e}")
            return False

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'

    def format_questions_for_rails(self, questions: List[Any]) -> List[Dict[str, Any]]:
        """Format questions for sending back to Rails API."""
        formatted_questions = []

        for question in questions:
            # Handle both Question objects and dictionaries
            if hasattr(question, 'dict'):
                q_data = question.dict()
            else:
                q_data = question

            formatted_question = {
                'id': q_data.get('id'),
                'text': q_data.get('text'),
                'answer': q_data.get('answer'),
                'answered': q_data.get('answered', False),
                'required': q_data.get('required', False)
            }

            formatted_questions.append(formatted_question)

        return formatted_questions
