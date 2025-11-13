"""
Spring Boot 배치 시스템용 모델들
AIStoryScheduler와 완벽 호환
"""

from pydantic import BaseModel, Field
from typing import List, Optional

class BatchStoryRequest(BaseModel):
    """Spring Boot에서 보내는 배치 스토리 생성 요청"""
    station_name: str = Field(..., description="역 이름")
    line_number: int = Field(..., ge=1, le=4, description="노선 번호")
    character_health: int = Field(80, ge=0, le=100, description="기본 캐릭터 체력")
    character_sanity: int = Field(80, ge=0, le=100, description="기본 캐릭터 정신력")
    story_type: str = Field("BATCH_GENERATION", description="스토리 타입")

class BatchOptionData(BaseModel):
    """배치용 선택지 데이터 (Spring Boot Options 엔티티와 매핑)"""
    content: str = Field(..., description="선택지 내용")
    effect: str = Field(..., description="효과 타입 (health/sanity/none)")
    amount: int = Field(..., ge=-10, le=10, description="효과 수치")
    effect_preview: str = Field(..., description="효과 미리보기")

class BatchPageData(BaseModel):
    """배치용 페이지 데이터 (Spring Boot Page 엔티티와 매핑)"""
    content: str = Field(..., description="페이지 내용")
    options: List[BatchOptionData] = Field(..., min_items=2, max_items=4, description="선택지 목록")

class BatchStoryResponse(BaseModel):
    """완전한 스토리 응답 (Spring Boot가 DB에 저장할 형식)"""
    story_title: str = Field(..., description="스토리 제목")
    description: str = Field(..., description="스토리 설명")
    theme: str = Field(..., description="테마")
    keywords: List[str] = Field(..., description="키워드 목록")
    pages: List[BatchPageData] = Field(..., min_items=1, description="페이지 목록")
    
    # 메타데이터
    estimated_length: int = Field(..., description="예상 길이")
    difficulty: str = Field(..., description="난이도")
    station_name: str = Field(..., description="역 이름")
    line_number: int = Field(..., description="노선 번호")

class BatchValidationRequest(BaseModel):
    """스토리 구조 검증 요청"""
    story_data: dict = Field(..., description="검증할 스토리 데이터")
    validation_level: str = Field("strict", description="검증 수준 (strict/normal/loose)")

class BatchValidationResponse(BaseModel):
    """스토리 구조 검증 응답"""
    is_valid: bool = Field(..., description="유효성 여부")
    errors: List[str] = Field(default_factory=list, description="오류 목록")
    warnings: List[str] = Field(default_factory=list, description="경고 목록")
    fixed_structure: Optional[dict] = Field(None, description="수정된 구조")
    quality_score: Optional[float] = Field(None, description="품질 점수")

class BatchSystemStatus(BaseModel):
    """배치 시스템 상태"""
    ai_server_status: str = Field(..., description="AI 서버 상태")
    current_provider: str = Field(..., description="현재 LLM Provider")
    available_providers: dict = Field(..., description="사용 가능한 Provider들")
    batch_service_ready: bool = Field(..., description="배치 서비스 준비 상태")
    supported_stations: int = Field(..., description="지원 역 개수")
    quality_stats: dict = Field(..., description="품질 통계")
    rate_limit_status: dict = Field(..., description="Rate Limit 상태")
    timestamp: str = Field(..., description="조회 시간")