"""
Story Assistant Module

Custom-built service for intelligent story continuation using local LLM.
Contains context extraction, narrative analysis, and continuation generation.

CUSTOM-BUILT COMPONENTS:
- Plot element extraction (events, conflicts, settings)
- Character extraction and tracking
- Narrative style detection (POV, tense, tone)
- Context compression for long texts
- Continuation prompt building
- Multi-option generation
- Streaming support

EXTERNAL DEPENDENCY:
- Ollama LLM (via llm_client.py)
"""

import re
import logging
import json
from typing import Optional, Dict, Any, List, Generator, Tuple, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ==================== NARRATIVE ENUMS ====================

class POVType(str, Enum):
    """Point of View types"""
    FIRST_PERSON = "first_person"
    SECOND_PERSON = "second_person"
    THIRD_PERSON_LIMITED = "third_person_limited"
    THIRD_PERSON_OMNISCIENT = "third_person_omniscient"
    UNKNOWN = "unknown"


class TenseType(str, Enum):
    """Narrative tense types"""
    PAST = "past"
    PRESENT = "present"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class ToneType(str, Enum):
    """Narrative tone types"""
    SERIOUS = "serious"
    HUMOROUS = "humorous"
    DARK = "dark"
    LIGHTHEARTED = "lighthearted"
    SUSPENSEFUL = "suspenseful"
    ROMANTIC = "romantic"
    MELANCHOLIC = "melancholic"
    ADVENTUROUS = "adventurous"
    MYSTERIOUS = "mysterious"
    NEUTRAL = "neutral"


class GenreHint(str, Enum):
    """Genre hints for continuation style"""
    FANTASY = "fantasy"
    SCIFI = "sci-fi"
    ROMANCE = "romance"
    THRILLER = "thriller"
    MYSTERY = "mystery"
    HORROR = "horror"
    LITERARY = "literary"
    ADVENTURE = "adventure"
    DRAMA = "drama"
    GENERAL = "general"


# ==================== DATA CLASSES ====================

@dataclass
class Character:
    """Extracted character information"""
    name: str
    mentions: int = 1
    first_appearance: int = 0  # Sentence index
    attributes: List[str] = field(default_factory=list)
    relationships: Dict[str, str] = field(default_factory=dict)
    is_protagonist: bool = False


@dataclass
class PlotElement:
    """Extracted plot element"""
    element_type: str  # event, conflict, setting, object
    text: str
    sentence_index: int
    importance: float = 0.5  # 0.0 to 1.0


@dataclass
class NarrativeContext:
    """Full narrative context extracted from story"""
    characters: List[Character]
    plot_elements: List[PlotElement]
    pov: POVType
    tense: TenseType
    tone: ToneType
    genre_hint: GenreHint
    themes: List[str]
    setting_description: str
    recent_events: List[str]
    unresolved_threads: List[str]
    word_count: int
    compressed_summary: str = ""


@dataclass
class ContinuationResult:
    """Result from story continuation"""
    continuation: str
    context_used: Dict[str, Any]
    pov: str
    tense: str
    tone: str
    generation_time_ms: float
    tokens_generated: int
    success: bool
    error: Optional[str] = None


@dataclass 
class ContinuationOption:
    """Single continuation option with metadata"""
    text: str
    direction: str  # e.g., "action", "dialogue", "description", "twist"
    confidence: float


# ==================== PROMPT TEMPLATES ====================
# Custom prompts optimized for story continuation

CONTINUATION_SYSTEM_PROMPT = """You are a creative writing assistant continuing a story. Your role is to:
1. Match the exact writing style, POV, and tense of the original
2. Maintain character consistency and voice
3. Continue the narrative naturally from where it left off
4. Create engaging, well-crafted prose
5. Never explain or meta-comment about the story - just write the continuation

CRITICAL: Output ONLY the story continuation. No greetings, explanations, or meta-text."""

CONTINUATION_PROMPT = """Continue this story naturally. Match the style, POV ({pov}), and tense ({tense}).

STORY CONTEXT:
{context}

CHARACTERS:
{characters}

SETTING:
{setting}

RECENT EVENTS:
{recent_events}

{themes_section}

THE STORY SO FAR (last portion):
---
{story_excerpt}
---

Continue the story from exactly where it ended. Write {word_target} words.
Match the {tone} tone. Output ONLY the story continuation:"""

