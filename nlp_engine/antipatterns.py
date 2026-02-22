"""
Anti-Pattern Detection Module  (Phase 8)
=========================================
Detects common writing anti-patterns and provides educational feedback with
"Before → After" examples for every flagged instance.

Categories
----------
1. Adverb overuse          – excessive -ly adverbs, esp. on dialogue tags
2. Show don't tell         – copula + emotion adjective ("was happy")
3. Nominalizations         – heavy -tion/-ment/-ness nouns ("utilization" → "use")
4. Hedge words             – "somewhat", "perhaps", "sort of", "kind of"
5. Redundant modifiers     – "very unique", "absolutely essential"
6. Weak openings           – "There is/are …", "It was …", "I was …"
7. Filter words            – "I saw that …", "I felt …"
8. Info dumps              – long exposition paragraphs (high adj density, no dialogue)
"""

from __future__ import annotations

import re
import math
from typing import Dict, List, Any, Optional, Tuple


# ════════════════════════════════════════════════
#  Constants / wordlists
# ════════════════════════════════════════════════

# Emotion / "telling" adjectives typically following a copula
_TELLING_ADJECTIVES = {
    "happy", "sad", "angry", "upset", "excited", "nervous", "afraid",
    "scared", "worried", "thrilled", "delighted", "furious", "anxious",
    "depressed", "lonely", "bored", "confused", "frustrated", "jealous",
    "proud", "embarrassed", "guilty", "ashamed", "tired", "exhausted",
    "surprised", "shocked", "disgusted", "amused", "grateful",
    "disappointed", "overwhelmed", "terrified", "desperate", "miserable",
    "content", "cheerful", "gloomy", "irritated", "panicked",
}

_COPULA_LEMMAS = {"be", "seem", "appear", "feel", "look", "become", "get", "grow"}

_HEDGE_WORDS: Dict[str, str] = {
    "somewhat":   "Remove the hedge — commit to a stronger statement.",
    "perhaps":    "Replace with a definitive claim or delete.",
    "maybe":      "Be decisive — state things with confidence.",
    "sort of":    "Use a precise descriptor instead.",
    "kind of":    "Use a precise descriptor instead.",
    "quite":      "Specify exactly how much.",
    "rather":     "Delete or replace with a precise qualifier.",
    "a little":   "Quantify or delete.",
    "a bit":      "Quantify or delete.",
    "i think":    "State the fact directly — show, don't tell your uncertainty.",
    "i believe":  "State the fact directly.",
    "i feel like":"State the observation directly.",
    "in my opinion":"Let the argument speak for itself.",
    "it seems":   "Investigate further or state the fact.",
    "to be honest":"Delete — readers assume you're honest.",
    "basically":  "Delete — let the content be self-evident.",
    "actually":   "Usually unnecessary — just state the point.",
    "really":     "Usually unnecessary — the fact is strong enough.",
    "just":       "Delete or replace with a precise word.",
    "probably":   "Use data or commit to a claim.",
}

# Two-word / multi-word hedges (checked via regex)
_HEDGE_MULTIWORD_PATTERNS = [
    (re.compile(r"\bsort\s+of\b", re.I), "sort of"),
    (re.compile(r"\bkind\s+of\b", re.I), "kind of"),
    (re.compile(r"\ba\s+little\b", re.I), "a little"),
    (re.compile(r"\ba\s+bit\b", re.I), "a bit"),
    (re.compile(r"\bi\s+think\b", re.I), "i think"),
    (re.compile(r"\bi\s+believe\b", re.I), "i believe"),
    (re.compile(r"\bi\s+feel\s+like\b", re.I), "i feel like"),
    (re.compile(r"\bin\s+my\s+opinion\b", re.I), "in my opinion"),
    (re.compile(r"\bit\s+seems\b", re.I), "it seems"),
    (re.compile(r"\bto\s+be\s+honest\b", re.I), "to be honest"),
]

