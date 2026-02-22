"""
LLM Enhancement Service

Custom-built service for generating writing improvements using local LLM.
Contains all prompt templates, response parsing, and enhancement logic.

CUSTOM-BUILT COMPONENTS:
- Prompt templates for each issue type (15+ templates)
- Response validation and parsing
- Context building for better suggestions
- Quality scoring for generated content
- Fallback handling

EXTERNAL DEPENDENCY:
- Ollama LLM (via llm_client.py)
"""

import re
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from nlp_engine.llm_client import (
    get_client,
    OllamaClient,
    TaskType,
    GenerationResult,
    LLMConfig
)

logger = logging.getLogger(__name__)


class IssueType(str, Enum):
    """Types of writing issues that can be enhanced"""
    # Grammar issues
    GRAMMAR_ERROR = "grammar_error"
    PASSIVE_VOICE = "passive_voice"
    SUBJECT_VERB_AGREEMENT = "subject_verb_agreement"
    SENTENCE_FRAGMENT = "sentence_fragment"
    RUN_ON_SENTENCE = "run_on_sentence"
    
    # Style issues
    WORDY_SENTENCE = "wordy_sentence"
    WEAK_OPENING = "weak_opening"
    CLICHE = "cliche"
    REPEATED_WORD = "repeated_word"
    LONG_SENTENCE = "long_sentence"
    
    # Anti-patterns
    SHOW_DONT_TELL = "show_dont_tell"
    ADVERB_OVERUSE = "adverb_overuse"
    HEDGE_WORDS = "hedge_words"
    NOMINALIZATION = "nominalization"
    
    # General
    GENERAL_IMPROVEMENT = "general"


class StyleType(str, Enum):
    """Target styles for text transformation"""
    FORMAL = "formal"
    CASUAL = "casual"
    ACADEMIC = "academic"
    CREATIVE = "creative"
    PERSUASIVE = "persuasive"
    JOURNALISTIC = "journalistic"
    NARRATIVE = "narrative"


@dataclass
class EnhancementResult:
    """Result from enhancement generation"""
    original: str
    suggestion: str
    explanation: str
    issue_type: str
    confidence: float  # 0.0 to 1.0
    success: bool
    error: Optional[str] = None
    generation_time_ms: float = 0.0


@dataclass
class StyleTransformResult:
    """Result from style transformation"""
    original: str
    transformed: str
    source_style: str
    target_style: str
    changes_summary: str
    confidence: float
    success: bool
    error: Optional[str] = None
    generation_time_ms: float = 0.0


# ==================== CUSTOM PROMPT TEMPLATES ====================
# These are hand-crafted prompts optimized for writing assistance tasks

