"""
Manager Classes for Prompt Engineering Module
"""
import json
import openai
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from prompt_engine.templates.base_template import UserExpertise, ResponseLength
from prompt_engine.templates.template_factory import TemplateFactory
from prompt_engine.intent_classifier import IntentClassifier
from prompt_engine.managers.context_manager import ContextManager
from prompt_engine.managers.response_controller import ResponseController
from prompt_engine.managers.citation_handler import CitationHandler
import logging

logger = logging.getLogger(__name__)

class PromptManager:
    """Central manager for prompt template selection and generation"""
   
    def __init__(self, openai_api_key: Optional[str] = None):
        self.intent_classifier = IntentClassifier()
        self.template_factory = TemplateFactory()
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        # Initialize OpenAI client with API key
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not provided or found in environment variables.")
        self.openai_client = openai.OpenAI(api_key=api_key)
       
    def process_query(self,
                     user_query: str,
                     graphrag_results: Dict,
                     conversation_context: Dict,
                     user_expertise: UserExpertise = UserExpertise.INTERMEDIATE,
                     response_length: ResponseLength = ResponseLength.MEDIUM) -> Dict:
        """
        Main method to process user query and generate response
       
        Args:
            user_query: User's question
            graphrag_results: Results from GraphRAG search
            conversation_context: Previous conversation history
            user_expertise: User's expertise level
            response_length: Desired response length
           
        Returns:
            Dict with generated response and metadata
        """
       
        # Step 1: Classify intent
        # intent_result now contains string values for question_type and topic
        intent_result = self.intent_classifier.classify_intent(user_query, graphrag_results) # Pass graphrag_results for refinement
       
        # Step 2: Create appropriate template
        # FIX: Access question_type directly as it's already a string
        template = self.template_factory.create_template(intent_result['question_type'])
       
        # Step 3: Generate prompt
        prompt = template.generate_prompt(
            user_query=user_query,
            graphrag_results=graphrag_results,
            context=conversation_context,
            user_expertise=user_expertise,
            response_length=response_length
        )
       
        # Step 4: Get GPT-4 response
        try:
            gpt_response = self._call_gpt4(prompt)
           
            return {
                'success': True,
                'response': gpt_response,
                'metadata': {
                    'intent': intent_result, # This dict is already JSON serializable
                    # FIX: Access question_type directly as it's already a string
                    'template_type': intent_result['question_type'],
                    'expertise_level': user_expertise.value,
                    'response_length': response_length.value,
                    'prompt_length': len(prompt),
                    'timestamp': datetime.now().isoformat()
                }
            }
           
        except Exception as e:
            # Log the full traceback for debugging internal server errors
            logger.error(f"Error in PromptManager.process_query: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'metadata': {
                    'intent': intent_result,
                    # FIX: Access question_type directly as it's already a string
                    'template_type': intent_result['question_type'],
                    'timestamp': datetime.now().isoformat()
                }
            }
   
    def _call_gpt4(self, prompt: str) -> str:
        """Call GPT-4 with the generated prompt"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14", # Ensure this model name is correct and available
                messages=[
                    {"role": "system", "content": prompt.split("USER QUESTION:")[0].strip()}, # Strip whitespace
                    {"role": "user", "content": prompt.split("USER QUESTION:")[1].strip() if "USER QUESTION:" in prompt else prompt.strip()} # Strip whitespace
                ],
                temperature=0.7,
                max_tokens=2000,  # Adjust based on response length requirements
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
           
            return response.choices[0].message.content
           
        except Exception as e:
            raise Exception(f"GPT-4 API call failed: {str(e)}")

# Integration Example (for testing, typically not part of the main app logic being imported)
class PromptEngineOrchestrator:
    """Main orchestrator that coordinates all components"""
   
    def __init__(self, openai_api_key: Optional[str] = None):
        self.prompt_manager = PromptManager(os.getenv("OPENAI_API_KEY"))
        self.context_manager = ContextManager()
        self.response_controller = ResponseController()
        self.citation_handler = CitationHandler()
   
    def process_user_query(self,
                          session_id: str,
                          user_query: str,
                          graphrag_results: Dict,
                          user_expertise: UserExpertise = UserExpertise.INTERMEDIATE,
                          response_length: ResponseLength = ResponseLength.MEDIUM) -> Dict:
        """
        Main method to process user query through the entire pipeline
        """
       
        # Get conversation context
        conversation_context = self.context_manager.get_context_with_topic_awareness(session_id)
   
        # Check if we should clear context due to topic change
        # Note: The logic for should_clear_context is usually based on intent_result from classify_intent,
        # which is *inside* prompt_manager.process_query.
        # This part of orchestrator might need to be re-evaluated if topic change detection
        # is meant to happen *before* calling prompt_manager.process_query.
        # For now, let's assume it works based on some prior context detection.
        if conversation_context.get('should_clear_context', False):
            self.context_manager.clear_context_on_topic_change(session_id)
            # Get fresh context after clearing
            conversation_context = self.context_manager.get_context_with_topic_awareness(session_id)
       
        # It seems `question_complexity` and `response_params` are defined AFTER `process_query` is called.
        # This block might be misplaced if these params are needed *before* `process_query`.
        # Assuming `response_params` are calculated for the *final* response, after LLM.
        question_complexity = graphrag_results.get('intent', {}).get('overall_confidence', 0.5) # Use overall_confidence
        response_params = self.response_controller.get_response_parameters(
            user_expertise, response_length, question_complexity
        )
       
        # Format citations
        citation_info = self.citation_handler.format_citations(graphrag_results)
       
        # Add citation instructions to GraphRAG results (this object is passed to template)
        enhanced_results = graphrag_results.copy()
        enhanced_results['citation_info'] = citation_info
       
        # Process query (this is where the LLM call happens)
        result = self.prompt_manager.process_query(
            user_query=user_query,
            graphrag_results=enhanced_results, # Use enhanced results for template
            conversation_context=conversation_context,
            user_expertise=user_expertise,
            response_length=response_length
        )
       
        # Add message to context (user message first)
        self.context_manager.add_message(
            session_id=session_id,
            role='user',
            content=user_query,
            metadata={'intent': result.get('metadata', {}).get('intent', {})} # Ensure default dict for intent
        )
       
        # Add assistant message to context if successful
        if result['success']:
            self.context_manager.add_message(
                session_id=session_id,
                role='assistant',
                content=result['response'],
                metadata=result['metadata'] # Pass the full metadata
            )
       
        # Add response parameters and citations to the final result dict
        result['response_params'] = response_params
        result['citations'] = citation_info
       
        return result


# Example usage for testing
if __name__ == "__main__":
    # Example usage
    # Ensure OPENAI_API_KEY is set in your environment variables for this to run
    # For local testing without a real API key, you might need to mock openai.OpenAI
    # os.environ["OPENAI_API_KEY"] = "sk-..." # Set a dummy key if needed for testing setup

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s') # Enable logging for testing

    orchestrator = PromptEngineOrchestrator(os.getenv("OPENAI_API_KEY"))
   
    sample_graphrag_results = {
        'results': [
            {
                'node_id': 'n_963250f1',
                'name': 'Single Responsibility Principle',
                'label': 'DesignPrinciple',
                'description': 'A class should have only one reason to change.',
                'source': 'solid-principles.pdf',
                'page': 5,
                'relevance_score': 0.9
            }
        ]
    }
   
    try:
        result = orchestrator.process_user_query(
            session_id="test_session_123",
            user_query="What is the Single Responsibility Principle?",
            graphrag_results=sample_graphrag_results,
            user_expertise=UserExpertise.INTERMEDIATE,
            response_length=ResponseLength.MEDIUM
        )
       
        # Use default=str for json.dumps to handle Enums or datetimes if they somehow sneak in
        print(json.dumps(result, indent=2, default=str))

    except Exception as e:
        print(f"An error occurred during orchestration: {e}")
        logging.error("Orchestration failed.", exc_info=True)