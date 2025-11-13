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

# ===== 품질 관련 데이터 클래스들 =====

@dataclass
class ValidationResult:
    """JSON 검증 결과"""
    is_valid: bool
    errors: List[str]
    fixed_json: Optional[Dict[str, Any]] = None

@dataclass
class QualityScore:
    """품질 평가 점수"""
    total_score: float  # 0-100
    creativity: float   # 창의성 (0-20)
    coherence: float    # 일관성 (0-20)
    engagement: float   # 몰입도 (0-20)
    korean_quality: float  # 한국어 품질 (0-20)
    game_suitability: float  # 게임 적합성 (0-20)
    feedback: str
    passed: bool  # 최소 점수 통과 여부

class StoryService:
    """스토리 생성 서비스 (품질 파이프라인 + 외부 프롬프트)"""
    
    def __init__(self, min_quality_score: float = 70.0, max_retries: int = 3):
        logger.info("🎬 StoryService 초기화")
        logger.info(f"  최소 품질 점수: {min_quality_score}")
        logger.info(f"  최대 재시도: {max_retries}")
        
        self.provider = LLMProviderFactory.get_provider()
        self.prompt_manager = get_prompt_manager()
        self.min_quality_score = min_quality_score
        self.max_retries = max_retries
        
        logger.info(f"  사용할 Provider: {self.provider.get_provider_name()}")
        logger.info(f"  Provider 타입: {type(self.provider).__name__}")
        
        # 기존 통계 + 품질 통계
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
                "excellent": 0,  # 90+
                "good": 0,       # 80-89
                "acceptable": 0, # 70-79
                "poor": 0        # <70
            }
        }
    
    async def generate_story(self, request: StoryGenerationRequest) -> StoryGenerationResponse:
        """품질 파이프라인을 통한 스토리 생성"""
        start_time = time.time()
        self.quality_stats["total_requests"] += 1
        
        logger.info("=" * 60)
        logger.info("🚀 StoryService.generate_story 시작")
        logger.info(f"📍 요청 정보:")
        logger.info(f"  역명: {request.station_name}")
        logger.info(f"  노선: {request.line_number}")
        logger.info(f"  캐릭터 상태: 체력={request.character_health}, 정신력={request.character_sanity}")
        logger.info(f"  선호 테마: {request.theme_preference}")
        logger.info(f"🤖 사용할 Provider: {self.provider.get_provider_name()}")
        logger.info(f"📊 현재 통계: 총 요청 {self.quality_stats['total_requests']}")
        logger.info("=" * 60)
        
        try:
            # 컨텍스트 준비
            context = {
                'station_name': request.station_name,
                'line_number': request.line_number,
                'character_health': request.character_health,
                'character_sanity': request.character_sanity,
                'theme_preference': request.theme_preference
            }
            
            logger.info("📋 컨텍스트 준비 완료:")
            logger.info(f"  {context}")
            
            # 품질 파이프라인을 통한 스토리 생성
            logger.info("🔄 품질 파이프라인 시작")
            story_data = await self._generate_validated_story(context)
            
            # 통계 업데이트
            generation_time = time.time() - start_time
            logger.info(f"⏱️ 총 생성 시간: {generation_time:.2f}초")
            
            self._update_quality_stats(request.station_name, story_data, generation_time)
            
            # 응답 형식으로 변환
            logger.info("📝 응답 형식 변환 시작")
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
            
            logger.info("✅ StoryService.generate_story 완료")
            logger.info(f"📈 최종 결과:")
            logger.info(f"  제목: {response.story_title}")
            logger.info(f"  테마: {response.theme}")
            logger.info(f"  선택지 수: {len(response.options)}")
            logger.info(f"  품질점수: {story_data.get('quality_score', 'N/A')}")
            logger.info(f"  소요시간: {generation_time:.2f}초")
            logger.info("=" * 60)
            
            return response
            
        except Exception as e:
            logger.error("❌ StoryService.generate_story 실패")
            logger.error(f"  오류 타입: {type(e).__name__}")
            logger.error(f"  오류 메시지: {str(e)}")
            logger.error(f"  스택 트레이스:", exc_info=True)
            
            self.quality_stats["quality_failures"] += 1
            
            logger.warning("⚠️ Fallback 응답 생성")
            return self._create_fallback_response(request)
    
    async def continue_story(self, request: StoryContinueRequest) -> StoryContinueResponse:
        """스토리 진행 (기존 로직 유지)"""
        logger.info("📖 StoryService.continue_story 시작")
        logger.info(f"  역명: {request.station_name}")
        logger.info(f"  이전 선택: {request.previous_choice}")
        
        provider = LLMProviderFactory.get_provider()
        
        # Mock Provider인 경우 특별 처리
        if provider.get_provider_name() == "Mock Provider":
            logger.info("🎭 Mock Provider로 스토리 진행")
            from templates.mock_templates import MockStoryGenerator
            generator = MockStoryGenerator()
            
            continuation_data = generator.continue_story(
                request.previous_choice,
                request.station_name,
                request.character_health,
                request.character_sanity
            )
        else:
            # 실제 LLM Provider 처리 - 외부 프롬프트 사용
            logger.info("🤖 실제 LLM Provider로 스토리 진행")
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
        
        logger.info("✅ StoryService.continue_story 완료")
        return response
    
    # ===== 품질 파이프라인 메서드들 =====
    
    async def _generate_validated_story(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """검증된 고품질 스토리 생성"""
        logger.info("🔄 _generate_validated_story 시작")
        logger.info(f"  최대 재시도: {self.max_retries}")
        logger.info(f"  최소 품질 점수: {self.min_quality_score}")
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"🎲 스토리 생성 시도 {attempt + 1}/{self.max_retries}")
                
                # 1단계: 외부 프롬프트로 스토리 생성
                logger.info("1️⃣ 외부 프롬프트로 스토리 생성")
                story_result = await self._generate_story_with_external_prompt(context)
                if not story_result:
                    logger.warning(f"❌ 시도 {attempt + 1}: 스토리 생성 실패")
                    continue
                
                logger.info(f"✅ 시도 {attempt + 1}: 스토리 생성 성공")
                
                # 2단계: JSON 검증
                logger.info("2️⃣ JSON 구조 검증")
                validation_result = self._validate_json_structure(story_result)
                if not validation_result.is_valid:
                    logger.warning(f"❌ 시도 {attempt + 1}: JSON 검증 실패: {validation_result.errors}")
                    self.quality_stats["json_failures"] += 1
                    continue
                
                logger.info(f"✅ 시도 {attempt + 1}: JSON 검증 통과")
                
                # 3단계: 품질 평가
                logger.info("3️⃣ 품질 평가")
                quality_score = await self._evaluate_story_quality(story_result)
                if not quality_score.passed:
                    logger.warning(f"❌ 시도 {attempt + 1}: 품질 평가 실패")
                    logger.warning(f"  점수: {quality_score.total_score:.1f}/{self.min_quality_score}")
                    logger.info(f"  피드백: {quality_score.feedback}")
                    continue
                
                # 성공!
                logger.info(f"🎉 고품질 스토리 생성 성공! (시도 {attempt + 1})")
                logger.info(f"  최종 점수: {quality_score.total_score:.1f}")
                logger.info(f"  피드백: {quality_score.feedback}")
                
                story_result["quality_score"] = quality_score.total_score
                story_result["quality_feedback"] = quality_score.feedback
                
                return story_result
                
            except Exception as e:
                logger.error(f"❌ 스토리 생성 시도 {attempt + 1} 예외 발생")
                logger.error(f"  오류: {str(e)}")
                logger.error(f"  스택 트레이스:", exc_info=True)
                continue
        
        # 모든 시도 실패시 fallback
        logger.error("❌ 모든 품질 시도 실패, fallback 스토리 반환")
        return self._create_fallback_story(context)
    
    async def _generate_story_with_external_prompt(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """외부 프롬프트 파일을 사용한 스토리 생성"""
        logger.info("🎯 _generate_story_with_external_prompt 시작")
        logger.info(f"  Provider: {self.provider.get_provider_name()}")
        logger.info(f"  Provider 타입: {type(self.provider).__name__}")
        logger.info(f"  Context: {context}")
        
        try:
            # Provider 타입 결정
            provider_name = self.provider.get_provider_name().lower()
            logger.info(f"  Provider name (lower): {provider_name}")
            
            if "openai" in provider_name:
                prompt_provider = "openai"
            elif "claude" in provider_name:
                prompt_provider = "claude"
            else:
                prompt_provider = "openai"
            
            logger.info(f"  선택된 prompt_provider: {prompt_provider}")
            
            # 외부 프롬프트 매니저에서 프롬프트 가져오기
            story_prompt = self.prompt_manager.get_story_prompt(prompt_provider)
            user_prompt = self.prompt_manager.create_user_prompt(context, "generation")
            full_prompt = f"{story_prompt}\n\n{user_prompt}"
            
            logger.info(f"  생성된 프롬프트 길이: {len(full_prompt)}")
            logger.info(f"  프롬프트 미리보기: {full_prompt[:200]}...")
            
            # 🆕 중요: LLM 호출 직전 로그
            logger.info("🚀 LLM Provider 호출 시작")
            logger.info(f"  호출할 Provider: {type(self.provider).__name__}")
            logger.info(f"  Provider 메서드: generate_story")
            logger.info(f"  Provider 사용 가능 여부: {self.provider.is_available()}")
            
            # LLM 호출
            result = await self.provider.generate_story(full_prompt, **context)
            
            # 🆕 LLM 호출 후 로그
            logger.info("📥 LLM Provider 호출 완료")
            logger.info(f"  결과 타입: {type(result)}")
            if isinstance(result, dict):
                logger.info(f"  결과 키들: {list(result.keys())}")
                logger.info(f"  story_title: {result.get('story_title', 'N/A')}")
                logger.info(f"  page_content 길이: {len(result.get('page_content', ''))}")
                logger.info(f"  options 개수: {len(result.get('options', []))}")
            else:
                logger.warning(f"  예상치 못한 결과 타입: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 외부 프롬프트 스토리 생성 실패")
            logger.error(f"  오류 타입: {type(e).__name__}")
            logger.error(f"  오류 메시지: {str(e)}")
            logger.error(f"  스택 트레이스:", exc_info=True)
            return None
    
    def _validate_json_structure(self, story_data: Dict[str, Any]) -> ValidationResult:
        """JSON 구조 검증 (간소화)"""
        logger.info("🔍 JSON 구조 검증 시작")
        
        try:
            errors = []
            
            # 필수 필드 확인
            required_fields = ["story_title", "page_content", "options", "difficulty", "theme", "station_name", "line_number"]
            for field in required_fields:
                if field not in story_data:
                    errors.append(f"필수 필드 누락: {field}")
            
            # options 검증
            options = story_data.get("options", [])
            if not isinstance(options, list) or len(options) < 2 or len(options) > 4:
                errors.append(f"선택지 개수 오류: {len(options)}개 (2-4개 필요)")
            
            # 각 선택지 검증
            for i, option in enumerate(options):
                if not isinstance(option, dict):
                    errors.append(f"선택지 {i+1} 형식 오류")
                    continue
                
                option_fields = ["content", "effect", "amount", "effect_preview"]
                for field in option_fields:
                    if field not in option:
                        errors.append(f"선택지 {i+1} 필드 누락: {field}")
                
                # 효과 값 검증
                if option.get("effect") not in ["health", "sanity", "none"]:
                    errors.append(f"선택지 {i+1} effect 값 오류: {option.get('effect')}")
                
                # 수치 검증
                amount = option.get("amount")
                if not isinstance(amount, int) or amount < -10 or amount > 10:
                    errors.append(f"선택지 {i+1} amount 값 오류: {amount}")
            
            is_valid = len(errors) == 0
            
            logger.info(f"  검증 결과: {'✅ 통과' if is_valid else '❌ 실패'}")
            if errors:
                logger.info(f"  오류 목록: {errors}")
            
            return ValidationResult(is_valid=is_valid, errors=errors)
            
        except Exception as e:
            logger.error(f"❌ JSON 검증 실패: {str(e)}")
            return ValidationResult(is_valid=False, errors=[str(e)])
    
    async def _evaluate_story_quality(self, story_data: Dict[str, Any]) -> QualityScore:
        """외부 프롬프트를 사용한 품질 평가"""
        logger.info("🎨 품질 평가 시작")
        
        try:
            provider_name = self.provider.get_provider_name().lower()
            prompt_provider = "openai" if "openai" in provider_name else "claude"
            
            logger.info(f"  평가용 프롬프트 Provider: {prompt_provider}")
            
            # 외부 평가 프롬프트 사용
            evaluation_prompt = self.prompt_manager.get_evaluation_prompt(prompt_provider)
            
            evaluation_request = f"""다음 스토리를 평가해주세요:

**스토리 데이터:**
{json.dumps(story_data, ensure_ascii=False, indent=2)}

위 스토리의 품질을 5개 기준으로 평가하고 JSON 형식으로 반환해주세요."""

            full_prompt = f"{evaluation_prompt}\n\n{evaluation_request}"
            
            logger.info("🤖 품질 평가를 위한 LLM 호출")
            result = await self.provider.generate_story(full_prompt)
            
            # 결과 파싱
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
                
                logger.info(f"  평가 점수: {total_score:.1f}")
                logger.info(f"  통과 여부: {'✅' if quality_score.passed else '❌'}")
                
                return quality_score
            
            # 파싱 실패시 기본값
            logger.warning("⚠️ 품질 평가 결과 파싱 실패")
            return QualityScore(
                total_score=0, creativity=0, coherence=0, engagement=0,
                korean_quality=0, game_suitability=0,
                feedback="품질 평가 실패", passed=False
            )
            
        except Exception as e:
            logger.error(f"❌ 품질 평가 실패: {str(e)}")
            return QualityScore(
                total_score=0, creativity=0, coherence=0, engagement=0,
                korean_quality=0, game_suitability=0,
                feedback=f"평가 오류: {str(e)}", passed=False
            )
    
    # ===== 통계 및 관리 메서드들 =====
    
    def _update_quality_stats(self, station_name: str, story_data: Dict, generation_time: float):
        """품질 통계 업데이트"""
        try:
            logger.info("📊 품질 통계 업데이트")
            self.quality_stats["successful_generations"] += 1
            
            # 평균 생성 시간 업데이트
            current_avg = self.quality_stats["average_generation_time"]
            count = self.quality_stats["successful_generations"]
            self.quality_stats["average_generation_time"] = ((current_avg * (count - 1)) + generation_time) / count
            
            # 역별 인기도 업데이트 (기존 로직)
            station_key = f"{station_name}_{story_data.get('line_number', 0)}"
            self.popular_stations[station_key] = self.popular_stations.get(station_key, 0) + 1
            
            # 품질 점수 통계
            quality_score = story_data.get("quality_score", 0)
            if quality_score > 0:
                current_avg_score = self.quality_stats["average_score"]
                self.quality_stats["average_score"] = ((current_avg_score * (count - 1)) + quality_score) / count
                
                # 품질 분포 업데이트
                if quality_score >= 90:
                    self.quality_stats["quality_distribution"]["excellent"] += 1
                elif quality_score >= 80:
                    self.quality_stats["quality_distribution"]["good"] += 1
                elif quality_score >= 70:
                    self.quality_stats["quality_distribution"]["acceptable"] += 1
                else:
                    self.quality_stats["quality_distribution"]["poor"] += 1
            
            logger.info(f"  평균 생성 시간: {self.quality_stats['average_generation_time']:.2f}초")
            logger.info(f"  평균 품질 점수: {self.quality_stats['average_score']:.1f}")
                    
        except Exception as e:
            logger.warning(f"⚠️ 통계 업데이트 실패: {str(e)}")
    
    def _create_fallback_response(self, request: StoryGenerationRequest) -> StoryGenerationResponse:
        """Fallback 응답 생성"""
        logger.warning("⚠️ Fallback 스토리 응답 생성")
        
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
        logger.warning("⚠️ Fallback 스토리 데이터 생성")
        
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
    
    # ===== 기존 메서드들 유지 =====
    
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
    
    # ===== 품질 관련 메서드들 =====
    
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
            logger.info(f"최소 품질 점수 업데이트: {min_quality_score}")
        
        if max_retries is not None:
            self.max_retries = max_retries
            logger.info(f"최대 재시도 횟수 업데이트: {max_retries}")
    
    def reset_quality_stats(self):
        """품질 통계 초기화"""
        logger.info("품질 통계 초기화")
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
        # 기존 통계도 초기화
        self.popular_stations.clear()
        self.request_count.clear()
    
    def reload_prompts(self):
        """프롬프트 파일 다시 로딩"""
        self.prompt_manager.reload_prompts()
        logger.info("프롬프트 파일 다시 로딩 완료")