PROMPT_TEMPLATES = {
    IssueType.GRAMMAR_ERROR: """Fix the grammar error in this sentence while preserving its meaning and style.

Sentence: "{text}"

Provide only the corrected sentence, nothing else.""",

    IssueType.PASSIVE_VOICE: """Convert this passive voice sentence to active voice while keeping the same meaning.

Passive: "{text}"

Provide only the active voice version, nothing else.""",

    IssueType.SUBJECT_VERB_AGREEMENT: """Fix the subject-verb agreement error in this sentence.

Sentence: "{text}"

Provide only the corrected sentence, nothing else.""",

    IssueType.SENTENCE_FRAGMENT: """Complete this sentence fragment into a proper complete sentence.

Fragment: "{text}"
Context: "{context}"

Provide only the complete sentence, nothing else.""",

    IssueType.RUN_ON_SENTENCE: """Split this run-on sentence into properly punctuated shorter sentences.

Run-on: "{text}"

Provide only the corrected version with proper sentence breaks, nothing else.""",

    IssueType.WORDY_SENTENCE: """Make this sentence more concise while keeping its meaning.

Wordy: "{text}"

Provide only the concise version, nothing else.""",

    IssueType.WEAK_OPENING: """Rewrite this weak sentence opening to be more engaging and direct.

Weak: "{text}"

Provide only the improved sentence, nothing else.""",

    IssueType.CLICHE: """Replace the cliche in this sentence with fresh, original wording.

Sentence with cliche: "{text}"

Provide only the improved sentence, nothing else.""",

    IssueType.REPEATED_WORD: """Rewrite this sentence using a synonym to avoid word repetition.

Sentence: "{text}"
Repeated word: "{word}"

Provide only the rewritten sentence with variety, nothing else.""",

    IssueType.LONG_SENTENCE: """Break this long sentence into 2-3 shorter, clearer sentences.

Long sentence: "{text}"

Provide only the improved version with shorter sentences, nothing else.""",

    IssueType.SHOW_DONT_TELL: """Rewrite this "telling" sentence to "show" through action, dialogue, or sensory details.

Telling: "{text}"

Provide only the descriptive "showing" version, nothing else. Make it about 1-2 sentences.""",

    IssueType.ADVERB_OVERUSE: """Rewrite this sentence replacing the adverb with stronger verbs or descriptive phrases.

Sentence with adverb: "{text}"
Adverb to replace: "{word}"

Provide only the improved sentence without the adverb, nothing else.""",

    IssueType.HEDGE_WORDS: """Rewrite this sentence to be more confident by removing hedge words.

Hedging: "{text}"

Provide only the confident, direct version, nothing else.""",

    IssueType.NOMINALIZATION: """Rewrite this sentence using strong verbs instead of nominalizations.

Sentence: "{text}"

Provide only the version with active verbs, nothing else.""",

    IssueType.GENERAL_IMPROVEMENT: """Improve this sentence for clarity, style, and impact while preserving its meaning.

Original: "{text}"

Provide only the improved sentence, nothing else."""
}

# Explanation templates for each issue type
EXPLANATION_TEMPLATES = {
    IssueType.GRAMMAR_ERROR: "Fixed grammatical error for correct sentence structure.",
    IssueType.PASSIVE_VOICE: "Converted to active voice for more direct, engaging writing.",
    IssueType.SUBJECT_VERB_AGREEMENT: "Corrected subject-verb agreement for grammatical accuracy.",
    IssueType.SENTENCE_FRAGMENT: "Completed the fragment into a proper sentence.",
    IssueType.RUN_ON_SENTENCE: "Split into shorter sentences for better readability.",
    IssueType.WORDY_SENTENCE: "Made more concise by removing unnecessary words.",
    IssueType.WEAK_OPENING: "Strengthened the opening for better engagement.",
    IssueType.CLICHE: "Replaced cliche with original, fresh wording.",
    IssueType.REPEATED_WORD: "Used synonym to add variety and avoid repetition.",
    IssueType.LONG_SENTENCE: "Broke into shorter sentences for clarity.",
    IssueType.SHOW_DONT_TELL: "Rewrote to show through action/detail instead of telling.",
    IssueType.ADVERB_OVERUSE: "Replaced adverb with stronger verbs for vivid writing.",
    IssueType.HEDGE_WORDS: "Removed hedging for more confident, direct tone.",
    IssueType.NOMINALIZATION: "Used active verbs instead of noun forms.",
    IssueType.GENERAL_IMPROVEMENT: "Enhanced for better clarity and impact."
}


# ==================== STYLE TRANSFORMATION PROMPTS ====================
# Custom prompts for each target style transformation

