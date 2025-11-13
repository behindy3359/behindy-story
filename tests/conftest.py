"""
Pytest 설정 및 공통 Fixtures
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# 경로 추가 - llmserver를 import할 수 있도록
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app


@pytest.fixture
def client():
    """FastAPI 테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API 응답"""
    return {
        "story_title": "강남역의 미스터리",
        "page_content": "강남역 플랫폼에 도착한 당신은 이상한 분위기를 감지했다. 사람들의 표정이 평소와 다르다.",
        "theme": "Mystery",
        "options": [
            {
                "content": "주변을 살핀다",
                "health_effect": -5,
                "sanity_effect": 0
            },
            {
                "content": "빨리 출구로 향한다",
                "health_effect": 0,
                "sanity_effect": -10
            },
            {
                "content": "가장 가까운 사람에게 말을 건다",
                "health_effect": 0,
                "sanity_effect": -5
            }
        ]
    }


@pytest.fixture
def sample_story_request():
    """샘플 스토리 생성 요청"""
    return {
        "station_name": "강남",
        "line_number": 2,
        "character_health": 80,
        "character_sanity": 70
    }


@pytest.fixture
def sample_continue_request():
    """샘플 스토리 계속 진행 요청"""
    return {
        "station_name": "강남",
        "line_number": 2,
        "character_health": 75,
        "character_sanity": 70,
        "previous_choice": "주변을 살핀다",
        "story_context": "강남역에서 이상한 분위기를 감지했다."
    }


@pytest.fixture
def mock_claude_response():
    """Mock Claude API 응답"""
    return {
        "story_title": "홍대입구역의 공포",
        "page_content": "홍대입구역에 도착했을 때, 당신은 갑자기 불안한 느낌을 받았다.",
        "theme": "Horror",
        "options": [
            {
                "content": "빠르게 계단을 올라간다",
                "health_effect": -10,
                "sanity_effect": 0
            },
            {
                "content": "천천히 주변을 관찰한다",
                "health_effect": 0,
                "sanity_effect": -15
            }
        ]
    }


@pytest.fixture
def invalid_story_request():
    """잘못된 스토리 요청 (필수 필드 누락)"""
    return {
        "station_name": "강남",
        # line_number 누락
        "character_health": 80,
    }


@pytest.fixture
def all_stations():
    """전체 지하철역 목록"""
    return [
        ("종각", 1), ("시청", 1), ("서울역", 1),
        ("강남", 2), ("홍대입구", 2), ("잠실", 2),
        ("압구정", 3), ("교대", 3), ("옥수", 3),
        ("명동", 4), ("혜화", 4), ("사당", 4)
    ]
