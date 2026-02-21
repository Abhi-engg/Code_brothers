"""
Style Transformer Module
Transform text between different writing styles (casual, formal, academic)
"""

import re
from typing import Dict, List, Any, Tuple


# Contraction expansions (casual -> formal)
CONTRACTIONS = {
    "ain't": "is not",
    "aren't": "are not",
    "can't": "cannot",
    "couldn't": "could not",
    "didn't": "did not",
    "doesn't": "does not",
    "don't": "do not",
    "hadn't": "had not",
    "hasn't": "has not",
    "haven't": "have not",
    "he'd": "he would",
    "he'll": "he will",
    "he's": "he is",
    "i'd": "I would",
    "i'll": "I will",
    "i'm": "I am",
    "i've": "I have",
    "isn't": "is not",
    "it'd": "it would",
    "it'll": "it will",
    "it's": "it is",
    "let's": "let us",
    "mightn't": "might not",
    "mustn't": "must not",
    "shan't": "shall not",
    "she'd": "she would",
    "she'll": "she will",
    "she's": "she is",
    "shouldn't": "should not",
    "that's": "that is",
    "there's": "there is",
    "they'd": "they would",
    "they'll": "they will",
    "they're": "they are",
    "they've": "they have",
    "we'd": "we would",
    "we'll": "we will",
    "we're": "we are",
    "we've": "we have",
    "weren't": "were not",
    "what'll": "what will",
    "what're": "what are",
    "what's": "what is",
    "what've": "what have",
    "where's": "where is",
    "who'd": "who would",
    "who'll": "who will",
    "who're": "who are",
    "who's": "who is",
    "who've": "who have",
    "won't": "will not",
    "wouldn't": "would not",
    "you'd": "you would",
    "you'll": "you will",
    "you're": "you are",
    "you've": "you have",
    "gonna": "going to",
    "gotta": "got to",
    "wanna": "want to",
    "kinda": "kind of",
    "sorta": "sort of",
    "lemme": "let me",
    "gimme": "give me",
    "coulda": "could have",
    "shoulda": "should have",
    "woulda": "would have",
    "musta": "must have",
    "oughta": "ought to",
    "y'all": "you all",
    "c'mon": "come on",
    "dunno": "do not know",
}

# Informal to formal word replacements
INFORMAL_TO_FORMAL = {
    # Common informal words
    "ok": "acceptable",
    "okay": "acceptable",
    "cool": "excellent",
    "awesome": "excellent",
    "great": "excellent",
    "nice": "pleasant",
    "good": "satisfactory",
    "bad": "unsatisfactory",
    "stuff": "materials",
    "things": "items",
    "thing": "item",
    "lot": "considerable amount",
    "lots": "numerous",
    "pretty": "quite",
    "really": "significantly",
    "very": "considerably",
    "super": "extremely",
    "totally": "completely",
    "basically": "fundamentally",
    "actually": "in fact",
    "anyway": "regardless",
    "anyways": "regardless",
    "maybe": "perhaps",
    "kind of": "somewhat",
    "sort of": "somewhat",
    "a bit": "slightly",
    "big": "substantial",
    "small": "minimal",
    "huge": "substantial",
    "tiny": "minimal",
    
    # Informal verbs
    "get": "obtain",
    "got": "obtained",
    "buy": "purchase",
    "fix": "repair",
    "start": "commence",
    "end": "conclude",
    "begin": "commence",
    "show": "demonstrate",
    "help": "assist",
    "need": "require",
    "use": "utilize",
    "give": "provide",
    "find": "locate",
    "look at": "examine",
    "look into": "investigate",
    "figure out": "determine",
    "find out": "discover",
    "come up with": "develop",
    "go over": "review",
    "go through": "examine",
    "put together": "assemble",
    "set up": "establish",
    "deal with": "address",
    "get rid of": "eliminate",
    
    # Informal phrases
    "a lot of": "numerous",
    "lots of": "numerous",
    "tons of": "substantial amounts of",
    "loads of": "substantial amounts of",
    "at the end of the day": "ultimately",
    "bottom line": "fundamental conclusion",
    "no way": "impossible",
    "by the way": "incidentally",
    "in a nutshell": "in summary",
    "as a matter of fact": "in fact",
    "for real": "genuinely",
    "for sure": "certainly",
    "right now": "immediately",
    "kind of like": "similar to",
}

