"""
Text Clarity and Structure Analyzer
Detects readability issues and provides actionable suggestions
"""

import re
import nltk
import textstat
from typing import List, Dict, Any, Tuple
from collections import Counter

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger', quiet=True)

try:
    nltk.data.find('taggers/averaged_perceptron_tagger_eng')
except LookupError:
    nltk.download('averaged_perceptron_tagger_eng', quiet=True)


def detect_long_sentences(text: str, threshold: int = 100) -> List[Dict[str, Any]]:
    """
    Detect sentences longer than the specified word count threshold.
    
    Args:
        text: Input text to analyze
        threshold: Maximum words per sentence (default: 100)
    
    Returns:
        List of issues with suggestions
    """
    issues = []
    sentences = nltk.sent_tokenize(text)
    
    for idx, sentence in enumerate(sentences, 1):
        words = nltk.word_tokenize(sentence)
        word_count = len([w for w in words if w.isalnum()])
        
        if word_count > threshold:
            issues.append({
                "issue": "Long sentence detected",
                "original_text": sentence.strip(),
                "word_count": word_count,
                "sentence_number": idx,
                "suggestion": f"Break this {word_count}-word sentence into 2-3 shorter sentences for better readability.",
                "explanation": f"Sentences with more than {threshold} words can be difficult to follow. Consider splitting at natural break points like conjunctions (and, but, or) or by separating different ideas."
            })
    
    return issues


def detect_passive_voice(text: str) -> List[Dict[str, Any]]:
    """
    Detect passive voice constructions in the text.
    
    Args:
        text: Input text to analyze
    
    Returns:
        List of passive voice issues with suggestions
    """
    issues = []
    sentences = nltk.sent_tokenize(text)
    
    # Common passive voice patterns
    passive_patterns = [
        r'\b(am|is|are|was|were|be|been|being)\s+\w+ed\b',
        r'\b(am|is|are|was|were|be|been|being)\s+\w+en\b',
    ]
    
    for idx, sentence in enumerate(sentences, 1):
        # Tag parts of speech
        words = nltk.word_tokenize(sentence)
        pos_tags = nltk.pos_tag(words)
        
        # Look for passive constructions: be verb + past participle (VBN)
        for i in range(len(pos_tags) - 1):
            word, tag = pos_tags[i]
            next_word, next_tag = pos_tags[i + 1]
            
            # Check for "be" verb followed by past participle
            if word.lower() in ['am', 'is', 'are', 'was', 'were', 'be', 'been', 'being']:
                if next_tag == 'VBN':  # Past participle
                    # Double-check with regex patterns
                    for pattern in passive_patterns:
                        if re.search(pattern, sentence, re.IGNORECASE):
                            issues.append({
                                "issue": "Passive voice detected",
                                "original_text": sentence.strip(),
                                "sentence_number": idx,
                                "passive_phrase": f"{word} {next_word}",
                                "suggestion": "Consider rewriting in active voice to make the sentence more direct and engaging.",
                                "explanation": "Passive voice ('was done by') is less direct than active voice ('did'). Active voice makes writing clearer and more dynamic by emphasizing who performs the action."
                            })
                            break
                    break
    
    return issues


