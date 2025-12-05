"""
Base Template System for Software Design Education Chatbot - Enhanced Version
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum

class UserExpertise(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class ResponseLength(Enum):
    SHORT = "short"
    MEDIUM = "medium"
    DETAILED = "detailed" # Using DETAILED as per your latest template

class BaseTemplate(ABC):
    """Base class for all prompt templates"""
   
    def __init__(self):
        self.system_role = self._get_system_role()
        self.base_instructions = self._get_base_instructions()
       
    def _get_system_role(self) -> str:
        """Define the system role for GPT-4"""
        return """You are an expert software design educator with deep knowledge of design patterns,
SOLID principles, software architecture, domain-driven design, code quality, and code structure.
You provide clear, educational explanations with practical examples and always cite your sources."""

    def _get_base_instructions(self) -> str:
        """Base instructions for all templates"""
        return """
IMPORTANT INSTRUCTIONS:

CONTENT REQUIREMENTS:
1. Always cite sources using the format: [Source: filename, page X] if applicable
2. Use clear, educational language appropriate for the user's expertise level
3. Provide practical examples when appropriate
4. Include related concepts that might be helpful
5. Encourage further learning with suggested follow-up topics

FORMATTING REQUIREMENTS:
6. Structure your response with clear markdown formatting:
   - Use # for main headings
   - Use ## for subheadings
   - Use ### for sub-subheadings
   - Use **bold** for important keywords, concepts, and principle names
   - Use *italics* for emphasis and definitions
   - Use `code formatting` for code snippets, class names, method names, and technical terms
   - Use bullet points (-) for lists and key points
   - Use numbered lists (1., 2., 3.) for step-by-step processes
   - Use > for important quotes or principles
   - Use --- for section separators when needed

VISUAL EMPHASIS:
7. **Bold** the following elements:
   - Design pattern names (e.g., **Singleton Pattern**, **Factory Pattern**)
   - SOLID principles (e.g., **Single Responsibility Principle**)
   - Important concepts (e.g., **Dependency Injection**, **Polymorphism**)
   - Key takeaways and main points
   - Warning keywords (e.g., **Important**, **Note**, **Warning**)

8. Use `backticks` for:
   - Code elements: `class`, `method()`, `variable`
   - File names: `main.py`, `config.json`
   - Technical terms: `API`, `HTTP`, `JSON`

