"""
Grammar Checker Module
Detects common grammar issues using spaCy's dependency parsing and morphological analysis.

Functions:
- check_grammar: Master orchestrator
- detect_subject_verb_agreement: Subject-verb number mismatches
- detect_sentence_fragments: Sentences missing a main verb
- detect_run_on_sentences: Comma splices and fused sentences
- detect_dangling_modifiers: Opening clause subject mismatch
- detect_article_errors: Incorrect a/an usage
- detect_double_negatives: "don't have no" patterns
- detect_punctuation_issues: Spacing and punctuation problems
"""

import re
from typing import Dict, List, Any, Optional


# ──────────────────────────────────────────────
# Master orchestrator
# ──────────────────────────────────────────────


def check_grammar(doc, text: str) -> Dict[str, Any]:
    """
    Run all grammar checks and return a unified report.

    Args:
        doc: spaCy Doc object
        text: Original raw text

    Returns:
        Dict with per-rule results and aggregate stats
    """
    results = {
        "subject_verb_agreement": detect_subject_verb_agreement(doc),
        "sentence_fragments": detect_sentence_fragments(doc),
        "run_on_sentences": detect_run_on_sentences(doc, text),
        "dangling_modifiers": detect_dangling_modifiers(doc),
        "article_errors": detect_article_errors(doc),
        "double_negatives": detect_double_negatives(doc),
        "punctuation_issues": detect_punctuation_issues(text),
    }

    # Flatten all issues into a single list for quick access
    all_issues: List[Dict[str, Any]] = []
    for issues in results.values():
        all_issues.extend(issues)

    # Sort by position in text
    all_issues.sort(key=lambda x: x.get("start_offset", 0))

    results["all_issues"] = all_issues
    results["total_issues"] = len(all_issues)

    # Severity summary
    severity_counts: Dict[str, int] = {"error": 0, "warning": 0, "info": 0}
    for issue in all_issues:
        sev = issue.get("severity", "info")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    results["severity_summary"] = severity_counts

    # Grammar score (100 = perfect, subtract per-issue penalty)
    penalty = severity_counts["error"] * 8 + severity_counts["warning"] * 4 + severity_counts["info"] * 1
    results["grammar_score"] = max(0, 100 - penalty)

    return results


# ──────────────────────────────────────────────
# 1. Subject–Verb Agreement
# ──────────────────────────────────────────────


def detect_subject_verb_agreement(doc) -> List[Dict[str, Any]]:
    """
    Detect subject-verb agreement errors using morphological features.

    Checks: singular subject + plural verb form and vice-versa.
    Example: "The dogs runs fast" → error
    """
    issues: List[Dict[str, Any]] = []

    for sent in doc.sents:
        subjects = [tok for tok in sent if tok.dep_ in ("nsubj", "nsubjpass")]
        for subj in subjects:
            verb = subj.head

            # Only check present-tense verbs (VBZ / VBP)
            if verb.pos_ != "VERB" and verb.pos_ != "AUX":
                continue
            if verb.tag_ not in ("VBZ", "VBP", "VB"):
                continue

            subj_number = subj.morph.get("Number")
            verb_tag = verb.tag_

            # Skip pronouns like "I" / "you" (special conjugation rules)
            if subj.lower_ in ("i", "you", "we", "they", "who"):
                continue

            # Singular subject expects VBZ; plural expects VBP
            if subj_number == ["Sing"] and verb_tag == "VBP" and subj.lower_ not in ("i", "you"):
                issues.append(_make_issue(
                    sent,
                    f"Singular subject '{subj.text}' may not agree with verb '{verb.text}'",
                    f"Consider using '{_suggest_singular_verb(verb.text)}' instead of '{verb.text}'",
                    "error",
                    verb.idx,
                    verb.idx + len(verb.text),
                    "subject_verb_agreement",
                ))
            elif subj_number == ["Plur"] and verb_tag == "VBZ":
                issues.append(_make_issue(
                    sent,
                    f"Plural subject '{subj.text}' may not agree with verb '{verb.text}'",
                    f"Consider using the base form instead of '{verb.text}'",
                    "error",
                    verb.idx,
                    verb.idx + len(verb.text),
                    "subject_verb_agreement",
                ))

    return issues


