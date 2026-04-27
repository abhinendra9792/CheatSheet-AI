# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently no authentication. In production, implement JWT/API key auth.

---

## Endpoints

### 1. Generate Cheatsheet from Prompt

**Endpoint:** `POST /api/generate`

**Description:** Generate a new cheatsheet from a text prompt

**Request Body:**
```json
{
  "prompt": "REST API Design Principles",
  "title": "REST API Cheatsheet",
  "format": "html",
  "no_image": false
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| prompt | string | Yes | Topic/prompt for cheatsheet |
| title | string | No | Custom title (auto-generated if not provided) |
| format | string | No | Output format: `html`, `pdf`, `png` (default: `html`) |
| no_image | boolean | No | Skip image generation (default: false) |

**Response (Success - 200):**
```json
{
  "status": "success",
  "request_id": "req_12345",
  "file_id": "file_67890",
  "download_url": "/api/download/file_67890",
  "preview_url": "/api/preview/file_67890",
  "created_at": "2025-04-27T12:34:56Z",
  "format": "html"
}
```

**Response (Processing - 202):**
```json
{
  "status": "processing",
  "request_id": "req_12345",
  "estimated_time": 25
}
```

**Response (Error - 400/500):**
```json
{
  "status": "error",
  "message": "Invalid prompt length",
  "code": "INVALID_INPUT"
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Python async programming",
    "title": "Async/Await Guide",
    "format": "html"
  }'
