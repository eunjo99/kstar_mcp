#!/usr/bin/env python3
"""
Natural Language Command Parser - LLM-based EPICS command translation

This module provides the core functionality for translating natural language
commands into structured EPICS control commands. It uses OpenAI's language
models to understand user intent and generate appropriate control sequences.

Key Features:
- Natural language to EPICS command translation
- Support for temperature, density, and heating control
- Safety limit validation
- Demo mode with rule-based parsing
- Integration with OpenAI GPT models

This PoC demonstrates a simple approach where target values are set and
current values gradually follow. Future versions will integrate with
sophisticated plasma physics models and machine learning algorithms.
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

# Load .env file
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)


@dataclass
class ControlCommand:
    """EPICS control command data class"""
    pv_name: str
    value: float
    unit: str
    description: str
    priority: int = 1  # 1=high, 2=medium, 3=low


@dataclass
class ParsedCommand:
    """Parsed natural language command"""
    original_command: str
    intent: str  # "temperature_control", "density_control", "heating_control", etc.
    target_value: Optional[float]
    duration: Optional[float]  # seconds
    control_commands: List[ControlCommand]
    safety_checks: List[str]
    estimated_time: float  # estimated execution time (seconds)


class CommandParser:
    """Natural language command parser
    
    This class handles the translation of natural language commands into
    structured EPICS control commands. It supports both LLM-based parsing
    and fallback rule-based parsing for demo mode.
    """
    
    def __init__(self):
        # Initialize OpenAI client (with demo mode support)
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self._client = OpenAI(api_key=api_key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            self.demo_mode = False
        else:
            self._client = None
            self.model = None
            self.demo_mode = True
            print("⚠️  OpenAI API key not found. Running in demo mode.")
        
        # KSTAR control mapping table
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
        """Return OpenAI client"""
        return self._client
    
    def parse_command(self, command: str) -> ParsedCommand:
        """Parse natural language command into structured control commands
        
        Args:
            command: Natural language command string
            
        Returns:
            ParsedCommand object with control instructions
        """
        
        # Use simple rule-based parsing in demo mode
        if self.demo_mode:
            return self._demo_parse_command(command)
        
        # Step 1: Try quick pattern matching for fast parsing
        quick_parse = self._quick_parse(command)
        if quick_parse:
            return quick_parse
        
        # Step 2: Use LLM for advanced parsing
        return self._llm_parse(command)
    
    def _demo_parse_command(self, command: str) -> ParsedCommand:
        """Demo mode simple rule-based parsing
        
        This method provides basic command parsing for demo mode when
        OpenAI API is not available. It uses regex patterns to extract
        temperature values and generate control commands.
        """
        
        # Extract temperature-related keywords and numbers
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
        
        # Calculate coil current and heater power based on temperature
        base_current = 1200
        base_power = 50
        temp_diff = target_temp - 8.0  # Reference temperature 8keV
        
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
        """Quick parsing using basic regex patterns
        
        Args:
            command: Natural language command string
            
        Returns:
            ParsedCommand if pattern matches, None otherwise
        """
        
        # Temperature control patterns
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
                
                # Generate temperature control commands
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
        """Advanced command parsing using LLM
        
        Args:
            command: Natural language command string
            
        Returns:
            ParsedCommand object with LLM-generated control instructions
        """
        
        system_prompt = """
You are an expert in KSTAR plasma control systems.
Analyze natural language commands and convert them to EPICS control commands.

Available control devices:
- Coil current (COIL:CURR): 0-2000A, used for temperature control
- Heater power (HEATER:POW): 0-100%, used for temperature control
- Gas injection (GAS:FLOW): 0-1000sccm, used for density control
- Magnetic field (MAGNET:BT): 0-3.5T, used for plasma stabilization

Response format:
{
    "intent": "temperature_control|density_control|heating_control|combined_control",
    "target_value": numeric_value,
    "duration": time_in_seconds,
    "control_commands": [
        {
            "pv_name": "PV_name",
            "value": numeric_value,
            "unit": "unit",
            "description": "description",
            "priority": 1
        }
    ],
    "safety_checks": ["check1", "check2"],
    "estimated_time": estimated_execution_time
}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please analyze this command: {command}"}
                ],
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Convert to ControlCommand objects
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
            print(f"LLM parsing error: {e}")
            # Fallback to basic parsing
            return self._create_fallback_command(command)
    
    def _extract_duration(self, command: str) -> Optional[float]:
        """Extract time information from command
        
        Args:
            command: Natural language command string
            
        Returns:
            Duration in seconds or None if not found
        """
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
        """Generate EPICS commands for temperature control
        
        Args:
            target_temp: Target temperature in keV
            
        Returns:
            List of ControlCommand objects
        """
        commands = []
        
        # Assume current temperature (should read from EPICS in practice)
        current_temp = 8.0  # keV
        
        if target_temp > current_temp:
            # Temperature increase: increase coil current and heater power
            temp_diff = target_temp - current_temp
            
            # Calculate coil current (empirical formula)
            coil_current = min(1500 + temp_diff * 100, 2000)
            commands.append(ControlCommand(
                pv_name="KSTAR:COIL:CURR",
                value=coil_current,
                unit="A",
                description=f"Temperature control via coil current for {target_temp} keV",
                priority=1
            ))
            
            # Calculate heater power
            heater_power = min(70 + temp_diff * 5, 100)
            commands.append(ControlCommand(
                pv_name="KSTAR:HEATER:POW",
                value=heater_power,
                unit="%",
                description=f"Temperature control via heater power for {target_temp} keV",
                priority=1
            ))
        
        elif target_temp < current_temp:
            # Temperature decrease: decrease coil current and heater power
            temp_diff = current_temp - target_temp
            
            coil_current = max(1000 - temp_diff * 50, 500)
            commands.append(ControlCommand(
                pv_name="KSTAR:COIL:CURR",
                value=coil_current,
                unit="A",
                description=f"Temperature control via coil current reduction for {target_temp} keV",
                priority=1
            ))
            
            heater_power = max(30 - temp_diff * 3, 10)
            commands.append(ControlCommand(
                pv_name="KSTAR:HEATER:POW",
                value=heater_power,
                unit="%",
                description=f"Temperature control via heater power reduction for {target_temp} keV",
                priority=1
            ))
        
        return commands
    
    def _create_fallback_command(self, command: str) -> ParsedCommand:
        """Create fallback command when parsing fails
        
        Args:
            command: Original command string
            
        Returns:
            Basic ParsedCommand object
        """
        return ParsedCommand(
            original_command=command,
            intent="unknown",
            target_value=None,
            duration=None,
            control_commands=[],
            safety_checks=["manual_review"],
            estimated_time=5.0
        )


# Test function
def test_command_parser():
    """Test command parser functionality"""
    parser = CommandParser()
    
    test_commands = [
        "Raise plasma temperature to 10 keV for 5 seconds",
        "Set temperature to 12 keV",
        "Adjust density to 3e19",
        "Increase heater power to 80%"
    ]
    
    for cmd in test_commands:
        print(f"\nCommand: {cmd}")
        result = parser.parse_command(cmd)
        print(f"Intent: {result.intent}")
        print(f"Target value: {result.target_value}")
        print(f"Duration: {result.duration} seconds")
        print(f"Control commands: {len(result.control_commands)}")
        for cmd_obj in result.control_commands:
            print(f"  - {cmd_obj.pv_name} = {cmd_obj.value} {cmd_obj.unit}")


if __name__ == "__main__":
    test_command_parser()
