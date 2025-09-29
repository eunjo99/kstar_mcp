#!/usr/bin/env python3
"""
KSTAR MCP PoC v2 - 메인 실행 파일
"""

import os
import sys
import asyncio
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.ui.demo_ui import DemoModeUI


def main():
    """메인 실행 함수"""
    
    # 환경 변수 로드
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # .env 파일이 없으면 config.env.example 사용
        env_file = project_root / "config.env.example"
        if env_file.exists():
            load_dotenv(env_file)
    
    # 환경 변수 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OpenAI API 키가 설정되지 않았습니다.")
        print("   config.env.example 파일을 복사하여 .env 파일을 만들고 API 키를 설정하세요.")
        return
    
    print("🚀 KSTAR MCP PoC v2 시작...")
    print("📋 프로젝트 정보:")
    print(f"   - 프로젝트 루트: {project_root}")
    print(f"   - OpenAI 모델: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
    print(f"   - EPICS 서버: {os.getenv('EPICS_CA_ADDR_LIST', '127.0.0.1')}")
    print(f"   - 서버 포트: {os.getenv('PORT', '8000')}")
    
    # UI 서버 실행 (데모 모드)
    ui = DemoModeUI()
    ui.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000"))
    )


if __name__ == "__main__":
    main()