def _suggest_singular_verb(verb_text: str) -> str:
    """Naive heuristic to suggest a singular verb form."""
    v = verb_text.lower()
    if v == "are":
        return "is"
    if v == "have":
        return "has"
    if v == "do":
        return "does"
    if v.endswith("s"):
        return v
    return v + "s"


# ──────────────────────────────────────────────
# 2. Sentence Fragments
# ──────────────────────────────────────────────


def detect_sentence_fragments(doc) -> List[Dict[str, Any]]:
    """
    Detect sentence fragments — clauses lacking a main (ROOT) verb.

    Skips very short sentences (≤3 tokens) which are often intentional.
    """
    issues: List[Dict[str, Any]] = []

    for sent in doc.sents:
        tokens = list(sent)
        # Skip very short or single-word sentences (titles, exclamations)
        if len(tokens) <= 3:
            continue

        has_root_verb = any(
            tok.dep_ == "ROOT" and tok.pos_ in ("VERB", "AUX")
            for tok in tokens
        )

        if not has_root_verb:
            issues.append(_make_issue(
                sent,
                "This may be a sentence fragment (no main verb detected)",
                "Add a verb or merge with an adjacent sentence",
                "warning",
                sent.start_char,
                sent.end_char,
                "sentence_fragment",
            ))

    return issues


# ──────────────────────────────────────────────
# 3. Run-on Sentences & Comma Splices
# ──────────────────────────────────────────────


def detect_run_on_sentences(doc, text: str) -> List[Dict[str, Any]]:
    """
    Detect run-on sentences and comma splices.

    A comma splice joins two independent clauses with only a comma.
    A run-on fuses them with no punctuation at all.
    """
    issues: List[Dict[str, Any]] = []

    for sent in doc.sents:
        tokens = list(sent)
        # Look for comma-separated independent clauses
        for i, tok in enumerate(tokens):
            if tok.text == "," and 2 < i < len(tokens) - 3:
                # Check if token after comma starts a new independent clause
                next_tok = tokens[i + 1] if i + 1 < len(tokens) else None
                if next_tok is None:
                    continue

                # Heuristic: pronoun or proper noun right after comma followed by a verb
                if next_tok.pos_ in ("PRON", "PROPN", "NOUN"):
                    # Look ahead for a verb within 3 tokens
                    upcoming = tokens[i + 1 : min(i + 5, len(tokens))]
                    has_verb = any(t.pos_ in ("VERB", "AUX") and t.dep_ != "aux" for t in upcoming)

                    # Also check: previous part had a verb (ROOT)
                    prev_has_root = any(
                        t.dep_ == "ROOT" and t.pos_ in ("VERB", "AUX")
                        for t in tokens[:i]
                    )

                    if has_verb and prev_has_root:
                        issues.append(_make_issue(
                            sent,
                            "Possible comma splice — two independent clauses joined by a comma",
                            "Use a semicolon, add a conjunction (and/but/so), or split into two sentences",
                            "warning",
                            tok.idx,
                            tok.idx + 1,
                            "comma_splice",
                        ))

        # Very long sentences may be run-ons
        word_count = sum(1 for t in tokens if not t.is_punct and not t.is_space)
        if word_count > 50:
            conj_count = sum(1 for t in tokens if t.dep_ == "cc")
            if conj_count >= 3:
                issues.append(_make_issue(
                    sent,
                    f"Possible run-on sentence ({word_count} words, {conj_count} conjunctions)",
                    "Break into shorter sentences for clarity",
                    "warning",
                    sent.start_char,
                    sent.end_char,
                    "run_on_sentence",
                ))

    return issues


# ──────────────────────────────────────────────
# 4. Dangling Modifiers
# ──────────────────────────────────────────────


