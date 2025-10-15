#!/usr/bin/env python3
"""
Command Execution Engine - Orchestrates natural language command execution

This module provides the main execution engine that coordinates the entire
process of executing natural language commands. It manages the workflow
from command parsing to EPICS execution and monitoring.

Key Features:
- Command parsing and validation
- Safety checks and limit validation
- EPICS command execution
- Real-time monitoring and feedback
- Progress tracking and status updates
- Error handling and recovery

This PoC demonstrates a simple approach where target values are set and
current values gradually follow. Future versions will integrate with
sophisticated plasma physics models and machine learning algorithms.
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
    """Command execution status"""
    PENDING = "pending"
    PARSING = "parsing"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionStep:
    """Command execution step"""
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
    """Command execution session"""
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
    
    # Real-time monitoring data
    monitoring_data: Dict[str, List[Dict]] = field(default_factory=dict)
    
    # Callback functions
    progress_callbacks: List[Callable] = field(default_factory=list)
    status_callbacks: List[Callable] = field(default_factory=list)


class CommandExecutionEngine:
    """Command execution engine
    
    This class orchestrates the entire process of executing natural language
    commands, from parsing to EPICS execution and monitoring. It provides
    comprehensive workflow management with safety checks and progress tracking.
    """
    
    def __init__(self):
        self.parser = CommandParser()
        self.controller = EPICSController()
        self.active_executions: Dict[str, CommandExecution] = {}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def execute_command(self, command: str, execution_id: Optional[str] = None) -> CommandExecution:
        """Execute natural language command
        
        Args:
            command: Natural language command string
            execution_id: Optional execution ID
            
        Returns:
            CommandExecution object with execution details
        """
        
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
            self.logger.error(f"Command execution failed: {e}")
        finally:
            execution.end_time = datetime.now()
            if execution.start_time:
                execution.progress = 100.0
        
        return execution
    
    async def _execute_command_internal(self, execution: CommandExecution):
        """Internal command execution logic
        
        Args:
            execution: CommandExecution object to process
        """
        
        execution.start_time = datetime.now()
        execution.status = ExecutionStatus.PARSING
        
        # Step 1: Command parsing
        await self._add_step(execution, "parsing", "Natural language command parsing")
        try:
            execution.parsed_command = self.parser.parse_command(execution.original_command)
            await self._complete_step(execution, "parsing", execution.parsed_command)
            execution.progress = 20.0
        except Exception as e:
            await self._fail_step(execution, "parsing", str(e))
            raise
        
        # Step 2: Safety checks
        await self._add_step(execution, "safety_check", "Safety validation")
        try:
            safety_result = await self._perform_safety_checks(execution.parsed_command)
            await self._complete_step(execution, "safety_check", safety_result)
            execution.progress = 40.0
        except Exception as e:
            await self._fail_step(execution, "safety_check", str(e))
            raise
        
        # Step 3: Control command execution
        execution.status = ExecutionStatus.EXECUTING
        await self._add_step(execution, "execution", "EPICS control command execution")
        try:
            execution.results = await self.controller.execute_parsed_command(execution.parsed_command)
            await self._complete_step(execution, "execution", execution.results)
            execution.progress = 70.0
        except Exception as e:
            await self._fail_step(execution, "execution", str(e))
            raise
        
        # Step 4: Result monitoring
        execution.status = ExecutionStatus.MONITORING
        await self._add_step(execution, "monitoring", "Result monitoring")
        try:
            monitoring_result = await self._monitor_results(execution)
            await self._complete_step(execution, "monitoring", monitoring_result)
            execution.progress = 90.0
        except Exception as e:
            await self._fail_step(execution, "monitoring", str(e))
            # Monitoring failure is not critical
            pass
        
        # Step 5: Completion
        execution.status = ExecutionStatus.COMPLETED
        execution.progress = 100.0
        
        self.logger.info(f"Command execution completed: {execution.execution_id}")
    
    async def _add_step(self, execution: CommandExecution, step_id: str, name: str):
        """Add execution step
        
        Args:
            execution: CommandExecution object
            step_id: Unique step identifier
            name: Human-readable step name
        """
        step = ExecutionStep(
            step_id=step_id,
            name=name,
            status=ExecutionStatus.PENDING,
            start_time=datetime.now()
        )
        execution.steps.append(step)
        execution.current_step = step_id
        
        self.logger.info(f"Step started: {name}")
        await self._notify_status_change(execution)
    
    async def _complete_step(self, execution: CommandExecution, step_id: str, result: Any):
        """Complete execution step
        
        Args:
            execution: CommandExecution object
            step_id: Step identifier
            result: Step execution result
        """
        for step in execution.steps:
            if step.step_id == step_id:
                step.status = ExecutionStatus.COMPLETED
                step.end_time = datetime.now()
                step.result = result
                if step.start_time:
                    step.duration = (step.end_time - step.start_time).total_seconds()
                break
        
        self.logger.info(f"Step completed: {step_id}")
        await self._notify_status_change(execution)
    
    async def _fail_step(self, execution: CommandExecution, step_id: str, error_message: str):
        """Fail execution step
        
        Args:
            execution: CommandExecution object
            step_id: Step identifier
            error_message: Error description
        """
        for step in execution.steps:
            if step.step_id == step_id:
                step.status = ExecutionStatus.FAILED
                step.end_time = datetime.now()
                step.error_message = error_message
                if step.start_time:
                    step.duration = (step.end_time - step.start_time).total_seconds()
                break
        
        self.logger.error(f"Step failed: {step_id} - {error_message}")
        await self._notify_status_change(execution)
    
    async def _perform_safety_checks(self, parsed_command: ParsedCommand) -> Dict[str, Any]:
        """Perform safety checks on parsed command
        
        Args:
            parsed_command: ParsedCommand object to validate
            
        Returns:
            Dictionary with safety check results
        """
        safety_result = {
            "passed": True,
            "checks": [],
            "warnings": []
        }
        
        for command in parsed_command.control_commands:
            # Safety limit check
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
        
        # Additional safety checks
        if parsed_command.duration and parsed_command.duration > 60:
            safety_result["warnings"].append("Long-term control execution - caution required")
        
        return safety_result
    
    async def _monitor_results(self, execution: CommandExecution) -> Dict[str, Any]:
        """Monitor command execution results
        
        Args:
            execution: CommandExecution object
            
        Returns:
            Dictionary with monitoring results
        """
        monitoring_result = {
            "monitoring_time": 10.0,  # 10초간 모니터링
            "data_points": [],
            "success_rate": 0.0
        }
        
        if not execution.results:
            return monitoring_result
        
        # Monitor PVs (temperature-related PVs)
        monitor_pvs = [
            "KSTAR:PCS:TE:SP",   # Temperature setpoint
            "KSTAR:PCS:TE:RBV",  # Temperature readback value
            "KSTAR:COIL:CURR",   # Coil current
            "KSTAR:HEATER:POW"   # Heater power
        ]
        
        # Collect monitoring data
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
            execution.monitoring_data["realtime"] = data_points[-20:]  # Keep recent 20 points
            
            # Broadcast real-time data via WebSocket
            await self._broadcast_monitoring_data(execution)
            
            await asyncio.sleep(0.2)  # Sample every 0.2 seconds
        
        monitoring_result["data_points"] = data_points
        
        # Calculate success rate
        successful_commands = sum(1 for r in execution.results if r.success)
        monitoring_result["success_rate"] = successful_commands / len(execution.results)
        
        return monitoring_result
    
    async def _broadcast_monitoring_data(self, execution: CommandExecution):
        """Broadcast monitoring data via WebSocket
        
        Args:
            execution: CommandExecution object
        """
        # This method is called from UI via WebSocket connection
        pass
    
    async def _notify_status_change(self, execution: CommandExecution):
        """Notify status change to callbacks
        
        Args:
            execution: CommandExecution object
        """
        for callback in execution.status_callbacks:
            try:
                await callback(execution)
            except Exception as e:
                self.logger.error(f"Status callback error: {e}")
    
    async def _notify_progress_change(self, execution: CommandExecution):
        """Notify progress change to callbacks
        
        Args:
            execution: CommandExecution object
        """
        for callback in execution.progress_callbacks:
            try:
                await callback(execution)
            except Exception as e:
                self.logger.error(f"Progress callback error: {e}")
    
    def get_execution_status(self, execution_id: str) -> Optional[CommandExecution]:
        """Get execution status
        
        Args:
            execution_id: Execution identifier
            
        Returns:
            CommandExecution object or None
        """
        return self.active_executions.get(execution_id)
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel execution
        
        Args:
            execution_id: Execution identifier
            
        Returns:
            True if cancelled successfully
        """
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = ExecutionStatus.CANCELLED
            execution.end_time = datetime.now()
            self.logger.info(f"Execution cancelled: {execution_id}")
            return True
        return False
    
    def get_active_executions(self) -> List[CommandExecution]:
        """Get active executions
        
        Returns:
            List of active CommandExecution objects
        """
        return list(self.active_executions.values())
    
    def cleanup_completed_executions(self):
        """Clean up completed executions
        
        Removes completed, failed, or cancelled executions from memory
        to prevent memory leaks in long-running applications.
        """
        completed_ids = []
        for execution_id, execution in self.active_executions.items():
            if execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                completed_ids.append(execution_id)
        
        for execution_id in completed_ids:
            del self.active_executions[execution_id]
        
        if completed_ids:
            self.logger.info(f"Completed executions cleaned up: {len(completed_ids)}")


# Test function
async def test_execution_engine():
    """Test execution engine functionality"""
    engine = CommandExecutionEngine()
    
    test_command = "Raise plasma temperature to 10 keV"
    
    print(f"Test command: {test_command}")
    
    execution = await engine.execute_command(test_command)
    
    print(f"Execution ID: {execution.execution_id}")
    print(f"Status: {execution.status}")
    print(f"Progress: {execution.progress}%")
    print(f"Steps: {len(execution.steps)}")
    
    for step in execution.steps:
        print(f"  - {step.name}: {step.status}")


if __name__ == "__main__":
    asyncio.run(test_execution_engine())
