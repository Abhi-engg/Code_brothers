"""
Character Consistency Module
Track characters, their traits, relationships, and ensure consistency throughout the narrative
"""

from typing import Dict, List, Any, Tuple, Optional, Set
from collections import defaultdict
import re


class CharacterTracker:
    """
    Track and analyze character consistency across a narrative.
    Monitors traits, relationships, dialogue patterns, and character arcs.
    """
    
    def __init__(self):
        self.characters: Dict[str, Dict[str, Any]] = {}
        self.relationships: List[Dict[str, Any]] = []
        self.dialogue_by_character: Dict[str, List[Dict]] = defaultdict(list)
        self.character_mentions: Dict[str, List[int]] = defaultdict(list)
    
    def analyze_characters(self, doc, text: str) -> Dict[str, Any]:
        """
        Comprehensive character analysis from the text.
        
        Args:
            doc: spaCy Doc object
            text: Original text
            
        Returns:
            Dictionary with character analysis results
        """
        # Extract characters from named entities
        characters = self._extract_characters(doc)
        
        # Analyze character traits
        traits = self._analyze_character_traits(doc, characters)
        
        # Extract dialogue and assign to characters
        dialogue_analysis = self._analyze_dialogue_attribution(doc, text, characters)
        
        # Detect relationships between characters
        relationships = self._detect_relationships(doc, characters)
        
        # Check for consistency issues
        consistency_issues = self._check_character_consistency(
            characters, traits, dialogue_analysis
        )
        
        # Build character profiles
        profiles = self._build_character_profiles(
            characters, traits, dialogue_analysis, relationships
        )
        
        # Calculate character arc presence
        arcs = self._analyze_character_arcs(doc, characters)
        
        return {
            "characters": profiles,
            "character_count": len(characters),
            "relationships": relationships,
            "dialogue_analysis": dialogue_analysis,
            "consistency_issues": consistency_issues,
            "character_arcs": arcs,
            "character_score": self._calculate_character_score(consistency_issues, len(characters))
        }
    
    def _extract_characters(self, doc) -> List[Dict[str, Any]]:
        """Extract character names from PERSON entities."""
        characters = []
        seen = set()
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name_lower = ent.text.lower()
                if name_lower not in seen:
                    characters.append({
                        "name": ent.text,
                        "normalized_name": self._normalize_name(ent.text),
                        "first_appearance": ent.start_char,
                        "mentions": 1
                    })
                    seen.add(name_lower)
                else:
                    # Increment mention count
                    for char in characters:
                        if char["name"].lower() == name_lower:
                            char["mentions"] += 1
                            break
        
        return characters
    
    def _normalize_name(self, name: str) -> str:
        """Normalize character name for matching."""
        # Remove titles
        titles = ["Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Sir", "Lady", "Lord"]
        normalized = name
        for title in titles:
            normalized = normalized.replace(title, "").strip()
        return normalized
    
    def _analyze_character_traits(self, doc, characters: List[Dict]) -> Dict[str, List[str]]:
        """
        Extract traits mentioned for each character.
        Look for adjectives and descriptive phrases near character mentions.
        """
        traits = defaultdict(list)
        character_names = {c["name"].lower(): c["name"] for c in characters}
        
        for sent in doc.sents:
            sent_text_lower = sent.text.lower()
            
            for name_lower, name in character_names.items():
                if name_lower in sent_text_lower or name.split()[0].lower() in sent_text_lower:
                    # Find adjectives in the sentence
                    for token in sent:
                        if token.pos_ == "ADJ":
                            # Check if adjective is describing a person
                            if token.head.pos_ in ["NOUN", "PROPN"] or token.dep_ in ["amod", "acomp"]:
                                trait = token.text.lower()
                                if trait not in traits[name] and len(trait) > 2:
                                    traits[name].append(trait)
                        
                        # Also capture descriptive patterns like "X was Y"
                        if token.dep_ == "attr" and token.pos_ == "ADJ":
                            traits[name].append(token.text.lower())
        
        return dict(traits)
    
    def _analyze_dialogue_attribution(self, doc, text: str, characters: List[Dict]) -> Dict[str, Any]:
        """
        Analyze dialogue and attribute to characters.
        """
        dialogue_pattern = r'["\']([^"\']+)["\']'
        speech_verbs = ["said", "asked", "replied", "whispered", "shouted", "muttered", 
                       "exclaimed", "answered", "called", "screamed", "yelled", "spoke",
                       "told", "explained", "added", "continued", "began"]
        
        dialogues = []
        dialogue_by_character = defaultdict(list)
        
        for sent in doc.sents:
            sent_text = sent.text
            matches = re.findall(dialogue_pattern, sent_text)
            
            if matches:
                # Try to find speaker
                speaker = None
                
                # Look for character name + speech verb pattern
                for char in characters:
                    name = char["name"]
                    first_name = name.split()[0] if name else ""
                    
                    for verb in speech_verbs:
                        patterns = [
                            f"{name} {verb}",
                            f"{first_name} {verb}",
                            f"{verb} {name}",
                            f"{verb} {first_name}",
                        ]
                        for p in patterns:
                            if p.lower() in sent_text.lower():
                                speaker = name
                                break
                        if speaker:
                            break
                    if speaker:
                        break
                
                for dialogue in matches:
                    dialogue_entry = {
                        "text": dialogue,
                        "speaker": speaker,
                        "sentence": sent_text.strip(),
                        "word_count": len(dialogue.split())
                    }
                    dialogues.append(dialogue_entry)
                    if speaker:
                        dialogue_by_character[speaker].append(dialogue_entry)
        
        # Analyze dialogue patterns per character
        character_dialogue_stats = {}
        for char_name, char_dialogues in dialogue_by_character.items():
            if char_dialogues:
                total_words = sum(d["word_count"] for d in char_dialogues)
                avg_length = total_words / len(char_dialogues)
                character_dialogue_stats[char_name] = {
                    "dialogue_count": len(char_dialogues),
                    "total_words": total_words,
                    "avg_dialogue_length": round(avg_length, 1),
                    "sample_dialogues": [d["text"][:50] for d in char_dialogues[:3]]
                }
        
        return {
            "total_dialogues": len(dialogues),
            "attributed_dialogues": sum(1 for d in dialogues if d["speaker"]),
            "unattributed_dialogues": sum(1 for d in dialogues if not d["speaker"]),
            "dialogues": dialogues,
            "by_character": character_dialogue_stats
        }
    
    def _detect_relationships(self, doc, characters: List[Dict]) -> List[Dict[str, Any]]:
        """
        Detect relationships between characters based on context.
        """
        relationships = []
        relationship_indicators = {
            "family": ["mother", "father", "sister", "brother", "daughter", "son", 
                      "wife", "husband", "grandmother", "grandfather", "aunt", "uncle",
                      "cousin", "granddaughter", "grandson", "parent", "child"],
            "romantic": ["love", "loved", "lover", "boyfriend", "girlfriend", "partner",
                        "married", "engaged", "dating", "kiss", "kissed"],
            "professional": ["boss", "employee", "colleague", "coworker", "assistant",
                           "manager", "supervisor", "team", "work"],
            "friendship": ["friend", "best friend", "buddy", "companion", "ally"]
        }
        
        char_names = [c["name"].lower() for c in characters]
        char_names.extend([c["name"].split()[0].lower() for c in characters if len(c["name"].split()) > 1])
        
        for sent in doc.sents:
            sent_lower = sent.text.lower()
            
            # Check if multiple characters mentioned in same sentence
            chars_in_sent = []
            for char in characters:
                if char["name"].lower() in sent_lower or char["name"].split()[0].lower() in sent_lower:
                    chars_in_sent.append(char["name"])
            
            if len(chars_in_sent) >= 2:
                # Look for relationship indicators
                for rel_type, indicators in relationship_indicators.items():
                    for indicator in indicators:
                        if indicator in sent_lower:
                            relationships.append({
                                "characters": chars_in_sent[:2],
                                "relationship_type": rel_type,
                                "indicator": indicator,
                                "context": sent.text.strip()[:100]
                            })
                            break
        
        # Deduplicate relationships
        unique_relationships = []
        seen = set()
        for rel in relationships:
            key = tuple(sorted(rel["characters"])) + (rel["relationship_type"],)
            if key not in seen:
                unique_relationships.append(rel)
                seen.add(key)
        
        return unique_relationships
    
    def _check_character_consistency(
        self, 
        characters: List[Dict], 
        traits: Dict[str, List[str]], 
        dialogue_analysis: Dict
    ) -> List[Dict[str, Any]]:
        """
        Check for character consistency issues.
        """
        issues = []
        
        # Check for name variations
        name_groups = self._group_similar_names([c["name"] for c in characters])
        for group in name_groups:
            if len(group) > 1:
                issues.append({
                    "type": "name_variation",
                    "severity": "low",
                    "message": f"Possible name variations detected: {', '.join(group)}",
                    "suggestion": "Consider using consistent naming throughout the text",
                    "characters": group
                })
        
        # Check for characters with no dialogue (in dialogue-heavy text)
        total_dialogues = dialogue_analysis.get("total_dialogues", 0)
        if total_dialogues > 5:  # Only check if there's substantial dialogue
            chars_with_dialogue = set(dialogue_analysis.get("by_character", {}).keys())
            for char in characters:
                if char["name"] not in chars_with_dialogue and char["mentions"] > 2:
                    issues.append({
                        "type": "silent_character",
                        "severity": "medium",
                        "message": f"'{char['name']}' is mentioned {char['mentions']} times but has no dialogue",
                        "suggestion": "Consider giving this character dialogue or explaining their silence",
                        "characters": [char["name"]]
                    })
        
        # Check for contradictory traits
        contradictory_pairs = [
            ("young", "old"), ("tall", "short"), ("happy", "sad"),
            ("kind", "cruel"), ("brave", "cowardly"), ("rich", "poor")
        ]
        for char_name, char_traits in traits.items():
            trait_set = set(char_traits)
            for t1, t2 in contradictory_pairs:
                if t1 in trait_set and t2 in trait_set:
                    issues.append({
                        "type": "contradictory_traits",
                        "severity": "high",
                        "message": f"'{char_name}' has contradictory traits: '{t1}' and '{t2}'",
                        "suggestion": "Review character description for consistency",
                        "characters": [char_name]
                    })
        
        return issues
    
    def _group_similar_names(self, names: List[str]) -> List[List[str]]:
        """Group names that might refer to the same character."""
        groups = []
        processed = set()
        
        for name in names:
            if name in processed:
                continue
            
            group = [name]
            name_parts = name.lower().split()
            
            for other in names:
                if other != name and other not in processed:
                    other_parts = other.lower().split()
                    
                    # Check if one is part of the other
                    if any(part in other_parts for part in name_parts) or \
                       any(part in name_parts for part in other_parts):
                        group.append(other)
                        processed.add(other)
            
            if len(group) > 1:
                groups.append(group)
            processed.add(name)
        
        return groups
    
    def _build_character_profiles(
        self,
        characters: List[Dict],
        traits: Dict[str, List[str]],
        dialogue_analysis: Dict,
        relationships: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Build complete character profiles."""
        profiles = []
        
        for char in characters:
            name = char["name"]
            
            # Get dialogue stats
            dialogue_stats = dialogue_analysis.get("by_character", {}).get(name, {})
            
            # Get relationships
            char_relationships = [
                r for r in relationships 
                if name in r.get("characters", [])
            ]
            
            profile = {
                "name": name,
                "mentions": char["mentions"],
                "first_appearance": char["first_appearance"],
                "traits": traits.get(name, []),
                "dialogue_count": dialogue_stats.get("dialogue_count", 0),
                "avg_dialogue_length": dialogue_stats.get("avg_dialogue_length", 0),
                "relationships": [
                    {
                        "with": [c for c in r["characters"] if c != name][0] if len(r["characters"]) > 1 else None,
                        "type": r["relationship_type"]
                    }
                    for r in char_relationships
                ],
                "role": self._infer_character_role(char, dialogue_stats, traits.get(name, []))
            }
            profiles.append(profile)
        
        return sorted(profiles, key=lambda x: x["mentions"], reverse=True)
    
    def _infer_character_role(
        self, 
        char: Dict, 
        dialogue_stats: Dict, 
        traits: List[str]
    ) -> str:
        """Infer character role (protagonist, supporting, minor)."""
        mentions = char.get("mentions", 0)
        dialogue_count = dialogue_stats.get("dialogue_count", 0)
        
        if mentions >= 5 or dialogue_count >= 3:
            return "major"
        elif mentions >= 2 or dialogue_count >= 1:
            return "supporting"
        else:
            return "minor"
    
    def _analyze_character_arcs(self, doc, characters: List[Dict]) -> List[Dict[str, Any]]:
        """
        Analyze character development and arcs throughout the text.
        Track how characters change or evolve.
        """
        arcs = []
        
        # Divide text into thirds for arc analysis
        sentences = list(doc.sents)
        if len(sentences) < 6:
            return []  # Too short for arc analysis
        
        third = len(sentences) // 3
        beginning = sentences[:third]
        middle = sentences[third:2*third]
        end = sentences[2*third:]
        
        for char in characters:
            if char["mentions"] < 3:
                continue
            
            name = char["name"]
            name_lower = name.lower()
            first_name_lower = name.split()[0].lower() if name else ""
            
            arc = {
                "character": name,
                "beginning_presence": 0,
                "middle_presence": 0,
                "end_presence": 0,
                "arc_type": "unknown"
            }
            
            # Count presence in each section
            for sent in beginning:
                if name_lower in sent.text.lower() or first_name_lower in sent.text.lower():
                    arc["beginning_presence"] += 1
            
            for sent in middle:
                if name_lower in sent.text.lower() or first_name_lower in sent.text.lower():
                    arc["middle_presence"] += 1
            
            for sent in end:
                if name_lower in sent.text.lower() or first_name_lower in sent.text.lower():
                    arc["end_presence"] += 1
            
            # Determine arc type
            b, m, e = arc["beginning_presence"], arc["middle_presence"], arc["end_presence"]
            if b > 0 and m > 0 and e > 0:
                if e > b:
                    arc["arc_type"] = "rising"
                elif e < b:
                    arc["arc_type"] = "declining"
                elif m > b and m > e:
                    arc["arc_type"] = "peak_middle"
                else:
                    arc["arc_type"] = "consistent"
            elif b > 0 and e == 0:
                arc["arc_type"] = "early_departure"
            elif b == 0 and e > 0:
                arc["arc_type"] = "late_arrival"
            
            arcs.append(arc)
        
        return arcs
    
    def _calculate_character_score(self, issues: List[Dict], char_count: int) -> float:
        """Calculate overall character consistency score."""
        if char_count == 0:
            return 100.0
        
        severity_weights = {"high": 15, "medium": 8, "low": 3}
        total_penalty = sum(
            severity_weights.get(issue.get("severity", "low"), 3)
            for issue in issues
        )
        
        max_penalty = char_count * 10
        score = max(0, 100 - (total_penalty / max(max_penalty, 1) * 100))
        
        return round(score, 1)


def analyze_character_consistency(doc, text: str) -> Dict[str, Any]:
    """
    Main entry point for character consistency analysis.
    
    Args:
        doc: spaCy Doc object
        text: Original text
        
    Returns:
        Complete character analysis
    """
    tracker = CharacterTracker()
    return tracker.analyze_characters(doc, text)
