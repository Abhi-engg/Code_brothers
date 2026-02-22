"""
Text Analyzer Module
Core NLP processing using spaCy: tokenization, POS tagging, NER, sentence analysis
"""

import spacy
from collections import Counter
from typing import Dict, List, Tuple, Any

from nlp_engine.consistency_checker import check_consistency
from nlp_engine.clarity_analyzer import analyze_clarity
from nlp_engine.style_transformer import apply_style
from nlp_engine.explanation import generate_explanation

# Load spaCy model once at module level
nlp = spacy.load("en_core_web_sm")


def get_nlp():
    """Return the loaded spaCy model for reuse"""
    return nlp


def analyze_text(text: str, style: str = "formal") -> Dict[str, Any]:
    """
    Analyze text with style consideration.
    
    Args:
        text: Input text to analyze
        style: Target style (formal, casual, academic)
        
    Returns:
        Dictionary containing analysis results and style information
    """
    # Perform basic analysis
    analysis_result = analyze(text)
    
    # Add style information
    analysis_result["style"] = style
    analysis_result["success"] = True
    
    return analysis_result


def analyze(text: str) -> Dict[str, Any]:
    """
    Perform comprehensive text analysis using spaCy.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary containing sentences, tokens, entities, and POS tags
    """
    doc = nlp(text)
    
    sentences = [sent.text.strip() for sent in doc.sents]
    tokens = [token.text for token in doc if not token.is_space]
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    
    # POS tagging with detailed info
    pos_tags = [
        {
            "token": token.text,
            "pos": token.pos_,
            "tag": token.tag_,
            "lemma": token.lemma_
        }
        for token in doc if not token.is_space
    ]
    
    return {
        "sentences": sentences,
        "tokens": tokens,
        "entities": entities,
        "pos_tags": pos_tags,
        "doc": doc  # Return doc for downstream processing
    }


def detect_long_sentences(sentences: List[str], threshold: int = 100) -> List[Dict[str, Any]]:
    """
    Detect sentences that exceed the word count threshold.
    
    Args:
        sentences: List of sentence strings
        threshold: Maximum acceptable word count (default: 100)
        
    Returns:
        List of dictionaries with long sentence info
    """
    long_sentences = []
    
    for idx, sentence in enumerate(sentences):
        word_count = len(sentence.split())
        if word_count >= threshold:
            long_sentences.append({
                "index": idx,
                "sentence": sentence,
                "word_count": word_count,
                "excess": word_count - threshold,
                "severity": "high" if word_count >= threshold * 1.5 else "medium"
            })
    
    return long_sentences


def detect_repeated_words(tokens: List[str], min_count: int = 3, 
                          exclude_common: bool = True) -> List[Dict[str, Any]]:
    """
    Find words that appear too frequently in the text.
    
    Args:
        tokens: List of token strings
        min_count: Minimum occurrences to flag as repeated
        exclude_common: Whether to exclude common words (articles, prepositions, etc.)
        
    Returns:
        List of dictionaries with repeated word info
    """
    # Common words to exclude from repetition detection
    common_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
        'we', 'they', 'what', 'which', 'who', 'whom', 'whose', 'where', 'when',
        'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
        'so', 'than', 'too', 'very', 'just', 'as', 'if', 'then', 'also'
    }
    
    # Normalize tokens to lowercase for counting
    normalized_tokens = [t.lower() for t in tokens if t.isalpha()]
    
    # Count occurrences
    word_counts = Counter(normalized_tokens)
    
    repeated_words = []
    for word, count in word_counts.most_common():
        if count >= min_count:
            if exclude_common and word in common_words:
                continue
            repeated_words.append({
                "word": word,
                "count": count,
                "frequency": round(count / len(normalized_tokens) * 100, 2) if normalized_tokens else 0,
                "severity": "high" if count >= min_count * 2 else "medium"
            })
    
    return repeated_words


def analyze_sentence_structure(doc) -> List[Dict[str, Any]]:
    """
    Analyze sentence structure for complexity and variety.
    
    Args:
        doc: spaCy Doc object
        
    Returns:
        List of sentence structure analysis
    """
    structures = []
    
    for sent in doc.sents:
        # Count clause indicators
        subordinate_conjunctions = sum(1 for t in sent if t.dep_ == 'mark')
        coordinating_conjunctions = sum(1 for t in sent if t.dep_ == 'cc')
        
        # Determine sentence type
        root = [t for t in sent if t.dep_ == 'ROOT']
        sentence_type = "unknown"
        if root:
            root_token = root[0]
            if sent.text.strip().endswith('?'):
                sentence_type = "interrogative"
            elif sent.text.strip().endswith('!'):
                sentence_type = "exclamatory"
            elif root_token.pos_ == 'VERB' and root_token.tag_ == 'VB':
                sentence_type = "imperative"
            else:
                sentence_type = "declarative"
        
        structures.append({
            "sentence": sent.text.strip(),
            "word_count": len([t for t in sent if not t.is_space]),
            "type": sentence_type,
            "has_subordinate_clause": subordinate_conjunctions > 0,
            "complexity": "complex" if subordinate_conjunctions > 0 else 
                         "compound" if coordinating_conjunctions > 0 else "simple"
        })
    
    return structures


def analyze_text_full(text, style):
    """
    Comprehensive text analysis with consistency, clarity, style transformation,
    and explanations.
    
    Args:
        text: Input text to analyze
        style: Target style for transformation
        
    Returns:
        Dictionary containing enhanced text, consistency report, clarity report,
        and explanation of changes
    """
    consistency_report = check_consistency(text)
    clarity_report = analyze_clarity(text)
    styled_text, style_changes = apply_style(text, style)

    explanation = generate_explanation(
        consistency_report,
        clarity_report,
        style_changes
    )

    return {
        "enhanced_text": styled_text,
        "consistency": consistency_report,
        "clarity": clarity_report,
        "changes": explanation
    }