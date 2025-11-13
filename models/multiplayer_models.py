from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ParticipantInfo(BaseModel):
    character_name: str = Field(..., description="캐릭터 이름")
    hp: int = Field(..., ge=0, le=100, description="현재 체력")
    sanity: int = Field(..., ge=0, le=100, description="현재 정신력")

class ChatHistoryItem(BaseModel):
    character_name: str = Field(..., description="발화자 캐릭터 이름")
    content: str = Field(..., description="메시지 내용")

class MultiplayerStoryRequest(BaseModel):
    station_id: int = Field(..., description="역 ID")
    station_name: str = Field(..., description="역 이름")
    line_number: int = Field(..., ge=1, le=4, description="노선 번호")
    current_phase: int = Field(..., ge=0, description="현재 Phase")
    summary: Optional[str] = Field(None, description="이전 Phase 요약")
    recent_messages: List[ChatHistoryItem] = Field(default_factory=list, description="최근 채팅 내역")
    participants: List[ParticipantInfo] = Field(..., description="참여자 정보")

class ParticipantUpdate(BaseModel):
    character_name: str = Field(..., description="캐릭터 이름")
    hp_change: int = Field(0, description="체력 변화량")
    sanity_change: int = Field(0, description="정신력 변화량")

class MultiplayerStoryResponse(BaseModel):
    content: str = Field(..., description="생성된 스토리 내용")
    summary: str = Field(..., description="현재 Phase 요약")
    participant_updates: List[ParticipantUpdate] = Field(default_factory=list, description="참여자 상태 변화")
