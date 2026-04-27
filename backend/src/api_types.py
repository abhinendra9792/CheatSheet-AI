"""
Enhanced API response types and schemas for better type safety and validation.
Generated: April 2025
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OutputFormat(str, Enum):
    """Supported output formats"""
    HTML = "html"
    PDF = "pdf"
    PNG = "png"
    MARKDOWN = "markdown"
    JSON = "json"


class PipelineStage(str, Enum):
    """Pipeline execution stages"""
    STAGE_1_INTENT_ANALYSIS = "stage_1"
    STAGE_2_IMAGE_ANALYSIS = "stage_2"
    STAGE_3_TREND_ANALYSIS = "stage_3"
    STAGE_4_PROMPT_ENGINEERING = "stage_4"
    STAGE_5_CONTENT_GENERATION = "stage_5"
    STAGE_6_IMAGE_SYNTHESIS = "stage_6"


class GenerationStatus(str, Enum):
    """Status of generation request"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StageProgress:
    """Progress information for a single pipeline stage"""
    stage: PipelineStage
    status: GenerationStatus
    duration: float
    start_time: datetime
    end_time: Optional[datetime]
    error: Optional[str] = None
    retry_count: int = 0
    tokens_used: Optional[int] = None


@dataclass
class GenerateRequest:
    """Request to generate a cheatsheet"""
    prompt: str
    title: Optional[str] = None
    format: OutputFormat = OutputFormat.HTML
    no_image: bool = False
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GenerateResponse:
    """Response from generation request"""
    status: GenerationStatus
    request_id: str
    file_id: Optional[str] = None
    download_url: Optional[str] = None
    preview_url: Optional[str] = None
    created_at: datetime = None
    format: OutputFormat = OutputFormat.HTML
    processing_time: Optional[float] = None
    error: Optional[str] = None


@dataclass
class PipelineStatus:
    """Current pipeline execution status"""
    request_id: str
    current_stage: int  # 0-6
    total_stages: int = 6
    percentage: float = 0.0
    estimated_completion: int  # seconds
    stages: List[StageProgress] = None
    started_at: datetime = None
    current_model: Optional[str] = None
    tokens_used: int = 0


@dataclass
class ImageAnalysisRequest:
    """Request to analyze an image"""
    analysis_type: str = "basic"  # basic or comprehensive
    extract_text: bool = True
    identify_design: bool = True
    suggest_improvements: bool = True


@dataclass
class ImageAnalysisResponse:
    """Response from image analysis"""
    topics: List[str]
    design_elements: Dict[str, Any]
    content_summary: str
    suggestions: List[str]
    extracted_text: Optional[str] = None
    design_patterns: Optional[List[str]] = None
    analysis_confidence: float = 0.0


@dataclass
class HealthStatus:
    """API health status"""
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    api_version: str
    dependencies: Dict[str, str]  # dependency -> status
    quota: Dict[str, Dict[str, Any]]
    uptime: float  # seconds


@dataclass
class CheatsheetMetadata:
    """Metadata for a generated cheatsheet"""
    file_id: str
    title: str
    prompt: str
    created_at: datetime
    format: OutputFormat
    size_bytes: int
    download_count: int = 0
    tags: List[str] = None
    ai_models_used: List[str] = None


# Error response types

@dataclass
class ErrorResponse:
    """Standard error response"""
    status: str = "error"
    code: str = None
    message: str = None
    details: Dict[str, Any] = None
    timestamp: datetime = None


class ErrorCode(str, Enum):
    """Standard error codes"""
    INVALID_INPUT = "INVALID_INPUT"
    PROMPT_TOO_LONG = "PROMPT_TOO_LONG"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    API_KEY_MISSING = "API_KEY_MISSING"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TIMEOUT = "TIMEOUT"
    INVALID_IMAGE = "INVALID_IMAGE"