9. Organize complex responses with clear sections:
   - Overview/Introduction
   - Main content with subheadings
   - Examples (with code blocks using ```)
   - Key takeaways or summary
   - Related concepts or further reading
"""

    @abstractmethod
    def generate_prompt(self,
                        user_query: str,
                        graphrag_results: Dict,
                        context: Dict,
                        user_expertise: UserExpertise = UserExpertise.INTERMEDIATE,
                        response_length: ResponseLength = ResponseLength.MEDIUM) -> str:
        """Generate the complete prompt for GPT-4"""
        pass

    def _format_graphrag_context(self, results: Dict) -> str:
        """
        Format GraphRAG results into context for the prompt.
        Safely accesses dictionary keys using .get() to prevent KeyErrors.
        """
        # Ensure results is not None or empty, and has a 'results' key or is a dict of dicts
        if not results or not (isinstance(results, dict) and (results.get('results') or any(isinstance(v, dict) for v in results.values()))):
            return "No specific knowledge graph results available."
           
        context_parts = []
        context_parts.append("KNOWLEDGE BASE CONTEXT:")
       
        # Normalize input to a list of result dictionaries
        list_of_results = []
        if isinstance(results, dict) and 'results' in results and isinstance(results['results'], list):
            list_of_results = results['results']
        elif isinstance(results, dict): # Handle the {"Concept Name": {...}} format
            list_of_results = list(results.values())
        elif isinstance(results, list): # Direct list of results (less likely from search_service, but robust)
            list_of_results = results

        # Limit to top 5 results to keep prompt concise
        for i, result in enumerate(list_of_results[:5], 1):  
            # --- FIX: Use .get() with a default value to avoid KeyError ---
            name = result.get('name')
            title = result.get('title') # 'title' often comes from raw Neo4j results
            label = result.get('label', 'General Concept')
            description = result.get('description')
            content = result.get('content') # 'content' often comes from raw Neo4j results
            source = result.get('source', 'N/A') # Safe access for 'source'
            page = result.get('page', 'N/A') # Safe access for 'page'
            relevance_score = result.get('relevance_score', 0.0)
           
            # Prefer 'name' over 'title', 'description' over 'content'
            display_title = name if name else title if title else 'Untitled Concept'
            display_content = description if description else content if content else 'No detailed description available.'

            context_parts.append(f"\n{i}. **{display_title}** ({label})")
            context_parts.append(f"   Description: {display_content}")
            context_parts.append(f"   Source: {source}, Page: {page}")
            context_parts.append(f"   Relevance: {relevance_score:.2f}")
           
            # Add related concepts if 'relationships' key exists and is not empty
            if result.get('relationships') and isinstance(result['relationships'], list):
                # Assuming relationships are structured like [{'type': 'RELATED_TO', 'target_node_name': 'ConceptX'}]
                related = [rel.get('target_node_name') for rel in result['relationships'] if rel.get('target_node_name')][:2] # Limit related to 2
                if related:
                    context_parts.append(f"   Related Concepts: {', '.join(related)}")
       
        return '\n'.join(context_parts)

    def _get_expertise_modifier(self, expertise: UserExpertise) -> str:
        """Get expertise-specific instructions"""
        modifiers = {
            UserExpertise.BEGINNER: """
BEGINNER-LEVEL FORMATTING:
- Use simple, non-technical language where possible
- **Bold** all new technical terms when first introduced
- Provide basic definitions for technical terms in *italics*
- Include step-by-step explanations with numbered lists
- Use analogies and real-world examples
- Focus on fundamental concepts
- Use more visual breaks and shorter paragraphs""",
           
            UserExpertise.INTERMEDIATE: """
INTERMEDIATE-LEVEL FORMATTING:
- Use standard technical terminology with `code formatting`
- **Bold** important concepts and design patterns
- Provide moderate detail in explanations
- Include code examples in proper code blocks
- Connect concepts to practical applications
- Mention common pitfalls in **bold warnings**
- Use subheadings to organize complex topics""",
           
            UserExpertise.ADVANCED: """
ADVANCED-LEVEL FORMATTING:
- Use precise technical language with proper formatting
- **Bold** principle names and advanced concepts
- Provide in-depth analysis with clear section headers
- Include advanced code examples with syntax highlighting
- Discuss trade-offs in organized comparison tables
- Reference academic or industry best practices with proper citations
- Use complex nested formatting for detailed explanations"""
        }
        return modifiers.get(expertise, modifiers[UserExpertise.INTERMEDIATE])

    def _get_length_modifier(self, length: ResponseLength) -> str:
        """Get response length instructions"""
        modifiers = {
            ResponseLength.SHORT: """
SHORT RESPONSE FORMAT:
- Keep response concise (2-3 paragraphs maximum)
- Focus on key points only with **bold** emphasis
- Use bullet points for quick scanning
- Include one brief example maximum""",
           
            ResponseLength.MEDIUM: """
MEDIUM RESPONSE FORMAT:
- Provide a comprehensive but focused response (4-6 paragraphs)
- Use clear headings and subheadings
- Include examples with proper code formatting
- **Bold** important concepts throughout
- End with key takeaways in bullet points""",
           
            ResponseLength.DETAILED: """
DETAILED RESPONSE FORMAT:
- Provide an extensive, detailed response with full formatting
- Use multiple heading levels (# ## ###)
- Include multiple examples with code blocks
- Create comparison tables where relevant
- **Bold** all important concepts and patterns
- Include sections for: Overview, Details, Examples, Best Practices, Related Concepts
- Use visual separators (---) between major sections"""
        }
        return modifiers.get(length, modifiers[ResponseLength.MEDIUM])

    def _format_conversation_context(self, context: Dict) -> str:
        """Format previous conversation context"""
        if not context.get('previous_messages'):
            return ""
           
        context_parts = ["CONVERSATION CONTEXT (for understanding references like 'it', 'that', 'this'):"]
       
        # Increased from 3 to 8 messages to capture more context for pronoun resolution
        # This helps LLM understand references like "that", "it", "this concept" in follow-up questions
        for msg in context['previous_messages'][-8:]:  
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            # Truncate long messages to prevent exceeding token limits
            truncated_content = content[:200] + "..." if len(content) > 200 else content
            context_parts.append(f"**{role.upper()}**: {truncated_content}")
           
        return '\n'.join(context_parts)

    def _get_formatting_examples(self) -> str:
        """Provide formatting examples for the LLM"""
        return """
FORMATTING EXAMPLES TO FOLLOW:

# Main Topic: Design Patterns

## Creational Patterns

The **Factory Pattern** is a *creational design pattern* that provides an interface for creating objects.

### Key Benefits:
- **Flexibility**: Easy to extend with new types
- **Decoupling**: Client code doesn't depend on concrete classes
- **Consistency**: Ensures objects are created properly

### Example Implementation:
```python
class ShapeFactory:
    def create_shape(self, shape_type: str):
        if shape_type == "circle":
            return Circle()
        elif shape_type == "square":
            return Square()
```

> **Important**: Always follow the **Single Responsibility Principle** when implementing factories.

**Key Takeaways:**
- Factory patterns promote loose coupling
- They make code more maintainable
- Consider using when you have multiple related classes
"""