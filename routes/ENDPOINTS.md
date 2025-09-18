## API Endpoints

### Chat

#### POST `/api/chat`
- **Description**: Send a chat message to the ClimeAI agent; message and response are saved to history.
- **Request body**:
```json
{
  "user_id": "string",
  "message": "string"
}
```
- **Response 200**:
```json
{
  "response": "string"
}
```
- **Response 500**:
```json
{
  "error": "We are facing an error. Please try again later."
}
```

#### GET `/api/chatHistory/{user_id}`
- **Description**: Retrieve a user's chat history (most recent first).
- **Path params**: `user_id: string`
- **Response 200**:
```json
{
  "history": [
    { "role": "user", "content": "string" },
    { "role": "bot", "content": "string" }
  ]
}
```
- **Response 500**:
```json
{
  "error": "We are facing an error. Please try again later."
}
```

#### DELETE `/api/chat`
- **Description**: Clear a user’s chat history, archive it, and remove graph checkpoints.
- **Request body**:
```json
{
  "user_id": "string"
}
```
- **Response 200**:
```json
{ "message": "Chat history reset successfully." }
```
- **Response 200 (already empty)**:
```json
{ "message": "Chat history is already reset" }
```
- **Response 404**:
```json
{ "message": "User chat history not found" }
```
- **Response 500**:
```json
{
  "error": "We are facing an error. Please try again later."
}
```

### Event Advisor

#### POST `/api/event-advisor`
- **Description**: Weather-aware advice for an event time window at a location.
- **Request body**:
```json
{
  "longitude": 73.0923,
  "latitude": 31.4221,
  "from_time": "2025-09-21T17:00:00Z",
  "to_time": "2025-09-21T20:00:00Z",
  "event_type": "outdoor",
  "event_details": "string"
}
```
- **Response 200**:
```json
{ "advice": "string" }
```
- **Response 500**:
```json
{
  "error": "Unable to get event advice.",
  "details": "string"
}
```

### Travel Advisor

#### POST `/api/travel-advisor`
- **Description**: Travel guidance using weather at origin (departure time) and destination (arrival time).
- **Request body**:
```json
{
  "from_longitude": 74.3587,
  "from_latitude": 31.5204,
  "to_longitude": 73.0479,
  "to_latitude": 33.6844,
  "from_time": "2025-09-21T06:30:00Z",
  "to_time": "2025-09-21T10:30:00Z",
  "vehicle_type": "car",
  "travel_details": "string"
}
```
- **Response 200**:
```json
{ "advice": "string" }
```
- **Response 500**:
```json
{
  "error": "Unable to get travel advice.",
  "details": "string"
}
```

### Health Checks

#### GET `/api/chat`
- **Description**: Health check endpoint.
- **Response 200**:
```json
"API is working"
```

#### GET `/`
- **Description**: Root health check.
- **Response 200**:
```json
"API is working"
```
