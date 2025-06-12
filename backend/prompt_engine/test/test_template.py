#========================================================
# tests/test_templates.py
"""
Test file for prompt templates using mock data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_engine.templates.explanation_template import ExplanationTemplate
from prompt_engine.templates.comparison_template import ComparisonTemplate
from prompt_engine.test.mock_graph_results import get_mock_search_results

def test_explanation_template():
    """Test explanation template with mock data"""
    print("=== Testing Explanation Template ===")
    
    template = ExplanationTemplate(user_level="intermediate")
    
    query = "What is the MVC pattern?"
    search_results = get_mock_search_results("mvc_pattern")
    context = {
        "user_background": "Has 2 years Java experience",
        "learning_objectives": "Understand architectural patterns",
        "conversation_history": ["Previously asked about design patterns"]
    }
    
    prompt = template.generate_prompt(query, search_results, context)
    
    print("Generated Prompt:")
    print("-" * 50)
    print(prompt)
    print("-" * 50)
    print()

def test_comparison_template():
    """Test comparison template with mock data"""
    print("=== Testing Comparison Template ===")
    
    template = ComparisonTemplate(user_level="advanced")
    
    query = "What's the difference between Factory and Builder patterns?"
    search_results = get_mock_search_results("factory_vs_builder")
    context = {
        "user_background": "Senior developer",
        "learning_objectives": "Master creational patterns"
    }
    
    prompt = template.generate_prompt(query, search_results, context)
    
    print("Generated Prompt:")
    print("-" * 50)
    print(prompt)
    print("-" * 50)
    print()

def test_different_user_levels():
    """Test how templates adapt to different user levels"""
    print("=== Testing Different User Levels ===")
    
    query = "Explain SOLID principles"
    search_results = get_mock_search_results("solid_principles")
    context = {"user_background": "New to design patterns"}
    
    for level in ["beginner", "intermediate", "advanced"]:
        print(f"\n--- {level.upper()} LEVEL ---")
        template = ExplanationTemplate(user_level=level)
        prompt = template.generate_prompt(query, search_results, context)
        
        # Show just the complexity instruction part
        lines = prompt.split('\n')
        for line in lines:
            if "Use simple language" in line or "Provide detailed" in line or "Include technical" in line:
                print(f"Complexity instruction: {line}")
                break

if __name__ == "__main__":
    test_explanation_template()
    test_comparison_template() 
    test_different_user_levels()