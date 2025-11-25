import logging
from typing import Dict, List, Any, Optional
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
            provider_name = self.provider.get_provider_name().lower()

            if "mock" in provider_name:
                return self._create_mock_response(request)

            if request.is_intro:
                return await self._generate_intro(request)
            else:
                return await self._generate_story(request)

        except Exception as e:
            logger.error(f"멀티플레이어 스토리 생성 실패: {str(e)}")
            logger.error("Fallback 응답 생성")
            return self._create_mock_response(request)

    async def _generate_intro(self, request: MultiplayerStoryRequest) -> MultiplayerStoryResponse:
        prompt = self._build_intro_prompt(request)

        try:
            result = await self.provider.generate_story(prompt, max_tokens=500)

            if isinstance(result, dict):
                story_text = result.get("story_text", self._get_default_intro(request))
                story_outline = result.get("story_outline", f"{request.station_name}역에서 벌어지는 미스터리")

                return MultiplayerStoryResponse(
                    story_text=story_text,
                    effects=[],
                    phase=1,
                    is_ending=False,
                    story_outline=story_outline
                )
            else:
                return self._create_mock_response(request)

        except Exception as e:
            logger.error(f"인트로 생성 실패: {str(e)}")
            return self._create_mock_response(request)

    async def _generate_story(self, request: MultiplayerStoryRequest) -> MultiplayerStoryResponse:
        prompt = self._build_story_prompt(request)

        try:
            result = await self.provider.generate_story(prompt, max_tokens=500)

            if isinstance(result, dict):
                return self._parse_llm_response(result, request)
            else:
                return self._create_mock_response(request)

        except Exception as e:
            logger.error(f"스토리 생성 실패: {str(e)}")
            return self._create_mock_response(request)

    def _build_intro_prompt(self, request: MultiplayerStoryRequest) -> str:
        participants_info = "\n".join([
            f"- {p.character_name}: 체력 {p.hp}/100, 정신력 {p.sanity}/100"
            for p in request.participants
        ])

        return f"""
당신은 공포/미스테리 텍스트 어드벤처 게임의 게임 마스터입니다.
짧고 명확한 스토리라인을 가진 이야기를 진행하세요.
스토리는 5-10개의 Phase 안에 완결되도록 설계하세요.

{request.station_name}역을 배경으로 공포/미스터리 스토리를 시작하세요.

참가자들:
{participants_info}

요구사항:
1. 참가자들이 처음 역에 도착한 상황을 묘사하세요
2. 긴장감 있는 분위기를 조성하세요
3. 2-3문장으로 간결하게 작성하세요
4. 스토리라인 개요를 2-3문장으로 요약하세요 (5-10 Phase 안에 완결)

JSON 형식으로 응답하세요:
{{
    "story_text": "인트로 스토리 (2-3문장)",
    "story_outline": "스토리라인 개요 (2-3문장, 5-10 Phase 안에 완결)"
}}
"""

    def _build_story_prompt(self, request: MultiplayerStoryRequest) -> str:
        participants_info = "\n".join([
            f"- {p.character_name}: 체력 {p.hp}/100, 정신력 {p.sanity}/100"
            for p in request.participants
        ])

        chat_history = "\n".join([
            f"{msg.character_name}: {msg.content}"
            for msg in request.message_stack[-20:]
        ]) if request.message_stack else "대화 없음"

        story_outline_section = ""
        if request.story_outline:
            story_outline_section = f"""
스토리라인 개요:
{request.story_outline}

위 스토리라인을 따라 진행하세요. 5-10 Phase 안에 완결되도록 조절하세요.
"""

        return f"""
당신은 공포/미스터리 텍스트 어드벤처 게임의 게임 마스터입니다.

배경:
- 역명: {request.station_name}역
- 현재 Phase: {request.phase}
{story_outline_section}

참가자 상태:
{participants_info}

최근 대화 (최대 20개):
{chat_history}

요구사항:
1. 최근 대화 내용을 반영하여 스토리를 전개하세요
2. 참가자들의 행동에 따라 적절한 결과를 제시하세요
3. 각 캐릭터의 상태 변화를 결정하세요 (HP, Sanity)
4. 2-3문장의 흥미로운 스토리를 작성하세요
5. Phase {request.phase}가 8 이상이면 스토리를 마무리하는 것을 고려하세요

JSON 형식으로 응답하세요:
{{
    "story_text": "스토리 내용 (2-3문장)",
    "effects": [
        {{
            "character_name": "캐릭터명",
            "hp_change": -5~+5,
            "sanity_change": -5~+5
        }}
    ],
    "is_ending": true/false (스토리 종료 여부)
}}

상태 변화 가이드:
- 위험한 행동: HP -3~-7
- 안전한 행동: HP +1~+3
- 공포스러운 상황: Sanity -3~-7
- 안정적인 상황: Sanity +1~+3
- 변경이 없는 캐릭터는 effects에서 제외 가능
"""

    def _parse_llm_response(self, result: Dict, request: MultiplayerStoryRequest) -> MultiplayerStoryResponse:
        story_text = result.get("story_text", f"{request.station_name}역에서 예상치 못한 일이 벌어집니다.")
        is_ending = result.get("is_ending", False)

        effects = []
        effects_data = result.get("effects", [])

        for effect_data in effects_data:
            if isinstance(effect_data, dict):
                effects.append(ParticipantUpdate(**effect_data))

        if not effects:
            effects = self._create_default_effects(request.participants)

        return MultiplayerStoryResponse(
            story_text=story_text,
            effects=effects,
            phase=request.phase + 1,
            is_ending=is_ending,
            story_outline=request.story_outline
        )

    def _create_default_effects(self, participants: List[ParticipantInfo]) -> List[ParticipantUpdate]:
        import random
        return [
            ParticipantUpdate(
                character_name=p.character_name,
                hp_change=random.randint(-2, 1),
                sanity_change=random.randint(-2, 1)
            )
            for p in participants
        ]

    def _get_default_intro(self, request: MultiplayerStoryRequest) -> str:
        return f"{request.station_name}역에 도착한 순간, 이상한 기운이 느껴집니다. 주변은 이상하리만치 조용하고, 어두운 그림자들이 벽을 따라 움직이는 것 같습니다."

    def _create_mock_response(self, request: MultiplayerStoryRequest) -> MultiplayerStoryResponse:
        import random

        if request.is_intro:
            story_text = self._get_default_intro(request)
            story_outline = f"{request.station_name}역에서 벌어지는 미스터리. 참가자들은 5-8 Phase 안에 진실을 밝혀야 합니다."
            return MultiplayerStoryResponse(
                story_text=story_text,
                effects=[],
                phase=1,
                is_ending=False,
                story_outline=story_outline
            )

        themes = {
            "미스터리": f"{request.station_name}역에서 수상한 표지판을 발견했습니다. 이상한 기호들이 무언가를 가리키고 있는 것 같습니다.",
            "공포": f"{request.station_name}역의 조명이 갑자기 어두워집니다. 어둠 속에서 무언가가 움직이는 소리가 들립니다.",
            "스릴러": f"{request.station_name}역에서 긴박한 상황이 발생했습니다. 누군가가 여러분을 따라오고 있는 것 같습니다."
        }

        selected_theme = random.choice(list(themes.keys()))
        story_text = themes[selected_theme]

        effects = [
            ParticipantUpdate(
                character_name=p.character_name,
                hp_change=random.randint(-3, 2),
                sanity_change=random.randint(-3, 2)
            )
            for p in request.participants
        ]

        is_ending = request.phase >= 8

        return MultiplayerStoryResponse(
            story_text=story_text,
            effects=effects,
            phase=request.phase + 1,
            is_ending=is_ending,
            story_outline=request.story_outline
        )
