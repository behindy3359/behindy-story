#!/usr/bin/env python3
"""
AI 서버 간단한 테스트 도구
직접 로그 확인용 - Docker 제외
"""

import requests
import json
import time

# 서버 URL
AI_SERVER = "http://localhost:8000"
SPRING_BOOT = "http://localhost:8080"

def test_ai_server():
    """AI 서버 기본 테스트"""
    print("🔍 AI 서버 테스트")
    print("-" * 20)
    
    try:
        # 헬스체크
        response = requests.get(f"{AI_SERVER}/health", timeout=5)
        if response.status_code == 200:
            print("✅ AI 서버 헬스체크 성공")
        else:
            print(f"❌ AI 서버 헬스체크 실패: {response.status_code}")
            return False
    except:
        print("❌ AI 서버 연결 실패")
        return False
    
    # 스토리 생성 테스트
    test_request = {
        "station_name": "강남",
        "line_number": 2,
        "character_health": 80,
        "character_sanity": 70
    }
    
    try:
        response = requests.post(f"{AI_SERVER}/generate-story", json=test_request, timeout=10)
        if response.status_code == 200:
            story = response.json()
            print(f"✅ 스토리 생성: {story['story_title']}")
            print(f"   선택지: {len(story['options'])}개")
            return True
        else:
            print(f"❌ 스토리 생성 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 스토리 생성 오류: {e}")
        return False

def test_spring_boot_connection():
    """Spring Boot 연동 테스트"""
    print("\n🔗 Spring Boot 연동 테스트")
    print("-" * 20)
    
    try:
        # AI 서버 상태 확인 (Spring Boot 경유)
        response = requests.get(f"{SPRING_BOOT}/api/ai-stories/health", timeout=5)
        if response.status_code == 200:
            print("✅ Spring Boot → AI 서버 연결 성공")
        else:
            print(f"❌ Spring Boot 연결 실패: {response.status_code}")
            return False
    except:
        print("❌ Spring Boot 서버 연결 실패")
        return False
    
    # Spring Boot를 통한 스토리 생성
    try:
        params = {
            "stationName": "강남",
            "lineNumber": 2,
            "characterHealth": 80,
            "characterSanity": 70
        }
        
        response = requests.get(f"{SPRING_BOOT}/api/ai-stories/generate", params=params, timeout=15)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Spring Boot 스토리 생성: {result.get('message', 'OK')}")
            return True
        else:
            print(f"❌ Spring Boot 스토리 생성 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Spring Boot 오류: {e}")
        return False

def test_story_flow():
    """스토리 흐름 테스트 (첫 페이지 → 선택 → 다음 페이지)"""
    print("\n📖 스토리 흐름 테스트")
    print("-" * 20)
    
    # 1. 첫 페이지 생성
    first_request = {
        "station_name": "옥수",
        "line_number": 3,
        "character_health": 80,
        "character_sanity": 80
    }
    
    try:
        response = requests.post(f"{AI_SERVER}/generate-story", json=first_request, timeout=10)
        if response.status_code != 200:
            print("❌ 첫 페이지 생성 실패")
            return False
            
        first_page = response.json()
        print(f"✅ 첫 페이지: {first_page['story_title']}")
        print(f"   내용: {first_page['page_content'][:50]}...")
        
        # 2. 첫 번째 선택지 선택
        selected_choice = first_page['options'][0]['content']
        print(f"   선택: {selected_choice}")
        
        # 3. 다음 페이지 생성
        continue_request = {
            "station_name": "옥수",
            "line_number": 3,
            "character_health": 75,  # 선택지 효과 반영
            "character_sanity": 80,
            "previous_choice": selected_choice,
            "story_context": "테스트 진행"
        }
        
        response = requests.post(f"{AI_SERVER}/continue-story", json=continue_request, timeout=10)
        if response.status_code == 200:
            next_page = response.json()
            print(f"✅ 다음 페이지: {next_page['page_content'][:50]}...")
            print(f"   다음 선택지: {len(next_page['options'])}개")
            return True
        else:
            print("❌ 다음 페이지 생성 실패")
            return False
            
    except Exception as e:
        print(f"❌ 스토리 흐름 테스트 오류: {e}")
        return False

def test_all_stations():
    """모든 역 테스트"""
    print("\n🚉 전체 역 테스트")
    print("-" * 20)
    
    stations = [
        ("종각", 1), ("시청", 1), ("서울역", 1),
        ("강남", 2), ("홍대입구", 2), ("잠실", 2),
        ("압구정", 3), ("교대", 3), ("옥수", 3),
        ("명동", 4), ("혜화", 4), ("사당", 4)
    ]
    
    success = 0
    for station, line in stations:
        try:
            request = {
                "station_name": station,
                "line_number": line,
                "character_health": 80,
                "character_sanity": 80
            }
            
            response = requests.post(f"{AI_SERVER}/generate-story", json=request, timeout=5)
            if response.status_code == 200:
                story = response.json()
                print(f"✅ {station}역: {story['theme']}")
                success += 1
            else:
                print(f"❌ {station}역 실패")
        except:
            print(f"❌ {station}역 오류")
        
        time.sleep(0.1)
    
    print(f"\n📊 결과: {success}/{len(stations)} 성공")
    return success == len(stations)

def main():
    """메인 테스트"""
    print("🚀 AI 서버 간단 테스트 시작")
    print("=" * 30)
    
    # 1. AI 서버 기본 테스트
    if not test_ai_server():
        print("❌ AI 서버 기본 테스트 실패")
        return
    
    # 2. Spring Boot 연동 테스트
    test_spring_boot_connection()
    
    # 3. 스토리 흐름 테스트
    test_story_flow()
    
    # 4. 전체 역 테스트
    test_all_stations()
    
    print("\n" + "=" * 30)
    print("🎯 테스트 완료")
    print("\n📋 다음 단계:")
    print("   1. 로그 파일에서 상세 정보 확인")
    print("   2. PostgreSQL에 데이터 저장 확인")
    print("   3. 실제 LLM API 연동 준비")

if __name__ == "__main__":
    main()