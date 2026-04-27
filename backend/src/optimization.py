"""
AI Pipeline Optimization Layer
Implements caching, model selection, and performance improvements.
Generated: April 2025
"""

import hashlib
import json
from typing import Any, Optional, Callable, Dict, List
from datetime import datetime, timedelta
from functools import wraps
import asyncio


class PromptCache:
    """
    Intelligent prompt caching system.
    Reduces API calls and costs by caching similar prompts.
    """
    
    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds
        self.max_entries = max_entries
    
    def _hash_prompt(self, prompt: str) -> str:
        """Generate hash for prompt"""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]
    
    def get(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached response"""
        key = self._hash_prompt(prompt)
        
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if datetime.now() > entry["expires"]:
            del self.cache[key]
            return None
        
        entry["hits"] += 1
        return entry["response"]
    
    def set(self, prompt: str, response: Dict[str, Any]):
        """Store response in cache"""
        if len(self.cache) >= self.max_entries:
            # Remove least recently used entry
            self._evict_lru()
        
        key = self._hash_prompt(prompt)
        self.cache[key] = {
            "response": response,
            "expires": datetime.now() + timedelta(seconds=self.ttl),
            "created": datetime.now(),
            "hits": 0
        }
    
    def _evict_lru(self):
        """Remove least recently used entry"""
        if not self.cache:
            return
        
        # Find entry with least hits
        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k]["hits"])
        del self.cache[lru_key]
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_hits = sum(entry["hits"] for entry in self.cache.values())
        return {
            "entries": len(self.cache),
            "capacity": self.max_entries,
            "total_hits": total_hits,
            "ttl_seconds": self.ttl
        }


class ModelSelector:
    """
    Intelligent model selection based on task requirements.
    Optimizes for cost, latency, or quality.
    """
    
    def __init__(self):
        # Model configurations: (cost, latency, quality, quota)
        self.models = {
            "gemini_pro": {
                "cost": 0.015,
                "latency": 1.5,
                "quality": 0.95,
                "quota_per_minute": 1500,
                "best_for": ["complex_reasoning", "high_quality_content"]
            },
            "gemini_2.0_flash": {
                "cost": 0.01,
                "latency": 0.8,
                "quality": 0.90,
                "quota_per_minute": 1500,
                "best_for": ["speed", "cost_optimization"]
            },
            "gemini_2.0_flash_lite": {
                "cost": 0.005,
                "latency": 0.5,
                "quality": 0.80,
                "quota_per_minute": 3000,
                "best_for": ["high_volume", "budget_conscious"]
            },
            "gemini_nano": {
                "cost": 0.002,
                "latency": 0.3,
                "quality": 0.75,
                "quota_per_minute": 600,
                "best_for": ["image_analysis", "lightweight_tasks"]
            }
        }
    
    def select_model(
        self,
        task_type: str,
        optimization: str = "balanced"  # cost, speed, quality, balanced
    ) -> str:
        """
        Select best model for task.
        
        Args:
            task_type: Type of task (e.g., "content_generation", "image_analysis")
            optimization: Optimization strategy
        
        Returns:
            Model name
        """
        if optimization == "cost":
            return "gemini_2.0_flash_lite"
        elif optimization == "speed":
            return "gemini_2.0_flash"
        elif optimization == "quality":
            return "gemini_pro"
        else:  # balanced
            return "gemini_2.0_flash"
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get model configuration"""
        return self.models.get(model, {})


class PipelineOptimizer:
    """Optimizes pipeline execution"""
    
    def __init__(self):
        self.cache = PromptCache()
        self.selector = ModelSelector()
        self.execution_times: Dict[int, List[float]] = {}  # stage -> times
    
    async def optimize_stage_execution(
        self,
        stage: int,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute stage with optimization"""
        
        # Try cache for applicable stages
        if stage in [1, 4]:  # Intent analysis, prompt engineering
            cache_key = str(args[0]) if args else ""
            cached_result = self.cache.get(cache_key)
            if cached_result:
                return cached_result
        
        # Execute function
        start_time = datetime.now()
        result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        duration = (datetime.now() - start_time).total_seconds()
        
        # Record timing
        if stage not in self.execution_times:
            self.execution_times[stage] = []
        self.execution_times[stage].append(duration)
        
        # Cache result for applicable stages
        if stage in [1, 4]:
            cache_key = str(args[0]) if args else ""
            self.cache.set(cache_key, result)
        
        return result
    
    def get_stage_statistics(self, stage: int) -> Dict[str, Any]:
        """Get execution statistics for a stage"""
        times = self.execution_times.get(stage, [])
        if not times:
            return {"stage": stage, "samples": 0}
        
        import statistics
        return {
            "stage": stage,
            "samples": len(times),
            "avg": statistics.mean(times),
            "min": min(times),
            "max": max(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0
        }
    
    def get_all_statistics(self) -> Dict[str, Any]:
        """Get all execution statistics"""
        return {
            "cache_stats": self.cache.get_stats(),
            "stage_stats": [
                self.get_stage_statistics(stage)
                for stage in sorted(self.execution_times.keys())
            ]
        }


class BatchProcessor:
    """
    Process multiple requests efficiently.
    Implements batching and concurrent processing.
    """
    
    def __init__(self, batch_size: int = 10, max_concurrent: int = 5):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.queue: List[Dict[str, Any]] = []
    
    async def process_batch(self, items: List[Any], processor: Callable):
        """Process items in batches"""
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            
            # Process concurrently within batch
            batch_results = await asyncio.gather(
                *[processor(item) for item in batch[:self.max_concurrent]],
                return_exceptions=True
            )
            results.extend(batch_results)
        
        return results


def cache_result(ttl_seconds: int = 3600):
    """Decorator for caching function results"""
    cache = PromptCache(ttl_seconds=ttl_seconds)
    
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key from args
            cache_key = json.dumps({
                "func": func.__name__,
                "args": str(args),
                "kwargs": str(kwargs)
            })
            
            # Check cache
            cached = cache.get(cache_key)
            if cached:
                return cached
            
            # Execute and cache
            result = await func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = json.dumps({
                "func": func.__name__,
                "args": str(args),
                "kwargs": str(kwargs)
            })
            
            cached = cache.get(cache_key)
            if cached:
                return cached
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# Global optimizer instance
pipeline_optimizer = PipelineOptimizer()
batch_processor = BatchProcessor()
