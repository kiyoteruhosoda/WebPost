"""
シナリオ実行API用のテストスクリプト

使い方:
    python scripts/test_api.py
"""
import requests
import json
from pathlib import Path


def test_health_check():
    """ヘルスチェック"""
    print("=== Health Check ===")
    response = requests.get("http://localhost:8000/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_run_scenario():
    """シナリオ実行テスト"""
    print("=== Run Scenario: fun-navi-reserve ===")
    
    # リクエストデータ
    request_data = {
        "vars": {
            "dates": ["", "2026/02/02", "2026/04/13"]
        },
        "secrets": {
            "username": "test_user",
            "password": "test_pass"
        }
    }
    
    # APIエンドポイントにPOST
    response = requests.post(
        "http://localhost:8000/scenarios/fun-navi-reserve/runs",
        json=request_data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print()


def test_scenario_not_found():
    """存在しないシナリオのテスト"""
    print("=== Scenario Not Found Test ===")
    
    response = requests.post(
        "http://localhost:8000/scenarios/not-exist/runs",
        json={"vars": {}, "secrets": {}}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


if __name__ == "__main__":
    try:
        test_health_check()
        test_run_scenario()
        test_scenario_not_found()
    except requests.exceptions.ConnectionError:
        print("❌ Error: APIサーバーが起動していません")
        print("以下のコマンドでサーバーを起動してください:")
        print("  python scripts/run_api.py")