# Separate prompts for each continuation direction (more reliable with smaller models)
OPTION_PROMPTS = {
    "action": """Continue this story with ACTION and PLOT ADVANCEMENT.
Move the plot forward with events, decisions, or revelations.

{context}

STORY:
{story_excerpt}

Continue with action/plot (2-3 sentences only). Output ONLY the continuation:""",
    
    "dialogue": """Continue this story with CHARACTER DIALOGUE and INTERACTION.
Add meaningful conversation that reveals character or advances relationships.

{context}

STORY:
{story_excerpt}

Continue with dialogue (2-3 sentences only). Output ONLY the continuation:""",
    
    "description": """Continue this story with ATMOSPHERIC DESCRIPTION.
Build mood, setting, or tension through sensory details.

{context}

STORY:
{story_excerpt}

Continue with description (2-3 sentences only). Output ONLY the continuation:""",
    
    "twist": """Continue this story with a SURPRISING TWIST or REVELATION.
Introduce something unexpected that changes the situation.

{context}

STORY:
{story_excerpt}

Continue with a twist (2-3 sentences only). Output ONLY the continuation:"""
}

SUMMARY_PROMPT = """Summarize this story excerpt, preserving key plot points, character details, and setting.
Focus on: main events, character motivations, unresolved conflicts, and important details.
Keep it concise but comprehensive (max 200 words).

STORY:
{story}

SUMMARY:"""


# ==================== ANALYSIS FUNCTIONS ====================

def detect_pov(text: str) -> POVType:
    """
    Detect the point of view of the narrative.
    
    Custom heuristic based on pronoun usage patterns.
    """
    # Count pronouns
    first_person = len(re.findall(r'\b(I|me|my|mine|myself|we|us|our|ours)\b', text, re.I))
    second_person = len(re.findall(r'\b(you|your|yours|yourself)\b', text, re.I))
    third_person = len(re.findall(r'\b(he|she|they|him|her|them|his|hers|their|theirs)\b', text, re.I))
    
    word_count = len(text.split())
    
    # Calculate ratios
    first_ratio = first_person / max(word_count, 1) * 100
    second_ratio = second_person / max(word_count, 1) * 100
    third_ratio = third_person / max(word_count, 1) * 100
    
    # Determine POV
    if first_ratio > 2.0 and first_ratio > second_ratio and first_ratio > third_ratio:
        return POVType.FIRST_PERSON
    elif second_ratio > 2.0 and second_ratio > first_ratio:
        return POVType.SECOND_PERSON
    elif third_ratio > 1.5:
        # Check for omniscient markers (multiple character thoughts, wide scope)
        thought_verbs = len(re.findall(r'\b(thought|felt|knew|wondered|realized)\b', text, re.I))
        if thought_verbs > 3 and third_person > 10:
            return POVType.THIRD_PERSON_OMNISCIENT
        return POVType.THIRD_PERSON_LIMITED
    
    return POVType.UNKNOWN


def detect_tense(text: str) -> TenseType:
    """
    Detect the primary narrative tense.
    
    Custom heuristic based on verb patterns.
    """
    # Past tense markers
    past_patterns = [
        r'\b\w+ed\b',  # Regular past tense verbs
        r'\bwas\b', r'\bwere\b', r'\bhad\b',
        r'\bsaid\b', r'\bwent\b', r'\bcame\b', r'\btook\b', r'\bmade\b',
        r'\bsaw\b', r'\bknew\b', r'\bthought\b', r'\bfelt\b'
    ]
    
    # Present tense markers
    present_patterns = [
        r'\b(is|are|am)\b(?!\s+\w+ing)',  # Be verbs not progressive
        r'\b(says?|goes?|comes?|takes?|makes?)\b',
        r'\b(sees?|knows?|thinks?|feels?)\b'
    ]
    
    past_count = sum(len(re.findall(p, text, re.I)) for p in past_patterns)
    present_count = sum(len(re.findall(p, text, re.I)) for p in present_patterns)
    
    # Calculate ratio
    total = past_count + present_count
    if total == 0:
        return TenseType.UNKNOWN
    
    past_ratio = past_count / total
    
    if past_ratio > 0.7:
        return TenseType.PAST
    elif past_ratio < 0.3:
        return TenseType.PRESENT
    else:
        return TenseType.MIXED


