# Behindy LLM Server - 2025.11.09

지하철 역 기반 텍스트 어드벤처 게임의 AI 스토리 생성 서버입니다.

## 기술 스택

- **Framework**: FastAPI
- **Language**: Python 3.11
- **LLM Providers**: OpenAI, Anthropic Claude
- **Cache**: Redis

## 주요 기능

### AI 스토리 생성
- 지하철 역 정보를 바탕으로 한 스토리 생성
- 캐릭터 특성을 반영한 맞춤형 스토리
- 선택지 자동 생성 (3-4개)
- 스토리 일관성 유지

### LLM Provider 지원
- OpenAI GPT-4o-mini
- Anthropic Claude 3 Haiku
- Provider 자동 전환 (Fallback)

### 성능 최적화
- Redis 캐싱 (중복 요청 방지)
- Rate Limiting (시간당/일일 제한)
- 비동기 처리

### 헬스 체크
- `/health` 엔드포인트
- LLM Provider 상태 확인
- Redis 연결 상태 확인

## API 엔드포인트

### 통합 스토리 생성
```
POST /generate-complete-story
Content-Type: application/json

{
  "station_name": "강남",
  "line_number": 2,
  "character_health": 90,
  "character_sanity": 80,
  "story_type": "PUBLIC"
}
```

### 헬스 체크
```
GET /health
```

### Provider 상태
```
GET /providers
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

서버는 `http://localhost:8000`에서 실행됩니다.

현재 테스트 스위트는 제공되지 않습니다.

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

자세한 내용은 `.github/workflows/deploy.yml` 참조

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

## 에러 처리

### 400 Bad Request
- 잘못된 요청 형식
- 필수 필드 누락

### 429 Too Many Requests
- Rate Limit 초과

### 500 Internal Server Error
- LLM Provider 에러
- Redis 연결 실패

### 503 Service Unavailable
- 모든 LLM Provider 실패

## 보안

- API Key 환경 변수 관리
- CORS 설정
- 내부 API 인증 (Backend 간)
- Rate Limiting

## 관련 레포지토리

- [behindy-backend](https://github.com/behindy3359/behindy-backend) - Spring Boot 백엔드
- [behindy-frontend](https://github.com/behindy3359/behindy-frontend) - Next.js 프론트엔드
- [behindy-ops](https://github.com/behindy3359/behindy-ops) - 인프라 설정

## 라이선스

MIT License
