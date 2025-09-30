#!/usr/bin/env python3
"""
자연어 명령을 EPICS 제어 명령으로 변환하는 LLM 파서
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# .env 파일 로드
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)


@dataclass
class ControlCommand:
    """EPICS 제어 명령 데이터 클래스"""
    pv_name: str
    value: float
    unit: str
    description: str
    priority: int = 1  # 1=높음, 2=보통, 3=낮음


@dataclass
class ParsedCommand:
    """파싱된 자연어 명령"""
    original_command: str
    intent: str  # "temperature_control", "density_control", "heating_control", etc.
    target_value: Optional[float]
    duration: Optional[float]  # 초 단위
    control_commands: List[ControlCommand]
    safety_checks: List[str]
    estimated_time: float  # 예상 실행 시간 (초)


class CommandParser:
    """자연어 명령 파서"""
    
    def __init__(self):
        # OpenAI 클라이언트 초기화 (데모 모드 지원)
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self._client = OpenAI(api_key=api_key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            self.demo_mode = False
        else:
            self._client = None
            self.model = None
            self.demo_mode = True
            print("⚠️  OpenAI API 키가 없습니다. 데모 모드로 실행됩니다.")
        
        # KSTAR 제어 매핑 테이블
        self.control_mappings = {
            "temperature": {
                "coil_current": "KSTAR:COIL:CURR",
                "heater_power": "KSTAR:HEATER:POW", 
                "gas_flow": "KSTAR:GAS:FLOW",
                "magnetic_field": "KSTAR:MAGNET:BT"
            },
            "density": {
                "gas_flow": "KSTAR:GAS:FLOW",
                "pump_speed": "KSTAR:PUMP:SPEED",
                "pressure": "KSTAR:PRESSURE:SP"
            },
            "heating": {
                "ech_power": "KSTAR:ECH:POWER",
                "icrh_power": "KSTAR:ICRH:POWER",
                "nbi_power": "KSTAR:NBI:POWER"
            }
        }
    
    @property
    def client(self):
        """OpenAI 클라이언트 반환"""
        return self._client
    
    def parse_command(self, command: str) -> ParsedCommand:
        """자연어 명령을 파싱하여 구조화된 제어 명령으로 변환"""
        
        # 데모 모드에서는 간단한 규칙 기반 파싱 사용
        if self.demo_mode:
            return self._demo_parse_command(command)
        
        # 1단계: 기본 패턴 매칭으로 빠른 파싱 시도
        quick_parse = self._quick_parse(command)
        if quick_parse:
            return quick_parse
        
        # 2단계: LLM을 사용한 고급 파싱
        return self._llm_parse(command)
    
    def _demo_parse_command(self, command: str) -> ParsedCommand:
        """데모 모드용 간단한 규칙 기반 파싱"""
        
        # 온도 관련 키워드와 숫자 추출
        temp_patterns = [
            r'(?:temperature|temp|온도).*?(\d+(?:\.\d+)?)\s*(?:keV|kev|도)',
            r'(\d+(?:\.\d+)?)\s*(?:keV|kev|도)',
            r'(?:to|올려|낮춰|설정).*?(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)'
        ]
        
        target_temp = None
        for pattern in temp_patterns:
            matches = re.findall(pattern, command.lower())
            if matches:
                target_temp = float(matches[0])
                break
        
        # 기본값 설정
        if not target_temp:
            target_temp = 10.0
        
        # 온도에 따른 코일 전류와 가열 파워 계산
        base_current = 1200
        base_power = 50
        temp_diff = target_temp - 8.0  # 기준 온도 8keV
        
        coil_current = base_current + (temp_diff * 100)
        heater_power = base_power + (temp_diff * 5)
        
        return ParsedCommand(
            original_command=command,
            intent="temperature_control",
            target_value=target_temp,
            duration=5.0,
            control_commands=[
                ControlCommand(
                    pv_name="KSTAR:COIL:CURR",
                    value=coil_current,
                    unit="A",
                    description=f"Temperature control via coil current for {target_temp} keV",
                    priority=1
                ),
                ControlCommand(
                    pv_name="KSTAR:HEATER:POW",
                    value=heater_power,
                    unit="%",
                    description=f"Temperature control via heater power for {target_temp} keV",
                    priority=1
                )
            ],
            safety_checks=["demo_mode_safety_check"],
            estimated_time=5.0
        )
    
    def _quick_parse(self, command: str) -> Optional[ParsedCommand]:
        """기본 정규식 패턴으로 빠른 파싱"""
        
        # 온도 제어 패턴
        temp_patterns = [
            r'온도를?\s*(\d+(?:\.\d+)?)\s*(?:keV|도|도씨)?\s*(?:로|으로)?\s*(?:올려|높여|증가)',
            r'온도를?\s*(\d+(?:\.\d+)?)\s*(?:keV|도|도씨)?\s*(?:로|으로)?\s*(?:내려|낮춰|감소)',
            r'온도를?\s*(\d+(?:\.\d+)?)\s*(?:keV|도|도씨)?\s*(?:로|으로)?\s*(?:설정|조절)',
            r'온도를?\s*(\d+(?:\.\d+)?)\s*(?:keV|도|도씨)?\s*(?:로|으로)?\s*(?:유지)'
        ]
        
        for pattern in temp_patterns:
            match = re.search(pattern, command)
            if match:
                target_temp = float(match.group(1))
                duration = self._extract_duration(command)
                
                # 온도 제어 명령 생성
                control_commands = self._generate_temperature_commands(target_temp)
                
                return ParsedCommand(
                    original_command=command,
                    intent="temperature_control",
                    target_value=target_temp,
                    duration=duration,
                    control_commands=control_commands,
                    safety_checks=["temperature_range", "heating_power_limit"],
                    estimated_time=duration or 10.0
                )
        
        return None
    
    def _llm_parse(self, command: str) -> ParsedCommand:
        """LLM을 사용한 고급 명령 파싱"""
        
        system_prompt = """