def detect_dangling_modifiers(doc) -> List[Dict[str, Any]]:
    """
    Detect dangling modifiers — introductory participial phrases
    whose implied subject doesn't match the sentence's actual subject.

    Example: "Running to the store, the rain started." → dangling modifier
    """
    issues: List[Dict[str, Any]] = []

    for sent in doc.sents:
        tokens = list(sent)
        if len(tokens) < 5:
            continue

        # Check if sentence starts with a participial phrase (VBG)
        first_tok = tokens[0]
        if first_tok.tag_ not in ("VBG", "VBN"):
            continue

        # Find the comma that ends the introductory phrase
        comma_idx = None
        for i, tok in enumerate(tokens):
            if tok.text == ",":
                comma_idx = i
                break

        if comma_idx is None or comma_idx < 2:
            continue

        # Find the main subject after the comma
        main_subject = None
        for tok in tokens[comma_idx + 1 :]:
            if tok.dep_ in ("nsubj", "nsubjpass"):
                main_subject = tok
                break

        if main_subject is None:
            continue

        # If subject is inanimate / abstract and intro is an action, likely dangling
        if main_subject.ent_type_ in ("DATE", "TIME", "MONEY", "CARDINAL", "ORG"):
            issues.append(_make_issue(
                sent,
                f"Possible dangling modifier — '{first_tok.text}...' does not clearly modify '{main_subject.text}'",
                f"Rewrite so the subject performing '{first_tok.text}' appears right after the comma",
                "warning",
                sent.start_char,
                sent.end_char,
                "dangling_modifier",
            ))
        elif main_subject.pos_ == "NOUN" and first_tok.tag_ == "VBG":
            # Extra heuristic: non-person nouns used with human-action gerunds
            if main_subject.ent_type_ not in ("PERSON", ""):
                issues.append(_make_issue(
                    sent,
                    f"Possible dangling modifier — '{first_tok.text}...' may not logically modify '{main_subject.text}'",
                    "Rewrite for clarity, placing the true actor right after the introductory phrase",
                    "info",
                    sent.start_char,
                    sent.end_char,
                    "dangling_modifier",
                ))

    return issues


# ──────────────────────────────────────────────
# 5. Article Errors (a/an)
# ──────────────────────────────────────────────

_VOWEL_SOUNDS = set("aeiouAEIOU")
_AN_BEFORE = {"hour", "honest", "honor", "honour", "heir", "herb"}
_A_BEFORE = {"university", "uniform", "unique", "union", "united", "universal",
             "unicorn", "unit", "usage", "useful", "usual", "utility",
             "european", "one", "once", "one-time"}


def detect_article_errors(doc) -> List[Dict[str, Any]]:
    """
    Detect incorrect usage of 'a' vs 'an' before words.

    Rules:
    - 'a' before consonant sounds: a book, a university
    - 'an' before vowel sounds: an apple, an hour
    """
    issues: List[Dict[str, Any]] = []

    tokens = list(doc)
    for i, tok in enumerate(tokens):
        if tok.lower_ not in ("a", "an"):
            continue
        if tok.pos_ != "DET":
            continue

        # Find the next meaningful word (skip adverbs/adjectives)
        next_word = None
        for j in range(i + 1, min(i + 4, len(tokens))):
            if tokens[j].pos_ not in ("SPACE", "PUNCT"):
                next_word = tokens[j]
                break

        if next_word is None:
            continue

        word_lower = next_word.lower_
        starts_vowel_sound = _starts_with_vowel_sound(word_lower)

        if tok.lower_ == "a" and starts_vowel_sound:
            issues.append(_make_issue(
                _sent_for_token(doc, tok),
                f"Use 'an' instead of 'a' before '{next_word.text}'",
                f"Change 'a {next_word.text}' to 'an {next_word.text}'",
                "error",
                tok.idx,
                tok.idx + len(tok.text),
                "article_error",
            ))
        elif tok.lower_ == "an" and not starts_vowel_sound:
            issues.append(_make_issue(
                _sent_for_token(doc, tok),
                f"Use 'a' instead of 'an' before '{next_word.text}'",
                f"Change 'an {next_word.text}' to 'a {next_word.text}'",
                "error",
                tok.idx,
                tok.idx + len(tok.text),
                "article_error",
            ))

    return issues


def _starts_with_vowel_sound(word: str) -> bool:
    """Determine if a word starts with a vowel sound (not just vowel letter)."""
    if not word:
        return False
    if word in _AN_BEFORE:
        return True
    if word in _A_BEFORE:
        return False
    return word[0] in _VOWEL_SOUNDS


# ──────────────────────────────────────────────
# 6. Double Negatives
# ──────────────────────────────────────────────

_NEGATIVE_WORDS = {
    "no", "not", "never", "neither", "nobody", "nothing",
    "nowhere", "nor", "none", "n't", "cannot",
}


