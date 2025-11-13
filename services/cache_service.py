"""
캐싱 서비스 (추후 Redis 연동)
"""
from typing import Optional, Dict, Any
import time

class CacheService:
    def __init__(self):
        # 메모리 기반 임시 캐시 (추후 Redis로 교체)
        self._cache = {}
        self._cache_stats = {"hits": 0, "misses": 0}
    
    def get_story(self, key: str) -> Optional[Dict[str, Any]]:
        """캐시에서 스토리 조회"""
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
        """캐시에 스토리 저장"""
        expire_time = time.time() + ttl
        self._cache[key] = (data, expire_time)
    
    def is_healthy(self) -> bool:
        """캐시 서비스 상태"""
        return True
    
    def get_hit_rate(self) -> float:
        """캐시 히트율"""
        total = self._cache_stats["hits"] + self._cache_stats["misses"]
        if total == 0:
            return 0.0
        return self._cache_stats["hits"] / total