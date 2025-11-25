from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import os
import logging
from datetime import datetime

from providers.llm_provider import LLMProviderFactory
from utils.rate_limiter import RateLimiter

from models.batch_models import BatchStoryRequest, BatchStoryResponse
from services.batch_story_service import BatchStoryService
from models.multiplayer_models import MultiplayerStoryRequest, MultiplayerStoryResponse
from services.multiplayer_story_service import MultiplayerStoryService

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱
app = FastAPI(
    title="Behindy AI Server",
    description="지하철 스토리 생성 서비스 (단일 엔드포인트)",
    version="3.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 초기화
logger.info("Initializing FastAPI services")

batch_story_service = BatchStoryService()
logger.info("BatchStoryService ready")

multiplayer_story_service = MultiplayerStoryService()
logger.info("MultiplayerStoryService ready")

rate_limiter = RateLimiter()
logger.info("RateLimiter ready")

# FastAPI 미들웨어로 모든 요청 로그
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Request %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("Response %s %s", request.method, response.status_code)
    return response

# ===== 헬스체크 및 상태 =====

@app.get("/")
async def root():
    """기본 헬스 체크"""
    provider = LLMProviderFactory.get_provider()
    
    return {
        "message": "Behindy AI Server (Simplified)",
        "status": "healthy",
        "provider": provider.get_provider_name(),
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "endpoints": ["generate-complete-story", "multiplayer/next-phase", "health", "providers"]
    }

@app.get("/health")
async def health_check():
    """상세 헬스 체크"""
    provider = LLMProviderFactory.get_provider()
    available_providers = LLMProviderFactory.get_available_providers()
    
    return {
        "status": "healthy",
        "current_provider": provider.get_provider_name(),
        "available_providers": available_providers,
        "total_requests": rate_limiter.get_total_requests(),
        "timestamp": datetime.now().isoformat(),
        "simplified_mode": True
    }

@app.get("/providers")
async def get_providers_status():
    """Provider 상태 확인"""
    available_providers = LLMProviderFactory.get_available_providers()
    current_provider = LLMProviderFactory.get_provider()
    
    return {
        "current": current_provider.get_provider_name(),
        "available": available_providers,
        "settings": {
            "ai_provider": os.getenv("AI_PROVIDER", "mock"),
            "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "claude_model": os.getenv("CLAUDE_MODEL", "claude-3-haiku"),
        }
    }

@app.post("/generate-complete-story", response_model=BatchStoryResponse)
async def generate_complete_story(request: BatchStoryRequest, http_request: Request):
    """통합 스토리 생성 엔드포인트"""
    try:
        api_key = http_request.headers.get("X-Internal-API-Key")
        request_mode = "BATCH" if api_key == "behindy-internal-2025-secret-key" else "PUBLIC"

        if request_mode == "PUBLIC":
            client_ip = http_request.client.host
            rate_limiter.check_rate_limit(client_ip)

        response = await batch_story_service.generate_complete_story(request)

        logger.info(
            "generate-complete-story success station=%s line=%s title=%s",
            request.station_name,
            request.line_number,
            response.story_title,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("generate-complete-story failed: %s", str(e), exc_info=True)

        return BatchStoryResponse(
            story_title=f"{request.station_name}역의 이야기",
            description=f"{request.station_name}역에서 벌어지는 예상치 못한 사건",
            theme="미스터리",
            keywords=[request.station_name, f"{request.line_number}호선", "지하철"],
            pages=[
                BatchPageData(
                    content=f"{request.station_name}역에서 주의를 요하는 상황이 발생했습니다.",
                    options=[
                        BatchOptionData(
                            content="신중하게 상황을 살핀다",
                            effect="sanity",
                            amount=2,
                            effect_preview="정신력 +2",
                        ),
                        BatchOptionData(
                            content="즉시 행동한다",
                            effect="health",
                            amount=-1,
                            effect_preview="체력 -1",
                        ),
                    ],
                )
            ],
            estimated_length=1,
            difficulty="보통",
            station_name=request.station_name,
            line_number=request.line_number,
        )

@app.post("/api/multiplayer/generate-story", response_model=MultiplayerStoryResponse)
async def generate_multiplayer_story(request: MultiplayerStoryRequest, http_request: Request):
    try:
        api_key = http_request.headers.get("X-Internal-API-Key")
        if api_key != "behindy-internal-2025-secret-key":
            raise HTTPException(status_code=403, detail="Unauthorized internal API access")

        response = await multiplayer_story_service.generate_next_phase(request)

        logger.info(
            "multiplayer story success room_id=%s station=%s phase=%s is_intro=%s",
            request.room_id,
            request.station_name,
            request.phase,
            request.is_intro,
        )

        return response

    except HTTPException as e:
        logger.error("multiplayer story HTTPException %s: %s", e.status_code, e.detail)
        raise
    except Exception as e:
        logger.error("multiplayer story failed: %s", str(e), exc_info=True)

        from models.multiplayer_models import ParticipantUpdate
        return MultiplayerStoryResponse(
            story_text=f"{request.station_name}역에서 예상치 못한 일이 벌어집니다. 여러분의 선택이 필요합니다.",
            effects=[
                ParticipantUpdate(
                    character_name=p.character_name,
                    hp_change=-1,
                    sanity_change=-1
                )
                for p in request.participants
            ],
            phase=request.phase + 1,
            is_ending=False,
            story_outline=request.story_outline
        )

# ===== 관리 및 디버깅 API =====

@app.post("/validate-story-structure")
async def validate_story_structure(validation_request: Dict[str, Any], http_request: Request):
    """스토리 구조 검증 (내부 API)"""
    try:
        # 내부 API 키 검증
        api_key = http_request.headers.get("X-Internal-API-Key")
        if api_key != "behindy-internal-2025-secret-key":
            raise HTTPException(status_code=403, detail="Unauthorized internal API access")
        
        logger.info("story validation requested")
        
        validation_result = await batch_story_service.validate_story_structure(
            validation_request.get("story_data", {})
        )
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"구조 검증 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"검증 중 오류: {str(e)}")

@app.get("/batch/system-status")
async def get_batch_system_status(http_request: Request):
    """배치 시스템 상태 (내부/공개 API)"""
    try:
        # 내부 API 키 확인 (선택적)
        api_key = http_request.headers.get("X-Internal-API-Key")
        is_internal = api_key == "behindy-internal-2025-secret-key"
        
        provider = LLMProviderFactory.get_provider()
        available_providers = LLMProviderFactory.get_available_providers()
        
        status = {
            "ai_server_status": "healthy",
            "current_provider": provider.get_provider_name(),
            "available_providers": available_providers,
            "batch_service_ready": True,
            "rate_limit_status": {
                "total_requests": rate_limiter.get_total_requests(),
                "hit_rate": "N/A"
            },
            "timestamp": datetime.now().isoformat(),
            "simplified_mode": True,
            "version": "3.0.0"
        }
        
        # 내부 요청인 경우 더 상세한 정보 제공
        if is_internal:
            status["internal_mode"] = True
            status["api_endpoints"] = ["generate-complete-story"]
        
        return status
        
    except Exception as e:
        logger.error(f"배치 시스템 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"상태 조회 중 오류: {str(e)}")

# ===== 테스트 API =====

@app.post("/test-provider")
async def test_provider(test_request: Dict[str, Any]):
    """Provider 테스트용 엔드포인트"""
    try:
        provider = LLMProviderFactory.get_provider()
        
        logger.info("Provider test started with provider=%s", provider.get_provider_name())
        
        # 간단한 테스트 스토리 생성 요청
        test_request_obj = BatchStoryRequest(
            station_name=test_request.get("station_name", "강남"),
            line_number=test_request.get("line_number", 2),
            character_health=80,
            character_sanity=80,
            story_type="TEST"
        )
        
        test_result = await batch_story_service.generate_complete_story(test_request_obj)
        
        return {
            "provider": provider.get_provider_name(),
            "status": "success",
            "test_result": {
                "title": test_result.story_title,
                "theme": test_result.theme,
                "pages": len(test_result.pages)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Provider 테스트 실패: {str(e)}")
        return {
            "provider": "unknown",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ===== 환경 설정 API =====

@app.get("/config")
async def get_config():
    """현재 환경 설정 확인"""
    return {
        "ai_provider": os.getenv("AI_PROVIDER", "mock"),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "claude_configured": bool(os.getenv("CLAUDE_API_KEY")),
        "request_limits": {
            "per_hour": os.getenv("REQUEST_LIMIT_PER_HOUR", "100"),
            "per_day": os.getenv("REQUEST_LIMIT_PER_DAY", "1000")
        },
        "simplified_mode": True,
        "active_endpoints": [
            "/generate-complete-story",
            "/health", 
            "/providers",
            "/batch/system-status"
        ]
    }

# ===== 에러 핸들러 =====

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP 오류: {exc.status_code} - {exc.detail}")
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"일반 오류: {str(exc)}")
    return {
        "error": "내부 서버 오류가 발생했습니다.",
        "status_code": 500,
        "timestamp": datetime.now().isoformat()
    }

# ===== 서버 실행 =====

if __name__ == "__main__":
    import uvicorn
    
    # 시작시 Provider 상태 로깅
    try:
        provider = LLMProviderFactory.get_provider()
        available = LLMProviderFactory.get_available_providers()
        
        logger.info("Behindy AI Server starting")
        logger.info("Current provider: %s", provider.get_provider_name())
        logger.info("Available providers: %s", available)
        
    except Exception as e:
        logger.error("Initialization error: %s", str(e))
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