_REDUNDANT_MODIFIERS: Dict[str, Tuple[str, str]] = {
    # key = "modifier adjective/adverb" (lowered), value = (replacement, educational note)
    "very unique":        ("unique",         "Unique is already absolute — it can't be 'more' unique."),
    "completely destroyed":("destroyed",     "Destroyed is absolute — nothing is left to complete."),
    "absolutely essential":("essential",     "Essential already means indispensable."),
    "totally unique":     ("unique",         "Unique is absolute — there are no degrees."),
    "extremely obvious":  ("obvious",        "Obvious already means clearly apparent."),
    "really amazing":     ("amazing",        "Amazing is strong enough on its own."),
    "very important":     ("important",      "Important already carries weight."),
    "completely unanimous":("unanimous",     "Unanimous already means everyone agrees."),
    "totally impossible":  ("impossible",    "Impossible already means no chance."),
    "entirely possible":   ("possible",      "Possible already means it can happen."),
    "very perfect":        ("perfect",       "Perfect is absolute — it can't be improved."),
    "really incredible":   ("incredible",    "Incredible already conveys disbelief."),
    "truly remarkable":    ("remarkable",    "Remarkable already commands attention."),
    "extremely critical":  ("critical",      "Critical already implies great importance."),
    "absolutely certain":  ("certain",       "Certain already means 100%."),
    "completely empty":    ("empty",         "Empty already means nothing inside."),
    "very dead":           ("dead",          "Dead is absolute."),
    "quite frankly":       ("frankly",       "Frankly already implies directness."),
    "very angry":          ("furious",       "Replace with a stronger, precise word."),
    "very tired":          ("exhausted",     "Replace with a stronger, precise word."),
    "very sad":            ("sorrowful",     "Replace with a stronger, precise word."),
    "very happy":          ("ecstatic",      "Replace with a stronger, precise word."),
    "very scared":         ("terrified",     "Replace with a stronger, precise word."),
    "very big":            ("enormous",      "Replace with a stronger, precise word."),
    "very small":          ("tiny",          "Replace with a stronger, precise word."),
    "very fast":           ("rapid",         "Replace with a stronger, precise word."),
}

_WEAK_OPENING_PATTERNS = [
    (re.compile(r"^There\s+(?:is|are|was|were|will\s+be)\b", re.I),
     "Restructure the sentence around the true subject and action."),
    (re.compile(r"^It\s+(?:is|was|will\s+be|has\s+been)\b", re.I),
     "Replace with a concrete subject and active verb."),
    (re.compile(r"^I\s+was\b", re.I),
     "Lead with an action or observation instead."),
    (re.compile(r"^There\s+(?:seems?|appears?)\s+to\s+be\b", re.I),
     "State what exists directly instead of hedging."),
]

_FILTER_VERBS = {"see", "saw", "hear", "heard", "feel", "felt", "notice",
                  "noticed", "realize", "realized", "watch", "watched",
                  "observe", "observed", "wonder", "wondered", "know", "knew",
                  "think", "thought", "decide", "decided"}

_NOMINALIZATION_SUFFIXES = ("tion", "sion", "ment", "ness", "ance", "ence", "ity")
_NOMINALIZATION_MAP: Dict[str, str] = {
    "utilization":   "use / utilize",
    "implementation":"implement",
    "investigation": "investigate",
    "communication": "communicate",
    "determination": "determine",
    "justification": "justify",
    "examination":   "examine",
    "consideration": "consider",
    "modification":  "modify",
    "authorization": "authorize",
    "participation": "participate",
    "documentation": "document",
    "establishment": "establish",
    "development":   "develop",
    "management":    "manage",
    "improvement":   "improve",
    "achievement":   "achieve",
    "assessment":    "assess",
    "movement":      "move",
    "commitment":    "commit",
    "involvement":   "involve",
    "fulfillment":   "fulfill",
    "requirement":   "require",
    "darkness":      "dark",
    "happiness":     "happy",
    "sadness":       "sad",
    "weakness":      "weak",
    "loneliness":    "lonely",
    "awareness":     "aware",
    "carelessness":  "careless",
    "effectiveness": "effective",
}


# ════════════════════════════════════════════════
#  Severity helpers
# ════════════════════════════════════════════════

def _severity_from_count(count: int, thresholds: Tuple[int, int] = (3, 6)) -> str:
    """Map instance count to severity label."""
    if count >= thresholds[1]:
        return "critical"
    elif count >= thresholds[0]:
        return "moderate"
    return "minor"


