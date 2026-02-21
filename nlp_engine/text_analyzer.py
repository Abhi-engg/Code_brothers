"""
Text Analyzer Module
Core NLP processing using spaCy: tokenization, POS tagging, NER, sentence analysis
"""

import spacy
from collections import Counter
from typing import Dict, List, Tuple, Any

# Load spaCy model once at module level
nlp = spacy.load("en_core_web_sm")


def get_nlp():
    """Return the loaded spaCy model for reuse"""
    return nlp


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


def detect_passive_voice(doc) -> List[Dict[str, Any]]:
    """
    Detect passive voice constructions in the text.
    
    Args:
        doc: spaCy Doc object
        
    Returns:
        List of passive voice sentences with details
    """
    passive_sentences = []
    
    for sent_idx, sent in enumerate(doc.sents):
        # Look for passive voice patterns
        # Passive voice typically has: (be verb) + past participle
        has_passive = False
        passive_verbs = []
        
        for token in sent:
            # Check for passive auxiliary (be verbs) followed by past participle
            if token.dep_ == "auxpass" or (
                token.lemma_ in ["be", "get"] and 
                any(child.tag_ == "VBN" for child in token.children)
            ):
                has_passive = True
                # Find the main verb (past participle)
                for child in token.head.children:
                    if child.tag_ == "VBN":
                        passive_verbs.append(f"{token.text} {child.text}")
                        break
                if not passive_verbs and token.head.tag_ == "VBN":
                    passive_verbs.append(f"{token.text} {token.head.text}")
        
        if has_passive:
            passive_sentences.append({
                "index": sent_idx,
                "sentence": sent.text.strip(),
                "passive_constructions": passive_verbs,
                "severity": "medium",
                "suggestion": "Consider using active voice for clearer, more direct writing"
            })
    
    return passive_sentences


def analyze_sentiment(doc) -> Dict[str, Any]:
    """
    Analyze sentiment polarity and subjectivity of the text.
    
    Args:
        doc: spaCy Doc object
        
    Returns:
        Dictionary with sentiment analysis results
    """
    # Calculate sentiment using word-level analysis
    positive_words = {
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 
        'perfect', 'beautiful', 'awesome', 'outstanding', 'superb', 'brilliant',
        'positive', 'happy', 'delighted', 'pleased', 'satisfied', 'love',
        'best', 'better', 'improve', 'success', 'successful', 'benefit'
    }
    
    negative_words = {
        'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst', 'worse',
        'negative', 'sad', 'unhappy', 'disappointed', 'dissatisfied', 'hate',
        'problem', 'issue', 'fail', 'failure', 'difficult', 'hard', 'wrong',
        'error', 'mistake', 'loss', 'lose', 'damage', 'harm', 'risk'
    }
    
    positive_count = 0
    negative_count = 0
    total_words = 0
    
    for token in doc:
        if token.is_alpha and not token.is_stop:
            total_words += 1
            lemma = token.lemma_.lower()
            if lemma in positive_words:
                positive_count += 1
            elif lemma in negative_words:
                negative_count += 1
    
    # Calculate sentiment score (-1 to +1)
    if total_words > 0:
        sentiment_score = (positive_count - negative_count) / total_words
    else:
        sentiment_score = 0.0
    
    # Determine sentiment category
    if sentiment_score > 0.1:
        sentiment = "positive"
    elif sentiment_score < -0.1:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return {
        "sentiment": sentiment,
        "score": round(sentiment_score, 3),
        "positive_words": positive_count,
        "negative_words": negative_count,
        "total_words_analyzed": total_words,
        "interpretation": f"The text has a {sentiment} tone with a sentiment score of {round(sentiment_score, 3)}"
    }


def analyze_vocabulary_complexity(doc, tokens: List[str]) -> Dict[str, Any]:
    """
    Analyze vocabulary complexity and richness.
    
    Args:
        doc: spaCy Doc object
        tokens: List of token strings
        
    Returns:
        Dictionary with vocabulary metrics
    """
    # Filter out punctuation and spaces
    words = [token.text.lower() for token in doc if token.is_alpha]
    
    if not words:
        return {
            "unique_words": 0,
            "total_words": 0,
            "lexical_diversity": 0.0,
            "advanced_words": 0,
            "complexity_level": "unknown"
        }
    
    # Calculate lexical diversity (Type-Token Ratio)
    unique_words = len(set(words))
    total_words = len(words)
    lexical_diversity = unique_words / total_words if total_words > 0 else 0
    
    # Identify advanced/complex words (more than 3 syllables or 8+ characters)
    advanced_words = []
    for token in doc:
        if token.is_alpha and (len(token.text) >= 8 or token.text.count('tion') > 0 or 
                               token.text.count('sion') > 0):
            advanced_words.append(token.text.lower())
    
    advanced_word_count = len(set(advanced_words))
    advanced_word_ratio = advanced_word_count / unique_words if unique_words > 0 else 0
    
    # Determine complexity level
    if lexical_diversity > 0.7 and advanced_word_ratio > 0.2:
        complexity = "advanced"
    elif lexical_diversity > 0.5 and advanced_word_ratio > 0.1:
        complexity = "intermediate"
    else:
        complexity = "basic"
    
    return {
        "unique_words": unique_words,
        "total_words": total_words,
        "lexical_diversity": round(lexical_diversity, 3),
        "advanced_words": advanced_word_count,
        "advanced_word_ratio": round(advanced_word_ratio, 3),
        "complexity_level": complexity,
        "interpretation": f"Vocabulary is {complexity} with {round(lexical_diversity * 100, 1)}% lexical diversity"
    }


def detect_filler_words(tokens: List[str]) -> Dict[str, Any]:
    """
    Detect filler words and phrases that weaken writing.
    
    Args:
        tokens: List of token strings
        
    Returns:
        Dictionary with filler word analysis
    """
    filler_words = {
        'just', 'really', 'very', 'quite', 'rather', 'somewhat', 'somehow',
        'actually', 'basically', 'literally', 'seriously', 'honestly',
        'obviously', 'clearly', 'simply', 'merely', 'only',
        'perhaps', 'maybe', 'probably', 'possibly', 'presumably',
        'seem', 'seems', 'seemed', 'appear', 'appears', 'appeared',
        'tend', 'tends', 'tended', 'like', 'kind', 'sort'
    }
    
    filler_phrases = [
        'a bit', 'a little', 'kind of', 'sort of', 'type of',
        'in order to', 'due to the fact', 'in spite of the fact',
        'at this point in time', 'for the purpose of'
    ]
    
    text_lower = ' '.join(tokens).lower()
    found_fillers = {}
    total_count = 0
    
    # Count individual filler words
    for word in tokens:
        word_lower = word.lower()
        if word_lower in filler_words:
            found_fillers[word_lower] = found_fillers.get(word_lower, 0) + 1
            total_count += 1
    
    # Check for filler phrases
    for phrase in filler_phrases:
        count = text_lower.count(phrase)
        if count > 0:
            found_fillers[phrase] = count
            total_count += count
    
    severity = "high" if total_count > 10 else "medium" if total_count > 5 else "low"
    
    return {
        "total_fillers": total_count,
        "unique_fillers": len(found_fillers),
        "filler_details": dict(sorted(found_fillers.items(), key=lambda x: x[1], reverse=True)[:10]),
        "severity": severity,
        "suggestion": "Remove unnecessary filler words to make writing more concise and impactful" if total_count > 0 else None
    }