# Formal to casual word replacements (reverse transformation)
FORMAL_TO_CASUAL = {
    "obtain": "get",
    "purchase": "buy",
    "commence": "start",
    "conclude": "end",
    "demonstrate": "show",
    "assist": "help",
    "require": "need",
    "utilize": "use",
    "provide": "give",
    "locate": "find",
    "examine": "look at",
    "investigate": "look into",
    "determine": "figure out",
    "discover": "find out",
    "develop": "come up with",
    "establish": "set up",
    "address": "deal with",
    "eliminate": "get rid of",
    "numerous": "a lot of",
    "substantial": "big",
    "minimal": "small",
    "considerable": "a lot",
    "significantly": "really",
    "considerably": "very",
    "extremely": "super",
    "completely": "totally",
    "fundamentally": "basically",
    "regardless": "anyway",
    "perhaps": "maybe",
    "somewhat": "kind of",
    "immediately": "right now",
    "incidentally": "by the way",
    "ultimately": "at the end of the day",
    "in summary": "in a nutshell",
    "certainly": "for sure",
    "excellent": "awesome",
    "satisfactory": "good",
    "unsatisfactory": "bad",
}


def transform_to_formal(text: str) -> Dict[str, Any]:
    """
    Transform casual/informal text to formal style.
    
    Args:
        text: Input text to transform
        
    Returns:
        Dictionary with original text, transformed text, and changes made
    """
    changes = []
    transformed = text
    
    # Step 1: Expand contractions
    for contraction, expansion in CONTRACTIONS.items():
        pattern = re.compile(re.escape(contraction), re.IGNORECASE)
        matches = pattern.findall(transformed)
        if matches:
            for match in matches:
                # Preserve case
                if match[0].isupper():
                    replacement = expansion.capitalize()
                else:
                    replacement = expansion
                changes.append({
                    "type": "contraction",
                    "original": match,
                    "replacement": replacement,
                    "reason": "Expanded contraction for formal style"
                })
            transformed = pattern.sub(lambda m: expansion.capitalize() if m.group()[0].isupper() else expansion, transformed)
    
    # Step 2: Replace informal words/phrases (longer phrases first)
    sorted_informal = sorted(INFORMAL_TO_FORMAL.items(), key=lambda x: len(x[0]), reverse=True)
    
    for informal, formal in sorted_informal:
        # Use word boundaries to avoid partial replacements
        pattern = re.compile(r'\b' + re.escape(informal) + r'\b', re.IGNORECASE)
        matches = pattern.findall(transformed)
        if matches:
            for match in matches:
                if match[0].isupper():
                    replacement = formal.capitalize()
                else:
                    replacement = formal
                changes.append({
                    "type": "word_replacement",
                    "original": match,
                    "replacement": replacement,
                    "reason": "Replaced informal word with formal equivalent"
                })
            transformed = pattern.sub(
                lambda m: formal.capitalize() if m.group()[0].isupper() else formal, 
                transformed
            )
    
    # Step 3: Remove filler words
    filler_words = ["like,", "you know,", "I mean,", "well,", "so,", "um,", "uh,", "basically,"]
    for filler in filler_words:
        pattern = re.compile(re.escape(filler), re.IGNORECASE)
        if pattern.search(transformed):
            changes.append({
                "type": "filler_removal",
                "original": filler,
                "replacement": "",
                "reason": "Removed filler word for conciseness"
            })
            transformed = pattern.sub("", transformed)
    
    # Clean up extra spaces
    transformed = re.sub(r'\s+', ' ', transformed).strip()
    
    return {
        "original": text,
        "transformed": transformed,
        "changes": changes,
        "change_count": len(changes),
        "style": "formal"
    }


def transform_to_casual(text: str) -> Dict[str, Any]:
    """
    Transform formal text to casual style.
    
    Args:
        text: Input text to transform
        
    Returns:
        Dictionary with original text, transformed text, and changes made
    """
    changes = []
    transformed = text
    
    # Replace formal words with casual equivalents
    sorted_formal = sorted(FORMAL_TO_CASUAL.items(), key=lambda x: len(x[0]), reverse=True)
    
    for formal, casual in sorted_formal:
        pattern = re.compile(r'\b' + re.escape(formal) + r'\b', re.IGNORECASE)
        matches = pattern.findall(transformed)
        if matches:
            for match in matches:
                if match[0].isupper():
                    replacement = casual.capitalize()
                else:
                    replacement = casual
                changes.append({
                    "type": "word_replacement",
                    "original": match,
                    "replacement": replacement,
                    "reason": "Replaced formal word with casual equivalent"
                })
            transformed = pattern.sub(
                lambda m: casual.capitalize() if m.group()[0].isupper() else casual, 
                transformed
            )
    
    return {
        "original": text,
        "transformed": transformed,
        "changes": changes,
        "change_count": len(changes),
        "style": "casual"
    }


