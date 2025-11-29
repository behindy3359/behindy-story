from typing import Optional, Dict, Any
import time

class CacheService:
    def __init__(self):
        self._cache = {}
        self._cache_stats = {"hits": 0, "misses": 0}
    
    def get_story(self, key: str) -> Optional[Dict[str, Any]]:
        if key in self._cache:
            data, expire_time = self._cache[key]
            if time.time() < expire_time:
                self._cache_stats["hits"] += 1
                return data
            else:
                del self._cache[key]
        
        self._cache_stats["misses"] += 1
        return None
    
    def save_story(self, key: str, data: Dict[str, Any], ttl: int = 3600):
        expire_time = time.time() + ttl
        self._cache[key] = (data, expire_time)
    
    def is_healthy(self) -> bool:
        return True
    
    def get_hit_rate(self) -> float:
        """캐시 히트율"""
        total = self._cache_stats["hits"] + self._cache_stats["misses"]
        if total == 0:
            return 0.0
        return self._cache_stats["hits"] / total