def _make_instance(text: str, location: str, severity: str, rule: str,
                   suggestion: str, before: str, after: str) -> Dict[str, Any]:
    return {
        "text": text,
        "location": location,
        "severity": severity,
        "rule": rule,
        "suggestion": suggestion,
        "before_after_example": {"before": before, "after": after},
    }


# ════════════════════════════════════════════════
#  1. Adverb Overuse
# ════════════════════════════════════════════════

def detect_adverb_overuse(doc) -> Dict[str, Any]:
    """Flag excessive -ly adverbs, especially near dialogue tags."""
    instances: List[Dict] = []
    total_words = sum(1 for t in doc if t.is_alpha)
    ly_adverbs = [t for t in doc if t.pos_ == "ADV" and t.text.lower().endswith("ly")]
    density = round(len(ly_adverbs) / max(total_words, 1) * 100, 2)

    dialogue_tag_verbs = {"said", "asked", "replied", "whispered", "shouted",
                          "exclaimed", "muttered", "cried", "yelled", "answered",
                          "called", "stated", "remarked", "insisted", "admitted"}

    for adv in ly_adverbs:
        head = adv.head
        near_dialogue = head.lemma_.lower() in dialogue_tag_verbs
        sev = "critical" if near_dialogue else ("moderate" if density > 4 else "minor")
        sent_text = adv.sent.text.strip()
        loc = f"Sentence: \"{sent_text[:80]}{'…' if len(sent_text) > 80 else ''}\""

        if near_dialogue:
            suggestion = f"Remove '{adv.text}' — let the dialogue convey the tone."
            before = f'"{sent_text[:60]}…"'
            # Remove the adverb from the sentence for the "after" example
            after = sent_text.replace(f" {adv.text}", "").replace(f"{adv.text} ", "")
            after = f'"{after[:60]}…"'
        else:
            suggestion = f"Consider a stronger verb instead of '{adv.head.text} {adv.text}'."
            before = f"{adv.head.text} {adv.text}"
            after = f"(use a more vivid verb)"

        instances.append(_make_instance(
            text=adv.text,
            location=loc,
            severity=sev,
            rule="adverb_overuse",
            suggestion=suggestion,
            before=before,
            after=after,
        ))

    return {
        "instances": instances,
        "count": len(instances),
        "category": "adverb_overuse",
        "density_pct": density,
        "educational_tip": (
            "Stephen King wrote: 'The road to hell is paved with adverbs.' "
            "Instead of modifying a weak verb with an adverb, choose a precise, "
            "powerful verb. 'She walked quickly' → 'She hurried.' "
            "Adverbs on dialogue tags are almost always unnecessary."
        ),
    }


# ════════════════════════════════════════════════
#  2. Show Don't Tell
# ════════════════════════════════════════════════

def detect_telling_language(doc) -> Dict[str, Any]:
    """Detect copula + emotion adjective patterns ('was happy')."""
    instances: List[Dict] = []

    for token in doc:
        if (token.pos_ == "ADJ"
                and token.text.lower() in _TELLING_ADJECTIVES
                and token.head.lemma_.lower() in _COPULA_LEMMAS):
            subj = None
            for child in token.head.children:
                if child.dep_ in ("nsubj", "nsubjpass"):
                    subj = child.text
                    break
            subj = subj or "The subject"
            sent_text = token.sent.text.strip()
            loc = f"Sentence: \"{sent_text[:80]}{'…' if len(sent_text) > 80 else ''}\""

            before = f"{subj} {token.head.text} {token.text}"
            after = f"(Show {subj.lower()}'s {token.text.lower()} emotion through action or body language)"

            instances.append(_make_instance(
                text=f"{token.head.text} {token.text}",
                location=loc,
                severity="moderate",
                rule="show_dont_tell",
                suggestion=(
                    f"Instead of telling the reader '{subj} {token.head.text} {token.text}', "
                    f"show it through action, dialogue, or body language."
                ),
                before=before,
                after=after,
            ))

    return {
        "instances": instances,
        "count": len(instances),
        "category": "show_dont_tell",
        "educational_tip": (
            "Anton Chekhov: 'Don't tell me the moon is shining; show me the glint "
            "of light on broken glass.' Replace emotion labels with physical "
            "sensations, actions, and dialogue that let the reader *feel* the emotion."
        ),
    }


