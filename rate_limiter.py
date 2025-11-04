import os
import time
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class RateLimiter:
    def __init__(self):
        self.use_redis = False
        self.redis_client = None
        self.memory_store = defaultdict(list)
        self.lock = Lock()
        
        if REDIS_AVAILABLE:
            redis_url = os.environ.get('REDIS_URL')
            if redis_url:
                try:
                    self.redis_client = redis.from_url(redis_url)
                    self.redis_client.ping()
                    self.use_redis = True
                    print("[RateLimit] Using Redis for rate limiting")
                except Exception as e:
                    print(f"[RateLimit] Redis connection failed: {e}, using memory store")
        
        if not self.use_redis:
            print("[RateLimit] Using in-memory rate limiting")
    
    def _cleanup_old_requests(self, requests: list, window: int) -> list:
        current_time = time.time()
        return [req_time for req_time in requests if current_time - req_time < window]
    
    def check_rate_limit(self, user_id: str, endpoint: str, max_requests: int = 10, window: int = 60) -> tuple:
        key = f"rate_limit:{user_id}:{endpoint}"
        current_time = time.time()
        
        if self.use_redis and self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.zadd(key, {str(current_time): current_time})
                pipe.zremrangebyscore(key, 0, current_time - window)
                pipe.zcard(key)
                pipe.expire(key, window)
                results = pipe.execute()
                
                request_count = results[2]
                
                if request_count > max_requests:
                    retry_after = window
                    return False, retry_after, request_count
                
                return True, 0, request_count
            except Exception as e:
                print(f"[RateLimit] Redis error: {e}, allowing request")
                return True, 0, 0
        else:
            with self.lock:
                self.memory_store[key] = self._cleanup_old_requests(self.memory_store[key], window)
                
                request_count = len(self.memory_store[key])
                
                if request_count >= max_requests:
                    oldest_request = min(self.memory_store[key])
                    retry_after = int(window - (current_time - oldest_request))
                    return False, retry_after, request_count
                
                self.memory_store[key].append(current_time)
                return True, 0, request_count + 1
    
    def get_usage_stats(self, user_id: str, endpoint: str, window: int = 60) -> dict:
        key = f"rate_limit:{user_id}:{endpoint}"
        current_time = time.time()
        
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.zremrangebyscore(key, 0, current_time - window)
                count = self.redis_client.zcard(key)
                return {'requests': count, 'window': window}
            except Exception as e:
                print(f"[RateLimit] Redis stats error: {e}")
                return {'requests': 0, 'window': window}
        else:
            with self.lock:
                self.memory_store[key] = self._cleanup_old_requests(self.memory_store[key], window)
                return {'requests': len(self.memory_store[key]), 'window': window}
    
    def reset_user_limits(self, user_id: str):
        if self.use_redis and self.redis_client:
            try:
                pattern = f"rate_limit:{user_id}:*"
                for key in self.redis_client.scan_iter(pattern):
                    self.redis_client.delete(key)
            except Exception as e:
                print(f"[RateLimit] Redis reset error: {e}")
        else:
            with self.lock:
                keys_to_delete = [k for k in self.memory_store.keys() if k.startswith(f"rate_limit:{user_id}:")]
                for key in keys_to_delete:
                    del self.memory_store[key]

_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
