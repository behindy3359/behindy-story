import logging
from typing import Dict, List, Any
from models.multiplayer_models import (
    MultiplayerStoryRequest,
    MultiplayerStoryResponse,
    ParticipantUpdate,
    ParticipantInfo
)
from providers.llm_provider import LLMProviderFactory

logger = logging.getLogger(__name__)

class MultiplayerStoryService:
    def __init__(self):
        self.provider = LLMProviderFactory.get_provider()

    async def generate_next_phase(self, request: MultiplayerStoryRequest) -> MultiplayerStoryResponse:
        try:
            logger.info("=" * 60)
            logger.info(f"멀티플레이어 Phase {request.current_phase} 생성 시작")
            logger.info(f"역: {request.station_name}역 ({request.line_number}호선)")
            logger.info(f"참여자 수: {len(request.participants)}")
            logger.info(f"최근 메시지 수: {len(request.recent_messages)}")

            provider_name = self.provider.get_provider_name().lower()

            if "mock" in provider_name:
                logger.info("Mock Provider로 응답 생성")
                return self._create_mock_response(request)

            context = self._build_context(request)
            prompt = self._build_prompt(request)

            logger.info(f"LLM 호출: {self.provider.get_provider_name()}")
            result = await self.provider.generate_story(prompt, **context)

            if isinstance(result, dict):
                return self._parse_llm_response(result, request)
            else:
                logger.warning("예상치 못한 LLM 응답 형식")
                return self._create_mock_response(request)

        except Exception as e:
            logger.error(f"멀티플레이어 스토리 생성 실패: {str(e)}")
            logger.error("Fallback 응답 생성")
            return self._create_mock_response(request)

    def _build_context(self, request: MultiplayerStoryRequest) -> Dict[str, Any]:
        return {
            'station_name': request.station_name,
            'line_number': request.line_number,
            'current_phase': request.current_phase,
            'participant_count': len(request.participants)
        }

    def _build_prompt(self, request: MultiplayerStoryRequest) -> str:
        participants_info = "\n".join([
            f"- {p.character_name}: 체력 {p.hp}/100, 정신력 {p.sanity}/100"
            for p in request.participants
        ])

        chat_history = "\n".join([
            f"{msg.character_name}: {msg.content}"
            for msg in request.recent_messages[-20:]
        ])

        summary_section = ""
        if request.summary:
            summary_section = f"""
이전 Phase 요약:
{request.summary}
"""

        return f"""
{request.station_name}역을 배경으로 한 멀티플레이어 텍스트 어드벤처 게임의 Phase {request.current_phase}를 생성해주세요.

배경:
- 역명: {request.station_name}역 ({request.line_number}호선)
- 현재 Phase: {request.current_phase}
- 테마: 공포, 미스터리, 스릴러 중 하나
{summary_section}

참여 캐릭터:
{participants_info}

최근 대화 내용:
{chat_history}

요구사항:
1. 최근 대화 내용을 반영하여 스토리를 전개하세요
2. 참여자들의 행동에 따라 적절한 결과를 제시하세요
3. 각 캐릭터의 상태 변화를 결정하세요 (HP, Sanity)
4. 150-300자의 흥미로운 스토리를 작성하세요
5. 현재 상황을 30-50자로 요약하세요

JSON 형식으로 응답하세요:
{{
    "content": "스토리 내용 (150-300자)",
    "summary": "현재 Phase 요약 (30-50자)",
    "participant_updates": [
        {{
            "character_name": "캐릭터명",
            "hp_change": -5~+5,
            "sanity_change": -5~+5
        }}
    ]
}}

상태 변화 가이드:
- 위험한 행동: HP -3~-7
- 안전한 행동: HP +1~+3
- 공포스러운 상황: Sanity -3~-7
- 안정적인 상황: Sanity +1~+3
- 참여자별로 다른 변화량 부여 가능
"""

    def _parse_llm_response(self, result: Dict, request: MultiplayerStoryRequest) -> MultiplayerStoryResponse:
        content = result.get("content", f"{request.station_name}역에서 예상치 못한 일이 벌어집니다.")
        summary = result.get("summary", f"Phase {request.current_phase} 진행")

        participant_updates = []
        updates_data = result.get("participant_updates", [])

        for update_data in updates_data:
            if isinstance(update_data, dict):
                participant_updates.append(ParticipantUpdate(**update_data))

        if not participant_updates:
            participant_updates = self._create_default_updates(request.participants)

        return MultiplayerStoryResponse(
            content=content,
            summary=summary,
            participant_updates=participant_updates
        )

    def _create_default_updates(self, participants: List[ParticipantInfo]) -> List[ParticipantUpdate]:
        import random
        return [
            ParticipantUpdate(
                character_name=p.character_name,
                hp_change=random.randint(-2, 1),
                sanity_change=random.randint(-2, 1)
            )
            for p in participants
        ]

    def _create_mock_response(self, request: MultiplayerStoryRequest) -> MultiplayerStoryResponse:
        import random

        themes = {
            "미스터리": f"{request.station_name}역에서 수상한 표지판을 발견했습니다. 이상한 기호들이 무언가를 가리키고 있는 것 같습니다.",
            "공포": f"{request.station_name}역의 조명이 갑자기 어두워집니다. 어둠 속에서 무언가가 움직이는 소리가 들립니다.",
            "스릴러": f"{request.station_name}역에서 긴박한 상황이 발생했습니다. 누군가가 여러분을 따라오고 있는 것 같습니다."
        }

        selected_theme = random.choice(list(themes.keys()))
        content = themes[selected_theme]

        participant_updates = [
            ParticipantUpdate(
                character_name=p.character_name,
                hp_change=random.randint(-3, 2),
                sanity_change=random.randint(-3, 2)
            )
            for p in request.participants
        ]

        return MultiplayerStoryResponse(
            content=content,
            summary=f"Phase {request.current_phase}: {selected_theme} 상황 발생",
            participant_updates=participant_updates
        )