# ════════════════════════════════════════════════
#  3. Nominalizations
# ════════════════════════════════════════════════

def detect_nominalizations(doc) -> Dict[str, Any]:
    """Flag heavy nominalizations that should be verbs/adjectives."""
    instances: List[Dict] = []
    seen: set = set()

    for token in doc:
        if token.pos_ != "NOUN":
            continue
        low = token.text.lower()
        if low in seen or len(low) < 6:
            continue
        if not low.endswith(_NOMINALIZATION_SUFFIXES):
            continue
        # Skip proper nouns and known non-nominalizations
        if token.ent_type_:
            continue

        verb_form = _NOMINALIZATION_MAP.get(low, None)
        if verb_form is None:
            # Auto-generate hint for unmapped words
            if low.endswith("tion") or low.endswith("sion"):
                base = low[:-4]
                verb_form = f"{base}e" if not base.endswith("e") else base
            elif low.endswith("ment"):
                verb_form = low[:-4]
            elif low.endswith("ness"):
                verb_form = low[:-4]
            elif low.endswith("ance") or low.endswith("ence"):
                verb_form = low[:-4]
            elif low.endswith("ity"):
                verb_form = low[:-3] + "e"
            else:
                continue
            # Only flag if the auto-generated form is >= 3 chars
            if len(verb_form) < 3:
                continue

        seen.add(low)
        sent_text = token.sent.text.strip()
        loc = f"Sentence: \"{sent_text[:80]}{'…' if len(sent_text) > 80 else ''}\""

        instances.append(_make_instance(
            text=token.text,
            location=loc,
            severity="minor",
            rule="nominalization",
            suggestion=f"Replace '{token.text}' with the verb/adjective form: '{verb_form}'.",
            before=f"The {low} of the process …",
            after=f"(verb form) {verb_form} the process …",
        ))

    return {
        "instances": instances,
        "count": len(instances),
        "category": "nominalizations",
        "educational_tip": (
            "Nominalizations turn vivid verbs into abstract nouns, making prose "
            "heavy and bureaucratic. 'We performed an investigation' → 'We investigated.' "
            "Prefer the verb form for directness and energy."
        ),
    }


# ════════════════════════════════════════════════
#  4. Hedge Words
# ════════════════════════════════════════════════

def detect_hedge_words(doc) -> Dict[str, Any]:
    """Detect hedging language that weakens assertions."""
    instances: List[Dict] = []
    text_lower = doc.text.lower()

    # Single-token hedges
    for token in doc:
        low = token.text.lower()
        if low in _HEDGE_WORDS and low not in ("sort", "kind", "a", "i", "it", "to", "be"):
            # skip multi-word fragments — handled below
            if low in ("sort", "kind", "little", "bit", "think", "believe", "feel", "seems", "honest"):
                continue
            sent_text = token.sent.text.strip()
            loc = f"Sentence: \"{sent_text[:80]}{'…' if len(sent_text) > 80 else ''}\""
            suggestion = _HEDGE_WORDS[low]
            instances.append(_make_instance(
                text=token.text,
                location=loc,
                severity="minor",
                rule="hedge_word",
                suggestion=suggestion,
                before=f"…{sent_text[:50]}…",
                after=f"(remove '{token.text}' or replace with a precise claim)",
            ))

    # Multi-word hedges
    for pat, hedge_key in _HEDGE_MULTIWORD_PATTERNS:
        for m in pat.finditer(doc.text):
            matched = m.group()
            # find which sentence
            start = m.start()
            sent_text = ""
            for sent in doc.sents:
                if sent.start_char <= start < sent.end_char:
                    sent_text = sent.text.strip()
                    break
            loc = f"Sentence: \"{sent_text[:80]}{'…' if len(sent_text) > 80 else ''}\""
            suggestion = _HEDGE_WORDS.get(hedge_key.lower(), "Remove or replace with a definitive statement.")
            instances.append(_make_instance(
                text=matched,
                location=loc,
                severity="minor",
                rule="hedge_word",
                suggestion=suggestion,
                before=f"…{sent_text[:50]}…",
                after=f"(remove '{matched}' or be more specific)",
            ))

    return {
        "instances": instances,
        "count": len(instances),
        "category": "hedge_words",
        "educational_tip": (
            "Hedge words ('somewhat', 'perhaps', 'sort of') signal uncertainty and "
            "weaken your argument. In most cases, delete them entirely — your "
            "prose will become more confident and direct."
        ),
    }


