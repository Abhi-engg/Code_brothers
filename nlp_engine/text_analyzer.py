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
    Uses 200+ words with intensity levels (slight / moderate / strong).
    
    Args:
        doc: spaCy Doc object
        
    Returns:
        Dictionary with sentiment analysis results
    """
    # Intensity-weighted word lists: word → weight
    # slight ~0.3, moderate ~0.6, strong ~1.0
    positive_words = {
        # strong (1.0)
        'excellent': 1.0, 'amazing': 1.0, 'wonderful': 1.0, 'fantastic': 1.0,
        'outstanding': 1.0, 'superb': 1.0, 'brilliant': 1.0, 'exceptional': 1.0,
        'magnificent': 1.0, 'extraordinary': 1.0, 'phenomenal': 1.0, 'spectacular': 1.0,
        'triumph': 1.0, 'masterpiece': 1.0, 'flawless': 1.0, 'impeccable': 1.0,
        'remarkable': 1.0, 'exquisite': 1.0, 'sublime': 1.0, 'unmatched': 1.0,
        'love': 1.0, 'adore': 1.0, 'bliss': 1.0, 'ecstatic': 1.0,
        'thrilling': 1.0, 'glorious': 1.0, 'breathtaking': 1.0,
        # moderate (0.6)
        'good': 0.6, 'great': 0.6, 'perfect': 0.6, 'beautiful': 0.6,
        'awesome': 0.6, 'positive': 0.6, 'happy': 0.6, 'delighted': 0.6,
        'pleased': 0.6, 'satisfied': 0.6, 'best': 0.6, 'better': 0.6,
        'improve': 0.6, 'success': 0.6, 'successful': 0.6, 'benefit': 0.6,
        'impressive': 0.6, 'admirable': 0.6, 'commendable': 0.6, 'favorable': 0.6,
        'rewarding': 0.6, 'enjoyable': 0.6, 'exciting': 0.6, 'inspiring': 0.6,
        'valuable': 0.6, 'worthy': 0.6, 'promising': 0.6, 'premium': 0.6,
        'elegant': 0.6, 'charming': 0.6, 'graceful': 0.6, 'vibrant': 0.6,
        'refreshing': 0.6, 'uplifting': 0.6, 'heartwarming': 0.6, 'cheerful': 0.6,
        'productive': 0.6, 'prosperous': 0.6, 'innovative': 0.6, 'creative': 0.6,
        'reliable': 0.6, 'trustworthy': 0.6, 'genuine': 0.6, 'kind': 0.6,
        'generous': 0.6, 'thoughtful': 0.6, 'talented': 0.6, 'skilled': 0.6,
        'courage': 0.6, 'brave': 0.6, 'heroic': 0.6, 'noble': 0.6,
        # slight (0.3)
        'nice': 0.3, 'fine': 0.3, 'fair': 0.3, 'decent': 0.3,
        'okay': 0.3, 'adequate': 0.3, 'acceptable': 0.3, 'reasonable': 0.3,
        'suitable': 0.3, 'pleasant': 0.3, 'agreeable': 0.3, 'comfortable': 0.3,
        'content': 0.3, 'calm': 0.3, 'steady': 0.3, 'stable': 0.3,
        'useful': 0.3, 'helpful': 0.3, 'practical': 0.3, 'convenient': 0.3,
        'handy': 0.3, 'simple': 0.3, 'clean': 0.3, 'neat': 0.3,
        'smooth': 0.3, 'warm': 0.3, 'safe': 0.3, 'secure': 0.3,
    }
    
    negative_words = {
        # strong (1.0)
        'terrible': 1.0, 'awful': 1.0, 'horrible': 1.0, 'worst': 1.0,
        'catastrophic': 1.0, 'devastating': 1.0, 'disastrous': 1.0, 'dreadful': 1.0,
        'atrocious': 1.0, 'abysmal': 1.0, 'appalling': 1.0, 'deplorable': 1.0,
        'hate': 1.0, 'despise': 1.0, 'loathe': 1.0, 'abhor': 1.0,
        'revolting': 1.0, 'disgusting': 1.0, 'repulsive': 1.0, 'vile': 1.0,
        'horrific': 1.0, 'nightmarish': 1.0, 'toxic': 1.0, 'lethal': 1.0,
        'ruinous': 1.0, 'tragic': 1.0, 'excruciating': 1.0,
        # moderate (0.6)
        'bad': 0.6, 'poor': 0.6, 'worse': 0.6, 'negative': 0.6,
        'sad': 0.6, 'unhappy': 0.6, 'disappointed': 0.6, 'dissatisfied': 0.6,
        'problem': 0.6, 'fail': 0.6, 'failure': 0.6, 'difficult': 0.6,
        'wrong': 0.6, 'error': 0.6, 'mistake': 0.6, 'damage': 0.6,
        'harm': 0.6, 'risk': 0.6, 'loss': 0.6, 'lose': 0.6,
        'painful': 0.6, 'frustrating': 0.6, 'annoying': 0.6, 'stressful': 0.6,
        'exhausting': 0.6, 'boring': 0.6, 'tedious': 0.6, 'mediocre': 0.6,
        'inferior': 0.6, 'flawed': 0.6, 'defective': 0.6, 'broken': 0.6,
        'hostile': 0.6, 'aggressive': 0.6, 'cruel': 0.6, 'harsh': 0.6,
        'bitter': 0.6, 'gloomy': 0.6, 'miserable': 0.6, 'hopeless': 0.6,
        'reckless': 0.6, 'careless': 0.6, 'neglect': 0.6, 'abandon': 0.6,
        'reject': 0.6, 'condemn': 0.6, 'criticize': 0.6, 'blame': 0.6,
        'weak': 0.6, 'vulnerable': 0.6, 'corrupt': 0.6, 'dishonest': 0.6,
        # slight (0.3)
        'hard': 0.3, 'tough': 0.3, 'complex': 0.3, 'tricky': 0.3,
        'unclear': 0.3, 'vague': 0.3, 'confusing': 0.3, 'awkward': 0.3,
        'clumsy': 0.3, 'dull': 0.3, 'ordinary': 0.3, 'bland': 0.3,
        'flat': 0.3, 'dry': 0.3, 'slow': 0.3, 'late': 0.3,
        'missing': 0.3, 'lacking': 0.3, 'limited': 0.3, 'narrow': 0.3,
        'rough': 0.3, 'cold': 0.3, 'distant': 0.3, 'rigid': 0.3,
        'tense': 0.3, 'uneasy': 0.3, 'worried': 0.3, 'nervous': 0.3,
    }
    
    positive_count = 0
    negative_count = 0
    positive_weighted = 0.0
    negative_weighted = 0.0
    total_words = 0
    found_positive: List[Dict] = []
    found_negative: List[Dict] = []
    
    for token in doc:
        if token.is_alpha and not token.is_stop:
            total_words += 1
            lemma = token.lemma_.lower()
            if lemma in positive_words:
                weight = positive_words[lemma]
                positive_count += 1
                positive_weighted += weight
                intensity = "strong" if weight >= 0.9 else ("moderate" if weight >= 0.5 else "slight")
                found_positive.append({"word": token.text, "lemma": lemma, "intensity": intensity, "weight": weight})
            elif lemma in negative_words:
                weight = negative_words[lemma]
                negative_count += 1
                negative_weighted += weight
                intensity = "strong" if weight >= 0.9 else ("moderate" if weight >= 0.5 else "slight")
                found_negative.append({"word": token.text, "lemma": lemma, "intensity": intensity, "weight": weight})
    
    # Calculate weighted sentiment score (-1 to +1)
    if total_words > 0:
        sentiment_score = (positive_weighted - negative_weighted) / total_words
    else:
        sentiment_score = 0.0
    
    # Determine sentiment category
    if sentiment_score > 0.1:
        sentiment = "positive"
    elif sentiment_score < -0.1:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    # Intensity breakdown
    def _count_intensity(items, level):
        return sum(1 for i in items if i["intensity"] == level)
    
    return {
        "sentiment": sentiment,
        "score": round(sentiment_score, 3),
        "positive_words": positive_count,
        "negative_words": negative_count,
        "total_words_analyzed": total_words,
        "interpretation": f"The text has a {sentiment} tone with a weighted sentiment score of {round(sentiment_score, 3)}",
        "intensity_breakdown": {
            "positive": {
                "strong": _count_intensity(found_positive, "strong"),
                "moderate": _count_intensity(found_positive, "moderate"),
                "slight": _count_intensity(found_positive, "slight"),
            },
            "negative": {
                "strong": _count_intensity(found_negative, "strong"),
                "moderate": _count_intensity(found_negative, "moderate"),
                "slight": _count_intensity(found_negative, "slight"),
            },
        },
        "positive_details": found_positive[:20],
        "negative_details": found_negative[:20],
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