def detect_repetition(text: str, proximity: int = 50, min_word_length: int = 4) -> List[Dict[str, Any]]:
    """
    Detect words repeated close together in the text.
    
    Args:
        text: Input text to analyze
        proximity: Maximum character distance to flag repetitions (default: 50)
        min_word_length: Minimum word length to check (default: 4)
    
    Returns:
        List of repetition issues with suggestions
    """
    issues = []
    
    # Tokenize and clean words
    words = nltk.word_tokenize(text.lower())
    words_with_positions = []
    
    current_pos = 0
    for word in words:
        if word.isalnum() and len(word) >= min_word_length:
            # Find position in original text
            pos = text.lower().find(word, current_pos)
            if pos != -1:
                words_with_positions.append((word, pos))
                current_pos = pos + len(word)
    
    # Track words we've already reported
    reported = set()
    
    for i in range(len(words_with_positions)):
        word1, pos1 = words_with_positions[i]
        
        # Skip common words
        if word1 in ['that', 'this', 'with', 'from', 'have', 'been', 'will', 'their', 'there']:
            continue
        
        for j in range(i + 1, len(words_with_positions)):
            word2, pos2 = words_with_positions[j]
            
            if word1 == word2:
                distance = pos2 - pos1
                
                if distance <= proximity and (word1, pos1, pos2) not in reported:
                    # Extract context
                    start = max(0, pos1 - 20)
                    end = min(len(text), pos2 + len(word2) + 20)
                    context = text[start:end].strip()
                    
                    issues.append({
                        "issue": "Word repetition detected",
                        "repeated_word": word1,
                        "original_text": context,
                        "distance_characters": distance,
                        "suggestion": f"Consider using a synonym or rephrasing to avoid repeating '{word1}' within {distance} characters.",
                        "explanation": "Repeating the same word close together can make writing feel monotonous. Try using synonyms, pronouns, or restructuring sentences to vary your language."
                    })
                    
                    reported.add((word1, pos1, pos2))
                    break
    
    return issues


def readability_score(text: str) -> Dict[str, Any]:
    """
    Calculate various readability metrics for the text.
    
    Args:
        text: Input text to analyze
    
    Returns:
        Dictionary with multiple readability scores and interpretation
    """
    if not text.strip():
        return {
            "error": "Empty text provided"
        }
    
    try:
        flesch_reading_ease = textstat.flesch_reading_ease(text)
        flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)
        gunning_fog = textstat.gunning_fog(text)
        smog_index = textstat.smog_index(text)
        automated_readability = textstat.automated_readability_index(text)
        coleman_liau = textstat.coleman_liau_index(text)
        
        # Determine overall readability level
        avg_grade = (flesch_kincaid_grade + gunning_fog + smog_index + 
                    automated_readability + coleman_liau) / 5
        
        if flesch_reading_ease >= 80:
            difficulty = "Very Easy"
            audience = "5th grade or lower"
        elif flesch_reading_ease >= 60:
            difficulty = "Easy"
            audience = "6th-8th grade"
        elif flesch_reading_ease >= 50:
            difficulty = "Fairly Difficult"
            audience = "High school"
        elif flesch_reading_ease >= 30:
            difficulty = "Difficult"
            audience = "College level"
        else:
            difficulty = "Very Difficult"
            audience = "College graduate or higher"
        
        result = {
            "scores": {
                "flesch_reading_ease": round(flesch_reading_ease, 2),
                "flesch_kincaid_grade": round(flesch_kincaid_grade, 2),
                "gunning_fog": round(gunning_fog, 2),
                "smog_index": round(smog_index, 2),
                "automated_readability_index": round(automated_readability, 2),
                "coleman_liau_index": round(coleman_liau, 2),
                "average_grade_level": round(avg_grade, 2)
            },
            "interpretation": {
                "difficulty": difficulty,
                "target_audience": audience,
                "reading_ease_score": round(flesch_reading_ease, 2)
            },
            "is_low_readability": flesch_reading_ease < 50 or avg_grade > 12,
            "suggestion": "",
            "explanation": ""
        }
        
        # Add suggestions for low readability
        if result["is_low_readability"]:
            result["suggestion"] = "The text has low readability. Consider using shorter sentences, simpler words, and clearer structure."
            result["explanation"] = (
                f"Your text scores {round(flesch_reading_ease, 2)} on the Flesch Reading Ease scale "
                f"(0-100, higher is easier) and requires a {round(avg_grade, 1)} grade level education. "
                f"To improve readability: use shorter sentences, replace complex words with simpler alternatives, "
                f"and break up long paragraphs."
            )
        else:
            result["suggestion"] = "Good readability! Your text is appropriately accessible for your target audience."
            result["explanation"] = (
                f"Your text scores {round(flesch_reading_ease, 2)} on the Flesch Reading Ease scale, "
                f"making it suitable for {audience} readers."
            )
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to calculate readability: {str(e)}",
            "suggestion": "Ensure your text has multiple sentences for accurate readability analysis."
        }


