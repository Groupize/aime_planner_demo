"""
Conversation model for managing chatbot interactions with vendors.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Annotated
from pydantic import BaseModel, Field, PlainSerializer
from enum import Enum
import uuid


class ConversationStatus(str, Enum):
    """Status of a conversation."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Question(BaseModel):
    """Individual question in a bid request."""
    id: int = Field(..., description="Unique question ID")
    text: str = Field(..., description="Question text")
    required: bool = Field(default=False, description="Whether question is required")
    options: Optional[List[str]] = Field(default=None, description="Multiple choice options")
    sub_questions: Optional[List['Question']] = Field(default=None, description="Nested sub-questions")
    answer: Optional[str] = Field(default=None, description="Vendor's answer")
    answered: bool = Field(default=False, description="Whether question has been answered")


class EventMetadata(BaseModel):
    """Metadata about the event being planned."""
    name: str = Field(..., description="Event name")
    dates: List[str] = Field(..., description="Event dates")
    event_type: str = Field(..., description="Type of event")
    planner_name: str = Field(..., description="Event planner's name")
    planner_email: str = Field(..., description="Event planner's email")
    planner_phone: Optional[str] = Field(default=None, description="Event planner's phone")


class VendorInfo(BaseModel):
    """Information about the vendor being contacted."""
    name: str = Field(..., description="Vendor name")
    email: str = Field(..., description="Vendor email")
    phone: Optional[str] = Field(default=None, description="Vendor phone")
    service_type: str = Field(..., description="Type of service (hotel, restaurant, catering, etc.)")


class EmailExchange(BaseModel):
    """Individual email in the conversation."""
    timestamp: Annotated[datetime, PlainSerializer(lambda x: x.isoformat())] = Field(default_factory=datetime.utcnow)
    direction: str = Field(..., description="'outbound' or 'inbound'")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    questions_addressed: List[int] = Field(default_factory=list, description="Question IDs addressed")


class Conversation(BaseModel):
    """Complete conversation state."""
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: ConversationStatus = Field(default=ConversationStatus.INITIATED)
    event_metadata: EventMetadata
    vendor_info: VendorInfo
    questions: List[Question]
    email_exchanges: List[EmailExchange] = Field(default_factory=list)
    attempt_count: int = Field(default=0)
    max_attempts: int = Field(default=4)
    created_at: Annotated[datetime, PlainSerializer(lambda x: x.isoformat())] = Field(default_factory=datetime.utcnow)
    updated_at: Annotated[datetime, PlainSerializer(lambda x: x.isoformat())] = Field(default_factory=datetime.utcnow)
    rails_api_callback_data: Optional[Dict[str, Any]] = Field(default=None)

    def get_unanswered_required_questions(self) -> List[Question]:
        """Get all required questions that haven't been answered."""
        return [q for q in self.questions if q.required and not q.answered]

    def get_answered_questions(self) -> List[Question]:
        """Get all questions that have been answered."""
        return [q for q in self.questions if q.answered]

    def is_complete(self) -> bool:
        """Check if all required questions are answered or max attempts reached."""
        unanswered_required = self.get_unanswered_required_questions()
        return len(unanswered_required) == 0 or self.attempt_count >= self.max_attempts

    def add_email_exchange(self, direction: str, subject: str, body: str,
                          questions_addressed: List[int] = None) -> None:
        """Add a new email exchange to the conversation."""
        if questions_addressed is None:
            questions_addressed = []

        exchange = EmailExchange(
            direction=direction,
            subject=subject,
            body=body,
            questions_addressed=questions_addressed
        )
        self.email_exchanges.append(exchange)
        self.updated_at = datetime.utcnow()

    def update_question_answer(self, question_id: int, answer: str) -> bool:
        """Update an answer for a specific question."""
        for question in self.questions:
            if question.id == question_id:
                question.answer = answer
                question.answered = True
                self.updated_at = datetime.utcnow()
                return True
        return False

    def to_dict(self) -> dict:
        """Convert to dictionary for DynamoDB storage."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> 'Conversation':
        """Create from dictionary from DynamoDB."""
        return cls(**data)


# Enable forward references for nested Question model
Question.model_rebuild()
