# prompt_engine/utils.py
"""
Utility functions for the prompt engine module
"""
import re
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class PromptUtils:
    """Utilities for prompt processing and manipulation"""
    
    @staticmethod
    def clean_prompt(prompt: str) -> str:
        """Clean and normalize prompt text"""
        if not prompt:
            return ""
        
        # Remove extra whitespace and normalize line breaks
        cleaned = re.sub(r'\s+', ' ', prompt.strip())
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        
        return cleaned
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """Extract important keywords from text"""
        if not text:
            return []
        
        # Simple keyword extraction - you might want to use NLP libraries
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 
            'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day',
            'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new',
            'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did',
            'man', 'men', 'put', 'say', 'she', 'too', 'use'
        }
        
        keywords = [word for word in words if word not in stop_words]
        return list(set(keywords))  # Remove duplicates
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 500, ellipsis: str = "...") -> str:
        """Truncate text to specified length with ellipsis"""
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(ellipsis)] + ellipsis
    
    @staticmethod
    def format_code_snippet(code: str, language: str = "python") -> str:
        """Format code snippet for display"""
        if not code:
            return ""
        
        return f"```{language}\n{code.strip()}\n```"
    
    @staticmethod
    def extract_topics(text: str) -> List[str]:
        """Extract software design topics from text"""
        topics = []
        
        # Common software design patterns and concepts
        design_patterns = [
            'singleton', 'factory', 'observer', 'strategy', 'decorator',
            'adapter', 'facade', 'command', 'template method', 'mvc',
            'mvp', 'mvvm', 'repository', 'dependency injection'
        ]
        
        principles = [
            'solid', 'dry', 'kiss', 'yagni', 'separation of concerns',
            'single responsibility', 'open closed', 'liskov substitution',
            'interface segregation', 'dependency inversion'
        ]
        
        all_concepts = design_patterns + principles
        text_lower = text.lower()
        
        for concept in all_concepts:
            if concept in text_lower:
                topics.append(concept)
        
        return topics

class ValidationUtils:
    """Utilities for validating inputs and data"""
    
    @staticmethod
    def validate_prompt_input(prompt: str, min_length: int = 1, max_length: int = 5000) -> bool:
        """Validate prompt input"""
        if not isinstance(prompt, str):
            return False
        
        if len(prompt.strip()) < min_length:
            return False
        
        if len(prompt) > max_length:
            return False
        
        return True
    
    @staticmethod
    def validate_intent(intent: str) -> bool:
        """Validate intent classification"""
        valid_intents = {
            'explanation', 'comparison', 'application', 'analysis',
            'example', 'definition', 'troubleshooting', 'best_practices'
        }
        
        return intent.lower() in valid_intents
    
    @staticmethod
    def validate_context(context: Dict[str, Any]) -> bool:
        """Validate context data structure"""
        if not isinstance(context, dict):
            return False
        
        required_keys = ['topic', 'difficulty_level', 'user_background']
        
        for key in required_keys:
            if key not in context:
                return False
        
        return True
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        if not text:
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', text)
        
        # Limit length
        sanitized = sanitized[:1000]
        
        return sanitized.strip()

class FormatUtils:
    """Utilities for formatting responses and content"""
    
    @staticmethod
    def format_explanation(title: str, content: str, examples: List[str] = None) -> str:
        """Format explanation response"""
        formatted = f"## {title}\n\n{content}\n\n"
        
        if examples:
            formatted += "### Examples:\n\n"
            for i, example in enumerate(examples, 1):
                formatted += f"{i}. {example}\n\n"
        
        return formatted
    
    @staticmethod
    def format_comparison(item1: str, item2: str, differences: List[str]) -> str:
        """Format comparison response"""
        formatted = f"## Comparison: {item1} vs {item2}\n\n"
        
        for diff in differences:
            formatted += f"• {diff}\n"
        
        return formatted + "\n"
    
    @staticmethod
    def format_code_example(title: str, code: str, explanation: str, language: str = "python") -> str:
        """Format code example with explanation"""
        formatted = f"## {title}\n\n"
        formatted += f"```{language}\n{code}\n```\n\n"
        formatted += f"**Explanation:** {explanation}\n\n"
        
        return formatted
    
    @staticmethod
    def format_learning_objective(objective: str, topics: List[str]) -> str:
        """Format learning objective with related topics"""
        formatted = f"**Learning Objective:** {objective}\n\n"
        
        if topics:
            formatted += "**Related Topics:**\n"
            for topic in topics:
                formatted += f"• {topic}\n"
            formatted += "\n"
        
        return formatted
    
    @staticmethod
    def add_timestamp(content: str) -> str:
        """Add timestamp to content"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{content}\n\n*Generated on: {timestamp}*"

class LoggingUtils:
    """Utilities for logging and debugging"""
    
    @staticmethod
    def log_prompt_processing(prompt: str, intent: str, response_time: float):
        """Log prompt processing details"""
        logger.info(f"Processed prompt - Intent: {intent}, Response time: {response_time:.2f}s")
        logger.debug(f"Prompt preview: {prompt[:100]}...")
    
    @staticmethod
    def log_error(error: Exception, context: str = ""):
        """Log error with context"""
        logger.error(f"Error in {context}: {str(error)}", exc_info=True)
    
    @staticmethod
    def log_performance_metrics(metrics: Dict[str, Any]):
        """Log performance metrics"""
        logger.info(f"Performance metrics: {json.dumps(metrics, indent=2)}")

# Configuration constants
DEFAULT_CONFIG = {
    'max_prompt_length': 5000,
    'max_response_length': 10000,
    'default_difficulty': 'intermediate',
    'supported_languages': ['python', 'java', 'javascript', 'csharp', 'cpp'],
    'cache_ttl': 3600,  # 1 hour
    'max_context_history': 10
}