# ════════════════════════════════════════════════
#  5. Redundant Modifiers
# ════════════════════════════════════════════════

def detect_redundant_modifiers(doc, text: str) -> Dict[str, Any]:
    """Detect redundant modifier + adjective pairs ('very unique')."""
    instances: List[Dict] = []
    text_lower = text.lower()

    for phrase, (replacement, note) in _REDUNDANT_MODIFIERS.items():
        pattern = re.compile(r"\b" + re.escape(phrase) + r"\b", re.I)
        for m in pattern.finditer(text):
            matched = m.group()
            start = m.start()
            sent_text = ""
            for sent in doc.sents:
                if sent.start_char <= start < sent.end_char:
                    sent_text = sent.text.strip()
                    break
            loc = f"Sentence: \"{sent_text[:80]}{'…' if len(sent_text) > 80 else ''}\""

            instances.append(_make_instance(
                text=matched,
                location=loc,
                severity="moderate",
                rule="redundant_modifier",
                suggestion=f"{note} Replace '{matched}' → '{replacement}'.",
                before=matched,
                after=replacement,
            ))

    return {
        "instances": instances,
        "count": len(instances),
        "category": "redundant_modifiers",
        "educational_tip": (
            "Redundant modifiers pair an intensifier with an already-absolute word. "
            "'Very unique' is like saying 'very one-of-a-kind.' "
            "Either the word is strong enough on its own, or pick a more precise word."
        ),
    }


# ════════════════════════════════════════════════
#  6. Weak Openings
# ════════════════════════════════════════════════

def detect_weak_openings(text: str) -> Dict[str, Any]:
    """Detect sentences beginning with 'There is/are', 'It was', etc."""
    instances: List[Dict] = []
    # Split into sentences (simple approach — period/excl/question followed by space+uppercase)
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        for pat, suggestion in _WEAK_OPENING_PATTERNS:
            if pat.match(sent):
                loc = f"Sentence: \"{sent[:80]}{'…' if len(sent) > 80 else ''}\""
                instances.append(_make_instance(
                    text=pat.match(sent).group(),
                    location=loc,
                    severity="moderate",
                    rule="weak_opening",
                    suggestion=suggestion,
                    before=sent[:60] + ("…" if len(sent) > 60 else ""),
                    after="(Restructure: lead with the true subject and action.)",
                ))
                break  # only one match per sentence

    return {
        "instances": instances,
        "count": len(instances),
        "category": "weak_openings",
        "educational_tip": (
            "'There is/are' and 'It was' openings are expletive constructions — "
            "they delay the real subject. 'There are five cats on the roof' → "
            "'Five cats sit on the roof.' The second version is tighter and more vivid."
        ),
    }


# ════════════════════════════════════════════════
#  7. Filter Words
# ════════════════════════════════════════════════

def detect_filter_words(doc) -> Dict[str, Any]:
    """Detect filtering verbs that distance the reader ('I saw that…')."""
    instances: List[Dict] = []

    for token in doc:
        if token.lemma_.lower() not in _FILTER_VERBS:
            continue
        # Must have a first-person subject
        has_first_person = False
        for child in token.children:
            if child.dep_ in ("nsubj", "nsubjpass") and child.text.lower() in ("i", "we"):
                has_first_person = True
                break
        if not has_first_person:
            continue
        # Check for a clausal complement ("I saw that…", "I realized…")
        has_complement = any(child.dep_ in ("ccomp", "xcomp", "advcl", "that", "mark")
                             for child in token.subtree)
        if not has_complement and token.lemma_.lower() not in ("wonder", "decide"):
            continue

        sent_text = token.sent.text.strip()
        loc = f"Sentence: \"{sent_text[:80]}{'…' if len(sent_text) > 80 else ''}\""

        instances.append(_make_instance(
            text=f"I {token.text}",
            location=loc,
            severity="minor",
            rule="filter_word",
            suggestion=(
                f"Remove the filter verb '{token.text}' and show the "
                f"observation directly. Let the reader experience it."
            ),
            before=f"I {token.text} that the room was dark.",
            after="The room was dark.",
        ))

    return {
        "instances": instances,
        "count": len(instances),
        "category": "filter_words",
        "educational_tip": (
            "Filter words ('I saw', 'I heard', 'I felt') put a middleman between "
            "the reader and the experience. Remove them to create immediacy. "
            "'I noticed the door was open' → 'The door was open.'"
        ),
    }


