#!/usr/bin/env python3
"""
KSTAR MCP PoC v2 - System Test Script

This script provides comprehensive testing capabilities for the KSTAR MCP PoC v2
system. It can test individual components or the entire system to ensure
proper functionality before deployment.

Key Features:
- Individual component testing
- Full system integration testing
- Command parser validation
- EPICS controller testing
- Execution engine testing

This is designed to help developers and users verify that the system
is working correctly before using it for actual plasma control.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.llm.command_parser import CommandParser, test_command_parser
from src.epics.controller import EPICSController, test_epics_controller
from src.core.execution_engine import CommandExecutionEngine, test_execution_engine


async def test_full_system():
    """Test the complete KSTAR MCP PoC v2 system
    
    This function runs comprehensive tests on all major components
    to ensure the system is working correctly.
    """
    print("🧪 KSTAR MCP PoC v2 Full System Test")
    print("=" * 50)
    
    # 1. Command parser test
    print("\n1️⃣ Command Parser Test")
    print("-" * 30)
    test_command_parser()
    
    # 2. EPICS controller test
    print("\n2️⃣ EPICS Controller Test")
    print("-" * 30)
    test_epics_controller()
    
    # 3. Execution engine test
    print("\n3️⃣ Execution Engine Test")
    print("-" * 30)
    await test_execution_engine()
    
    print("\n✅ All tests completed!")


def test_individual_components():
    """Test individual system components
    
    This function provides focused testing of specific components
    for debugging and development purposes.
    """
    print("🔧 Individual Component Test")
    print("=" * 30)
    
    # Test command parser only
    parser = CommandParser()
    test_commands = [
        "Raise plasma temperature to 10 keV for 5 seconds",
        "Set temperature to 12 keV",
        "Adjust density to 3e19"
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


def main():
    """Main test function with command line interface
    
    This function provides a command-line interface for running
    different types of tests on the KSTAR MCP PoC v2 system.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="KSTAR MCP PoC v2 Test Suite")
    parser.add_argument("--component", choices=["parser", "epics", "engine", "all"], 
                       default="all", help="Select component to test")
    
    args = parser.parse_args()
    
    if args.component == "parser":
        test_command_parser()
    elif args.component == "epics":
        test_epics_controller()
    elif args.component == "engine":
        asyncio.run(test_execution_engine())
    elif args.component == "all":
        asyncio.run(test_full_system())
    
    print("\n🎉 Testing completed!")


if __name__ == "__main__":
    main()
