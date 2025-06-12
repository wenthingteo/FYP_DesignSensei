from typing import Dict
from backend.prompt_engine.templates.base_template import BaseTemplate, UserExpertise, ResponseLength

class AnalysisTemplate(BaseTemplate):
    """Template for analysis/evaluation questions about software design"""
    
    def generate_prompt(self, user_query: str, graphrag_results: Dict, context: Dict,
                       user_expertise: UserExpertise = UserExpertise.INTERMEDIATE,
                       response_length: ResponseLength = ResponseLength.MEDIUM) -> str:
        
        knowledge_context = self._format_graphrag_context(graphrag_results)
        conversation_context = self._format_conversation_context(context)
        expertise_modifier = self._get_expertise_modifier(user_expertise)
        length_modifier = self._get_length_modifier(response_length)
        analysis_focus = self._get_analysis_focus(user_expertise)
        
        prompt = f"""
{self.system_role}

{self.base_instructions}

TASK TYPE: SOFTWARE DESIGN ANALYSIS
USER EXPERTISE LEVEL: {user_expertise.value.upper()}
{expertise_modifier}

RESPONSE LENGTH REQUIREMENTS:
{length_modifier}

{knowledge_context}

{conversation_context}

USER QUESTION: "{user_query}"

ANALYSIS TASK INSTRUCTIONS:
You are conducting a comprehensive software design analysis. Follow this structured approach:

## Analysis Framework:

### 1. **Design Element Identification**
- Identify and **bold** all design patterns, principles, and architectural elements
- Categorize them (structural, behavioral, creational, architectural)
- Explain their roles and relationships

### 2. **Quality Assessment**
- Evaluate **strengths** and **weaknesses** systematically
- Assess adherence to **SOLID principles** and other design principles
- Identify code smells, anti-patterns, or architectural issues

### 3. **Best Practices Evaluation**
- Compare against industry standards and best practices
- Reference specific guidelines from your knowledge base
- Highlight deviations and their implications

### 4. **Improvement Analysis**
- Propose specific, actionable improvements
- Suggest alternative design approaches
- Explain the rationale behind each recommendation

### 5. **Trade-off Discussion**
- Analyze pros and cons of different approaches
- Discuss performance, maintainability, scalability implications
- Consider context-specific factors

### 6. **Recommendation Synthesis**
- Provide clear, prioritized recommendations
- Justify each recommendation with evidence
- Consider implementation complexity and impact

### 7. **Success Metrics**
- Suggest measurable criteria for evaluation
- Recommend tools or techniques for assessment
- Define what "good" looks like for this specific case

{analysis_focus}

## Response Requirements:
- Use proper markdown formatting with headings and **bold** keywords
- Support all claims with [Source: filename, page X] citations
- Include code examples where relevant using ```code blocks```
- Provide practical, actionable insights
- Connect analysis to broader software design principles

Begin your analysis now:
"""
        return prompt.strip()
    
    def _get_analysis_focus(self, expertise: UserExpertise) -> str:
        """Get expertise-specific analysis focus areas"""
        focus_areas = {
            UserExpertise.BEGINNER: """
## Beginner Analysis Focus:
- **Prioritize**: Basic design principles and common patterns
- **Explain**: Why certain approaches are better than others
- **Avoid**: Complex architectural discussions or advanced patterns
- **Include**: Step-by-step reasoning and simple examples
- **Emphasize**: Fundamental concepts like coupling, cohesion, and readability
""",
            
            UserExpertise.INTERMEDIATE: """
## Intermediate Analysis Focus:
- **Prioritize**: Design pattern applications and SOLID principles
- **Explain**: Trade-offs between different design approaches
- **Include**: Practical refactoring suggestions and best practices
- **Emphasize**: Code maintainability, extensibility, and common pitfalls
- **Connect**: Theory to real-world implementation scenarios
""",
            
            UserExpertise.ADVANCED: """
## Advanced Analysis Focus:
- **Prioritize**: Architectural implications and system-wide impacts
- **Explain**: Complex trade-offs and edge cases
- **Include**: Performance considerations and scalability analysis
- **Emphasize**: Enterprise patterns, domain modeling, and architectural styles
- **Discuss**: Advanced topics like event sourcing, CQRS, microservices patterns
- **Consider**: Team dynamics, technology constraints, and business context
"""
        }
        return focus_areas.get(expertise, focus_areas[UserExpertise.INTERMEDIATE])