#!/usr/bin/env python3
"""
KSTAR MCP PoC v2 - 테스트 스크립트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.llm.command_parser import CommandParser, test_command_parser
from src.epics.controller import EPICSController, test_epics_controller
from src.core.execution_engine import CommandExecutionEngine, test_execution_engine


async def test_full_system():
    """전체 시스템 테스트"""
    print("🧪 KSTAR MCP PoC v2 전체 시스템 테스트")
    print("=" * 50)
    
    # 1. 명령 파서 테스트
    print("\n1️⃣ 명령 파서 테스트")
    print("-" * 30)
    test_command_parser()
    
    # 2. EPICS 컨트롤러 테스트
    print("\n2️⃣ EPICS 컨트롤러 테스트")
    print("-" * 30)
    test_epics_controller()
    
    # 3. 실행 엔진 테스트
    print("\n3️⃣ 실행 엔진 테스트")
    print("-" * 30)
    await test_execution_engine()
    
    print("\n✅ 모든 테스트 완료!")


def test_individual_components():
    """개별 컴포넌트 테스트"""
    print("🔧 개별 컴포넌트 테스트")
    print("=" * 30)
    
    # 명령 파서만 테스트
    parser = CommandParser()
    test_commands = [
        "플라즈마 온도를 10도 올려줘 5초 동안",
        "온도를 12 keV로 설정해줘",
        "밀도를 3e19로 조절해줘"
    ]
    
    for cmd in test_commands:
        print(f"\n명령: {cmd}")
        result = parser.parse_command(cmd)
        print(f"의도: {result.intent}")
        print(f"목표값: {result.target_value}")
        print(f"지속시간: {result.duration}초")
        print(f"제어명령 수: {len(result.control_commands)}")
        
        for cmd_obj in result.control_commands:
            print(f"  - {cmd_obj.pv_name} = {cmd_obj.value} {cmd_obj.unit}")


def main():
    """메인 테스트 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="KSTAR MCP PoC v2 테스트")
    parser.add_argument("--component", choices=["parser", "epics", "engine", "all"], 
                       default="all", help="테스트할 컴포넌트 선택")
    
    args = parser.parse_args()
    
    if args.component == "parser":
        test_command_parser()
    elif args.component == "epics":
        test_epics_controller()
    elif args.component == "engine":
        asyncio.run(test_execution_engine())
    elif args.component == "all":
        asyncio.run(test_full_system())
    
    print("\n🎉 테스트 완료!")


if __name__ == "__main__":
    main()
