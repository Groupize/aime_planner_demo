"""
Lambda handler for initiating bid requests to vendors.
"""

import json
import os
import sys
from typing import Dict, Any

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.conversation import (Conversation, Question, EventMetadata,
                                VendorInfo, ConversationStatus)
from services.database import DatabaseService
from services.email_service import EmailService
from services.llm_service import LLMService
from services.rails_api import RailsAPIService


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle initiation of bid requests from Rails API.

    Expected payload:
    {
        "event_metadata": {
            "name": "Annual Company Retreat",
            "dates": ["2024-06-15", "2024-06-16"],
            "event_type": "corporate retreat",
            "planner_name": "Jane Smith",
            "planner_email": "jane.smith@company.com",
            "planner_phone": "+1-555-123-4567"
        },
        "vendor_info": {
            "name": "Mountain View Resort",
            "email": "sales@mountainviewresort.com",
            "service_type": "hotel"
        },
        "questions": [
            {
                "id": 1,
                "text": "Do you have availability for our dates?",
                "required": true
            },
            {
                "id": 2,
                "text": "What is your rate per room per night?",
                "required": true,
                "options": ["Standard Room", "Deluxe Room", "Suite"]
            }
        ],
        "callback_data": {
            "rails_request_id": "req_123",
            "planner_id": 456
        }
    }
    """

    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        # Validate required fields
        if not all(key in body for key in ['event_metadata', 'vendor_info', 'questions']):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required fields: event_metadata, vendor_info, questions'
                })
            }

        # Initialize services
        db_service = DatabaseService()
        email_service = EmailService()
        llm_service = LLMService()
        rails_api = RailsAPIService()

        # Create conversation model
        event_metadata = EventMetadata(**body['event_metadata'])
        vendor_info = VendorInfo(**body['vendor_info'])
        questions = [Question(**q) for q in body['questions']]

        conversation = Conversation(
            event_metadata=event_metadata,
            vendor_info=vendor_info,
            questions=questions,
            rails_api_callback_data=body.get('callback_data')
        )

        # Save initial conversation state
        if not db_service.save_conversation(conversation):
            raise Exception("Failed to save conversation to database")

        # Save questions separately for easier querying
        if not db_service.save_questions(conversation.conversation_id, questions):
            raise Exception("Failed to save questions to database")

        # Generate initial email using LLM
        subject, email_body = llm_service.generate_initial_bid_email(conversation)

        # Send email to vendor
        email_sent = email_service.send_vendor_email(
            to_email=vendor_info.email,
            subject=subject,
            body=email_body,
            conversation_id=conversation.conversation_id,
            planner_name=event_metadata.planner_name
        )

        if not email_sent:
            # Update conversation status to failed
            conversation.status = ConversationStatus.FAILED
            db_service.update_conversation(conversation)

            # Report error to Rails API
            rails_api.report_error(
                conversation.conversation_id,
                "email_sending_failed",
                "Failed to send initial bid request email",
                {"vendor_email": vendor_info.email}
            )

            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Failed to send email to vendor',
                    'conversation_id': conversation.conversation_id
                })
            }

        # Record email exchange
        conversation.add_email_exchange(
            direction="outbound",
            subject=subject,
            body=email_body,
            questions_addressed=[q.id for q in questions]
        )
        conversation.attempt_count = 1
        conversation.status = ConversationStatus.IN_PROGRESS

        # Update conversation in database
        db_service.update_conversation(conversation)

        # Notify Rails API of successful start
        rails_api.notify_conversation_started(
            conversation.conversation_id,
            vendor_info.email,
            email_sent
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Bid request initiated successfully',
                'conversation_id': conversation.conversation_id,
                'email_sent': email_sent,
                'vendor_email': vendor_info.email,
                'questions_count': len(questions)
            })
        }

    except Exception as e:
        print(f"Error in initiate_bid handler: {str(e)}")

        # Try to report error to Rails API if we have a conversation ID
        try:
            if 'conversation' in locals():
                rails_api = RailsAPIService()
                rails_api.report_error(
                    conversation.conversation_id,
                    "lambda_error",
                    str(e),
                    {"handler": "initiate_bid"}
                )
        except Exception:
            pass  # Don't fail on error reporting

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def validate_request_payload(payload: Dict[str, Any]) -> tuple[bool, str]:
    """Validate the incoming request payload."""

    # Check event_metadata
    event_meta = payload.get('event_metadata', {})
    required_event_fields = ['name', 'dates', 'event_type', 'planner_name', 'planner_email']
    for field in required_event_fields:
        if field not in event_meta:
            return False, f"Missing required event_metadata field: {field}"

    # Check vendor_info
    vendor_info = payload.get('vendor_info', {})
    required_vendor_fields = ['name', 'email', 'service_type']
    for field in required_vendor_fields:
        if field not in vendor_info:
            return False, f"Missing required vendor_info field: {field}"

    # Check questions
    questions = payload.get('questions', [])
    if not questions:
        return False, "At least one question is required"

    for i, question in enumerate(questions):
        if 'id' not in question or 'text' not in question:
            return False, f"Question {i} missing required 'id' or 'text' field"

    return True, ""