def detect_tone(text: str) -> ToneType:
    """
    Detect the narrative tone using keyword and pattern analysis.
    """
    text_lower = text.lower()
    
    # Tone indicators
    tone_patterns = {
        ToneType.DARK: [
            r'\b(death|darkness|shadow|fear|dread|terror|blood|pain|despair)\b',
            r'\b(cold|harsh|bitter|grim|bleak)\b'
        ],
        ToneType.HUMOROUS: [
            r'\b(laughed?|chuckled?|grinned?|smirked?|joked?)\b',
            r'\b(funny|hilarious|ridiculous|absurd)\b'
        ],
        ToneType.ROMANTIC: [
            r'\b(love|heart|kiss|embrace|passion|desire)\b',
            r'\b(beautiful|gorgeous|tender|gentle)\b'
        ],
        ToneType.SUSPENSEFUL: [
            r'\b(suddenly|something|watched|followed|someone)\b',
            r'\b(silent|quiet|waiting|tense|nervous)\b'
        ],
        ToneType.ADVENTUROUS: [
            r'\b(journey|quest|adventure|explore|discover)\b',
            r'\b(battle|fight|challenge|brave|hero)\b'
        ],
        ToneType.MELANCHOLIC: [
            r'\b(sad|tears?|cried?|lost|grief|lonely)\b',
            r'\b(memory|memories|remember|past|gone)\b'
        ],
        ToneType.MYSTERIOUS: [
            r'\b(strange|mysterious|secret|hidden|unknown)\b',
            r'\b(wondered?|puzzled?|curious|enigma)\b'
        ],
        ToneType.LIGHTHEARTED: [
            r'\b(happy|cheerful|bright|sunny|pleasant)\b',
            r'\b(smiled?|delighted?|enjoyed?|wonderful)\b'
        ]
    }
    
    scores = {}
    for tone, patterns in tone_patterns.items():
        score = sum(len(re.findall(p, text_lower)) for p in patterns)
        scores[tone] = score
    
    # Get highest scoring tone
    if scores:
        max_tone = max(scores, key=scores.get)
        if scores[max_tone] > 2:  # Minimum threshold
            return max_tone
    
    return ToneType.NEUTRAL


def detect_genre(text: str, characters: List[Character], setting: str) -> GenreHint:
    """
    Detect likely genre from content analysis.
    """
    text_lower = text.lower()
    
    genre_indicators = {
        GenreHint.FANTASY: [
            r'\b(magic|wizard|dragon|elf|sword|kingdom|spell|castle|throne)\b',
            r'\b(ancient|prophecy|realm|enchanted)\b'
        ],
        GenreHint.SCIFI: [
            r'\b(ship|space|planet|robot|alien|technology|computer|laser)\b',
            r'\b(future|system|data|program|AI|android)\b'
        ],
        GenreHint.ROMANCE: [
            r'\b(love|heart|kiss|passion|romance|relationship)\b',
            r'\b(dating|married|wedding|together)\b'
        ],
        GenreHint.THRILLER: [
            r'\b(gun|chase|escape|danger|threat|kill|dead)\b',
            r'\b(agent|spy|mission|target)\b'
        ],
        GenreHint.MYSTERY: [
            r'\b(clue|detective|investigate|murder|crime|suspect)\b',
            r'\b(evidence|witness|victim|alibi)\b'
        ],
        GenreHint.HORROR: [
            r'\b(horror|terror|monster|demon|ghost|haunted)\b',
            r'\b(scream|nightmare|creature|evil)\b'
        ],
        GenreHint.ADVENTURE: [
            r'\b(journey|travel|expedition|explore|treasure)\b',
            r'\b(map|compass|wilderness|survive)\b'
        ]
    }
    
    scores = {}
    for genre, patterns in genre_indicators.items():
        score = sum(len(re.findall(p, text_lower)) for p in patterns)
        scores[genre] = score
    
    if scores:
        max_genre = max(scores, key=scores.get)
        if scores[max_genre] > 3:
            return max_genre
    
    return GenreHint.GENERAL


