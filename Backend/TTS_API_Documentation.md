# Text-to-Speech API Documentation

The IT HelpDesk Chatbot now includes text-to-speech functionality. Here are the available endpoints:

## Speech API Endpoints

### 1. POST `/text-to-speech`
Convert text to speech and return status.

**Request Body:**
```json
{
    "text": "Hello, this is a test message",
    "language": "en"  // "en" for English, "vn" for Vietnamese
}
```

**Response:**
```json
{
    "success": true,
    "message": "Speech generated successfully",
    "audio_url": null
}
```

### 2. POST `/text-to-speech/audio`
Convert text to speech and return audio file as download.

**Request Body:**
```json
{
    "text": "Hello, this is a test message",
    "language": "en"
}
```

**Response:** WAV audio file download

### 3. POST `/text-to-speech/stream`
Convert text to speech and return audio as stream.

**Request Body:**
```json
{
    "text": "Hello, this is a test message", 
    "language": "en"
}
```

**Response:** Streaming WAV audio

### 4. GET `/speech/models`
Get list of available speech models.

**Response:**
```json
{
    "models": [
        {
            "language": "en",
            "name": "English TTS",
            "model_id": "facebook/mms-tts-eng"
        },
        {
            "language": "vn",
            "name": "Vietnamese TTS", 
            "model_id": "facebook/mms-tts-vie"
        }
    ]
}
```

### 5. GET `/audio/{filename}`
Serve generated audio files.

**Response:** WAV audio file

## Enhanced Chat API

The `/chat` endpoint now supports text-to-speech:

**Request Body:**
```json
{
    "message": "Help me reset my password",
    "conversation_id": "optional-conversation-id",
    "file_ids": [],
    "enable_tts": true,        // Enable text-to-speech
    "tts_language": "en"       // TTS language: "en" or "vn"
}
```

**Response:**
```json
{
    "response": "I can help you reset your password...",
    "conversation_id": "conversation-uuid",
    "function_calls": [],
    "has_audio": true,         // Whether audio was generated
    "audio_url": "/audio/speech_uuid_12345678.wav"  // URL to audio file
}
```

## Usage Examples

### Frontend Integration

```javascript
// Enable TTS in chat request
const chatRequest = {
    message: userMessage,
    conversation_id: conversationId,
    enable_tts: true,
    tts_language: "en"
};

const response = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(chatRequest)
});

const data = await response.json();

// Play audio if available
if (data.has_audio && data.audio_url) {
    const audio = new Audio(data.audio_url);
    audio.play();
}
```

### Direct TTS API Usage

```javascript
// Convert text to speech directly
const ttsRequest = {
    text: "Welcome to IT HelpDesk support",
    language: "en"
};

const response = await fetch('/text-to-speech/audio', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ttsRequest)
});

// Get audio blob and play
const audioBlob = await response.blob();
const audioUrl = URL.createObjectURL(audioBlob);
const audio = new Audio(audioUrl);
audio.play();
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `400` - Bad request (e.g., empty text)
- `404` - Audio file not found
- `500` - Server error (e.g., model loading failed)

Error responses include detailed messages:
```json
{
    "detail": "Failed to load speech model for language: vn"
}
```

## Performance Notes

- Speech models are cached in memory after first load
- Audio files are temporarily stored in `temp_audio/` directory
- Large text inputs may take longer to process
- Consider implementing audio file cleanup for production use
