"""
LLM service for email parsing and response generation using OpenAI.
"""

import os
import json
from typing import List, Tuple
from openai import OpenAI

from models.conversation import Question, Conversation


class LLMService:
    """Service for LLM-based email processing and generation."""

    def __init__(self):
        """Initialize the LLM service."""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key must be set in environment variables")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4-turbo-preview"

    def generate_initial_bid_email(self, conversation: Conversation) -> Tuple[str, str]:
        """Generate the initial bid request email to vendor."""

        # Format questions for the email
        questions_text = self._format_questions_for_email(conversation.questions)

        prompt = f"""
        You are a professional event planner writing an email to a vendor to
        request pricing and availability information.
        Write a conversational, professional but semi-casual email that clearly
        indicates you are representing a client in negotiations.

        Event Details:
        - Event Name: {conversation.event_metadata.name}
        - Event Type: {conversation.event_metadata.event_type}
        - Dates: {', '.join(conversation.event_metadata.dates)}
        - Your Name: {conversation.event_metadata.planner_name}

        Vendor Details:
        - Vendor Name: {conversation.vendor_info.name}
        - Service Type: {conversation.vendor_info.service_type}

        Questions to ask:
        {questions_text}

        Requirements:
        1. Use a conversational, professional tone
        2. Make it clear you're representing a client
        3. Ask all the questions in a natural way
        4. Include a clear call to action for response
        5. Be friendly but business-focused
        6. Subject line should be compelling and clear

        Format your response as JSON with 'subject' and 'body' fields.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system",
                     "content": "You are a professional event planner who writes effective vendor outreach emails."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )

            content = response.choices[0].message.content
            email_data = json.loads(content)

            return email_data.get('subject', ''), email_data.get('body', '')

        except Exception as e:
            print(f"Error generating initial email: {e}")
            # Fallback to template
            return self._generate_fallback_initial_email(conversation)

    def parse_vendor_response(self, email_body: str, questions: List[Question]) -> List[Tuple[int, str]]:
        """Parse vendor's email response and extract answers to questions."""

        questions_context = self._format_questions_for_parsing(questions)

        prompt = f"""
        You are analyzing a vendor's email response to extract answers to specific questions.

        Original Questions:
        {questions_context}

        Vendor's Email Response:
        {email_body}

        Task: Extract any answers provided in the email for the questions above.

        Instructions:
        1. Look for explicit and implicit answers
        2. Match answers to question IDs
        3. Extract the vendor's actual response text as the answer
        4. Only include answers that are clearly provided
        5. If a question is not answered, don't include it

        Return your response as a JSON array of objects with 'question_id' and 'answer' fields.
        Example: [{{"question_id": 1, "answer": "We have availability for those dates"}},
                  {{"question_id": 3, "answer": "$150 per person"}}]
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system",
                     "content": "You are an expert at parsing vendor responses and extracting structured information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            content = response.choices[0].message.content
            parsed_answers = json.loads(content)

            # Convert to list of tuples
            return [(item['question_id'], item['answer']) for item in parsed_answers]

        except Exception as e:
            print(f"Error parsing vendor response: {e}")
            return []

    def generate_follow_up_email(self, conversation: Conversation,
                                  unanswered_questions: List[Question]) -> Tuple[str, str]:
        """Generate a follow-up email for unanswered questions."""

        # Get previous exchanges for context
        previous_emails = conversation.email_exchanges[-2:] if len(conversation.email_exchanges) >= 2 else []

        previous_context = ""
        if previous_emails:
            previous_context = "\n\nPrevious email exchange summary:\n"
            for exchange in previous_emails:
                previous_context += f"- {exchange.direction.title()}: {exchange.subject}\n"

        unanswered_text = self._format_questions_for_email(unanswered_questions)

        prompt = f"""
        You are following up with a vendor who responded to your initial inquiry but didn't answer all questions.
        Write a polite, professional follow-up email.

        Event: {conversation.event_metadata.name}
        Vendor: {conversation.vendor_info.name}
        Service Type: {conversation.vendor_info.service_type}

        {previous_context}

        Unanswered Questions that still need responses:
        {unanswered_text}

        Requirements:
        1. Thank them for their previous response
        2. Politely mention the specific information still needed
        3. Maintain a collaborative tone
        4. Be brief but complete
        5. Include a clear deadline if this is attempt 2 or 3

        Attempt number: {conversation.attempt_count + 1}

        Format your response as JSON with 'subject' and 'body' fields.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional event planner writing follow-up emails."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            content = response.choices[0].message.content
            email_data = json.loads(content)

            return email_data.get('subject', ''), email_data.get('body', '')

        except Exception as e:
            print(f"Error generating follow-up email: {e}")
            return self._generate_fallback_followup_email(conversation, unanswered_questions)

    def _format_questions_for_email(self, questions: List[Question]) -> str:
        """Format questions for inclusion in emails."""
        formatted = []
        for q in questions:
            question_text = f"{q.id}. {q.text}"
            if q.required:
                question_text += " (Required)"
            if q.options:
                question_text += f"\n   Options: {', '.join(q.options)}"
            formatted.append(question_text)
        return "\n\n".join(formatted)

    def _format_questions_for_parsing(self, questions: List[Question]) -> str:
        """Format questions for LLM parsing context."""
        formatted = []
        for q in questions:
            formatted.append(f"ID {q.id}: {q.text}")
            if q.options:
                formatted.append(f"   (Options: {', '.join(q.options)})")
        return "\n".join(formatted)

    def _generate_fallback_initial_email(self, conversation: Conversation) -> Tuple[str, str]:
        """Generate fallback initial email if LLM fails."""
        subject = (f"Pricing Inquiry for {conversation.event_metadata.name} - "
                  f"{conversation.event_metadata.event_type}")

        event_dates = ', '.join(conversation.event_metadata.dates)
        body = f"""Hi {conversation.vendor_info.name},

I hope this email finds you well. I'm {conversation.event_metadata.planner_name}, and I'm working with a client to plan their upcoming {conversation.event_metadata.event_type} called "{conversation.event_metadata.name}" scheduled for {event_dates}.

We're exploring {conversation.vendor_info.service_type} options and would love to discuss how you might be able to support this event. Could you please provide information on the following:

{self._format_questions_for_email(conversation.questions)}

Thank you for your time, and I look forward to hearing from you soon!

Best regards,
{conversation.event_metadata.planner_name}
{conversation.event_metadata.planner_email}"""

        return subject, body

    def _generate_fallback_followup_email(self, conversation: Conversation,
                                        unanswered_questions: List[Question]) -> Tuple[str, str]:
        """Generate fallback follow-up email if LLM fails."""
        subject = f"Follow-up: {conversation.event_metadata.name} - Additional Information Needed"

        body = f"""Hi {conversation.vendor_info.name},

Thank you for your response regarding {conversation.event_metadata.name}.

To complete our evaluation, I still need a few additional details:

{self._format_questions_for_email(unanswered_questions)}

I'd appreciate your response when you have a chance.

Best regards,
{conversation.event_metadata.planner_name}"""

        return subject, body
