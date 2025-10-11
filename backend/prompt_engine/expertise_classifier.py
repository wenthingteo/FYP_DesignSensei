# prompt_engine/expertise_classifier.py
import re
import logging
from typing import Dict, List
from prompt_engine.templates.base_template import UserExpertise, ResponseLength

logger = logging.getLogger(__name__)

class ExpertiseClassifier:
    def __init__(self):
        # Keywords and patterns for different expertise levels
        self.beginner_patterns = [
            r'what is\\b', r'explain\\s+([^\\s]+)\\s+in simple terms', r'tell me about (.*) like i am five',
            r'what does (.*) mean', r'basics of (.*)', r'introduction to (.*)'
        ]
        self.intermediate_patterns = [
            r'how does (.*) work', r'compare (.*) and (.*)', r'pros and cons of (.*)',
            r'when to use (.*)', r'example of (.*) implementation', r'design principles behind (.*)'
        ]
        self.advanced_patterns = [
            r'deep dive into (.*)', r'optimize (.*) performance', r'scalability of (.*)',
            r'trade-offs of (.*)', r'challenges in (.*) architecture', r'advanced concepts of (.*)',
            r'best practices for (.*)'
        ]
        self.keywords = {
            UserExpertise.BEGINNER: ['simple', 'basics', 'intro', 'what is', 'explain like'],
            UserExpertise.INTERMEDIATE: ['compare', 'how does', 'pros and cons', 'when to use', 'example', 'principles'],
            UserExpertise.ADVANCED: ['deep dive', 'optimize', 'scale', 'trade-offs', 'challenges', 'advanced', 'best practices']
        }

    def infer_expertise(self, user_query: str, conversation_history: List[Dict]) -> UserExpertise:
        query_lower = user_query.lower()
        
        # Initialize scores for each expertise level
        scores = {
            UserExpertise.BEGINNER: 0,
            UserExpertise.INTERMEDIATE: 0,
            UserExpertise.ADVANCED: 0
        }

        # Analyze current query based on patterns
        for pattern in self.beginner_patterns:
            if re.search(pattern, query_lower):
                scores[UserExpertise.BEGINNER] += 1
        for pattern in self.intermediate_patterns:
            if re.search(pattern, query_lower):
                scores[UserExpertise.INTERMEDIATE] += 1
        for pattern in self.advanced_patterns:
            if re.search(pattern, query_lower):
                scores[UserExpertise.ADVANCED] += 1

        # Analyze current query based on keywords
        for expertise, kws in self.keywords.items():
            for kw in kws:
                if kw in query_lower:
                    scores[expertise] += 0.5 # Give keywords a slightly lower weight than patterns

        # Factor in previous conversation context (if available)
        # This part is simplistic; a more robust approach would analyze historical
        # query complexity, bot response clarity, and user follow-ups.
        if conversation_history:
            # Look at the most recent message's inferred expertise, if any
            # For simplicity, we'll just look at the last user message
            last_user_message = next((m['text'] for m in reversed(conversation_history) if m['sender'] == 'user'), None)
            if last_user_message:
                last_query_lower = last_user_message.lower()
                for pattern in self.beginner_patterns:
                    if re.search(pattern, last_query_lower):
                        scores[UserExpertise.BEGINNER] += 0.2
                for pattern in self.intermediate_patterns:
                    if re.search(pattern, last_query_lower):
                        scores[UserExpertise.INTERMEDIATE] += 0.2
                for pattern in self.advanced_patterns:
                    if re.search(pattern, last_query_lower):
                        scores[UserExpertise.ADVANCED] += 0.2

        # Determine the expertise with the highest score
        # Handle ties by preferring Intermediate > Advanced > Beginner as a default
        # or stick to the current_expertise if score differences are minimal
        
        max_score = -1
        inferred_level = UserExpertise.INTERMEDIATE # Default if no strong signal

        # Prioritize based on scores
        if scores[UserExpertise.ADVANCED] > max_score:
            max_score = scores[UserExpertise.ADVANCED]
            inferred_level = UserExpertise.ADVANCED
        if scores[UserExpertise.INTERMEDIATE] >= max_score: # Use >= to give intermediate a slight edge if tied with beginner
            max_score = scores[UserExpertise.INTERMEDIATE]
            inferred_level = UserExpertise.INTERMEDIATE
        if scores[UserExpertise.BEGINNER] > max_score:
            max_score = scores[UserExpertise.BEGINNER]
            inferred_level = UserExpertise.BEGINNER
        
        # If all scores are zero, default to INTERMEDIATE or a predefined default
        if all(score == 0 for score in scores.values()):
            inferred_level = UserExpertise.INTERMEDIATE
            
        logger.info(f"Inferred Expertise Scores: {scores}")
        logger.info(f"Inferred Expertise Level for '{user_query}': {inferred_level.value}")
        
        return inferred_level

# Example usage (for testing this module independently)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    classifier = ExpertiseClassifier()

    # Test cases
    queries = [
        "what is an object?",
        "explain SOLID principles simply",
        "how does dependency injection work in Spring?",
        "compare microservices and monolith architectures",
        "deep dive into eventual consistency in distributed systems",
        "what are the trade-offs of using GraphQL?",
        "tell me about design patterns",
        "how to optimize database queries?",
        "what does OOP mean for a beginner?"
    ]

    for q in queries:
        # Simulate an empty conversation history for initial inference
        inferred = classifier.infer_expertise(q, [])
        print(f"Query: '{q}' -> Inferred: {inferred.value}")

    print("\\n--- Testing with Conversation History (simplified) ---")
    history1 = [{'sender': 'user', 'text': 'what is a class?'},
                {'sender': 'bot', 'text': 'A class is a blueprint...'}]
    inferred = classifier.infer_expertise("explain inheritance simply", history1)
    print(f"Query: 'explain inheritance simply' (with history) -> Inferred: {inferred.value}")

    history2 = [{'sender': 'user', 'text': 'how does REST work?'},
                {'sender': 'bot', 'text': 'REST is an architectural style...'}]
    inferred = classifier.infer_expertise("what are the challenges with idempotent operations?", history2)
    print(f"Query: 'what are the challenges with idempotent operations?' (with history) -> Inferred: {inferred.value}")