"""
Unit tests for database service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from botocore.exceptions import ClientError

from services.database import DatabaseService
from models.conversation import Conversation, Question, ConversationStatus


class TestDatabaseService:
    """Test cases for DatabaseService."""

    @patch('services.database.boto3')
    def test_init_success(self, mock_boto3, mock_dynamodb_resource):
        """Test successful database service initialization."""
        mock_boto3.resource.return_value = mock_dynamodb_resource

        db_service = DatabaseService()

        assert db_service.conversation_table_name == 'test-conversations'
        assert db_service.questions_table_name == 'test-questions'
        mock_boto3.resource.assert_called_once_with('dynamodb')

    @patch('services.database.boto3')
    def test_init_missing_env_vars(self, mock_boto3):
        """Test initialization failure with missing environment variables."""
        # Temporarily remove environment variables
        import os
        old_conv_table = os.environ.pop('CONVERSATION_TABLE_NAME', None)

        try:
            with pytest.raises(ValueError, match="DynamoDB table names must be set"):
                DatabaseService()
        finally:
            # Restore environment variable
            if old_conv_table:
                os.environ['CONVERSATION_TABLE_NAME'] = old_conv_table

    @patch('services.database.boto3')
    def test_save_conversation_success(self, mock_boto3, mock_dynamodb_table, sample_conversation):
        """Test successful conversation save."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        db_service = DatabaseService()
        result = db_service.save_conversation(sample_conversation)

        assert result is True
        mock_dynamodb_table.put_item.assert_called_once()

        # Verify the item data structure
        call_args = mock_dynamodb_table.put_item.call_args
        item_data = call_args[1]['Item']

        assert 'conversation_id' in item_data
        assert 'status' in item_data
        assert 'created_at' in item_data
        assert 'updated_at' in item_data

    @patch('services.database.boto3')
    def test_save_conversation_client_error(self, mock_boto3, mock_dynamodb_table, sample_conversation):
        """Test conversation save with DynamoDB client error."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        # Mock ClientError
        mock_dynamodb_table.put_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Test error'}},
            'PutItem'
        )

        db_service = DatabaseService()
        result = db_service.save_conversation(sample_conversation)

        assert result is False

    @patch('services.database.boto3')
    def test_get_conversation_success(self, mock_boto3, mock_dynamodb_table, sample_conversation):
        """Test successful conversation retrieval."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        # Mock successful response
        conv_data = sample_conversation.to_dict()
        conv_data['created_at'] = sample_conversation.created_at.isoformat()
        conv_data['updated_at'] = sample_conversation.updated_at.isoformat()

        mock_dynamodb_table.get_item.return_value = {'Item': conv_data}

        db_service = DatabaseService()
        result = db_service.get_conversation(sample_conversation.conversation_id)

        assert result is not None
        assert isinstance(result, Conversation)
        assert result.conversation_id == sample_conversation.conversation_id
        mock_dynamodb_table.get_item.assert_called_once_with(
            Key={'conversation_id': sample_conversation.conversation_id}
        )

    @patch('services.database.boto3')
    def test_get_conversation_not_found(self, mock_boto3, mock_dynamodb_table):
        """Test conversation retrieval when not found."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        # Mock not found response
        mock_dynamodb_table.get_item.return_value = {}

        db_service = DatabaseService()
        result = db_service.get_conversation('nonexistent-id')

        assert result is None

    @patch('services.database.boto3')
    def test_get_conversation_client_error(self, mock_boto3, mock_dynamodb_table):
        """Test conversation retrieval with client error."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        mock_dynamodb_table.get_item.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
            'GetItem'
        )

        db_service = DatabaseService()
        result = db_service.get_conversation('test-id')

        assert result is None

    @patch('services.database.boto3')
    def test_update_conversation(self, mock_boto3, mock_dynamodb_table, sample_conversation):
        """Test conversation update."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        db_service = DatabaseService()

        # Capture original updated_at
        original_updated_at = sample_conversation.updated_at

        result = db_service.update_conversation(sample_conversation)

        assert result is True
        # Verify updated_at was modified
        assert sample_conversation.updated_at > original_updated_at
        mock_dynamodb_table.put_item.assert_called_once()

    @patch('services.database.boto3')
    def test_save_questions_success(self, mock_boto3, mock_dynamodb_table, sample_questions):
        """Test successful questions save."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        # Mock batch writer
        mock_batch_writer = MagicMock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_batch_writer
        mock_context_manager.__exit__.return_value = None
        mock_dynamodb_table.batch_writer.return_value = mock_context_manager

        db_service = DatabaseService()
        result = db_service.save_questions('test-conversation-id', sample_questions)

        assert result is True
        mock_dynamodb_table.batch_writer.assert_called_once()

        # Verify batch writer was used correctly
        assert mock_batch_writer.put_item.call_count == len(sample_questions)

    @patch('services.database.boto3')
    def test_save_questions_client_error(self, mock_boto3, mock_dynamodb_table, sample_questions):
        """Test questions save with client error."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        # Mock batch writer with error
        mock_dynamodb_table.batch_writer.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Batch error'}},
            'BatchWriteItem'
        )

        db_service = DatabaseService()
        result = db_service.save_questions('test-conversation-id', sample_questions)

        assert result is False

    @patch('services.database.boto3')
    @patch('services.database.Key')
    def test_get_questions_success(self, mock_key, mock_boto3, mock_dynamodb_table, sample_questions):
        """Test successful questions retrieval."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        # Mock query response
        questions_data = [q.model_dump() for q in sample_questions]
        for i, q_data in enumerate(questions_data):
            q_data['conversation_id'] = 'test-conversation-id'

        mock_dynamodb_table.query.return_value = {'Items': questions_data}

        db_service = DatabaseService()
        result = db_service.get_questions('test-conversation-id')

        assert len(result) == len(sample_questions)
        assert all(isinstance(q, Question) for q in result)

        # Verify questions are sorted by ID
        question_ids = [q.id for q in result]
        assert question_ids == sorted(question_ids)

    @patch('services.database.boto3')
    @patch('services.database.Key')
    def test_get_questions_client_error(self, mock_key, mock_boto3, mock_dynamodb_table):
        """Test questions retrieval with client error."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        mock_dynamodb_table.query.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Query error'}},
            'Query'
        )

        db_service = DatabaseService()
        result = db_service.get_questions('test-conversation-id')

        assert result == []

    @patch('services.database.boto3')
    def test_update_question_answer_success(self, mock_boto3, mock_dynamodb_table):
        """Test successful question answer update."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        db_service = DatabaseService()
        result = db_service.update_question_answer('test-conv-id', 1, 'Test answer')

        assert result is True
        mock_dynamodb_table.update_item.assert_called_once()

        # Verify update parameters
        call_args = mock_dynamodb_table.update_item.call_args
        assert call_args[1]['Key'] == {'conversation_id': 'test-conv-id', 'question_id': 1}
        assert call_args[1]['ExpressionAttributeValues'][':answer'] == 'Test answer'
        assert call_args[1]['ExpressionAttributeValues'][':answered'] is True

    @patch('services.database.boto3')
    def test_update_question_answer_client_error(self, mock_boto3, mock_dynamodb_table):
        """Test question answer update with client error."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        mock_dynamodb_table.update_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Update error'}},
            'UpdateItem'
        )

        db_service = DatabaseService()
        result = db_service.update_question_answer('test-conv-id', 1, 'Test answer')

        assert result is False

    @patch('services.database.boto3')
    def test_get_recent_conversations(self, mock_boto3, mock_dynamodb_table):
        """Test getting recent conversations."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        # Mock scan response
        mock_items = [
            {
                'conversation_id': {'S': 'conv-1'},
                'status': {'S': 'completed'},
                'created_at': '2024-01-01T12:00:00',
                'vendor_info': {'M': {'name': {'S': 'Vendor 1'}}}
            },
            {
                'conversation_id': {'S': 'conv-2'},
                'status': {'S': 'in_progress'},
                'created_at': '2024-01-01T11:00:00',
                'vendor_info': {'M': {'name': {'S': 'Vendor 2'}}}
            }
        ]
        mock_dynamodb_table.scan.return_value = {'Items': mock_items}

        db_service = DatabaseService()
        result = db_service.get_recent_conversations(limit=10)

        assert len(result) == 2
        # Verify sorting (most recent first)
        assert result[0]['conversation_id']['S'] == 'conv-1'  # Created later

    @patch('services.database.boto3')
    def test_delete_conversation_success(self, mock_boto3, mock_dynamodb_table, sample_questions):
        """Test successful conversation deletion."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        # Mock questions retrieval
        questions_data = [q.model_dump() for q in sample_questions]
        for q_data in questions_data:
            q_data['conversation_id'] = 'test-conversation-id'
        mock_dynamodb_table.query.return_value = {'Items': questions_data}

        # Mock batch writer for deletion
        mock_batch_writer = MagicMock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_batch_writer
        mock_context_manager.__exit__.return_value = None
        mock_dynamodb_table.batch_writer.return_value = mock_context_manager

        db_service = DatabaseService()
        result = db_service.delete_conversation('test-conversation-id')

        assert result is True

        # Verify questions were deleted
        mock_dynamodb_table.batch_writer.assert_called_once()
        assert mock_batch_writer.delete_item.call_count == len(sample_questions)

        # Verify conversation was deleted
        mock_dynamodb_table.delete_item.assert_called_once_with(
            Key={'conversation_id': 'test-conversation-id'}
        )

    @patch('services.database.boto3')
    def test_delete_conversation_client_error(self, mock_boto3, mock_dynamodb_table):
        """Test conversation deletion with client error."""
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_dynamodb_table
        mock_boto3.resource.return_value = mock_resource

        # Mock questions retrieval to succeed but deletion to fail
        mock_dynamodb_table.query.return_value = {'Items': []}

        # Mock batch writer
        mock_batch_writer = MagicMock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_batch_writer
        mock_context_manager.__exit__.return_value = None
        mock_dynamodb_table.batch_writer.return_value = mock_context_manager

        mock_dynamodb_table.delete_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Delete error'}},
            'DeleteItem'
        )

        db_service = DatabaseService()
        result = db_service.delete_conversation('test-conversation-id')

        assert result is False
