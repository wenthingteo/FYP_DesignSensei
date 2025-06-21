# prompt_engine/managers/prompt_manager.py
import json
import openai
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from prompt_engine.templates.base_template import UserExpertise, ResponseLength
from prompt_engine.managers.response_controller import ResponseController
from prompt_engine.managers.context_manager import ContextManager
from prompt_engine.managers.citation_handler import CitationHandler
from prompt_engine.templates.template_factory import TemplateFactory
from prompt_engine.intent_classifier import IntentClassifier, QuestionType 
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
                     conversation_context: Dict, # This context is passed from Orchestrator
                     user_expertise: UserExpertise = UserExpertise.INTERMEDIATE,
                     response_length: ResponseLength = ResponseLength.MEDIUM) -> Dict:
        """
        Main method to process user query and generate response.
        This method is now solely responsible for:
        1. Classifying the intent.
        2. Getting the appropriate template or generating a generic prompt.
        3. Generating the LLM prompt.
        4. Calling the LLM for all intents.
        5. Returning the raw LLM response along with the classified intent.
        """
        
        # Step 1: Classify intent
        intent_result = self.intent_classifier.classify_intent(user_query, graphrag_results)
        intent_type = intent_result['question_type'] # Get the string value of the intent

        llm_prompt = ""
        system_role = ""
        
        # Determine prompt based on intent type
        if intent_type == QuestionType.GREETING.value:
            system_role = "You are a friendly and helpful AI assistant."
            llm_prompt = f"The user greeted you. Respond to 'User: {user_query}' with a friendly greeting and offer assistance related to software design."
            # For greetings, we don't need extensive graphrag_results or conversation_context in the prompt
            # Max tokens for greeting should be short.
            max_tokens = 50
        elif intent_type == QuestionType.OUT_OF_SCOPE_GENERAL.value:
            system_role = "You are an AI assistant specialized in software design. Politely decline questions outside your expertise."
            llm_prompt = f"The user asked: '{user_query}'. This question is outside your expertise in software design. Politely explain that you are specialized in software design and suggest they try a different topic or seek help elsewhere. Avoid giving an answer to the specific out-of-scope question."
            # Max tokens for out-of-scope should be medium.
            max_tokens = 150
        else: # Software design specific intents (EXPLANATION, COMPARISON, etc.)
            # Step 2: Create appropriate template
            # FIX: Use create_template instead of get_template as per TemplateFactory's definition
            template = self.template_factory.create_template(intent_type) # Pass string value
            system_role = template.system_role
            
            # Step 3: Generate prompt for software design questions
            llm_prompt = template.generate_prompt(
                user_query=user_query,
                graphrag_results=graphrag_results,
                context=conversation_context,
                user_expertise=user_expertise,
                response_length=response_length
            )
            # Determine max_tokens from a dummy ResponseController (Orchestrator will use its own)
            dummy_response_controller = ResponseController() # Temp instance for max_tokens only
            response_params = dummy_response_controller.get_response_parameters(
                user_expertise=user_expertise,
                response_length=response_length,
                question_complexity=intent_result.get('overall_confidence', 0.5), # Use actual intent confidence
                conversation_length=len(conversation_context.get('previous_messages', []))
            )
            max_tokens = response_params['max_tokens']
        
        # --- MODIFIED LINE: Truncate llm_prompt for logging display ---
        logger.debug(f"Generated LLM Prompt for {intent_type}:\n{llm_prompt[:300]}..." if len(llm_prompt) > 300 else llm_prompt)

        # Step 4: Call LLM for ALL intent types
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14", 
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": llm_prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            raw_response_content = response.choices[0].message.content
            logger.info(f"Raw LLM Response (first 100 chars): {raw_response_content[:100]}...")

            return {
                'success': True,
                'response': raw_response_content,
                'metadata': {
                    'intent': intent_result,
                    'template_type': intent_type,
                    'expertise_level': user_expertise.value,
                    'response_length': response_length.value,
                    'prompt_length': len(llm_prompt),
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except openai.APITimeoutError as e:
            logger.error(f"OpenAI API request timed out: {e}")
            return {'success': False, 'error': f"API timeout: {e}", 'metadata': {'intent': intent_result, 'template_type': intent_type, 'timestamp': datetime.now().isoformat()}}
        except openai.APIConnectionError as e:
            logger.error(f"Could not connect to OpenAI API: {e}")
            return {'success': False, 'error': f"API connection error: {e}", 'metadata': {'intent': intent_result, 'template_type': intent_type, 'timestamp': datetime.now().isoformat()}}
        except openai.APIStatusError as e:
            logger.error(f"OpenAI API returned an API Status Error: {e.status_code} - {e.response}")
            return {'success': False, 'error': f"API status error {e.status_code}: {e.response}", 'metadata': {'intent': intent_result, 'template_type': intent_type, 'timestamp': datetime.now().isoformat()}}
        except Exception as e:
            logger.error(f"An unexpected error occurred during LLM call: {e}", exc_info=True)
            return {'success': False, 'error': f"Unexpected error: {e}", 'metadata': {'intent': intent_result, 'template_type': intent_type, 'timestamp': datetime.now().isoformat()}}

# Integration Example (This is your PromptEngineOrchestrator)
class PromptEngineOrchestrator:
    """Main orchestrator that coordinates all components"""
   
    def __init__(self, openai_api_key: Optional[str] = None):
        self.prompt_manager = PromptManager(openai_api_key) # Pass API key
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
        Main method to process user query through the entire pipeline.
        This orchestrator now relies entirely on PromptManager to call the LLM
        for ALL intent types (including greetings and out-of-scope).
        """
        
        # Get conversation context BEFORE classifying intent, so it's available for add_message
        conversation_context_for_prompt_manager = self.context_manager.get_context_with_topic_awareness(session_id)

        # PromptManager now handles LLM call for all intents, including greetings/out-of-scope
        llm_processing_result = self.prompt_manager.process_query(
            user_query=user_query,
            graphrag_results=graphrag_results, # Pass the results from the search module
            conversation_context=conversation_context_for_prompt_manager,
            user_expertise=user_expertise,
            response_length=response_length
        )

        # Handle errors from LLM call within PromptManager
        if not llm_processing_result['success']:
            self.context_manager.add_message(session_id, "user", user_query)
            self.context_manager.add_message(session_id, "bot", llm_processing_result.get('error', 'An error occurred.'), metadata={"intent": {"type": llm_processing_result['metadata']['intent']['question_type']}})
            return llm_processing_result # Return the error result

        raw_llm_response = llm_processing_result['response']
        intent_type = llm_processing_result['metadata']['intent']['question_type']

        # Calculate response parameters (as per your original Orchestrator design)
        # This will still be relevant for software design queries, and can be default for others.
        question_complexity = llm_processing_result['metadata']['intent'].get('overall_confidence', 0.5)
        response_params = self.response_controller.get_response_parameters(
            user_expertise, 
            response_length, 
            question_complexity,
            len(conversation_context_for_prompt_manager.get('previous_messages', []))
        )
        
        # Format citations only if there are graph results and it's a software design intent
        citation_info = {'citations': [], 'references': []}
        if graphrag_results.get('results') and intent_type not in [QuestionType.GREETING.value, QuestionType.OUT_OF_SCOPE_GENERAL.value]:
            citation_info = self.citation_handler.format_citations(graphrag_results)
        
        # Add messages to context (user message first, then assistant message)
        self.context_manager.add_message(
            session_id=session_id,
            role='user',
            content=user_query,
            metadata={'intent': llm_processing_result['metadata']['intent']}
        )
        self.context_manager.add_message(
            session_id=session_id,
            role='assistant',
            content=raw_llm_response,
            metadata={
                'intent': llm_processing_result['metadata']['intent'],
                'response_params': response_params,
                'citations': citation_info.get('citations', []),
                'references': citation_info.get('references', [])
            }
        )
        
        final_result = {
            'success': True,
            'response': raw_llm_response,
            'metadata': {
                'intent': llm_processing_result['metadata']['intent'],
                'template_type': intent_type,
                'expertise_level': user_expertise.value,
                'response_length': response_length.value,
                'prompt_length': llm_processing_result['metadata']['prompt_length'],
                'timestamp': datetime.now().isoformat()
            },
            'response_params': response_params,
            'citations': citation_info.get('citations', []),
            'references': citation_info.get('references', [])
        }
        
        return final_result


# Example usage for testing (This is your original __main__ block, now correctly referencing Orchestrator)
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv() # Load environment variables for API key

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
    empty_graphrag_results = {'results': []}

    try:
        # Test 1: Greeting - now LLM-generated
        print("\n--- Testing Greeting (LLM Generated) ---")
        result_greeting = orchestrator.process_user_query(
            session_id="test_session_greet_llm",
            user_query="Hi Sensei, how are you today?",
            graphrag_results=empty_graphrag_results,
            user_expertise=UserExpertise.BEGINNER,
            response_length=ResponseLength.SHORT
        )
        print(f"Sensei (Greeting): {result_greeting['response']}")
        print(f"Success: {result_greeting['success']}")
        print(f"Intent: {result_greeting['metadata']['intent']['question_type']}")

        # Test 2: Out of Scope - now LLM-generated
        print("\n--- Testing Out of Scope (LLM Generated) ---")
        result_oos = orchestrator.process_user_query(
            session_id="test_session_oos_llm",
            user_query="Tell me about the history of the internet.",
            graphrag_results=empty_graphrag_results,
            user_expertise=UserExpertise.INTERMEDIATE,
            response_length=ResponseLength.MEDIUM
        )
        print(f"Sensei (Out of Scope): {result_oos['response']}")
        print(f"Success: {result_oos['success']}\n")
        print(f"Intent: {result_oos['metadata']['intent']['question_type']}")

        # Test 3: Software Design Question
        print("\n--- Testing Software Design Question ---")
        result_sd = orchestrator.process_user_query(
            session_id="test_session_sd",
            user_query="What is the Single Responsibility Principle?",
            graphrag_results=sample_graphrag_results,
            user_expertise=UserExpertise.INTERMEDIATE,
            response_length=ResponseLength.MEDIUM
        )
        print(f"Sensei (Software Design): {result_sd['response'][:200]}...")
        print(f"Success: {result_sd['success']}")
        print(f"Intent: {result_sd['metadata']['intent']['question_type']}")
        print(f"Citations: {result_sd.get('citations', 'N/A')}")


    except Exception as e:
        print(f"An error occurred during orchestration: {e}")
        logging.error("Orchestration failed.", exc_info=True)