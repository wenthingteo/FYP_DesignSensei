# Fixed test_full_system.py
from search_module.mock_search_module import MockSearchModule, MOCK_KNOWLEDGE_GRAPH_DATA
from prompt_engine.managers.prompt_manager import PromptManager
from prompt_engine.templates.base_template import UserExpertise, ResponseLength
import os

# Initialize the mock search module
mock_search_module_instance = MockSearchModule(MOCK_KNOWLEDGE_GRAPH_DATA)

# Initialize your PromptManager (ensure you have your OpenAI API key set as an environment variable)
# For testing without API key, we'll set call_gpt=False
prompt_manager = PromptManager(openai_api_key=os.getenv("OPENAI_API_KEY"))

# Example: Simulating a user query and passing results to PromptManager
user_question = "Explain the Dependency Inversion Principle."

print("=" * 60)
print("TESTING PROMPT GENERATION SYSTEM")
print("=" * 60)

# 1. Use the mock search module to get "graphrag_results"
print("Step 1: Getting search results from mock module...")
search_results_from_mock = mock_search_module_instance.search(user_question)
print(f"Found {len(search_results_from_mock['results'])} results")

# 2. Prepare conversation context (from your ContextManager)
conversation_context = {
    'previous_messages': [
        {'role': 'user', 'content': 'Hello!'},
        {'role': 'assistant', 'content': 'How can I help you learn about software design today?'}
    ]
}

# 3. Process the query with your PromptManager
print("\nStep 2: Processing query with PromptManager...")
try:
    result = prompt_manager.process_query(
        user_query=user_question,
        graphrag_results=search_results_from_mock,
        conversation_context=conversation_context,
        user_expertise=UserExpertise.INTERMEDIATE,
        response_length=ResponseLength.MEDIUM
    )
    
    print("✅ Query processed successfully!")
    print(f"Available result keys: {list(result.keys())}")
    
    # Display results based on what's actually available
    print(f"\n--- RESULT SUMMARY ---")
    print(f"Success: {result.get('success', 'Unknown')}")
    
    if 'metadata' in result:
        metadata = result['metadata']
        print(f"Intent: {metadata.get('intent', {}).get('question_type', 'Unknown')}")
        print(f"Topic: {metadata.get('intent', {}).get('topic', 'Unknown')}")
        print(f"Template Type: {metadata.get('template_type', 'Unknown')}")
        print(f"Expertise Level: {metadata.get('expertise_level', 'Unknown')}")
        print(f"Response Length: {metadata.get('response_length', 'Unknown')}")
    
    # Handle different possible return formats
    if 'prompt' in result:
        print(f"\n--- GENERATED PROMPT ---")
        prompt_text = result['prompt']
        if len(prompt_text) > 500:
            print(prompt_text[:500] + "\n... [TRUNCATED] ...")
        else:
            print(prompt_text)
    elif 'response' in result and result['response']:
        print(f"\n--- GPT-4 RESPONSE ---")
        response_text = result['response']
        if len(response_text) > 500:
            print(response_text[:500] + "\n... [TRUNCATED] ...")
        else:
            print(response_text)
    else:
        print(f"\n--- NO PROMPT OR RESPONSE FOUND ---")
        print("This might indicate an issue with the PromptManager implementation.")
    
    # Display any errors
    if 'error' in result:
        print(f"\n--- ERROR ---")
        print(f"Error: {result['error']}")
    
    # Display additional info if available
    if 'response_params' in result:
        print(f"\n--- RESPONSE PARAMETERS ---")
        print(f"Response Params: {result['response_params']}")
    
    if 'citations' in result:
        print(f"\n--- CITATIONS ---")
        citations = result['citations']
        if isinstance(citations, dict) and 'references' in citations:
            for ref in citations['references']:
                print(f"- {ref.get('name', 'Unknown')} ({ref.get('source', 'Unknown')}, page {ref.get('page', 'Unknown')})")
        else:
            print(f"Citations: {citations}")

except Exception as e:
    print(f"❌ Error processing query: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    print(f"Traceback:\n{traceback.format_exc()}")

print("\n" + "=" * 60)
print("ADDITIONAL DEBUGGING INFO")
print("=" * 60)

# Test the individual components
print("\n1. Testing Intent Classifier...")
try:
    from prompt_engine.intent_classifier import IntentClassifier
    classifier = IntentClassifier()
    intent_result = classifier.classify_intent(user_question)
    print(f"✅ Intent classification successful: {intent_result}")
except Exception as e:
    print(f"❌ Intent classifier error: {e}")

print("\n2. Testing Template Factory...")
try:
    from prompt_engine.templates.template_factory import TemplateFactory
    factory = TemplateFactory()
    template = factory.create_template('explanation')
    print(f"✅ Template creation successful: {template.__class__.__name__}")
except Exception as e:
    print(f"❌ Template factory error: {e}")

print("\n3. Testing Mock Search Module...")
try:
    test_results = mock_search_module_instance.search("test query")
    print(f"✅ Mock search successful: {len(test_results['results'])} results")
except Exception as e:
    print(f"❌ Mock search error: {e}")

print("\n4. Environment Check...")
print(f"OpenAI API Key present: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
print(f"Python path: {os.getcwd()}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)