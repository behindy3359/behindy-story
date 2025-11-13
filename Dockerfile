FROM python:3.11-slim

# 메타데이터 설정
LABEL maintainer="behindy-project"
LABEL description="FastAPI AI Story Generation Server with LLM Provider Support"
LABEL version="2.0.0"

# 환경변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    AI_PROVIDER=mock \
    OPENAI_API_KEY="" \
    OPENAI_MODEL=gpt-4o-mini \
    OPENAI_MAX_TOKENS=1000 \
    CLAUDE_API_KEY="" \
    CLAUDE_MODEL=claude-3-haiku-20240307 \
    REQUEST_LIMIT_PER_HOUR=100 \
    REQUEST_LIMIT_PER_DAY=1000 \
    USE_CACHE=true \
    CACHE_TTL=3600 \
    REDIS_URL=redis://redis:6379 \
    LOG_LEVEL=INFO

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 먼저 복사 (Docker 캐시 최적화)
COPY requirements.txt .

# Python 의존성 설치
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 프롬프트 파일들이 올바르게 복사되었는지 확인
RUN ls -la /app/prompt/ || echo "프롬프트 디렉토리 확인 중..."

# 비루트 사용자 생성 및 설정
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app && \
    chmod +x /app

# 사용자 전환
USER appuser

# 포트 노출
EXPOSE 8000

# 헬스체크 추가 (AI 서버 상태 확인)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 실행 명령 (개발환경에서는 reload 활성화, 운영환경에서는 workers 조정)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info"]