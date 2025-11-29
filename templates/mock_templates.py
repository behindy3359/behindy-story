"""
AI 서버 간단한 Mock 템플릿 시스템
Spring Boot 호환 + 첫 페이지 + 선택지 분화 2페이지만
테마 제한: 공포/미스터리/스릴러만
"""

import random
from typing import Dict, List, Any
from enum import Enum

class StationTheme(Enum):
    MYSTERY = "미스터리"
    HORROR = "공포"
    THRILLER = "스릴러"

STATION_CONFIG = {
    "종각": {"line": 1, "theme": StationTheme.MYSTERY},
    "시청": {"line": 1, "theme": StationTheme.THRILLER},
    "서울역": {"line": 1, "theme": StationTheme.MYSTERY},
    "강남": {"line": 2, "theme": StationTheme.THRILLER},
    "홍대입구": {"line": 2, "theme": StationTheme.MYSTERY},
    "잠실": {"line": 2, "theme": StationTheme.HORROR},
    "압구정": {"line": 3, "theme": StationTheme.THRILLER},
    "교대": {"line": 3, "theme": StationTheme.MYSTERY},
    "옥수": {"line": 3, "theme": StationTheme.MYSTERY},
    "명동": {"line": 4, "theme": StationTheme.THRILLER},
    "혜화": {"line": 4, "theme": StationTheme.HORROR},
    "사당": {"line": 4, "theme": StationTheme.HORROR}
}

ALLOWED_THEMES = ["미스터리", "공포", "스릴러"]

