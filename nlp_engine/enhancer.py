"""
Enhancer Module
Readability analysis and flow checking for text improvement suggestions
"""

import textstat
from typing import Dict, List, Any, Optional


def calculate_readability(text: str) -> Dict[str, Any]:
    """
    Calculate comprehensive readability metrics using textstat.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary containing various readability scores and interpretations
    """
    if not text or not text.strip():
        return {
            "scores": {},
            "grade_level": "N/A",
            "reading_time": 0,
            "interpretation": "No text provided for analysis"
        }
    
    # Core readability scores
    flesch_reading_ease = textstat.flesch_reading_ease(text)
    flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)
    gunning_fog = textstat.gunning_fog(text)
    smog_index = textstat.smog_index(text)
    coleman_liau = textstat.coleman_liau_index(text)
    automated_readability = textstat.automated_readability_index(text)
    dale_chall = textstat.dale_chall_readability_score(text)
    
    # Text statistics
    word_count = textstat.lexicon_count(text, removepunct=True)
    sentence_count = textstat.sentence_count(text)
    syllable_count = textstat.syllable_count(text)
    
    # Average reading time (assuming 200 words per minute)
    reading_time_minutes = round(word_count / 200, 2)
    
    # Determine overall grade level
    avg_grade = round((flesch_kincaid_grade + gunning_fog + coleman_liau + automated_readability) / 4, 1)
    
    # Interpret Flesch Reading Ease score
    interpretation = interpret_flesch_score(flesch_reading_ease)
    
    return {
        "scores": {
            "flesch_reading_ease": round(flesch_reading_ease, 2),
            "flesch_kincaid_grade": round(flesch_kincaid_grade, 2),
            "gunning_fog": round(gunning_fog, 2),
            "smog_index": round(smog_index, 2),
            "coleman_liau_index": round(coleman_liau, 2),
            "automated_readability_index": round(automated_readability, 2),
            "dale_chall_score": round(dale_chall, 2)
        },
        "statistics": {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "syllable_count": syllable_count,
            "avg_words_per_sentence": round(word_count / sentence_count, 2) if sentence_count > 0 else 0,
            "avg_syllables_per_word": round(syllable_count / word_count, 2) if word_count > 0 else 0
        },
        "grade_level": avg_grade,
        "reading_time_minutes": reading_time_minutes,
        "interpretation": interpretation,
        "difficulty": categorize_difficulty(flesch_reading_ease)
    }


def interpret_flesch_score(score: float) -> str:
    """
    Provide human-readable interpretation of Flesch Reading Ease score.
    
    Args:
        score: Flesch Reading Ease score (0-100+)
        
    Returns:
        Human-readable interpretation string
    """
    if score >= 90:
        return "Very Easy - Easily understood by an average 11-year-old student"
    elif score >= 80:
        return "Easy - Conversational English for consumers"
    elif score >= 70:
        return "Fairly Easy - Understandable by 7th grade students"
    elif score >= 60:
        return "Standard - Plain English, easily understood by 13-15 year olds"
    elif score >= 50:
        return "Fairly Difficult - High school level reading"
    elif score >= 30:
        return "Difficult - College level reading"
    else:
        return "Very Difficult - Best understood by university graduates"


def categorize_difficulty(score: float) -> str:
    """Categorize text difficulty level."""
    if score >= 70:
        return "easy"
    elif score >= 50:
        return "moderate"
    elif score >= 30:
        return "difficult"
    else:
        return "very_difficult"


