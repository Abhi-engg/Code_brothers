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


def analyze_paragraph_structure(text: str) -> Dict[str, Any]:
    """
    Analyze paragraph structure and cohesion.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary with paragraph analysis metrics
    """
    # Split text into paragraphs (separated by double newlines or single newlines with blank lines)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    
    if len(paragraphs) <= 1:
        # Treat entire text as one paragraph
        paragraphs = [text]
    
    paragraph_metrics = []
    
    for idx, para in enumerate(paragraphs):
        sentences = [s.strip() for s in para.split('.') if s.strip()]
        words = para.split()
        
        paragraph_metrics.append({
            "index": idx,
            "sentence_count": len(sentences),
            "word_count": len(words),
            "character_count": len(para),
            "avg_sentence_length": round(len(words) / len(sentences), 2) if sentences else 0,
            "too_long": len(words) > 150,
            "too_short": len(words) < 20 and len(paragraphs) > 1
        })
    
    # Calculate paragraph consistency
    word_counts = [p["word_count"] for p in paragraph_metrics]
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
    
    # Identify issues
    issues = []
    for metric in paragraph_metrics:
        if metric["too_long"]:
            issues.append({
                "type": "long_paragraph",
                "paragraph_index": metric["index"] + 1,
                "message": f"Paragraph {metric['index'] + 1} is very long ({metric['word_count']} words)",
                "severity": "medium"
            })
        elif metric["too_short"]:
            issues.append({
                "type": "short_paragraph",
                "paragraph_index": metric["index"] + 1,
                "message": f"Paragraph {metric['index'] + 1} is very short ({metric['word_count']} words)",
                "severity": "low"
            })
    
    return {
        "paragraph_count": len(paragraphs),
        "paragraphs": paragraph_metrics,
        "average_words_per_paragraph": round(avg_words, 2),
        "issues": issues,
        "assessment": "Well-structured" if not issues else f"Found {len(issues)} structural issues"
    }


def calculate_lexical_density(doc) -> Dict[str, Any]:
    """
    Calculate lexical density (ratio of content words to total words).
    Higher density = more informational content.
    
    Args:
        doc: spaCy Doc object
        
    Returns:
        Dictionary with lexical density metrics
    """
    content_pos = {'NOUN', 'VERB', 'ADJ', 'ADV'}
    function_pos = {'ADP', 'DET', 'CONJ', 'PRON', 'AUX', 'PART'}
    
    content_words = []
    function_words = []
    total_words = 0
    
    for token in doc:
        if token.is_alpha and not token.is_space:
            total_words += 1
            if token.pos_ in content_pos:
                content_words.append(token.text)
            elif token.pos_ in function_pos:
                function_words.append(token.text)
    
    if total_words == 0:
        return {
            "lexical_density": 0.0,
            "content_words": 0,
            "function_words": 0,
            "interpretation": "No words to analyze"
        }
    
    lexical_density = len(content_words) / total_words
    
    # Interpret density
    if lexical_density > 0.6:
        interpretation = "High density - Very informational, may be dense for some readers"
        style = "academic/technical"
    elif lexical_density > 0.4:
        interpretation = "Moderate density - Good balance of information and readability"
        style = "formal"
    else:
        interpretation = "Low density - Conversational and easy to read"
        style = "casual"
    
    return {
        "lexical_density": round(lexical_density, 3),
        "content_words": len(content_words),
        "function_words": len(function_words),
        "total_words": total_words,
        "content_ratio": round(len(content_words) / total_words, 3),
        "interpretation": interpretation,
        "suggested_style": style
    }


def analyze_sentence_rhythm(sentences: List[str]) -> Dict[str, Any]:
    """
    Analyze the rhythm and pacing of sentences.
    
    Args:
        sentences: List of sentence strings
        
    Returns:
        Dictionary with rhythm analysis
    """
    if not sentences:
        return {"rhythm_score": 0, "pattern": "none"}
    
    # Get sentence lengths
    lengths = [len(sent.split()) for sent in sentences]
    
    if not lengths:
        return {"rhythm_score": 0, "pattern": "none"}
    
    # Calculate variation
    avg_length = sum(lengths) / len(lengths)
    variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
    std_dev = variance ** 0.5
    
    # Detect patterns (short-long alternation, consistent length, etc.)
    pattern = "varied"
    if std_dev < 3:
        pattern = "monotonous"
    elif std_dev > 15:
        pattern = "highly_varied"
    
    # Check for short-long alternation pattern
    alternations = 0
    for i in range(len(lengths) - 1):
        if (lengths[i] < avg_length < lengths[i + 1]) or (lengths[i] > avg_length > lengths[i + 1]):
            alternations += 1
    
    if alternations > len(lengths) * 0.6:
        pattern = "alternating"
    
    # Calculate rhythm score (50 = ideal)
    rhythm_score = max(0, 100 - abs(50 - (std_dev * 3)))
    
    return {
        "rhythm_score": round(rhythm_score, 2),
        "pattern": pattern,
        "sentence_lengths": lengths,
        "average_length": round(avg_length, 2),
        "std_deviation": round(std_dev, 2),
        "shortest": min(lengths),
        "longest": max(lengths),
        "interpretation": get_rhythm_interpretation(pattern, rhythm_score)
    }


def get_rhythm_interpretation(pattern: str, score: float) -> str:
    """Interpret rhythm analysis results."""
    interpretations = {
        "monotonous": "Sentences are very similar in length - consider varying for better pacing",
        "highly_varied": "Excellent variety in sentence length creates dynamic rhythm",
        "alternating": "Nice alternating pattern between short and long sentences",
        "varied": "Good mix of sentence lengths maintains reader interest"
    }
    
    interpretation = interpretations.get(pattern, "Sentence rhythm is acceptable")
    
    if score < 40:
        interpretation += " (could be improved)"
    elif score > 70:
        interpretation += " (excellent pacing)"
    
    return interpretation
