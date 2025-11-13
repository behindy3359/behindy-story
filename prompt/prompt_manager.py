"""
프롬프트 관리자 - 외부 파일 분리
🎯 테마 제한: 공포/미스터리/스릴러만
llmserver/prompts/prompt_manager.py
"""

from typing import Dict, Any
import os
import json
from pathlib import Path

# 허용된 테마 (전역 설정)
ALLOWED_THEMES = ["미스터리", "공포", "스릴러"]

class PromptManager:
    """프롬프트 외부 파일 관리자 - 테마 제한 적용"""
    
    def __init__(self):
        self.prompts_dir = Path(__file__).parent
        self.story_prompts = self._load_story_prompts()
        self.validation_prompts = self._load_validation_prompts()
        self.evaluation_prompts = self._load_evaluation_prompts()
    
    def _load_story_prompts(self) -> Dict[str, str]:
        """스토리 생성 프롬프트 로딩"""
        try:
            openai_path = self.prompts_dir / "story_generation_openai.txt"
            claude_path = self.prompts_dir / "story_generation_claude.txt"
            
            return {
                "openai": self._read_prompt_file(openai_path),
                "claude": self._read_prompt_file(claude_path)
            }
        except Exception as e:
            return self._get_default_story_prompts()
    
    def _load_validation_prompts(self) -> Dict[str, str]:
        """JSON 검증 프롬프트 로딩"""
        try:
            openai_path = self.prompts_dir / "json_validation_openai.txt"
            claude_path = self.prompts_dir / "json_validation_claude.txt"
            
            return {
                "openai": self._read_prompt_file(openai_path),
                "claude": self._read_prompt_file(claude_path)
            }
        except Exception as e:
            return self._get_default_validation_prompts()
    
    def _load_evaluation_prompts(self) -> Dict[str, str]:
        """품질 평가 프롬프트 로딩"""
        try:
            openai_path = self.prompts_dir / "quality_evaluation_openai.txt"
            claude_path = self.prompts_dir / "quality_evaluation_claude.txt"
            
            return {
                "openai": self._read_prompt_file(openai_path),
                "claude": self._read_prompt_file(claude_path)
            }
        except Exception as e:
            return self._get_default_evaluation_prompts()
    
    def _read_prompt_file(self, file_path: Path) -> str:
        """프롬프트 파일 읽기"""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        else:
            raise FileNotFoundError(f"프롬프트 파일 없음: {file_path}")
    
    def get_story_prompt(self, provider: str) -> str:
        """스토리 생성 프롬프트 반환"""
        return self.story_prompts.get(provider, self.story_prompts.get("openai", ""))
    
    def get_validation_prompt(self, provider: str) -> str:
        """JSON 검증 프롬프트 반환"""
        return self.validation_prompts.get(provider, self.validation_prompts.get("openai", ""))
    
    def get_evaluation_prompt(self, provider: str) -> str:
        """품질 평가 프롬프트 반환"""
        return self.evaluation_prompts.get(provider, self.evaluation_prompts.get("openai", ""))
    
    def reload_prompts(self):
        """프롬프트 파일 다시 로딩"""
        self.story_prompts = self._load_story_prompts()
        self.validation_prompts = self._load_validation_prompts()
        self.evaluation_prompts = self._load_evaluation_prompts()
    
    def create_user_prompt(self, context: Dict[str, Any], prompt_type: str = "generation") -> str:
        """사용자 프롬프트 생성 - 테마 제한 적용"""
        if prompt_type == "generation":
            return self._create_generation_user_prompt(context)
        elif prompt_type == "continuation":
            return self._create_continuation_user_prompt(context)
        else:
            return ""
    
    def _create_generation_user_prompt(self, context: Dict[str, Any]) -> str:
        """스토리 생성용 사용자 프롬프트 - 테마 제한"""
        station_name = context.get('station_name', '강남')
        line_number = context.get('line_number', 2)
        health = context.get('character_health', 80)
        sanity = context.get('character_sanity', 80)
        theme_preference = context.get('theme_preference')
        
        # 🎯 테마 제한 메시지
        theme_constraint = f"""
🎯 중요: 테마 제한
- 반드시 다음 3개 테마 중 하나만 사용: {', '.join(ALLOWED_THEMES)}
- 다른 테마는 절대 사용하지 마세요
"""
        
        # 선호 테마가 있고 허용된 테마인 경우 언급
        theme_hint = ""
        if theme_preference and theme_preference in ALLOWED_THEMES:
            theme_hint = f"- 가능하면 '{theme_preference}' 테마를 고려해주세요\n"
        
        return f"""스토리 생성 요청:

📍 **역 정보**
- 역명: {station_name}역
- 노선: {line_number}호선

👤 **캐릭터 상태**
- 체력: {health}/100
- 정신력: {sanity}/100

{theme_constraint}
{theme_hint}

**테마별 가이드:**
- 미스터리: 수수께끼, 단서 발견, 추리, 의문스러운 상황
- 공포: 두려움, 어둠, 섬뜩한 분위기, 위험한 상황  
- 스릴러: 긴장감, 추격, 시간 압박, 예상치 못한 전개

{station_name}역을 배경으로 한 허용된 테마의 텍스트 어드벤처 게임을 JSON 형식으로 생성해주세요."""
    
    def _create_continuation_user_prompt(self, context: Dict[str, Any]) -> str:
        """스토리 진행용 사용자 프롬프트 - 테마 일관성 유지"""
        station_name = context.get('station_name', '강남')
        line_number = context.get('line_number', 2)
        health = context.get('character_health', 80)
        sanity = context.get('character_sanity', 80)
        previous_choice = context.get('previous_choice', '')
        story_context = context.get('story_context', '')
        current_theme = context.get('theme', '미스터리')
        
        # 🎯 테마 일관성 강조
        theme_consistency = f"""
🎯 중요: 테마 일관성
- 기존 테마 '{current_theme}'를 반드시 유지하세요
- 테마를 변경하지 마세요
- {current_theme} 분위기를 계속 이어가세요
"""
        
        return f"""이전 스토리에서 "{previous_choice}" 선택의 결과로 스토리를 이어가주세요.

현재 상황:
- 위치: {station_name}역 ({line_number}호선)
- 캐릭터 상태: 체력 {health}/100, 정신력 {sanity}/100
- 스토리 맥락: {story_context or "이전 상황에서 이어집니다"}

{theme_consistency}

**테마별 연결 가이드:**
- 미스터리: 단서가 추가되거나 수수께끼가 심화
- 공포: 공포감이 증대되거나 새로운 위협 등장
- 스릴러: 긴장감이 고조되거나 상황이 더 복잡해짐

JSON 형식으로 응답해주세요:
{{
    "page_content": "이어지는 스토리 내용 (150-250자, {current_theme} 테마 유지)",
    "options": [
        {{
            "content": "선택지 내용",
            "effect": "health|sanity|none",
            "amount": -5~+5,
            "effect_preview": "효과 미리보기"
        }}
    ],
    "is_last_page": false
}}"""
    
    # ===== 기본 프롬프트 (파일이 없을 때 사용) - 테마 제한 적용 =====
    
    def _get_default_story_prompts(self) -> Dict[str, str]:
        """기본 스토리 프롬프트 - 테마 제한"""
        return {
            "openai": f"""당신은 지하철역 텍스트 어드벤처 게임의 전문 스토리 작가입니다.

🎯 중요: 테마 제한
- 반드시 다음 3개 테마만 사용: {', '.join(ALLOWED_THEMES)}
- 다른 테마는 절대 사용하지 마세요

반드시 다음 JSON 형식으로만 응답하세요:
{{
    "story_title": "스토리 제목 (20자 이내)",
    "page_content": "스토리 내용 (150-300자)",
    "options": [
        {{
            "content": "선택지 설명",
            "effect": "health|sanity|none",
            "amount": -10~+10,
            "effect_preview": "효과 미리보기"
        }}
    ],
    "estimated_length": 5,
    "difficulty": "쉬움|보통|어려움",
    "theme": "{ALLOWED_THEMES[0]}|{ALLOWED_THEMES[1]}|{ALLOWED_THEMES[2]}",
    "station_name": "역명",
    "line_number": 노선번호
}}

품질 기준:
- 선택지 2-4개, 효과 -10~+10 범위
- theme 필드는 반드시 허용된 테마 중 하나
- 한국어로 자연스럽게 작성
- 역의 특성을 허용된 테마로 해석""",

            "claude": f"""지하철역 텍스트 어드벤처 게임의 스토리 작가입니다.

🎯 테마 제한: {', '.join(ALLOWED_THEMES)}만 사용하세요.

JSON 형식으로만 응답하세요:
{{
    "story_title": "스토리 제목",
    "page_content": "스토리 내용 (150-300자)",
    "options": [선택지 배열],
    "estimated_length": 예상페이지수,
    "difficulty": "쉬움|보통|어려움",
    "theme": "허용된테마중하나",
    "station_name": "역명",
    "line_number": 노선번호
}}

작성 가이드:
- 선택지 2-4개 제공
- 허용된 테마의 분위기 충실히 반영
- 한국 지하철역 특성 활용
- 자연스러운 한국어 사용"""
        }
    
    def _get_default_validation_prompts(self) -> Dict[str, str]:
        """기본 검증 프롬프트 - 테마 제한 포함"""
        return {
            "openai": f"""JSON 검증 및 수정 전문가입니다.

주어진 텍스트를 검증하고 수정해주세요.

🎯 추가 검증: 테마 제한
- theme 필드가 다음 중 하나인지 확인: {', '.join(ALLOWED_THEMES)}
- 허용되지 않은 테마는 오류로 처리

응답 형식:
{{
    "is_valid": true/false,
    "errors": ["오류 목록"],
    "fixed_json": 수정된객체또는null,
    "theme_valid": true/false
}}""",

            "claude": f"""JSON 검증 전문가입니다.

테마 제한 포함 검증: {', '.join(ALLOWED_THEMES)}만 허용

검증 결과를 JSON으로 반환하세요:
{{
    "is_valid": boolean,
    "errors": ["오류들"],
    "fixed_json": 수정된데이터또는null,
    "theme_valid": boolean
}}"""
        }
    
    def _get_default_evaluation_prompts(self) -> Dict[str, str]:
        """기본 평가 프롬프트 - 테마 적합성 포함"""
        return {
            "openai": f"""텍스트 어드벤처 게임 품질 평가 전문가입니다.

6개 기준으로 평가 (총 120점):
1. 창의성 (20점)
2. 일관성 (20점)  
3. 몰입도 (20점)
4. 한국어 품질 (20점)
5. 게임 적합성 (20점)
6. 🆕 테마 적합성 (20점) - 허용된 테마({', '.join(ALLOWED_THEMES)}) 충실도

JSON 응답:
{{
    "total_score": 85.5,
    "creativity": 18.0,
    "coherence": 17.5,
    "engagement": 16.0,
    "korean_quality": 19.0,
    "game_suitability": 15.0,
    "theme_consistency": 18.0,
    "feedback": "상세 피드백",
    "passed": true,
    "theme_valid": true
}}

통과 기준: 70점 이상 + 테마 적합성""",

            "claude": f"""품질 평가 전문가입니다.

6개 기준 평가 (테마 적합성 포함):
- 허용 테마: {', '.join(ALLOWED_THEMES)}

JSON 응답:
{{
    "total_score": 점수,
    "creativity": 창의성점수,
    "coherence": 일관성점수,
    "engagement": 몰입도점수,
    "korean_quality": 한국어품질점수,
    "game_suitability": 게임적합성점수,
    "theme_consistency": 테마적합성점수,
    "feedback": "피드백",
    "passed": boolean,
    "theme_valid": boolean
}}"""
        }
    
    @staticmethod
    def get_allowed_themes() -> list:
        """허용된 테마 목록 반환"""
        return ALLOWED_THEMES.copy()
    
    @staticmethod
    def is_theme_allowed(theme: str) -> bool:
        """테마 허용 여부 확인"""
        return theme in ALLOWED_THEMES
    
    def validate_theme_in_content(self, content: str) -> Dict[str, Any]:
        """콘텐츠 내 테마 검증"""
        try:
            # 간단한 키워드 기반 테마 추정
            theme_keywords = {
                "미스터리": ["수수께끼", "단서", "의문", "추리", "비밀"],
                "공포": ["두려움", "무서운", "섬뜩한", "어둠", "공포"],
                "스릴러": ["긴장", "추격", "위험", "스릴", "압박"]
            }
            
            detected_themes = []
            for theme, keywords in theme_keywords.items():
                if any(keyword in content for keyword in keywords):
                    detected_themes.append(theme)
            
            return {
                "detected_themes": detected_themes,
                "is_valid": len(detected_themes) > 0,
                "primary_theme": detected_themes[0] if detected_themes else None
            }
            
        except Exception as e:
            return {
                "detected_themes": [],
                "is_valid": False,
                "primary_theme": None,
                "error": str(e)
            }

# 전역 인스턴스
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """프롬프트 매니저 싱글톤 반환"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager