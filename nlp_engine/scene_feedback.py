"""
Scene Feedback Module
Analyze scene structure, pacing, transitions, and provide actionable feedback
"""

from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import re


class SceneAnalyzer:
    """
    Analyze scenes in narrative text.
    Evaluates structure, pacing, sensory details, tension, and transitions.
    """
    
    # Scene break indicators
    SCENE_BREAK_PATTERNS = [
        r'\n\s*\*\s*\*\s*\*\s*\n',  # ***
        r'\n\s*#\s*#\s*#\s*\n',      # ###
        r'\n\s*~\s*~\s*~\s*\n',      # ~~~
        r'\n\s*-\s*-\s*-\s*\n',      # ---
        r'\n{3,}',                    # Multiple blank lines
    ]
    
    # Time transition words
    TIME_TRANSITIONS = [
        "later", "afterwards", "the next day", "the following", "hours later",
        "minutes later", "that evening", "that morning", "meanwhile", "suddenly",
        "eventually", "finally", "soon", "before long", "in the meantime"
    ]
    
    # Location indicators
    LOCATION_PATTERNS = [
        r'\b(in the|at the|inside|outside|near|by the|at|on)\s+(\w+)',
        r'\b(room|house|building|office|street|park|garden|kitchen|bedroom|hall)\b',
        r'\b(arrived at|entered|left|walked into|stepped into|stood in)\b'
    ]
    
    # Sensory words by type
    SENSORY_WORDS = {
        "sight": ["saw", "looked", "watched", "gazed", "glanced", "stared", 
                  "bright", "dark", "colorful", "shadowy", "gleaming", "shimmering"],
        "sound": ["heard", "listened", "noise", "sound", "quiet", "loud", 
                  "whispered", "shouted", "rang", "echoed", "silence", "thunder"],
        "touch": ["felt", "touched", "cold", "warm", "soft", "hard", "rough", 
                  "smooth", "wet", "dry", "sharp", "gentle"],
        "smell": ["smelled", "scent", "odor", "fragrant", "stench", "aroma",
                  "perfume", "musty", "fresh", "acrid"],
        "taste": ["tasted", "sweet", "bitter", "sour", "salty", "delicious",
                  "savory", "bland", "spicy"]
    }
    
    # Tension/conflict indicators
    TENSION_WORDS = [
        "but", "however", "suddenly", "despite", "although", "conflict",
        "problem", "danger", "fear", "worried", "anxious", "threat",
        "struggle", "challenge", "obstacle", "confronted", "attacked"
    ]
    
    def __init__(self):
        self.scenes = []
    
    def analyze_scenes(self, doc, text: str) -> Dict[str, Any]:
        """
        Comprehensive scene analysis.
        
        Args:
            doc: spaCy Doc object
            text: Original text
            
        Returns:
            Dictionary with scene analysis and feedback
        """
        # Detect and segment scenes
        scenes = self._segment_scenes(text)
        
        # Analyze each scene
        scene_analyses = []
        for i, scene in enumerate(scenes):
            analysis = self._analyze_single_scene(doc, scene, i)
            scene_analyses.append(analysis)
        
        # Analyze scene transitions
        transitions = self._analyze_transitions(scenes, text)
        
        # Overall pacing analysis
        pacing = self._analyze_overall_pacing(scene_analyses)
        
        # Generate feedback and suggestions
        feedback = self._generate_scene_feedback(scene_analyses, transitions)
        
        # Calculate scene score
        scene_score = self._calculate_scene_score(scene_analyses, transitions)
        
        return {
            "scene_count": len(scenes),
            "scenes": scene_analyses,
            "transitions": transitions,
            "pacing": pacing,
            "feedback": feedback,
            "scene_score": scene_score,
            "summary": self._generate_summary(scene_analyses, pacing)
        }
    
    def _segment_scenes(self, text: str) -> List[Dict[str, Any]]:
        """Segment text into scenes based on breaks or natural divisions."""
        scenes = []
        
        # Try explicit scene breaks first
        combined_pattern = '|'.join(self.SCENE_BREAK_PATTERNS)
        parts = re.split(combined_pattern, text)
        
        if len(parts) > 1:
            # Explicit scene breaks found
            position = 0
            for i, part in enumerate(parts):
                part = part.strip()
                if part:
                    scenes.append({
                        "number": i + 1,
                        "text": part,
                        "start_position": position,
                        "word_count": len(part.split()),
                        "has_explicit_break": True
                    })
                position += len(part) + 10  # Approximate for break markers
        else:
            # No explicit breaks - try to detect natural scene changes
            scenes = self._detect_natural_scene_breaks(text)
        
        return scenes if scenes else [{
            "number": 1,
            "text": text,
            "start_position": 0,
            "word_count": len(text.split()),
            "has_explicit_break": False
        }]
    
    def _detect_natural_scene_breaks(self, text: str) -> List[Dict[str, Any]]:
        """Detect natural scene breaks based on time/location changes."""
        scenes = []
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if len(paragraphs) <= 1:
            return []
        
        current_scene = {
            "number": 1,
            "paragraphs": [paragraphs[0]],
            "start_position": 0
        }
        
        position = len(paragraphs[0])
        
        for i, para in enumerate(paragraphs[1:], 1):
            # Check for scene change indicators
            is_scene_change = False
            
            # Time jump
            for transition in self.TIME_TRANSITIONS:
                if transition.lower() in para.lower()[:100]:
                    is_scene_change = True
                    break
            
            # Location change at paragraph start
            if not is_scene_change:
                location_match = re.match(
                    r'^(In|At|Inside|Outside|Near)\s+the\s+\w+',
                    para,
                    re.IGNORECASE
                )
                if location_match:
                    is_scene_change = True
            
            if is_scene_change and len(current_scene["paragraphs"]) >= 2:
                # Save current scene
                scene_text = '\n\n'.join(current_scene["paragraphs"])
                scenes.append({
                    "number": current_scene["number"],
                    "text": scene_text,
                    "start_position": current_scene["start_position"],
                    "word_count": len(scene_text.split()),
                    "has_explicit_break": False
                })
                
                # Start new scene
                current_scene = {
                    "number": len(scenes) + 1,
                    "paragraphs": [para],
                    "start_position": position
                }
            else:
                current_scene["paragraphs"].append(para)
            
            position += len(para) + 2
        
        # Add final scene
        if current_scene["paragraphs"]:
            scene_text = '\n\n'.join(current_scene["paragraphs"])
            scenes.append({
                "number": current_scene["number"],
                "text": scene_text,
                "start_position": current_scene["start_position"],
                "word_count": len(scene_text.split()),
                "has_explicit_break": False
            })
        
        return scenes
    
    def _analyze_single_scene(self, doc, scene: Dict, index: int) -> Dict[str, Any]:
        """Analyze a single scene for various elements."""
        text = scene["text"]
        text_lower = text.lower()
        
        # Sensory details
        sensory = self._analyze_sensory_details(text_lower)
        
        # Tension and conflict
        tension = self._analyze_tension(text_lower)
        
        # Setting/Location
        setting = self._extract_setting(text)
        
        # Dialogue ratio
        dialogue_ratio = self._calculate_dialogue_ratio(text)
        
        # Action vs description ratio
        action_description = self._analyze_action_description(doc, text)
        
        # Opening and closing strength
        opening = self._analyze_opening(text)
        closing = self._analyze_closing(text)
        
        # Scene structure (beginning, middle, end)
        structure = self._analyze_structure(text)
        
        return {
            "number": scene["number"],
            "word_count": scene["word_count"],
            "start_position": scene["start_position"],
            "sensory_details": sensory,
            "tension_level": tension,
            "setting": setting,
            "dialogue_ratio": dialogue_ratio,
            "action_description_balance": action_description,
            "opening_strength": opening,
            "closing_strength": closing,
            "structure": structure,
            "scene_type": self._classify_scene_type(dialogue_ratio, tension, action_description)
        }
    
    def _analyze_sensory_details(self, text_lower: str) -> Dict[str, Any]:
        """Analyze presence and variety of sensory details."""
        found = defaultdict(list)
        
        for sense, words in self.SENSORY_WORDS.items():
            for word in words:
                if word in text_lower:
                    found[sense].append(word)
        
        senses_used = len([s for s, words in found.items() if words])
        
        return {
            "senses_used": senses_used,
            "details_by_sense": dict(found),
            "sensory_score": min(100, senses_used * 20),
            "missing_senses": [s for s in self.SENSORY_WORDS.keys() if not found.get(s)],
            "feedback": self._get_sensory_feedback(senses_used, found)
        }
    
    def _get_sensory_feedback(self, count: int, details: Dict) -> str:
        """Generate feedback on sensory details."""
        if count >= 4:
            return "Excellent use of multiple senses. Scene feels immersive."
        elif count >= 2:
            missing = [s for s in self.SENSORY_WORDS.keys() if not details.get(s)]
            return f"Good sensory details. Consider adding: {', '.join(missing[:2])}"
        elif count == 1:
            return "Scene relies on single sense. Add more sensory variety for immersion."
        else:
            return "Scene lacks sensory details. Ground readers with sights, sounds, and textures."
    
    def _analyze_tension(self, text_lower: str) -> Dict[str, Any]:
        """Analyze tension and conflict in the scene."""
        tension_count = sum(1 for word in self.TENSION_WORDS if word in text_lower)
        
        # Look for conflict patterns
        conflict_patterns = [
            r'\b(argued|fought|disagreed|confronted)\b',
            r'\b(problem|issue|crisis|danger)\b',
            r'\b(fear|worry|anxiety|dread)\b',
            r'\b(but|however|yet|despite)\b'
        ]
        
        conflict_indicators = sum(
            1 for pattern in conflict_patterns 
            if re.search(pattern, text_lower)
        )
        
        # Calculate tension level
        word_count = len(text_lower.split())
        tension_density = (tension_count + conflict_indicators * 2) / max(word_count, 1) * 100
        
        if tension_density > 2:
            level = "high"
        elif tension_density > 0.5:
            level = "medium"
        else:
            level = "low"
        
        return {
            "level": level,
            "tension_indicators": tension_count,
            "conflict_indicators": conflict_indicators,
            "tension_density": round(tension_density, 2),
            "feedback": self._get_tension_feedback(level, conflict_indicators)
        }
    
    def _get_tension_feedback(self, level: str, conflicts: int) -> str:
        """Generate feedback on scene tension."""
        if level == "high":
            return "High tension scene. Ensure pacing allows readers to breathe."
        elif level == "medium":
            return "Good tension level. Scene maintains reader interest."
        else:
            if conflicts == 0:
                return "Low tension. Consider adding conflict or stakes to engage readers."
            return "Relatively calm scene. Works for transitions or setup."
    
    def _extract_setting(self, text: str) -> Dict[str, Any]:
        """Extract setting/location information from scene."""
        locations = []
        
        for pattern in self.LOCATION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    locations.extend([m for m in match if m and len(m) > 2])
                else:
                    locations.append(match)
        
        # Deduplicate and clean
        unique_locations = list(set(loc.lower() for loc in locations if len(loc) > 2))
        
        # Determine setting clarity
        setting_established = len(unique_locations) > 0
        
        return {
            "locations_mentioned": unique_locations[:5],
            "setting_established": setting_established,
            "primary_location": unique_locations[0] if unique_locations else None,
            "feedback": "Setting is established" if setting_established else "Consider grounding readers with location details"
        }
    
    def _calculate_dialogue_ratio(self, text: str) -> Dict[str, Any]:
        """Calculate ratio of dialogue to narrative."""
        dialogue_pattern = r'["\']([^"\']+)["\']'
        dialogues = re.findall(dialogue_pattern, text)
        
        dialogue_words = sum(len(d.split()) for d in dialogues)
        total_words = len(text.split())
        
        ratio = (dialogue_words / max(total_words, 1)) * 100
        
        if ratio > 60:
            balance = "dialogue-heavy"
        elif ratio > 30:
            balance = "balanced"
        elif ratio > 10:
            balance = "narrative-heavy"
        else:
            balance = "minimal-dialogue"
        
        return {
            "dialogue_percentage": round(ratio, 1),
            "dialogue_word_count": dialogue_words,
            "total_words": total_words,
            "balance": balance
        }
    
    def _analyze_action_description(self, doc, text: str) -> Dict[str, Any]:
        """Analyze balance of action vs description."""
        action_verbs = 0
        descriptive_words = 0
        
        # Simple heuristic using word patterns
        action_patterns = [
            r'\b(ran|walked|jumped|grabbed|threw|hit|kicked|pushed|pulled)\b',
            r'\b(said|asked|replied|shouted|whispered)\b',
            r'\b(opened|closed|entered|left|arrived|departed)\b'
        ]
        
        description_patterns = [
            r'\b(was|were|had been|seemed|appeared|looked)\b',
            r'\b(beautiful|large|small|old|young|dark|bright)\b'
        ]
        
        text_lower = text.lower()
        
        for pattern in action_patterns:
            action_verbs += len(re.findall(pattern, text_lower))
        
        for pattern in description_patterns:
            descriptive_words += len(re.findall(pattern, text_lower))
        
        total = action_verbs + descriptive_words
        if total == 0:
            ratio = 50
        else:
            ratio = (action_verbs / total) * 100
        
        if ratio > 70:
            balance = "action-heavy"
        elif ratio > 30:
            balance = "balanced"
        else:
            balance = "description-heavy"
        
        return {
            "action_ratio": round(ratio, 1),
            "balance": balance,
            "action_count": action_verbs,
            "description_count": descriptive_words
        }
    
    def _analyze_opening(self, text: str) -> Dict[str, Any]:
        """Analyze scene opening strength."""
        first_sentence = text.split('.')[0] if text else ""
        first_para = text.split('\n\n')[0] if text else ""
        
        # Check for strong opening elements
        strong_indicators = {
            "action_start": bool(re.match(r'^[A-Z][a-z]+\s+(ran|walked|grabbed|saw|heard)', first_sentence)),
            "dialogue_start": bool(re.match(r'^["\']', first_sentence.strip())),
            "setting_anchor": bool(re.search(r'^(In the|At the|The room|Outside)', first_sentence)),
            "hook_question": bool(re.search(r'\?', first_sentence)),
            "sensory_detail": any(word in first_para.lower() for word in ["saw", "heard", "felt", "smell"])
        }
        
        strength_score = sum(strong_indicators.values()) * 20
        
        if strength_score >= 60:
            quality = "strong"
        elif strength_score >= 40:
            quality = "adequate"
        else:
            quality = "weak"
        
        return {
            "quality": quality,
            "score": strength_score,
            "indicators": strong_indicators,
            "first_sentence": first_sentence[:100] if first_sentence else "",
            "feedback": self._get_opening_feedback(quality, strong_indicators)
        }
    
    def _get_opening_feedback(self, quality: str, indicators: Dict) -> str:
        """Generate feedback for scene opening."""
        if quality == "strong":
            return "Strong opening that draws readers in immediately."
        elif quality == "adequate":
            suggestions = []
            if not indicators.get("action_start"):
                suggestions.append("action")
            if not indicators.get("sensory_detail"):
                suggestions.append("sensory detail")
            return f"Opening works but could be stronger. Consider starting with {' or '.join(suggestions)}."
        else:
            return "Opening may not grab reader attention. Try starting with action, dialogue, or a compelling image."
    
    def _analyze_closing(self, text: str) -> Dict[str, Any]:
        """Analyze scene closing/ending strength."""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        last_sentence = sentences[-1] if sentences else ""
        last_para_sentences = sentences[-3:] if len(sentences) >= 3 else sentences
        last_para = '. '.join(last_para_sentences)
        
        # Check for strong closing elements
        strong_indicators = {
            "cliffhanger": bool(re.search(r'(but then|suddenly|before|without warning)', last_para.lower())),
            "emotional_beat": bool(re.search(r'(felt|realized|understood|knew|wondered)', last_para.lower())),
            "forward_momentum": bool(re.search(r'(would|must|had to|needed to)', last_para.lower())),
            "image_ending": bool(re.search(r'(darkness|light|silence|shadow|door)', last_para.lower())),
            "dialogue_ending": bool(re.search(r'["\'][^"\']+["\']$', last_sentence))
        }
        
        strength_score = sum(strong_indicators.values()) * 20
        
        if strength_score >= 60:
            quality = "strong"
        elif strength_score >= 40:
            quality = "adequate"
        else:
            quality = "weak"
        
        return {
            "quality": quality,
            "score": strength_score,
            "indicators": strong_indicators,
            "last_sentence": last_sentence[:100] if last_sentence else "",
            "feedback": self._get_closing_feedback(quality, strong_indicators)
        }
    
    def _get_closing_feedback(self, quality: str, indicators: Dict) -> str:
        """Generate feedback for scene closing."""
        if quality == "strong":
            return "Strong ending that propels readers forward."
        elif quality == "adequate":
            return "Scene ends adequately. Consider adding a hook or emotional beat."
        else:
            return "Scene ending could be stronger. End with tension, revelation, or emotional impact."
    
    def _analyze_structure(self, text: str) -> Dict[str, Any]:
        """Analyze scene structure (setup, confrontation, resolution)."""
        words = text.split()
        word_count = len(words)
        
        if word_count < 50:
            return {
                "has_structure": False,
                "feedback": "Scene too short for full structure analysis"
            }
        
        # Divide into thirds
        third = word_count // 3
        beginning = ' '.join(words[:third])
        middle = ' '.join(words[third:2*third])
        end = ' '.join(words[2*third:])
        
        # Check each section
        has_setup = bool(re.search(r'\b(was|were|had|the|in the|at the)\b', beginning.lower()))
        has_conflict = any(word in middle.lower() for word in self.TENSION_WORDS)
        has_change = bool(re.search(r'\b(realized|understood|decided|knew|then)\b', end.lower()))
        
        structure_score = (has_setup + has_conflict + has_change) / 3 * 100
        
        return {
            "has_structure": structure_score > 50,
            "has_setup": has_setup,
            "has_conflict": has_conflict,
            "has_resolution_or_change": has_change,
            "structure_score": round(structure_score, 1),
            "feedback": self._get_structure_feedback(has_setup, has_conflict, has_change)
        }
    
    def _get_structure_feedback(self, setup: bool, conflict: bool, change: bool) -> str:
        """Generate structure feedback."""
        missing = []
        if not setup:
            missing.append("clear setup")
        if not conflict:
            missing.append("conflict or tension")
        if not change:
            missing.append("character shift or resolution")
        
        if not missing:
            return "Scene has good structural elements."
        else:
            return f"Scene could benefit from: {', '.join(missing)}"
    
    def _classify_scene_type(
        self, 
        dialogue: Dict, 
        tension: Dict, 
        action: Dict
    ) -> str:
        """Classify the type of scene."""
        dialogue_percent = dialogue.get("dialogue_percentage", 0)
        tension_level = tension.get("level", "low")
        action_balance = action.get("balance", "balanced")
        
        if dialogue_percent > 50 and tension_level in ["medium", "high"]:
            return "confrontation"
        elif dialogue_percent > 50:
            return "dialogue"
        elif tension_level == "high" and action_balance == "action-heavy":
            return "action"
        elif action_balance == "description-heavy":
            return "descriptive"
        elif tension_level == "low":
            return "transitional"
        else:
            return "mixed"
    
    def _analyze_transitions(self, scenes: List[Dict], text: str) -> Dict[str, Any]:
        """Analyze transitions between scenes."""
        if len(scenes) <= 1:
            return {
                "transition_count": 0,
                "transitions": [],
                "feedback": "Single scene - no transitions to analyze"
            }
        
        transitions = []
        
        for i in range(len(scenes) - 1):
            current_end = scenes[i]["text"][-200:] if len(scenes[i]["text"]) > 200 else scenes[i]["text"]
            next_start = scenes[i+1]["text"][:200] if len(scenes[i+1]["text"]) > 200 else scenes[i+1]["text"]
            
            transition = {
                "from_scene": i + 1,
                "to_scene": i + 2,
                "type": self._classify_transition(current_end, next_start),
                "smoothness": self._rate_transition_smoothness(current_end, next_start)
            }
            transitions.append(transition)
        
        avg_smoothness = sum(t["smoothness"] for t in transitions) / len(transitions)
        
        return {
            "transition_count": len(transitions),
            "transitions": transitions,
            "average_smoothness": round(avg_smoothness, 1),
            "feedback": self._get_transition_feedback(avg_smoothness)
        }
    
    def _classify_transition(self, end_text: str, start_text: str) -> str:
        """Classify the type of transition."""
        start_lower = start_text.lower()
        
        # Time-based
        for time_word in self.TIME_TRANSITIONS:
            if time_word in start_lower:
                return "time_jump"
        
        # Location-based
        if re.search(r'^(In|At|Inside|Outside)\s+', start_text):
            return "location_change"
        
        # Character POV change
        if re.search(r'^[A-Z][a-z]+\s+(was|had|felt|thought)', start_text):
            return "pov_shift"
        
        return "continuous"
    
    def _rate_transition_smoothness(self, end_text: str, start_text: str) -> float:
        """Rate how smooth a transition is (0-100)."""
        score = 70  # Base score
        
        # Bonus for connecting elements
        end_words = set(end_text.lower().split())
        start_words = set(start_text.lower().split())
        
        # Shared significant words suggest continuity
        shared = end_words & start_words - {'the', 'a', 'an', 'is', 'was', 'were', 'and', 'but'}
        if shared:
            score += min(20, len(shared) * 5)
        
        # Penalty for abrupt starts
        if re.match(r'^(Suddenly|Without warning|Then)', start_text):
            score -= 10
        
        return max(0, min(100, score))
    
    def _get_transition_feedback(self, smoothness: float) -> str:
        """Generate transition feedback."""
        if smoothness >= 80:
            return "Transitions between scenes are smooth and well-handled."
        elif smoothness >= 60:
            return "Transitions work but could be more elegantly handled."
        else:
            return "Some transitions feel abrupt. Consider adding bridging elements."
    
    def _analyze_overall_pacing(self, scene_analyses: List[Dict]) -> Dict[str, Any]:
        """Analyze overall pacing across all scenes."""
        if not scene_analyses:
            return {"overall_pace": "unknown", "feedback": "No scenes to analyze"}
        
        # Collect tension levels
        tension_levels = [s["tension_level"]["level"] for s in scene_analyses]
        scene_types = [s["scene_type"] for s in scene_analyses]
        
        # Check for variety
        tension_variety = len(set(tension_levels))
        type_variety = len(set(scene_types))
        
        # Check for tension arc
        tension_map = {"low": 1, "medium": 2, "high": 3}
        tension_values = [tension_map.get(t, 1) for t in tension_levels]
        
        has_rise = any(
            tension_values[i] < tension_values[i+1] 
            for i in range(len(tension_values)-1)
        ) if len(tension_values) > 1 else False
        
        has_fall = any(
            tension_values[i] > tension_values[i+1] 
            for i in range(len(tension_values)-1)
        ) if len(tension_values) > 1 else False
        
        # Determine pacing style
        high_tension_ratio = tension_levels.count("high") / len(tension_levels)
        
        if high_tension_ratio > 0.6:
            pace = "intense"
        elif high_tension_ratio < 0.2 and tension_levels.count("low") / len(tension_levels) > 0.5:
            pace = "slow"
        elif has_rise and has_fall:
            pace = "dynamic"
        else:
            pace = "steady"
        
        return {
            "overall_pace": pace,
            "tension_variety": tension_variety,
            "scene_variety": type_variety,
            "has_tension_arc": has_rise and has_fall,
            "scene_types_breakdown": {t: scene_types.count(t) for t in set(scene_types)},
            "feedback": self._get_pacing_feedback(pace, tension_variety, has_rise, has_fall)
        }
    
    def _get_pacing_feedback(
        self, 
        pace: str, 
        variety: int, 
        has_rise: bool, 
        has_fall: bool
    ) -> str:
        """Generate pacing feedback."""
        feedback = []
        
        if pace == "intense":
            feedback.append("Pacing is very intense. Ensure readers have moments to breathe.")
        elif pace == "slow":
            feedback.append("Pacing is slow. Consider adding more tension or conflict.")
        elif pace == "dynamic":
            feedback.append("Good dynamic pacing with rising and falling tension.")
        else:
            feedback.append("Pacing is steady throughout.")
        
        if variety < 2:
            feedback.append("Consider varying scene types for better rhythm.")
        
        if not has_rise:
            feedback.append("Story could benefit from building tension.")
        
        return " ".join(feedback)
    
    def _generate_scene_feedback(
        self, 
        scenes: List[Dict], 
        transitions: Dict
    ) -> List[Dict[str, Any]]:
        """Generate actionable feedback for scenes."""
        feedback = []
        
        for scene in scenes:
            scene_feedback = []
            
            # Sensory feedback
            if scene["sensory_details"]["senses_used"] < 2:
                scene_feedback.append({
                    "type": "sensory",
                    "priority": "medium",
                    "message": "Add more sensory details",
                    "suggestion": f"Missing: {', '.join(scene['sensory_details']['missing_senses'][:3])}"
                })
            
            # Tension feedback
            if scene["tension_level"]["level"] == "low" and scene["scene_type"] not in ["transitional", "descriptive"]:
                scene_feedback.append({
                    "type": "tension",
                    "priority": "high",
                    "message": "Scene lacks tension",
                    "suggestion": "Add conflict, obstacles, or emotional stakes"
                })
            
            # Opening feedback
            if scene["opening_strength"]["quality"] == "weak":
                scene_feedback.append({
                    "type": "opening",
                    "priority": "high",
                    "message": "Weak scene opening",
                    "suggestion": "Start with action, dialogue, or striking imagery"
                })
            
            # Closing feedback
            if scene["closing_strength"]["quality"] == "weak":
                scene_feedback.append({
                    "type": "closing",
                    "priority": "medium",
                    "message": "Scene ending could be stronger",
                    "suggestion": "End with a hook, revelation, or emotional beat"
                })
            
            if scene_feedback:
                feedback.append({
                    "scene_number": scene["number"],
                    "issues": scene_feedback
                })
        
        return feedback
    
    def _calculate_scene_score(self, scenes: List[Dict], transitions: Dict) -> float:
        """Calculate overall scene quality score."""
        if not scenes:
            return 0.0
        
        scores = []
        
        for scene in scenes:
            scene_score = 60  # Base
            
            # Sensory (up to +20)
            scene_score += scene["sensory_details"]["sensory_score"] * 0.2
            
            # Opening (+10 for strong, +5 for adequate)
            opening_quality = scene["opening_strength"]["quality"]
            if opening_quality == "strong":
                scene_score += 10
            elif opening_quality == "adequate":
                scene_score += 5
            
            # Closing
            closing_quality = scene["closing_strength"]["quality"]
            if closing_quality == "strong":
                scene_score += 10
            elif closing_quality == "adequate":
                scene_score += 5
            
            # Structure
            if scene["structure"].get("has_structure"):
                scene_score += 5
            
            scores.append(min(100, scene_score))
        
        avg_score = sum(scores) / len(scores)
        
        # Adjust for transitions
        if transitions.get("average_smoothness"):
            avg_score = avg_score * 0.8 + transitions["average_smoothness"] * 0.2
        
        return round(avg_score, 1)
    
    def _generate_summary(self, scenes: List[Dict], pacing: Dict) -> str:
        """Generate a summary of the scene analysis."""
        if not scenes:
            return "No scenes detected for analysis."
        
        scene_count = len(scenes)
        pace = pacing.get("overall_pace", "unknown")
        
        # Count scene types
        types = [s["scene_type"] for s in scenes]
        dominant_type = max(set(types), key=types.count) if types else "unknown"
        
        return (
            f"Analyzed {scene_count} scene(s). "
            f"Overall pacing is {pace}. "
            f"Dominant scene type: {dominant_type}. "
            f"{pacing.get('feedback', '')}"
        )


def analyze_scenes(doc, text: str) -> Dict[str, Any]:
    """
    Main entry point for scene analysis.
    
    Args:
        doc: spaCy Doc object
        text: Original text
        
    Returns:
        Complete scene analysis with feedback
    """
    analyzer = SceneAnalyzer()
    return analyzer.analyze_scenes(doc, text)


def get_scene_feedback(doc, text: str) -> List[Dict[str, Any]]:
    """
    Get specific scene improvement suggestions.
    
    Args:
        doc: spaCy Doc object
        text: Original text
        
    Returns:
        List of scene-specific feedback
    """
    analysis = analyze_scenes(doc, text)
    return analysis.get("feedback", [])