def detect_complex_sentences(text: str) -> List[Dict[str, Any]]:
    """
    Detect overly complex sentences based on structure and vocabulary.
    
    Args:
        text: Input text to analyze
    
    Returns:
        List of complex sentence issues
    """
    issues = []
    sentences = nltk.sent_tokenize(text)
    
    for idx, sentence in enumerate(sentences, 1):
        words = nltk.word_tokenize(sentence)
        
        # Count syllables and long words
        long_words = [w for w in words if len(w) > 10 and w.isalpha()]
        syllable_count = textstat.syllable_count(sentence)
        word_count = len([w for w in words if w.isalpha()])
        
        if word_count == 0:
            continue
        
        avg_syllables = syllable_count / word_count if word_count > 0 else 0
        
        # Complex if: many long words OR high syllable count
        is_complex = len(long_words) >= 3 or avg_syllables > 2.5
        
        if is_complex:
            issues.append({
                "issue": "Complex sentence detected",
                "original_text": sentence.strip(),
                "sentence_number": idx,
                "metrics": {
                    "long_words_count": len(long_words),
                    "average_syllables_per_word": round(avg_syllables, 2),
                    "total_words": word_count
                },
                "long_words": long_words[:5],  # Show first 5
                "suggestion": "Simplify this sentence by using shorter, more common words and breaking complex ideas into multiple sentences.",
                "explanation": f"This sentence contains {len(long_words)} long words and averages {round(avg_syllables, 2)} syllables per word. Simpler vocabulary and shorter sentences improve clarity and reader engagement."
            })
    
    return issues


def analyze_clarity(text: str, long_sentence_threshold: int = 100, 
                    repetition_proximity: int = 50) -> Dict[str, Any]:
    """
    Main function to analyze text clarity and structure.
    Performs all checks and returns comprehensive results.
    
    Args:
        text: Input text to analyze
        long_sentence_threshold: Word count threshold for long sentences (default: 100)
        repetition_proximity: Character distance for repetition detection (default: 50)
    
    Returns:
        Dictionary containing all analysis results and suggestions
    """
    if not text or not text.strip():
        return {
            "error": "Empty text provided",
            "success": False
        }
    
    # Run all detection functions
    long_sentences = detect_long_sentences(text, long_sentence_threshold)
    passive_voice = detect_passive_voice(text)
    repetitions = detect_repetition(text, repetition_proximity)
    readability = readability_score(text)
    complex_sentences = detect_complex_sentences(text)
    
    # Compile statistics
    total_issues = (len(long_sentences) + len(passive_voice) + 
                   len(repetitions) + len(complex_sentences))
    
    if readability.get("is_low_readability", False):
        total_issues += 1
    
    # Generate overall assessment
    if total_issues == 0:
        overall_assessment = "Excellent clarity! Your text is well-structured and easy to read."
        priority = "none"
    elif total_issues <= 3:
        overall_assessment = "Good clarity with minor improvements possible."
        priority = "low"
    elif total_issues <= 7:
        overall_assessment = "Moderate clarity issues detected. Consider the suggestions below."
        priority = "medium"
    else:
        overall_assessment = "Several clarity issues detected. Focus on simplifying sentences and improving flow."
        priority = "high"
    
    # Compile all suggestions
    all_suggestions = []
    
    for issue in long_sentences:
        all_suggestions.append({
            "category": "Long Sentence",
            **issue
        })
    
    for issue in passive_voice:
        all_suggestions.append({
            "category": "Passive Voice",
            **issue
        })
    
    for issue in repetitions:
        all_suggestions.append({
            "category": "Word Repetition",
            **issue
        })
    
    for issue in complex_sentences:
        all_suggestions.append({
            "category": "Complex Sentence",
            **issue
        })
    
    # Add readability as a suggestion if low
    if readability.get("is_low_readability", False):
        all_suggestions.append({
            "category": "Low Readability",
            "issue": "Overall low readability score",
            "suggestion": readability.get("suggestion", ""),
            "explanation": readability.get("explanation", ""),
            "scores": readability.get("scores", {})
        })
    
    return {
        "success": True,
        "input": {
            "text": text,
            "character_count": len(text),
            "word_count": len(text.split()),
            "sentence_count": len(nltk.sent_tokenize(text))
        },
        "analysis": {
            "long_sentences": long_sentences,
            "passive_voice": passive_voice,
            "repetitions": repetitions,
            "complex_sentences": complex_sentences,
            "readability": readability
        },
        "summary": {
            "total_issues": total_issues,
            "issue_breakdown": {
                "long_sentences": len(long_sentences),
                "passive_voice": len(passive_voice),
                "repetitions": len(repetitions),
                "complex_sentences": len(complex_sentences),
                "low_readability": 1 if readability.get("is_low_readability") else 0
            },
            "overall_assessment": overall_assessment,
            "priority": priority
        },
        "suggestions": all_suggestions,
        "readability_scores": readability.get("scores", {}),
        "interpretation": readability.get("interpretation", {})
    }


