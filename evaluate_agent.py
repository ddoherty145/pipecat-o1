import asyncio
import csv
from baml_agent import main as baml_main
from vanilla_agent import main as vanilla_main

async def run_evaluation():
    test_scenarios = [
        "I need help with my account",
        "My order hasn't arrived",
        "I want to cancel my subscription",
        "There's a charge I don't recognize",
        "How do I update my payment method?"
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios):
        print(f"Testing scenario {i+1}: {scenario}")
        
        # Test BAML agent
        baml_metrics = await run_agent_test(baml_main, scenario, f"baml_scenario_{i+1}")
        
        # Test Vanilla agent  
        vanilla_metrics = await run_agent_test(vanilla_main, scenario, f"vanilla_scenario_{i+1}")
        
        results.append({
            "scenario": scenario,
            "baml_latency": baml_metrics["avg_latency_ms"],
            "vanilla_latency": vanilla_metrics["avg_latency_ms"],
            "baml_accuracy": baml_metrics["turn_accuracy_rate"],
            "vanilla_accuracy": vanilla_metrics["turn_accuracy_rate"]
        })
    
    # Save results to CSV
    with open('evaluation/metrics.csv', 'w', newline='') as csvfile:
        fieldnames = ['scenario', 'baml_latency', 'vanilla_latency', 'baml_accuracy', 'vanilla_accuracy']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)