def extract_characters_basic(text: str) -> List[Character]:
    """
    Extract characters using basic pattern matching.
    
    For use when spaCy is not available.
    """
    characters = {}
    
    # Common name patterns - capitalized words that appear multiple times
    # This is a simplified approach without NER
    capitalized = re.findall(r'\b([A-Z][a-z]{2,})\b', text)
    
    # Filter out common non-names
    common_words = {
        'The', 'This', 'That', 'Then', 'There', 'They', 'What', 'When', 'Where',
        'Who', 'Why', 'How', 'But', 'And', 'For', 'Not', 'She', 'His', 'Her',
        'Him', 'Its', 'After', 'Before', 'During', 'While', 'Because', 'Although',
        'However', 'Meanwhile', 'Nevertheless', 'Furthermore', 'Therefore',
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
        'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
        'September', 'October', 'November', 'December'
    }
    
    for name in capitalized:
        if name not in common_words:
            if name in characters:
                characters[name].mentions += 1
            else:
                characters[name] = Character(name=name)
    
    # Filter to names mentioned at least twice
    result = [c for c in characters.values() if c.mentions >= 2]
    
    # Sort by mentions
    result.sort(key=lambda x: x.mentions, reverse=True)
    
    # Mark most mentioned as protagonist
    if result:
        result[0].is_protagonist = True
    
    return result[:10]  # Limit to top 10


def extract_characters_spacy(doc) -> List[Character]:
    """
    Extract characters using spaCy NER.
    
    Args:
        doc: spaCy Doc object
        
    Returns:
        List of Character objects
    """
    characters = {}
    
    for sent_idx, sent in enumerate(doc.sents):
        for ent in sent.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                if name in characters:
                    characters[name].mentions += 1
                else:
                    characters[name] = Character(
                        name=name,
                        first_appearance=sent_idx
                    )
    
    result = list(characters.values())
    result.sort(key=lambda x: x.mentions, reverse=True)
    
    if result:
        result[0].is_protagonist = True
    
    return result[:10]


def extract_plot_elements(text: str) -> List[PlotElement]:
    """
    Extract plot elements from story text.
    
    Identifies events, conflicts, settings, and important objects.
    """
    elements = []
    sentences = re.split(r'[.!?]+', text)
    
    for idx, sent in enumerate(sentences):
        sent = sent.strip()
        if not sent:
            continue
        
        # Event detection - action verbs
        if re.search(r'\b(ran|jumped|attacked|escaped|found|discovered|realized|decided|killed|saved)\b', sent, re.I):
            elements.append(PlotElement(
                element_type="event",
                text=sent,
                sentence_index=idx,
                importance=0.7
            ))
        
        # Conflict detection
        elif re.search(r'\b(against|fight|problem|danger|threat|enemy|struggle|conflict)\b', sent, re.I):
            elements.append(PlotElement(
                element_type="conflict",
                text=sent,
                sentence_index=idx,
                importance=0.8
            ))
        
        # Setting detection
        elif re.search(r'\b(in the|at the|inside|outside|within|beneath|above|near)\b.*\b(house|room|forest|city|castle|ship|building)\b', sent, re.I):
            elements.append(PlotElement(
                element_type="setting",
                text=sent,
                sentence_index=idx,
                importance=0.5
            ))
        
        # Important object detection
        elif re.search(r'\b(sword|key|letter|map|weapon|treasure|ring|book|artifact)\b', sent, re.I):
            elements.append(PlotElement(
                element_type="object",
                text=sent,
                sentence_index=idx,
                importance=0.6
            ))
    
    return elements


def extract_themes(text: str) -> List[str]:
    """
    Extract potential themes from the story.
    """
    theme_patterns = {
        "love": r'\b(love|heart|romance|passion|affection)\b',
        "revenge": r'\b(revenge|vengeance|payback|retaliate)\b',
        "redemption": r'\b(redemption|forgiveness|atone|second chance)\b',
        "survival": r'\b(survive|survival|endure|persevere)\b',
        "power": r'\b(power|control|dominate|rule|authority)\b',
        "identity": r'\b(identity|self|who am i|belong|true self)\b',
        "family": r'\b(family|father|mother|brother|sister|parent|child)\b',
        "friendship": r'\b(friend|friendship|companion|ally|loyal)\b',
        "betrayal": r'\b(betray|betrayal|traitor|deceive|trust)\b',
        "justice": r'\b(justice|fair|right|wrong|moral)\b',
        "freedom": r'\b(freedom|free|escape|liberty|cage|prison)\b',
        "sacrifice": r'\b(sacrifice|give up|cost|price|trade)\b'
    }
    
    themes = []
    text_lower = text.lower()
    
    for theme, pattern in theme_patterns.items():
        if len(re.findall(pattern, text_lower)) >= 2:
            themes.append(theme)
    
    return themes[:5]  # Limit to top 5


