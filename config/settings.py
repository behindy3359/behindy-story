"""
환경 설정 관리 (Ollama 제거)
"""

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # AI Provider 설정 (ollama 제거)
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock")
    
    # OpenAI 설정
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    
    # Claude 설정
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
    
    # Rate Limiting
    REQUEST_LIMIT_PER_HOUR: int = int(os.getenv("REQUEST_LIMIT_PER_HOUR", "100"))
    REQUEST_LIMIT_PER_DAY: int = int(os.getenv("REQUEST_LIMIT_PER_DAY", "1000"))
    
    # 캐싱 설정
    USE_CACHE: bool = os.getenv("USE_CACHE", "true").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1시간
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # 로깅 설정
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # 추가 환경 변수 무시
    
    def get_available_providers(self) -> dict:
        """사용 가능한 Provider 목록"""
        return {
            "openai": bool(self.OPENAI_API_KEY),
            "claude": bool(self.CLAUDE_API_KEY),
            "mock": True
        }
    
    def get_current_provider_info(self) -> dict:
        """현재 Provider 정보"""
        if self.AI_PROVIDER == "openai" and self.OPENAI_API_KEY:
            return {
                "provider": "openai",
                "model": self.OPENAI_MODEL,
                "status": "configured"
            }
        elif self.AI_PROVIDER == "claude" and self.CLAUDE_API_KEY:
            return {
                "provider": "claude", 
                "model": self.CLAUDE_MODEL,
                "status": "configured"
            }
        else:
            return {
                "provider": "mock",
                "model": "mock_generator",
                "status": "fallback"
            }
    
    def validate_settings(self) -> list:
        """설정 검증 및 경고 반환"""
        warnings = []
        
        if self.AI_PROVIDER not in ["mock", "openai", "claude"]:
            warnings.append(f"알 수 없는 AI_PROVIDER: {self.AI_PROVIDER}")
        
        if self.AI_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            warnings.append("OpenAI 선택되었으나 API 키가 없습니다.")
        
        if self.AI_PROVIDER == "claude" and not self.CLAUDE_API_KEY:
            warnings.append("Claude 선택되었으나 API 키가 없습니다.")
        
        if self.REQUEST_LIMIT_PER_HOUR > 1000:
            warnings.append("시간당 요청 제한이 너무 높습니다.")
        
        return warnings