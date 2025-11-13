"""
요청 모델 정의 (Spring Boot DTO와 호환)
"""

from pydantic import BaseModel, Field
from typing import Optional

class StoryGenerationRequest(BaseModel):
    station_name: str = Field(..., description="현재 역 이름")
    line_number: int = Field(..., ge=1, le=4, description="노선 번호 (1-4)")
    character_health: int = Field(..., ge=0, le=100, description="캐릭터 체력")
    character_sanity: int = Field(..., ge=0, le=100, description="캐릭터 정신력")
    theme_preference: Optional[str] = Field(None, description="선호 테마")

class StoryContinueRequest(BaseModel):
    station_name: str = Field(..., description="현재 역 이름")
    line_number: int = Field(..., ge=1, le=4, description="노선 번호")
    character_health: int = Field(..., ge=0, le=100, description="캐릭터 체력")
    character_sanity: int = Field(..., ge=0, le=100, description="캐릭터 정신력")
    previous_choice: str = Field(..., description="이전 선택")
    story_context: Optional[str] = Field(None, description="스토리 맥락")