STYLE_PROMPTS = {
    StyleType.FORMAL: """Transform this text to formal style. Use professional language, avoid contractions, 
and maintain a polished, business-appropriate tone.

Original text: "{text}"

Provide only the formal version, nothing else.""",

    StyleType.CASUAL: """Transform this text to casual, conversational style. Use contractions, 
friendly language, and a relaxed tone as if talking to a friend.

Original text: "{text}"

Provide only the casual version, nothing else.""",

    StyleType.ACADEMIC: """Transform this text to academic style. Use scholarly language, formal structure,
objective tone, and avoid first-person where possible. Include hedging language appropriate for academic writing.

Original text: "{text}"

Provide only the academic version, nothing else.""",

    StyleType.CREATIVE: """Transform this text to creative, literary style. Use vivid imagery, 
sensory details, varied sentence structure, and artistic expression.

Original text: "{text}"

Provide only the creative version, nothing else.""",

    StyleType.PERSUASIVE: """Transform this text to persuasive style. Use compelling language, 
rhetorical devices, strong calls to action, and emotional appeals.

Original text: "{text}"

Provide only the persuasive version, nothing else.""",

    StyleType.JOURNALISTIC: """Transform this text to journalistic style. Use the inverted pyramid structure,
objective reporting tone, concise sentences, and factual language.

Original text: "{text}"

Provide only the journalistic version, nothing else.""",

    StyleType.NARRATIVE: """Transform this text to narrative storytelling style. Use descriptive prose,
character-focused language, scene-setting details, and engaging storytelling techniques.

Original text: "{text}"

Provide only the narrative version, nothing else."""
}

STYLE_DESCRIPTIONS = {
    StyleType.FORMAL: "Professional, polished language suitable for business communication.",
    StyleType.CASUAL: "Relaxed, conversational tone as if talking to a friend.",
    StyleType.ACADEMIC: "Scholarly language with objective tone and hedging.",
    StyleType.CREATIVE: "Vivid, artistic expression with imagery and varied structure.",
    StyleType.PERSUASIVE: "Compelling language designed to convince and motivate.",
    StyleType.JOURNALISTIC: "Objective, concise reporting in inverted pyramid style.",
    StyleType.NARRATIVE: "Storytelling prose with description and character focus."
}


