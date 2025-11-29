"""
스토리 생성 서비스 (디버깅 로그 추가)
"""

from typing import Dict, List, Optional, Any
from models.request_models import StoryGenerationRequest, StoryContinueRequest
from models.response_models import StoryGenerationResponse, StoryContinueResponse, OptionData
from providers.llm_provider import LLMProviderFactory
from prompt.prompt_manager import get_prompt_manager
from dataclasses import dataclass
import logging
import json
import time
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """JSON 검증 결과"""
    is_valid: bool
    errors: List[str]
    fixed_json: Optional[Dict[str, Any]] = None

@dataclass
class QualityScore:
    """품질 평가 점수"""
    total_score: float
    creativity: float
    coherence: float
    engagement: float
    korean_quality: float
    game_suitability: float
    feedback: str
    passed: bool

class StoryService:
    """스토리 생성 서비스 (품질 파이프라인 + 외부 프롬프트)"""

    def __init__(self, min_quality_score: float = 70.0, max_retries: int = 3):

        self.provider = LLMProviderFactory.get_provider()
        self.prompt_manager = get_prompt_manager()
        self.min_quality_score = min_quality_score
        self.max_retries = max_retries

        self.request_count = {}
        self.popular_stations = {}
        self.quality_stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "quality_failures": 0,
            "json_failures": 0,
            "average_score": 0.0,
            "average_generation_time": 0.0,
            "quality_distribution": {
                "excellent": 0,
                "good": 0,
                "acceptable": 0,
                "poor": 0
            }
        }

    async def generate_story(self, request: StoryGenerationRequest) -> StoryGenerationResponse:
        """품질 파이프라인을 통한 스토리 생성"""
        start_time = time.time()
        self.quality_stats["total_requests"] += 1

        try:
            context = {
                'station_name': request.station_name,
                'line_number': request.line_number,
                'character_health': request.character_health,
                'character_sanity': request.character_sanity,
                'theme_preference': request.theme_preference
            }

            story_data = await self._generate_validated_story(context)

            generation_time = time.time() - start_time

            self._update_quality_stats(request.station_name, story_data, generation_time)

            response = StoryGenerationResponse(
                story_title=story_data["story_title"],
                page_content=story_data["page_content"],
                options=[OptionData(**opt) for opt in story_data["options"]],
                estimated_length=story_data.get("estimated_length", 5),
                difficulty=story_data.get("difficulty", "보통"),
                theme=story_data.get("theme", "미스터리"),
                station_name=story_data.get("station_name", request.station_name),
                line_number=story_data.get("line_number", request.line_number)
            )

            return response

        except Exception as e:
            logger.error("StoryService.generate_story 실패")
            logger.error(f"  오류 타입: {type(e).__name__}")
            logger.error(f"  오류 메시지: {str(e)}")
            logger.error(f"  스택 트레이스:", exc_info=True)

            self.quality_stats["quality_failures"] += 1

            return self._create_fallback_response(request)

    async def continue_story(self, request: StoryContinueRequest) -> StoryContinueResponse:
        """스토리 진행 (기존 로직 유지)"""

        provider = LLMProviderFactory.get_provider()

        if provider.get_provider_name() == "Mock Provider":
            from templates.mock_templates import MockStoryGenerator
            generator = MockStoryGenerator()

            continuation_data = generator.continue_story(
                request.previous_choice,
                request.station_name,
                request.character_health,
                request.character_sanity
            )
        else:
            context = {
                'station_name': request.station_name,
                'line_number': request.line_number,
                'character_health': request.character_health,
                'character_sanity': request.character_sanity,
                'previous_choice': request.previous_choice,
                'story_context': request.story_context
            }

            user_prompt = self.prompt_manager.create_user_prompt(context, "continuation")
            continuation_data = await provider.generate_story(user_prompt, **context)

        response = StoryContinueResponse(
            page_content=continuation_data["page_content"],
            options=[OptionData(**opt) for opt in continuation_data["options"]],
            is_last_page=continuation_data.get("is_last_page", False)
        )

        return response

    async def _generate_validated_story(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """검증된 고품질 스토리 생성"""

        for attempt in range(self.max_retries):
            try:

                story_result = await self._generate_story_with_external_prompt(context)
                if not story_result:
                    continue

                validation_result = self._validate_json_structure(story_result)
                if not validation_result.is_valid:
                    self.quality_stats["json_failures"] += 1
                    continue

                quality_score = await self._evaluate_story_quality(story_result)
                if not quality_score.passed:
                    continue

                story_result["quality_score"] = quality_score.total_score
                story_result["quality_feedback"] = quality_score.feedback

                return story_result

            except Exception as e:
                logger.error(f"스토리 생성 시도 {attempt + 1} 예외 발생")
                logger.error(f"  오류: {str(e)}")
                logger.error(f"  스택 트레이스:", exc_info=True)
                continue

        logger.error("모든 품질 시도 실패, fallback 스토리 반환")
        return self._create_fallback_story(context)

    async def _generate_story_with_external_prompt(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """외부 프롬프트 파일을 사용한 스토리 생성"""

        try:
            provider_name = self.provider.get_provider_name().lower()

            if "openai" in provider_name:
                prompt_provider = "openai"
            elif "claude" in provider_name:
                prompt_provider = "claude"
            else:
                prompt_provider = "openai"

            story_prompt = self.prompt_manager.get_story_prompt(prompt_provider)
            user_prompt = self.prompt_manager.create_user_prompt(context, "generation")
            full_prompt = f"{story_prompt}\n\n{user_prompt}"

            result = await self.provider.generate_story(full_prompt, **context)

            return result

        except Exception as e:
            logger.error(f"외부 프롬프트 스토리 생성 실패")
            logger.error(f"  오류 타입: {type(e).__name__}")
            logger.error(f"  오류 메시지: {str(e)}")
            logger.error(f"  스택 트레이스:", exc_info=True)
            return None

    def _validate_json_structure(self, story_data: Dict[str, Any]) -> ValidationResult:
        """JSON 구조 검증 (간소화)"""

        try:
            errors = []

            required_fields = ["story_title", "page_content", "options", "difficulty", "theme", "station_name", "line_number"]
            for field in required_fields:
                if field not in story_data:
                    errors.append(f"필수 필드 누락: {field}")

            options = story_data.get("options", [])
            if not isinstance(options, list) or len(options) < 2 or len(options) > 4:
                errors.append(f"선택지 개수 오류: {len(options)}개 (2-4개 필요)")

            for i, option in enumerate(options):
                if not isinstance(option, dict):
                    errors.append(f"선택지 {i+1} 형식 오류")
                    continue

                option_fields = ["content", "effect", "amount", "effect_preview"]
                for field in option_fields:
                    if field not in option:
                        errors.append(f"선택지 {i+1} 필드 누락: {field}")

                if option.get("effect") not in ["health", "sanity", "none"]:
                    errors.append(f"선택지 {i+1} effect 값 오류: {option.get('effect')}")

                amount = option.get("amount")
                if not isinstance(amount, int) or amount < -10 or amount > 10:
                    errors.append(f"선택지 {i+1} amount 값 오류: {amount}")

            is_valid = len(errors) == 0
            return ValidationResult(is_valid=is_valid, errors=errors)

        except Exception as e:
            logger.error(f"JSON 검증 실패: {str(e)}")
            return ValidationResult(is_valid=False, errors=[str(e)])

    async def _evaluate_story_quality(self, story_data: Dict[str, Any]) -> QualityScore:
        """외부 프롬프트를 사용한 품질 평가"""

        try:
            provider_name = self.provider.get_provider_name().lower()
            prompt_provider = "openai" if "openai" in provider_name else "claude"

            evaluation_prompt = self.prompt_manager.get_evaluation_prompt(prompt_provider)

            evaluation_request = f"""다음 스토리를 평가해주세요:

**스토리 데이터:**
{json.dumps(story_data, ensure_ascii=False, indent=2)}

위 스토리의 품질을 5개 기준으로 평가하고 JSON 형식으로 반환해주세요."""

            full_prompt = f"{evaluation_prompt}\n\n{evaluation_request}"

            result = await self.provider.generate_story(full_prompt)

            if isinstance(result, dict):
                total_score = result.get("total_score", 0)
                quality_score = QualityScore(
                    total_score=total_score,
                    creativity=result.get("creativity", 0),
                    coherence=result.get("coherence", 0),
                    engagement=result.get("engagement", 0),
                    korean_quality=result.get("korean_quality", 0),
                    game_suitability=result.get("game_suitability", 0),
                    feedback=result.get("feedback", "평가 완료"),
                    passed=total_score >= self.min_quality_score
                )

                return quality_score

            return QualityScore(
                total_score=0, creativity=0, coherence=0, engagement=0,
                korean_quality=0, game_suitability=0,
                feedback="품질 평가 실패", passed=False
            )

        except Exception as e:
            logger.error(f"품질 평가 실패: {str(e)}")
            return QualityScore(
                total_score=0, creativity=0, coherence=0, engagement=0,
                korean_quality=0, game_suitability=0,
                feedback=f"평가 오류: {str(e)}", passed=False
            )

    def _update_quality_stats(self, station_name: str, story_data: Dict, generation_time: float):
        """품질 통계 업데이트"""
        try:
            self.quality_stats["successful_generations"] += 1

            current_avg = self.quality_stats["average_generation_time"]
            count = self.quality_stats["successful_generations"]
            self.quality_stats["average_generation_time"] = ((current_avg * (count - 1)) + generation_time) / count

            station_key = f"{station_name}_{story_data.get('line_number', 0)}"
            self.popular_stations[station_key] = self.popular_stations.get(station_key, 0) + 1

            quality_score = story_data.get("quality_score", 0)
            if quality_score > 0:
                current_avg_score = self.quality_stats["average_score"]
                self.quality_stats["average_score"] = ((current_avg_score * (count - 1)) + quality_score) / count

                if quality_score >= 90:
                    self.quality_stats["quality_distribution"]["excellent"] += 1
                elif quality_score >= 80:
                    self.quality_stats["quality_distribution"]["good"] += 1
                elif quality_score >= 70:
                    self.quality_stats["quality_distribution"]["acceptable"] += 1
                else:
                    self.quality_stats["quality_distribution"]["poor"] += 1

        except Exception as e:
            pass

    def _create_fallback_response(self, request: StoryGenerationRequest) -> StoryGenerationResponse:
        """Fallback 응답 생성"""

        return StoryGenerationResponse(
            story_title=f"{request.station_name}역의 상황",
            page_content=f"{request.station_name}역에서 예상치 못한 일이 벌어졌습니다. 주변 상황을 파악하고 신중하게 행동해야 합니다.",
            options=[
                OptionData(
                    content="상황을 자세히 관찰한다",
                    effect="sanity",
                    amount=2,
                    effect_preview="정신력 +2"
                ),
                OptionData(
                    content="빠르게 대응한다",
                    effect="health",
                    amount=-1,
                    effect_preview="체력 -1"
                )
            ],
            estimated_length=5,
            difficulty="보통",
            theme="일상",
            station_name=request.station_name,
            line_number=request.line_number
        )

    def _create_fallback_story(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback 스토리 데이터 (고품질 생성 실패시)"""

        return {
            "story_title": f"{context.get('station_name', '강남')}역의 모험",
            "page_content": f"{context.get('station_name', '강남')}역에서 예상치 못한 상황이 벌어졌습니다. 신중하게 대처해야 할 때입니다.",
            "options": [
                {
                    "content": "주변을 신중하게 관찰한다",
                    "effect": "sanity",
                    "amount": 3,
                    "effect_preview": "정신력 +3"
                },
                {
                    "content": "빠르게 행동한다",
                    "effect": "health",
                    "amount": -2,
                    "effect_preview": "체력 -2"
                }
            ],
            "estimated_length": 5,
            "difficulty": "보통",
            "theme": "미스터리",
            "station_name": context.get('station_name', '강남'),
            "line_number": context.get('line_number', 2),
            "quality_score": 60.0,
            "quality_feedback": "Fallback 스토리 (품질 검증 우회)"
        }

    def get_supported_stations(self) -> List[Dict]:
        """지원 역 목록"""
        from templates.mock_templates import STATION_CONFIG

        return [
            {
                "station_name": station,
                "line_number": config["line"],
                "theme": config["theme"].value,
                "difficulty": config.get("difficulty", "보통"),
                "popularity": self.popular_stations.get(f"{station}_{config['line']}", 0)
            }
            for station, config in STATION_CONFIG.items()
        ]

    def get_popular_stations(self) -> Dict:
        """인기 역 통계"""
        return dict(sorted(self.popular_stations.items(), key=lambda x: x[1], reverse=True)[:10])

    def get_quality_stats(self) -> Dict:
        """품질 통계 반환"""
        return {
            **self.quality_stats,
            "provider": self.provider.get_provider_name(),
            "min_quality_score": self.min_quality_score,
            "success_rate": (
                self.quality_stats["successful_generations"] / max(self.quality_stats["total_requests"], 1) * 100
            ),
            "last_updated": datetime.now().isoformat()
        }

    def get_quality_report(self) -> Dict:
        """품질 보고서"""
        total_quality_stories = sum(self.quality_stats["quality_distribution"].values())

        if total_quality_stories == 0:
            return {"message": "품질 데이터 없음"}

        return {
            "average_score": round(self.quality_stats["average_score"], 2),
            "total_evaluated": total_quality_stories,
            "distribution": {
                "excellent_90+": {
                    "count": self.quality_stats["quality_distribution"]["excellent"],
                    "percentage": round(self.quality_stats["quality_distribution"]["excellent"] / total_quality_stories * 100, 1)
                },
                "good_80_89": {
                    "count": self.quality_stats["quality_distribution"]["good"],
                    "percentage": round(self.quality_stats["quality_distribution"]["good"] / total_quality_stories * 100, 1)
                },
                "acceptable_70_79": {
                    "count": self.quality_stats["quality_distribution"]["acceptable"],
                    "percentage": round(self.quality_stats["quality_distribution"]["acceptable"] / total_quality_stories * 100, 1)
                },
                "poor_below_70": {
                    "count": self.quality_stats["quality_distribution"]["poor"],
                    "percentage": round(self.quality_stats["quality_distribution"]["poor"] / total_quality_stories * 100, 1)
                }
            }
        }

    def update_quality_config(self, min_quality_score: float = None, max_retries: int = None):
        """품질 설정 업데이트"""
        if min_quality_score is not None:
            self.min_quality_score = min_quality_score

        if max_retries is not None:
            self.max_retries = max_retries

    def reset_quality_stats(self):
        """품질 통계 초기화"""
        self.quality_stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "quality_failures": 0,
            "json_failures": 0,
            "average_score": 0.0,
            "average_generation_time": 0.0,
            "quality_distribution": {
                "excellent": 0,
                "good": 0,
                "acceptable": 0,
                "poor": 0
            }
        }
        self.popular_stations.clear()
        self.request_count.clear()

    def reload_prompts(self):
        """프롬프트 파일 다시 로딩"""
        self.prompt_manager.reload_prompts()
