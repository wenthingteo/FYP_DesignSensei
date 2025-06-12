from typing import Dict
from backend.prompt_engine.templates.base_template import BaseTemplate, UserExpertise, ResponseLength

class ComparisonTemplate(BaseTemplate):
    """Template for comparison-type questions about software design patterns, principles, and architectures"""
    
    def generate_prompt(self, user_query: str, graphrag_results: Dict, context: Dict,
                       user_expertise: UserExpertise = UserExpertise.INTERMEDIATE,
                       response_length: ResponseLength = ResponseLength.MEDIUM) -> str:
        
        knowledge_context = self._format_graphrag_context(graphrag_results)
        conversation_context = self._format_conversation_context(context)
        expertise_modifier = self._get_expertise_modifier(user_expertise)
        length_modifier = self._get_length_modifier(response_length)
        comparison_focus = self._get_comparison_focus(user_expertise)
        comparison_depth = self._get_comparison_depth(user_expertise)
        
        prompt = f"""
{self.system_role}

{self.base_instructions}

TASK TYPE: SOFTWARE DESIGN COMPARISON ANALYSIS
USER EXPERTISE LEVEL: {user_expertise.value.upper()}
{expertise_modifier}

RESPONSE LENGTH REQUIREMENTS:
{length_modifier}

{knowledge_context}

{conversation_context}

USER QUESTION: "{user_query}"

COMPARISON TASK INSTRUCTIONS:
You are conducting a comprehensive comparison of software design concepts. Follow this structured analytical approach:

## Comparison Framework:

### 1. **Concept Definition & Overview**
- **Define** each concept being compared with clear, precise definitions
- **Bold** all pattern/principle names throughout your response
- Provide brief context on the origin and purpose of each concept
- Cite sources for definitions using [Source: filename, page X]

### 2. **Detailed Feature Analysis**
Create a systematic comparison covering:
- **Core Characteristics**: What makes each approach unique
- **Structural Differences**: How they're implemented differently
- **Behavioral Differences**: How they function in practice
- **Complexity Levels**: Implementation and maintenance complexity

### 3. **Similarities & Common Ground**
- Identify **shared characteristics** and common use cases
- Explain how they relate to the same design principles
- Discuss scenarios where they might be used together
- Highlight overlapping benefits and goals

### 4. **Key Differences & Distinctions**
- Create a **clear comparison table** or structured list
- Highlight **critical differences** that affect decision-making
- Explain the implications of each difference
- Use code examples to illustrate differences when helpful

### 5. **Contextual Application Guidelines**
{comparison_depth}
- **When to use Approach A**: Specific scenarios, requirements, constraints
- **When to use Approach B**: Different scenarios and trade-offs
- **When NOT to use either**: Situations where alternatives are better
- Include **decision trees** or selection criteria

### 6. **Trade-off Analysis**
- **Performance implications**: Speed, memory, scalability
- **Maintainability factors**: Code complexity, testing, debugging
- **Development considerations**: Learning curve, team expertise, timeline
- **Long-term implications**: Evolution, extensibility, technical debt

### 7. **Practical Examples & Use Cases**
- Provide **concrete code examples** for each approach
- Show **real-world scenarios** where each excels
- Include **before/after** comparisons when refactoring
- Demonstrate **integration patterns** with other design elements

### 8. **Selection Criteria & Recommendations**
- Present **clear decision framework** for choosing between options
- List **key questions** to ask when making the choice
- Provide **priority-based recommendations** (performance vs. maintainability)
- Include **migration considerations** if switching between approaches

{comparison_focus}

## Formatting Requirements:
- Use **comparison tables** where appropriate
- Create **side-by-side code examples** with clear labels
- Use **pros/cons lists** with bullet points
- Include **visual indicators** (✅ advantages, ❌ disadvantages, ⚠️ considerations)
- Structure with clear markdown headings (# ## ###)

## Educational Requirements:
- Connect comparisons to **fundamental design principles**
- Reference **established patterns and practices** from your knowledge base
- Explain **why** differences matter, not just what they are
- Help users develop **decision-making skills** for future scenarios
- Encourage **critical thinking** about design choices

Begin your comprehensive comparison analysis now:
"""
        return prompt.strip()
    
    def _get_comparison_focus(self, expertise: UserExpertise) -> str:
        """Get expertise-specific comparison focus areas"""
        focus_areas = {
            UserExpertise.BEGINNER: """
## Beginner Comparison Focus:
- **Emphasize**: Basic differences and simple use cases
- **Use**: Clear, non-technical language for complex concepts
- **Include**: Step-by-step decision-making guidance
- **Focus on**: Fundamental concepts like inheritance vs. composition
- **Provide**: Simple code examples with extensive explanations
- **Avoid**: Deep architectural discussions or advanced edge cases
- **Highlight**: Most common scenarios and typical choices
""",
            
            UserExpertise.INTERMEDIATE: """
## Intermediate Comparison Focus:
- **Emphasize**: Practical implications and real-world trade-offs
- **Include**: Multiple implementation approaches and variations
- **Focus on**: Design pattern comparisons and SOLID principle applications
- **Provide**: Realistic code examples with moderate complexity
- **Discuss**: Common pitfalls and best practices for each approach
- **Connect**: Choices to maintainability and team productivity
- **Show**: How decisions impact larger system architecture
""",
            
            UserExpertise.ADVANCED: """
## Advanced Comparison Focus:
- **Emphasize**: Architectural implications and system-wide impacts
- **Include**: Performance benchmarks and scalability considerations
- **Focus on**: Enterprise patterns, advanced architectures, and complex scenarios
- **Provide**: Production-ready examples with comprehensive error handling
- **Discuss**: Framework-specific implementations and integration challenges
- **Analyze**: Long-term evolution and maintenance implications
- **Consider**: Team dynamics, organizational constraints, and business context
"""
        }
        return focus_areas.get(expertise, focus_areas[UserExpertise.INTERMEDIATE])
    
    def _get_comparison_depth(self, expertise: UserExpertise) -> str:
        """Get expertise-appropriate comparison depth guidelines"""
        depth_levels = {
            UserExpertise.BEGINNER: """
**Comparison Depth for Beginners:**
- Focus on **2-3 key scenarios** per approach
- Use **simple, relatable examples** (e.g., car vs. bicycle analogies)
- Provide **clear yes/no decision criteria**
- Avoid overwhelming with too many edge cases""",
            
            UserExpertise.INTERMEDIATE: """
**Comparison Depth for Intermediate:**
- Cover **4-6 realistic scenarios** with nuanced considerations
- Include **moderate complexity examples** from typical applications
- Provide **weighted decision criteria** (priority-based choices)
- Balance depth with practical applicability""",
            
            UserExpertise.ADVANCED: """
**Comparison Depth for Advanced:**
- Analyze **comprehensive scenario matrices** with multiple variables
- Include **enterprise-scale examples** with complex constraints
- Provide **multi-dimensional decision frameworks** with trade-off analysis
- Cover edge cases and advanced integration scenarios"""
        }
        return depth_levels.get(expertise, depth_levels[UserExpertise.INTERMEDIATE])