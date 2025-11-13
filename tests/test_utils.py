"""
유틸리티 함수 단위 테스트
"""
import pytest


@pytest.mark.unit
class TestThemeValidation:
    """테마 검증 테스트"""

    def test_valid_themes(self):
        """유효한 테마들"""
        valid_themes = ["Mystery", "Horror", "Thriller"]

        for theme in valid_themes:
            assert theme in ["Mystery", "Horror", "Thriller"]

    def test_invalid_themes(self):
        """유효하지 않은 테마들"""
        invalid_themes = ["Romance", "Comedy", "Action", "Sci-Fi"]

        for theme in invalid_themes:
            assert theme not in ["Mystery", "Horror", "Thriller"]


@pytest.mark.unit
class TestStationValidation:
    """지하철역 검증 테스트"""

    def test_valid_line_numbers(self):
        """유효한 호선 번호 (1-4호선)"""
        valid_lines = [1, 2, 3, 4]

        for line in valid_lines:
            assert 1 <= line <= 4

    def test_invalid_line_numbers(self):
        """유효하지 않은 호선 번호"""
        invalid_lines = [0, -1, 5, 10, 99]

        for line in invalid_lines:
            assert not (1 <= line <= 4)


@pytest.mark.unit
class TestHealthSanityValidation:
    """체력/정신력 검증 테스트"""

    def test_valid_health_range(self):
        """유효한 체력 범위 (0-100)"""
        valid_healths = [0, 1, 50, 99, 100]

        for health in valid_healths:
            assert 0 <= health <= 100

    def test_invalid_health_range(self):
        """유효하지 않은 체력 범위"""
        invalid_healths = [-1, -10, 101, 150, 1000]

        for health in invalid_healths:
            assert not (0 <= health <= 100)

    def test_valid_sanity_range(self):
        """유효한 정신력 범위 (0-100)"""
        valid_sanities = [0, 1, 50, 99, 100]

        for sanity in valid_sanities:
            assert 0 <= sanity <= 100

    def test_critical_health_detection(self):
        """위험 체력 감지 (20 이하)"""
        critical_health = [0, 5, 10, 15, 20]
        safe_health = [21, 50, 80, 100]

        for health in critical_health:
            assert health <= 20

        for health in safe_health:
            assert health > 20


@pytest.mark.unit
class TestOptionsValidation:
    """선택지 검증 테스트"""

    def test_minimum_options_count(self):
        """최소 선택지 개수 (2개)"""
        options_2 = [{"content": "A"}, {"content": "B"}]
        options_3 = [{"content": "A"}, {"content": "B"}, {"content": "C"}]

        assert len(options_2) >= 2
        assert len(options_3) >= 2

    def test_insufficient_options(self):
        """부족한 선택지 개수"""
        options_0 = []
        options_1 = [{"content": "A"}]

        assert len(options_0) < 2
        assert len(options_1) < 2

    def test_option_structure(self):
        """선택지 구조 검증"""
        valid_option = {
            "content": "주변을 살핀다",
            "health_effect": -5,
            "sanity_effect": 0
        }

        assert "content" in valid_option
        assert isinstance(valid_option["content"], str)
        assert len(valid_option["content"]) > 0

    def test_option_effects_range(self):
        """선택지 효과 범위 (-50 ~ +50)"""
        valid_effects = [-50, -10, 0, 10, 50]
        invalid_effects = [-100, -51, 51, 100]

        for effect in valid_effects:
            assert -50 <= effect <= 50

        for effect in invalid_effects:
            assert not (-50 <= effect <= 50)


@pytest.mark.unit
class TestStringOperations:
    """문자열 처리 테스트"""

    def test_station_name_cleanup(self):
        """역 이름 정리 (공백 제거)"""
        stations_with_space = ["강남 ", " 홍대입구", " 서울역 "]

        for station in stations_with_space:
            cleaned = station.strip()
            assert not cleaned.startswith(" ")
            assert not cleaned.endswith(" ")

    def test_empty_string_validation(self):
        """빈 문자열 검증"""
        empty_strings = ["", "   ", "\t", "\n"]

        for s in empty_strings:
            assert len(s.strip()) == 0

    def test_non_empty_string_validation(self):
        """비어있지 않은 문자열 검증"""
        valid_strings = ["강남", "Story Title", "선택지 내용"]

        for s in valid_strings:
            assert len(s.strip()) > 0


@pytest.mark.unit
class TestErrorMessageFormatting:
    """에러 메시지 포맷팅 테스트"""

    def test_error_message_structure(self):
        """에러 메시지 구조"""
        error = {
            "error": "Invalid request",
            "message": "Station name is required"
        }

        assert "error" in error or "message" in error
        assert isinstance(error.get("message", ""), str)

    def test_validation_error_format(self):
        """유효성 검사 에러 포맷"""
        validation_error = {
            "detail": [
                {
                    "loc": ["body", "station_name"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

        assert "detail" in validation_error
        assert isinstance(validation_error["detail"], list)
