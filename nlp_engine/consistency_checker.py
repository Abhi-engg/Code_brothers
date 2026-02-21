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
