"""
Models package for AIME Planner chatbot.
"""

from .conversation import (
    Conversation,
    ConversationStatus,
    Question,
    EventMetadata,
    VendorInfo,
    EmailExchange
)

__all__ = [
    'Conversation',
    'ConversationStatus',
    'Question',
    'EventMetadata',
    'VendorInfo',
    'EmailExchange'
]
