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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Behindy AI Server",
    description="    ( )",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

batch_story_service = BatchStoryService()
multiplayer_story_service = MultiplayerStoryService()
rate_limiter = RateLimiter()


@app.get("/")
async def root():
    """  """
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
    """  """
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
    """Provider  """
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
    """   """
    try:
        api_key = http_request.headers.get("X-Internal-API-Key")
        request_mode = "BATCH" if api_key == "behindy-internal-2025-secret-key" else "PUBLIC"

        if request_mode == "PUBLIC":
            client_ip = http_request.client.host
            rate_limiter.check_rate_limit(client_ip)

        response = await batch_story_service.generate_complete_story(request)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("generate-complete-story failed: %s", str(e), exc_info=True)

        return BatchStoryResponse(
            story_title=f"{request.station_name} ",
            description=f"{request.station_name}    ",
            theme="",
            keywords=[request.station_name, f"{request.line_number}", ""],
            pages=[
                BatchPageData(
                    content=f"{request.station_name}    .",
                    options=[
                        BatchOptionData(
                            content="  ",
                            effect="sanity",
                            amount=2,
                            effect_preview=" +2",
                        ),
                        BatchOptionData(
                            content=" ",
                            effect="health",
                            amount=-1,
                            effect_preview=" -1",
                        ),
                    ],
                )
            ],
            estimated_length=1,
            difficulty="",
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
        return response

    except HTTPException as e:
        logger.error("multiplayer story HTTPException %s: %s", e.status_code, e.detail)
        raise
    except Exception as e:
        logger.error("multiplayer story failed: %s", str(e), exc_info=True)

        from models.multiplayer_models import ParticipantUpdate
        return MultiplayerStoryResponse(
            story_text=f"{request.station_name}    .   .",
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


@app.post("/validate-story-structure")
async def validate_story_structure(validation_request: Dict[str, Any], http_request: Request):
    """   ( API)"""
    try:
        api_key = http_request.headers.get("X-Internal-API-Key")
        if api_key != "behindy-internal-2025-secret-key":
            raise HTTPException(status_code=403, detail="Unauthorized internal API access")

        validation_result = await batch_story_service.validate_story_structure(
            validation_request.get("story_data", {})
        )
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"  : {str(e)}")
        raise HTTPException(status_code=500, detail=f"  : {str(e)}")

@app.get("/batch/system-status")
async def get_batch_system_status(http_request: Request):
    """   (/ API)"""
    try:
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
        
        if is_internal:
            status["internal_mode"] = True
            status["api_endpoints"] = ["generate-complete-story"]
        
        return status
        
    except Exception as e:
        logger.error(f"    : {str(e)}")
        raise HTTPException(status_code=500, detail=f"   : {str(e)}")


@app.post("/test-provider")
async def test_provider(test_request: Dict[str, Any]):
    """Provider  """
    try:
        provider = LLMProviderFactory.get_provider()

        test_request_obj = BatchStoryRequest(
            station_name=test_request.get("station_name", ""),
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
        logger.error(f"Provider  : {str(e)}")
        return {
            "provider": "unknown",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/config")
async def get_config():
    """   """
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


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return {
        "error": "   .",
        "status_code": 500,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
