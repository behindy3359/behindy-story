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
            logger.error(f"   : {str(e)}")
            logger.error("Fallback  ")
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
                    story_content = self._create_default_story_content(request)

                story_outline = result.get("story_outline", f"{request.station_name}  ")
                phase_summary = result.get("phase_summary", f"{request.station_name}    ")

                return MultiplayerStoryResponse(
                    story=story_content,
                    effects=[],
                    phase=1,
                    is_ending=False,
                    story_outline=story_outline,
                    phase_summary=phase_summary
                )
            else:
                return self._create_mock_response(request)

        except Exception as e:
            logger.error(f"  : {str(e)}")
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
            logger.error(f"  : {str(e)}")
            return self._create_mock_response(request)

    def _build_intro_prompt(self, request: MultiplayerStoryRequest) -> str:
        participants_info = "\n".join([
            f"- {p.character_name}:  {p.hp}/100,  {p.sanity}/100"
            for p in request.participants
        ])

        return f"""
 /     .

[ ]
1.       
2.  5-8 Phase   
3.     

[ ]
- : {request.station_name}
- : /
- : 5-8 Phase     

[ ]
{participants_info}

[ ]
- current_situation:    (2-3)
- special_event:    (1-2)
- hint:     (1-2)

[ ]
JSON  :
{{
    "story": {{
        "current_situation": "{request.station_name}   ...",
        "special_event": "   ...",
        "hint": "     ..."
    }},
    "effects": [],
    "story_outline": "   (5-8 Phase )",
    "phase_summary": " Phase  (1-2)"
}}
"""

    def _build_story_prompt(self, request: MultiplayerStoryRequest) -> str:
        participants_info = "\n".join([
            f"- {p.character_name}:  {p.hp}/100,  {p.sanity}/100"
            for p in request.participants
        ])

        chat_history = "\n".join([
            f"{msg.character_name}: {msg.content}"
            for msg in request.message_stack[-20:]
        ]) if request.message_stack else " "

        story_history_section = ""
        if request.story_history:
            history_text = "\n".join([
                f"Phase {h.phase}: {h.summary}"
                for h in request.story_history
            ])
            story_history_section = f"""
[  ]
{history_text}

    .
"""

        story_outline_section = ""
        if request.story_outline:
            story_outline_section = f"""
 :
{request.story_outline}

   . 5-10 Phase   .
"""

        return f"""
 /     .

[ ]
1. Phase 6    
2. Phase 8   is_ending true  ending_summary 
3.     
4. effects      (  0)
5.  Phase phase_summary 1-2 

:
- : {request.station_name}
-  Phase: {request.phase}
{story_outline_section}
{story_history_section}

 :
{participants_info}

  ( Phase  20):
{chat_history}

[ ]
- current_situation:    (2-3)
- special_event:    (1-2)
- hint:     (1-2)

:
1.      
2.      
3.      (HP, Sanity)
4. Phase {request.phase} 6   
5. Phase {request.phase} 8     (is_ending: true)

JSON  :
{{
    "story": {{
        "current_situation": "   (2-3)...",
        "special_event": "   (1-2)...",
        "hint": "   (1-2)..."
    }},
    "effects": [
        {{
            "character_name": "",
            "hp_change": -5~+5,
            "sanity_change": -5~+5
        }}
    ],
    "is_ending": true/false (Phase 8  true),
    "phase_summary": " Phase  (1-2)",
    "ending_summary": "     (500-1000)"
}}

  :
-  : HP -3~-7
-  : HP +1~+3
-  : Sanity -3~-7
-  : Sanity +1~+3
-   effects  (  hp_change: 0, sanity_change: 0)

  :
- is_ending true  ending_summary 
-   500-1000 
-     
"""

    def _parse_llm_response(self, result: Dict, request: MultiplayerStoryRequest) -> MultiplayerStoryResponse:
        story_data = result.get("story", {})
        if isinstance(story_data, dict):
            story_content = StoryContent(
                current_situation=story_data.get("current_situation", ""),
                special_event=story_data.get("special_event", ""),
                hint=story_data.get("hint", "")
            )
        else:
            story_content = self._create_default_story_content(request)

        is_ending = result.get("is_ending", False)
        phase_summary = result.get("phase_summary", "")
        ending_summary = result.get("ending_summary") if is_ending else None

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
            story_outline=request.story_outline,
            phase_summary=phase_summary,
            ending_summary=ending_summary
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
        return f"{request.station_name}  ,   .   ,       ."

    def _create_default_story_content(self, request: MultiplayerStoryRequest) -> StoryContent:
        return StoryContent(
            current_situation=f"{request.station_name}    .",
            special_event=" .",
            hint=" ."
        )

    def _create_mock_response(self, request: MultiplayerStoryRequest) -> MultiplayerStoryResponse:
        import random

        if request.is_intro:
            story_content = StoryContent(
                current_situation=f"{request.station_name}  ,   .",
                special_event="  ,       .",
                hint="   ."
            )
            story_outline = f"{request.station_name}  .  5-8 Phase    ."
            phase_summary = f"{request.station_name}    "
            return MultiplayerStoryResponse(
                story=story_content,
                effects=[],
                phase=1,
                is_ending=False,
                story_outline=story_outline,
                phase_summary=phase_summary
            )

        themes = {
            "": {
                "situation": f"{request.station_name}   .",
                "event": "      .",
                "hint": "  ."
            },
            "": {
                "situation": f"{request.station_name}   .",
                "event": "     .",
                "hint": "   ."
            },
            "": {
                "situation": f"{request.station_name}   .",
                "event": "     .",
                "hint": "      ."
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
        phase_summary = f"{selected_theme}  "
        ending_summary = f"{request.station_name}  ." if is_ending else None

        return MultiplayerStoryResponse(
            story=story_content,
            effects=effects,
            phase=request.phase + 1,
            is_ending=is_ending,
            story_outline=request.story_outline,
            phase_summary=phase_summary,
            ending_summary=ending_summary
        )
