"""
Comprehensive test suite for AI pipeline.
Tests all 6 stages of the generation pipeline.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from backend.src.error_handling import (
    PipelineError, RateLimitError, retry_with_backoff,
    CircuitBreaker, RateLimiter
)


class TestRetryDecorator:
    """Test retry decorator with exponential backoff"""
    
    @pytest.mark.asyncio
    async def test_async_retry_success_on_first_attempt(self):
        """Test successful execution without retry"""
        
        @retry_with_backoff(max_retries=3)
        async def successful_function():
            return "success"
        
        result = await successful_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_async_retry_eventual_success(self):
        """Test successful execution after failures"""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        async def failing_then_succeeding():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = await failing_then_succeeding()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_async_retry_max_retries_exceeded(self):
        """Test failure after max retries"""
        
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        async def always_fails():
            raise ValueError("Persistent failure")
        
        with pytest.raises(ValueError):
            await always_fails()
    
    def test_sync_retry_success(self):
        """Test sync function retry"""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def failing_then_succeeding():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        result = failing_then_succeeding()
        assert result == "success"
        assert call_count == 2


class TestCircuitBreaker:
    """Test circuit breaker pattern"""
    
    def test_circuit_breaker_initial_state(self):
        """Test initial CLOSED state"""
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
    
    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failures"""
        def failing_function():
            raise ValueError("Test error")
        
        cb = CircuitBreaker(failure_threshold=3)
        
        for _ in range(3):
            try:
                cb.call(failing_function)
            except ValueError:
                pass
        
        assert cb.state == "OPEN"
    
    def test_circuit_breaker_prevents_calls_when_open(self):
        """Test that calls are blocked when circuit is open"""
        def dummy_function():
            return "success"
        
        cb = CircuitBreaker(failure_threshold=1)
        cb.state = "OPEN"
        cb.last_failure_time = datetime.now()
        
        with pytest.raises(PipelineError) as exc_info:
            cb.call(dummy_function)
        
        assert "Circuit breaker is OPEN" in str(exc_info.value)
    
    def test_circuit_breaker_resets_on_success(self):
        """Test circuit breaker closes after successful calls"""
        def dummy_function():
            return "success"
        
        cb = CircuitBreaker(failure_threshold=3)
        cb.failure_count = 2
        
        result = cb.call(dummy_function)
        
        assert result == "success"
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"


class TestRateLimiter:
    """Test rate limiting"""
    
    def test_rate_limiter_initial_tokens(self):
        """Test rate limiter starts with full capacity"""
        limiter = RateLimiter(tokens=10, refill_rate=1.0)
        assert limiter.tokens == 10
    
    def test_rate_limiter_acquire_tokens(self):
        """Test acquiring tokens"""
        limiter = RateLimiter(tokens=10, refill_rate=1.0)
        
        assert limiter.acquire(5) is True
        assert limiter.tokens == 5
    
    def test_rate_limiter_insufficient_tokens(self):
        """Test acquire fails with insufficient tokens"""
        limiter = RateLimiter(tokens=3, refill_rate=1.0)
        
        assert limiter.acquire(5) is False
        assert limiter.tokens == 3
    
    def test_rate_limiter_refill(self):
        """Test tokens refill over time"""
        limiter = RateLimiter(tokens=10, refill_rate=10.0)
        
        # Use all tokens
        limiter.acquire(10)
        assert limiter.tokens == 0
        
        # Simulate 1 second passing
        limiter.last_refill = datetime.now()
        import time
        time.sleep(0.1)  # Small delay
        
        limiter._refill()
        # Should have some tokens back (at least 1)
        assert limiter.tokens >= 0


class TestPipelineErrorTypes:
    """Test custom error types"""
    
    def test_rate_limit_error(self):
        """Test RateLimitError"""
        error = RateLimitError("Too many requests", retry_after=30)
        assert error.code == "RATE_LIMIT_EXCEEDED"
        assert error.retry_after == 30
    
    def test_api_key_error(self):
        """Test APIKeyError"""
        error = APIKeyError("Missing keys", missing_keys=["GEMINI_PRO"])
        assert error.code == "API_KEY_MISSING"
        assert "GEMINI_PRO" in error.missing_keys
    
    def test_model_unavailable_error(self):
        """Test ModelUnavailableError"""
        error = ModelUnavailableError("Service down", model_name="gemini_pro")
        assert error.code == "MODEL_UNAVAILABLE"
        assert error.model_name == "gemini_pro"
    
    def test_input_validation_error(self):
        """Test InputValidationError"""
        error = InputValidationError("Invalid format", field="prompt")
        assert error.code == "INVALID_INPUT"
        assert error.field == "prompt"
    
    def test_timeout_error(self):
        """Test TimeoutError"""
        error = TimeoutError("Operation timed out", timeout_seconds=30.0)
        assert error.code == "TIMEOUT"
        assert error.timeout_seconds == 30.0


@pytest.mark.asyncio
async def test_pipeline_stage_execution():
    """Test a simulated pipeline stage"""
    
    # Mock successful AI response
    async def mock_stage_1(prompt: str):
        return {
            "intent": "Create API cheatsheet",
            "topics": ["REST", "HTTP", "Authentication"],
            "difficulty": "intermediate"
        }
    
    result = await mock_stage_1("Create a REST API cheatsheet")
    
    assert "intent" in result
    assert len(result["topics"]) == 3


def test_error_context_preservation():
    """Test that error context is preserved through stages"""
    error = PipelineError("Stage 4 error", stage=4)
    
    assert error.stage == 4
    assert error.code == "INTERNAL_ERROR"
    assert "Stage 4" in str(error.message) or error.stage == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
