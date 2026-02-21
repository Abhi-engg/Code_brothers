"""
Consistency Checker Module
Track narrative consistency of entities and detect inconsistencies in text
"""

from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict


import re


def check_entity_consistency(doc, entities: List[Tuple[str, str]]) -> Dict[str, Any]:
    """
    Check narrative consistency of named entities across the text.
    
    Args:
        doc: spaCy Doc object
        entities: List of (entity_text, entity_label) tuples
        
    Returns:
        Dictionary containing entity tracking and consistency analysis
    """
    # Track entities by type
    entity_map = defaultdict(list)
    entity_mentions = defaultdict(list)
    
    # Process entities with sentence context
    for sent_idx, sent in enumerate(doc.sents):
        sent_start = sent.start
        sent_end = sent.end
        
        for ent in doc.ents:
            if ent.start >= sent_start and ent.end <= sent_end:
                entity_map[ent.label_].append({
                    "text": ent.text,
                    "sentence_index": sent_idx,
                    "sentence": sent.text.strip(),
                    "start": ent.start_char,
                    "end": ent.end_char
                })
                entity_mentions[ent.text.lower()].append({
                    "text": ent.text,
                    "sentence_index": sent_idx,
                    "label": ent.label_
                })
    
    # Detect potential consistency issues
    issues = []
    
    # Check for name variations (e.g., "John Smith" -> "Smith" -> "John")
    person_variations = detect_name_variations(entity_map.get("PERSON", []))
    for variation in person_variations:
        issues.append({
            "type": "name_variation",
            "severity": "low",
            "details": variation,
            "message": f"Name variation detected: '{variation['variations']}' - ensure consistent naming"
        })
    
    # Check for first mentions without context
    first_mentions = check_first_mentions(doc, entity_map)
    for mention in first_mentions:
        issues.append({
            "type": "abrupt_introduction",
            "severity": "medium",
            "details": mention,
            "message": f"Entity '{mention['entity']}' introduced without context in sentence {mention['sentence_index'] + 1}"
        })
    
    # Check for entity type conflicts
    type_conflicts = detect_type_conflicts(entity_mentions)
    for conflict in type_conflicts:
        issues.append({
            "type": "type_conflict",
            "severity": "high",
            "details": conflict,
            "message": f"'{conflict['entity']}' categorized as different types: {conflict['types']}"
        })
    
    # Build entity timeline
    timeline = build_entity_timeline(doc, entity_map)
    
    return {
        "entities_by_type": {k: v for k, v in entity_map.items()},
        "unique_entities": get_unique_entities(entity_map),
        "entity_frequency": calculate_entity_frequency(entities),
        "issues": issues,
        "issue_count": len(issues),
        "timeline": timeline,
        "consistency_score": calculate_consistency_score(issues, len(entities))
    }


def detect_name_variations(person_entities: List[Dict]) -> List[Dict]:
    """
    Detect variations in person names that might indicate inconsistency.
    
    Args:
        person_entities: List of person entity dictionaries
        
    Returns:
        List of detected name variations
    """
    variations = []
    name_groups = defaultdict(set)
    
    # Group names by potential matches
    all_names = [e["text"] for e in person_entities]
    
    for name in all_names:
        parts = name.split()
        
        # Check if any part matches another name
        for other_name in all_names:
            if name != other_name:
                other_parts = other_name.split()
                
                # Check for partial matches
                if any(p.lower() == other_name.lower() for p in parts):
                    name_groups[name.lower()].add(other_name)
                elif any(p.lower() == name.lower() for p in other_parts):
                    name_groups[other_name.lower()].add(name)
                elif len(parts) > 1 and len(other_parts) > 1:
                    # Check for shared surnames
                    if parts[-1].lower() == other_parts[-1].lower():
                        key = parts[-1].lower()
                        name_groups[key].add(name)
                        name_groups[key].add(other_name)
    
    # Convert to list of variations
    processed = set()
    for key, names in name_groups.items():
        if len(names) > 0 and key not in processed:
            variations.append({
                "base": key,
                "variations": list(names),
                "count": len(names)
            })
            processed.add(key)
    
    return variations


