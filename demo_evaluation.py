#!/usr/bin/env python3
"""
Demo script for the evaluation framework
"""

import asyncio
from evaluate_agent import AgentEvaluator

async def demo():
    """Demonstrate the evaluation framework"""
    print("🚀 Pipecat Voice Agent Evaluation Demo")
    print("=" * 50)
    
    evaluator = AgentEvaluator()
    
    print(f"📋 Available test scenarios: {len(evaluator.scenarios)}")
    
    # Show the scenarios
    for i, scenario in enumerate(evaluator.scenarios, 1):
        print(f"{i:2d}. {scenario.name} ({scenario.complexity})")
        print(f"    Input: '{scenario.user_input}'")
        print(f"    Expected: {scenario.expected_intent} -> {scenario.expected_response_type}")
        print()
    
    print("💡 To run full evaluation:")
    print("   python evaluate_agent.py --agent both --scenarios all")
    print()
    print("💡 To test specific agent:")
    print("   python evaluate_agent.py --agent baml")
    print("   python evaluate_agent.py --agent vanilla")
    print()
    print("💡 To test specific complexity:")
    print("   python evaluate_agent.py --scenarios simple")
    print("   python evaluate_agent.py --scenarios medium")
    print("   python evaluate_agent.py --scenarios complex")

if __name__ == "__main__":
    asyncio.run(demo())
