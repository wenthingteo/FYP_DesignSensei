# prompt_engine/templates/__init__.py
"""
Template classes for generating different types of educational content
"""
from backend.prompt_engine.templates.base_template import BaseTemplate
from backend.prompt_engine.templates.explanation_template import ExplanationTemplate
from backend.prompt_engine.templates.comparison_template import ComparisonTemplate
from backend.prompt_engine.templates.application_template import ApplicationTemplate
from backend.prompt_engine.templates.analysis_template import AnalysisTemplate

__all__ = [
    "BaseTemplate",
    "ExplanationTemplate",
    "ComparisonTemplate", 
    "ApplicationTemplate",
    "AnalysisTemplate"
]
