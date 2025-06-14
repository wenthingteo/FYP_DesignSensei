from typing import Dict
from prompt_engine.templates.base_template import BaseTemplate, UserExpertise, ResponseLength

class ExplanationTemplate(BaseTemplate):
    """Template for explanation-type questions about software design concepts, patterns, and principles"""
    
    def generate_prompt(self, user_query: str, graphrag_results: Dict, context: Dict,
                       user_expertise: UserExpertise = UserExpertise.INTERMEDIATE,
                       response_length: ResponseLength = ResponseLength.MEDIUM) -> str:
        
        knowledge_context = self._format_graphrag_context(graphrag_results)
        conversation_context = self._format_conversation_context(context)
        expertise_modifier = self._get_expertise_modifier(user_expertise)
        length_modifier = self._get_length_modifier(response_length)
        explanation_approach = self._get_explanation_approach(user_expertise)
        pedagogical_strategy = self._get_pedagogical_strategy(user_expertise)
        
        prompt = f"""
{self.system_role}

{self.base_instructions}

TASK TYPE: SOFTWARE DESIGN CONCEPT EXPLANATION
USER EXPERTISE LEVEL: {user_expertise.value.upper()}
{expertise_modifier}

RESPONSE LENGTH REQUIREMENTS:
{length_modifier}

{knowledge_context}

{conversation_context}

USER QUESTION: "{user_query}"

EXPLANATION TASK INSTRUCTIONS:
You are providing a comprehensive educational explanation of software design concepts. Follow this pedagogical framework:

## Educational Explanation Framework:

### 1. **Concept Introduction & Definition**
- Start with a **clear, precise definition** of the main concept
- **Bold** the concept name and key terminology throughout
- Provide the *etymology* or historical context when relevant
- Explain what problem this concept solves in software design
# - Use [Source: filename, page X] citations for definitions # REMOVED

### 2. **Core Principles & Fundamentals**
- Break down the concept into **fundamental components**
- Explain the **underlying principles** that make it work
- Connect to **foundational design principles** (SOLID, DRY, KISS, etc.)
- Use clear, logical progression from simple to complex
- **Bold** each principle or component as you introduce it

### 3. **Why It Matters: Problem & Solution Context**
- Explain the **specific problems** this concept addresses
- Describe what happens **without** using this approach
- Show the **benefits and advantages** of applying the concept
- Connect to broader software quality attributes (maintainability, scalability, etc.)
- Use real-world analogies when appropriate

### 4. **Practical Examples & Demonstrations**
{explanation_approach}
- Provide **multiple concrete examples** with different contexts
- Include **code examples** using ```language syntax highlighting```
- Show **before/after scenarios** to demonstrate improvement
- Use **progressive complexity** - start simple, build up
- Include **visual diagrams or pseudocode** when helpful

### 5. **Implementation Patterns & Variations**
- Present the **standard implementation approach**
- Show **common variations** and when to use each
- Discuss **different contexts** where the approach varies
- **Bold** pattern names and key implementation choices
- Explain trade-offs between different approaches

### 6. **Relationship to Other Concepts**
- Connect to **related design patterns** and principles
- Explain how it **works with or complements** other concepts
- Identify **concepts that conflict** or are alternatives
- Show how it fits into **larger architectural contexts**
- Create a **conceptual map** of relationships

### 7. **Common Misconceptions & Pitfalls**
- Address **frequent misunderstandings** about the concept
- Explain **common implementation mistakes**
- Clarify **when NOT to use** this approach
- Provide **warning signs** of incorrect usage
- Offer **debugging tips** for common issues

### 8. **Best Practices & Guidelines**
- Present **industry-standard best practices**
- Provide **implementation guidelines** and rules of thumb
- Discuss **code organization** and structural considerations
- Include **naming conventions** and documentation practices
- Reference **established standards** from your knowledge base

### 9. **Learning Path & Further Exploration**
- Suggest **prerequisite concepts** if any are missing
- Recommend **next concepts** to learn for progression
- Provide **practice exercises** or challenges to try
- Suggest **additional resources** for deeper learning
- Connect to **career development** and practical applications

{pedagogical_strategy}

## Educational Requirements:
- Use **progressive disclosure** - introduce complexity gradually
- Include **multiple learning modalities** (text, code, examples, analogies)
- Provide **scaffolding** - build on previously explained concepts
- Create **cognitive bridges** between new and familiar concepts
- Encourage **active learning** through questions and exercises

## Formatting Requirements:
- Use clear **heading hierarchy** (# ## ###) for easy navigation
- **Bold** all important concepts, pattern names, and principles
- Use `code formatting` for technical terms and class names
- Include **bullet points** for lists and key takeaways
- Create **comparison tables** when explaining variations
- Use **callout boxes** with > for important notes and tips

Begin your comprehensive educational explanation now:
"""
        return prompt.strip()
    
    def _get_explanation_approach(self, expertise: UserExpertise) -> str:
        """Get expertise-specific explanation approach"""
        approaches = {
            UserExpertise.BEGINNER: """
**Explanation Approach for Beginners:**
- **Start with analogies** from everyday life or familiar domains
- **Use simple code examples** with extensive comments
- **Explain every technical term** when first introduced
- **Break complex concepts** into smaller, digestible pieces
- **Repeat key points** in different ways to reinforce learning
- **Use visual aids** and step-by-step walkthroughs
- **Focus on the 'why'** before diving into the 'how'""",
            
            UserExpertise.INTERMEDIATE: """
**Explanation Approach for Intermediate:**
- **Build on existing knowledge** of basic OOP and design concepts
- **Use realistic code examples** from common application scenarios
- **Show multiple implementation styles** and discuss trade-offs
- **Connect to practical development experience** and common challenges
- **Include refactoring examples** showing evolution of code
- **Balance theory with practical application**
- **Reference industry practices** and common frameworks""",
            
            UserExpertise.ADVANCED: """
**Explanation Approach for Advanced:**
- **Assume solid foundation** in design principles and patterns
- **Focus on nuanced details** and advanced considerations
- **Include performance implications** and scalability factors
- **Show enterprise-scale examples** with complex requirements
- **Discuss framework-specific implementations** and integrations
- **Analyze edge cases** and advanced scenarios
- **Connect to architectural patterns** and system design"""
        }
        return approaches.get(expertise, approaches[UserExpertise.INTERMEDIATE])
    
    def _get_pedagogical_strategy(self, expertise: UserExpertise) -> str:
        """Get expertise-appropriate pedagogical strategy"""
        strategies = {
            UserExpertise.BEGINNER: """
## Pedagogical Strategy for Beginners:
- **Learning Objective**: Build foundational understanding
- **Cognitive Load**: Keep concepts simple and well-separated
- **Examples**: Use familiar domains (library, restaurant, simple games)
- **Progression**: Linear, step-by-step with clear checkpoints
- **Assessment**: Include simple comprehension questions
- **Motivation**: Connect to immediate practical benefits
""",
            
            UserExpertise.INTERMEDIATE: """
## Pedagogical Strategy for Intermediate:
- **Learning Objective**: Deepen understanding and practical application
- **Cognitive Load**: Moderate complexity with clear organization
- **Examples**: Use realistic business applications and common scenarios
- **Progression**: Spiral learning - revisit concepts with added complexity
- **Assessment**: Include application and analysis questions
- **Motivation**: Connect to career growth and code quality improvement
""",
            
            UserExpertise.ADVANCED: """
## Pedagogical Strategy for Advanced:
- **Learning Objective**: Master advanced applications and system thinking
- **Cognitive Load**: High complexity with sophisticated connections
- **Examples**: Use enterprise systems and architectural challenges
- **Progression**: Non-linear, exploring multiple perspectives and approaches
- **Assessment**: Include synthesis and evaluation challenges
- **Motivation**: Connect to system design mastery and technical leadership
"""
        }
        return strategies.get(expertise, strategies[UserExpertise.INTERMEDIATE])
