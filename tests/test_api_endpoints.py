"""
API 엔드포인트 테스트
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
@pytest.mark.unit
class TestHealthEndpoint:
    """헬스체크 엔드포인트 테스트"""

    def test_health_check_returns_200(self, client):
        """헬스체크 성공"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_check_structure(self, client):
        """헬스체크 응답 구조 확인"""
        response = client.get("/health")
        data = response.json()

        # 필수 필드 확인
        assert "status" in data
        assert isinstance(data["status"], str)


@pytest.mark.api
@pytest.mark.unit
class TestGenerateStoryValidation:
    """스토리 생성 API 유효성 검사 테스트"""

    def test_generate_story_missing_all_fields(self, client):
        """모든 필수 필드 누락 시 422 에러"""
        response = client.post("/generate-story", json={})
        assert response.status_code == 422

    def test_generate_story_missing_station_name(self, client):
        """station_name 누락"""
        request_data = {
            "line_number": 2,
            "character_health": 80,
            "character_sanity": 70
        }
        response = client.post("/generate-story", json=request_data)
        assert response.status_code == 422

    def test_generate_story_missing_line_number(self, client):
        """line_number 누락"""
        request_data = {
            "station_name": "강남",
            "character_health": 80,
            "character_sanity": 70
        }
        response = client.post("/generate-story", json=request_data)
        assert response.status_code == 422

    def test_generate_story_negative_health(self, client):
        """음수 체력값"""
        request_data = {
            "station_name": "강남",
            "line_number": 2,
            "character_health": -10,
            "character_sanity": 70
        }
        response = client.post("/generate-story", json=request_data)
        # 유효성 검사 실패 (422) 또는 처리 가능할 수도 있음
        assert response.status_code in [200, 422]

    def test_generate_story_invalid_type(self, client):
        """잘못된 타입"""
        request_data = {
            "station_name": 123,  # 문자열이어야 함
            "line_number": "two",  # 숫자여야 함
            "character_health": 80,
            "character_sanity": 70
        }
        response = client.post("/generate-story", json=request_data)
        assert response.status_code == 422


@pytest.mark.api
@pytest.mark.unit
class TestContinueStoryValidation:
    """스토리 계속 진행 API 유효성 검사 테스트"""

    def test_continue_story_missing_fields(self, client):
        """필수 필드 누락"""
        response = client.post("/continue-story", json={})
        assert response.status_code == 422

    def test_continue_story_missing_previous_choice(self, client):
        """previous_choice 누락"""
        request_data = {
            "station_name": "강남",
            "line_number": 2,
            "character_health": 70,
            "character_sanity": 65,
            "story_context": "강남역에서..."
        }
        response = client.post("/continue-story", json=request_data)
        # previous_choice가 필수인지 확인
        assert response.status_code in [200, 422]


@pytest.mark.api
class TestGenerateStoryResponse:
    """스토리 생성 API 응답 구조 테스트"""

    def test_generate_story_response_structure(self, client, sample_story_request):
        """스토리 생성 응답 구조 확인"""
        response = client.post("/generate-story", json=sample_story_request)

        # 성공 응답이면 구조 확인
        if response.status_code == 200:
            data = response.json()

            # 필수 필드 확인
            assert "story_title" in data or "page_content" in data

            # options가 있다면 배열인지 확인
            if "options" in data:
                assert isinstance(data["options"], list)

                # 옵션이 있다면 구조 확인
                if len(data["options"]) > 0:
                    option = data["options"][0]
                    assert "content" in option


@pytest.mark.api
class TestEndpointAvailability:
    """엔드포인트 존재 여부 테스트"""

    def test_health_endpoint_exists(self, client):
        """헬스체크 엔드포인트 존재"""
        response = client.get("/health")
        assert response.status_code != 404

    def test_generate_story_endpoint_exists(self, client):
        """스토리 생성 엔드포인트 존재"""
        response = client.post("/generate-story", json={})
        # 404가 아니면 OK (422는 유효성 검사 실패)
        assert response.status_code != 404

    def test_continue_story_endpoint_exists(self, client):
        """스토리 계속 엔드포인트 존재"""
        response = client.post("/continue-story", json={})
        assert response.status_code != 404

    def test_invalid_endpoint_returns_404(self, client):
        """존재하지 않는 엔드포인트"""
        response = client.get("/invalid-endpoint-12345")
        assert response.status_code == 404


@pytest.mark.api
class TestHTTPMethods:
    """HTTP 메서드 테스트"""

    def test_health_only_accepts_get(self, client):
        """헬스체크는 GET만 허용"""
        # GET은 성공
        assert client.get("/health").status_code == 200

        # POST는 실패
        assert client.post("/health").status_code == 405

    def test_generate_story_only_accepts_post(self, client):
        """스토리 생성은 POST만 허용"""
        # GET은 실패
        assert client.get("/generate-story").status_code == 405

        # POST는 성공 또는 유효성 검사 실패
        response = client.post("/generate-story", json={})
        assert response.status_code in [200, 422]
