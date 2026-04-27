"""
Enhanced error handling and retry logic for AI pipeline.
Implements exponential backoff and graceful degradation.
Generated: April 2025
"""

import asyncio
import logging
from typing import Callable, TypeVar, Optional, Any
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')


class PipelineError(Exception):
    """Base exception for pipeline errors"""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", stage: Optional[int] = None):
        self.message = message
        self.code = code
        self.stage = stage
        super().__init__(message)


class APIKeyError(PipelineError):
    """API key configuration error"""
    def __init__(self, message: str, missing_keys: list = None):
        self.missing_keys = missing_keys or []
        super().__init__(message, code="API_KEY_MISSING")


class RateLimitError(PipelineError):
    """Rate limit exceeded error"""
    def __init__(self, message: str, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message, code="RATE_LIMIT_EXCEEDED")


class ModelUnavailableError(PipelineError):
    """AI model temporarily unavailable"""
    def __init__(self, message: str, model_name: str = None):
        self.model_name = model_name
        super().__init__(message, code="MODEL_UNAVAILABLE")


class InputValidationError(PipelineError):
    """Input validation error"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, code="INVALID_INPUT")


class TimeoutError(PipelineError):
    """Operation timeout error"""
    def __init__(self, message: str, timeout_seconds: float = None):
        self.timeout_seconds = timeout_seconds
        super().__init__(message, code="TIMEOUT")


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retriable_exceptions: tuple = (Exception,)
):
    """
    Retry decorator with exponential backoff and jitter.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Add random jitter to avoid thundering herd
        retriable_exceptions: Tuple of exception types to retry on
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retriable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Failed after {max_retries} retries: {str(e)}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter if enabled
                    if jitter:
                        import random
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retriable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Failed after {max_retries} retries: {str(e)}")
                        raise
                    
                    # Calculate delay
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    if jitter:
                        import random
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    import time
                    time.sleep(delay)
            
            raise last_exception
        
        # Return async wrapper if function is async, else sync wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for AI API calls.
    Prevents cascading failures by temporarily disabling calls to failing services.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise PipelineError(
                    f"Circuit breaker is OPEN. Service unavailable. "
                    f"Retry in {self._time_until_retry()}s",
                    code="SERVICE_UNAVAILABLE"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if recovery timeout has elapsed"""
        if self.last_failure_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def _time_until_retry(self) -> int:
        """Calculate seconds until retry should be attempted"""
        if self.last_failure_time is None:
            return 0
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return max(0, int(self.recovery_timeout - elapsed))


class RateLimiter:
    """Token bucket rate limiter for API quotas"""
    
    def __init__(self, tokens: int, refill_rate: float):
        """
        Args:
            tokens: Initial token count
            refill_rate: Tokens per second
        """
        self.capacity = tokens
        self.tokens = tokens
        self.refill_rate = refill_rate
        self.last_refill = datetime.now()
    
    def acquire(self, tokens: int = 1) -> bool:
        """Check if tokens are available"""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = datetime.now()
        elapsed = (now - self.last_refill).total_seconds()
        self.tokens = min(
            self.capacity,
            self.tokens + (elapsed * self.refill_rate)
        )
        self.last_refill = now


# Global circuit breakers per model
circuit_breakers = {
    "gemini_pro": CircuitBreaker(failure_threshold=3, recovery_timeout=30),
    "gemini_nano": CircuitBreaker(failure_threshold=3, recovery_timeout=30),
    "imagen_4": CircuitBreaker(failure_threshold=5, recovery_timeout=60),
}


def handle_pipeline_error(error: Exception, stage: int) -> PipelineError:
    """Convert various exceptions to PipelineError with context"""
    
    if isinstance(error, PipelineError):
        error.stage = stage
        return error
    
    if "rate limit" in str(error).lower():
        return RateLimitError(str(error), stage=stage)
    
    if "timeout" in str(error).lower():
        return TimeoutError(str(error), stage=stage)
    
    if "unavailable" in str(error).lower() or "offline" in str(error).lower():
        return ModelUnavailableError(str(error), stage=stage)
    
    return PipelineError(str(error), stage=stage)
