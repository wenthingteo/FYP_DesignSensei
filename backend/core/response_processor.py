"""
Response Processor Module
Handles post-processing of LLM-generated responses to ensure quality and consistency.
"""

import re
import logging

logger = logging.getLogger(__name__)


class ResponseProcessor:
    """
    Post-processes LLM responses with:
    1. Validation (empty/fallback detection)
    2. Code block formatting (Java/Python/etc.)
    3. Redundancy removal
    4. Markdown enhancement
    """
    
    FALLBACK_PHRASES = [
        "I don't know",
        "I am not sure",
        "cannot answer",
        "I'm not certain",
        "I don't have enough information",
        "I cannot provide"
    ]
    
    MIN_RESPONSE_LENGTH = 50
    MAX_RESPONSE_LENGTH = 5000 

    @staticmethod
    def process(response: str, language_hint: str = "java") -> str:
        """
        Main processing pipeline for LLM responses.
        
        Args:
            response: Raw LLM response text
            language_hint: Programming language for code block detection (default: "java")
            
        Returns:
            Processed and validated response text
        """
        logger.info(f"Processing response (length: {len(response)} chars)")
        
        # 1. Validation
        if not ResponseProcessor._is_valid_response(response):
            logger.warning("Invalid response detected, returning fallback message")
            return "⚠️ I apologize, but I couldn't generate a proper response. Could you please rephrase your question or provide more context?"
        
        # 2. Remove fallback phrases (partial failures)
        response = ResponseProcessor._remove_fallbacks(response)
        
        # 3. Wrap code blocks
        response = ResponseProcessor._wrap_code_blocks(response, language_hint)
        
        # 4. Remove redundant lines
        response = ResponseProcessor._remove_redundancy(response)
        
        # 5. Clean up excessive whitespace
        response = ResponseProcessor._clean_whitespace(response)
        
        # 6. Truncate long responses for device-friendly display
        response = ResponseProcessor._truncate_for_display(response)
        
        logger.info(f"Response processed successfully (final length: {len(response)} chars)")
        return response.strip()

    @staticmethod
    def _is_valid_response(text: str) -> bool:
        """
        Validates response is not empty or too short/long.
        """
        if not text or not text.strip():
            return False
        
        text_length = len(text.strip())
        
        if text_length < ResponseProcessor.MIN_RESPONSE_LENGTH:
            logger.warning(f"Response too short: {text_length} chars")
            return False
        
        if text_length > ResponseProcessor.MAX_RESPONSE_LENGTH:
            logger.warning(f"Response too long: {text_length} chars (truncating)")
            # Don't reject, just flag for review
        
        return True

    @staticmethod
    def _remove_fallbacks(text: str) -> str:
        """
        Removes common fallback phrases that indicate LLM uncertainty.
        """
        original_text = text
        for phrase in ResponseProcessor.FALLBACK_PHRASES:
            # Case-insensitive removal
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            text = pattern.sub("", text)
        
        if text != original_text:
            logger.debug("Removed fallback phrases from response")
        
        return text

    @staticmethod
    def _wrap_code_blocks(text: str, language: str = "java") -> str:
        """
        Detects code-like patterns and wraps them in proper markdown code blocks.
        Supports Java, Python, JavaScript, and generic code.
        """
        # Java class/method pattern
        java_pattern = r"(?<!```)(public|private|protected|class|interface|enum)\s+(?:class|interface|enum)?\s*\w+[\s\S]*?\{[\s\S]*?\n\}"
        
        # Python class/function pattern
        python_pattern = r"(?<!```)(def|class)\s+\w+[\s\S]*?:\s*\n(?:\s{4}|\t)[\s\S]*?(?=\n(?!\s{4}|\t)\S|\Z)"
        
        # Generic code block (multiple lines with common code indicators)
        generic_pattern = r"(?<!```)(?:(?:public|private|def|class|function|const|let|var|if|for|while)\s+[\s\S]{20,}?\n)"
        
        patterns = {
            'java': java_pattern,
            'python': python_pattern,
            'generic': generic_pattern
        }
        
        def wrap_code(match):
            code = match.group(0)
            # Check if already wrapped
            if "```" in code or code.strip().startswith("```"):
                return code
            
            # Clean and wrap
            code = code.strip()
            logger.debug(f"Wrapping code block in ```{language}")
            return f"\n```{language}\n{code}\n```\n"
        
        # Try language-specific pattern first
        if language.lower() in patterns:
            text = re.sub(patterns[language.lower()], wrap_code, text, flags=re.MULTILINE)
        
        # Fallback to generic pattern
        text = re.sub(patterns['generic'], wrap_code, text, flags=re.MULTILINE)
        
        return text

    @staticmethod
    def _remove_redundancy(text: str) -> str:
        """
        Removes consecutive duplicate lines while preserving structure.
        Does NOT remove intentional repetition like headers or bullet points.
        """
        lines = text.splitlines()
        cleaned = []
        prev_line = None
        
        for line in lines:
            stripped = line.strip()
            
            # Keep empty lines for formatting
            if not stripped:
                cleaned.append(line)
                prev_line = None
                continue
            
            # Keep markdown special lines (headers, lists, etc.)
            if stripped.startswith(('#', '-', '*', '>', '```', '|')):
                cleaned.append(line)
                prev_line = stripped
                continue
            
            # Remove consecutive duplicates
            if stripped != prev_line:
                cleaned.append(line)
                prev_line = stripped
        
        removed_count = len(lines) - len(cleaned)
        if removed_count > 0:
            logger.debug(f"Removed {removed_count} duplicate lines")
        
        return "\n".join(cleaned)

    @staticmethod
    def _clean_whitespace(text: str) -> str:
        """
        Cleans up excessive whitespace while preserving markdown formatting.
        """
        # Remove trailing whitespace from each line
        lines = [line.rstrip() for line in text.splitlines()]
        
        # Join lines
        text = "\n".join(lines)
        
        # Replace 3+ consecutive newlines with just 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    @staticmethod
    def enhance_structure(text: str, intent_type: str = "explanation") -> str:
        """
        Optional: Add structural improvements based on intent.
        Can be called separately if needed for specific intents.
        
        Args:
            text: Response text
            intent_type: Question intent (explanation, comparison, application, etc.)
            
        Returns:
            Structurally enhanced text
        """
        # Check if response already has clear structure
        has_headers = bool(re.search(r'^#{1,3}\s+\w+', text, re.MULTILINE))
        
        if not has_headers and intent_type == "explanation":
            # Add basic structure for explanations
            logger.debug("Adding basic explanation structure")
            text = f"## Overview\n\n{text}"
        
        return text


# Example usage and testing
if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(level=logging.DEBUG)
    
    # Test case 1: Code wrapping
    test_response_1 = """
    Here's an example:
    
    public class Singleton {
        private static Singleton instance;
        
        private Singleton() {}
        
        public static Singleton getInstance() {
            if (instance == null) {
                instance = new Singleton();
            }
            return instance;
        }
    }
    
    This ensures only one instance exists.
    """
    
    processed_1 = ResponseProcessor.process(test_response_1, language_hint="java")
    print("=== Test 1: Code Wrapping ===")
    print(processed_1)
    print()
    
    # Test case 2: Fallback removal
    test_response_2 = """
    I'm not certain about this, but here's what I know:
    
    The Factory pattern is a creational design pattern.
    The Factory pattern is a creational design pattern.
    
    I cannot provide more details without more context.
    """
    
    processed_2 = ResponseProcessor.process(test_response_2)
    print("=== Test 2: Fallback & Redundancy Removal ===")
    print(processed_2)
    print()
    
    # Test case 3: Invalid response
    test_response_3 = ""
    
    processed_3 = ResponseProcessor.process(test_response_3)
    print("=== Test 3: Invalid Response ===")
    print(processed_3)
