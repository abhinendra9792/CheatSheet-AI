# Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────┐
│           USER INTERFACE (React + Vite)         │
│         - Upload interface                      │
│         - Prompt input                          │
│         - Result preview                        │
└────────────────────┬────────────────────────────┘
                     │ HTTP/REST API
                     ▼
┌─────────────────────────────────────────────────┐
│        API GATEWAY (FastAPI Server)             │
│    ├─ /api/generate                             │
│    ├─ /api/analyze                              │
│    └─ /api/status                               │
└────────────────────┬────────────────────────────┘
                     │ Internal orchestration
                     ▼
┌─────────────────────────────────────────────────┐
│      AI PIPELINE ORCHESTRATOR                   │
│   Coordinates 6-stage pipeline execution        │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │ Stage  │  │ Stage  │  │ Stage  │
    │ 1,4,5  │  │ 2,3    │  │ 6      │
    │ Gemini │  │ Nano & │  │ Imagen │
    │ Pro    │  │Research│  │ 4      │
    └────────┘  └────────┘  └────────┘
        │            │            │
        └────────────┼────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│        OUTPUT ASSEMBLY                          │
│   ├─ PDF Generation                             │
│   ├─ HTML Rendering                             │
│   └─ PNG Export                                 │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│   FILE STORAGE & DELIVERY                       │
│   ├─ /outputs/ directory                        │
│   └─ HTTP download endpoint                     │
└─────────────────────────────────────────────────┘
```

## Component Details

### Frontend (React 19 + Vite)

**Key Components:**
- `App.jsx` - Main application shell
- `InputForm.jsx` - User input interface
- `Preview.jsx` - Live preview panel
- `DownloadButton.jsx` - Export functionality
- `StatusIndicator.jsx` - Pipeline status display

**Features:**
- Dual input modes (text/image)
- Real-time preview
- Format selection
- Progress tracking
- Error handling

### Backend API (FastAPI)

**Endpoints:**
- `POST /api/generate` - Generate cheatsheet from prompt
- `POST /api/analyze` - Analyze uploaded image
- `GET /api/status/{request_id}` - Check pipeline status
- `GET /api/download/{file_id}` - Download generated cheatsheet
- `GET /docs` - Auto-generated API documentation

### AI Pipeline

**6-Stage Architecture:**

**Stage 1: User Intent Analysis** (Gemini Pro)
- Input: Text prompt
- Process: Extract key concepts, topics, difficulty level
- Output: Structured intent object

**Stage 2: Image Analysis** (Gemini Nano Banana)
- Input: Uploaded image (if provided)
- Process: OCR, design extraction, content analysis
- Output: Identified topics, design patterns, existing content

**Stage 3: Trend Analysis** (Deep Research Pro)
- Input: Topics identified in Stages 1-2
- Process: Analyze latest trends, best practices
- Output: Enhanced topic context, modern approaches

**Stage 4: Prompt Engineering** (Gemini Pro)
- Input: Intent + Trend analysis
- Process: Build optimized prompts with examples
- Output: Fine-tuned prompts for Stage 5

**Stage 5: Content Generation** (Gemini Pro)
- Input: Optimized prompts
- Process: Generate cheatsheet content
- Output: Structured markdown/HTML content

**Stage 6: Image Synthesis** (Imagen 4 Ultra)
- Input: Design specifications
- Process: Generate visual elements
- Output: High-quality PNG/SVG graphics

## Data Flow

```
User Input (text/image)
    ↓
REST API Request
    ↓
Pipeline Orchestrator
    ├─ Load configuration
    ├─ Initialize AI clients
    └─ Begin stage execution
    ↓
Stage 1: Intent Analysis → JSON structure
    ↓
Stage 2: Image Analysis → Design patterns
    ↓
Stage 3: Trend Analysis → Current context
    ↓
Stage 4: Prompt Engineering → Optimized prompts
    ↓
Stage 5: Content Generation → Formatted content
    ↓
Stage 6: Image Synthesis → Visual assets
    ↓
Output Assembly
    ├─ Combine content + images
    ├─ Apply formatting
    └─ Export to multiple formats
    ↓
Store & Serve
    ├─ Save to /outputs/
    └─ Return download link
```

## Deployment Architecture

### Development Environment
- Local Python environment
- FastAPI development server
- Vite development server
- Direct file storage

### Production Environment
- Docker containers
- Kubernetes orchestration (optional)
- CDN for static assets
- Cloud storage for cheatsheets
- Load balancer for API
- Database for metadata

## Error Handling & Resilience

**API Key Fallback Chain:**
- Primary model → Fallback 1 → Fallback 2 → Error

**Rate Limiting:**
- Per-user quota tracking
- Request queuing
- Exponential backoff retry

**Caching:**
- Prompt caching (5-minute TTL)
- Response caching (1-hour TTL)
- Image caching (permanent)

**Monitoring:**
- Request logging
- Performance metrics
- Error tracking
- API quota monitoring

## Security Considerations

1. **API Key Management**
   - Environment variables only
   - No hardcoded secrets
   - Key rotation support

2. **Input Validation**
   - Prompt length limits
   - File size restrictions
   - Content filtering

3. **Output Validation**
   - Schema validation
   - Content sanitization
   - Safe file export

4. **Rate Limiting**
   - Per-IP throttling
   - User-based quotas
   - DDoS protection

## Performance Optimization

1. **Caching**
   - Response caching (Gemini outputs)
   - Image caching (generated assets)
   - Prompt template caching

2. **Parallelization**
   - Concurrent API calls
   - Batch image generation
   - Async I/O operations

3. **Model Selection**
   - Use Flash-lite for cost
   - Use Pro for quality
   - Intelligent fallback

4. **Resource Management**
   - Connection pooling
   - Memory limits
   - Timeout configuration

## Scalability Considerations

1. **Horizontal Scaling**
   - Load balancer
   - Multiple API instances
   - Shared file storage

2. **Queue System**
   - Process long-running requests asynchronously
   - Redis queue for job management
   - Worker pool for pipeline execution

3. **Database**
   - Store metadata (request history)
   - Track API quota usage
   - User analytics

4. **CDN Integration**
   - Serve generated cheatsheets
   - Cache popular outputs
   - Reduce bandwidth costs