def check_first_mentions(doc, entity_map: Dict) -> List[Dict]:
    """
    Check if entities are introduced without proper context.
    
    Args:
        doc: spaCy Doc object
        entity_map: Dictionary of entities by type
        
    Returns:
        List of abrupt first mentions
    """
    abrupt_mentions = []
    
    # Context indicators that suggest proper introduction
    intro_patterns = [
        r'\b(named|called|known as|introduced|meet)\b',
        r'\b(this is|here is|there is)\b',
        r'\b(a|an|the)\s+(?:man|woman|person|individual|company|organization)\b',
    ]
    
    # Check PERSON and ORG entities for proper introduction
    for label in ["PERSON", "ORG"]:
        entities = entity_map.get(label, [])
        
        # Group by entity text to find first mention
        first_mentions = {}
        for ent in entities:
            text_lower = ent["text"].lower()
            if text_lower not in first_mentions:
                first_mentions[text_lower] = ent
        
        for text, ent in first_mentions.items():
            sentence = ent["sentence"]
            
            # Check if sentence has introduction context
            has_context = any(re.search(p, sentence, re.IGNORECASE) for p in intro_patterns)
            
            # Check if it's a well-known entity (heuristic: all caps or common titles)
            is_well_known = ent["text"].isupper() or any(
                title in ent["text"] for title in ["Mr.", "Mrs.", "Dr.", "Prof.", "President", "CEO"]
            )
            
            # Flag if first sentence and no context
            if ent["sentence_index"] == 0 and not has_context and not is_well_known:
                # Only flag if it's not a common name pattern
                if len(ent["text"].split()) == 1 or label == "ORG":
                    abrupt_mentions.append({
                        "entity": ent["text"],
                        "label": label,
                        "sentence_index": ent["sentence_index"],
                        "sentence": sentence
                    })
    
    return abrupt_mentions


def detect_type_conflicts(entity_mentions: Dict) -> List[Dict]:
    """
    Detect when the same text is categorized as different entity types.
    
    Args:
        entity_mentions: Dictionary mapping entity text to mentions
        
    Returns:
        List of type conflicts
    """
    conflicts = []
    
    for entity_text, mentions in entity_mentions.items():
        labels = set(m["label"] for m in mentions)
        
        if len(labels) > 1:
            conflicts.append({
                "entity": entity_text,
                "types": list(labels),
                "mention_count": len(mentions)
            })
    
    return conflicts


def build_entity_timeline(doc, entity_map: Dict) -> List[Dict]:
    """
    Build a timeline of entity mentions across the document.
    
    Args:
        doc: spaCy Doc object
        entity_map: Dictionary of entities by type
        
    Returns:
        List of timeline entries
    """
    timeline = []
    
    # Flatten all entities with sentence info
    all_entities = []
    for label, entities in entity_map.items():
        for ent in entities:
            all_entities.append({
                "text": ent["text"],
                "label": label,
                "sentence_index": ent["sentence_index"]
            })
    
    # Sort by sentence index
    all_entities.sort(key=lambda x: x["sentence_index"])
    
    # Group by sentence
    current_sentence = -1
    current_group = None
    
    for ent in all_entities:
        if ent["sentence_index"] != current_sentence:
            if current_group:
                timeline.append(current_group)
            current_sentence = ent["sentence_index"]
            current_group = {
                "sentence_index": current_sentence,
                "entities": []
            }
        current_group["entities"].append({
            "text": ent["text"],
            "label": ent["label"]
        })
    
    if current_group:
        timeline.append(current_group)
    
    return timeline


def get_unique_entities(entity_map: Dict) -> Dict[str, List[str]]:
    """Get unique entity names by type."""
    unique = {}
    for label, entities in entity_map.items():
        unique[label] = list(set(e["text"] for e in entities))
    return unique


