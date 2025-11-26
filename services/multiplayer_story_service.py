import logging
from typing import Dict, List, Any, Optional
from models.multiplayer_models import (
    MultiplayerStoryRequest,
    MultiplayerStoryResponse,
    StoryContent,
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
                story_data = result.get("story", {})
                if isinstance(story_data, dict):
                    story_content = StoryContent(
                        current_situation=story_data.get("current_situation", ""),
                        special_event=story_data.get("special_event", ""),
                        hint=story_data.get("hint", "")
                    )
                else:
                    # Fallback for old format
                    story_content = self._create_default_story_content(request)

                story_outline = result.get("story_outline", f"{request.station_name}역에서 벌어지는 미스터리")

                return MultiplayerStoryResponse(
                    story=story_content,
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

[필수 규칙]
1. 반드시 명확한 엔딩을 설정하고 플레이어를 그쪽으로 유도하세요
2. 스토리는 5-8 Phase 안에 완결되도록 설계하세요
3. 구조화된 스토리 형식을 따라야 합니다

[게임 설정]
- 역: {request.station_name}
- 테마: 공포/미스터리
- 목표: 5-8 Phase 안에 진실 규명 또는 탈출

[참여자 정보]
{participants_info}

[스토리 구조]
- current_situation: 현재 상황 묘사 (2-3문장)
- special_event: 이번 특별한 이벤트 (1-2문장)
- hint: 플레이어 행동 유도 힌트 (1-2문장)

[응답 형식]
JSON 형식으로만 응답하세요:
{{
    "story": {{
        "current_situation": "{request.station_name}역에 도착한 상황 묘사...",
        "special_event": "긴장감 있는 첫 이벤트...",
        "hint": "플레이어가 할 수 있는 행동 제시..."
    }},
    "effects": [],
    "story_outline": "스토리 전체 줄거리 (5-8 Phase 계획)"
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

[필수 규칙]
1. Phase 6 이상부터는 적극적으로 엔딩으로 유도하세요
2. Phase 8에 도달하면 반드시 is_ending을 true로 설정하세요
3. 구조화된 스토리 형식을 따라야 합니다
4. effects 배열에는 모든 캐릭터가 포함되어야 합니다 (변화가 없으면 0으로)

배경:
- 역명: {request.station_name}역
- 현재 Phase: {request.phase}
{story_outline_section}

참가자 상태:
{participants_info}

최근 대화 (최대 20개):
{chat_history}

[스토리 구조]
- current_situation: 현재 상황 묘사 (2-3문장)
- special_event: 이번 특별한 이벤트 (1-2문장)
- hint: 플레이어 행동 유도 힌트 (1-2문장)

요구사항:
1. 최근 대화 내용을 반영하여 스토리를 전개하세요
2. 참가자들의 행동에 따라 적절한 결과를 제시하세요
3. 각 캐릭터의 상태 변화를 결정하세요 (HP, Sanity)
4. Phase {request.phase}가 6 이상이면 클라이맥스로 진행하세요
5. Phase {request.phase}가 8 이상이면 반드시 스토리를 마무리하세요 (is_ending: true)

JSON 형식으로 응답하세요:
{{
    "story": {{
        "current_situation": "현재 상황 묘사 (2-3문장)...",
        "special_event": "이번 특별 이벤트 (1-2문장)...",
        "hint": "플레이어 행동 제안 (1-2문장)..."
    }},
    "effects": [
        {{
            "character_name": "캐릭터명",
            "hp_change": -5~+5,
            "sanity_change": -5~+5
        }}
    ],
    "is_ending": true/false (Phase 8 이상이면 true)
}}

상태 변화 가이드:
- 위험한 행동: HP -3~-7
- 안전한 행동: HP +1~+3
- 공포스러운 상황: Sanity -3~-7
- 안정적인 상황: Sanity +1~+3
- 모든 캐릭터를 effects에 포함하세요 (변화 없으면 hp_change: 0, sanity_change: 0)
"""

    def _parse_llm_response(self, result: Dict, request: MultiplayerStoryRequest) -> MultiplayerStoryResponse:
        # 구조화된 스토리 파싱
        story_data = result.get("story", {})
        if isinstance(story_data, dict):
            story_content = StoryContent(
                current_situation=story_data.get("current_situation", ""),
                special_event=story_data.get("special_event", ""),
                hint=story_data.get("hint", "")
            )
        else:
            # Fallback for old format
            story_content = self._create_default_story_content(request)

        is_ending = result.get("is_ending", False)

        effects = []
        effects_data = result.get("effects", [])

        for effect_data in effects_data:
            if isinstance(effect_data, dict):
                effects.append(ParticipantUpdate(**effect_data))

        if not effects:
            effects = self._create_default_effects(request.participants)

        return MultiplayerStoryResponse(
            story=story_content,
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

    def _create_default_story_content(self, request: MultiplayerStoryRequest) -> StoryContent:
        return StoryContent(
            current_situation=f"{request.station_name}역에서 예상치 못한 일이 벌어집니다.",
            special_event="긴장감이 감돕니다.",
            hint="신중하게 행동하세요."
        )

    def _create_mock_response(self, request: MultiplayerStoryRequest) -> MultiplayerStoryResponse:
        import random

        if request.is_intro:
            story_content = StoryContent(
                current_situation=f"{request.station_name}역에 도착한 순간, 이상한 기운이 느껴집니다.",
                special_event="주변은 이상하리만치 조용하고, 어두운 그림자들이 벽을 따라 움직이는 것 같습니다.",
                hint="주변을 살펴보며 단서를 찾아보세요."
            )
            story_outline = f"{request.station_name}역에서 벌어지는 미스터리. 참가자들은 5-8 Phase 안에 진실을 밝혀야 합니다."
            return MultiplayerStoryResponse(
                story=story_content,
                effects=[],
                phase=1,
                is_ending=False,
                story_outline=story_outline
            )

        themes = {
            "미스터리": {
                "situation": f"{request.station_name}역에서 수상한 표지판을 발견했습니다.",
                "event": "이상한 기호들이 무언가를 가리키고 있는 것 같습니다.",
                "hint": "표지판의 기호를 해독해보세요."
            },
            "공포": {
                "situation": f"{request.station_name}역의 조명이 갑자기 어두워집니다.",
                "event": "어둠 속에서 무언가가 움직이는 소리가 들립니다.",
                "hint": "조심스럽게 소리의 근원을 찾아보세요."
            },
            "스릴러": {
                "situation": f"{request.station_name}역에서 긴박한 상황이 발생했습니다.",
                "event": "누군가가 여러분을 따라오고 있는 것 같습니다.",
                "hint": "안전한 장소를 찾거나 맞서 싸울 준비를 하세요."
            }
        }

        selected_theme = random.choice(list(themes.keys()))
        theme_data = themes[selected_theme]

        story_content = StoryContent(
            current_situation=theme_data["situation"],
            special_event=theme_data["event"],
            hint=theme_data["hint"]
        )

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
            story=story_content,
            effects=effects,
            phase=request.phase + 1,
            is_ending=is_ending,
            story_outline=request.story_outline
        )
