"""
Lambda handler for processing inbound vendor email responses.
"""

import json
import os
import sys
from typing import Dict, Any, List, Tuple
from datetime import datetime

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.conversation import Conversation, ConversationStatus
from services.database import DatabaseService
from services.email_service import EmailService
from services.llm_service import LLMService
from services.rails_api import RailsAPIService


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle inbound vendor email responses via SNS from SES.

    Expected SNS event structure:
    {
        "Records": [
            {
                "Sns": {
                    "Message": "{...SES mail object...}"
                }
            }
        ]
    }
    """

    try:
        # Parse SNS records
        records = event.get('Records', [])
        if not records:
            print("No records found in event")
            return {'statusCode': 200, 'body': json.dumps({'message': 'No records to process'})}

        results = []

        for record in records:
            try:
                result = process_single_email_record(record)
                results.append(result)
            except Exception as e:
                print(f"Error processing email record: {e}")
                results.append({'status': 'error', 'error': str(e)})

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Email processing completed',
                'results': results
            })
        }

    except Exception as e:
        print(f"Error in process_email handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def process_single_email_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single email record from SNS."""

    # Initialize services
    db_service = DatabaseService()
    email_service = EmailService()
    llm_service = LLMService()
    rails_api = RailsAPIService()

    # Parse email from SNS message
    sns_message = record.get('Sns', {})
    email_data = email_service.parse_inbound_email(sns_message)

    if not email_data:
        return {'status': 'error', 'error': 'Failed to parse email data'}

    conversation_id = email_data['conversation_id']

    # Get conversation from database
    conversation = db_service.get_conversation(conversation_id)
    if not conversation:
        return {
            'status': 'error',
            'error': f'Conversation {conversation_id} not found',
            'conversation_id': conversation_id
        }

    # Check if conversation is already completed or failed
    if conversation.status in [ConversationStatus.COMPLETED, ConversationStatus.FAILED]:
        print(f"Conversation {conversation_id} already {conversation.status.value}, ignoring email")
        return {
            'status': 'ignored',
            'reason': f'Conversation already {conversation.status.value}',
            'conversation_id': conversation_id
        }

    try:
        # Parse vendor response using LLM
        email_body = email_data.get('body', '')
        answers = llm_service.parse_vendor_response(email_body, conversation.questions)

        # Update question answers
        questions_answered = []
        for question_id, answer in answers:
            if conversation.update_question_answer(question_id, answer):
                questions_answered.append(question_id)

        # Record email exchange
        conversation.add_email_exchange(
            direction="inbound",
            subject=email_data.get('subject', ''),
            body=email_body,
            questions_addressed=questions_answered
        )

        # Check if we need to send follow-up
        unanswered_required = conversation.get_unanswered_required_questions()
        should_follow_up = (
            len(unanswered_required) > 0 and
            conversation.attempt_count < conversation.max_attempts
        )

        if should_follow_up:
            # Generate and send follow-up email
            follow_up_sent = send_follow_up_email(
                conversation, unanswered_required, llm_service, email_service
            )

            if follow_up_sent:
                conversation.attempt_count += 1
            else:
                # Mark as failed if we can't send follow-up
                conversation.status = ConversationStatus.FAILED

        else:
            # Conversation is complete (all required answered or max attempts reached)
            conversation.status = ConversationStatus.COMPLETED

        # Save updated conversation
        db_service.update_conversation(conversation)

        # Send update to Rails API
        answered_questions = rails_api.format_questions_for_rails(
            conversation.get_answered_questions()
        )

        is_final = conversation.status == ConversationStatus.COMPLETED

        rails_api.send_conversation_update(
            conversation_id=conversation.conversation_id,
            status=conversation.status.value,
            questions_answered=answered_questions,
            is_final=is_final,
            raw_email_content=email_body
        )

        # If conversation is complete, send final notification
        if is_final:
            rails_api.notify_conversation_completed(
                conversation_id=conversation.conversation_id,
                final_status=conversation.status.value,
                all_answers=answered_questions,
                attempt_count=conversation.attempt_count
            )

        return {
            'status': 'success',
            'conversation_id': conversation_id,
            'questions_answered': len(questions_answered),
            'unanswered_required': len(unanswered_required),
            'follow_up_sent': should_follow_up and conversation.status != ConversationStatus.FAILED,
            'conversation_status': conversation.status.value,
            'attempt_count': conversation.attempt_count
        }

    except Exception as e:
        print(f"Error processing email for conversation {conversation_id}: {e}")

        # Mark conversation as failed
        conversation.status = ConversationStatus.FAILED
        db_service.update_conversation(conversation)

        # Report error to Rails API
        rails_api.report_error(
            conversation_id,
            "email_processing_error",
            str(e),
            {
                "email_data": email_data,
                "handler": "process_email"
            }
        )

        return {
            'status': 'error',
            'error': str(e),
            'conversation_id': conversation_id
        }


def send_follow_up_email(conversation: Conversation,
                        unanswered_questions: List[Any],
                        llm_service: LLMService,
                        email_service: EmailService) -> bool:
    """Send follow-up email for unanswered questions."""

    try:
        # Generate follow-up email
        subject, body = llm_service.generate_follow_up_email(
            conversation, unanswered_questions
        )

        # Send email
        email_sent = email_service.send_vendor_email(
            to_email=conversation.vendor_info.email,
            subject=subject,
            body=body,
            conversation_id=conversation.conversation_id,
            planner_name=conversation.event_metadata.planner_name
        )

        if email_sent:
            # Record the follow-up email
            conversation.add_email_exchange(
                direction="outbound",
                subject=subject,
                body=body,
                questions_addressed=[q.id for q in unanswered_questions]
            )

            print(f"Follow-up email sent for conversation {conversation.conversation_id}")
            return True
        else:
            print(f"Failed to send follow-up email for conversation {conversation.conversation_id}")
            return False

    except Exception as e:
        print(f"Error sending follow-up email: {e}")
        return False
