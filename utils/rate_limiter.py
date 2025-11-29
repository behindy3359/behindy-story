"""
요청 제한 서비스
"""

import time
from typing import Dict
from fastapi import HTTPException

class RateLimiter:
    def __init__(self):
        self._requests = {}
        self._total_requests = 0

    def check_rate_limit(self, client_ip: str = "default") -> bool:
        """요청 제한 체크"""
        current_time = time.time()
        hour_ago = current_time - 3600

        if client_ip in self._requests:
            self._requests[client_ip] = [
                req_time for req_time in self._requests[client_ip]
                if req_time > hour_ago
            ]
        else:
            self._requests[client_ip] = []

        if len(self._requests[client_ip]) >= 100:
            raise HTTPException(
                status_code=429,
                detail="시간당 요청 제한을 초과했습니다."
            )

        self._requests[client_ip].append(current_time)
        self._total_requests += 1

        return True

    def get_status(self) -> Dict:
        """제한 상태 반환"""
        return {
            "active_clients": len(self._requests),
            "total_requests": self._total_requests
        }

    def get_total_requests(self) -> int:
        return self._total_requests
