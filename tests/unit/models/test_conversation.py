"""
Unit tests for conversation models.
"""

import pytest
from datetime import datetime
from models.conversation import (
    Conversation, Question, EventMetadata, VendorInfo,
    ConversationStatus, EmailExchange
)


class TestQuestion:
    """Test cases for Question model."""

    def test_question_creation(self):
        """Test basic question creation."""
        question = Question(
            id=1,
            text="Test question?",
            required=True
        )

        assert question.id == 1
        assert question.text == "Test question?"
        assert question.required is True
        assert question.options is None
        assert question.sub_questions is None
        assert question.answer is None
        assert question.answered is False

    def test_question_with_options(self):
        """Test question creation with multiple choice options."""
        options = ["Option A", "Option B", "Option C"]
        question = Question(
            id=2,
            text="Choose one:",
            required=False,
            options=options
        )

        assert question.options == options
        assert question.required is False

    def test_question_with_sub_questions(self):
        """Test question with nested sub-questions."""
        sub_question = Question(id=2, text="Sub question?", required=False)
        main_question = Question(
            id=1,
            text="Main question?",
            required=True,
            sub_questions=[sub_question]
        )

        assert len(main_question.sub_questions) == 1
        assert main_question.sub_questions[0].text == "Sub question?"


class TestEventMetadata:
    """Test cases for EventMetadata model."""

    def test_event_metadata_creation(self):
        """Test basic event metadata creation."""
        event = EventMetadata(
            name="Test Event",
            dates=["2024-06-15"],
            event_type="conference",
            planner_name="John Doe",
            planner_email="john@example.com"
        )

        assert event.name == "Test Event"
        assert event.dates == ["2024-06-15"]
        assert event.event_type == "conference"
        assert event.planner_name == "John Doe"
        assert event.planner_email == "john@example.com"
        assert event.planner_phone is None

    def test_event_metadata_with_phone(self):
        """Test event metadata with phone number."""
        event = EventMetadata(
            name="Test Event",
            dates=["2024-06-15"],
            event_type="conference",
            planner_name="John Doe",
            planner_email="john@example.com",
            planner_phone="+1-555-123-4567"
        )

        assert event.planner_phone == "+1-555-123-4567"


class TestVendorInfo:
    """Test cases for VendorInfo model."""

    def test_vendor_info_creation(self):
        """Test basic vendor info creation."""
        vendor = VendorInfo(
            name="Test Vendor",
            email="vendor@example.com",
            service_type="catering"
        )

        assert vendor.name == "Test Vendor"
        assert vendor.email == "vendor@example.com"
        assert vendor.service_type == "catering"
        assert vendor.phone is None

    def test_vendor_info_with_phone(self):
        """Test vendor info with phone number."""
        vendor = VendorInfo(
            name="Test Vendor",
            email="vendor@example.com",
            service_type="catering",
            phone="+1-555-987-6543"
        )

        assert vendor.phone == "+1-555-987-6543"


class TestEmailExchange:
    """Test cases for EmailExchange model."""

    def test_email_exchange_creation(self):
        """Test email exchange creation."""
        exchange = EmailExchange(
            direction="outbound",
            subject="Test Subject",
            body="Test email body",
            questions_addressed=[1, 2]
        )

        assert exchange.direction == "outbound"
        assert exchange.subject == "Test Subject"
        assert exchange.body == "Test email body"
        assert exchange.questions_addressed == [1, 2]
        assert isinstance(exchange.timestamp, datetime)

    def test_email_exchange_defaults(self):
        """Test email exchange with default values."""
        exchange = EmailExchange(
            direction="inbound",
            subject="Re: Test",
            body="Reply body"
        )

        assert exchange.questions_addressed == []
        assert isinstance(exchange.timestamp, datetime)