def detect_double_negatives(doc) -> List[Dict[str, Any]]:
    """
    Detect double negatives in sentences.

    Example: "I don't have no money" → double negative
    """
    issues: List[Dict[str, Any]] = []

    for sent in doc.sents:
        neg_tokens = []
        for tok in sent:
            # Catch "n't" contractions as well
            if tok.lower_ in _NEGATIVE_WORDS or tok.dep_ == "neg":
                neg_tokens.append(tok)

        if len(neg_tokens) >= 2:
            neg_text = " ... ".join(t.text for t in neg_tokens)
            issues.append(_make_issue(
                sent,
                f"Possible double negative: '{neg_text}'",
                "Remove one of the negatives for clearer meaning",
                "warning",
                neg_tokens[0].idx,
                neg_tokens[-1].idx + len(neg_tokens[-1].text),
                "double_negative",
            ))

    return issues


# ──────────────────────────────────────────────
# 7. Punctuation Issues
# ──────────────────────────────────────────────


def detect_punctuation_issues(text: str) -> List[Dict[str, Any]]:
    """
    Detect common punctuation and spacing problems using regex.

    Checks:
    - Multiple consecutive spaces
    - Missing space after punctuation (.,;:!?)
    - Multiple consecutive punctuation marks (!! or ??)
    - Space before punctuation
    """
    issues: List[Dict[str, Any]] = []

    # Multiple spaces
    for m in re.finditer(r"  +", text):
        issues.append({
            "sentence": _context_around(text, m.start(), 40),
            "issue": "Multiple consecutive spaces",
            "suggestion": "Use a single space",
            "severity": "info",
            "start_offset": m.start(),
            "end_offset": m.end(),
            "rule": "extra_spaces",
        })

    # Missing space after sentence-ending punctuation
    for m in re.finditer(r"(?<=[.!?;:,])(?=[A-Za-z])", text):
        # Exclude common abbreviations like "e.g." "i.e." "Mr." "Dr."
        before = text[max(0, m.start() - 3) : m.start()]
        if re.search(r"\b[A-Za-z]$", before):  # single letter before period = abbreviation
            continue
        issues.append({
            "sentence": _context_around(text, m.start(), 40),
            "issue": "Missing space after punctuation",
            "suggestion": "Add a space after the punctuation mark",
            "severity": "info",
            "start_offset": m.start(),
            "end_offset": m.start() + 1,
            "rule": "missing_space_after_punct",
        })

    # Repeated punctuation (!! ?? ..)
    for m in re.finditer(r"([!?.])\1{1,}", text):
        issues.append({
            "sentence": _context_around(text, m.start(), 40),
            "issue": f"Repeated punctuation: '{m.group()}'",
            "suggestion": "Use a single punctuation mark for formal writing",
            "severity": "info",
            "start_offset": m.start(),
            "end_offset": m.end(),
            "rule": "repeated_punctuation",
        })

    # Space before punctuation
    for m in re.finditer(r" +(?=[.!?,;:])", text):
        issues.append({
            "sentence": _context_around(text, m.start(), 40),
            "issue": "Unnecessary space before punctuation",
            "suggestion": "Remove the space before the punctuation mark",
            "severity": "info",
            "start_offset": m.start(),
            "end_offset": m.end(),
            "rule": "space_before_punct",
        })

    return issues


# ──────────────────────────────────────────────
# Helper utilities
# ──────────────────────────────────────────────


def _make_issue(
    sent,
    issue: str,
    suggestion: str,
    severity: str,
    start_offset: int,
    end_offset: int,
    rule: str,
) -> Dict[str, Any]:
    """Build a standardized issue dict."""
    return {
        "sentence": sent.text.strip(),
        "issue": issue,
        "suggestion": suggestion,
        "severity": severity,
        "start_offset": start_offset,
        "end_offset": end_offset,
        "rule": rule,
    }


def _sent_for_token(doc, token):
    """Return the sentence span containing a given token."""
    for sent in doc.sents:
        if sent.start <= token.i < sent.end:
            return sent
    # Fallback to whole doc
    return doc[:]


def _context_around(text: str, pos: int, window: int = 40) -> str:
    """Return a context snippet around a position."""
    start = max(0, pos - window)
    end = min(len(text), pos + window)
    snippet = text[start:end].replace("\n", " ")
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{snippet}{suffix}"