# ════════════════════════════════════════════════
#  8. Info Dumps
# ════════════════════════════════════════════════

def detect_info_dumps(text: str, doc) -> Dict[str, Any]:
    """Detect paragraphs with heavy exposition (high adj density, no dialogue)."""
    instances: List[Dict] = []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs or len(paragraphs) < 1:
        # Also try single newline split if no double newlines
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    for i, para in enumerate(paragraphs):
        if len(para.split()) < 30:
            # Skip short paragraphs
            continue

        words = para.split()
        word_count = len(words)

        # Check for dialogue
        has_dialogue = '"' in para or "'" in para or '"' in para or '"' in para

        # Count descriptive tokens via simple heuristics
        adj_count = 0
        verb_count = 0
        for sent in doc.sents:
            if sent.text.strip() in para or para[:40] in sent.text:
                for tok in sent:
                    if tok.pos_ == "ADJ":
                        adj_count += 1
                    if tok.pos_ == "VERB" and tok.dep_ not in ("aux", "auxpass"):
                        verb_count += 1

        adj_density = adj_count / max(word_count, 1) * 100
        action_ratio = verb_count / max(word_count, 1) * 100

        # Flag if: high adjective density, low action verbs, no dialogue
        if adj_density > 8 and action_ratio < 4 and not has_dialogue and word_count > 40:
            loc = f"Paragraph {i + 1}"
            instances.append(_make_instance(
                text=para[:80] + ("…" if len(para) > 80 else ""),
                location=loc,
                severity="moderate",
                rule="info_dump",
                suggestion=(
                    "This paragraph is exposition-heavy. Break it up with action, "
                    "dialogue, or shorter paragraphs to maintain reader engagement."
                ),
                before=f"[{word_count} words, {adj_count} adjectives, {verb_count} action verbs, no dialogue]",
                after="(Weave exposition into action scenes; use dialogue to reveal information.)",
            ))

    return {
        "instances": instances,
        "count": len(instances),
        "category": "info_dumps",
        "educational_tip": (
            "Info dumps overload the reader with background, description, or "
            "explanation in one heavy block. Instead, sprinkle information through "
            "dialogue, action, and internalization across multiple scenes."
        ),
    }


# ════════════════════════════════════════════════
#  Master function
# ════════════════════════════════════════════════

def detect_all_antipatterns(doc, text: str) -> Dict[str, Any]:
    """
    Run all anti-pattern detectors and return a unified result.

    Returns
    -------
    dict with keys:
        categories : dict[str, category_result]
        summary    : {total, critical, moderate, minor}
    """
    categories = {
        "adverb_overuse":      detect_adverb_overuse(doc),
        "show_dont_tell":      detect_telling_language(doc),
        "nominalizations":     detect_nominalizations(doc),
        "hedge_words":         detect_hedge_words(doc),
        "redundant_modifiers": detect_redundant_modifiers(doc, text),
        "weak_openings":       detect_weak_openings(text),
        "filter_words":        detect_filter_words(doc),
        "info_dumps":          detect_info_dumps(text, doc),
    }

    # Tally severities
    total = 0
    crit = 0
    mod = 0
    minor = 0
    for cat_data in categories.values():
        for inst in cat_data.get("instances", []):
            total += 1
            s = inst.get("severity", "minor")
            if s == "critical":
                crit += 1
            elif s == "moderate":
                mod += 1
            else:
                minor += 1

    return {
        "categories": categories,
        "summary": {
            "total": total,
            "critical": crit,
            "moderate": mod,
            "minor": minor,
        },
    }