def calculate_entity_frequency(entities: List[Tuple[str, str]]) -> List[Dict]:
    """Calculate frequency of each entity mention."""
    freq = defaultdict(int)
    labels = {}
    
    for text, label in entities:
        freq[text] += 1
        labels[text] = label
    
    return [
        {"entity": text, "label": labels[text], "count": count}
        for text, count in sorted(freq.items(), key=lambda x: x[1], reverse=True)
    ]


def calculate_consistency_score(issues: List[Dict], entity_count: int) -> float:
    """
    Calculate overall consistency score (0-100).
    
    Args:
        issues: List of detected issues
        entity_count: Total number of entity mentions
        
    Returns:
        Consistency score
    """
    if entity_count == 0:
        return 100.0
    
    # Weight issues by severity
    severity_weights = {"high": 10, "medium": 5, "low": 2}
    
    total_penalty = sum(
        severity_weights.get(issue.get("severity", "low"), 1)
        for issue in issues
    )
    
    # Calculate score (higher is better)
    max_penalty = entity_count * 2  # Reasonable max based on entity count
    score = max(0, 100 - (total_penalty / max(max_penalty, 1) * 100))
    
    return round(score, 2)


def check_pronoun_consistency(doc) -> Dict[str, Any]:
    """
    Check for pronoun usage consistency and potential ambiguity.
    
    Args:
        doc: spaCy Doc object
        
    Returns:
        Dictionary with pronoun analysis
    """
    pronoun_issues = []
    pronouns_by_sentence = defaultdict(list)
    
    for sent_idx, sent in enumerate(doc.sents):
        sentence_pronouns = []
        sentence_nouns = []
        
        for token in sent:
            if token.pos_ == "PRON":
                sentence_pronouns.append({
                    "text": token.text,
                    "type": token.tag_
                })
            elif token.pos_ in ["NOUN", "PROPN"]:
                sentence_nouns.append(token.text)
        
        pronouns_by_sentence[sent_idx] = {
            "pronouns": sentence_pronouns,
            "potential_referents": sentence_nouns
        }
        
        # Check for ambiguous pronouns (pronouns without clear referents)
        if sentence_pronouns and not sentence_nouns:
            # Check if previous sentence has referents
            if sent_idx > 0:
                prev_nouns = pronouns_by_sentence.get(sent_idx - 1, {}).get("potential_referents", [])
                if not prev_nouns:
                    pronoun_issues.append({
                        "sentence_index": sent_idx,
                        "pronouns": [p["text"] for p in sentence_pronouns],
                        "issue": "Pronouns without clear referent in context"
                    })
    
    return {
        "pronouns_by_sentence": dict(pronouns_by_sentence),
        "issues": pronoun_issues,
        "issue_count": len(pronoun_issues)
    }


def analyze_narrative_consistency(doc, entities: List[Tuple[str, str]]) -> Dict[str, Any]:
    """
    Comprehensive narrative consistency analysis.
    
    Args:
        doc: spaCy Doc object
        entities: List of entity tuples
        
    Returns:
        Complete consistency analysis
    """
    entity_analysis = check_entity_consistency(doc, entities)
    pronoun_analysis = check_pronoun_consistency(doc)
    
    # Combine all issues
    all_issues = entity_analysis["issues"] + [
        {
            "type": "pronoun_ambiguity",
            "severity": "low",
            "details": issue,
            "message": issue["issue"]
        }
        for issue in pronoun_analysis["issues"]
    ]
    
    # Calculate overall score
    total_elements = len(entities) + sum(
        len(p["pronouns"]) for p in pronoun_analysis["pronouns_by_sentence"].values()
    )
    overall_score = calculate_consistency_score(all_issues, total_elements)
    
    return {
        "entity_analysis": entity_analysis,
        "pronoun_analysis": pronoun_analysis,
        "all_issues": all_issues,
        "total_issue_count": len(all_issues),
        "overall_consistency_score": overall_score,
        "assessment": get_consistency_assessment(overall_score)
    }


def get_consistency_assessment(score: float) -> str:
    """Get human-readable consistency assessment."""
    if score >= 90:
        return "Excellent - Text maintains strong narrative consistency"
    elif score >= 70:
        return "Good - Minor consistency improvements possible"
    elif score >= 50:
        return "Fair - Several consistency issues detected"
    else:
        return "Needs Improvement - Significant consistency problems found"