```

---

### 2. Analyze Cheatsheet Image

**Endpoint:** `POST /api/analyze`

**Description:** Analyze an uploaded cheatsheet image and suggest improvements

**Request:**
- Content-Type: `multipart/form-data`
- `image`: File upload (PNG, JPG, JPEG)
- `analysis_type`: `basic` or `comprehensive` (optional, default: `basic`)

**Response (Success - 200):**
```json
{
  "status": "success",
  "analysis": {
    "topics": ["REST", "HTTP", "API Design"],
    "design_elements": {
      "colors": ["#0066CC", "#FFFFFF", "#333333"],
      "typography": ["Arial", "Courier New"],
      "layout": "grid-based"
    },
    "content_summary": "REST API best practices...",
    "suggestions": [
      "Add more code examples",
      "Include rate limiting info",
      "Add error handling section"
    ]
  },
  "analyzed_at": "2025-04-27T12:34:56Z"
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "image=@cheatsheet.png" \
  -F "analysis_type=comprehensive"
```

---

### 3. Get Pipeline Status

**Endpoint:** `GET /api/status/{request_id}`

**Description:** Get current status of a generation request

**Response (Success - 200):**
```json
{
  "status": "processing",
  "request_id": "req_12345",
  "progress": {
    "current_stage": 4,
    "total_stages": 6,
    "percentage": 67
  },
  "stage_details": {
    "1": { "status": "completed", "duration": "2.3s" },
    "2": { "status": "completed", "duration": "1.8s" },
    "3": { "status": "completed", "duration": "3.2s" },
    "4": { "status": "in_progress", "duration": "2.1s" },
    "5": { "status": "pending", "duration": "-" },
    "6": { "status": "pending", "duration": "-" }
  },
  "estimated_completion": 25
}
```

**Example cURL:**
```bash
curl http://localhost:8000/api/status/req_12345
```

---

### 4. Download Generated Cheatsheet

**Endpoint:** `GET /api/download/{file_id}`

**Description:** Download the generated cheatsheet

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| format | string | Override format (html, pdf, png) |

**Response:**
- Returns file with appropriate Content-Type header
- Filename in Content-Disposition header

**Example cURL:**
```bash
curl http://localhost:8000/api/download/file_67890 -o cheatsheet.html
```

---

### 5. Preview Cheatsheet

**Endpoint:** `GET /api/preview/{file_id}`

**Description:** Get HTML preview of generated cheatsheet

**Response:**
- HTML content for browser display

**Example:**
```bash
curl http://localhost:8000/api/preview/file_67890
```

---

### 6. List Generated Cheatsheets

**Endpoint:** `GET /api/cheatsheets`

**Description:** List all generated cheatsheets

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | integer | 0 | Number to skip (pagination) |
| limit | integer | 10 | Items per page |
| sort | string | date | Sort by: `date`, `title`, `popularity` |

**Response (Success - 200):**
```json
{
  "status": "success",
  "total": 150,
  "items": [
    {
      "file_id": "file_67890",
      "title": "REST API Cheatsheet",
      "prompt": "REST API Design Principles",
      "created_at": "2025-04-27T12:34:56Z",
      "format": "html",
      "download_url": "/api/download/file_67890"
    }
  ],
  "pagination": {
    "skip": 0,
    "limit": 10,
    "total": 150
  }
}
```

**Example cURL:**
```bash
curl "http://localhost:8000/api/cheatsheets?limit=5&sort=date"
```

---

### 7. Delete Cheatsheet

**Endpoint:** `DELETE /api/cheatsheets/{file_id}`

**Description:** Delete a generated cheatsheet

**Response (Success - 204):**
No content

**Example cURL:**
```bash
curl -X DELETE http://localhost:8000/api/cheatsheets/file_67890
```

---

### 8. Health Check

**Endpoint:** `GET /api/health`

**Description:** Check API and pipeline health

**Response (Success - 200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-04-27T12:34:56Z",
  "api_version": "1.0.0",
  "dependencies": {
    "gemini_pro": "connected",
    "gemini_nano": "connected",
    "deep_research": "connected",
    "imagen_4": "connected"
  },
  "quota": {
    "gemini_pro": { "used": 250, "limit": 1500, "percentage": 16.7 },
    "gemini_nano": { "used": 100, "limit": 600, "percentage": 16.7 },
    "imagen_4": { "used": 50, "limit": 600, "percentage": 8.3 }
  }
}
```

**Example cURL:**
```bash
curl http://localhost:8000/api/health
```

---

## Error Handling

### Error Response Format
```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "stage": 4,
    "timestamp": "2025-04-27T12:34:56Z"
  }
}
```

### Common Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| INVALID_INPUT | 400 | Invalid request parameters |
| PROMPT_TOO_LONG | 400 | Prompt exceeds max length |
| UNSUPPORTED_FORMAT | 400 | Unsupported output format |
| API_KEY_MISSING | 500 | API key not configured |
| MODEL_UNAVAILABLE | 503 | AI model temporarily unavailable |
| RATE_LIMIT_EXCEEDED | 429 | Rate limit exceeded |
| INTERNAL_ERROR | 500 | Unexpected server error |

---

## Rate Limiting

**Limits (per minute):**
- 10 requests per IP for generation
- 20 requests per IP for analysis
- 100 requests per IP for other endpoints

**Headers:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1682428800
```

---

## WebSocket (Future Enhancement)

Real-time pipeline status updates via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/status/req_12345');

ws.onmessage = (event) => {
  const status = JSON.parse(event.data);
  console.log(`Stage ${status.stage}/6: ${status.message}`);
};
```

---

## Pagination

List endpoints support pagination:

```bash
# First page
curl "http://localhost:8000/api/cheatsheets?skip=0&limit=10"

# Next page
curl "http://localhost:8000/api/cheatsheets?skip=10&limit=10"
```

---

## CORS Headers

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, DELETE
Access-Control-Allow-Headers: Content-Type
```

---

## Changelog

### v1.0.0 (Current)
- Initial release
- 6-stage pipeline
- HTML/PDF/PNG export
- Image analysis
- Real-time status

### v1.1.0 (Planned)
- WebSocket support
- Batch API
- Advanced caching
- Usage analytics

---

## Support

For API issues:
1. Check `/api/health`
2. Review server logs
3. Verify API keys
4. Check rate limits
5. Open GitHub issue

---

Last Updated: April 2025