class TestConversation:
    """Test cases for Conversation model."""

    def test_conversation_creation(self, sample_event_metadata, sample_vendor_info, sample_questions):
        """Test basic conversation creation."""
        conversation = Conversation(
            event_metadata=sample_event_metadata,
            vendor_info=sample_vendor_info,
            questions=sample_questions
        )

        assert conversation.status == ConversationStatus.INITIATED
        assert len(conversation.questions) == 3
        assert conversation.attempt_count == 0
        assert conversation.max_attempts == 4
        assert len(conversation.email_exchanges) == 0
        assert isinstance(conversation.created_at, datetime)
        assert isinstance(conversation.updated_at, datetime)
        assert conversation.conversation_id is not None

    def test_conversation_with_custom_values(self, sample_event_metadata, sample_vendor_info, sample_questions):
        """Test conversation creation with custom values."""
        conversation = Conversation(
            event_metadata=sample_event_metadata,
            vendor_info=sample_vendor_info,
            questions=sample_questions,
            max_attempts=3,
            status=ConversationStatus.IN_PROGRESS
        )

        assert conversation.max_attempts == 3
        assert conversation.status == ConversationStatus.IN_PROGRESS

    def test_get_unanswered_required_questions(self, sample_conversation):
        """Test getting unanswered required questions."""
        unanswered = sample_conversation.get_unanswered_required_questions()

        # Should have 2 required questions (ids 1 and 2)
        assert len(unanswered) == 2
        assert all(q.required for q in unanswered)
        assert {q.id for q in unanswered} == {1, 2}

    def test_get_answered_questions(self, answered_conversation):
        """Test getting answered questions."""
        answered = answered_conversation.get_answered_questions()

        # Should have 2 answered questions (ids 1 and 3)
        assert len(answered) == 2
        assert {q.id for q in answered} == {1, 3}
        assert all(q.answered for q in answered)

    def test_is_complete_all_required_answered(self, sample_conversation):
        """Test conversation completion when all required questions are answered."""
        # Answer all required questions
        sample_conversation.update_question_answer(1, "Yes")
        sample_conversation.update_question_answer(2, "Standard Room - $150/night")

        assert sample_conversation.is_complete() is True

    def test_is_complete_max_attempts_reached(self, sample_conversation):
        """Test conversation completion when max attempts reached."""
        sample_conversation.attempt_count = sample_conversation.max_attempts

        assert sample_conversation.is_complete() is True

    def test_is_complete_not_finished(self, sample_conversation):
        """Test conversation not complete when requirements not met."""
        # Only answer one required question
        sample_conversation.update_question_answer(1, "Yes")

        assert sample_conversation.is_complete() is False

    def test_add_email_exchange(self, sample_conversation):
        """Test adding email exchange."""
        initial_count = len(sample_conversation.email_exchanges)
        initial_updated_at = sample_conversation.updated_at

        sample_conversation.add_email_exchange(
            direction="outbound",
            subject="Test Subject",
            body="Test Body",
            questions_addressed=[1, 2]
        )

        assert len(sample_conversation.email_exchanges) == initial_count + 1

        exchange = sample_conversation.email_exchanges[-1]
        assert exchange.direction == "outbound"
        assert exchange.subject == "Test Subject"
        assert exchange.body == "Test Body"
        assert exchange.questions_addressed == [1, 2]
        assert sample_conversation.updated_at > initial_updated_at

    def test_update_question_answer(self, sample_conversation):
        """Test updating question answer."""
        initial_updated_at = sample_conversation.updated_at

        result = sample_conversation.update_question_answer(1, "Yes, available")

        assert result is True
        assert sample_conversation.questions[0].answer == "Yes, available"
        assert sample_conversation.questions[0].answered is True
        assert sample_conversation.updated_at > initial_updated_at

    def test_update_question_answer_invalid_id(self, sample_conversation):
        """Test updating question answer with invalid ID."""
        result = sample_conversation.update_question_answer(999, "Invalid")

        assert result is False
        # No questions should be modified
        assert all(not q.answered for q in sample_conversation.questions)

    def test_to_dict_conversion(self, sample_conversation):
        """Test conversation to dictionary conversion."""
        conv_dict = sample_conversation.to_dict()

        assert isinstance(conv_dict, dict)
        assert 'conversation_id' in conv_dict
        assert 'status' in conv_dict
        assert 'event_metadata' in conv_dict
        assert 'vendor_info' in conv_dict
        assert 'questions' in conv_dict
        assert 'email_exchanges' in conv_dict

    def test_from_dict_conversion(self, sample_conversation):
        """Test conversation from dictionary conversion."""
        conv_dict = sample_conversation.to_dict()
        restored_conv = Conversation.from_dict(conv_dict)

        assert restored_conv.conversation_id == sample_conversation.conversation_id
        assert restored_conv.status == sample_conversation.status
        assert restored_conv.event_metadata.name == sample_conversation.event_metadata.name
        assert restored_conv.vendor_info.name == sample_conversation.vendor_info.name
        assert len(restored_conv.questions) == len(sample_conversation.questions)

    def test_conversation_status_enum(self):
        """Test conversation status enumeration."""
        assert ConversationStatus.INITIATED == "initiated"
        assert ConversationStatus.IN_PROGRESS == "in_progress"
        assert ConversationStatus.COMPLETED == "completed"
        assert ConversationStatus.FAILED == "failed"

    def test_conversation_with_callback_data(self, sample_event_metadata, sample_vendor_info, sample_questions):
        """Test conversation with Rails callback data."""
        callback_data = {
            "rails_request_id": "req_123",
            "planner_id": 456
        }

        conversation = Conversation(
            event_metadata=sample_event_metadata,
            vendor_info=sample_vendor_info,
            questions=sample_questions,
            rails_api_callback_data=callback_data
        )

        assert conversation.rails_api_callback_data == callback_data
        assert conversation.rails_api_callback_data["rails_request_id"] == "req_123"
