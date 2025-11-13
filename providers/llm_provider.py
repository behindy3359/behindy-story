"""
개선된 LLM Provider (디버깅 로그 추가)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import json
import aiohttp
import logging
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

@dataclass
class StoryPromptContext:
    """스토리 생성용 프롬프트 컨텍스트"""
    station_name: str
    line_number: int
    character_health: int
    character_sanity: int
    theme_preference: Optional[str] = None
    previous_choice: Optional[str] = None
    story_context: Optional[str] = None

class LLMProvider(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    async def generate_story(self, prompt: str, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """프로바이더 사용 가능 여부"""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI GPT Provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", max_tokens: int = 1000):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
        # 🆕 초기화 로그
        logger.info("🔧 OpenAIProvider 초기화")
        logger.info(f"  API 키 마스킹: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else '짧음'}")
        logger.info(f"  모델: {model}")
        logger.info(f"  최대 토큰: {max_tokens}")
        logger.info(f"  Base URL: {self.base_url}")
    
    def is_available(self) -> bool:
        available = bool(self.api_key and self.api_key != "" and aiohttp is not None)
        logger.info(f"🔍 OpenAI Provider 사용 가능 체크: {available}")
        logger.info(f"  API 키 존재: {bool(self.api_key)}")
        logger.info(f"  API 키 길이: {len(self.api_key) if self.api_key else 0}")
        logger.info(f"  aiohttp 사용 가능: {aiohttp is not None}")
        return available

    async def generate_story(self, prompt: str, **kwargs) -> Dict[str, Any]:
        # 🆕 메서드 진입 확인 로그 (최상단에)
        logger.info("🎯 OpenAIProvider.generate_story 메서드 진입")
        logger.info(f"  프롬프트 길이: {len(prompt)}")
        logger.info(f"  kwargs: {kwargs}")
        
        if not self.is_available():
            logger.error("❌ OpenAIProvider 사용 불가")
            logger.error(f"  API 키 존재: {bool(self.api_key)}")
            logger.error(f"  API 키 길이: {len(self.api_key) if self.api_key else 0}")
            logger.error(f"  aiohttp 사용 가능: {aiohttp is not None}")
            raise ValueError("OpenAI API 키가 설정되지 않았거나 aiohttp가 설치되지 않았습니다.")
        
        # 🆕 요청 전 로그
        logger.info("🔥 OpenAI API 호출 시작")
        logger.info(f"  모델: {self.model}")
        logger.info(f"  최대 토큰: {self.max_tokens}")
        logger.info(f"  프롬프트 길이: {len(prompt)}자")
        logger.info(f"  컨텍스트: {kwargs}")
        logger.info(f"  프롬프트 미리보기: {prompt[:300]}...")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0.8,
            "response_format": {"type": "json_object"}
        }
        
        logger.info(f"📤 OpenAI 요청 페이로드:")
        logger.info(f"  모델: {payload['model']}")
        logger.info(f"  temperature: {payload['temperature']}")
        logger.info(f"  response_format: {payload['response_format']}")
        logger.info(f"  Authorization 헤더: Bearer {self.api_key[:20]}...")
        
        try:
            start_time = time.time()
            
            logger.info("📡 aiohttp 세션 생성 및 POST 요청 시작")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload, timeout=30) as response:
                    
                    # 🆕 응답 수신 로그
                    response_time = time.time() - start_time
                    logger.info(f"📥 OpenAI API 응답 수신:")
                    logger.info(f"  HTTP 상태: {response.status}")
                    logger.info(f"  응답 시간: {response_time:.2f}초")
                    logger.info(f"  응답 헤더: {dict(response.headers)}")
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # 🆕 응답 내용 상세 로그
                        logger.info("✅ OpenAI 응답 성공:")
                        logger.info(f"  응답 ID: {result.get('id', 'N/A')}")
                        logger.info(f"  생성된 시간: {result.get('created', 'N/A')}")
                        logger.info(f"  사용된 토큰: {result.get('usage', {})}")
                        
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result["choices"][0]["message"]["content"]
                            logger.info(f"  생성된 콘텐츠 길이: {len(content)}자")
                            logger.info(f"  콘텐츠 미리보기: {content[:500]}...")
                            
                            # JSON 파싱 시도
                            try:
                                parsed_content = json.loads(content)
                                logger.info(f"  JSON 파싱 성공: {list(parsed_content.keys())}")
                            except json.JSONDecodeError as e:
                                logger.error(f"  ❌ JSON 파싱 실패: {e}")
                                logger.error(f"  원본 콘텐츠: {content}")
                            
                            return self._parse_response(content, kwargs)
                        else:
                            logger.error("❌ OpenAI 응답에 choices가 없음")
                            logger.error(f"  전체 응답: {result}")
                            return self._fallback_response(kwargs)
                            
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ OpenAI API 오류:")
                        logger.error(f"  상태코드: {response.status}")
                        logger.error(f"  오류 내용: {error_text}")
                        
                        # 401 오류 특별 처리
                        if response.status == 401:
                            logger.error("❌ 인증 실패 - API 키 문제")
                            logger.error(f"  사용된 API 키: {self.api_key[:20]}...")
                        
                        raise Exception(f"OpenAI API 오류: {response.status}")
        
        except asyncio.TimeoutError:
            logger.error("❌ OpenAI API 타임아웃 (30초 초과)")
            raise Exception("OpenAI API 요청 시간 초과")
        except aiohttp.ClientError as e:
            logger.error(f"❌ HTTP 클라이언트 오류:")
            logger.error(f"  오류 타입: {type(e).__name__}")
            logger.error(f"  오류 메시지: {str(e)}")
            raise Exception(f"HTTP 클라이언트 오류: {str(e)}")
        except Exception as e:
            logger.error(f"❌ OpenAI API 호출 실패:")
            logger.error(f"  오류 타입: {type(e).__name__}")
            logger.error(f"  오류 메시지: {str(e)}")
            logger.error(f"  스택 트레이스:", exc_info=True)
            raise Exception(f"OpenAI API 호출 실패: {str(e)}")
    
    def _parse_response(self, content: str, context: Dict) -> Dict[str, Any]:
        """OpenAI 응답 파싱"""
        logger.info("🔄 OpenAI 응답 파싱 시작")
        try:
            data = json.loads(content)
            logger.info(f"✅ JSON 파싱 성공: {list(data.keys())}")
            
            # 필수 필드 보완
            if "station_name" not in data:
                data["station_name"] = context.get('station_name', '강남')
                logger.info(f"  station_name 보완: {data['station_name']}")
            if "line_number" not in data:
                data["line_number"] = context.get('line_number', 2)
                logger.info(f"  line_number 보완: {data['line_number']}")
            
            logger.info("✅ OpenAI 응답 파싱 완료")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"❌ OpenAI 응답 파싱 실패: {e}")
            logger.error(f"  원본 콘텐츠: {content}")
            return self._fallback_response(context)
    
    def _fallback_response(self, context: Dict) -> Dict[str, Any]:
        """파싱 실패시 기본 응답"""
        logger.warning("⚠️ OpenAI Provider Fallback 응답 생성")
        return {
            "story_title": f"{context.get('station_name', '강남')}역의 모험",
            "page_content": "예상치 못한 상황이 발생했습니다. 어떻게 대처하시겠습니까?",
            "options": [
                {"content": "신중하게 행동한다", "effect": "sanity", "amount": 3, "effect_preview": "정신력 +3"},
                {"content": "빠르게 대응한다", "effect": "health", "amount": -2, "effect_preview": "체력 -2"}
            ],
            "estimated_length": 5,
            "difficulty": "보통",
            "theme": "어드벤처",
            "station_name": context.get('station_name', '강남'),
            "line_number": context.get('line_number', 2)
        }
    
    def get_provider_name(self) -> str:
        return f"OpenAI {self.model}"

class ClaudeProvider(LLMProvider):
    """Anthropic Claude Provider"""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"
        
        # 🆕 초기화 로그
        logger.info("🔧 ClaudeProvider 초기화")
        logger.info(f"  API 키 마스킹: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else '짧음'}")
        logger.info(f"  모델: {model}")
    
    def is_available(self) -> bool:
        available = bool(self.api_key and self.api_key != "" and aiohttp is not None)
        logger.info(f"🔍 Claude Provider 사용 가능 체크: {available}")
        return available
    
    async def generate_story(self, prompt: str, **kwargs) -> Dict[str, Any]:
        logger.info("🎯 ClaudeProvider.generate_story 메서드 진입")
        logger.info(f"  프롬프트 길이: {len(prompt)}")
        logger.info(f"  kwargs: {kwargs}")
        
        if not self.is_available():
            logger.error("❌ ClaudeProvider 사용 불가")
            raise ValueError("Claude API 키가 설정되지 않았거나 aiohttp가 설치되지 않았습니다.")
        
        # Claude API 구현은 여기에...
        # 현재는 Mock 데이터 반환
        logger.warning("⚠️ Claude API 구현 미완성, Mock 데이터 반환")
        return self._fallback_response(kwargs)
    
    def _parse_response(self, content: str, context: Dict) -> Dict[str, Any]:
        """Claude 응답 파싱 (JSON 블록 추출)"""
        try:
            # JSON 블록 찾기
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                json_content = content[start:end]
                data = json.loads(json_content)
                
                # 필수 필드 보완
                if "station_name" not in data:
                    data["station_name"] = context.get('station_name', '강남')
                if "line_number" not in data:
                    data["line_number"] = context.get('line_number', 2)
                
                return data
            else:
                raise ValueError("JSON 형식을 찾을 수 없습니다.")
        
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Claude 응답 파싱 실패: {content[:100]}...")
            return self._fallback_response(context)
    
    def _fallback_response(self, context: Dict) -> Dict[str, Any]:
        """파싱 실패시 기본 응답"""
        logger.warning("⚠️ Claude Provider Fallback 응답 생성")
        return {
            "story_title": f"{context.get('station_name', '강남')}역의 모험",
            "page_content": "예상치 못한 상황이 발생했습니다. 어떻게 대처하시겠습니까?",
            "options": [
                {"content": "신중하게 행동한다", "effect": "sanity", "amount": 3, "effect_preview": "정신력 +3"},
                {"content": "빠르게 대응한다", "effect": "health", "amount": -2, "effect_preview": "체력 -2"}
            ],
            "estimated_length": 5,
            "difficulty": "보통",
            "theme": "어드벤처",
            "station_name": context.get('station_name', '강남'),
            "line_number": context.get('line_number', 2)
        }
    
    def get_provider_name(self) -> str:
        return f"Claude {self.model}"

class MockProvider(LLMProvider):
    """Mock 데이터 제공자"""
    
    def __init__(self):
        super().__init__()
        logger.info("🎭 MockProvider 초기화")
        try:
            from templates.mock_templates import MockStoryGenerator
            self.generator = MockStoryGenerator()
            logger.info("✅ MockStoryGenerator 로드 성공")
        except ImportError:
            logger.warning("⚠️ MockStoryGenerator import 실패, 기본 응답 사용")
            self.generator = None
    
    def is_available(self) -> bool:
        return True
    
    async def generate_story(self, prompt: str, **kwargs) -> Dict[str, Any]:
        # 🆕 Mock Provider 호출 감지 로그
        logger.warning("⚠️ MockProvider.generate_story 호출됨")
        logger.warning(f"  이유: 실제 LLM Provider 실패로 Mock 사용")
        logger.warning(f"  프롬프트 길이: {len(prompt)}")
        logger.warning(f"  kwargs: {kwargs}")
        
        # 인위적 지연 (실제 API 호출 시뮬레이션)
        await asyncio.sleep(0.3)
        
        if self.generator:
            logger.info("🎭 MockStoryGenerator 사용")
            station_name = kwargs.get('station_name', '강남')
            character_health = kwargs.get('character_health', 80)
            character_sanity = kwargs.get('character_sanity', 80)
            
            result = self.generator.generate_story(station_name, character_health, character_sanity)
            
            logger.warning("⚠️ Mock 데이터 생성됨:")
            logger.warning(f"  제목: {result.get('story_title', 'N/A')}")
            logger.warning(f"  내용 미리보기: {result.get('page_content', 'N/A')[:100]}")
            
            return result
        else:
            logger.warning("⚠️ MockStoryGenerator 없음, 기본 응답 사용")
            # Generator가 없을 때 기본 응답
            result = {
                "story_title": f"{kwargs.get('station_name', '강남')}역의 이야기",
                "page_content": f"{kwargs.get('station_name', '강남')}역에서 흥미로운 일이 벌어집니다.",
                "options": [
                    {"content": "관찰한다", "effect": "sanity", "amount": 2, "effect_preview": "정신력 +2"},
                    {"content": "행동한다", "effect": "health", "amount": -1, "effect_preview": "체력 -1"}
                ],
                "estimated_length": 5,
                "difficulty": "보통",
                "theme": "일상",
                "station_name": kwargs.get('station_name', '강남'),
                "line_number": kwargs.get('line_number', 2)
            }
            
            logger.info("✅ 기본 Mock 응답 생성 완료")
            return result
    
    def get_provider_name(self) -> str:
        return "Mock Provider"

class LLMProviderFactory:
    """LLM Provider 팩토리"""
    
    @staticmethod
    def get_provider() -> LLMProvider:
        logger.info("🏭 LLMProviderFactory.get_provider 시작")
        
        try:
            from config.settings import Settings
            settings = Settings()
            logger.info("✅ Settings 로드 성공")
        except ImportError as e:
            logger.warning(f"⚠️ Settings import 실패: {e}, 환경변수로 직접 읽기")
            import os
            provider_name = os.getenv("AI_PROVIDER", "mock").lower()
            logger.info(f"📊 환경변수 AI_PROVIDER: {provider_name}")
            
            if provider_name == "openai" and os.getenv("OPENAI_API_KEY"):
                logger.info("🚀 환경변수로 OpenAI Provider 생성")
                return OpenAIProvider(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                )
            elif provider_name == "claude" and os.getenv("CLAUDE_API_KEY"):
                logger.info("🚀 환경변수로 Claude Provider 생성")
                return ClaudeProvider(
                    api_key=os.getenv("CLAUDE_API_KEY"),
                    model=os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
                )
            else:
                logger.warning("⚠️ 환경변수로 Mock Provider 사용")
                return MockProvider()
        
        provider_name = settings.AI_PROVIDER.lower()
        logger.info(f"📊 Settings AI_PROVIDER: {provider_name}")
        
        # 실제 API Provider 우선 시도
        if provider_name == "openai" and settings.OPENAI_API_KEY:
            logger.info(f"✅ OpenAI Provider phase1, apikey : {settings.OPENAI_API_KEY[:15]}")
            logger.info(f"🔑 API 키 전체 길이: {len(settings.OPENAI_API_KEY)}")
            
            provider = OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                max_tokens=settings.OPENAI_MAX_TOKENS
            )
            
            if provider.is_available():
                logger.info(f"✅ OpenAI Provider 활성화: {settings.OPENAI_MODEL}")
                logger.info("🎯 OpenAI Provider 반환")
                return provider
            else:
                # 🆕 사용 불가 시 로그
                logger.error("❌ OpenAI Provider 생성했으나 사용 불가")
                logger.error(f"  API 키 상태: {bool(settings.OPENAI_API_KEY)}")
                logger.error(f"  API 키 길이: {len(settings.OPENAI_API_KEY)}")
                logger.error(f"  aiohttp 상태: {aiohttp is not None}")
        
        elif provider_name == "claude" and settings.CLAUDE_API_KEY:
            logger.info(f"✅ Claude Provider 시도")
            provider = ClaudeProvider(
                api_key=settings.CLAUDE_API_KEY,
                model=settings.CLAUDE_MODEL
            )
            if provider.is_available():
                logger.info(f"✅ Claude Provider 활성화: {settings.CLAUDE_MODEL}")
                return provider
            else:
                logger.error("❌ Claude Provider 생성했으나 사용 불가")
        
        # 모든 실제 Provider가 실패하면 Mock 사용
        logger.warning(f"⚠️ 실제 LLM Provider 사용 불가, Mock Provider로 전환 (요청: {provider_name})")
        logger.warning("⚠️ 이 지점에서 Mock 데이터 사용이 결정됨")
        logger.warning(f"⚠️ Mock Provider 반환 이유:")
        logger.warning(f"  - AI_PROVIDER: {provider_name}")
        logger.warning(f"  - OpenAI 키 존재: {bool(settings.OPENAI_API_KEY) if 'settings' in locals() else 'N/A'}")
        logger.warning(f"  - Claude 키 존재: {bool(settings.CLAUDE_API_KEY) if 'settings' in locals() else 'N/A'}")
        
        return MockProvider()
    
    @staticmethod
    def get_available_providers() -> Dict[str, bool]:
        """사용 가능한 Provider 목록"""
        logger.info("📋 사용 가능한 Provider 목록 조회")
        
        try:
            from config.settings import Settings
            settings = Settings()
            
            providers = {
                "openai": bool(settings.OPENAI_API_KEY and aiohttp is not None),
                "claude": bool(settings.CLAUDE_API_KEY and aiohttp is not None),
                "mock": True
            }
            
            logger.info(f"📋 Provider 상태: {providers}")
            return providers
            
        except ImportError:
            import os
            providers = {
                "openai": bool(os.getenv("OPENAI_API_KEY") and aiohttp is not None),
                "claude": bool(os.getenv("CLAUDE_API_KEY") and aiohttp is not None),
                "mock": True
            }
            
            logger.info(f"📋 Provider 상태 (환경변수): {providers}")
            return providers
    
    @staticmethod
    def test_provider(provider_name: str) -> Dict[str, Any]:
        """특정 Provider 테스트"""
        logger.info(f"🧪 Provider 테스트: {provider_name}")
        
        try:
            if provider_name == "openai":
                import os
                provider = OpenAIProvider(
                    os.getenv("OPENAI_API_KEY", ""), 
                    os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                )
            elif provider_name == "claude":
                import os
                provider = ClaudeProvider(
                    os.getenv("CLAUDE_API_KEY", ""), 
                    os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
                )
            elif provider_name == "mock":
                provider = MockProvider()
            else:
                return {"status": "error", "message": f"알 수 없는 Provider: {provider_name}"}
            
            result = {
                "status": "available" if provider.is_available() else "unavailable",
                "provider": provider.get_provider_name(),
                "message": "사용 가능" if provider.is_available() else "API 키 없음 또는 의존성 누락"
            }
            
            logger.info(f"🧪 테스트 결과: {result}")
            return result
            
        except Exception as e:
            logger.error(f"🧪 Provider 테스트 실패: {str(e)}")
            return {"status": "error", "message": str(e)}