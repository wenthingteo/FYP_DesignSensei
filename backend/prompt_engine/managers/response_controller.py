# prompt_engine/managers/response_controller.py

from typing import Dict
from enum import Enum
from prompt_engine.templates.base_template import UserExpertise, ResponseLength

class ResponseController:
    """Controls response length and complexity based on user needs"""
    
    def __init__(self):
        self.complexity_rules = {
            UserExpertise.BEGINNER: {
                'max_concepts_per_response': 3,
                'include_code_examples': False,
                'technical_depth': 'basic',
                'analogies_preferred': True
            },
            UserExpertise.INTERMEDIATE: {
                'max_concepts_per_response': 5,
                'include_code_examples': True,
                'technical_depth': 'moderate',
                'analogies_preferred': False
            },
            UserExpertise.ADVANCED: {
                'max_concepts_per_response': 8,
                'include_code_examples': True,
                'technical_depth': 'deep',
                'analogies_preferred': False
            }
        }
        
        self.length_rules = {
            ResponseLength.SHORT: {
                'max_tokens': 300,
                'max_examples': 1,
                'include_followup': False
            },
            ResponseLength.MEDIUM: {
                'max_tokens': 800,
                'max_examples': 2,
                'include_followup': True
            },
            ResponseLength.DETAILED: {
                'max_tokens': 1500,
                'max_examples': 3,
                'include_followup': True
            }
        }

    def get_response_parameters(self, 
                               user_expertise: UserExpertise, 
                               response_length: ResponseLength,
                               question_complexity: float, # 0.0 (simple) to 1.0 (complex)
                               conversation_length: int = 0) -> Dict: # <-- ADDED THIS PARAMETER WITH DEFAULT
        """
        Determines dynamic response parameters based on user expertise, desired length,
        and question complexity.
        """
        complexity_params = self.complexity_rules.get(user_expertise, self.complexity_rules[UserExpertise.INTERMEDIATE]).copy()
        length_params = self.length_rules.get(response_length, self.length_rules[ResponseLength.MEDIUM]).copy()
        
        # Adjust max_concepts and max_tokens based on question complexity
        if question_complexity > 0.7:  # High complexity question
            complexity_params['max_concepts_per_response'] += 1
            length_params['max_tokens'] = int(length_params['max_tokens'] * 1.2)
        elif question_complexity < 0.3:  # Simple question
            complexity_params['max_concepts_per_response'] = max(1, 
                complexity_params['max_concepts_per_response'] - 1)
            length_params['max_tokens'] = int(length_params['max_tokens'] * 0.8)
        
        # Adjust follow-up inclusion based on conversation length and expertise
        length_params['include_followup'] = self.should_include_followup(
            user_expertise, response_length, conversation_length
        )

        return {
            **complexity_params,
            **length_params,
            'question_complexity': question_complexity
        }
    
    def should_include_followup(self, 
                               user_expertise: UserExpertise,
                               response_length: ResponseLength,
                               conversation_length: int) -> bool:
        """Determine if follow-up questions should be included"""
        
        # Don't include follow-up for short responses
        if response_length == ResponseLength.SHORT:
            return False
        
        # Include follow-up for beginners to encourage learning
        if user_expertise == UserExpertise.BEGINNER:
            return True
        
        # Include follow-up if conversation is short (< 3 exchanges)
        if conversation_length < 6:  # 6 messages = 3 exchanges (user + bot)
            return True
        
        return response_length == ResponseLength.DETAILED # Always include for detailed
