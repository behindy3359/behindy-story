"""
Spring Boot 배치 시스템용 스토리 생성 서비스
완전한 스토리 (여러 페이지 + 선택지) 생성
테마 제한: 공포/미스터리/스릴러만
"""

import logging
import json
from typing import Dict, List, Any, Optional
from models.batch_models import (
    BatchStoryRequest, BatchStoryResponse,
    BatchPageData, BatchOptionData,
    BatchValidationResponse
)
from providers.llm_provider import LLMProviderFactory
from prompt.prompt_manager import get_prompt_manager
import random

logger = logging.getLogger(__name__)

ALLOWED_THEMES = ["미스터리", "공포", "스릴러"]

class BatchStoryService:
    """배치용 완전한 스토리 생성 서비스 - 테마 제한"""

    def __init__(self):
        self.provider = LLMProviderFactory.get_provider()
        self.prompt_manager = get_prompt_manager()

        self.default_story_length = 5
        self.min_story_length = 3
        self.max_story_length = 8


    async def generate_complete_story(self, request: BatchStoryRequest) -> BatchStoryResponse:
        """완전한 스토리 생성 (Spring Boot DB 저장용) - 테마 제한 적용"""
        try:
            story_info = await self._generate_story_metadata(request)

            if story_info.get("theme") not in ALLOWED_THEMES:
                story_info["theme"] = self._get_fallback_theme(request.station_name)

            pages = await self._generate_story_pages(request, story_info)

            response = BatchStoryResponse(
                story_title=story_info["story_title"],
                description=story_info["description"],
                theme=story_info["theme"],
                keywords=story_info["keywords"],
                pages=pages,
                estimated_length=len(pages),
                difficulty=story_info["difficulty"],
                station_name=request.station_name,
                line_number=request.line_number,
            )

            return response

        except Exception as e:
            logger.error("Batch story generation failed: %s", str(e), exc_info=True)
            return self._create_fallback_complete_story(request)

    async def _generate_story_metadata(self, request: BatchStoryRequest) -> Dict[str, Any]:
        """스토리 메타데이터 생성 - 테마 제한 적용"""
        try:
            provider_name = self.provider.get_provider_name().lower()

            if "mock" in provider_name:
                return self._create_mock_story_metadata(request)

            metadata_prompt = self._create_themed_metadata_prompt(request)

            context = {
                'station_name': request.station_name,
                'line_number': request.line_number
            }

            result = await self.provider.generate_story(metadata_prompt, **context)

            if isinstance(result, dict) and "story_title" in result:
                theme = result.get('theme')
                if theme not in ALLOWED_THEMES:
                    result['theme'] = self._get_fallback_theme(request.station_name)

                if 'keywords' in result:
                    result['keywords'].append(result.get('theme', '미스터리'))

                return result

            return self._create_mock_story_metadata(request)

        except Exception as e:
            return self._create_mock_story_metadata(request)

    def _create_themed_metadata_prompt(self, request: BatchStoryRequest) -> str:
        """테마 제한이 적용된 메타데이터 생성 프롬프트"""
        return f"""
{request.station_name}역을 배경으로 한 텍스트 어드벤처 게임의 메타데이터를 JSON 형식으로 생성해주세요.

중요: 테마 제한
- 반드시 다음 3개 테마 중 하나만 사용: "미스터리", "공포", "스릴러"
- 다른 테마는 절대 사용하지 마세요

역 정보:
- 역명: {request.station_name}역
- 노선: {request.line_number}호선

캐릭터 상태:
- 체력: {request.character_health}/100
- 정신력: {request.character_sanity}/100

JSON 응답 형식:
{{
    "story_title": "{request.station_name}역의 [테마] (20자 이내)",
    "description": "스토리 설명 (50-100자)",
    "theme": "미스터리|공포|스릴러",
    "keywords": ["{request.station_name}", "{request.line_number}호선", "지하철", "기타키워드"],
    "difficulty": "쉬움|보통|어려움",
    "estimated_length": 4-6
}}

테마별 가이드:
- 미스터리: 수수께끼, 단서, 의문의 사건
- 공포: 두려움, 어둠, 섬뜩한 분위기
- 스릴러: 긴장감, 추격, 시간 압박

반드시 허용된 테마만 사용하여 응답하세요.
"""

    async def _generate_story_pages(self, request: BatchStoryRequest, story_info: Dict) -> List[BatchPageData]:
        """스토리 페이지들 생성 - 테마 일관성 유지"""
        target_length = story_info.get("estimated_length", 5)
        pages = []
        theme = story_info.get("theme", "미스터리")

        for page_num in range(1, target_length + 1):
            try:
                page_data = await self._generate_single_page(
                    request, story_info, page_num, target_length, pages
                )

                if page_data:
                    pages.append(page_data)
                else:
                    pages.append(self._create_fallback_page(page_num, target_length, theme))

            except Exception as e:
                pages.append(self._create_fallback_page(page_num, target_length, theme))

        return pages

    def _validate_page_theme_consistency(self, page_data: BatchPageData, expected_theme: str) -> bool:
        return True

    async def _generate_single_page(self, request: BatchStoryRequest, story_info: Dict,
                                   page_num: int, total_pages: int,
                                   previous_pages: List[BatchPageData]) -> Optional[BatchPageData]:
        """단일 페이지 생성 - 테마 강제"""
        try:
            provider_name = self.provider.get_provider_name().lower()
            if "mock" in provider_name:
                return self._create_mock_page(request, story_info, page_num, total_pages)

            context = self._prepare_page_context(request, story_info, page_num, total_pages, previous_pages)

            theme = story_info.get("theme", "미스터리")
            page_prompt = f"""
다음 스토리의 {page_num}페이지를 생성해주세요:

**중요: 테마 고정**
- 반드시 "{theme}" 테마를 유지하세요
- 다른 테마로 변경하지 마세요

**스토리 정보:**
- 제목: {story_info['story_title']}
- 테마: {theme} (고정)
- 배경: {request.station_name}역 ({request.line_number}호선)
- 전체 길이: {total_pages}페이지 중 {page_num}페이지

**테마별 가이드:**
- 미스터리: 수수께끼, 단서 발견, 추리 요소
- 공포: 두려움, 섬뜩한 분위기, 위험한 상황
- 스릴러: 긴장감, 시간 압박, 예상치 못한 전개

**페이지 요구사항:**
- 150-300자의 흥미로운 내용
- 2-4개의 의미있는 선택지
- 선택지별 적절한 효과 (-10~+10)
- 테마에 맞는 분위기와 어조

JSON 형식으로만 응답하세요:
{{
    "content": "페이지 내용 (150-300자, {theme} 테마)",
    "options": [
        {{
            "content": "선택지 내용",
            "effect": "health|sanity|none",
            "amount": -5~+5,
            "effect_preview": "체력 +3"
        }}
    ]
}}
"""

            result = await self.provider.generate_story(page_prompt, **context)

            if isinstance(result, dict) and "content" in result and "options" in result:
                options = [
                    BatchOptionData(**opt) for opt in result["options"]
                    if isinstance(opt, dict) and all(k in opt for k in ["content", "effect", "amount", "effect_preview"])
                ]

                if len(options) >= 2:
                    return BatchPageData(
                        content=result["content"],
                        options=options
                    )

            return None

        except Exception as e:
            return None

    def _prepare_page_context(self, request: BatchStoryRequest, story_info: Dict,
                             page_num: int, total_pages: int,
                             previous_pages: List[BatchPageData]) -> Dict[str, Any]:
        """페이지 생성용 컨텍스트 준비"""
        context = {
            'station_name': request.station_name,
            'line_number': request.line_number,
            'character_health': request.character_health,
            'character_sanity': request.character_sanity,
            'story_title': story_info['story_title'],
            'theme': story_info['theme'],
            'page_number': page_num,
            'total_pages': total_pages,
            'is_first_page': page_num == 1,
            'is_last_page': page_num == total_pages
        }

        if previous_pages:
            context['previous_content'] = previous_pages[-1].content[:100] + "..."

        return context

    def _get_fallback_theme(self, station_name: str) -> str:
        """역 이름 기반 fallback 테마 선택"""
        theme_mapping = {
            "종각": "미스터리",
            "시청": "스릴러",
            "서울역": "미스터리",
            "강남": "스릴러",
            "홍대입구": "미스터리",
            "잠실": "공포",
            "압구정": "스릴러",
            "교대": "미스터리",
            "옥수": "미스터리",
            "명동": "스릴러",
            "혜화": "공포",
            "사당": "공포"
        }

        return theme_mapping.get(station_name, random.choice(ALLOWED_THEMES))

    async def validate_story_structure(self, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """스토리 구조 검증 - 테마 제한 포함"""
        try:
            errors = []
            warnings = []

            required_fields = ["story_title", "description", "theme", "keywords", "pages"]
            for field in required_fields:
                if field not in story_data:
                    errors.append(f"필수 필드 누락: {field}")

            theme = story_data.get("theme")
            if theme not in ALLOWED_THEMES:
                errors.append(f"허용되지 않은 테마: {theme} (허용: {ALLOWED_THEMES})")

            pages = story_data.get("pages", [])
            if not pages:
                errors.append("페이지가 없습니다")
            elif len(pages) < 3:
                warnings.append(f"페이지 수가 적습니다: {len(pages)}개")
            elif len(pages) > 10:
                warnings.append(f"페이지 수가 많습니다: {len(pages)}개")

            for i, page in enumerate(pages):
                if not isinstance(page, dict):
                    errors.append(f"페이지 {i+1} 형식 오류")
                    continue

                if "content" not in page:
                    errors.append(f"페이지 {i+1} 내용 누락")

                options = page.get("options", [])
                if len(options) < 2:
                    errors.append(f"페이지 {i+1} 선택지 부족: {len(options)}개")
                elif len(options) > 4:
                    warnings.append(f"페이지 {i+1} 선택지 과다: {len(options)}개")

                for j, option in enumerate(options):
                    if not isinstance(option, dict):
                        errors.append(f"페이지 {i+1} 선택지 {j+1} 형식 오류")
                        continue

                    option_fields = ["content", "effect", "amount", "effect_preview"]
                    for field in option_fields:
                        if field not in option:
                            errors.append(f"페이지 {i+1} 선택지 {j+1} {field} 누락")

            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "fixed_structure": None,
                "theme_valid": theme in ALLOWED_THEMES if theme else False
            }

        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"검증 오류: {str(e)}"],
                "warnings": [],
                "fixed_structure": None,
                "theme_valid": False
            }

    def _create_mock_story_metadata(self, request: BatchStoryRequest) -> Dict[str, Any]:
        """Mock 스토리 메타데이터 - 허용된 테마만"""
        selected_theme = self._get_fallback_theme(request.station_name)

        return {
            "story_title": f"{request.station_name}역의 {selected_theme}",
            "description": f"{request.station_name}역에서 벌어지는 {selected_theme} 이야기입니다.",
            "theme": selected_theme,
            "keywords": [
                request.station_name,
                f"{request.line_number}호선",
                "지하철",
                selected_theme,
                self._get_theme_keyword(selected_theme)
            ],
            "difficulty": self._get_difficulty_by_theme(selected_theme),
            "estimated_length": random.randint(4, 6)
        }

    def _get_theme_keyword(self, theme: str) -> str:
        """테마별 키워드"""
        keyword_map = {
            "공포": "두려움",
            "미스터리": "수수께끼",
            "스릴러": "긴장감"
        }
        return keyword_map.get(theme, "모험")

    def _get_difficulty_by_theme(self, theme: str) -> str:
        """테마별 난이도"""
        difficulty_map = {
            "공포": "어려움",
            "미스터리": "보통",
            "스릴러": "어려움"
        }
        return difficulty_map.get(theme, "보통")

    def _create_mock_page(self, request: BatchStoryRequest, story_info: Dict,
                         page_num: int, total_pages: int) -> BatchPageData:
        """Mock 페이지 데이터 - 테마별 특화"""
        theme = story_info.get("theme", "미스터리")

        if page_num == 1:
            content = self._get_themed_opening(request.station_name, theme)
        elif page_num == total_pages:
            content = self._get_themed_ending(request.station_name, theme)
        else:
            content = self._get_themed_middle(request.station_name, theme, page_num, total_pages)

        options = self._get_themed_options(theme)

        return BatchPageData(content=content, options=options)

    def _get_themed_opening(self, station_name: str, theme: str) -> str:
        """테마별 오프닝"""
        if theme == "공포":
            return f"{station_name}역에 도착한 순간, 섬뜩한 기운이 당신을 감쌉니다. 어둠 속에서 무언가가 움직이는 것 같고..."
        elif theme == "미스터리":
            return f"{station_name}역에서 이상한 일이 벌어지고 있습니다. 평소와 다른 분위기, 수상한 표지판들..."
        else:
            return f"{station_name}역에서 긴박한 상황이 발생했습니다. 누군가가 당신을 지켜보고 있는 것 같고..."

    def _get_themed_ending(self, station_name: str, theme: str) -> str:
        """테마별 엔딩"""
        if theme == "공포":
            return f"마침내 {station_name}역의 공포스러운 진실을 알아냈습니다. 이제 선택의 순간입니다..."
        elif theme == "미스터리":
            return f"{station_name}역의 수수께끼가 풀렸습니다. 모든 단서가 하나로 연결되며..."
        else:
            return f"{station_name}역에서의 긴박한 상황이 절정에 달했습니다. 최후의 결정을 내려야 합니다..."

    def _get_themed_middle(self, station_name: str, theme: str, page_num: int, total_pages: int) -> str:
        """테마별 중간 내용"""
        if theme == "공포":
            return f"공포스러운 상황이 계속됩니다... ({page_num}/{total_pages}페이지) {station_name}역의 어둠이 점점 깊어갑니다."
        elif theme == "미스터리":
            return f"수수께끼가 점점 복잡해집니다... ({page_num}/{total_pages}페이지) {station_name}역에 숨겨진 진실이 조금씩 드러나고 있습니다."
        else:
            return f"긴장감이 고조됩니다... ({page_num}/{total_pages}페이지) {station_name}역에서의 스릴 넘치는 상황이 이어집니다."

    def _get_themed_options(self, theme: str) -> List[BatchOptionData]:
        """테마별 선택지"""
        if theme == "공포":
            return [
                BatchOptionData(
                    content="용기를 내어 맞선다",
                    effect="health",
                    amount=-7,
                    effect_preview="체력 -7"
                ),
                BatchOptionData(
                    content="침착하게 상황을 관찰한다",
                    effect="sanity",
                    amount=3,
                    effect_preview="정신력 +3"
                )
            ]
        elif theme == "미스터리":
            return [
                BatchOptionData(
                    content="단서를 찾아 수사한다",
                    effect="health",
                    amount=-2,
                    effect_preview="체력 -2"
                ),
                BatchOptionData(
                    content="논리적으로 추리한다",
                    effect="sanity",
                    amount=4,
                    effect_preview="정신력 +4"
                )
            ]
        else:
            return [
                BatchOptionData(
                    content="대담하게 행동한다",
                    effect="health",
                    amount=-5,
                    effect_preview="체력 -5"
                ),
                BatchOptionData(
                    content="냉정하게 판단한다",
                    effect="sanity",
                    amount=3,
                    effect_preview="정신력 +3"
                )
            ]

    def _create_fallback_complete_story(self, request: BatchStoryRequest) -> BatchStoryResponse:
        """전체 생성 실패시 Fallback 스토리 - 테마 제한 적용"""
        metadata = self._create_mock_story_metadata(request)
        theme = metadata["theme"]

        pages = [
            self._create_fallback_page(1, 3, theme),
            self._create_fallback_page(2, 3, theme),
            self._create_fallback_page(3, 3, theme)
        ]

        return BatchStoryResponse(
            story_title=metadata["story_title"],
            description=metadata["description"],
            theme=metadata["theme"],
            keywords=metadata["keywords"],
            pages=pages,
            estimated_length=len(pages),
            difficulty=metadata["difficulty"],
            station_name=request.station_name,
            line_number=request.line_number
        )

    def _create_fallback_page(self, page_num: int, total_pages: int, theme: str = "미스터리") -> BatchPageData:
        """Fallback 페이지 - 테마별 특화"""
        if theme == "공포":
            content = f"공포스러운 상황이 계속됩니다. ({page_num}/{total_pages}페이지) 어둠 속에서 무언가가 당신을 노리고 있습니다."
            options = [
                BatchOptionData(
                    content="공포에 맞선다",
                    effect="health",
                    amount=-6,
                    effect_preview="체력 -6"
                ),
                BatchOptionData(
                    content="침착함을 유지한다",
                    effect="sanity",
                    amount=2,
                    effect_preview="정신력 +2"
                )
            ]
        elif theme == "미스터리":
            content = f"수수께끼가 더 복잡해집니다. ({page_num}/{total_pages}페이지) 새로운 단서가 나타났지만 의미를 파악하기 어렵습니다."
            options = [
                BatchOptionData(
                    content="단서를 분석한다",
                    effect="sanity",
                    amount=3,
                    effect_preview="정신력 +3"
                ),
                BatchOptionData(
                    content="직접 조사한다",
                    effect="health",
                    amount=-2,
                    effect_preview="체력 -2"
                )
            ]
        else:
            content = f"긴장감이 최고조에 달합니다. ({page_num}/{total_pages}페이지) 시간이 얼마 남지 않았고 빠른 판단이 필요합니다."
            options = [
                BatchOptionData(
                    content="즉시 행동한다",
                    effect="health",
                    amount=-4,
                    effect_preview="체력 -4"
                ),
                BatchOptionData(
                    content="냉정하게 생각한다",
                    effect="sanity",
                    amount=2,
                    effect_preview="정신력 +2"
                )
            ]

        return BatchPageData(content=content, options=options)