def extract_setting(text: str) -> str:
    """
    Extract setting description from story.
    """
    setting_parts = []
    
    # Location patterns
    locations = re.findall(
        r'(?:in|at|inside|within|around|near|outside)\s+(?:the\s+)?([A-Za-z\s]+?)(?:\.|,|;|\s+(?:where|which|that))',
        text,
        re.I
    )
    setting_parts.extend(locations[:3])
    
    # Time patterns
    time_refs = re.findall(
        r'(?:during|in|at)\s+(?:the\s+)?(morning|afternoon|evening|night|dawn|dusk|midnight)',
        text,
        re.I
    )
    setting_parts.extend(time_refs[:2])
    
    # Weather/atmosphere
    atmosphere = re.findall(
        r'(?:the\s+)?(rain|storm|snow|fog|sun|wind|cold|heat|dark|bright)',
        text,
        re.I
    )
    setting_parts.extend(atmosphere[:2])
    
    if setting_parts:
        return ", ".join(set(setting_parts))
    return "Not explicitly described"


def extract_recent_events(text: str, num_events: int = 5) -> List[str]:
    """
    Extract recent events from the end of the story.
    """
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Take last portion of story
    recent = sentences[-min(len(sentences), 10):]
    
    events = []
    for sent in recent:
        # Look for action-oriented sentences
        if re.search(r'\b(he|she|they|I)\s+\w+ed\b', sent, re.I) or \
           re.search(r'\b(said|asked|replied|shouted|whispered)\b', sent, re.I):
            events.append(sent)
    
    return events[-num_events:] if events else recent[-num_events:]


# ==================== CONTEXT COMPRESSION ====================

def compress_context(text: str, max_words: int = 500, keep_recent: int = 300) -> Tuple[str, str]:
    """
    Compress long story context for LLM input.
    
    Returns:
        Tuple of (compressed_summary, recent_excerpt)
    """
    words = text.split()
    
    if len(words) <= max_words + keep_recent:
        # No compression needed
        return "", text
    
    # Split into summary portion and recent portion
    summary_portion = " ".join(words[:-keep_recent])
    recent_portion = " ".join(words[-keep_recent:])
    
    # Create summary markers for key elements
    summary_lines = []
    
    # Key events from early story
    early_sentences = re.split(r'[.!?]+', summary_portion)
    for sent in early_sentences[:5]:
        if sent.strip():
            summary_lines.append(f"• {sent.strip()}")
    
    compressed = "\n".join(summary_lines)
    
    return compressed, recent_portion


# ==================== NARRATIVE CONTEXT BUILDER ====================

def build_narrative_context(
    text: str,
    spacy_doc=None,
    max_words: int = 500
) -> NarrativeContext:
    """
    Build complete narrative context from story text.
    
    Args:
        text: Story text
        spacy_doc: Optional spaCy Doc for better NER
        max_words: Maximum words for context (compress if longer)
        
    Returns:
        NarrativeContext with all extracted information
    """
    # Detect narrative style
    pov = detect_pov(text)
    tense = detect_tense(text)
    tone = detect_tone(text)
    
    # Extract characters
    if spacy_doc:
        characters = extract_characters_spacy(spacy_doc)
    else:
        characters = extract_characters_basic(text)
    
    # Extract plot elements
    plot_elements = extract_plot_elements(text)
    
    # Extract themes
    themes = extract_themes(text)
    
    # Extract setting
    setting = extract_setting(text)
    
    # Detect genre
    genre = detect_genre(text, characters, setting)
    
    # Extract recent events
    recent_events = extract_recent_events(text)
    
    # Identify unresolved threads (simplified)
    unresolved = []
    if re.search(r'\b(would|could|might|must|should)\b', text[-500:], re.I):
        unresolved.append("Potential unresolved action or decision")
    if re.search(r'\b(question|wonder|ask|why|how|what)\b', text[-500:], re.I):
        unresolved.append("Unanswered question")
    
    # Compress if needed
    compressed, _ = compress_context(text, max_words)
    
    return NarrativeContext(
        characters=characters,
        plot_elements=plot_elements,
        pov=pov,
        tense=tense,
        tone=tone,
        genre_hint=genre,
        themes=themes,
        setting_description=setting,
        recent_events=recent_events,
        unresolved_threads=unresolved,
        word_count=len(text.split()),
        compressed_summary=compressed
    )


# ==================== PROMPT BUILDERS ====================

