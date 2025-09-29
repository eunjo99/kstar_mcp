#!/usr/bin/env python3
"""
명령 실행 엔진 - 자연어 명령을 받아서 전체 제어 과정을 관리
"""

import asyncio
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from ..llm.command_parser import CommandParser, ParsedCommand, ControlCommand
from ..epics.controller import EPICSController, ControlResult, PVStatus


class ExecutionStatus(Enum):
    """실행 상태"""
    PENDING = "pending"
    PARSING = "parsing"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionStep:
    """실행 단계"""
    step_id: str
    name: str
    status: ExecutionStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None


@dataclass
class CommandExecution:
    """명령 실행 세션"""
    execution_id: str
    original_command: str
    parsed_command: Optional[ParsedCommand] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    steps: List[ExecutionStep] = field(default_factory=list)
    results: List[ControlResult] = field(default_factory=list)
    progress: float = 0.0
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    
    # 실시간 모니터링 데이터
    monitoring_data: Dict[str, List[Dict]] = field(default_factory=dict)
    
    # 콜백 함수들
    progress_callbacks: List[Callable] = field(default_factory=list)
    status_callbacks: List[Callable] = field(default_factory=list)


class CommandExecutionEngine:
    """명령 실행 엔진"""
    
    def __init__(self):
        self.parser = CommandParser()
        self.controller = EPICSController()
        self.active_executions: Dict[str, CommandExecution] = {}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def execute_command(self, command: str, execution_id: Optional[str] = None) -> CommandExecution:
        """자연어 명령 실행"""
        
        if not execution_id:
            execution_id = f"cmd_{int(time.time())}"
        
        execution = CommandExecution(
            execution_id=execution_id,
            original_command=command,
            status=ExecutionStatus.PENDING
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            await self._execute_command_internal(execution)
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            self.logger.error(f"명령 실행 실패: {e}")
        finally:
            execution.end_time = datetime.now()
            if execution.start_time:
                execution.progress = 100.0
        
        return execution
    
    async def _execute_command_internal(self, execution: CommandExecution):
        """내부 명령 실행 로직"""
        
        execution.start_time = datetime.now()
        execution.status = ExecutionStatus.PARSING
        
        # 1단계: 명령 파싱
        await self._add_step(execution, "parsing", "자연어 명령 파싱")
        try:
            execution.parsed_command = self.parser.parse_command(execution.original_command)
            await self._complete_step(execution, "parsing", execution.parsed_command)
            execution.progress = 20.0
        except Exception as e:
            await self._fail_step(execution, "parsing", str(e))
            raise
        
        # 2단계: 안전 검사
        await self._add_step(execution, "safety_check", "안전 검사")
        try:
            safety_result = await self._perform_safety_checks(execution.parsed_command)
            await self._complete_step(execution, "safety_check", safety_result)
            execution.progress = 40.0
        except Exception as e:
            await self._fail_step(execution, "safety_check", str(e))
            raise
        
        # 3단계: 제어 명령 실행
        execution.status = ExecutionStatus.EXECUTING
        await self._add_step(execution, "execution", "EPICS 제어 명령 실행")
        try:
            execution.results = await self.controller.execute_parsed_command(execution.parsed_command)
            await self._complete_step(execution, "execution", execution.results)
            execution.progress = 70.0
        except Exception as e:
            await self._fail_step(execution, "execution", str(e))
            raise
        
        # 4단계: 결과 모니터링
        execution.status = ExecutionStatus.MONITORING
        await self._add_step(execution, "monitoring", "결과 모니터링")
        try:
            monitoring_result = await self._monitor_results(execution)
            await self._complete_step(execution, "monitoring", monitoring_result)
            execution.progress = 90.0
        except Exception as e:
            await self._fail_step(execution, "monitoring", str(e))
            # 모니터링 실패는 치명적이지 않음
        
        # 5단계: 완료
        execution.status = ExecutionStatus.COMPLETED
        execution.progress = 100.0
        
        self.logger.info(f"명령 실행 완료: {execution.execution_id}")
    
    async def _add_step(self, execution: CommandExecution, step_id: str, name: str):
        """실행 단계 추가"""
        step = ExecutionStep(
            step_id=step_id,
            name=name,
            status=ExecutionStatus.PENDING,
            start_time=datetime.now()
        )
        execution.steps.append(step)
        execution.current_step = step_id
        
        self.logger.info(f"단계 시작: {name}")
        await self._notify_status_change(execution)
    
    async def _complete_step(self, execution: CommandExecution, step_id: str, result: Any):
        """실행 단계 완료"""
        for step in execution.steps:
            if step.step_id == step_id:
                step.status = ExecutionStatus.COMPLETED
                step.end_time = datetime.now()
                step.result = result
                if step.start_time:
                    step.duration = (step.end_time - step.start_time).total_seconds()
                break
        
        self.logger.info(f"단계 완료: {step_id}")
        await self._notify_status_change(execution)
    
    async def _fail_step(self, execution: CommandExecution, step_id: str, error_message: str):
        """실행 단계 실패"""
        for step in execution.steps:
            if step.step_id == step_id:
                step.status = ExecutionStatus.FAILED
                step.end_time = datetime.now()
                step.error_message = error_message
                if step.start_time:
                    step.duration = (step.end_time - step.start_time).total_seconds()
                break
        
        self.logger.error(f"단계 실패: {step_id} - {error_message}")
        await self._notify_status_change(execution)
    
    async def _perform_safety_checks(self, parsed_command: ParsedCommand) -> Dict[str, Any]:
        """안전 검사 수행"""
        safety_result = {
            "passed": True,
            "checks": [],
            "warnings": []
        }
        
        for command in parsed_command.control_commands:
            # 안전 제한 검사
            if not self.controller._check_safety_limits(command.pv_name, command.value):
                safety_result["passed"] = False
                safety_result["checks"].append({
                    "type": "safety_limit",
                    "pv": command.pv_name,
                    "value": command.value,
                    "status": "FAILED"
                })
            else:
                safety_result["checks"].append({
                    "type": "safety_limit",
                    "pv": command.pv_name,
                    "value": command.value,
                    "status": "PASSED"
                })
        
        # 추가 안전 검사들
        if parsed_command.duration and parsed_command.duration > 60:
            safety_result["warnings"].append("장시간 제어 실행 - 주의 필요")
        
        return safety_result
    
    async def _monitor_results(self, execution: CommandExecution) -> Dict[str, Any]:
        """결과 모니터링"""
        monitoring_result = {
            "monitoring_time": 10.0,  # 10초간 모니터링
            "data_points": [],
            "success_rate": 0.0
        }
        
        if not execution.results:
            return monitoring_result
        
        # 모니터링할 PV 목록 (온도 관련 PV들)
        monitor_pvs = [
            "KSTAR:PCS:TE:SP",   # 온도 설정값
            "KSTAR:PCS:TE:RBV",  # 온도 측정값
            "KSTAR:COIL:CURR",   # 코일 전류
            "KSTAR:HEATER:POW"   # 가열 파워
        ]
        
        # 모니터링 데이터 수집
        start_time = time.time()
        data_points = []
        
        while time.time() - start_time < monitoring_result["monitoring_time"]:
            point = {
                "timestamp": datetime.now().isoformat(),
                "values": {}
            }
            
            for pv_name in monitor_pvs:
                value = self.controller.get_pv_value(pv_name)
                point["values"][pv_name] = value
            
            data_points.append(point)
            execution.monitoring_data["realtime"] = data_points[-20:]  # 최근 20개만 유지
            
            # WebSocket으로 실시간 데이터 브로드캐스트
            await self._broadcast_monitoring_data(execution)
            
            await asyncio.sleep(0.2)  # 0.2초마다 샘플링
        
        monitoring_result["data_points"] = data_points
        
        # 성공률 계산
        successful_commands = sum(1 for r in execution.results if r.success)
        monitoring_result["success_rate"] = successful_commands / len(execution.results)
        
        return monitoring_result
    
    async def _broadcast_monitoring_data(self, execution: CommandExecution):
        """모니터링 데이터를 WebSocket으로 브로드캐스트"""
        # 이 메서드는 UI에서 WebSocket 연결을 통해 호출됩니다
        pass
    
    async def _notify_status_change(self, execution: CommandExecution):
        """상태 변경 알림"""
        for callback in execution.status_callbacks:
            try:
                await callback(execution)
            except Exception as e:
                self.logger.error(f"상태 콜백 오류: {e}")
    
    async def _notify_progress_change(self, execution: CommandExecution):
        """진행률 변경 알림"""
        for callback in execution.progress_callbacks:
            try:
                await callback(execution)
            except Exception as e:
                self.logger.error(f"진행률 콜백 오류: {e}")
    
    def get_execution_status(self, execution_id: str) -> Optional[CommandExecution]:
        """실행 상태 조회"""
        return self.active_executions.get(execution_id)
    
    def cancel_execution(self, execution_id: str) -> bool:
        """실행 취소"""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = ExecutionStatus.CANCELLED
            execution.end_time = datetime.now()
            self.logger.info(f"실행 취소: {execution_id}")
            return True
        return False
    
    def get_active_executions(self) -> List[CommandExecution]:
        """활성 실행 목록 조회"""
        return list(self.active_executions.values())
    
    def cleanup_completed_executions(self):
        """완료된 실행 정리"""
        completed_ids = []
        for execution_id, execution in self.active_executions.items():
            if execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                completed_ids.append(execution_id)
        
        for execution_id in completed_ids:
            del self.active_executions[execution_id]
        
        if completed_ids:
            self.logger.info(f"완료된 실행 정리: {len(completed_ids)}개")


# 테스트 함수
async def test_execution_engine():
    """실행 엔진 테스트"""
    engine = CommandExecutionEngine()
    
    test_command = "플라즈마 온도를 10 keV로 올려줘"
    
    print(f"테스트 명령: {test_command}")
    
    execution = await engine.execute_command(test_command)
    
    print(f"실행 ID: {execution.execution_id}")
    print(f"상태: {execution.status}")
    print(f"진행률: {execution.progress}%")
    print(f"단계 수: {len(execution.steps)}")
    
    for step in execution.steps:
        print(f"  - {step.name}: {step.status}")


if __name__ == "__main__":
    asyncio.run(test_execution_engine())
