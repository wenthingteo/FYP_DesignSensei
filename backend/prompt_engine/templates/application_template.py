from typing import Dict
from prompt_engine.templates.base_template import BaseTemplate, UserExpertise, ResponseLength

class ApplicationTemplate(BaseTemplate):
    """Template for application/implementation questions about software design patterns and principles"""
    
    def generate_prompt(self, user_query: str, graphrag_results: Dict, context: Dict,
                       user_expertise: UserExpertise = UserExpertise.INTERMEDIATE,
                       response_length: ResponseLength = ResponseLength.MEDIUM) -> str:
        
        knowledge_context = self._format_graphrag_context(graphrag_results)
        conversation_context = self._format_conversation_context(context)
        expertise_modifier = self._get_expertise_modifier(user_expertise)
        length_modifier = self._get_length_modifier(response_length)
        implementation_focus = self._get_implementation_focus(user_expertise)
        code_complexity = self._get_code_complexity(user_expertise)
        
        prompt = f"""
{self.system_role}

{self.base_instructions}

TASK TYPE: SOFTWARE DESIGN IMPLEMENTATION
USER EXPERTISE LEVEL: {user_expertise.value.upper()}
{expertise_modifier}

RESPONSE LENGTH REQUIREMENTS:
{length_modifier}

{knowledge_context}

{conversation_context}

USER QUESTION: "{user_query}"

IMPLEMENTATION TASK INSTRUCTIONS:
You are providing practical implementation guidance for software design concepts. Follow this structured approach:

## Implementation Framework:

### 1. **Conceptual Foundation**
- Provide a brief, clear explanation of the concept
- **Bold** the main design pattern/principle name
- Explain *when* and *why* to use this approach
- Connect to relevant design principles (SOLID, DRY, etc.)

### 2. **Step-by-Step Implementation Guide**
Create a numbered, actionable implementation plan:
- Break down the implementation into logical steps
- **Bold** key implementation decisions at each step
- Explain the reasoning behind each step
- Highlight dependencies between steps

### 3. **Concrete Code Examples**
{code_complexity}
- Use proper syntax highlighting with ```language blocks```
- Include meaningful variable/class names
- Add inline comments for complex logic
- Show before/after comparisons when refactoring

### 4. **Implementation Patterns & Variations**
- Present the **standard implementation pattern**
- Show common variations and when to use them
- Discuss different approaches for different contexts
- **Bold** pattern names and key variations

### 5. **Pitfalls & Prevention**
- List **common mistakes** and anti-patterns
- Explain why these mistakes happen
- Provide specific strategies to avoid them
- Include warning signs to watch for

### 6. **Best Practices & Optimization**
- Present **industry best practices**
- Discuss performance considerations
- Suggest code organization and structure
- Mention relevant tools and frameworks

### 7. **Testing & Validation Strategy**
- Provide **concrete testing approaches**
- Show example test cases
- Explain how to validate the implementation
- Suggest metrics for measuring success

{implementation_focus}

## Code Requirements:
- Provide **working, executable code examples**
- Use consistent coding style and conventions
- Include error handling where appropriate
- Show both interface/abstract and concrete implementations
- Demonstrate the pattern in a realistic scenario

## Educational Requirements:
- Connect implementation to broader design principles
- Explain trade-offs and design decisions
- Reference patterns and principles from your knowledge base
- Use [Source: filename, page X] citations for all concepts
- Encourage understanding, not just copying

Begin your implementation guidance now:
"""
        return prompt.strip()
    
    def _get_implementation_focus(self, expertise: UserExpertise) -> str:
        """Get expertise-specific implementation focus areas"""
        focus_areas = {
            UserExpertise.BEGINNER: """
## Beginner Implementation Focus:
- **Start Simple**: Begin with the most basic implementation
- **Explain Everything**: Don't assume prior knowledge of syntax or concepts
- **Use Familiar Examples**: Choose relatable, real-world scenarios
- **Step-by-Step**: Break down each line of code if necessary
- **Focus on**: Single responsibility, basic inheritance, simple composition
- **Avoid**: Complex generics, advanced language features, multiple design patterns
- **Include**: Detailed comments and explanations for each code section
""",
            
            UserExpertise.INTERMEDIATE: """
## Intermediate Implementation Focus:
- **Build Progressively**: Start simple, then add complexity
- **Show Alternatives**: Present multiple implementation approaches
- **Explain Trade-offs**: Discuss when to choose one approach over another
- **Focus on**: SOLID principles, common design patterns, refactoring techniques
- **Include**: Practical examples from real-world scenarios
- **Connect**: Implementation choices to maintainability and extensibility
- **Demonstrate**: How patterns work together in larger systems
""",
            
            UserExpertise.ADVANCED: """
## Advanced Implementation Focus:
- **System-Level Thinking**: Show how patterns fit into larger architectures
- **Performance Considerations**: Discuss memory, CPU, and scalability implications
- **Enterprise Patterns**: Include dependency injection, event sourcing, CQRS
- **Focus on**: Advanced OOP concepts, architectural patterns, design trade-offs
- **Include**: Thread safety, async patterns, and concurrent implementations
- **Discuss**: Framework integration, testing strategies, and production concerns
- **Show**: Complex scenarios with multiple interacting patterns
"""
        }
        return focus_areas.get(expertise, focus_areas[UserExpertise.INTERMEDIATE])
    
    def _get_code_complexity(self, expertise: UserExpertise) -> str:
        """Get expertise-appropriate code complexity guidelines"""
        complexity_levels = {
            UserExpertise.BEGINNER: """
**Code Complexity for Beginners:**
- Use simple, single-file examples
- Avoid complex inheritance hierarchies
- Focus on one concept at a time
- Use clear, descriptive variable names
- Include extensive comments explaining each section""",
            
            UserExpertise.INTERMEDIATE: """
**Code Complexity for Intermediate:**
- Show multi-file, multi-class implementations
- Demonstrate proper separation of concerns
- Include interfaces and abstract classes
- Show realistic error handling
- Balance brevity with educational value""",
            
            UserExpertise.ADVANCED: """
**Code Complexity for Advanced:**
- Present production-ready implementations
- Include comprehensive error handling and edge cases
- Show integration with frameworks and libraries
- Demonstrate performance optimizations
- Include concurrent and async implementations where relevant"""
        }
        return complexity_levels.get(expertise, complexity_levels[UserExpertise.INTERMEDIATE])