def build_continuation_prompt(
    story_text: str,
    context: NarrativeContext,
    word_target: int = 150,
    custom_instruction: str = ""
) -> str:
    """
    Build the continuation prompt for LLM.
    """
    # Format characters
    char_lines = []
    for char in context.characters[:5]:
        char_lines.append(f"- {char.name} (mentioned {char.mentions}x" + 
                         (", protagonist" if char.is_protagonist else "") + ")")
    characters_str = "\n".join(char_lines) if char_lines else "- No named characters identified"
    
    # Format recent events
    events_str = "\n".join(f"- {e}" for e in context.recent_events[-3:]) if context.recent_events else "- None identified"
    
    # Format themes if present
    themes_section = ""
    if context.themes:
        themes_section = f"THEMES TO MAINTAIN:\n{', '.join(context.themes)}\n"
    
    # Get story excerpt (last portion)
    words = story_text.split()
    if len(words) > 400:
        story_excerpt = "..." + " ".join(words[-400:])
    else:
        story_excerpt = story_text
    
    # POV string
    pov_str = context.pov.value.replace("_", " ")
    
    # Build prompt
    prompt = CONTINUATION_PROMPT.format(
        pov=pov_str,
        tense=context.tense.value,
        context=context.compressed_summary or "Direct continuation",
        characters=characters_str,
        setting=context.setting_description,
        recent_events=events_str,
        themes_section=themes_section,
        story_excerpt=story_excerpt,
        word_target=word_target,
        tone=context.tone.value
    )
    
    if custom_instruction:
        prompt += f"\n\nADDITIONAL DIRECTION: {custom_instruction}"
    
    return prompt


# ==================== STORY ASSISTANT CLASS ====================

