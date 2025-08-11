"""
Database service for managing conversations and questions in DynamoDB.
"""

import os
import json
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
from typing import Optional, List, Dict, Any
from botocore.exceptions import ClientError

from models.conversation import Conversation, Question


class DatabaseService:
    """Service for DynamoDB operations."""

    def __init__(self):
        """Initialize the database service."""
        self.dynamodb = boto3.resource('dynamodb')
        self.conversation_table_name = os.environ.get('CONVERSATION_TABLE_NAME')
        self.questions_table_name = os.environ.get('QUESTIONS_TABLE_NAME')

        if not self.conversation_table_name or not self.questions_table_name:
            raise ValueError("DynamoDB table names must be set in environment variables")

        self.conversation_table = self.dynamodb.Table(self.conversation_table_name)
        self.questions_table = self.dynamodb.Table(self.questions_table_name)

    def save_conversation(self, conversation: Conversation) -> bool:
        """Save a conversation to DynamoDB."""
        try:
            # Convert conversation to dict and handle datetime serialization
            conversation_data = conversation.to_dict()

            # Convert datetime objects to ISO strings for DynamoDB
            conversation_data['created_at'] = conversation.created_at.isoformat()
            conversation_data['updated_at'] = conversation.updated_at.isoformat()

            # Convert email exchanges timestamps
            for exchange in conversation_data.get('email_exchanges', []):
                if 'timestamp' in exchange:
                    if isinstance(exchange['timestamp'], datetime):
                        exchange['timestamp'] = exchange['timestamp'].isoformat()

            self.conversation_table.put_item(Item=conversation_data)
            return True
        except ClientError as e:
            print(f"Error saving conversation: {e}")
            return False

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve a conversation from DynamoDB."""
        try:
            response = self.conversation_table.get_item(
                Key={'conversation_id': conversation_id}
            )

            if 'Item' not in response:
                return None

            item = response['Item']

            # Convert ISO strings back to datetime objects
            if 'created_at' in item:
                item['created_at'] = datetime.fromisoformat(item['created_at'])
            if 'updated_at' in item:
                item['updated_at'] = datetime.fromisoformat(item['updated_at'])

            # Convert email exchange timestamps
            for exchange in item.get('email_exchanges', []):
                if 'timestamp' in exchange:
                    exchange['timestamp'] = datetime.fromisoformat(exchange['timestamp'])

            return Conversation.from_dict(item)
        except ClientError as e:
            print(f"Error retrieving conversation: {e}")
            return None

    def update_conversation(self, conversation: Conversation) -> bool:
        """Update an existing conversation."""
        conversation.updated_at = datetime.utcnow()
        return self.save_conversation(conversation)

    def save_questions(self, conversation_id: str, questions: List[Question]) -> bool:
        """Save questions for a conversation."""
        try:
            # Use batch write for efficiency
            with self.questions_table.batch_writer() as batch:
                for question in questions:
                    question_data = question.model_dump()
                    question_data['conversation_id'] = conversation_id
                    batch.put_item(Item=question_data)
            return True
        except ClientError as e:
            print(f"Error saving questions: {e}")
            return False

    def get_questions(self, conversation_id: str) -> List[Question]:
        """Get all questions for a conversation."""
        try:
            response = self.questions_table.query(
                KeyConditionExpression=Key('conversation_id').eq(conversation_id)
            )

            questions = []
            for item in response.get('Items', []):
                questions.append(Question(**item))

            # Sort by question ID
            questions.sort(key=lambda q: q.id)
            return questions
        except ClientError as e:
            print(f"Error retrieving questions: {e}")
            return []

    def update_question_answer(self, conversation_id: str, question_id: int,
                              answer: str) -> bool:
        """Update a specific question's answer."""
        try:
            self.questions_table.update_item(
                Key={
                    'conversation_id': conversation_id,
                    'question_id': question_id
                },
                UpdateExpression='SET answer = :answer, answered = :answered',
                ExpressionAttributeValues={
                    ':answer': answer,
                    ':answered': True
                }
            )
            return True
        except ClientError as e:
            print(f"Error updating question answer: {e}")
            return False

    def get_recent_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent conversations for monitoring/debugging."""
        try:
            response = self.conversation_table.scan(
                Limit=limit,
                ProjectionExpression='conversation_id, #status, created_at, event_metadata, vendor_info',
                ExpressionAttributeNames={'#status': 'status'}
            )

            items = response.get('Items', [])
            # Sort by created_at descending
            items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return items
        except ClientError as e:
            print(f"Error retrieving recent conversations: {e}")
            return []

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and its questions (for cleanup/testing)."""
        try:
            # Delete all questions first
            questions = self.get_questions(conversation_id)
            with self.questions_table.batch_writer() as batch:
                for question in questions:
                    batch.delete_item(
                        Key={
                            'conversation_id': conversation_id,
                            'question_id': question.id
                        }
                    )

            # Delete the conversation
            self.conversation_table.delete_item(
                Key={'conversation_id': conversation_id}
            )
            return True
        except ClientError as e:
            print(f"Error deleting conversation: {e}")
            return False
