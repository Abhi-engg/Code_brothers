"""
NLP Engine Package
Writing Assistant - A comprehensive NLP pipeline for text analysis and improvement

Modules:
- text_analyzer: Core NLP processing (tokenization, POS, NER, sentence detection)
- enhancer: Readability scoring and flow analysis
- style_transformer: Style transformation (casual to formal, etc.)
- consistency_checker: Narrative consistency and entity tracking
- explanation: Human-readable explanation generation

Usage:
    from nlp_engine import WritingAssistant
    
    assistant = WritingAssistant()
    results = assistant.analyze("Your text here...")
    
    # Or for quick analysis:
    from nlp_engine import analyze_text
    results = analyze_text("Your text here...")
"""

from .pipeline import WritingAssistant, analyze_text
from .consistency_checker import NarrativeConsistencyAnalyzer

# Module-level exports for direct access
from . import text_analyzer
from . import enhancer
from . import style_transformer
from . import consistency_checker
from . import explanation

__all__ = [
    "WritingAssistant",
    "analyze_text",
    "NarrativeConsistencyAnalyzer",
    "text_analyzer",
    "enhancer",
    "style_transformer",
    "consistency_checker",
    "explanation"
]

__version__ = "1.0.0"
__author__ = "Code Brothers"