class MockStoryGenerator:
    """간단한 Mock 스토리 생성기 - 공포/미스터리/스릴러 전용"""

    def generate_story(self, station_name: str, character_health: int, character_sanity: int) -> Dict[str, Any]:
        """첫 페이지 스토리 생성 - 테마 제한"""
        config = STATION_CONFIG.get(station_name, {"line": 1, "theme": StationTheme.MYSTERY})
        theme = config["theme"]
        line_number = config["line"]

        story_content = self._generate_themed_content(station_name, theme.value, character_health, character_sanity)

        options = self._generate_themed_options(theme.value, character_health, character_sanity)

        return {
            "story_title": f"{station_name}역의 {theme.value}",
            "page_content": story_content,
            "options": options,
            "estimated_length": 6,
            "difficulty": self._get_difficulty_by_theme(theme.value),
            "theme": theme.value,
            "station_name": station_name,
            "line_number": line_number
        }

    def _generate_themed_content(self, station_name: str, theme: str, health: int, sanity: int) -> str:
        """테마별 특화 스토리 내용"""

        if theme == "공포":
            return f"{station_name}역에 도착한 순간, 섬뜩한 기운이 느껴집니다.\n\n" \
                   f"어둠 속에서 무언가가 움직이는 것 같고, 차가운 바람이 등줄기를 타고 내려옵니다.\n" \
                   f"현재 상태 - 체력: {health}, 정신력: {sanity}\n\n" \
                   f"이상한 소리가 들려오는데... 어떻게 하시겠습니까?"

        elif theme == "미스터리":
            return f"{station_name}역에서 수상한 일이 벌어지고 있습니다.\n\n" \
                   f"평소와 다른 분위기, 이상한 표지판, 그리고 의문스러운 사람들...\n" \
                   f"현재 상태 - 체력: {health}, 정신력: {sanity}\n\n" \
                   f"무언가 숨겨진 비밀이 있는 것 같습니다. 어떻게 조사하시겠습니까?"

        else:
            return f"{station_name}역에서 긴박한 상황이 발생했습니다.\n\n" \
                   f"누군가가 당신을 지켜보고 있는 것 같고, 시간이 얼마 남지 않은 느낌입니다.\n" \
                   f"현재 상태 - 체력: {health}, 정신력: {sanity}\n\n" \
                   f"빠른 판단이 필요한 순간입니다. 어떻게 행동하시겠습니까?"

    def _generate_themed_options(self, theme: str, health: int, sanity: int) -> List[Dict[str, Any]]:
        """테마별 특화 선택지"""

        if theme == "공포":
            return [
                {
                    "content": "용기를 내어 소리의 근원지로 간다",
                    "effect": "health",
                    "amount": -8,
                    "effect_preview": "체력 -8"
                },
                {
                    "content": "침착하게 주변을 관찰한다",
                    "effect": "sanity",
                    "amount": 2,
                    "effect_preview": "정신력 +2"
                },
                {
                    "content": "빠르게 다른 출구를 찾는다",
                    "effect": "sanity",
                    "amount": -3,
                    "effect_preview": "정신력 -3"
                }
            ]

        elif theme == "미스터리":
            return [
                {
                    "content": "단서를 찾기 위해 적극적으로 수사한다",
                    "effect": "health",
                    "amount": -3,
                    "effect_preview": "체력 -3"
                },
                {
                    "content": "논리적으로 상황을 분석한다",
                    "effect": "sanity",
                    "amount": 5,
                    "effect_preview": "정신력 +5"
                },
                {
                    "content": "조심스럽게 정보를 수집한다",
                    "effect": "none",
                    "amount": 0,
                    "effect_preview": "변화 없음"
                }
            ]

        else:
            return [
                {
                    "content": "즉시 대담하게 행동한다",
                    "effect": "health",
                    "amount": -6,
                    "effect_preview": "체력 -6"
                },
                {
                    "content": "냉정하게 상황을 파악한다",
                    "effect": "sanity",
                    "amount": 3,
                    "effect_preview": "정신력 +3"
                },
                {
                    "content": "전략적으로 대기한다",
                    "effect": "sanity",
                    "amount": -2,
                    "effect_preview": "정신력 -2"
                }
            ]

    def _get_difficulty_by_theme(self, theme: str) -> str:
        """테마별 난이도"""
        difficulty_map = {
            "공포": "어려움",
            "미스터리": "보통",
            "스릴러": "어려움"
        }
        return difficulty_map.get(theme, "보통")

    def continue_story(self, previous_choice: str, station_name: str,
                      character_health: int, character_sanity: int) -> Dict[str, Any]:
        """선택지에 따른 다음 페이지 - 테마별 특화"""

        config = STATION_CONFIG.get(station_name, {"theme": StationTheme.MYSTERY})
        theme = config["theme"].value

        content, options = self._generate_continuation_by_theme(theme, previous_choice)

        return {
            "page_content": content,
            "options": options,
            "is_last_page": len(options) < 2
        }

    def _generate_continuation_by_theme(self, theme: str, previous_choice: str) -> tuple:
        """테마별 연결 스토리"""

        if theme == "공포":
            if "용기를" in previous_choice:
                content = "어둠 속으로 걸어가자 끔찍한 진실이 드러납니다...\n체력은 소모되었지만 공포의 원인을 알게 되었습니다."
                options = [
                    {"content": "끝까지 맞선다", "effect": "health", "amount": -5, "effect_preview": "체력 -5"},
                    {"content": "도망친다", "effect": "sanity", "amount": -8, "effect_preview": "정신력 -8"}
                ]
            elif "침착하게" in previous_choice:
                content = "냉정한 관찰로 공포의 정체를 파악했습니다.\n정신력이 회복되고 대응 방법을 찾았습니다."
                options = [
                    {"content": "계획적으로 대응한다", "effect": "sanity", "amount": 3, "effect_preview": "정신력 +3"},
                    {"content": "신중하게 접근한다", "effect": "health", "amount": 2, "effect_preview": "체력 +2"}
                ]
            else:
                content = "다른 출구를 찾던 중 더 큰 공포와 마주쳤습니다...\n정신적 충격을 받았지만 새로운 경로를 발견했습니다."
                options = [
                    {"content": "새 경로로 탈출한다", "effect": "health", "amount": 3, "effect_preview": "체력 +3"},
                    {"content": "원래 자리로 돌아간다", "effect": "sanity", "amount": -2, "effect_preview": "정신력 -2"}
                ]

        elif theme == "미스터리":
            if "적극적으로" in previous_choice:
                content = "적극적인 수사 결과 중요한 단서를 발견했습니다!\n체력은 소모되었지만 진실에 한 발 더 다가섰습니다."
                options = [
                    {"content": "단서를 깊이 분석한다", "effect": "sanity", "amount": 4, "effect_preview": "정신력 +4"},
                    {"content": "추가 증거를 찾는다", "effect": "health", "amount": -2, "effect_preview": "체력 -2"}
                ]
            elif "논리적으로" in previous_choice:
                content = "논리적 분석으로 사건의 전체적인 그림이 보입니다.\n정신력이 크게 향상되고 해결책이 명확해졌습니다."
                options = [
                    {"content": "추론을 검증한다", "effect": "sanity", "amount": 2, "effect_preview": "정신력 +2"},
                    {"content": "결론을 내린다", "effect": "none", "amount": 0, "effect_preview": "변화 없음"}
                ]
            else:
                content = "조심스러운 정보 수집으로 안전하게 진전을 이뤘습니다.\n위험은 피했지만 시간이 걸렸습니다."
                options = [
                    {"content": "더 많은 정보를 수집한다", "effect": "sanity", "amount": 3, "effect_preview": "정신력 +3"},
                    {"content": "현재까지 정보로 추론한다", "effect": "health", "amount": 1, "effect_preview": "체력 +1"}
                ]

        else:
            if "즉시" in previous_choice:
                content = "대담한 행동이 상황을 급변시켰습니다!\n체력은 크게 소모되었지만 주도권을 잡았습니다."
                options = [
                    {"content": "계속 압박한다", "effect": "health", "amount": -4, "effect_preview": "체력 -4"},
                    {"content": "잠시 쉬면서 재정비한다", "effect": "health", "amount": 3, "effect_preview": "체력 +3"}
                ]
            elif "냉정하게" in previous_choice:
                content = "냉정한 판단으로 최적의 대응책을 찾았습니다.\n정신적으로 안정되고 상황을 통제하고 있습니다."
                options = [
                    {"content": "계획을 실행한다", "effect": "health", "amount": 2, "effect_preview": "체력 +2"},
                    {"content": "더 완벽한 계획을 세운다", "effect": "sanity", "amount": 2, "effect_preview": "정신력 +2"}
                ]
            else:
                content = "전략적 대기가 새로운 기회를 만들어냈습니다.\n정신적 긴장은 있지만 유리한 위치에 서게 되었습니다."
                options = [
                    {"content": "기회를 활용한다", "effect": "sanity", "amount": 4, "effect_preview": "정신력 +4"},
                    {"content": "더 기다린다", "effect": "sanity", "amount": -1, "effect_preview": "정신력 -1"}
                ]

        return content, options

    @staticmethod
    def get_random_allowed_theme() -> str:
        """허용된 테마 중 랜덤 선택"""
        return random.choice(ALLOWED_THEMES)


