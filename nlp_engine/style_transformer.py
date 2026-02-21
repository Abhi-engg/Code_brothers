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


def transform_technical_to_plain(text: str) -> Dict[str, Any]:
    """
    Transform technical jargon to plain language for broader audience.
    
    Args:
        text: Input text with technical language
        
    Returns:
        Dictionary with simplified text and changes
    """
    technical_to_plain = {
        "utilize": "use",
        "implement": "carry out",
        "methodology": "method",
        "facilitate": "help",
        "prioritize": "rank",
        "optimize": "improve",
        "leverage": "use",
        "paradigm": "model",
        "synergy": "teamwork",
        "bandwidth": "capacity",
        "interface": "connect",
        "architect": "design",
        "scalable": "flexible",
        "robust": "strong",
        "granular": "detailed",
        "holistic": "complete",
        "iterate": "repeat",
        "synchronize": "coordinate",
        "aggregate": "combine",
        "instantiate": "create",
        "modular": "separate parts",
        "binary": "yes or no",
        "parameter": "setting",
        "algorithm": "process",
        "heuristic": "rule of thumb",
        "recursive": "repeating",
        "compile": "build",
        "deploy": "release",
        "refactor": "reorganize",
        "deprecated": "outdated"
    }
    
    changes = []
    transformed = text
    
    for technical, plain in sorted(technical_to_plain.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(r'\b' + re.escape(technical) + r'\b', re.IGNORECASE)
        matches = pattern.findall(transformed)
        if matches:
            for match in matches:
                changes.append({
                    "type": "simplification",
                    "original": match,
                    "replacement": plain if match.islower() else plain.capitalize(),
                    "reason": "Simplified technical term for broader audience"
                })
            transformed = pattern.sub(
                lambda m: plain.capitalize() if m.group()[0].isupper() else plain,
                transformed
            )
    
    return {
        "original": text,
        "transformed": transformed,
        "changes": changes,
        "change_count": len(changes),
        "style": "plain_language"
    }


def enhance_conciseness(text: str) -> Dict[str, Any]:
    """
    Make text more concise by removing redundant phrases.
    
    Args:
        text: Input text to make concise
        
    Returns:
        Dictionary with concise text and changes
    """
    redundant_phrases = {
        "absolutely essential": "essential",
        "advance planning": "planning",
        "added bonus": "bonus",
        "basic fundamentals": "fundamentals",
        "close proximity": "proximity",
        "completely unanimous": "unanimous",
        "end result": "result",
        "exact same": "same",
        "final outcome": "outcome",
        "free gift": "gift",
        "future plans": "plans",
        "past history": "history",
        "personal opinion": "opinion",
        "true fact": "fact",
        "unexpected surprise": "surprise",
        "usual custom": "custom",
        "very unique": "unique",
        "in order to": "to",
        "due to the fact that": "because",
        "at this point in time": "now",
        "for the purpose of": "for",
        "in the event that": "if",
        "with regard to": "about",
        "in spite of the fact that": "although",
        "until such time as": "until",
        "at the present time": "now",
        "on a daily basis": "daily",
        "in the near future": "soon",
        "by means of": "by",
        "in view of the fact": "because",
        "make a decision": "decide",
        "give consideration to": "consider",
        "take into account": "consider",
        "make an assumption": "assume",
        "conduct an investigation": "investigate"
    }
    
    changes = []
    transformed = text
    
    for redundant, concise in sorted(redundant_phrases.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(r'\b' + re.escape(redundant) + r'\b', re.IGNORECASE)
        matches = pattern.findall(transformed)
        if matches:
            for match in matches:
                changes.append({
                    "type": "conciseness",
                    "original": match,
                    "replacement": concise if match[0].islower() else concise.capitalize(),
                    "reason": "Removed redundancy for conciseness"
                })
            transformed = pattern.sub(
                lambda m: concise.capitalize() if m.group()[0].isupper() else concise,
                transformed
            )
    
    # Remove duplicate words
    transformed = re.sub(r'\b(\w+)\s+\1\b', r'\1', transformed, flags=re.IGNORECASE)
    
    return {
        "original": text,
        "transformed": transformed,
        "changes": changes,
        "change_count": len(changes),
        "improvement": "conciseness"
    }


def strengthen_verbs(text: str) -> Dict[str, Any]:
    """
    Replace weak verbs with stronger alternatives.
    
    Args:
        text: Input text
        
    Returns:
        Dictionary with strengthened text and changes
    """
    weak_to_strong = {
        "is able to": "can",
        "are able to": "can",
        "has the ability to": "can",
        "is going to": "will",
        "are going to": "will",
        "is in charge of": "manages",
        "takes care of": "handles",
        "makes a contribution": "contributes",
        "gives assistance": "assists",
        "makes a recommendation": "recommends",
        "provides information": "informs",
        "carries out": "executes",
        "brings about": "causes",
        "puts emphasis on": "emphasizes",
        "makes a reference to": "references",
        "takes action": "acts",
        "gives approval": "approves",
        "makes changes": "changes",
        "does research": "researches",
        "has an effect on": "affects",
        "makes use of": "uses",
        "takes place": "occurs",
        "gives rise to": "causes",
        "makes progress": "progresses"
    }
    
    changes = []
    transformed = text
    
    for weak, strong in sorted(weak_to_strong.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(r'\b' + re.escape(weak) + r'\b', re.IGNORECASE)
        matches = pattern.findall(transformed)
        if matches:
            for match in matches:
                changes.append({
                    "type": "verb_strengthening",
                    "original": match,
                    "replacement": strong if match[0].islower() else strong.capitalize(),
                    "reason": "Replaced weak verb phrase with stronger verb"
                })
            transformed = pattern.sub(
                lambda m: strong.capitalize() if m.group()[0].isupper() else strong,
                transformed
            )
    
    return {
        "original": text,
        "transformed": transformed,
        "changes": changes,
        "change_count": len(changes),
        "improvement": "verb_strength"
    }


def detect_cliches(text: str) -> Dict[str, Any]:
    """
    Detect clichés and overused phrases in text.
    
    Args:
        text: Input text
        
    Returns:
        Dictionary with detected clichés
    """
    cliches = [
        "at the end of the day",
        "think outside the box",
        "low hanging fruit",
        "paradigm shift",
        "game changer",
        "move the needle",
        "circle back",
        "touch base",
        "ballpark figure",
        "win-win situation",
        "best practices",
        "bleeding edge",
        "cutting edge",
        "state of the art",
        "pushing the envelope",
        "hit the ground running",
        "take it to the next level",
        "bring to the table",
        "add value",
        "drill down",
        "deep dive",
        "hard stop",
        "take offline",
        "open the kimono",
        "boil the ocean",
        "move forward",
        "going forward",
        "reach out",
        "leverage synergies",
        "core competency",
        "value add"
    ]
    
    text_lower = text.lower()
    found_cliches = []
    
    for cliche in cliches:
        if cliche in text_lower:
            # Find all occurrences with context
            start = 0
            while True:
                pos = text_lower.find(cliche, start)
                if pos == -1:
                    break
                
                # Get some context (30 chars before and after)
                context_start = max(0, pos - 30)
                context_end = min(len(text), pos + len(cliche) + 30)
                context = text[context_start:context_end]
                
                found_cliches.append({
                    "cliche": cliche,
                    "position": pos,
                    "context": "..." + context + "...",
                    "suggestion": "Consider rephrasing with original language"
                })
                
                start = pos + 1
    
    return {
        "cliches_found": len(found_cliches),
        "cliches": found_cliches,
        "severity": "high" if len(found_cliches) > 3 else "medium" if len(found_cliches) > 0 else "none",
        "message": f"Found {len(found_cliches)} overused phrases or clichés" if found_cliches else "No clichés detected"
    }
