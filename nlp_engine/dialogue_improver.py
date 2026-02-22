"""
Dialogue Improver Module
Analyze dialogue quality and provide suggestions for improvement
"""

from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import re


class DialogueAnalyzer:
    """
    Analyze and improve dialogue in narrative text.
    Checks for natural flow, variety, pacing, and common dialogue issues.
    """
    
    # Speech tags categorized by type
    BASIC_TAGS = ["said", "asked", "replied", "answered"]
    EXPRESSIVE_TAGS = ["whispered", "shouted", "muttered", "exclaimed", "screamed", 
                       "yelled", "gasped", "sighed", "groaned", "laughed", "cried",
                       "snapped", "growled", "hissed", "murmured", "stammered"]
    NEUTRAL_TAGS = ["stated", "mentioned", "noted", "added", "continued", "began",
                    "explained", "told", "spoke", "called"]
    
    # Common dialogue issues patterns
    ADVERB_SAID_PATTERN = r'\b(said|asked|replied)\s+(\w+ly)\b'
    EXCESSIVE_EXCLAMATION = r'[!]{2,}'
    
    def __init__(self):
        self.all_tags = self.BASIC_TAGS + self.EXPRESSIVE_TAGS + self.NEUTRAL_TAGS
    
    def analyze_dialogue(self, doc, text: str) -> Dict[str, Any]:
        """
        Comprehensive dialogue analysis.
        
        Args:
            doc: spaCy Doc object
            text: Original text
            
        Returns:
            Dictionary with dialogue analysis and improvement suggestions
        """
        # Extract all dialogues
        dialogues = self._extract_dialogues(text)
        
        if not dialogues:
            return {
                "has_dialogue": False,
                "message": "No dialogue detected in the text",
                "dialogue_count": 0
            }
        
        # Analyze speech tags
        tag_analysis = self._analyze_speech_tags(dialogues)
        
        # Check dialogue pacing
        pacing = self._analyze_dialogue_pacing(doc, dialogues)
        
        # Detect dialogue issues
        issues = self._detect_dialogue_issues(dialogues, text)
        
        # Generate improvement suggestions
        suggestions = self._generate_suggestions(dialogues, tag_analysis, issues)
        
        # Analyze dialogue authenticity
        authenticity = self._analyze_authenticity(dialogues)
        
        # Calculate dialogue quality score
        quality_score = self._calculate_quality_score(tag_analysis, issues, pacing)
        
        return {
            "has_dialogue": True,
            "dialogue_count": len(dialogues),
            "dialogues": dialogues,
            "tag_analysis": tag_analysis,
            "pacing": pacing,
            "issues": issues,
            "suggestions": suggestions,
            "authenticity": authenticity,
            "quality_score": quality_score,
            "improved_versions": self._generate_improvements(dialogues[:5])  # Improve first 5
        }
    
    def _extract_dialogues(self, text: str) -> List[Dict[str, Any]]:
        """Extract dialogue segments from text."""
        dialogues = []
        
        # Pattern for dialogue with surrounding context
        # Matches "dialogue" or 'dialogue' with context
        patterns = [
            r'(["\'])(.+?)\1\s*([,.]?\s*(?:' + '|'.join(self.all_tags) + r')\w*[^.!?]*[.!?]?)',
            r'(["\'])(.+?)\1',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                groups = match.groups()
                quote_char = groups[0]
                dialogue_text = groups[1]
                context = groups[2] if len(groups) > 2 else ""
                
                # Find speech tag
                speech_tag = None
                for tag in self.all_tags:
                    if tag in context.lower():
                        speech_tag = tag
                        break
                
                # Avoid duplicates
                if not any(d["text"] == dialogue_text for d in dialogues):
                    dialogues.append({
                        "text": dialogue_text,
                        "quote_char": quote_char,
                        "context": context.strip() if context else None,
                        "speech_tag": speech_tag,
                        "position": match.start(),
                        "word_count": len(dialogue_text.split()),
                        "has_action_beat": bool(re.search(r'\b(turned|looked|walked|sat|stood|nodded|smiled|frowned)\b', context.lower())) if context else False
                    })
        
        return sorted(dialogues, key=lambda x: x["position"])
    
    def _analyze_speech_tags(self, dialogues: List[Dict]) -> Dict[str, Any]:
        """Analyze speech tag usage and variety."""
        tags_used = defaultdict(int)
        tag_categories = {"basic": 0, "expressive": 0, "neutral": 0, "none": 0}
        
        for d in dialogues:
            tag = d.get("speech_tag")
            if tag:
                tags_used[tag] += 1
                if tag in self.BASIC_TAGS:
                    tag_categories["basic"] += 1
                elif tag in self.EXPRESSIVE_TAGS:
                    tag_categories["expressive"] += 1
                else:
                    tag_categories["neutral"] += 1
            else:
                tag_categories["none"] += 1
        
        # Calculate variety score
        unique_tags = len(tags_used)
        total_tagged = sum(tags_used.values())
        variety_score = (unique_tags / max(total_tagged, 1)) * 100 if total_tagged else 0
        
        # Detect overused tags
        overused = [
            {"tag": tag, "count": count, "percentage": round(count/total_tagged*100, 1)}
            for tag, count in tags_used.items()
            if count > 3 and (count / max(total_tagged, 1)) > 0.3
        ]
        
        return {
            "tags_used": dict(tags_used),
            "tag_categories": tag_categories,
            "unique_tag_count": unique_tags,
            "variety_score": round(variety_score, 1),
            "overused_tags": overused,
            "recommendation": self._get_tag_recommendation(tag_categories, overused)
        }
    
    def _get_tag_recommendation(self, categories: Dict, overused: List) -> str:
        """Generate recommendation for speech tag usage."""
        total = sum(categories.values())
        if total == 0:
            return "No dialogue tags detected"
        
        basic_ratio = categories["basic"] / total
        
        if overused:
            return f"Consider varying your dialogue tags. '{overused[0]['tag']}' is used too frequently."
        elif basic_ratio > 0.7:
            return "Good use of simple tags. Consider occasional expressive tags for emphasis."
        elif categories["expressive"] / total > 0.5:
            return "Many expressive tags. Consider more 'said' for better readability."
        else:
            return "Good balance of dialogue tags."
    
    def _analyze_dialogue_pacing(self, doc, dialogues: List[Dict]) -> Dict[str, Any]:
        """Analyze the pacing and rhythm of dialogue in the text."""
        sentences = list(doc.sents)
        total_sentences = len(sentences)
        
        if total_sentences == 0:
            return {"dialogue_density": 0, "pacing": "none"}
        
        # Count dialogue sentences vs narrative
        dialogue_positions = [d["position"] for d in dialogues]
        
        dialogue_sentences = 0
        narrative_sentences = 0
        
        for sent in sentences:
            has_dialogue = any(
                sent.start_char <= pos <= sent.end_char 
                for pos in dialogue_positions
            )
            if has_dialogue:
                dialogue_sentences += 1
            else:
                narrative_sentences += 1
        
        dialogue_density = dialogue_sentences / total_sentences * 100
        
        # Analyze dialogue clustering
        clusters = self._find_dialogue_clusters(dialogues)
        
        # Determine pacing type
        if dialogue_density > 60:
            pacing = "dialogue-heavy"
        elif dialogue_density > 30:
            pacing = "balanced"
        elif dialogue_density > 10:
            pacing = "narrative-heavy"
        else:
            pacing = "minimal-dialogue"
        
        return {
            "dialogue_density": round(dialogue_density, 1),
            "dialogue_sentences": dialogue_sentences,
            "narrative_sentences": narrative_sentences,
            "pacing": pacing,
            "clusters": clusters,
            "avg_dialogue_gap": self._calculate_avg_gap(dialogues)
        }
    
    def _find_dialogue_clusters(self, dialogues: List[Dict]) -> List[Dict]:
        """Find clusters of rapid dialogue exchange."""
        if len(dialogues) < 2:
            return []
        
        clusters = []
        current_cluster = [dialogues[0]]
        
        for i in range(1, len(dialogues)):
            gap = dialogues[i]["position"] - dialogues[i-1]["position"]
            
            # If dialogues are close together (within ~200 chars)
            if gap < 200:
                current_cluster.append(dialogues[i])
            else:
                if len(current_cluster) >= 3:
                    clusters.append({
                        "size": len(current_cluster),
                        "start_position": current_cluster[0]["position"],
                        "type": "rapid_exchange" if len(current_cluster) >= 5 else "dialogue_cluster"
                    })
                current_cluster = [dialogues[i]]
        
        # Don't forget the last cluster
        if len(current_cluster) >= 3:
            clusters.append({
                "size": len(current_cluster),
                "start_position": current_cluster[0]["position"],
                "type": "rapid_exchange" if len(current_cluster) >= 5 else "dialogue_cluster"
            })
        
        return clusters
    
    def _calculate_avg_gap(self, dialogues: List[Dict]) -> float:
        """Calculate average character gap between dialogues."""
        if len(dialogues) < 2:
            return 0
        
        gaps = [
            dialogues[i]["position"] - dialogues[i-1]["position"]
            for i in range(1, len(dialogues))
        ]
        return round(sum(gaps) / len(gaps), 1)
    
    def _detect_dialogue_issues(self, dialogues: List[Dict], text: str) -> List[Dict[str, Any]]:
        """Detect common dialogue problems."""
        issues = []
        
        # Check for "said + adverb" (Tom Swifty)
        for match in re.finditer(self.ADVERB_SAID_PATTERN, text, re.IGNORECASE):
            issues.append({
                "type": "said_adverb",
                "severity": "low",
                "text": match.group(0),
                "position": match.start(),
                "message": "Consider showing emotion through action instead of adverb",
                "suggestion": f"Instead of '{match.group(0)}', show the emotion through character action"
            })
        
        # Check for excessive exclamation marks
        for match in re.finditer(self.EXCESSIVE_EXCLAMATION, text):
            issues.append({
                "type": "excessive_exclamation",
                "severity": "medium",
                "text": match.group(0),
                "position": match.start(),
                "message": "Multiple exclamation marks reduce impact",
                "suggestion": "Use a single exclamation mark for emphasis"
            })
        
        # Check for very long dialogue
        for d in dialogues:
            if d["word_count"] > 50:
                issues.append({
                    "type": "long_dialogue",
                    "severity": "medium",
                    "text": d["text"][:50] + "...",
                    "position": d["position"],
                    "message": f"Dialogue is {d['word_count']} words. Consider breaking into smaller exchanges.",
                    "suggestion": "Long monologues can lose reader attention. Add interruptions or reactions."
                })
        
        # Check for talking heads (dialogue without action)
        consecutive_no_action = 0
        for d in dialogues:
            if not d.get("has_action_beat"):
                consecutive_no_action += 1
                if consecutive_no_action >= 4:
                    issues.append({
                        "type": "talking_heads",
                        "severity": "medium",
                        "text": d["text"][:30],
                        "position": d["position"],
                        "message": "Several consecutive dialogues without action beats",
                        "suggestion": "Add character actions, gestures, or scene description between dialogue"
                    })
                    consecutive_no_action = 0
            else:
                consecutive_no_action = 0
        
        # Check for on-the-nose dialogue
        obvious_patterns = [
            (r"I'?m (so )?(angry|happy|sad|scared|worried)", "emotion_telling"),
            (r"As you know", "as_you_know"),
            (r"Let me explain", "exposition_marker"),
        ]
        
        for d in dialogues:
            for pattern, issue_type in obvious_patterns:
                if re.search(pattern, d["text"], re.IGNORECASE):
                    issues.append({
                        "type": issue_type,
                        "severity": "low",
                        "text": d["text"][:40],
                        "position": d["position"],
                        "message": "Dialogue may be too on-the-nose",
                        "suggestion": "Show emotions through subtext and action rather than direct statements"
                    })
        
        return issues
    
    def _generate_suggestions(
        self, 
        dialogues: List[Dict], 
        tag_analysis: Dict, 
        issues: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate actionable improvement suggestions."""
        suggestions = []
        
        # Tag variety suggestions
        if tag_analysis.get("variety_score", 100) < 30:
            suggestions.append({
                "category": "speech_tags",
                "priority": "medium",
                "title": "Vary your dialogue tags",
                "description": "Your dialogue uses limited speech tags. Mix 'said' with occasional expressive tags.",
                "examples": ["murmured", "whispered", "replied", "answered"]
            })
        
        # Action beat suggestions
        dialogues_without_action = sum(1 for d in dialogues if not d.get("has_action_beat"))
        if dialogues_without_action > len(dialogues) * 0.7:
            suggestions.append({
                "category": "action_beats",
                "priority": "high",
                "title": "Add action beats between dialogue",
                "description": "Many dialogues lack accompanying action. Add character movements or observations.",
                "examples": [
                    "She crossed her arms. 'I don't believe you.'",
                    "'Really?' He raised an eyebrow.",
                    "She glanced at the door. 'We should go.'"
                ]
            })
        
        # Issue-based suggestions
        issue_types = defaultdict(int)
        for issue in issues:
            issue_types[issue["type"]] += 1
        
        if issue_types.get("said_adverb", 0) >= 2:
            suggestions.append({
                "category": "show_dont_tell",
                "priority": "medium",
                "title": "Show emotion through action",
                "description": "Replace 'said angrily' type constructions with character actions.",
                "examples": [
                    "Instead of: 'Stop!' she said angrily.",
                    "Try: 'Stop!' She slammed her fist on the table."
                ]
            })
        
        if issue_types.get("long_dialogue", 0) >= 1:
            suggestions.append({
                "category": "pacing",
                "priority": "medium",
                "title": "Break up long speeches",
                "description": "Long monologues can lose reader attention. Add reactions and interruptions.",
                "examples": [
                    "Add: 'Go on,' he prompted.",
                    "Insert: She paused, gathering her thoughts."
                ]
            })
        
        return suggestions
    
    def _analyze_authenticity(self, dialogues: List[Dict]) -> Dict[str, Any]:
        """Analyze how natural the dialogue sounds."""
        if not dialogues:
            return {"score": 0, "feedback": "No dialogue to analyze"}
        
        # Check for natural speech patterns
        natural_indicators = 0
        formal_indicators = 0
        
        natural_patterns = [
            r"\b(yeah|yep|nope|gonna|wanna|gotta|kinda|sorta)\b",
            r"\b(um|uh|well|like|you know)\b",
            r"^(So|But|And)\s",
            r"[.]{3}",  # Ellipsis for trailing off
            r"—",  # Em dash for interruption
        ]
        
        formal_patterns = [
            r"\b(therefore|furthermore|however|nevertheless)\b",
            r"\b(shall|whom|whilst)\b",
            r"\b(it is|there are|one must)\b"
        ]
        
        for d in dialogues:
            text = d["text"]
            for pattern in natural_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    natural_indicators += 1
                    break
            
            for pattern in formal_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    formal_indicators += 1
                    break
        
        total = len(dialogues)
        natural_ratio = natural_indicators / total if total else 0
        formal_ratio = formal_indicators / total if total else 0
        
        # Determine authenticity style
        if natural_ratio > 0.3:
            style = "conversational"
            feedback = "Dialogue has a natural, conversational tone"
        elif formal_ratio > 0.3:
            style = "formal"
            feedback = "Dialogue is quite formal. Consider if this matches your characters."
        else:
            style = "neutral"
            feedback = "Dialogue is balanced in formality"
        
        return {
            "style": style,
            "natural_ratio": round(natural_ratio * 100, 1),
            "formal_ratio": round(formal_ratio * 100, 1),
            "feedback": feedback,
            "tip": "Match dialogue style to character backgrounds and story setting"
        }
    
    def _calculate_quality_score(
        self, 
        tag_analysis: Dict, 
        issues: List[Dict], 
        pacing: Dict
    ) -> float:
        """Calculate overall dialogue quality score (0-100)."""
        score = 100.0
        
        # Penalize for issues
        severity_penalties = {"high": 8, "medium": 5, "low": 2}
        for issue in issues:
            score -= severity_penalties.get(issue.get("severity", "low"), 2)
        
        # Bonus for variety
        variety_score = tag_analysis.get("variety_score", 50)
        if variety_score > 50:
            score += 5
        elif variety_score < 20:
            score -= 5
        
        # Consider pacing
        if pacing.get("pacing") == "balanced":
            score += 5
        
        return max(0, min(100, round(score, 1)))
    
    def _generate_improvements(self, dialogues: List[Dict]) -> List[Dict[str, Any]]:
        """Generate improved versions of dialogue snippets."""
        improvements = []
        
        for d in dialogues:
            original = d["text"]
            tag = d.get("speech_tag", "said")
            improved = None
            explanation = None
            
            # Improve "said + adverb" patterns in context
            if d.get("context"):
                context = d["context"]
                adverb_match = re.search(r'(said|asked)\s+(\w+ly)', context, re.IGNORECASE)
                if adverb_match:
                    emotion = adverb_match.group(2).replace("ly", "").lower()
                    action_alternatives = {
                        "angri": "slammed their fist on the table",
                        "sadl": "looked away, voice breaking",
                        "happi": "couldn't help but smile",
                        "quietl": "leaned in close",
                        "nervous": "shifted their weight",
                    }
                    for key, action in action_alternatives.items():
                        if key in emotion:
                            improved = f'"{original}" They {action}.'
                            explanation = "Replaced adverb with action beat"
                            break
            
            # Improve very short dialogue
            if not improved and len(original.split()) <= 2:
                improved = f'"{original}" A pause. Then, more firmly, they continued.'
                explanation = "Added beat to short dialogue for emphasis"
            
            if improved:
                improvements.append({
                    "original": f'"{original}"',
                    "improved": improved,
                    "explanation": explanation
                })
        
        return improvements


def analyze_dialogue_quality(doc, text: str) -> Dict[str, Any]:
    """
    Main entry point for dialogue analysis.
    
    Args:
        doc: spaCy Doc object
        text: Original text
        
    Returns:
        Complete dialogue analysis with improvement suggestions
    """
    analyzer = DialogueAnalyzer()
    return analyzer.analyze_dialogue(doc, text)


def get_dialogue_improvements(doc, text: str) -> List[Dict[str, Any]]:
    """
    Get specific dialogue improvement suggestions.
    
    Args:
        doc: spaCy Doc object
        text: Original text
        
    Returns:
        List of improvement suggestions
    """
    analysis = analyze_dialogue_quality(doc, text)
    return analysis.get("suggestions", [])