class LLMEnhancer:
    """
    Custom LLM Enhancement Service
    
    Provides intelligent writing suggestions using local LLM.
    All prompt engineering, response parsing, and quality control is custom-built.
    """
    
    def __init__(self, client: Optional[OllamaClient] = None):
        """Initialize enhancer with optional custom client"""
        self.client = client or get_client()
    
    def _build_prompt(
        self,
        issue_type: IssueType,
        text: str,
        context: str = "",
        word: str = ""
    ) -> str:
        """
        Build prompt from template with variables.
        
        Custom logic: Template selection, variable substitution, context handling.
        """
        template = PROMPT_TEMPLATES.get(issue_type, PROMPT_TEMPLATES[IssueType.GENERAL_IMPROVEMENT])
        
        return template.format(
            text=text,
            context=context or "No additional context provided.",
            word=word
        )
    
    def _validate_response(self, response: str, original: str) -> tuple[bool, float]:
        """
        Validate LLM response quality.
        
        Custom logic: Quality checks, confidence scoring.
        
        Returns:
            (is_valid, confidence_score)
        """
        if not response or len(response.strip()) < 3:
            return False, 0.0
        
        # Check response isn't just the original
        if response.strip().lower() == original.strip().lower():
            return False, 0.0
        
        # Check response isn't too long (likely hallucination)
        if len(response) > len(original) * 5:
            return False, 0.3
        
        # Check response isn't too short (likely truncated)
        if len(response) < len(original) * 0.2 and len(original) > 20:
            return False, 0.3
        
        # Calculate confidence based on various factors
        confidence = 0.8
        
        # Penalize if response contains common LLM artifacts
        artifacts = ["here is", "here's the", "sure,", "certainly", "i would", "the corrected"]
        for artifact in artifacts:
            if artifact in response.lower():
                confidence -= 0.2
                break
        
        # Penalize if response is wrapped in quotes (should be clean)
        if response.startswith('"') and response.endswith('"'):
            response = response[1:-1]
            confidence -= 0.1
        
        return True, max(0.0, min(1.0, confidence))
    
    def _clean_response(self, response: str) -> str:
        """
        Clean LLM response to extract just the rewritten text.
        
        Custom logic: Response parsing, artifact removal.
        """
        # Remove common prefixes
        prefixes = [
            "here is the", "here's the", "the corrected sentence is:",
            "corrected:", "improved:", "rewritten:", "active voice:",
            "concise version:", "sure,", "certainly,"
        ]
        
        cleaned = response.strip()
        lower_cleaned = cleaned.lower()
        
        for prefix in prefixes:
            if lower_cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                lower_cleaned = cleaned.lower()
        
        # Remove surrounding quotes
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        if cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]
        
        # Remove trailing explanations (after period + extra content)
        sentences = cleaned.split('. ')
        if len(sentences) > 3:
            # Likely includes explanation, take first few sentences
            cleaned = '. '.join(sentences[:3]) + '.'
        
        return cleaned.strip()
    
    def generate_rewrite(
        self,
        text: str,
        issue_type: str,
        context: str = "",
        word: str = ""
    ) -> EnhancementResult:
        """
        Generate a rewrite suggestion for the given issue.
        
        Args:
            text: The original text with the issue
            issue_type: Type of issue (from IssueType enum)
            context: Surrounding text for better context
            word: Specific word to address (for repeated word, adverb issues)
            
        Returns:
            EnhancementResult with suggestion and metadata
        """
        try:
            # Convert string to enum
            try:
                issue_enum = IssueType(issue_type)
            except ValueError:
                issue_enum = IssueType.GENERAL_IMPROVEMENT
            
            # Build prompt
            prompt = self._build_prompt(issue_enum, text, context, word)
            
            # Generate with LLM
            result = self.client.generate(
                prompt=prompt,
                task_type=TaskType.REWRITE,
                max_tokens=256
            )
            
            if not result.success:
                return EnhancementResult(
                    original=text,
                    suggestion="",
                    explanation="",
                    issue_type=issue_type,
                    confidence=0.0,
                    success=False,
                    error=result.error or "Generation failed"
                )
            
            # Clean and validate response
            cleaned = self._clean_response(result.text)
            is_valid, confidence = self._validate_response(cleaned, text)
            
            if not is_valid:
                return EnhancementResult(
                    original=text,
                    suggestion=cleaned,
                    explanation="Suggestion may need review.",
                    issue_type=issue_type,
                    confidence=confidence,
                    success=True,  # Still return, but with low confidence
                    generation_time_ms=result.total_duration_ms
                )
            
            # Get explanation
            explanation = EXPLANATION_TEMPLATES.get(
                issue_enum,
                "Enhanced for better writing quality."
            )
            
            return EnhancementResult(
                original=text,
                suggestion=cleaned,
                explanation=explanation,
                issue_type=issue_type,
                confidence=confidence,
                success=True,
                generation_time_ms=result.total_duration_ms
            )
            
        except Exception as e:
            logger.error(f"Enhancement failed: {e}")
            return EnhancementResult(
                original=text,
                suggestion="",
                explanation="",
                issue_type=issue_type,
                confidence=0.0,
                success=False,
                error=str(e)
            )
    
    async def generate_rewrite_async(
        self,
        text: str,
        issue_type: str,
        context: str = "",
        word: str = ""
    ) -> EnhancementResult:
        """Async version of generate_rewrite"""
        try:
            try:
                issue_enum = IssueType(issue_type)
            except ValueError:
                issue_enum = IssueType.GENERAL_IMPROVEMENT
            
            prompt = self._build_prompt(issue_enum, text, context, word)
            
            result = await self.client.generate_async(
                prompt=prompt,
                task_type=TaskType.REWRITE,
                max_tokens=256
            )
            
            if not result.success:
                return EnhancementResult(
                    original=text,
                    suggestion="",
                    explanation="",
                    issue_type=issue_type,
                    confidence=0.0,
                    success=False,
                    error=result.error or "Generation failed"
                )
            
            cleaned = self._clean_response(result.text)
            is_valid, confidence = self._validate_response(cleaned, text)
            
            explanation = EXPLANATION_TEMPLATES.get(
                issue_enum,
                "Enhanced for better writing quality."
            )
            
            return EnhancementResult(
                original=text,
                suggestion=cleaned,
                explanation=explanation,
                issue_type=issue_type,
                confidence=confidence,
                success=True,
                generation_time_ms=result.total_duration_ms
            )
            
        except Exception as e:
            logger.error(f"Async enhancement failed: {e}")
            return EnhancementResult(
                original=text,
                suggestion="",
                explanation="",
                issue_type=issue_type,
                confidence=0.0,
                success=False,
                error=str(e)
            )
    
    def generate_batch_rewrites(
        self,
        issues: List[Dict[str, Any]],
        max_issues: int = 5
    ) -> List[EnhancementResult]:
        """
        Generate rewrites for multiple issues efficiently.
        
        Uses a single LLM call with multiple issues in the prompt.
        
        Args:
            issues: List of {"text": str, "issue_type": str, "context": str, "word": str}
            max_issues: Maximum issues to process (default 5)
            
        Returns:
            List of EnhancementResult for each issue
        """
        if not issues:
            return []
        
        # Limit issues
        issues = issues[:max_issues]
        
        # Build batch prompt
        batch_prompt = """Improve each of the following sentences. For each numbered item, provide only the improved sentence, nothing else.

"""
        for i, issue in enumerate(issues, 1):
            issue_type = issue.get("issue_type", "general")
            text = issue.get("text", "")
            batch_prompt += f"{i}. ({issue_type}) {text}\n"
        
        batch_prompt += "\nImprovements:\n"
        
        try:
            result = self.client.generate(
                prompt=batch_prompt,
                task_type=TaskType.REWRITE,
                max_tokens=512
            )
            
            if not result.success:
                # Return individual failures
                return [
                    EnhancementResult(
                        original=issue.get("text", ""),
                        suggestion="",
                        explanation="",
                        issue_type=issue.get("issue_type", "general"),
                        confidence=0.0,
                        success=False,
                        error=result.error
                    )
                    for issue in issues
                ]
            
            # Parse batch response
            lines = result.text.strip().split('\n')
            results = []
            
            for i, issue in enumerate(issues):
                # Try to find matching line
                suggestion = ""
                for line in lines:
                    # Match lines starting with number
                    if line.strip().startswith(f"{i+1}.") or line.strip().startswith(f"{i+1})"):
                        suggestion = re.sub(r'^[\d]+[\.\)]\s*', '', line.strip())
                        break
                
                # If no numbered match, try sequential
                if not suggestion and i < len(lines):
                    suggestion = self._clean_response(lines[i])
                
                is_valid, confidence = self._validate_response(suggestion, issue.get("text", ""))
                
                issue_enum = IssueType.GENERAL_IMPROVEMENT
                try:
                    issue_enum = IssueType(issue.get("issue_type", "general"))
                except ValueError:
                    pass
                
                results.append(EnhancementResult(
                    original=issue.get("text", ""),
                    suggestion=suggestion,
                    explanation=EXPLANATION_TEMPLATES.get(issue_enum, "Enhanced for better quality."),
                    issue_type=issue.get("issue_type", "general"),
                    confidence=confidence,
                    success=bool(suggestion),
                    generation_time_ms=result.total_duration_ms / len(issues)
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Batch enhancement failed: {e}")
            return [
                EnhancementResult(
                    original=issue.get("text", ""),
                    suggestion="",
                    explanation="",
                    issue_type=issue.get("issue_type", "general"),
                    confidence=0.0,
                    success=False,
                    error=str(e)
                )
                for issue in issues
            ]
    
    # ==================== Style Transformation ====================
    
    def transform_style(
        self,
        text: str,
        target_style: str,
        source_style: str = "auto"
    ) -> StyleTransformResult:
        """
        Transform text to a different writing style using LLM.
        
        This is the "deep transform" mode that uses LLM for full sentence-level
        transformation, producing more natural results than rule-based approach.
        
        Args:
            text: Text to transform
            target_style: Target style (formal, casual, academic, creative, persuasive, journalistic, narrative)
            source_style: Source style hint (optional, "auto" to detect)
            
        Returns:
            StyleTransformResult with transformed text and metadata
        """
        try:
            # Convert to enum
            try:
                style_enum = StyleType(target_style.lower())
            except ValueError:
                style_enum = StyleType.FORMAL
            
            # Get prompt template
            prompt = STYLE_PROMPTS.get(style_enum, STYLE_PROMPTS[StyleType.FORMAL])
            prompt = prompt.format(text=text)
            
            # Generate transformation
            result = self.client.generate(
                prompt=prompt,
                task_type=TaskType.STYLE_TRANSFORM,
                max_tokens=1024  # Allow longer output for style transforms
            )
            
            if not result.success:
                return StyleTransformResult(
                    original=text,
                    transformed="",
                    source_style=source_style,
                    target_style=target_style,
                    changes_summary="",
                    confidence=0.0,
                    success=False,
                    error=result.error or "Transformation failed"
                )
            
            # Clean response
            transformed = self._clean_response(result.text)
            
            # Validate
            is_valid, confidence = self._validate_style_transform(transformed, text, style_enum)
            
            # Get style description
            changes_summary = STYLE_DESCRIPTIONS.get(style_enum, "Style transformation applied.")
            
            return StyleTransformResult(
                original=text,
                transformed=transformed,
                source_style=source_style,
                target_style=target_style,
                changes_summary=changes_summary,
                confidence=confidence,
                success=True,
                generation_time_ms=result.total_duration_ms
            )
            
        except Exception as e:
            logger.error(f"Style transformation failed: {e}")
            return StyleTransformResult(
                original=text,
                transformed="",
                source_style=source_style,
                target_style=target_style,
                changes_summary="",
                confidence=0.0,
                success=False,
                error=str(e)
            )
    
    async def transform_style_async(
        self,
        text: str,
        target_style: str,
        source_style: str = "auto"
    ) -> StyleTransformResult:
        """Async version of transform_style"""
        try:
            try:
                style_enum = StyleType(target_style.lower())
            except ValueError:
                style_enum = StyleType.FORMAL
            
            prompt = STYLE_PROMPTS.get(style_enum, STYLE_PROMPTS[StyleType.FORMAL])
            prompt = prompt.format(text=text)
            
            result = await self.client.generate_async(
                prompt=prompt,
                task_type=TaskType.STYLE_TRANSFORM,
                max_tokens=1024
            )
            
            if not result.success:
                return StyleTransformResult(
                    original=text,
                    transformed="",
                    source_style=source_style,
                    target_style=target_style,
                    changes_summary="",
                    confidence=0.0,
                    success=False,
                    error=result.error or "Transformation failed"
                )
            
            transformed = self._clean_response(result.text)
            is_valid, confidence = self._validate_style_transform(transformed, text, style_enum)
            changes_summary = STYLE_DESCRIPTIONS.get(style_enum, "Style transformation applied.")
            
            return StyleTransformResult(
                original=text,
                transformed=transformed,
                source_style=source_style,
                target_style=target_style,
                changes_summary=changes_summary,
                confidence=confidence,
                success=True,
                generation_time_ms=result.total_duration_ms
            )
            
        except Exception as e:
            logger.error(f"Async style transformation failed: {e}")
            return StyleTransformResult(
                original=text,
                transformed="",
                source_style=source_style,
                target_style=target_style,
                changes_summary="",
                confidence=0.0,
                success=False,
                error=str(e)
            )
    
    def _validate_style_transform(
        self,
        transformed: str,
        original: str,
        target_style: StyleType
    ) -> tuple[bool, float]:
        """
        Validate style transformation quality.
        
        Custom logic: Check that transformation is meaningful and appropriate.
        
        Returns:
            (is_valid, confidence_score)
        """
        if not transformed or len(transformed.strip()) < 5:
            return False, 0.0
        
        # Check it's not identical (transformation should change something)
        if transformed.strip().lower() == original.strip().lower():
            return False, 0.2
        
        # Check reasonable length relationship
        len_ratio = len(transformed) / max(len(original), 1)
        if len_ratio > 3.0 or len_ratio < 0.2:
            return False, 0.3
        
        confidence = 0.75
        
        # Style-specific validation
        if target_style == StyleType.FORMAL:
            # Check for contractions (should be fewer)
            contractions = ["'s", "'t", "'re", "'ve", "'ll", "'d", "n't"]
            if any(c in transformed.lower() for c in contractions):
                confidence -= 0.1
        
        elif target_style == StyleType.CASUAL:
            # Casual should have some informal markers
            informal_markers = ["'s", "'t", "'re", "!", "you", "gonna", "kinda"]
            if not any(m in transformed.lower() for m in informal_markers):
                confidence -= 0.1
        
        elif target_style == StyleType.ACADEMIC:
            # Academic should avoid first person
            first_person = [" i ", "i'm", "i've", "my ", "we "]
            has_first_person = any(fp in transformed.lower() for fp in first_person)
            if has_first_person:
                confidence -= 0.15
        
        # Check for LLM artifacts
        artifacts = ["here is", "here's the", "sure,", "certainly"]
        for artifact in artifacts:
            if artifact in transformed.lower():
                confidence -= 0.2
                break
        
        return True, max(0.0, min(1.0, confidence))


# ==================== Global Instance ====================

_enhancer: Optional[LLMEnhancer] = None


def get_enhancer() -> LLMEnhancer:
    """Get or create the default enhancer instance"""
    global _enhancer
    if _enhancer is None:
        _enhancer = LLMEnhancer()
    return _enhancer


# ==================== Convenience Functions ====================

def enhance_text(
    text: str,
    issue_type: str = "general",
    context: str = "",
    word: str = ""
) -> EnhancementResult:
    """Enhance text using the default enhancer"""
    return get_enhancer().generate_rewrite(text, issue_type, context, word)


def enhance_batch(issues: List[Dict[str, Any]]) -> List[EnhancementResult]:
    """Enhance multiple issues using the default enhancer"""
    return get_enhancer().generate_batch_rewrites(issues)


def transform_style_deep(
    text: str,
    target_style: str,
    source_style: str = "auto"
) -> StyleTransformResult:
    """Transform text style using LLM (deep mode)"""
    return get_enhancer().transform_style(text, target_style, source_style)


# ==================== Testing ====================

if __name__ == "__main__":
    """Test the LLM enhancer"""
    print("Testing LLM Enhancer...")
    print("=" * 60)
    
    # Test cases for each issue type
    test_cases = [
        {
            "text": "The ball was thrown by the boy.",
            "issue_type": "passive_voice",
            "expected": "Active voice"
        },
        {
            "text": "She walked very quickly to the store.",
            "issue_type": "adverb_overuse",
            "word": "very quickly",
            "expected": "Stronger verb"
        },
        {
            "text": "He was sad.",
            "issue_type": "show_dont_tell",
            "expected": "Descriptive showing"
        },
        {
            "text": "The implementation of the algorithm was completed.",
            "issue_type": "nominalization",
            "expected": "Active verb"
        },
        {
            "text": "It is possible that the results might perhaps indicate a trend.",
            "issue_type": "hedge_words",
            "expected": "Confident statement"
        }
    ]
    
    enhancer = get_enhancer()
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['issue_type']}")
        print(f"  Original: {test['text']}")
        
        result = enhancer.generate_rewrite(
            text=test['text'],
            issue_type=test['issue_type'],
            word=test.get('word', '')
        )
        
        print(f"  Success: {result.success}")
        print(f"  Suggestion: {result.suggestion}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Time: {result.generation_time_ms:.0f}ms")
        print(f"  Explanation: {result.explanation}")
    
    # Test batch enhancement
    print("\n" + "=" * 60)
    print("Testing Batch Enhancement...")
    
    batch_issues = [
        {"text": "The door was opened by him.", "issue_type": "passive_voice"},
        {"text": "She ran really fast.", "issue_type": "adverb_overuse", "word": "really fast"},
        {"text": "He felt angry.", "issue_type": "show_dont_tell"}
    ]
    
    batch_results = enhancer.generate_batch_rewrites(batch_issues)
    
    for i, result in enumerate(batch_results, 1):
        print(f"\nBatch {i}:")
        print(f"  Original: {result.original}")
        print(f"  Suggestion: {result.suggestion}")
        print(f"  Confidence: {result.confidence:.2f}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
