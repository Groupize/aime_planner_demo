# Rails API Integration Documentation

This document describes the API requirements for the Ruby on Rails backend that integrates with the AIME Planner Chatbot.

## Table of Contents

- [Authentication](#authentication)
- [Environment Configuration](#environment-configuration)
- [API Endpoints](#api-endpoints)
- [Initiating Conversations](#initiating-conversations)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Retry Strategy](#retry-strategy)

## Authentication

The AIME Planner Chatbot uses **Bearer Token authentication** for all API requests.

### Headers Required

```http
Authorization: Bearer {RAILS_API_KEY}
Content-Type: application/json
User-Agent: AIME-Planner-Chatbot/1.0
```

### Environment Variables

The Rails backend URL and API key must be configured via environment variables:

- `RAILS_API_BASE_URL`: Base URL of your Rails API (e.g., `https://api.example.com`)
- `RAILS_API_KEY`: API key for authentication

## Environment Configuration

```bash
# Required environment variables
RAILS_API_BASE_URL=https://api.example.com
RAILS_API_KEY=your-secret-api-key-here
```

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /api/v1/health`

**Purpose:** Validate API connectivity

**Request:** No body required

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Status Codes:** `200 OK`

---

### 2. Get Conversation Context

**Endpoint:** `GET /api/v1/chatbot/conversations/{conversation_id}`

**Purpose:** Retrieve additional context for an existing conversation

**Parameters:**
- `conversation_id` (string): Unique conversation identifier

**Response:**
```json
{
  "conversation_id": "conv_12345",
  "status": "in_progress",
  "created_at": "2024-01-15T10:00:00Z",
  "event_metadata": {
    "name": "Annual Company Retreat",
    "dates": ["2024-06-15", "2024-06-16"],
    "event_type": "corporate retreat",
    "planner_name": "Jane Smith",
    "planner_email": "jane.smith@company.com"
  },
  "vendor_info": {
    "name": "Mountain View Resort",
    "email": "sales@mountainviewresort.com",
    "service_type": "hotel"
  }
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Conversation not found

---

### 3. Notify Conversation Started

**Endpoint:** `POST /api/v1/chatbot/conversations/{conversation_id}/started`

**Purpose:** Notify Rails API that a conversation has been initiated

**Request Body:**
```json
{
  "conversation_id": "conv_12345",
  "vendor_email": "sales@mountainviewresort.com",
  "initial_email_sent": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Response:** No specific body required

**Status Codes:** `200 OK`, `201 Created`, `202 Accepted`

---

### 4. Send Conversation Updates

**Endpoint:** `POST /api/v1/chatbot/conversation_updates`

**Purpose:** Send progress updates during the conversation

**Request Body:**
```json
{
  "conversation_id": "conv_12345",
  "status": "awaiting_response",
  "questions_answered": [
    {
      "id": 1,
      "text": "Do you have availability for our dates?",
      "answer": "Yes, we have availability for those dates",
      "answered": true,
      "required": true
    },
    {
      "id": 2,
      "text": "What is your rate per room per night?",
      "answer": null,
      "answered": false,
      "required": true
    }
  ],
  "is_final": false,
  "timestamp": "2024-01-15T10:35:00Z",
  "raw_email_content": "Thank you for your inquiry..."
}
```

**Status Codes:** `200 OK`, `201 Created`, `202 Accepted`

---

### 5. Notify Conversation Completed

**Endpoint:** `POST /api/v1/chatbot/conversations/{conversation_id}/completed`

**Purpose:** Notify Rails API that a conversation has finished

**Request Body:**
```json
{
  "conversation_id": "conv_12345",
  "final_status": "completed",
  "all_answers": [
    {
      "id": 1,
      "text": "Do you have availability for our dates?",
      "answer": "Yes, we have availability for those dates",
      "answered": true,
      "required": true
    },
    {
      "id": 2,
      "text": "What is your rate per room per night?",
      "answer": "$250 per night for standard rooms",
      "answered": true,
      "required": true
    }
  ],
  "attempt_count": 2,
  "completed_at": "2024-01-15T11:00:00Z"
}
```

**Status Codes:** `200 OK`, `201 Created`, `202 Accepted`

---

### 6. Report Errors

**Endpoint:** `POST /api/v1/chatbot/errors`

**Purpose:** Report errors for monitoring and debugging

**Request Body:**
```json
{
  "conversation_id": "conv_12345",
  "error_type": "email_send_failure",
  "error_message": "Failed to send email to vendor",
  "context": {
    "vendor_email": "sales@mountainviewresort.com",
    "attempt_count": 3,
    "handler": "initiate_bid"
  },
  "timestamp": "2024-01-15T10:45:00Z"
}
```

**Status Codes:** `200 OK`, `201 Created`, `202 Accepted`

## Initiating Conversations

To initiate a new conversation, your Rails application should send a request to the AIME Planner Lambda function with the following payload structure:

### Lambda Invocation Payload

```json
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
    "planner_id": 456,
    "event_id": 789
  }
}
```

## Data Models

### Event Metadata
```typescript
interface EventMetadata {
  name: string;                    // Event name
  dates: string[];                // Array of dates in YYYY-MM-DD format
  event_type: string;             // Type of event (e.g., "corporate retreat")
  planner_name: string;           // Event planner's name
  planner_email: string;          // Event planner's email
  planner_phone?: string;         // Optional phone number
}
```

### Vendor Information
```typescript
interface VendorInfo {
  name: string;                   // Vendor/business name
  email: string;                  // Vendor contact email
  service_type: string;           // Type of service (e.g., "hotel", "catering")
}
```

### Question
```typescript
interface Question {
  id: number;                     // Unique question identifier
  text: string;                   // Question text
  required: boolean;              // Whether answer is required
  options?: string[];             // Optional multiple choice options
  answer?: string;                // Vendor's answer (when answered)
  answered: boolean;              // Whether question has been answered
}
```

### Conversation Status Values
- `"pending"`: Conversation created but not started
- `"in_progress"`: Email sent, awaiting vendor response
- `"awaiting_response"`: Follow-up sent, still awaiting response
- `"completed"`: All required questions answered
- `"failed"`: Max attempts reached without completion
- `"cancelled"`: Conversation cancelled

## Error Handling

### Error Types
The chatbot reports the following error types:

- `"lambda_error"`: General Lambda function errors
- `"email_send_failure"`: Failed to send email to vendor
- `"llm_error"`: OpenAI/LLM service errors
- `"database_error"`: DynamoDB operation failures
- `"validation_error"`: Invalid input data
- `"api_connection_error"`: Rails API connectivity issues

### Error Context
Error reports include contextual information such as:
- `conversation_id`: Related conversation
- `vendor_email`: Target vendor email
- `attempt_count`: Number of attempts made
- `handler`: Which Lambda handler reported the error

## Retry Strategy

The AIME Planner Chatbot implements automatic retries for Rails API calls:

- **Total Retries:** 3 attempts
- **Retry Status Codes:** 429, 500, 502, 503, 504
- **Retry Methods:** HEAD, GET, OPTIONS, POST, PUT
- **Timeout:** 30 seconds per request (10 seconds for health checks)

### Backoff Strategy
The retry mechanism uses exponential backoff with jitter to avoid overwhelming your Rails API during outages.

## Implementation Notes

1. **Timestamps:** All timestamps are in ISO 8601 UTC format with 'Z' suffix
2. **Conversation IDs:** Generated by the chatbot as UUIDs
3. **Timeouts:** Set reasonable timeouts on your Rails API endpoints (< 30 seconds)
4. **Logging:** The chatbot logs all API interactions for debugging
5. **Idempotency:** Design endpoints to handle duplicate requests gracefully

## Example Rails Controller

```ruby
class Api::V1::Chatbot::ConversationUpdatesController < ApiController
  before_action :authenticate_api_key
  
  def create
    conversation_id = params[:conversation_id]
    status = params[:status]
    questions_answered = params[:questions_answered]
    
    # Update your conversation record
    conversation = Conversation.find_by(chatbot_id: conversation_id)
    conversation.update!(
      status: status,
      questions_answered: questions_answered,
      last_updated_at: Time.current
    )
    
    render json: { status: 'success' }, status: :ok
  rescue => e
    render json: { error: e.message }, status: :unprocessable_entity
  end
  
  private
  
  def authenticate_api_key
    api_key = request.headers['Authorization']&.gsub('Bearer ', '')
    unless api_key == ENV['CHATBOT_API_KEY']
      render json: { error: 'Unauthorized' }, status: :unauthorized
    end
  end
end
```

## Testing Your Integration

Use the health check endpoint to verify your Rails API is properly configured:

```bash
curl -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     https://your-api.example.com/api/v1/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00Z"
}
```
