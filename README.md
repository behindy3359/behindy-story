# Behindy Story

서울 지하철 역을 배경으로 한 텍스트 어드벤처 게임의 AI 스토리 생성 서버입니다. OpenAI GPT 및 Anthropic Claude를 활용하여 역 정보와 캐릭터 상태에 기반한 맞춤형 스토리와 선택지를 생성합니다.

## 기술 스택

- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.11
- **ASGI Server**: Uvicorn 0.24 (with standard extras)
- **Data Validation**: Pydantic 2.5 + pydantic-settings 2.1
- **LLM Providers**: OpenAI 1.3 (GPT-4o-mini), Anthropic 0.7 (Claude 3 Haiku)
- **HTTP Client**: aiohttp 3.9 (비동기), requests 2.31 (동기)

## 주요 기능

### AI 스토리 생성
- 서울 지하철 역 정보 기반 컨텍스트 생성
- 역의 특성, 분위기, 시간대를 반영한 스토리
- 캐릭터 상태 (HP, Sanity) 고려
- 3-4개 선택지 자동 생성
- 각 선택지별 HP/Sanity 변화 예측
- 스토리 일관성 및 몰입감 유지

### 멀티플레이어 스토리 생성
- 다중 참여자의 채팅 히스토리 분석
- Phase별 상황 진행
- 참여자별 개별 상태 변화 계산
- 실시간 협력 스토리텔링

### LLM Provider 관리
- OpenAI GPT-4o-mini (Primary)
- Anthropic Claude 3 Haiku (Fallback)
- Provider 자동 전환 (장애 복구)
- Mock Provider (개발/테스트 환경)

### 성능 최적화
- 비동기 처리 (asyncio, aiohttp)
- Rate Limiting (시간당/일일 요청 제한)
- 응답 캐싱 (옵션)

### 모니터링
- `/health` 헬스 체크 엔드포인트
- `/providers` Provider 상태 조회
- 구조화된 로깅

## API 엔드포인트

### 싱글플레이어 스토리 생성
```
POST /generate-complete-story
POST /llm/story/generate
POST /llm/batch/stories
```

### 멀티플레이어 스토리 생성
```
POST /llm/multiplayer/next-phase
```

### 모니터링
```
GET /health          # 헬스 체크
GET /providers       # LLM Provider 상태
```

## 환경 변수

```bash
# LLM Provider
AI_PROVIDER=openai              # openai 또는 claude

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000

# Claude
CLAUDE_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-haiku-20240307

# Rate Limiting
REQUEST_LIMIT_PER_HOUR=50
REQUEST_LIMIT_PER_DAY=500

# Cache
USE_CACHE=true
CACHE_TTL=7200                  # 2시간
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
```

## 로컬 개발

### 요구사항
- Python 3.11+
- Redis 7

### 실행
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

# 테스트 실행
pytest
pytest -v                    # Verbose 모드
pytest tests/test_story.py   # 특정 파일만

## Docker 빌드

```bash
# 이미지 빌드
docker build -t behindy-llmserver .

# 컨테이너 실행
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e REDIS_URL=redis://redis:6379 \
  behindy-llmserver
```

## 배포

GitHub Actions를 통한 자동 배포:

1. `main` 브랜치에 push
2. 자동으로 Docker 이미지 빌드
3. EC2 서버에 배포 및 재시작

## 프로젝트 구조

```
.
├── main.py
├── config/
│   └── settings.py
├── providers/
│   └── llm_provider.py
├── services/
│   ├── batch_story_service.py
│   ├── multiplayer_story_service.py
│   └── story_service.py
├── models/
│   ├── batch_models.py
│   ├── multiplayer_models.py
│   ├── request_models.py
│   └── response_models.py
├── prompt/
│   └── prompt_manager.py
├── templates/
├── utils/
│   └── rate_limiter.py
└── requirements.txt
```

## 스토리 생성 로직

### 1. 요청 검증
- 역 이름, 호선, 캐릭터 정보 검증
- Rate Limit 체크

### 2. 캐시 확인
- Redis에서 동일 요청 캐시 확인
- 있으면 즉시 반환 (API 비용 절감)

### 3. 프롬프트 생성
```python
prompt = f"""
당신은 텍스트 어드벤처 게임의 스토리 작가입니다.

배경: {station}역 ({line}호선)
캐릭터: {character.name} (체력: {character.health}, 정신력: {character.mental})

이 상황에서 흥미로운 스토리와 3-4개의 선택지를 생성하세요.
"""
```

### 4. LLM 호출
- Primary Provider 호출
- 실패 시 Fallback Provider로 전환

### 5. 응답 파싱 및 검증
- JSON 형식 검증
- 선택지 개수 확인 (3-4개)
- 스토리 길이 확인

### 6. 캐싱 및 반환
- Redis에 결과 캐싱 (TTL: 2시간)
- 클라이언트에 응답

## 성능 최적화

### 캐싱 전략
```python
cache_key = f"story:{station}:{line}:{character_hash}"
ttl = 7200  # 2시간
```

### Rate Limiting
- IP 기반 제한
- 시간당 50회, 일일 500회
- 429 Too Many Requests 반환

### 비동기 처리
```python
@app.post("/api/story/generate")
async def generate_story(request: StoryRequest):
    # 비동기로 LLM 호출
    result = await llm_provider.generate(prompt)
    return result
```

## 모니터링

### 로그 레벨
- DEBUG: 상세한 디버깅 정보
- INFO: 일반 요청 로그
- WARNING: 경고 (Rate Limit 등)
- ERROR: 에러 발생

### 주요 메트릭
- 요청 수 (시간당/일일)
- 캐시 히트율
- LLM 응답 시간
- Provider 실패율
- 
## 보안

- API Key 환경 변수 관리
- CORS 설정
- 내부 API 인증
- Rate Limiting

## 아키텍처

- Frontend: Next.js 기반 UI 레이어
- Backend: Spring Boot 기반 API 서버 및 비즈니스 로직
- Story (이 레포): FastAPI 기반 AI 스토리 생성 전담 서버
- Ops: Docker Compose 기반 인프라 관리

## 관련 레포지토리

- [behindy-front](https://github.com/behindy3359/behindy-front) - Next.js 프론트엔드
- [behindy-back](https://github.com/behindy3359/behindy-back) - Spring Boot 백엔드 API 서버
- [behindy-ops](https://github.com/behindy3359/behindy-ops) - 인프라 관리 (PostgreSQL, Redis, Nginx)