def check_flow(sentences: List[str], doc) -> Dict[str, Any]:
    """
    Analyze text flow by checking transition words and sentence connections.
    
    Args:
        sentences: List of sentence strings
        doc: spaCy Doc object
        
    Returns:
        Dictionary containing flow analysis
    """
    # Transition word categories
    transition_words = {
        "addition": ["also", "furthermore", "moreover", "additionally", "besides", 
                     "in addition", "likewise", "similarly", "as well"],
        "contrast": ["however", "nevertheless", "nonetheless", "although", "though",
                     "but", "yet", "on the other hand", "in contrast", "conversely",
                     "while", "whereas", "despite", "instead"],
        "cause_effect": ["therefore", "thus", "consequently", "hence", "accordingly",
                         "as a result", "because", "since", "due to", "so"],
        "sequence": ["first", "second", "third", "finally", "then", "next",
                     "subsequently", "afterwards", "meanwhile", "previously"],
        "emphasis": ["indeed", "certainly", "clearly", "obviously", "notably",
                     "especially", "particularly", "importantly", "significantly"],
        "example": ["for example", "for instance", "such as", "specifically",
                    "namely", "to illustrate", "in particular"],
        "conclusion": ["in conclusion", "to summarize", "in summary", "overall",
                       "ultimately", "in short", "to conclude", "finally"]
    }
    
    found_transitions = []
    transitions_by_category = {cat: [] for cat in transition_words}
    
    text_lower = " ".join(sentences).lower()
    
    for category, words in transition_words.items():
        for word in words:
            if word in text_lower:
                found_transitions.append(word)
                transitions_by_category[category].append(word)
    
    # Calculate flow score (0-100)
    transition_density = len(found_transitions) / len(sentences) if sentences else 0
    flow_score = min(100, transition_density * 50)  # Scale to 100
    
    # Check for sentence variety (starting words)
    sentence_starters = []
    for sent in sentences:
        words = sent.split()
        if words:
            sentence_starters.append(words[0].lower())
    
    unique_starters = len(set(sentence_starters))
    starter_variety = unique_starters / len(sentence_starters) if sentence_starters else 0
    
    # Identify potential flow issues
    issues = []
    
    if transition_density < 0.2:
        issues.append({
            "type": "low_transitions",
            "message": "Text has few transition words, which may affect readability",
            "severity": "medium"
        })
    
    if starter_variety < 0.5:
        issues.append({
            "type": "repetitive_starters",
            "message": "Many sentences start with the same word - consider varying sentence beginnings",
            "severity": "low"
        })
    
    return {
        "flow_score": round(flow_score, 2),
        "transition_count": len(found_transitions),
        "transitions_found": found_transitions,
        "transitions_by_category": {k: v for k, v in transitions_by_category.items() if v},
        "sentence_variety": {
            "unique_starters": unique_starters,
            "total_sentences": len(sentences),
            "variety_ratio": round(starter_variety, 2)
        },
        "issues": issues,
        "assessment": assess_flow(flow_score, starter_variety)
    }


def assess_flow(flow_score: float, variety_ratio: float) -> str:
    """Provide overall flow assessment."""
    if flow_score >= 70 and variety_ratio >= 0.7:
        return "Excellent - Text flows well with good transitions and variety"
    elif flow_score >= 50 and variety_ratio >= 0.5:
        return "Good - Decent flow with room for improvement"
    elif flow_score >= 30 or variety_ratio >= 0.3:
        return "Fair - Consider adding more transitions or varying sentence structure"
    else:
        return "Needs Improvement - Text may feel choppy or repetitive"


def get_improvement_suggestions(readability: Dict, flow: Dict) -> List[Dict[str, str]]:
    """
    Generate specific improvement suggestions based on analysis.
    
    Args:
        readability: Readability analysis results
        flow: Flow analysis results
        
    Returns:
        List of improvement suggestions
    """
    suggestions = []
    
    # Readability-based suggestions
    if readability.get("difficulty") == "very_difficult":
        suggestions.append({
            "category": "readability",
            "priority": "high",
            "suggestion": "Consider simplifying complex sentences and using more common words",
            "impact": "Significantly improve reader comprehension"
        })
    
    stats = readability.get("statistics", {})
    if stats.get("avg_words_per_sentence", 0) > 25:
        suggestions.append({
            "category": "sentence_length",
            "priority": "medium",
            "suggestion": "Break down long sentences into shorter, clearer ones",
            "impact": "Improve readability and clarity"
        })
    
    if stats.get("avg_syllables_per_word", 0) > 2:
        suggestions.append({
            "category": "vocabulary",
            "priority": "low",
            "suggestion": "Consider using simpler words where appropriate",
            "impact": "Make text more accessible to wider audience"
        })
    
    # Flow-based suggestions
    if flow.get("flow_score", 0) < 30:
        suggestions.append({
            "category": "flow",
            "priority": "high",
            "suggestion": "Add transition words to connect ideas (e.g., 'however', 'therefore', 'additionally')",
            "impact": "Improve logical flow and coherence"
        })
    
    variety = flow.get("sentence_variety", {})
    if variety.get("variety_ratio", 0) < 0.5:
        suggestions.append({
            "category": "variety",
            "priority": "medium",
            "suggestion": "Vary how you begin sentences to maintain reader interest",
            "impact": "Create more engaging and dynamic writing"
        })
    
    return suggestions
