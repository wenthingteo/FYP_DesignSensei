from typing import List, Dict, Optional
import logging
from prompt_engine.templates.base_template import BaseTemplate, UserExpertise, ResponseLength
from prompt_engine.templates.explanation_template import ExplanationTemplate
from prompt_engine.templates.comparison_template import ComparisonTemplate
from prompt_engine.templates.application_template import ApplicationTemplate
from prompt_engine.templates.analysis_template import AnalysisTemplate

# Configure logging
logger = logging.getLogger(__name__)

class TemplateFactory:
    """Factory to create appropriate templates based on question type"""
    
    # Enhanced template registry with aliases and descriptions
    _templates = {
        # Primary templates
        'explanation': {
            'class': ExplanationTemplate,
            'description': 'For explaining concepts, principles, and patterns',
            'aliases': ['explain', 'what', 'define', 'describe', 'tell']
        },
        'comparison': {
            'class': ComparisonTemplate,
            'description': 'For comparing different approaches, patterns, or principles',
            'aliases': ['compare', 'vs', 'versus', 'difference', 'differences', 'better']
        },
        'application': {
            'class': ApplicationTemplate,
            'description': 'For implementation guidance and how-to questions',
            'aliases': ['implement', 'how', 'apply', 'use', 'build', 'create', 'make']
        },
        'analysis': {
            'class': AnalysisTemplate,
            'description': 'For analyzing code, evaluating designs, and troubleshooting',
            'aliases': ['analyze', 'evaluate', 'review', 'assess', 'troubleshoot', 'debug', 'fix', 'problem']
        }
    }
    
    @classmethod
    def create_template(cls, question_type: str) -> BaseTemplate:
        """
        Create appropriate template based on question type with improved error handling
        
        Args:
            question_type: The type of question/template needed
            
        Returns:
            BaseTemplate: Instance of the appropriate template
            
        Raises:
            ValueError: If question_type is None or empty
        """
        if not question_type:
            logger.warning("Empty or None question_type provided, defaulting to explanation")
            return ExplanationTemplate()
        
        question_type = question_type.lower().strip()
        
        # Direct match
        if question_type in cls._templates:
            template_class = cls._templates[question_type]['class']
            logger.debug(f"Created template: {template_class.__name__} for type: {question_type}")
            return template_class()
        
        # Check aliases
        for template_key, template_info in cls._templates.items():
            if question_type in template_info['aliases']:
                template_class = template_info['class']
                logger.debug(f"Created template: {template_class.__name__} for alias: {question_type}")
                return template_class()
        
        # Fallback to explanation template with warning
        logger.warning(f"Unknown question type '{question_type}', defaulting to ExplanationTemplate")
        return ExplanationTemplate()
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """Get list of available template types"""
        return list(cls._templates.keys())
    
    @classmethod
    def get_all_aliases(cls) -> Dict[str, List[str]]:
        """Get all available aliases for each template type"""
        return {
            template_type: template_info['aliases'] 
            for template_type, template_info in cls._templates.items()
        }
    
    @classmethod
    def get_template_info(cls, question_type: Optional[str] = None) -> Dict:
        """
        Get information about templates
        
        Args:
            question_type: Specific template type to get info for, or None for all
            
        Returns:
            Dict: Template information
        """
        if question_type:
            question_type = question_type.lower().strip()
            if question_type in cls._templates:
                return {question_type: cls._templates[question_type]}
            else:
                logger.warning(f"Template type '{question_type}' not found")
                return {}
        
        return {
            template_type: {
                'description': template_info['description'],
                'aliases': template_info['aliases']
            }
            for template_type, template_info in cls._templates.items()
        }
    
    @classmethod
    def suggest_template_type(cls, user_query: str) -> str:
        """
        Suggest the most appropriate template type based on user query keywords
        
        Args:
            user_query: The user's question/query
            
        Returns:
            str: Suggested template type
        """
        if not user_query:
            logger.warning("Empty user query, defaulting to explanation template")
            return 'explanation'
        
        query_lower = user_query.lower()
        
        # Enhanced keyword mapping for better detection
        keyword_mapping = {
            'explanation': ['what', 'explain', 'define', 'describe', 'tell me about', 'how does', 'concept'],
            'comparison': ['vs', 'versus', 'compare', 'difference', 'better', 'choose between', 'which', 'pros and cons'],
            'application': ['how to', 'implement', 'build', 'create', 'apply', 'use', 'make', 'step by step'],
            'analysis': ['analyze', 'evaluate', 'review', 'assess', 'wrong', 'problem', 'issue', 'fix', 'debug', 'troubleshoot']
        }
        
        # Score each template type based on keyword matches
        scores = {}
        for template_type, keywords in keyword_mapping.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                scores[template_type] = score
        
        if scores:
            # Return the template type with the highest score
            suggested_type = max(scores, key=scores.get)
            logger.debug(f"Suggested template type '{suggested_type}' for query: '{user_query[:50]}...'")
            return suggested_type
        
        # Default to explanation if no clear indicators
        logger.debug(f"No clear template type indicators found, defaulting to 'explanation' for query: '{user_query[:50]}...'")
        return 'explanation'
    
    @classmethod
    def validate_template_type(cls, question_type: str) -> bool:
        """
        Validate if a template type exists (including aliases)
        
        Args:
            question_type: Template type to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not question_type:
            return False
        
        question_type = question_type.lower().strip()
        
        # Check direct match
        if question_type in cls._templates:
            return True
        
        # Check aliases
        for template_info in cls._templates.values():
            if question_type in template_info['aliases']:
                return True
        
        return False


# Enhanced example usage and testing
if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example GraphRAG results
    sample_results = {
        'results': [
            {
                'node_id': 'n_963250f1',
                'name': 'Polymorphic Open/Closed Principle',
                'label': 'DesignPrinciple',
                'description': 'A principle that states software entities should be open for extension but closed for modification.',
                'source': '12-design-principles.pdf',
                'page': 15,
                'relevance_score': 0.9,
                'relationships': [
                    {'related_node': 'Inheritance', 'relationship_type': 'IMPLEMENTS'}
                ]
            }
        ]
    }
    
    # Enhanced test cases
    test_cases = [
        ("explanation", "What is the Open/Closed Principle?"),
        ("compare", "Factory Pattern vs Builder Pattern"),
        ("how", "How to implement Singleton pattern?"),
        ("analyze", "Is this code following SOLID principles?"),
        ("debug", "Why is my factory pattern not working?"),
        ("invalid_type", "Some random question"),
        ("", "Empty template type test"),
        (None, "None template type test")
    ]
    
    print("Enhanced Template Factory Testing")
    print("=" * 60)
    
    # Test template creation and validation
    for template_type, query in test_cases:
        print(f"\n{'='*40}")
        print(f"Testing template type: '{template_type}'")
        print(f"Query: '{query}'")
        
        # Test validation
        is_valid = TemplateFactory.validate_template_type(template_type) if template_type else False
        print(f"Valid template type: {is_valid}")
        
        # Test template creation
        try:
            template = TemplateFactory.create_template(template_type)
            print(f"Created: {template.__class__.__name__}")
        except Exception as e:
            print(f"Error creating template: {e}")
        
        # Test template suggestion
        suggested = TemplateFactory.suggest_template_type(query)
        print(f"Suggested type: {suggested}")
    
    # Display factory information
    print(f"\n{'='*60}")
    print("Template Factory Information:")
    print("=" * 60)
    
    print(f"\nAvailable template types: {TemplateFactory.get_available_types()}")
    print(f"\nAll aliases: {TemplateFactory.get_all_aliases()}")
    
    # Show template info
    print(f"\nTemplate Information:")
    template_info = TemplateFactory.get_template_info()
    for template_type, info in template_info.items():
        print(f"\n{template_type.upper()}:")
        print(f"  Description: {info['description']}")
        print(f"  Aliases: {', '.join(info['aliases'])}")
    
    # Generate a sample prompt
    print(f"\n{'='*60}")
    print("Sample Prompt Generation:")
    print("=" * 60)
    
    try:
        template = TemplateFactory.create_template('explanation')
        prompt = template.generate_prompt(
            user_query="What is the Open/Closed Principle?",
            graphrag_results=sample_results,
            context={},
            user_expertise=UserExpertise.INTERMEDIATE,
            response_length=ResponseLength.MEDIUM
        )
        
        print("\nGenerated Prompt:")
        print("-" * 50)
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        
    except Exception as e:
        print(f"Error generating prompt: {e}")