def transform_style(text: str, target_style: str = "formal") -> Dict[str, Any]:
    """
    Transform text to the specified style.
    
    Args:
        text: Input text to transform
        target_style: Target style ('formal', 'casual', 'academic')
        
    Returns:
        Dictionary with transformation results
    """
    if target_style == "formal":
        return transform_to_formal(text)
    elif target_style == "casual":
        return transform_to_casual(text)
    elif target_style == "academic":
        # Academic is formal + additional academic conventions
        result = transform_to_formal(text)
        result["style"] = "academic"
        # Add academic-specific transformations
        academic_changes = apply_academic_conventions(result["transformed"])
        result["transformed"] = academic_changes["text"]
        result["changes"].extend(academic_changes["changes"])
        result["change_count"] = len(result["changes"])
        return result
    else:
        return {
            "original": text,
            "transformed": text,
            "changes": [],
            "change_count": 0,
            "style": target_style,
            "error": f"Unknown style: {target_style}"
        }


def apply_academic_conventions(text: str) -> Dict[str, Any]:
    """
    Apply academic writing conventions to text.
    
    Args:
        text: Input text (already formalized)
        
    Returns:
        Dictionary with text and changes
    """
    changes = []
    transformed = text
    
    # Academic conventions
    academic_replacements = {
        r'\bI think\b': "It can be argued",
        r'\bI believe\b': "Evidence suggests",
        r'\bI feel\b': "It appears",
        r'\bwe found\b': "the findings indicate",
        r'\byou can see\b': "it is evident",
        r'\bthis shows\b': "this demonstrates",
        r'\bproves\b': "suggests",
        r'\bobviously\b': "evidently",
        r'\bof course\b': "naturally",
        r'\beveryone knows\b': "it is widely accepted",
        r'\bnever\b': "rarely",
        r'\balways\b': "typically",
    }
    
    for pattern, replacement in academic_replacements.items():
        regex = re.compile(pattern, re.IGNORECASE)
        matches = regex.findall(transformed)
        if matches:
            for match in matches:
                changes.append({
                    "type": "academic_convention",
                    "original": match,
                    "replacement": replacement,
                    "reason": "Applied academic writing convention"
                })
            transformed = regex.sub(replacement, transformed)
    
    return {
        "text": transformed,
        "changes": changes
    }


def analyze_current_style(text: str) -> Dict[str, Any]:
    """
    Analyze the current style of the text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary with style analysis
    """
    text_lower = text.lower()
    
    # Count style indicators
    contraction_count = sum(1 for c in CONTRACTIONS if c in text_lower)
    informal_count = sum(1 for word in INFORMAL_TO_FORMAL if word in text_lower)
    formal_count = sum(1 for word in FORMAL_TO_CASUAL if word in text_lower)
    
    # Check for first person
    first_person = len(re.findall(r'\b(I|me|my|mine|we|us|our|ours)\b', text, re.IGNORECASE))
    
    # Check for passive voice indicators
    passive_indicators = len(re.findall(r'\b(was|were|been|being|is|are)\s+\w+ed\b', text, re.IGNORECASE))
    
    # Calculate style scores
    total_words = len(text.split())
    informal_score = (contraction_count + informal_count) / max(total_words, 1) * 100
    formal_score = (formal_count + passive_indicators) / max(total_words, 1) * 100
    
    # Determine dominant style
    if informal_score > formal_score * 1.5:
        dominant_style = "casual"
    elif formal_score > informal_score * 1.5:
        dominant_style = "formal"
    else:
        dominant_style = "neutral"
    
    return {
        "dominant_style": dominant_style,
        "indicators": {
            "contractions": contraction_count,
            "informal_words": informal_count,
            "formal_words": formal_count,
            "first_person_usage": first_person,
            "passive_voice": passive_indicators
        },
        "scores": {
            "informal": round(informal_score, 2),
            "formal": round(formal_score, 2)
        },
        "recommendation": get_style_recommendation(dominant_style)
    }


def get_style_recommendation(current_style: str) -> str:
    """Get recommendation based on current style analysis."""
    recommendations = {
        "casual": "Text is informal. Consider formalizing if intended for professional or academic use.",
        "formal": "Text is formal. Good for professional and academic contexts.",
        "neutral": "Text has a neutral style. Can be adapted for various contexts."
    }
    return recommendations.get(current_style, "Unable to determine style.")
