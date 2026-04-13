import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any
from pathlib import Path
from tenant_context import current_tenant_id, normalize_tenant_id

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class CacheManager:
    def __init__(self):
        self.use_redis = False
        self.redis_client = None
        self.memory_cache = {}
        self.cache_ttl = {}
        
        if REDIS_AVAILABLE:
            redis_url = os.environ.get('REDIS_URL')
            if redis_url:
                try:
                    self.redis_client = redis.from_url(redis_url, decode_responses=True)
                    self.redis_client.ping()
                    self.use_redis = True
                    print("[Cache] Using Redis for caching")
                except Exception as e:
                    print(f"[Cache] Redis connection failed: {e}, falling back to memory cache")
        
        if not self.use_redis:
            print("[Cache] Using in-memory cache")
            self._cleanup_thread()
    
    def _cleanup_thread(self):
        import threading
        def cleanup():
            while True:
                time.sleep(300)
                self._cleanup_expired()
        
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
    
    def _cleanup_expired(self):
        current_time = time.time()
        expired_keys = [k for k, ttl in self.cache_ttl.items() if ttl < current_time]
        for key in expired_keys:
            self.memory_cache.pop(key, None)
            self.cache_ttl.pop(key, None)
    
    def _generate_key(self, prefix: str, identifier: str, tenant_id: str = None) -> str:
        tenant_id = normalize_tenant_id(tenant_id or current_tenant_id()) or 'legacy'
        return f"{tenant_id}:{prefix}:{hashlib.md5(identifier.encode()).hexdigest()}"

    def get(self, key: str, tenant_id: str = None) -> Optional[Any]:
        key = self._generate_key('raw', key, tenant_id)
        if self.use_redis and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                print(f"[Cache] Redis get error: {e}")
        else:
            if key in self.memory_cache:
                if key in self.cache_ttl:
                    if time.time() < self.cache_ttl[key]:
                        return self.memory_cache[key]
                    else:
                        del self.memory_cache[key]
                        del self.cache_ttl[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600, tenant_id: str = None):
        key = self._generate_key('raw', key, tenant_id)
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(value))
                return True
            except Exception as e:
                print(f"[Cache] Redis set error: {e}")
        else:
            self.memory_cache[key] = value
            self.cache_ttl[key] = time.time() + ttl
            return True
        return False
    
    def delete(self, key: str, tenant_id: str = None):
        key = self._generate_key('raw', key, tenant_id)
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                print(f"[Cache] Redis delete error: {e}")
        else:
            self.memory_cache.pop(key, None)
            self.cache_ttl.pop(key, None)
    
    def cache_youtube_transcript(self, video_id: str, transcript: str, ttl: int = 604800, tenant_id: str = None):
        key = self._generate_key("yt_transcript", video_id, tenant_id)
        self.set(key, transcript, ttl, tenant_id=tenant_id)

    def get_youtube_transcript(self, video_id: str, tenant_id: str = None) -> Optional[str]:
        key = self._generate_key("yt_transcript", video_id, tenant_id)
        return self.get(key, tenant_id=tenant_id)

    def cache_blog_post(self, content_hash: str, blog_data: dict, ttl: int = 86400, tenant_id: str = None):
        key = self._generate_key("blog_post", content_hash, tenant_id)
        self.set(key, blog_data, ttl, tenant_id=tenant_id)

    def get_cached_blog_post(self, content_hash: str, tenant_id: str = None) -> Optional[dict]:
        key = self._generate_key("blog_post", content_hash, tenant_id)
        return self.get(key, tenant_id=tenant_id)

    def cache_image(self, prompt_hash: str, image_data: str, ttl: int = 604800, tenant_id: str = None):
        key = self._generate_key("image", prompt_hash, tenant_id)
        self.set(key, image_data, ttl, tenant_id=tenant_id)

    def get_cached_image(self, prompt_hash: str, tenant_id: str = None) -> Optional[str]:
        key = self._generate_key("image", prompt_hash, tenant_id)
        return self.get(key, tenant_id=tenant_id)

    def cache_ai_response(self, prompt_hash: str, response: str, ttl: int = 3600, tenant_id: str = None):
        key = self._generate_key("ai_response", prompt_hash, tenant_id)
        self.set(key, response, ttl, tenant_id=tenant_id)

    def get_cached_ai_response(self, prompt_hash: str, tenant_id: str = None) -> Optional[str]:
        key = self._generate_key("ai_response", prompt_hash, tenant_id)
        return self.get(key, tenant_id=tenant_id)

    def clear_tenant(self, tenant_id: str):
        tenant_id = normalize_tenant_id(tenant_id or current_tenant_id()) or 'legacy'
        if self.use_redis and self.redis_client:
            try:
                keys = self.redis_client.keys(f'{tenant_id}:*')
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                print(f"[Cache] Redis tenant clear error: {e}")
        else:
            keys = [k for k in list(self.memory_cache.keys()) if k.startswith(f'{tenant_id}:')]
            for key in keys:
                self.memory_cache.pop(key, None)
                self.cache_ttl.pop(key, None)
    
    def clear_all(self):
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                print(f"[Cache] Redis flush error: {e}")
        else:
            self.memory_cache.clear()
            self.cache_ttl.clear()

_cache_manager = None

def get_cache_manager() -> CacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
