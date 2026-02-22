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
from .consistency_checker import NarrativeConsistencyAnalyzer, run_narrative_tracker

# NEW: Import new modules for Phase 9 features
from .character_consistency import CharacterTracker, analyze_character_consistency
from .dialogue_improver import DialogueAnalyzer, analyze_dialogue_quality, get_dialogue_improvements
from .scene_feedback import SceneAnalyzer, analyze_scenes, get_scene_feedback
from .writer_modes import ModeAnalyzer, WriterMode, analyze_with_mode, get_available_modes

# Module-level exports for direct access
from . import text_analyzer
from . import enhancer
from . import style_transformer
from . import consistency_checker
from . import explanation
from . import grammar_checker
from . import concept_extractor
from . import antipatterns
from . import character_consistency
from . import dialogue_improver
from . import scene_feedback
from . import writer_modes

__all__ = [
    "WritingAssistant",
    "analyze_text",
    "NarrativeConsistencyAnalyzer",
    "text_analyzer",
    "enhancer",
    "style_transformer",
    "consistency_checker",
    "explanation",
    "grammar_checker",
    "concept_extractor",
    "antipatterns",
    # Phase 9: New modules
    "CharacterTracker",
    "analyze_character_consistency",
    "DialogueAnalyzer",
    "analyze_dialogue_quality",
    "get_dialogue_improvements",
    "SceneAnalyzer",
    "analyze_scenes",
    "get_scene_feedback",
    "ModeAnalyzer",
    "WriterMode",
    "analyze_with_mode",
    "get_available_modes",
    "character_consistency",
    "dialogue_improver",
    "scene_feedback",
    "writer_modes"
]

__version__ = "1.0.0"
__author__ = "Code Brothers"