class StoryAssistant:
    """
    Story continuation assistant using LLM.
    
    All prompt engineering, context extraction, and validation logic
    is custom-built. Only the LLM generation is external (Ollama).
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the story assistant.
        
        Args:
            llm_client: Optional OllamaClient instance
        """
        from nlp_engine.llm_client import get_client, TaskType, OllamaClient
        self.client = llm_client or get_client()
        self.TaskType = TaskType
        
    def analyze_story(self, text: str, spacy_doc=None) -> NarrativeContext:
        """
        Analyze story text and extract narrative context.
        
        Args:
            text: Story text
            spacy_doc: Optional spaCy Doc for better NER
            
        Returns:
            NarrativeContext with all extracted information
        """
        return build_narrative_context(text, spacy_doc)
    
    def continue_story(
        self,
        text: str,
        word_target: int = 150,
        custom_instruction: str = "",
        context: Optional[NarrativeContext] = None,
        temperature: Optional[float] = None
    ) -> ContinuationResult:
        """
        Generate a story continuation.
        
        Args:
            text: Story text to continue
            word_target: Target word count for continuation
            custom_instruction: Optional direction for continuation
            context: Pre-computed NarrativeContext (optional)
            temperature: Override temperature (default: 0.85 for stories)
            
        Returns:
            ContinuationResult with generated continuation
        """
        import time
        start_time = time.time()
        
        try:
            # Build context if not provided
            if context is None:
                context = self.analyze_story(text)
            
            # Build prompt
            prompt = build_continuation_prompt(
                text, 
                context, 
                word_target,
                custom_instruction
            )
            
            # Add system prompt
            full_prompt = f"{CONTINUATION_SYSTEM_PROMPT}\n\n{prompt}"
            
            # Generate
            result = self.client.generate(
                prompt=full_prompt,
                task_type=self.TaskType.STORY_CONTINUE,
                temperature=temperature,
                max_tokens=max(300, word_target * 2)  # Allow buffer
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if not result.success:
                return ContinuationResult(
                    continuation="",
                    context_used={},
                    pov=context.pov.value,
                    tense=context.tense.value,
                    tone=context.tone.value,
                    generation_time_ms=elapsed_ms,
                    tokens_generated=0,
                    success=False,
                    error=result.error
                )
            
            # Clean continuation
            continuation = self._clean_continuation(result.text)
            
            return ContinuationResult(
                continuation=continuation,
                context_used={
                    "characters": [c.name for c in context.characters[:5]],
                    "setting": context.setting_description,
                    "themes": context.themes,
                    "genre": context.genre_hint.value
                },
                pov=context.pov.value,
                tense=context.tense.value,
                tone=context.tone.value,
                generation_time_ms=elapsed_ms,
                tokens_generated=result.completion_tokens,
                success=True
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"Story continuation failed: {e}")
            return ContinuationResult(
                continuation="",
                context_used={},
                pov="unknown",
                tense="unknown",
                tone="unknown",
                generation_time_ms=elapsed_ms,
                tokens_generated=0,
                success=False,
                error=str(e)
            )
    
    async def continue_story_async(
        self,
        text: str,
        word_target: int = 150,
        custom_instruction: str = "",
        context: Optional[NarrativeContext] = None,
        temperature: Optional[float] = None
    ) -> ContinuationResult:
        """Async version of continue_story"""
        import time
        start_time = time.time()
        
        try:
            if context is None:
                context = self.analyze_story(text)
            
            prompt = build_continuation_prompt(text, context, word_target, custom_instruction)
            full_prompt = f"{CONTINUATION_SYSTEM_PROMPT}\n\n{prompt}"
            
            result = await self.client.generate_async(
                prompt=full_prompt,
                task_type=self.TaskType.STORY_CONTINUE,
                temperature=temperature,
                max_tokens=max(300, word_target * 2)
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if not result.success:
                return ContinuationResult(
                    continuation="",
                    context_used={},
                    pov=context.pov.value,
                    tense=context.tense.value,
                    tone=context.tone.value,
                    generation_time_ms=elapsed_ms,
                    tokens_generated=0,
                    success=False,
                    error=result.error
                )
            
            continuation = self._clean_continuation(result.text)
            
            return ContinuationResult(
                continuation=continuation,
                context_used={
                    "characters": [c.name for c in context.characters[:5]],
                    "setting": context.setting_description,
                    "themes": context.themes,
                    "genre": context.genre_hint.value
                },
                pov=context.pov.value,
                tense=context.tense.value,
                tone=context.tone.value,
                generation_time_ms=elapsed_ms,
                tokens_generated=result.completion_tokens,
                success=True
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"Async story continuation failed: {e}")
            return ContinuationResult(
                continuation="",
                context_used={},
                pov="unknown",
                tense="unknown",
                tone="unknown",
                generation_time_ms=elapsed_ms,
                tokens_generated=0,
                success=False,
                error=str(e)
            )
    
    def continue_story_stream(
        self,
        text: str,
        word_target: int = 150,
        custom_instruction: str = "",
        context: Optional[NarrativeContext] = None,
        temperature: Optional[float] = None
    ) -> Generator[str, None, None]:
        """
        Stream story continuation token by token.
        
        Yields:
            String tokens as they are generated
        """
        try:
            if context is None:
                context = self.analyze_story(text)
            
            prompt = build_continuation_prompt(text, context, word_target, custom_instruction)
            full_prompt = f"{CONTINUATION_SYSTEM_PROMPT}\n\n{prompt}"
            
            # Stream tokens
            for token in self.client.generate_stream(
                prompt=full_prompt,
                task_type=self.TaskType.STORY_CONTINUE,
                temperature=temperature,
                max_tokens=max(300, word_target * 2)
            ):
                yield token
                
        except Exception as e:
            logger.error(f"Stream continuation failed: {e}")
            yield f"[Error: {e}]"
    
    async def continue_story_stream_async(
        self,
        text: str,
        word_target: int = 150,
        custom_instruction: str = "",
        context: Optional[NarrativeContext] = None,
        temperature: Optional[float] = None
    ) -> AsyncGenerator[str, None]:
        """
        Async stream story continuation token by token.
        
        Yields:
            String tokens as they are generated
        """
        try:
            if context is None:
                context = self.analyze_story(text)
            
            prompt = build_continuation_prompt(text, context, word_target, custom_instruction)
            full_prompt = f"{CONTINUATION_SYSTEM_PROMPT}\n\n{prompt}"
            
            # Stream tokens
            async for token in self.client.generate_stream_async(
                prompt=full_prompt,
                task_type=self.TaskType.STORY_CONTINUE,
                temperature=temperature,
                max_tokens=max(300, word_target * 2)
            ):
                yield token
                
        except Exception as e:
            logger.error(f"Async stream continuation failed: {e}")
            yield f"[Error: {e}]"
    
    def generate_continuation_options(
        self,
        text: str,
        num_options: int = 3,
        context: Optional[NarrativeContext] = None
    ) -> List[ContinuationOption]:
        """
        Generate multiple continuation options for user to choose from.
        
        Uses separate generation calls for each direction type,
        which is more reliable with smaller models than JSON mode.
        
        Args:
            text: Story text
            num_options: Number of options to generate (2-4)
            context: Pre-computed context
            
        Returns:
            List of ContinuationOption objects
        """
        try:
            if context is None:
                context = self.analyze_story(text)
            
            # Get story excerpt
            words = text.split()
            excerpt = " ".join(words[-200:]) if len(words) > 200 else text
            
            # Context string
            context_str = f"POV: {context.pov.value.replace('_', ' ')}, Tense: {context.tense.value}, Tone: {context.tone.value}"
            
            # Direction types to generate
            directions = ["action", "dialogue", "description"]
            if num_options >= 4:
                directions.append("twist")
            
            options = []
            
            # Generate each option separately (more reliable than JSON mode)
            for direction in directions[:num_options]:
                prompt_template = OPTION_PROMPTS.get(direction, OPTION_PROMPTS["action"])
                prompt = prompt_template.format(
                    context=context_str,
                    story_excerpt=excerpt
                )
                
                result = self.client.generate(
                    prompt=prompt,
                    task_type=self.TaskType.STORY_CONTINUE,
                    temperature=0.85,
                    max_tokens=150
                )
                
                if result.success and result.text.strip():
                    cleaned = self._clean_continuation(result.text)
                    if cleaned:
                        options.append(ContinuationOption(
                            text=cleaned,
                            direction=direction,
                            confidence=0.8
                        ))
            
            # If we got no options, try a single fallback
            if not options:
                logger.warning("All option generations failed, trying fallback")
                single = self.continue_story(text, 80)
                if single.success:
                    return [ContinuationOption(
                        text=single.continuation,
                        direction="continuation",
                        confidence=0.6
                    )]
            
            return options
            
        except Exception as e:
            logger.error(f"Option generation failed: {e}")
            return []
    
    def summarize_story(
        self,
        text: str,
        max_words: int = 200
    ) -> str:
        """
        Summarize a long story for context compression.
        
        Args:
            text: Story text to summarize
            max_words: Maximum words in summary
            
        Returns:
            Summary string
        """
        try:
            prompt = SUMMARY_PROMPT.format(story=text[:4000])  # Limit input
            
            result = self.client.generate(
                prompt=prompt,
                task_type=self.TaskType.EXPLANATION,  # Low temperature for faithful summary
                max_tokens=max_words * 2
            )
            
            if result.success:
                return result.text.strip()
            return ""
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return ""
    
    def _clean_continuation(self, text: str) -> str:
        """
        Clean LLM output to remove artifacts.
        """
        # Remove common LLM artifacts
        artifacts = [
            r'^(Here(?:\'s| is).*?:?\s*)',
            r'^(Sure,?\s*)',
            r'^(Continuing.*?:?\s*)',
            r'^(The continuation.*?:?\s*)',
            r'^\*\*.*?\*\*\s*',  # Markdown bold headers
            r'^---\s*',  # Separators
        ]
        
        cleaned = text.strip()
        for pattern in artifacts:
            cleaned = re.sub(pattern, '', cleaned, flags=re.I)
        
        return cleaned.strip()


# ==================== MODULE-LEVEL FUNCTIONS ====================

_story_assistant = None

def get_story_assistant() -> StoryAssistant:
    """Get or create the singleton StoryAssistant instance."""
    global _story_assistant
    if _story_assistant is None:
        _story_assistant = StoryAssistant()
    return _story_assistant


def analyze_story(text: str, spacy_doc=None) -> Dict[str, Any]:
    """
    Analyze story text and return narrative context as dict.
    
    Convenience function for API use.
    """
    context = build_narrative_context(text, spacy_doc)
    return {
        "pov": context.pov.value,
        "tense": context.tense.value,
        "tone": context.tone.value,
        "genre_hint": context.genre_hint.value,
        "characters": [
            {"name": c.name, "mentions": c.mentions, "is_protagonist": c.is_protagonist}
            for c in context.characters
        ],
        "themes": context.themes,
        "setting": context.setting_description,
        "recent_events": context.recent_events,
        "word_count": context.word_count,
        "plot_element_count": len(context.plot_elements)
    }


def continue_story(
    text: str,
    word_target: int = 150,
    custom_instruction: str = ""
) -> Dict[str, Any]:
    """
    Continue a story (convenience function).
    
    Returns dict for API use.
    """
    assistant = get_story_assistant()
    result = assistant.continue_story(text, word_target, custom_instruction)
    return {
        "success": result.success,
        "continuation": result.continuation,
        "context": result.context_used,
        "pov": result.pov,
        "tense": result.tense,
        "tone": result.tone,
        "generation_time_ms": result.generation_time_ms,
        "tokens_generated": result.tokens_generated,
        "error": result.error
    }
