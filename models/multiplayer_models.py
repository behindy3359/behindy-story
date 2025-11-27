from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ParticipantInfo(BaseModel):
    character_name: str = Field(..., description="캐릭터 이름")
    hp: int = Field(..., ge=0, le=100, description="현재 체력")
    sanity: int = Field(..., ge=0, le=100, description="현재 정신력")

class ChatHistoryItem(BaseModel):
    character_name: str = Field(..., description="발화자 캐릭터 이름")
    content: str = Field(..., description="메시지 내용")

class StoryHistoryItem(BaseModel):
    phase: int = Field(..., description="Phase 번호")
    summary: str = Field(..., description="해당 Phase의 요약")

class MultiplayerStoryRequest(BaseModel):
    room_id: int = Field(..., description="방 ID")
    phase: int = Field(..., ge=0, description="현재 Phase")
    station_name: str = Field(..., description="역 이름")
    story_outline: Optional[str] = Field(None, description="스토리 개요 (컨텍스트 유지용)")
    participants: List[ParticipantInfo] = Field(..., description="참여자 정보")
    message_stack: List[ChatHistoryItem] = Field(default_factory=list, description="대화 스택 (최근 20개)")
    story_history: List[StoryHistoryItem] = Field(default_factory=list, description="이전 Phase들의 요약")
    is_intro: bool = Field(False, description="인트로 생성 모드 여부")

class ParticipantUpdate(BaseModel):
    character_name: str = Field(..., description="캐릭터 이름")
    hp_change: int = Field(0, description="체력 변화량")
    sanity_change: int = Field(0, description="정신력 변화량")

class StoryContent(BaseModel):
    current_situation: str = Field(..., description="현재 상황 묘사")
    special_event: str = Field(..., description="특별한 이벤트")
    hint: str = Field(..., description="플레이어 행동 유도 힌트")

class MultiplayerStoryResponse(BaseModel):
    story: StoryContent = Field(..., description="구조화된 스토리 내용")
    effects: List[ParticipantUpdate] = Field(default_factory=list, description="참여자 상태 변화")
    phase: int = Field(..., ge=1, description="현재 Phase")
    is_ending: bool = Field(False, description="스토리 종료 여부")
    story_outline: Optional[str] = Field(None, description="스토리 개요 (인트로 시 반환)")
    phase_summary: Optional[str] = Field(None, description="이번 Phase 요약 (다음 요청에 포함)")
    ending_summary: Optional[str] = Field(None, description="엔딩 시 전체 스토리 요약")