class NarrativeConsistencyAnalyzer:
    """
    Class-based Narrative Consistency Analyzer for AI writing assistant.
    
    Detects inconsistencies in long-form writing like stories or scripts:
    - Same character referenced with different names
    - Pronoun confusion
    - Sudden new entities without introduction
    
    Uses spaCy for NLP processing.
    """
    
    def __init__(self):
        """Initialize the analyzer with spaCy model."""
        import spacy
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            from spacy.cli import download
            download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
        # Character memory dictionary to track entities across document
        self.character_memory = {}
    
    def analyze_consistency(self, text: str) -> List[Dict[str, str]]:
        """
        Analyze text for narrative consistency issues.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of issues in format:
            [
                {
                    "issue": "Issue type",
                    "original_text": "Problematic text",
                    "suggestion": "How to fix",
                    "explanation": "Why this is an issue"
                }
            ]
        """
        # Reset character memory for new analysis
        self.character_memory = {}
        issues = []
        
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract entities
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        # Track characters and build memory
        self._build_character_memory(doc)
        
        # Check for name variations
        name_variation_issues = self._check_name_variations(doc)
        issues.extend(name_variation_issues)
        
        # Check for pronoun confusion
        pronoun_issues = self._check_pronoun_confusion(doc)
        issues.extend(pronoun_issues)
        
        # Check for abrupt entity introductions
        introduction_issues = self._check_abrupt_introductions(doc)
        issues.extend(introduction_issues)
        
        # Check for entity type conflicts
        type_conflict_issues = self._check_type_conflicts(doc)
        issues.extend(type_conflict_issues)
        
        return issues
    
    def _build_character_memory(self, doc) -> None:
        """Build memory dictionary of characters in the document."""
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE"]:
                base_name = ent.text.lower()
                
                if base_name not in self.character_memory:
                    self.character_memory[base_name] = {
                        "canonical_name": ent.text,
                        "type": ent.label_,
                        "mentions": [],
                        "variations": set(),
                        "first_mention_sentence": None
                    }
                
                self.character_memory[base_name]["mentions"].append({
                    "text": ent.text,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
                
                # Track first mention
                for sent_idx, sent in enumerate(doc.sents):
                    if ent.start >= sent.start and ent.end <= sent.end:
                        if self.character_memory[base_name]["first_mention_sentence"] is None:
                            self.character_memory[base_name]["first_mention_sentence"] = sent_idx
                        break
    
    def _check_name_variations(self, doc) -> List[Dict[str, str]]:
        """Detect character name variations that may cause confusion."""
        issues = []
        person_names = []
        
        # Collect all person entities
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                person_names.append(ent.text)
        
        # Find potential variations
        name_groups = defaultdict(set)
        
        for name in person_names:
            parts = name.split()
            for other_name in person_names:
                if name != other_name:
                    other_parts = other_name.split()
                    
                    # Check if one name is part of another
                    if any(p.lower() == other_name.lower() for p in parts):
                        name_groups[tuple(sorted([name, other_name]))].add(name)
                        name_groups[tuple(sorted([name, other_name]))].add(other_name)
                    
                    # Check for shared surnames
                    if len(parts) > 1 and len(other_parts) > 1:
                        if parts[-1].lower() == other_parts[-1].lower():
                            name_groups[tuple(sorted([name, other_name]))].add(name)
                            name_groups[tuple(sorted([name, other_name]))].add(other_name)
        
        # Create issues for variations
        processed = set()
        for key, names in name_groups.items():
            if len(names) >= 2 and key not in processed:
                names_list = list(names)
                issues.append({
                    "issue": "Possible character inconsistency",
                    "original_text": ", ".join(names_list),
                    "suggestion": f"Consider using '{names_list[0]}' consistently throughout the text",
                    "explanation": f"Character name appears with multiple variations: {', '.join(names_list)}. This may confuse readers."
                })
                processed.add(key)
        
        return issues
    
    def _check_pronoun_confusion(self, doc) -> List[Dict[str, str]]:
        """Detect potential pronoun confusion or ambiguity."""
        issues = []
        sentences = list(doc.sents)
        
        for sent_idx, sent in enumerate(sentences):
            pronouns = [token for token in sent if token.pos_ == "PRON" and token.text.lower() in ["he", "she", "they", "it", "him", "her", "them"]]
            nouns = [token for token in sent if token.pos_ in ["NOUN", "PROPN"]]
            
            # Check for ambiguous pronouns
            if pronouns and not nouns:
                # Check previous sentence for referents
                prev_nouns = []
                if sent_idx > 0:
                    prev_nouns = [token for token in sentences[sent_idx - 1] if token.pos_ in ["NOUN", "PROPN"]]
                
                if not prev_nouns:
                    pronoun_text = ", ".join([p.text for p in pronouns])
                    issues.append({
                        "issue": "Pronoun confusion",
                        "original_text": sent.text.strip(),
                        "suggestion": "Add a clear noun or name before using pronouns to clarify who is being referenced",
                        "explanation": f"The pronoun(s) '{pronoun_text}' appear without a clear referent in the immediate context."
                    })
            
            # Check for multiple people with same pronouns
            if sent_idx > 0:
                prev_persons = [ent for ent in sentences[sent_idx - 1].ents if ent.label_ == "PERSON"]
                curr_pronouns = [p for p in pronouns if p.text.lower() in ["he", "she", "him", "her"]]
                
                if len(prev_persons) > 1 and curr_pronouns:
                    issues.append({
                        "issue": "Ambiguous pronoun reference",
                        "original_text": sent.text.strip(),
                        "suggestion": f"Specify which person you mean instead of using '{curr_pronouns[0].text}'",
                        "explanation": f"Multiple people ({', '.join([p.text for p in prev_persons])}) were mentioned, making it unclear who the pronoun refers to."
                    })
        
        return issues
    
    def _check_abrupt_introductions(self, doc) -> List[Dict[str, str]]:
        """Detect entities introduced without proper context."""
        issues = []
        sentences = list(doc.sents)
        
        # Introduction patterns
        intro_patterns = [
            r'\b(named|called|known as|introduced|meet)\b',
            r'\b(this is|here is|there is)\b',
            r'\b(a|an|the)\s+(?:man|woman|person|character|protagonist)\b',
        ]
        
        # Track first mentions
        first_mentions = {}
        
        for sent_idx, sent in enumerate(sentences):
            for ent in sent.ents:
                if ent.label_ in ["PERSON", "ORG"] and ent.text.lower() not in first_mentions:
                    first_mentions[ent.text.lower()] = {
                        "text": ent.text,
                        "sentence_index": sent_idx,
                        "sentence": sent.text.strip(),
                        "label": ent.label_
                    }
        
        for entity_key, mention in first_mentions.items():
            sentence = mention["sentence"]
            
            # Check for introduction context
            has_intro = any(re.search(p, sentence, re.IGNORECASE) for p in intro_patterns)
            
            # Check for titles indicating known entity
            has_title = any(t in mention["text"] for t in ["Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "President", "CEO", "Sir", "Lord"])
            
            # First sentence with no context is potentially abrupt
            if mention["sentence_index"] == 0 and not has_intro and not has_title:
                if mention["label"] == "ORG" or (mention["label"] == "PERSON" and len(mention["text"].split()) == 1):
                    issues.append({
                        "issue": "Sudden entity introduction",
                        "original_text": sentence,
                        "suggestion": f"Consider introducing '{mention['text']}' with more context, e.g., 'A character named {mention['text']}...'",
                        "explanation": f"The entity '{mention['text']}' ({mention['label']}) appears without introduction, which may confuse readers unfamiliar with the story."
                    })
        
        return issues
    
    def _check_type_conflicts(self, doc) -> List[Dict[str, str]]:
        """Detect when same text is categorized as different entity types."""
        issues = []
        entity_types = defaultdict(set)
        
        for ent in doc.ents:
            entity_types[ent.text.lower()].add(ent.label_)
        
        for entity_text, labels in entity_types.items():
            if len(labels) > 1:
                issues.append({
                    "issue": "Entity type conflict",
                    "original_text": entity_text,
                    "suggestion": f"Ensure '{entity_text}' is used consistently as one type throughout",
                    "explanation": f"The term '{entity_text}' is identified as multiple types ({', '.join(labels)}), which may indicate inconsistent usage."
                })
        
        return issues
    
    def get_character_memory(self) -> Dict[str, Any]:
        """Return the current character memory dictionary."""
        return self.character_memory
    
    def get_analysis_summary(self, text: str) -> Dict[str, Any]:
        """
        Get comprehensive analysis with summary statistics.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with issues and summary stats
        """
        issues = self.analyze_consistency(text)
        
        # Categorize issues
        issue_categories = defaultdict(int)
        for issue in issues:
            issue_categories[issue["issue"]] += 1
        
        return {
            "issues": issues,
            "total_issues": len(issues),
            "issue_breakdown": dict(issue_categories),
            "characters_tracked": len(self.character_memory),
            "consistency_score": max(0, 100 - (len(issues) * 10))
        }


def check_tense_consistency(doc) -> Dict[str, Any]:
    """
    Check for tense consistency throughout the text.
    
    Args:
        doc: spaCy Doc object
        
    Returns:
        Dictionary with tense analysis and issues
    """
    tense_map = {
        'VBD': 'past',      # past tense
        'VBN': 'past',      # past participle
        'VB': 'present',    # base form
        'VBP': 'present',   # present non-3rd person
        'VBZ': 'present',   # present 3rd person
        'VBG': 'continuous' # gerund/present participle
    }
    
    tense_by_sentence = []
    all_tenses = []
    
    for sent_idx, sent in enumerate(doc.sents):
        sentence_tenses = []
        main_tense = None
        
        for token in sent:
            if token.pos_ == 'VERB' or token.pos_ == 'AUX':
                tense = tense_map.get(token.tag_, 'other')
                if tense != 'other':
                    sentence_tenses.append(tense)
                    all_tenses.append(tense)
        
        # Determine dominant tense for sentence
        if sentence_tenses:
            main_tense = max(set(sentence_tenses), key=sentence_tenses.count)
        
        tense_by_sentence.append({
            "sentence_index": sent_idx,
            "sentence": sent.text.strip(),
            "tenses": sentence_tenses,
            "main_tense": main_tense
        })
    
    # Identify dominant tense in document
    if all_tenses:
        dominant_tense = max(set(all_tenses), key=all_tenses.count)
        tense_distribution = {
            "past": all_tenses.count("past"),
            "present": all_tenses.count("present"),
            "continuous": all_tenses.count("continuous")
        }
    else:
        dominant_tense = None
        tense_distribution = {}
    
    # Detect inconsistencies
    issues = []
    for sent_data in tense_by_sentence:
        if sent_data["main_tense"] and sent_data["main_tense"] != dominant_tense:
            # Allow some flexibility (e.g., dialogue, quotes)
            if sent_data["sentence_index"] > 0:  # Don't flag first sentence
                issues.append({
                    "sentence_index": sent_data["sentence_index"],
                    "sentence": sent_data["sentence"][:100] + "..." if len(sent_data["sentence"]) > 100 else sent_data["sentence"],
                    "tense": sent_data["main_tense"],
                    "expected": dominant_tense,
                    "severity": "medium"
                })
    
    # Calculate consistency score
    if all_tenses:
        consistency_ratio = all_tenses.count(dominant_tense) / len(all_tenses)
        consistency_score = round(consistency_ratio * 100, 2)
    else:
        consistency_score = 100.0
    
    return {
        "dominant_tense": dominant_tense,
        "tense_distribution": tense_distribution,
        "consistency_score": consistency_score,
        "sentences": tense_by_sentence,
        "issues": issues,
        "issue_count": len(issues),
        "interpretation": f"Text primarily uses {dominant_tense} tense" if dominant_tense else "No clear tense detected"
    }


def check_perspective_consistency(doc) -> Dict[str, Any]:
    """
    Check for perspective/point-of-view consistency.
    
    Args:
        doc: spaCy Doc object
        
    Returns:
        Dictionary with perspective analysis
    """
    # Pronoun categories for perspective detection
    first_person = {'i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours', 'myself', 'ourselves'}
    second_person = {'you', 'your', 'yours', 'yourself', 'yourselves'}
    third_person = {'he', 'him', 'his', 'she', 'her', 'hers', 'they', 'them', 'their', 
                     'theirs', 'himself', 'herself', 'themselves', 'it', 'its', 'itself'}
    
    perspective_by_sentence = []
    all_perspectives = []
    
    for sent_idx, sent in enumerate(doc.sents):
        first_count = 0
        second_count = 0
        third_count = 0
        
        for token in sent:
            if token.pos_ == 'PRON':
                lower_text = token.text.lower()
                if lower_text in first_person:
                    first_count += 1
                    all_perspectives.append('first')
                elif lower_text in second_person:
                    second_count += 1
                    all_perspectives.append('second')
                elif lower_text in third_person:
                    third_count += 1
                    all_perspectives.append('third')
        
        # Determine dominant perspective for sentence
        counts = {
            'first': first_count,
            'second': second_count,
            'third': third_count
        }
        main_perspective = max(counts, key=counts.get) if any(counts.values()) else None
        
        perspective_by_sentence.append({
            "sentence_index": sent_idx,
            "sentence": sent.text.strip(),
            "first_person": first_count,
            "second_person": second_count,
            "third_person": third_count,
            "main_perspective": main_perspective if any(counts.values()) else None
        })
    
    # Identify dominant perspective
    if all_perspectives:
        dominant_perspective = max(set(all_perspectives), key=all_perspectives.count)
        perspective_distribution = {
            "first_person": all_perspectives.count("first"),
            "second_person": all_perspectives.count("second"),
            "third_person": all_perspectives.count("third")
        }
    else:
        dominant_perspective = None
        perspective_distribution = {}
    
    # Detect shifts
    issues = []
    prev_perspective = None
    
    for sent_data in perspective_by_sentence:
        curr_perspective = sent_data["main_perspective"]
        
        if curr_perspective and prev_perspective and curr_perspective != prev_perspective:
            # Perspective shift detected
            issues.append({
                "sentence_index": sent_data["sentence_index"],
                "sentence": sent_data["sentence"][:100] + "..." if len(sent_data["sentence"]) > 100 else sent_data["sentence"],
                "from_perspective": prev_perspective,
                "to_perspective": curr_perspective,
                "severity": "medium"
            })
        
        if curr_perspective:
            prev_perspective = curr_perspective
    
    # Calculate consistency
    if all_perspectives:
        consistency_ratio = all_perspectives.count(dominant_perspective) / len(all_perspectives)
        consistency_score = round(consistency_ratio * 100, 2)
    else:
        consistency_score = 100.0
    
    return {
        "dominant_perspective": dominant_perspective,
        "perspective_distribution": perspective_distribution,
        "consistency_score": consistency_score,
        "sentences": perspective_by_sentence,
        "perspective_shifts": issues,
        "shift_count": len(issues),
        "interpretation": get_perspective_interpretation(dominant_perspective, len(issues))
    }


def get_perspective_interpretation(perspective: str, shift_count: int) -> str:
    """Generate interpretation of perspective analysis."""
    if not perspective:
        return "No clear narrative perspective detected"
    
    perspective_names = {
        "first": "first-person",
        "second": "second-person",
        "third": "third-person"
    }
    
    name = perspective_names.get(perspective, perspective)
    
    if shift_count == 0:
        return f"Consistent {name} perspective throughout"
    elif shift_count <= 2:
        return f"Primarily {name} with minor perspective shifts"
    else:
        return f"Multiple perspective shifts detected - may confuse readers"