def analyze_clarity_simple(text):

    return {
        "long_sentences": [],
        "passive_voice": [],
        "readability_score": 70
    }


# Demo and testing
if __name__ == "__main__":
    # Test text with various issues
    test_text = """
    The comprehensive analysis of the text was being conducted by the research team, and it was found that 
    the methodology that was employed was significantly sophisticated and required extensive expertise in 
    natural language processing and computational linguistics to understand the intricate patterns and 
    relationships within the data. The team discovered that many sentences were unnecessarily long and 
    could be simplified. The team also discovered that passive voice was being used extensively throughout 
    the document. This document was written to demonstrate various clarity issues that might be found in 
    academic or technical writing.
    """
    
    print("=" * 80)
    print("TEXT CLARITY AND STRUCTURE ANALYZER")
    print("=" * 80)
    print("\nAnalyzing text...\n")
    
    results = analyze_clarity(test_text)
    
    print(f"Overall Assessment: {results['summary']['overall_assessment']}")
    print(f"Priority: {results['summary']['priority'].upper()}")
    print(f"Total Issues Found: {results['summary']['total_issues']}")
    print(f"\nIssue Breakdown:")
    for issue_type, count in results['summary']['issue_breakdown'].items():
        if count > 0:
            print(f"  - {issue_type.replace('_', ' ').title()}: {count}")
    
    print(f"\n{'=' * 80}")
    print("READABILITY SCORES")
    print("=" * 80)
    print(f"Flesch Reading Ease: {results['readability_scores']['flesch_reading_ease']}")
    print(f"Grade Level: {results['readability_scores']['average_grade_level']}")
    print(f"Difficulty: {results['interpretation']['difficulty']}")
    print(f"Target Audience: {results['interpretation']['target_audience']}")
    
    if results['suggestions']:
        print(f"\n{'=' * 80}")
        print("DETAILED SUGGESTIONS")
        print("=" * 80)
        
        for i, suggestion in enumerate(results['suggestions'][:5], 1):  # Show first 5
            print(f"\n[{i}] {suggestion['category'].upper()}")
            print(f"Issue: {suggestion['issue']}")
            if 'original_text' in suggestion:
                text_preview = suggestion['original_text'][:100]
                if len(suggestion['original_text']) > 100:
                    text_preview += "..."
                print(f"Text: \"{text_preview}\"")
            print(f"Suggestion: {suggestion['suggestion']}")
            print(f"Explanation: {suggestion['explanation']}")
