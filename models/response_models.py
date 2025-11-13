"""
응답 모델 정의 (Spring Boot DTO와 완벽 호환)
"""

from pydantic import BaseModel
from typing import List, Optional

class OptionData(BaseModel):
    content: str
    effect: str  # "HEALTH", "SANITY"
    amount: int
    effect_preview: str  # "체력 -10", "정신력 +5"

class StoryGenerationResponse(BaseModel):
    story_title: str
    page_content: str
    options: List[OptionData]
    estimated_length: int
    difficulty: str  # "쉬움", "보통", "어려움"
    theme: str
    station_name: str
    line_number: int

class StoryContinueResponse(BaseModel):
    page_content: str
    options: List[OptionData]
    is_last_page: bool