def test_themed_generation():
    """테마별 생성 테스트"""
    print("=== 테마 제한 Mock 데이터 테스트 ===")
    generator = MockStoryGenerator()

    test_stations = [
        ("사당", "공포"),
        ("종각", "미스터리"),
        ("시청", "스릴러")
    ]

    for station, expected_theme in test_stations:
        story = generator.generate_story(station, 80, 70)
        print(f"{station}역: {story['theme']} (예상: {expected_theme})")
        print(f"   제목: {story['story_title']}")
        print(f"   난이도: {story['difficulty']}")
        print(f"   선택지: {[opt['content'] for opt in story['options']]}")
        print()

    return True

def validate_theme_restriction():
    """테마 제한 검증"""
    print("=== 테마 제한 검증 ===")
    generator = MockStoryGenerator()

    all_themes = set()
    for station in STATION_CONFIG:
        story = generator.generate_story(station, 80, 80)
        all_themes.add(story['theme'])

    print(f"생성된 모든 테마: {all_themes}")
    print(f"허용된 테마: {set(ALLOWED_THEMES)}")

    if all_themes.issubset(set(ALLOWED_THEMES)):
        print("테마 제한 검증 통과")
        return True
    else:
        print("허용되지 않은 테마 발견")
        return False

if __name__ == "__main__":
    success1 = test_themed_generation()
    success2 = validate_theme_restriction()
    print(f"\n테스트 결과: {'성공' if (success1 and success2) else '실패'}")