당신은 KSTAR 플라즈마 제어 시스템의 전문가입니다. 
자연어 명령을 분석하여 EPICS 제어 명령으로 변환해주세요.

사용 가능한 제어 장치:
- 코일 전류 (COIL:CURR): 0-2000A, 온도 제어에 사용
- 가열 파워 (HEATER:POW): 0-100%, 온도 제어에 사용  
- 가스 주입 (GAS:FLOW): 0-1000sccm, 밀도 제어에 사용
- 자기장 (MAGNET:BT): 0-3.5T, 플라즈마 안정화에 사용

응답 형식:
{
    "intent": "temperature_control|density_control|heating_control|combined_control",
    "target_value": 숫자값,
    "duration": 초단위_시간,
    "control_commands": [
        {
            "pv_name": "PV이름",
            "value": 숫자값,
            "unit": "단위",
            "description": "설명",
            "priority": 1
        }
    ],
    "safety_checks": ["체크항목1", "체크항목2"],
    "estimated_time": 예상실행시간
}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"다음 명령을 분석해주세요: {command}"}
                ],
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # ControlCommand 객체로 변환
            control_commands = [
                ControlCommand(
                    pv_name=cmd["pv_name"],
                    value=cmd["value"],
                    unit=cmd["unit"],
                    description=cmd["description"],
                    priority=cmd.get("priority", 1)
                )
                for cmd in result["control_commands"]
            ]
            
            return ParsedCommand(
                original_command=command,
                intent=result["intent"],
                target_value=result.get("target_value"),
                duration=result.get("duration"),
                control_commands=control_commands,
                safety_checks=result.get("safety_checks", []),
                estimated_time=result.get("estimated_time", 10.0)
            )
            
        except Exception as e:
            print(f"LLM 파싱 오류: {e}")
            # 기본 파싱으로 폴백
            return self._create_fallback_command(command)
    
    def _extract_duration(self, command: str) -> Optional[float]:
        """명령에서 시간 정보 추출"""
        duration_patterns = [
            r'(\d+)\s*초\s*(?:동안|간)',
            r'(\d+)\s*분\s*(?:동안|간)',
            r'(\d+)\s*시간\s*(?:동안|간)'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, command)
            if match:
                value = float(match.group(1))
                if '분' in pattern:
                    return value * 60
                elif '시간' in pattern:
                    return value * 3600
                else:
                    return value
        
        return None
    
    def _generate_temperature_commands(self, target_temp: float) -> List[ControlCommand]:
        """온도 제어를 위한 EPICS 명령 생성"""
        commands = []
        
        # 현재 온도 가정 (실제로는 EPICS에서 읽어와야 함)
        current_temp = 8.0  # keV
        
        if target_temp > current_temp:
            # 온도 상승: 코일 전류 증가, 가열 파워 증가
            temp_diff = target_temp - current_temp
            
            # 코일 전류 계산 (경험적 공식)
            coil_current = min(1500 + temp_diff * 100, 2000)
            commands.append(ControlCommand(
                pv_name="KSTAR:COIL:CURR",
                value=coil_current,
                unit="A",
                description=f"온도 {target_temp}keV 달성을 위한 코일 전류 설정",
                priority=1
            ))
            
            # 가열 파워 계산
            heater_power = min(70 + temp_diff * 5, 100)
            commands.append(ControlCommand(
                pv_name="KSTAR:HEATER:POW",
                value=heater_power,
                unit="%",
                description=f"온도 {target_temp}keV 달성을 위한 가열 파워 설정",
                priority=1
            ))
        
        elif target_temp < current_temp:
            # 온도 하강: 코일 전류 감소, 가열 파워 감소
            temp_diff = current_temp - target_temp
            
            coil_current = max(1000 - temp_diff * 50, 500)
            commands.append(ControlCommand(
                pv_name="KSTAR:COIL:CURR",
                value=coil_current,
                unit="A",
                description=f"온도 {target_temp}keV 달성을 위한 코일 전류 감소",
                priority=1
            ))
            
            heater_power = max(30 - temp_diff * 3, 10)
            commands.append(ControlCommand(
                pv_name="KSTAR:HEATER:POW",
                value=heater_power,
                unit="%",
                description=f"온도 {target_temp}keV 달성을 위한 가열 파워 감소",
                priority=1
            ))
        
        return commands
    
    def _create_fallback_command(self, command: str) -> ParsedCommand:
        """파싱 실패 시 기본 명령 생성"""
        return ParsedCommand(
            original_command=command,
            intent="unknown",
            target_value=None,
            duration=None,
            control_commands=[],
            safety_checks=["manual_review"],
            estimated_time=5.0
        )


# 테스트 함수
def test_command_parser():
    """명령 파서 테스트"""
    parser = CommandParser()
    
    test_commands = [
        "플라즈마 온도를 10도 올려줘 5초 동안",
        "온도를 12 keV로 설정해줘",
        "밀도를 3e19로 조절해줘",
        "가열 파워를 80%로 올려줘"
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


if __name__ == "__main__":
    test_command_parser()
