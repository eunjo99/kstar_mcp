#!/usr/bin/env python3
"""
Demo Mode UI - Web-based interface for KSTAR MCP PoC v2

This module provides a complete web-based user interface that works without EPICS connection.
It simulates the natural language to EPICS command translation process and provides
real-time monitoring of plasma parameters.

Key Features:
- Real-time WebSocket communication
- Interactive command input and execution
- Live temperature and parameter monitoring
- Command translation visualization
- Demo mode with realistic simulation

This is designed as a PoC to demonstrate the concept of natural language control
of plasma parameters, with plans for future integration with sophisticated models.
"""

import asyncio
import json
import random
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ..core.execution_engine import CommandExecutionEngine, CommandExecution, ExecutionStatus
from ..epics.controller import EPICSController


class ConnectionManager:
    """WebSocket connection manager for real-time communication"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                if connection in self.active_connections:
                    self.active_connections.remove(connection)


class DemoModeUI:
    """Demo Mode UI - Complete web interface without EPICS dependency
    
    This class provides a full-featured web UI that simulates the KSTAR control system
    without requiring actual EPICS hardware. It demonstrates the natural language
    to EPICS command translation process and provides realistic parameter monitoring.
    """
    
    def __init__(self):
        self.app = FastAPI(title="KSTAR MCP PoC v2 - Demo Mode")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        self.connection_manager = ConnectionManager()
        self.execution_engine = CommandExecutionEngine()
        
        # Demo mode virtual PV values (simulated KSTAR parameters)
        self.demo_values = {
            "KSTAR:PCS:TE:SP": 8.0,    # Temperature setpoint (keV)
            "KSTAR:PCS:TE:RBV": 8.0,   # Temperature readback value (keV)
            "KSTAR:COIL:CURR": 1200.0, # Coil current (A)
            "KSTAR:HEATER:POW": 50.0   # Heater power (%)
        }
        
        # Continuous monitoring data for real-time updates
        self.continuous_monitoring = {
            "temperature_history": [],
            "command_history": [],
            "last_update": None
        }
        
        self._setup_routes()
        self._setup_websocket_handlers()
    
    def _setup_routes(self):
        """Setup FastAPI routes for web interface"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def get_ui():
            return self._get_demo_html_ui()
        
        @self.app.post("/command")
        async def execute_command(request: dict):
            command = request.get("command", "")
            if not command:
                raise HTTPException(status_code=400, detail="Command is required")
            
            # Execute command simulation instead of real EPICS commands
            execution = await self._simulate_command_execution(command)
            
            # Add command to history for tracking
            command_record = {
                "timestamp": datetime.now().isoformat(),
                "original_command": command,
                "parsed_command": execution.get("parsed_command", {}),
                "results": execution.get("results", [])
            }
            
            self.continuous_monitoring["command_history"].append(command_record)
            
            # Broadcast command execution via WebSocket
            await self.connection_manager.broadcast(json.dumps({
                "type": "command_executed",
                "command_record": command_record
            }))
            
            return {
                "execution_id": f"demo_{int(time.time())}",
                "status": "completed",
                "message": "Command executed successfully (Demo Mode)"
            }
        
        @self.app.get("/monitoring/status")
        async def get_monitoring_status():
            return {
                "temperature_history": self.continuous_monitoring["temperature_history"][-100:],
                "command_history": self.continuous_monitoring["command_history"][-10:],
                "last_update": self.continuous_monitoring["last_update"]
            }
        
        @self.app.get("/system/status")
        async def get_system_status():
            return {
                "epics_available": False,
                "demo_mode": True,
                "pv_status": {
                    pv: {"value": value, "connected": True}
                    for pv, value in self.demo_values.items()
                }
            }
    
    def _setup_websocket_handlers(self):
        """Setup WebSocket handlers for real-time communication"""
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.connection_manager.connect(websocket)
            
            try:
                while True:
                    # Continuous temperature monitoring (demo mode)
                    await self._update_demo_monitoring()
                    
                    # Send real-time data via WebSocket
                    await self.connection_manager.broadcast(json.dumps({
                        "type": "continuous_update",
                        "temperature_data": self.continuous_monitoring["temperature_history"][-50:],
                        "current_status": self.demo_values,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    await asyncio.sleep(0.5)  # Update every 0.5 seconds
                    
            except WebSocketDisconnect:
                self.connection_manager.disconnect(websocket)
    
    async def _update_demo_monitoring(self):
        """Update demo monitoring data with realistic temperature changes
        
        This simulates how plasma temperature gradually approaches target values,
        providing a realistic demonstration of the control system behavior.
        """
        try:
            # Simulate gradual temperature approach to target
            target_temp = self.demo_values["KSTAR:PCS:TE:SP"]
            current_temp = self.demo_values["KSTAR:PCS:TE:RBV"]
            
            # Gradually approach target temperature if difference exists
            if abs(target_temp - current_temp) > 0.01:
                diff = target_temp - current_temp
                # Move 5% of difference every 0.5 seconds (realistic behavior)
                self.demo_values["KSTAR:PCS:TE:RBV"] += diff * 0.05
            
            # Add temperature record to history
            temp_record = {
                "timestamp": datetime.now().isoformat(),
                "sp": self.demo_values["KSTAR:PCS:TE:SP"],
                "rbv": self.demo_values["KSTAR:PCS:TE:RBV"],
                "coil_current": self.demo_values["KSTAR:COIL:CURR"],
                "heater_power": self.demo_values["KSTAR:HEATER:POW"]
            }
            
            self.continuous_monitoring["temperature_history"].append(temp_record)
            
            # Keep maximum 200 data points for performance
            if len(self.continuous_monitoring["temperature_history"]) > 200:
                self.continuous_monitoring["temperature_history"] = self.continuous_monitoring["temperature_history"][-200:]
            
            self.continuous_monitoring["last_update"] = datetime.now().isoformat()
            
        except Exception as e:
            print(f"Demo monitoring update error: {e}")
    
    async def _simulate_command_execution(self, command: str) -> Dict[str, Any]:
        """Simulate command execution with improved parsing
        
        This method parses natural language commands and simulates the execution
        of EPICS control commands, providing realistic feedback for the demo.
        """
        
        # Extract numbers from command (improved parsing)
        import re
        
        # Temperature-related keywords and number extraction
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
        
        # Set default value if no temperature found
        if not target_temp:
            target_temp = 10.0
        
        # Generate control commands based on temperature
        base_current = 1200
        base_power = 50
        temp_diff = target_temp - 8.0  # Reference temperature 8keV
        
        coil_current = base_current + (temp_diff * 100)
        heater_power = base_power + (temp_diff * 5)
        
        parsed_command = {
            "intent": "temperature_control",
            "target_value": target_temp,
            "duration": 5.0,
            "control_commands": [
                {
                    "pv_name": "KSTAR:COIL:CURR",
                    "value": coil_current,
                    "unit": "A",
                    "description": f"Temperature control via coil current for {target_temp} keV"
                },
                {
                    "pv_name": "KSTAR:HEATER:POW",
                    "value": heater_power,
                    "unit": "%",
                    "description": f"Temperature control via heater power for {target_temp} keV"
                }
            ]
        }
        
        # Simulate execution results (store previous values)
        results = []
        
        # Store previous values before command execution
        old_values = {
            "KSTAR:COIL:CURR": self.demo_values.get("KSTAR:COIL:CURR", 0),
            "KSTAR:HEATER:POW": self.demo_values.get("KSTAR:HEATER:POW", 0)
        }
        
        # Set target temperature immediately (actual temperature follows gradually via WebSocket)
        target_temp = parsed_command["target_value"]
        if target_temp:
            self.demo_values["KSTAR:PCS:TE:SP"] = target_temp
            
            # Calculate coil current and heater power based on temperature
            base_current = 1200
            base_power = 50
            temp_diff = target_temp - 8.0  # Reference temperature 8keV
            
            self.demo_values["KSTAR:COIL:CURR"] = base_current + (temp_diff * 100)
            self.demo_values["KSTAR:HEATER:POW"] = base_power + (temp_diff * 5)
        
        # Execute each command and record results
        for cmd in parsed_command["control_commands"]:
            old_value = old_values[cmd["pv_name"]]
            new_value = cmd["value"]
            
            results.append({
                "pv_name": cmd["pv_name"],
                "value": cmd["value"],
                "unit": cmd["unit"],
                "success": True,
                "old_value": old_value,
                "new_value": new_value,
                "execution_time": 0.1
            })
        
        # Target temperature is set immediately, actual temperature follows gradually
        target_temp = parsed_command["target_value"]
        if target_temp:
            # Set target temperature immediately
            self.demo_values["KSTAR:PCS:TE:SP"] = target_temp
            
            # Actual temperature follows gradually (handled by WebSocket)
            # Don't change immediately here
        
        return {
            "parsed_command": parsed_command,
            "results": results
        }
    
    def _get_demo_html_ui(self) -> str:
        """Return demo HTML UI with complete web interface
        
        This method returns a complete HTML page with embedded CSS and JavaScript
        that provides a modern, responsive interface for the KSTAR control system.
        """
        return """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KSTAR MCP PoC v2 - Demo Mode</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 25px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            backdrop-filter: blur(15px);
            border: 2px solid rgba(0, 212, 255, 0.3);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 15px;
            background: linear-gradient(45deg, #00d4ff, #ff6b6b, #4ade80);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .demo-banner {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 10px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: bold;
        }
        
        .main-layout {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .control-panel {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 25px;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .monitoring-panel {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 25px;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .panel-title {
            font-size: 1.3em;
            margin-bottom: 20px;
            color: #00d4ff;
            border-bottom: 2px solid #00d4ff;
            padding-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .command-input {
            width: 100%;
            padding: 15px;
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            background: rgba(255, 255, 255, 0.05);
            color: white;
            font-size: 1.1em;
            margin-bottom: 15px;
        }
        
        .command-input:focus {
            outline: none;
            border-color: #00d4ff;
            box-shadow: 0 0 25px rgba(0, 212, 255, 0.4);
        }
        
        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-right: 10px;
            margin-bottom: 10px;
        }
        
        .btn-primary {
            background: linear-gradient(45deg, #00d4ff, #0099cc);
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 212, 255, 0.4);
        }
        
        .btn-demo {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        }
        
        .btn-demo:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(255, 107, 107, 0.4);
        }
        
        /* 실시간 상태 표시 */
        .status-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .status-card {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 15px;
            padding: 15px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        
        .status-card:hover {
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-2px);
        }
        
        .status-card h3 {
            font-size: 1em;
            margin-bottom: 8px;
            color: #00d4ff;
        }
        
        .status-value {
            font-size: 1.8em;
            font-weight: bold;
            font-family: 'Courier New', monospace;
        }
        
        .status-unit {
            font-size: 0.8em;
            opacity: 0.7;
            margin-top: 5px;
        }
        
        /* 실시간 차트 */
        .chart-container {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        #temperatureChart {
            width: 100%;
            height: 400px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .chart-legend {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 15px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
        }
        
        .legend-color {
            width: 20px;
            height: 3px;
            border-radius: 2px;
        }
        
        .legend-sp { background: #2563eb; }
        .legend-rbv { background: #f59e0b; }
        .legend-coil { background: #8b5cf6; }
        .legend-heater { background: #ef4444; }
        
        /* 명령 변환 과정 표시 */
        .command-conversion {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .conversion-step {
            margin: 15px 0;
            padding: 15px;
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.2);
            border-left: 4px solid #00d4ff;
            animation: slideIn 0.5s ease-out;
        }
        
        .conversion-step.set-command {
            border-left-color: #ff6b6b;
            background: rgba(255, 107, 107, 0.1);
        }
        
        @keyframes slideIn {
            from { transform: translateX(-100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .step-header {
            font-weight: bold;
            color: #00d4ff;
            margin-bottom: 8px;
        }
        
        .step-content {
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        .pv-name {
            color: #00d4ff;
            font-weight: bold;
        }
        
        .pv-value {
            color: #4ade80;
            font-weight: bold;
        }
        
        .pv-unit {
            color: #f59e0b;
        }
        
        /* 명령 히스토리 */
        .command-history {
            max-height: 300px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            padding: 15px;
        }
        
        .history-item {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
            border-left: 3px solid #00d4ff;
            font-size: 0.9em;
        }
        
        .history-timestamp {
            color: #64748b;
            font-size: 0.8em;
        }
        
        .history-command {
            color: #ffffff;
            margin: 5px 0;
        }
        
        .history-result {
            color: #4ade80;
            font-family: 'Courier New', monospace;
            font-size: 0.8em;
        }
        
        /* 연결 상태 */
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        
        .connected {
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
            border: 2px solid #22c55e;
        }
        
        .disconnected {
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            border: 2px solid #ef4444;
        }
        
        /* 애니메이션 */
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* 반응형 */
        @media (max-width: 1200px) {
            .main-layout {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 KSTAR MCP PoC v2</h1>
            <p>Interactive Real-time Temperature Monitoring & Natural Language Command Translation</p>
            <div class="demo-banner">
                🎬 Demo Mode - Simulation without EPICS Connection
            </div>
            <div class="connection-status" id="connectionStatus">Connecting...</div>
        </div>
        
        <div class="main-layout">
            <!-- Control Panel -->
            <div class="control-panel">
                <h2 class="panel-title">🎯 Natural Language Commands</h2>
                <input type="text" id="commandInput" class="command-input" 
                       placeholder="e.g., Increase plasma temperature to 10 keV for 5 seconds">
                <div>
                    <button onclick="executeCommand()" class="btn btn-primary">Execute Command</button>
                    <button onclick="startDemo()" class="btn btn-demo">🎬 Demo</button>
                </div>
                
                <div class="status-grid">
                    <div class="status-card">
                        <h3>🌡️ Current Temperature</h3>
                        <div class="status-value" id="currentTemp">--</div>
                        <div class="status-unit">keV</div>
                    </div>
                    <div class="status-card">
                        <h3>🎯 Target Temperature</h3>
                        <div class="status-value" id="targetTemp">--</div>
                        <div class="status-unit">keV</div>
                    </div>
                    <div class="status-card">
                        <h3>⚡ Coil Current</h3>
                        <div class="status-value" id="coilCurrent">--</div>
                        <div class="status-unit">A</div>
                    </div>
                    <div class="status-card">
                        <h3>🔥 Heater Power</h3>
                        <div class="status-value" id="heaterPower">--</div>
                        <div class="status-unit">%</div>
                    </div>
                </div>
                
                <h3 class="panel-title">📝 Command Translation Process</h3>
                <div class="command-conversion" id="commandConversion">
                    <div style="text-align: center; opacity: 0.7;">Command translation process will be displayed here</div>
                </div>
                
                <h3 class="panel-title">📚 Command History</h3>
                <div class="command-history" id="commandHistory">
                    <div style="text-align: center; opacity: 0.7;">Command history will be displayed here</div>
                </div>
            </div>
            
            <!-- Monitoring Panel -->
            <div class="monitoring-panel">
                <h2 class="panel-title">📊 Real-time Temperature Monitoring</h2>
                <div class="chart-container">
                    <canvas id="temperatureChart"></canvas>
                    <div class="chart-legend">
                        <div class="legend-item">
                            <div class="legend-color legend-sp"></div>
                            <span>SP (Target)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color legend-rbv"></div>
                            <span>RBV (Measured)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color legend-coil"></div>
                            <span>Coil Current</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color legend-heater"></div>
                            <span>Heater Power</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let chart = null;
        let temperatureData = [];
        let commandHistory = [];
        
        // WebSocket 연결
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                console.log('WebSocket connected');
                updateConnectionStatus(true);
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };
            
            ws.onclose = function() {
                console.log('WebSocket disconnected');
                updateConnectionStatus(false);
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
                updateConnectionStatus(false);
            };
        }
        
        function updateConnectionStatus(connected) {
            const status = document.getElementById('connectionStatus');
            if (connected) {
                status.textContent = '🟢 Connected (Demo)';
                status.className = 'connection-status connected';
            } else {
                status.textContent = '🔴 Disconnected';
                status.className = 'connection-status disconnected';
            }
        }
        
        function handleWebSocketMessage(data) {
            switch(data.type) {
                case 'continuous_update':
                    updateContinuousData(data);
                    break;
                case 'command_executed':
                    handleCommandExecuted(data.command_record);
                    break;
            }
        }
        
        function updateContinuousData(data) {
            // 온도 데이터 업데이트
            if (data.temperature_data) {
                temperatureData = data.temperature_data;
                updateChart();
            }
            
            // 현재 상태 업데이트
            if (data.current_status) {
                updateCurrentStatus(data.current_status);
            }
        }
        
        function updateCurrentStatus(status) {
            // 현재 온도
            const currentTemp = status['KSTAR:PCS:TE:RBV'];
            if (currentTemp !== null) {
                document.getElementById('currentTemp').textContent = currentTemp.toFixed(2);
            }
            
            // 목표 온도
            const targetTemp = status['KSTAR:PCS:TE:SP'];
            if (targetTemp !== null) {
                document.getElementById('targetTemp').textContent = targetTemp.toFixed(2);
            }
            
            // 코일 전류
            const coilCurrent = status['KSTAR:COIL:CURR'];
            if (coilCurrent !== null) {
                document.getElementById('coilCurrent').textContent = coilCurrent.toFixed(1);
            }
            
            // 가열 파워
            const heaterPower = status['KSTAR:HEATER:POW'];
            if (heaterPower !== null) {
                document.getElementById('heaterPower').textContent = heaterPower.toFixed(1);
            }
        }
        
        function handleCommandExecuted(commandRecord) {
            // 명령 변환 과정 표시
            showCommandConversion(commandRecord);
            
            // 명령 히스토리에 추가
            addToCommandHistory(commandRecord);
        }
        
        function showCommandConversion(commandRecord) {
            const conversionDiv = document.getElementById('commandConversion');
            
            const conversionHtml = `
                <div class="conversion-step fade-in">
                    <div class="step-header">1️⃣ Natural Language Input</div>
                    <div class="step-content">"${commandRecord.original_command}"</div>
                </div>
                
                <div class="conversion-step fade-in">
                    <div class="step-header">2️⃣ LLM Interpretation</div>
                    <div class="step-content">
                        Intent: ${commandRecord.parsed_command.intent}<br>
                        Target Value: ${commandRecord.parsed_command.target_value || 'N/A'}<br>
                        Duration: ${commandRecord.parsed_command.duration || 'N/A'} seconds
                    </div>
                </div>
                
                ${commandRecord.parsed_command.control_commands.map(cmd => `
                    <div class="conversion-step set-command fade-in">
                        <div class="step-header">3️⃣ EPICS SET Command</div>
                        <div class="step-content">
                            SET <span class="pv-name">${cmd.pv_name}</span> = 
                            <span class="pv-value">${cmd.value}</span> 
                            <span class="pv-unit">${cmd.unit}</span><br>
                            <small>${cmd.description}</small>
                        </div>
                    </div>
                `).join('')}
                
                <div class="conversion-step fade-in">
                    <div class="step-header">4️⃣ Execution Results</div>
                    <div class="step-content">
                        ${commandRecord.results.map(result => `
                            <span class="pv-name">${result.pv_name}</span>: 
                            ${result.old_value} → <span class="pv-value">${result.new_value}</span> 
                            <span class="pv-unit">${result.unit}</span>
                            <span style="color: ${result.success ? '#22c55e' : '#ef4444'}">
                                ${result.success ? '✅' : '❌'}
                            </span><br>
                        `).join('')}
                    </div>
                </div>
            `;
            
            conversionDiv.innerHTML = conversionHtml;
        }
        
        function addToCommandHistory(commandRecord) {
            const historyDiv = document.getElementById('commandHistory');
            
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item fade-in';
            
            const timestamp = new Date(commandRecord.timestamp).toLocaleTimeString();
            
            historyItem.innerHTML = `
                <div class="history-timestamp">${timestamp}</div>
                <div class="history-command">"${commandRecord.original_command}"</div>
                <div class="history-result">
                    ${commandRecord.parsed_command.control_commands.map(cmd => 
                        `SET ${cmd.pv_name} = ${cmd.value} ${cmd.unit}`
                    ).join('<br>')}
                </div>
            `;
            
            historyDiv.insertBefore(historyItem, historyDiv.firstChild);
            
            // 최대 10개 항목 유지
            while (historyDiv.children.length > 10) {
                historyDiv.removeChild(historyDiv.lastChild);
            }
        }
        
        function updateChart() {
            const canvas = document.getElementById('temperatureChart');
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            const width = canvas.width = canvas.clientWidth;
            const height = canvas.height = canvas.clientHeight;
            
            // 배경 클리어
            ctx.clearRect(0, 0, width, height);
            
            if (temperatureData.length < 2) return;
            
            // 그리드 그리기
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
            ctx.lineWidth = 1;
            
            // 수평 그리드
            for (let i = 0; i <= 6; i++) {
                const y = (height / 6) * i;
                ctx.beginPath();
                ctx.moveTo(40, y);
                ctx.lineTo(width - 20, y);
                ctx.stroke();
            }
            
            // Y축 레이블
            ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
            ctx.font = '12px Arial';
            ctx.textAlign = 'right';
            for (let i = 0; i <= 6; i++) {
                const value = 30 - (i * 5);
                const y = (height / 6) * i + 5;
                ctx.fillText(value.toString(), 35, y);
            }
            
            // 좌표 변환 함수
            const toX = (index) => 40 + (index / (temperatureData.length - 1)) * (width - 60);
            const toY = (value) => height - 20 - ((value / 30) * (height - 40));
            
            // 데이터 포인트 그리기
            const colors = {
                sp: '#2563eb',
                rbv: '#f59e0b',
                coil: '#8b5cf6',
                heater: '#ef4444'
            };
            
            // 라인 그리기
            ['sp', 'rbv', 'coil', 'heater'].forEach((key, keyIndex) => {
                const points = [];
                
                temperatureData.forEach((point, index) => {
                    let value = null;
                    switch(key) {
                        case 'sp': value = point.sp; break;
                        case 'rbv': value = point.rbv; break;
                        case 'coil': value = point.coil_current; break;
                        case 'heater': value = point.heater_power; break;
                    }
                    
                    if (value !== null) {
                        points.push({x: toX(index), y: toY(value)});
                    }
                });
                
                if (points.length > 1) {
                    ctx.strokeStyle = colors[key];
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    points.forEach((point, index) => {
                        if (index === 0) ctx.moveTo(point.x, point.y);
                        else ctx.lineTo(point.x, point.y);
                    });
                    ctx.stroke();
                }
                
                // 데이터 포인트 그리기
                ctx.fillStyle = colors[key];
                points.forEach(point => {
                    ctx.beginPath();
                    ctx.arc(point.x, point.y, 2, 0, 2 * Math.PI);
                    ctx.fill();
                });
            });
        }
        
        async function executeCommand() {
            const input = document.getElementById('commandInput');
            const command = input.value.trim();
            
            if (!command) {
                alert('Please enter a command.');
                return;
            }
            
            try {
                const response = await fetch('/command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ command: command })
                });
                
                const result = await response.json();
                console.log('Command execution result:', result);
                
                input.value = '';
            } catch (error) {
                console.error('Command execution error:', error);
                alert('An error occurred while executing the command.');
            }
        }
        
        function startDemo() {
            const demoCommands = [
                "Increase plasma temperature to 10 keV",
                "Set temperature to 12 keV for 3 seconds",
                "Increase heater power to 80%",
                "Lower temperature to 6 keV"
            ];
            
            let index = 0;
            const interval = setInterval(() => {
                if (index < demoCommands.length) {
                    document.getElementById('commandInput').value = demoCommands[index];
                    executeCommand();
                    index++;
                } else {
                    clearInterval(interval);
                }
            }, 8000);
        }
        
        // 키보드 이벤트
        document.getElementById('commandInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                executeCommand();
            }
        });
        
        // 페이지 로드 시 초기화
        window.addEventListener('load', function() {
            connectWebSocket();
            updateChart();
        });
        
        // 윈도우 리사이즈 시 차트 업데이트
        window.addEventListener('resize', updateChart);
    </script>
</body>
</html>
        """
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the demo mode server
        
        Args:
            host: Server host address
            port: Server port number
        """
        print(f"🚀 KSTAR MCP PoC v2 Demo Mode Server Starting...")
        print(f"🌐 Web UI: http://{host}:{port}")
        print(f"📡 WebSocket: ws://{host}:{port}/ws")
        print(f"🎬 Demo Mode: Simulation without EPICS connection")
        
        uvicorn.run(self.app, host=host, port=port, log_level="info")


# Main execution function
def main():
    """Main execution function for standalone operation"""
    ui = DemoModeUI()
    ui.run()


if __name__ == "__main__":
    main()
