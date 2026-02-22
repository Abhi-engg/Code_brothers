"""
Writer Modes Module
Provide different analysis perspectives based on writing style, genre, and goals
Each mode emphasizes different aspects of writing quality
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import re


class WriterMode(str, Enum):
    """Available writer modes for analysis."""
    FICTION = "fiction"
    ACADEMIC = "academic"
    CREATIVE = "creative"
    JOURNALISM = "journalism"
    TECHNICAL = "technical"
    SCREENPLAY = "screenplay"
    POETRY = "poetry"


class ModeAnalyzer:
    """
    Analyze text based on different writer modes.
    Each mode has specific criteria and feedback tailored to that style.
    """
    
    # Mode-specific configurations
    MODE_CONFIGS = {
        WriterMode.FICTION: {
            "name": "Fiction Writer",
            "description": "Focus on storytelling, character development, and narrative flow",
            "priorities": ["character", "dialogue", "scene", "pacing", "show_dont_tell"],
            "ideal_readability": (50, 70),  # Flesch Reading Ease range
            "dialogue_range": (20, 50),  # Ideal dialogue percentage
            "sentence_variety_weight": 0.8,
            "sensory_weight": 0.9,
            "active_voice_preference": 0.7
        },
        WriterMode.ACADEMIC: {
            "name": "Academic Writer",
            "description": "Focus on clarity, precision, citations, and formal structure",
            "priorities": ["clarity", "structure", "formal_tone", "passive_acceptable", "technical_terms"],
            "ideal_readability": (30, 50),
            "dialogue_range": (0, 5),
            "sentence_variety_weight": 0.4,
            "sensory_weight": 0.2,
            "active_voice_preference": 0.5
        },
        WriterMode.CREATIVE: {
            "name": "Creative Writer",
            "description": "Emphasis on experimentation, voice, and artistic expression",
            "priorities": ["voice", "imagery", "rhythm", "originality", "emotional_impact"],
            "ideal_readability": (40, 80),
            "dialogue_range": (0, 60),
            "sentence_variety_weight": 1.0,
            "sensory_weight": 1.0,
            "active_voice_preference": 0.6
        },
        WriterMode.JOURNALISM: {
            "name": "Journalist",
            "description": "Focus on facts, inverted pyramid structure, and objectivity",
            "priorities": ["clarity", "brevity", "factual", "lead_strength", "5w1h"],
            "ideal_readability": (60, 80),
            "dialogue_range": (5, 25),
            "sentence_variety_weight": 0.5,
            "sensory_weight": 0.3,
            "active_voice_preference": 0.9
        },
        WriterMode.TECHNICAL: {
            "name": "Technical Writer",
            "description": "Focus on accuracy, step-by-step clarity, and user assistance",
            "priorities": ["clarity", "accuracy", "structure", "actionable", "consistency"],
            "ideal_readability": (45, 65),
            "dialogue_range": (0, 5),
            "sentence_variety_weight": 0.3,
            "sensory_weight": 0.1,
            "active_voice_preference": 0.8
        },
        WriterMode.SCREENPLAY: {
            "name": "Screenwriter",
            "description": "Focus on visual storytelling, tight dialogue, and scene economy",
            "priorities": ["visual", "dialogue", "action", "subtext", "pacing"],
            "ideal_readability": (60, 80),
            "dialogue_range": (40, 70),
            "sentence_variety_weight": 0.7,
            "sensory_weight": 0.8,
            "active_voice_preference": 0.95
        },
        WriterMode.POETRY: {
            "name": "Poet",
            "description": "Focus on rhythm, imagery, sound, and emotional resonance",
            "priorities": ["rhythm", "imagery", "sound", "compression", "emotion"],
            "ideal_readability": (30, 70),  # Wide range for poetry
            "dialogue_range": (0, 20),
            "sentence_variety_weight": 1.0,
            "sensory_weight": 1.0,
            "active_voice_preference": 0.5
        }
    }
    
    def __init__(self, mode: WriterMode = WriterMode.FICTION):
        """
        Initialize the mode analyzer.
        
        Args:
            mode: The writer mode to use for analysis
        """
        self.mode = mode
        self.config = self.MODE_CONFIGS.get(mode, self.MODE_CONFIGS[WriterMode.FICTION])
    
    def analyze_for_mode(self, doc, text: str, base_analysis: Dict = None) -> Dict[str, Any]:
        """
        Analyze text according to the current writer mode.
        
        Args:
            doc: spaCy Doc object
            text: Original text
            base_analysis: Optional pre-computed base analysis
            
        Returns:
            Mode-specific analysis with tailored feedback
        """
        # Mode-specific checks
        mode_analysis = {
            "mode": self.mode.value,
            "mode_name": self.config["name"],
            "mode_description": self.config["description"],
            "priorities": self.config["priorities"],
        }
        
        # Run mode-specific analysis
        if self.mode == WriterMode.FICTION:
            mode_analysis["analysis"] = self._analyze_fiction(doc, text, base_analysis)
        elif self.mode == WriterMode.ACADEMIC:
            mode_analysis["analysis"] = self._analyze_academic(doc, text, base_analysis)
        elif self.mode == WriterMode.CREATIVE:
            mode_analysis["analysis"] = self._analyze_creative(doc, text, base_analysis)
        elif self.mode == WriterMode.JOURNALISM:
            mode_analysis["analysis"] = self._analyze_journalism(doc, text, base_analysis)
        elif self.mode == WriterMode.TECHNICAL:
            mode_analysis["analysis"] = self._analyze_technical(doc, text, base_analysis)
        elif self.mode == WriterMode.SCREENPLAY:
            mode_analysis["analysis"] = self._analyze_screenplay(doc, text, base_analysis)
        elif self.mode == WriterMode.POETRY:
            mode_analysis["analysis"] = self._analyze_poetry(doc, text, base_analysis)
        
        # Generate mode-specific score
        mode_analysis["score"] = self._calculate_mode_score(mode_analysis["analysis"])
        
        # Generate tailored suggestions
        mode_analysis["suggestions"] = self._generate_mode_suggestions(mode_analysis["analysis"])
        
        return mode_analysis
    
    def _analyze_fiction(self, doc, text: str, base: Dict = None) -> Dict[str, Any]:
        """Fiction-specific analysis."""
        analysis = {}
        
        # Show don't tell detection
        analysis["show_dont_tell"] = self._check_show_dont_tell(text)
        
        # Character presence
        analysis["character_presence"] = self._analyze_character_presence(doc)
        
        # Dialogue quality for fiction
        analysis["dialogue_assessment"] = self._assess_fiction_dialogue(text)
        
        # Scene structure
        analysis["scene_elements"] = self._check_scene_elements(text)
        
        # Narrative voice
        analysis["narrative_voice"] = self._analyze_narrative_voice(doc, text)
        
        # Pacing indicators
        analysis["pacing_indicators"] = self._analyze_pacing_indicators(doc, text)
        
        return analysis
    
    def _analyze_academic(self, doc, text: str, base: Dict = None) -> Dict[str, Any]:
        """Academic writing analysis."""
        analysis = {}
        
        # Thesis/argument clarity
        analysis["argument_clarity"] = self._check_argument_clarity(text)
        
        # Citation indicators
        analysis["citation_usage"] = self._detect_citation_patterns(text)
        
        # Formal language check
        analysis["formality"] = self._assess_formality(doc, text)
        
        # Hedging language
        analysis["hedging"] = self._detect_hedging(text)
        
        # Paragraph structure
        analysis["paragraph_structure"] = self._check_academic_structure(text)
        
        # Jargon/terminology
        analysis["technical_terms"] = self._analyze_terminology(doc)
        
        return analysis
    
    def _analyze_creative(self, doc, text: str, base: Dict = None) -> Dict[str, Any]:
        """Creative writing analysis."""
        analysis = {}
        
        # Imagery and metaphor
        analysis["figurative_language"] = self._detect_figurative_language(text)
        
        # Voice distinctiveness
        analysis["voice_distinctiveness"] = self._assess_voice(doc, text)
        
        # Rhythm and flow
        analysis["rhythm"] = self._analyze_rhythm(doc)
        
        # Originality markers
        analysis["originality"] = self._check_originality(text)
        
        # Emotional resonance
        analysis["emotional_impact"] = self._assess_emotional_impact(doc, text)
        
        return analysis
    
    def _analyze_journalism(self, doc, text: str, base: Dict = None) -> Dict[str, Any]:
        """Journalism analysis."""
        analysis = {}
        
        # Lead/lede strength
        analysis["lead_strength"] = self._assess_lead(text)
        
        # 5W1H coverage
        analysis["five_ws"] = self._check_five_ws(doc, text)
        
        # Objectivity
        analysis["objectivity"] = self._assess_objectivity(doc, text)
        
        # Quote usage
        analysis["quote_usage"] = self._analyze_quote_usage(text)
        
        # Inverted pyramid structure
        analysis["structure"] = self._check_inverted_pyramid(text)
        
        return analysis
    
    def _analyze_technical(self, doc, text: str, base: Dict = None) -> Dict[str, Any]:
        """Technical writing analysis."""
        analysis = {}
        
        # Clarity and precision
        analysis["clarity"] = self._assess_technical_clarity(doc, text)
        
        # Actionable instructions
        analysis["actionability"] = self._check_actionability(text)
        
        # Consistency
        analysis["terminology_consistency"] = self._check_term_consistency(text)
        
        # Structure and organization
        analysis["organization"] = self._assess_organization(text)
        
        # Ambiguity detection
        analysis["ambiguity"] = self._detect_ambiguity(text)
        
        return analysis
    
    def _analyze_screenplay(self, doc, text: str, base: Dict = None) -> Dict[str, Any]:
        """Screenplay analysis."""
        analysis = {}
        
        # Visual writing
        analysis["visual_writing"] = self._check_visual_writing(text)
        
        # Dialogue economy
        analysis["dialogue_economy"] = self._assess_dialogue_economy(text)
        
        # Action line quality
        analysis["action_lines"] = self._assess_action_lines(text)
        
        # Subtext presence
        analysis["subtext"] = self._detect_subtext(text)
        
        # Scene economy
        analysis["scene_economy"] = self._assess_scene_economy(text)
        
        return analysis
    
    def _analyze_poetry(self, doc, text: str, base: Dict = None) -> Dict[str, Any]:
        """Poetry analysis."""
        analysis = {}
        
        # Sound devices
        analysis["sound_devices"] = self._detect_sound_devices(text)
        
        # Line breaks and rhythm
        analysis["rhythm_patterns"] = self._analyze_poetic_rhythm(text)
        
        # Imagery density
        analysis["imagery"] = self._assess_imagery_density(text)
        
        # Compression
        analysis["compression"] = self._assess_compression(text)
        
        # Emotional core
        analysis["emotional_core"] = self._find_emotional_core(doc, text)
        
        return analysis
    
    # ===== Fiction Helper Methods =====
    
    def _check_show_dont_tell(self, text: str) -> Dict[str, Any]:
        """Detect telling vs showing."""
        telling_patterns = [
            (r'\b(was|were|felt)\s+(very\s+)?(angry|happy|sad|scared|worried|excited)\b', 'emotion_telling'),
            (r'\b(he|she|they)\s+felt\s+\w+\b', 'felt_statement'),
            (r'\b(obviously|clearly|apparently)\b', 'telling_adverb')
        ]
        
        issues = []
        for pattern, issue_type in telling_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                issues.append({
                    "type": issue_type,
                    "count": len(matches)
                })
        
        return {
            "telling_instances": len(issues),
            "issues": issues,
            "score": max(0, 100 - len(issues) * 10),
            "feedback": "Good showing!" if len(issues) < 3 else "Consider showing emotions through action and detail"
        }
    
    def _analyze_character_presence(self, doc) -> Dict[str, Any]:
        """Check for character presence in text."""
        persons = [ent for ent in doc.ents if ent.label_ == "PERSON"]
        pronouns = [t for t in doc if t.pos_ == "PRON" and t.text.lower() in 
                   ['he', 'she', 'they', 'him', 'her', 'them', 'his', 'her', 'their']]
        
        return {
            "named_characters": len(set(p.text for p in persons)),
            "character_mentions": len(persons) + len(pronouns),
            "has_protagonist_focus": len(pronouns) > 5,
            "feedback": "Good character presence" if persons else "Consider introducing named characters"
        }
    
    def _assess_fiction_dialogue(self, text: str) -> Dict[str, Any]:
        """Assess dialogue quality for fiction."""
        dialogue_pattern = r'["\']([^"\']+)["\']'
        dialogues = re.findall(dialogue_pattern, text)
        
        if not dialogues:
            return {"has_dialogue": False, "feedback": "Consider adding dialogue to bring scenes alive"}
        
        avg_length = sum(len(d.split()) for d in dialogues) / len(dialogues)
        
        return {
            "has_dialogue": True,
            "dialogue_count": len(dialogues),
            "avg_length": round(avg_length, 1),
            "feedback": "Good dialogue presence" if 5 < avg_length < 30 else "Review dialogue length for naturalness"
        }
    
    def _check_scene_elements(self, text: str) -> Dict[str, Any]:
        """Check for essential scene elements."""
        elements = {
            "setting": bool(re.search(r'\b(room|house|street|building|outside|inside|sky|sun|night|morning)\b', text.lower())),
            "action": bool(re.search(r'\b(walked|ran|grabbed|opened|moved|sat|stood)\b', text.lower())),
            "sensory": bool(re.search(r'\b(saw|heard|felt|smelled|tasted|touched)\b', text.lower())),
            "emotion": bool(re.search(r'\b(fear|joy|anger|love|hope|dread)\b', text.lower()))
        }
        
        present = sum(elements.values())
        
        return {
            "elements": elements,
            "elements_present": present,
            "score": present * 25,
            "missing": [k for k, v in elements.items() if not v]
        }
    
    def _analyze_narrative_voice(self, doc, text: str) -> Dict[str, Any]:
        """Analyze narrative voice and POV."""
        first_person = len(re.findall(r'\b(I|me|my|mine|myself)\b', text, re.IGNORECASE))
        second_person = len(re.findall(r'\b(you|your|yours|yourself)\b', text, re.IGNORECASE))
        third_person = len(re.findall(r'\b(he|she|they|him|her|them|his|their)\b', text, re.IGNORECASE))
        
        total = first_person + second_person + third_person
        if total == 0:
            return {"pov": "unclear", "consistency": 0}
        
        # Determine dominant POV
        if first_person > second_person and first_person > third_person:
            pov = "first_person"
            dominant = first_person
        elif second_person > first_person and second_person > third_person:
            pov = "second_person"
            dominant = second_person
        else:
            pov = "third_person"
            dominant = third_person
        
        consistency = (dominant / total) * 100
        
        return {
            "pov": pov,
            "consistency": round(consistency, 1),
            "feedback": f"Narrative uses {pov.replace('_', ' ')} POV" + 
                       (" consistently" if consistency > 80 else " - watch for POV shifts")
        }
    
    def _analyze_pacing_indicators(self, doc, text: str) -> Dict[str, Any]:
        """Analyze pacing through sentence and paragraph analysis."""
        sentences = list(doc.sents)
        lengths = [len(list(sent)) for sent in sentences]
        
        if not lengths:
            return {"pacing": "unknown"}
        
        avg_length = sum(lengths) / len(lengths)
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        
        # High variance = more dynamic pacing
        if variance > 100:
            pacing = "dynamic"
        elif variance > 50:
            pacing = "varied"
        else:
            pacing = "steady"
        
        return {
            "pacing": pacing,
            "avg_sentence_length": round(avg_length, 1),
            "sentence_variety": "good" if variance > 50 else "consider varying",
            "feedback": f"Pacing is {pacing}" + (". Good variety!" if variance > 50 else ". Try varying sentence lengths.")
        }
    
    # ===== Academic Helper Methods =====
    
    def _check_argument_clarity(self, text: str) -> Dict[str, Any]:
        """Check for clear argument/thesis indicators."""
        thesis_indicators = [
            r'\b(this (paper|essay|study|article) (argues|examines|explores|demonstrates))\b',
            r'\b(the (main|primary|central) (argument|thesis|claim))\b',
            r'\b(I argue that|we argue that|it is argued that)\b',
            r'\b(the purpose of this)\b'
        ]
        
        found = []
        for pattern in thesis_indicators:
            if re.search(pattern, text.lower()):
                found.append(pattern.split('\\b')[1])
        
        return {
            "has_clear_thesis": len(found) > 0,
            "indicators_found": len(found),
            "feedback": "Clear thesis statement present" if found else "Consider stating your thesis more explicitly"
        }
    
    def _detect_citation_patterns(self, text: str) -> Dict[str, Any]:
        """Detect citation patterns."""
        patterns = {
            "apa": r'\([A-Z][a-z]+,?\s*\d{4}\)',
            "mla": r'\([A-Z][a-z]+\s+\d+\)',
            "footnote": r'\[\d+\]|\*{1,3}',
            "inline": r'according to [A-Z][a-z]+'
        }
        
        citations = {}
        for style, pattern in patterns.items():
            count = len(re.findall(pattern, text))
            if count:
                citations[style] = count
        
        return {
            "citation_styles_detected": citations,
            "total_citations": sum(citations.values()),
            "feedback": "Citations present" if citations else "Consider adding citations to support claims"
        }
    
    def _assess_formality(self, doc, text: str) -> Dict[str, Any]:
        """Assess formality level."""
        informal_markers = len(re.findall(
            r"\b(can't|won't|don't|isn't|aren't|gonna|wanna|kinda|sorta|yeah|okay|ok)\b",
            text.lower()
        ))
        
        formal_markers = len(re.findall(
            r'\b(therefore|furthermore|moreover|consequently|nevertheless|notwithstanding)\b',
            text.lower()
        ))
        
        contractions = len(re.findall(r"\w+'[a-z]+\b", text.lower()))
        
        formality_score = 50 + (formal_markers * 10) - (informal_markers * 10) - (contractions * 5)
        formality_score = max(0, min(100, formality_score))
        
        return {
            "formality_score": formality_score,
            "contractions": contractions,
            "formal_transitions": formal_markers,
            "informal_language": informal_markers,
            "feedback": "Appropriate formality" if formality_score > 70 else "Consider more formal language"
        }
    
    def _detect_hedging(self, text: str) -> Dict[str, Any]:
        """Detect hedging language."""
        hedges = re.findall(
            r'\b(may|might|could|possibly|perhaps|probably|somewhat|relatively|'
            r'it seems|appears to|tends to|suggests that)\b',
            text.lower()
        )
        
        word_count = len(text.split())
        hedge_ratio = (len(hedges) / max(word_count, 1)) * 100
        
        return {
            "hedge_count": len(hedges),
            "hedge_ratio": round(hedge_ratio, 2),
            "appropriate": 0.5 < hedge_ratio < 3,
            "feedback": "Appropriate use of hedging" if 0.5 < hedge_ratio < 3 else 
                       "Too much hedging - be more assertive" if hedge_ratio > 3 else
                       "Consider hedging strong claims appropriately"
        }
    
    def _check_academic_structure(self, text: str) -> Dict[str, Any]:
        """Check for academic paragraph structure."""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        well_structured = 0
        for para in paragraphs:
            # Check for topic sentence (starts with clear statement)
            if re.match(r'^[A-Z][^.]+\.(.*[.!?])+', para[:200] if len(para) > 200 else para):
                well_structured += 1
        
        return {
            "paragraph_count": len(paragraphs),
            "well_structured": well_structured,
            "structure_ratio": round(well_structured / max(len(paragraphs), 1) * 100, 1),
            "feedback": "Good paragraph structure" if well_structured >= len(paragraphs) * 0.7 else 
                       "Ensure paragraphs have clear topic sentences"
        }
    
    def _analyze_terminology(self, doc) -> Dict[str, Any]:
        """Analyze use of academic/technical terminology."""
        # Look for capitalized terms, acronyms, compound nouns
        technical = []
        
        for token in doc:
            if token.pos_ == "NOUN" and len(token.text) > 4:
                if token.text[0].isupper() or token.text.isupper():
                    technical.append(token.text)
        
        unique_terms = list(set(technical))
        
        return {
            "technical_terms": unique_terms[:10],
            "term_count": len(unique_terms),
            "feedback": f"Found {len(unique_terms)} technical/specialized terms"
        }
    
    # ===== Journalism Helper Methods =====
    
    def _assess_lead(self, text: str) -> Dict[str, Any]:
        """Assess the strength of the lead/lede."""
        first_para = text.split('\n\n')[0] if text else ""
        first_sentence = first_para.split('.')[0] if first_para else ""
        
        # Strong leads are typically 25-35 words
        word_count = len(first_sentence.split())
        
        # Check for news elements in lead
        has_who = bool(re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', first_sentence))
        has_what = bool(re.search(r'\b(said|announced|revealed|discovered|won|lost|killed|died)\b', first_sentence.lower()))
        
        score = 50
        if 20 <= word_count <= 40:
            score += 20
        if has_who:
            score += 15
        if has_what:
            score += 15
        
        return {
            "lead_length": word_count,
            "has_who": has_who,
            "has_what": has_what,
            "score": score,
            "feedback": "Strong lead" if score > 70 else "Lead could be stronger - include who and what"
        }
    
    def _check_five_ws(self, doc, text: str) -> Dict[str, Any]:
        """Check coverage of Who, What, When, Where, Why, How."""
        ws = {
            "who": bool(doc.ents) or bool(re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', text)),
            "what": bool(re.search(r'\b(action|event|incident|announcement|decision)\b', text.lower())),
            "when": bool(re.search(r'\b(today|yesterday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|\d{4}|last week|this morning)\b', text)),
            "where": any(ent.label_ in ["GPE", "LOC", "FAC"] for ent in doc.ents),
            "why": bool(re.search(r'\b(because|due to|reason|caused by|in order to)\b', text.lower())),
            "how": bool(re.search(r'\b(by|through|via|using|method)\b', text.lower()))
        }
        
        coverage = sum(ws.values())
        
        return {
            "coverage": ws,
            "score": round(coverage / 6 * 100, 1),
            "missing": [k.upper() for k, v in ws.items() if not v],
            "feedback": "Good 5W1H coverage" if coverage >= 4 else f"Missing: {', '.join([k.upper() for k, v in ws.items() if not v])}"
        }
    
    def _assess_objectivity(self, doc, text: str) -> Dict[str, Any]:
        """Assess objectivity of the writing."""
        subjective_markers = len(re.findall(
            r'\b(I think|I believe|in my opinion|personally|beautiful|terrible|amazing|awful)\b',
            text.lower()
        ))
        
        first_person = len(re.findall(r'\bI\b', text))
        
        objectivity_score = 100 - (subjective_markers * 10) - (first_person * 5)
        objectivity_score = max(0, min(100, objectivity_score))
        
        return {
            "objectivity_score": objectivity_score,
            "subjective_markers": subjective_markers,
            "first_person_usage": first_person,
            "feedback": "Good objectivity" if objectivity_score > 70 else "Remove subjective language for news writing"
        }
    
    def _analyze_quote_usage(self, text: str) -> Dict[str, Any]:
        """Analyze use of quotes in journalism."""
        quotes = re.findall(r'["\']([^"\']+)["\']', text)
        attributed = len(re.findall(r'["\'][^"\']+["\'],?\s*(said|says|told|according to)', text))
        
        return {
            "quote_count": len(quotes),
            "attributed_quotes": attributed,
            "feedback": "Good use of quotes" if quotes else "Consider adding quotes from sources"
        }
    
    def _check_inverted_pyramid(self, text: str) -> Dict[str, Any]:
        """Check for inverted pyramid structure."""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if len(paragraphs) < 3:
            return {"has_structure": False, "feedback": "Text too short to assess structure"}
        
        # First paragraph should be longest/most info-dense
        para_lengths = [len(p.split()) for p in paragraphs]
        
        decreasing = all(para_lengths[i] >= para_lengths[i+1] * 0.7 
                        for i in range(min(3, len(para_lengths)-1)))
        
        return {
            "follows_pyramid": decreasing,
            "paragraph_lengths": para_lengths[:5],
            "feedback": "Good inverted pyramid structure" if decreasing else "Consider front-loading key information"
        }
    
    # ===== Technical Writing Helper Methods =====
    
    def _assess_technical_clarity(self, doc, text: str) -> Dict[str, Any]:
        """Assess clarity for technical writing."""
        avg_sentence_length = len(text.split()) / max(len(list(doc.sents)), 1)
        
        passive_count = len(re.findall(r'\b(is|are|was|were|been|being)\s+\w+ed\b', text.lower()))
        
        clarity_score = 100
        if avg_sentence_length > 25:
            clarity_score -= 20
        if passive_count > 5:
            clarity_score -= 15
        
        return {
            "avg_sentence_length": round(avg_sentence_length, 1),
            "passive_constructions": passive_count,
            "clarity_score": max(0, clarity_score),
            "feedback": "Good clarity" if clarity_score > 70 else "Simplify sentences for better clarity"
        }
    
    def _check_actionability(self, text: str) -> Dict[str, Any]:
        """Check for actionable instructions."""
        imperatives = len(re.findall(r'^[A-Z][a-z]+\s', text, re.MULTILINE))
        action_verbs = len(re.findall(
            r'\b(click|select|choose|enter|type|open|close|save|delete|install|configure|set)\b',
            text.lower()
        ))
        
        numbered_steps = len(re.findall(r'^\s*\d+[.)]\s', text, re.MULTILINE))
        
        return {
            "action_verbs": action_verbs,
            "numbered_steps": numbered_steps,
            "actionable_score": min(100, (action_verbs + numbered_steps) * 10),
            "feedback": "Good actionable content" if action_verbs > 3 else "Add more action verbs and clear steps"
        }
    
    def _check_term_consistency(self, text: str) -> Dict[str, Any]:
        """Check for consistent terminology."""
        # Look for potential inconsistencies
        variations = {
            "click/press/tap": len(set(re.findall(r'\b(click|press|tap)\b', text.lower()))),
            "select/choose/pick": len(set(re.findall(r'\b(select|choose|pick)\b', text.lower()))),
        }
        
        inconsistent = [k for k, v in variations.items() if v > 1]
        
        return {
            "terminology_variations": variations,
            "inconsistencies": inconsistent,
            "consistency_score": 100 - len(inconsistent) * 20,
            "feedback": "Consistent terminology" if not inconsistent else f"Standardize terms: {', '.join(inconsistent)}"
        }
    
    def _assess_organization(self, text: str) -> Dict[str, Any]:
        """Assess organization and structure."""
        # Check for headers, lists, numbered items
        headers = len(re.findall(r'^#{1,6}\s|\n[A-Z][^.?!]+:\n', text, re.MULTILINE))
        lists = len(re.findall(r'^\s*[-*•]\s', text, re.MULTILINE))
        numbered = len(re.findall(r'^\s*\d+[.)]\s', text, re.MULTILINE))
        
        organization_score = min(100, 50 + headers * 10 + lists * 5 + numbered * 5)
        
        return {
            "headers": headers,
            "bullet_lists": lists,
            "numbered_lists": numbered,
            "organization_score": organization_score,
            "feedback": "Well organized" if organization_score > 70 else "Add headers and lists for better organization"
        }
    
    def _detect_ambiguity(self, text: str) -> Dict[str, Any]:
        """Detect ambiguous language."""
        ambiguous_terms = re.findall(
            r'\b(it|this|that|these|those|some|few|many|several|various|etc|and so on)\b',
            text.lower()
        )
        
        vague_count = len(ambiguous_terms)
        
        return {
            "ambiguous_terms": vague_count,
            "examples": list(set(ambiguous_terms))[:5],
            "feedback": "Clear and specific" if vague_count < 5 else "Replace vague terms with specific references"
        }
    
    # ===== Additional Helper Methods =====
    
    def _detect_figurative_language(self, text: str) -> Dict[str, Any]:
        """Detect metaphors, similes, and other figurative language."""
        similes = len(re.findall(r'\b(like|as)\s+(?:a|an|the)?\s*\w+', text.lower()))
        metaphor_indicators = len(re.findall(r'\b(is|was|are|were)\s+(?:a|an|the)\s+\w+', text.lower()))
        
        return {
            "similes_detected": similes,
            "potential_metaphors": metaphor_indicators,
            "figurative_richness": "high" if similes + metaphor_indicators > 5 else "moderate" if similes + metaphor_indicators > 2 else "low"
        }
    
    def _assess_voice(self, doc, text: str) -> Dict[str, Any]:
        """Assess voice distinctiveness."""
        # Voice indicators: sentence variety, word choice, rhythm
        sentence_lengths = [len(list(sent)) for sent in doc.sents]
        variety = len(set(sentence_lengths)) / max(len(sentence_lengths), 1)
        
        return {
            "variety_score": round(variety * 100, 1),
            "distinctive": variety > 0.6,
            "feedback": "Distinctive voice" if variety > 0.6 else "Develop more sentence variety for stronger voice"
        }
    
    def _analyze_rhythm(self, doc) -> Dict[str, Any]:
        """Analyze rhythmic patterns."""
        syllable_patterns = []
        
        return {
            "rhythm_detected": True,
            "feedback": "Analyze rhythm patterns manually for creative assessment"
        }
    
    def _check_originality(self, text: str) -> Dict[str, Any]:
        """Check for clichés and originality."""
        cliches = [
            "at the end of the day", "think outside the box", "it is what it is",
            "in the nick of time", "cold as ice", "dead as a doornail"
        ]
        
        found = [c for c in cliches if c in text.lower()]
        
        return {
            "cliches_found": found,
            "originality_score": max(0, 100 - len(found) * 15),
            "feedback": "Original language" if not found else f"Replace clichés: {', '.join(found[:3])}"
        }
    
    def _assess_emotional_impact(self, doc, text: str) -> Dict[str, Any]:
        """Assess emotional impact of creative writing."""
        emotion_words = len(re.findall(
            r'\b(love|hate|fear|joy|sorrow|anger|despair|hope|longing|grief)\b',
            text.lower()
        ))
        
        return {
            "emotion_word_density": emotion_words,
            "impact": "high" if emotion_words > 5 else "moderate" if emotion_words > 2 else "subtle",
            "feedback": "Strong emotional content" if emotion_words > 3 else "Consider deepening emotional resonance"
        }
    
    def _check_visual_writing(self, text: str) -> Dict[str, Any]:
        """Check for visual/cinematic writing style."""
        visual_verbs = len(re.findall(
            r'\b(sees|watches|looks|glances|stares|peers|notices|observes)\b',
            text.lower()
        ))
        
        return {
            "visual_verbs": visual_verbs,
            "is_visual": visual_verbs > 3,
            "feedback": "Good visual writing" if visual_verbs > 3 else "Add more visual, show-able actions"
        }
    
    def _assess_dialogue_economy(self, text: str) -> Dict[str, Any]:
        """Assess dialogue economy for screenwriting."""
        dialogues = re.findall(r'["\']([^"\']+)["\']', text)
        
        if not dialogues:
            return {"economy": "n/a", "feedback": "No dialogue to assess"}
        
        avg_length = sum(len(d.split()) for d in dialogues) / len(dialogues)
        
        return {
            "avg_dialogue_length": round(avg_length, 1),
            "economy": "good" if avg_length < 20 else "verbose",
            "feedback": "Tight dialogue" if avg_length < 20 else "Trim dialogue for screen economy"
        }
    
    def _assess_action_lines(self, text: str) -> Dict[str, Any]:
        """Assess action line quality."""
        # Action lines should be present tense, visual
        present_tense = len(re.findall(r'\b(walks|runs|grabs|opens|turns)\b', text.lower()))
        
        return {
            "present_tense_verbs": present_tense,
            "feedback": "Good action writing" if present_tense > 3 else "Use more present tense, active verbs"
        }
    
    def _detect_subtext(self, text: str) -> Dict[str, Any]:
        """Detect subtext indicators."""
        subtext_indicators = len(re.findall(
            r'\b(unsaid|unspoken|beneath|underneath|really meant|implied)\b',
            text.lower()
        ))
        
        return {
            "subtext_indicators": subtext_indicators,
            "has_subtext": subtext_indicators > 0,
            "feedback": "Subtext present" if subtext_indicators > 0 else "Consider adding layers of meaning beneath dialogue"
        }
    
    def _assess_scene_economy(self, text: str) -> Dict[str, Any]:
        """Assess scene economy for screenwriting."""
        word_count = len(text.split())
        
        return {
            "word_count": word_count,
            "is_economical": word_count < 500,
            "feedback": "Good scene length" if word_count < 500 else "Consider trimming for screen pacing"
        }
    
    def _detect_sound_devices(self, text: str) -> Dict[str, Any]:
        """Detect alliteration, assonance, consonance."""
        words = text.lower().split()
        
        # Simple alliteration check
        alliteration = 0
        for i in range(len(words) - 1):
            if words[i] and words[i+1] and words[i][0] == words[i+1][0]:
                alliteration += 1
        
        return {
            "alliteration_instances": alliteration,
            "sound_richness": "high" if alliteration > 5 else "moderate" if alliteration > 2 else "low"
        }
    
    def _analyze_poetic_rhythm(self, text: str) -> Dict[str, Any]:
        """Analyze rhythm patterns in poetry."""
        lines = text.split('\n')
        line_lengths = [len(line.split()) for line in lines if line.strip()]
        
        if not line_lengths:
            return {"pattern": "unknown"}
        
        # Check for regularity
        variance = sum((l - sum(line_lengths)/len(line_lengths))**2 for l in line_lengths) / len(line_lengths)
        
        return {
            "line_count": len(line_lengths),
            "avg_line_length": round(sum(line_lengths)/len(line_lengths), 1),
            "regularity": "regular" if variance < 5 else "varied",
            "feedback": "Regular meter detected" if variance < 5 else "Free verse rhythm"
        }
    
    def _assess_imagery_density(self, text: str) -> Dict[str, Any]:
        """Assess density of imagery in poetry."""
        imagery = len(re.findall(
            r'\b(sun|moon|star|sky|sea|wind|fire|earth|water|light|dark|shadow|blood|stone|flower)\b',
            text.lower()
        ))
        
        word_count = len(text.split())
        density = (imagery / max(word_count, 1)) * 100
        
        return {
            "imagery_words": imagery,
            "density_percentage": round(density, 2),
            "richness": "rich" if density > 5 else "moderate" if density > 2 else "sparse"
        }
    
    def _assess_compression(self, text: str) -> Dict[str, Any]:
        """Assess compression/economy in poetry."""
        word_count = len(text.split())
        unique_words = len(set(text.lower().split()))
        
        lexical_density = (unique_words / max(word_count, 1)) * 100
        
        return {
            "lexical_density": round(lexical_density, 1),
            "is_compressed": lexical_density > 60,
            "feedback": "Well compressed" if lexical_density > 60 else "Consider tightening language"
        }
    
    def _find_emotional_core(self, doc, text: str) -> Dict[str, Any]:
        """Find emotional core/theme of poem."""
        emotions = {
            "love": len(re.findall(r'\b(love|heart|embrace|kiss|dear|beloved)\b', text.lower())),
            "loss": len(re.findall(r'\b(loss|gone|missing|empty|grief|mourn)\b', text.lower())),
            "nature": len(re.findall(r'\b(tree|flower|river|mountain|sky|bird)\b', text.lower())),
            "time": len(re.findall(r'\b(time|moment|forever|fleeting|eternal|past)\b', text.lower())),
            "death": len(re.findall(r'\b(death|dying|grave|end|final|mortal)\b', text.lower())),
        }
        
        dominant = max(emotions.items(), key=lambda x: x[1]) if any(emotions.values()) else ("unclear", 0)
        
        return {
            "themes": {k: v for k, v in emotions.items() if v > 0},
            "dominant_theme": dominant[0] if dominant[1] > 0 else "varied/unclear",
            "feedback": f"Dominant theme: {dominant[0]}" if dominant[1] > 0 else "Multiple or subtle themes"
        }
    
    def _calculate_mode_score(self, analysis: Dict) -> float:
        """Calculate overall score based on mode-specific analysis."""
        scores = []
        
        for key, value in analysis.items():
            if isinstance(value, dict):
                if "score" in value:
                    scores.append(value["score"])
                elif "clarity_score" in value:
                    scores.append(value["clarity_score"])
                elif "consistency_score" in value:
                    scores.append(value["consistency_score"])
        
        if not scores:
            return 70.0  # Default score
        
        return round(sum(scores) / len(scores), 1)
    
    def _generate_mode_suggestions(self, analysis: Dict) -> List[Dict[str, Any]]:
        """Generate mode-specific suggestions."""
        suggestions = []
        
        for key, value in analysis.items():
            if isinstance(value, dict) and "feedback" in value:
                if value.get("score", 100) < 70 or \
                   any(word in value["feedback"].lower() for word in ["consider", "could", "add", "replace"]):
                    suggestions.append({
                        "area": key.replace("_", " ").title(),
                        "feedback": value["feedback"],
                        "priority": "high" if value.get("score", 100) < 50 else "medium"
                    })
        
        return suggestions


def analyze_with_mode(doc, text: str, mode: str = "fiction", base_analysis: Dict = None) -> Dict[str, Any]:
    """
    Main entry point for mode-specific analysis.
    
    Args:
        doc: spaCy Doc object
        text: Original text
        mode: Writer mode string (fiction, academic, creative, etc.)
        base_analysis: Optional pre-computed base analysis
        
    Returns:
        Mode-specific analysis with tailored feedback
    """
    try:
        writer_mode = WriterMode(mode.lower())
    except ValueError:
        writer_mode = WriterMode.FICTION
    
    analyzer = ModeAnalyzer(writer_mode)
    return analyzer.analyze_for_mode(doc, text, base_analysis)


def get_available_modes() -> List[Dict[str, str]]:
    """Get list of available writer modes with descriptions."""
    return [
        {
            "mode": mode.value,
            "name": ModeAnalyzer.MODE_CONFIGS[mode]["name"],
            "description": ModeAnalyzer.MODE_CONFIGS[mode]["description"]
        }
        for mode in WriterMode
    ]
