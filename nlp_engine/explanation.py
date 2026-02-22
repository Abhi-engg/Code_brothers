"""
WriteCraft — Explanation Generator Module
Generate human-readable, writer-friendly explanations for all analysis results.
Covers: text analysis, readability, flow, style, consistency, issues,
        grammar, tone, anti-patterns, passive voice, filler words,
        clichés, vocabulary complexity, and actionable suggestions.
"""

from typing import Dict, List, Any, Optional


def generate_explanations(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate comprehensive explanations for all analysis components.

    Args:
        analysis_results: Complete analysis results from the pipeline

    Returns:
        Dictionary containing explanations for each component
    """
    explanations = {
        "summary": generate_summary(analysis_results),
        "text_analysis": explain_text_analysis(analysis_results.get("text_analysis", {})),
        "readability": explain_readability(analysis_results.get("readability", {})),
        "flow": explain_flow(analysis_results.get("flow", {})),
        "style": explain_style(analysis_results.get("style_analysis", {})),
        "consistency": explain_consistency(analysis_results.get("consistency", {})),
        "issues": explain_issues(analysis_results.get("issues", {})),
        "suggestions": generate_actionable_suggestions(analysis_results),
        "grammar": explain_grammar(analysis_results.get("grammar_analysis", {})),
        "tone": explain_tone(analysis_results.get("tone_analysis", {})),
        "antipatterns": explain_antipatterns(analysis_results.get("antipatterns", {})),
        "passive_voice": explain_passive_voice(analysis_results.get("passive_voice", {})),
        "filler_words": explain_filler_words(analysis_results.get("filler_words", {})),
        "cliches": explain_cliches(analysis_results.get("cliches", {})),
        "vocabulary": explain_vocabulary(analysis_results.get("vocabulary_complexity", {})),
    }

    return explanations


def generate_summary(results: Dict[str, Any]) -> str:
    """Generate an executive summary of the analysis."""
    parts = []
    
    # Word count and structure
    text_analysis = results.get("text_analysis", {})
    if text_analysis:
        sentence_count = len(text_analysis.get("sentences", []))
        token_count = len(text_analysis.get("tokens", []))
        entity_count = len(text_analysis.get("entities", []))
        
        parts.append(
            f"Your text contains {sentence_count} sentences with {token_count} words "
            f"and {entity_count} named entities."
        )
    
    # Readability
    readability = results.get("readability", {})
    if readability:
        grade = readability.get("grade_level", "N/A")
        difficulty = readability.get("difficulty", "unknown")
        parts.append(
            f"The text is at grade level {grade} ({difficulty} difficulty)."
        )
    
    # Issues count
    issues = results.get("issues", {})
    total_issues = sum(len(v) if isinstance(v, list) else 0 for v in issues.values())
    if total_issues > 0:
        parts.append(f"We found {total_issues} potential areas for improvement.")
    else:
        parts.append("No major issues were detected.")
    
    return " ".join(parts)


def explain_text_analysis(text_analysis: Dict[str, Any]) -> Dict[str, str]:
    """Generate explanations for basic text analysis."""
    explanations = {}
    
    # Sentences
    sentences = text_analysis.get("sentences", [])
    explanations["sentences"] = (
        f"Your text has been divided into {len(sentences)} sentences. "
        "Sentence boundaries are detected using punctuation and grammatical patterns."
    )
    
    # Tokens
    tokens = text_analysis.get("tokens", [])
    explanations["tokens"] = (
        f"The text contains {len(tokens)} tokens (words and punctuation). "
        "Tokenization breaks down the text into its smallest meaningful units."
    )
    
    # Entities
    entities = text_analysis.get("entities", [])
    if entities:
        entity_types = {}
        for ent_text, ent_label in entities:
            if ent_label not in entity_types:
                entity_types[ent_label] = []
            entity_types[ent_label].append(ent_text)
        
        entity_breakdown = ", ".join(
            f"{len(v)} {k}" for k, v in entity_types.items()
        )
        explanations["entities"] = (
            f"Found {len(entities)} named entities: {entity_breakdown}. "
            "Named entities include people, organizations, locations, dates, and other proper nouns."
        )
    else:
        explanations["entities"] = "No named entities were detected in the text."
    
    # POS Tags
    pos_tags = text_analysis.get("pos_tags", [])
    if pos_tags:
        pos_counts = {}
        for tag_info in pos_tags:
            pos = tag_info.get("pos", "UNKNOWN")
            pos_counts[pos] = pos_counts.get(pos, 0) + 1
        
        top_pos = sorted(pos_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        pos_summary = ", ".join(f"{count} {pos}" for pos, count in top_pos)
        explanations["pos_tags"] = (
            f"Part-of-speech analysis found: {pos_summary}. "
            "POS tagging identifies the grammatical role of each word."
        )
    
    return explanations


def explain_readability(readability: Dict[str, Any]) -> Dict[str, str]:
    """Generate explanations for readability analysis."""
    explanations = {}
    
    scores = readability.get("scores", {})
    stats = readability.get("statistics", {})
    
    # Flesch Reading Ease
    fre = scores.get("flesch_reading_ease", 0)
    explanations["flesch_reading_ease"] = (
        f"Flesch Reading Ease score: {fre}. "
        f"{get_flesch_explanation(fre)} "
        "This score ranges from 0-100, with higher scores indicating easier readability."
    )
    
    # Grade Level
    grade = readability.get("grade_level", 0)
    explanations["grade_level"] = (
        f"Estimated reading grade level: {grade}. "
        f"This means the text is appropriate for someone with {get_grade_description(grade)}. "
        "This is calculated by averaging multiple readability formulas."
    )
    
    # Statistics
    avg_words = stats.get("avg_words_per_sentence", 0)
    avg_syllables = stats.get("avg_syllables_per_word", 0)
    
    explanations["statistics"] = (
        f"Average words per sentence: {avg_words}. "
        f"Average syllables per word: {avg_syllables}. "
        f"{'Sentences are longer than typical. Consider breaking them up.' if avg_words > 20 else 'Sentence length is reasonable.'} "
        f"{'Word complexity is high. Consider simpler alternatives.' if avg_syllables > 1.7 else 'Word complexity is appropriate.'}"
    )
    
    # Reading time
    reading_time = readability.get("reading_time_minutes", 0)
    explanations["reading_time"] = (
        f"Estimated reading time: {reading_time} minutes "
        "(based on average reading speed of 200 words per minute)."
    )
    
    return explanations


def get_flesch_explanation(score: float) -> str:
    """Get detailed Flesch score explanation."""
    if score >= 90:
        return "Very easy to read - suitable for 5th graders."
    elif score >= 80:
        return "Easy to read - conversational English."
    elif score >= 70:
        return "Fairly easy to read - suitable for 7th graders."
    elif score >= 60:
        return "Standard difficulty - plain English."
    elif score >= 50:
        return "Fairly difficult - high school level."
    elif score >= 30:
        return "Difficult - college level reading."
    else:
        return "Very difficult - professional/academic level."


def get_grade_description(grade: float) -> str:
    """Get description of grade level."""
    if grade <= 6:
        return "elementary school education"
    elif grade <= 8:
        return "middle school education"
    elif grade <= 12:
        return "high school education"
    elif grade <= 16:
        return "undergraduate college education"
    else:
        return "graduate-level education"


def explain_flow(flow: Dict[str, Any]) -> Dict[str, str]:
    """Generate explanations for flow analysis."""
    explanations = {}
    
    flow_score = flow.get("flow_score", 0)
    explanations["flow_score"] = (
        f"Flow score: {flow_score}/100. "
        f"{'Excellent flow with good use of transitions.' if flow_score >= 70 else ''}"
        f"{'Good flow, but could benefit from more connective phrases.' if 50 <= flow_score < 70 else ''}"
        f"{'Text may feel choppy. Consider adding transition words.' if flow_score < 50 else ''}"
    )
    
    # Transitions
    transitions = flow.get("transitions_found", [])
    if transitions:
        explanations["transitions"] = (
            f"Found {len(transitions)} transition words/phrases: {', '.join(transitions[:5])}{'...' if len(transitions) > 5 else ''}. "
            "Transitions help connect ideas and improve readability."
        )
    else:
        explanations["transitions"] = (
            "No transition words detected. Consider adding words like 'however', 'therefore', "
            "'additionally', or 'for example' to improve flow."
        )
    
    # Sentence variety
    variety = flow.get("sentence_variety", {})
    variety_ratio = variety.get("variety_ratio", 0)
    explanations["sentence_variety"] = (
        f"Sentence starter variety: {variety_ratio * 100:.0f}%. "
        f"{'Good variety in how sentences begin.' if variety_ratio >= 0.7 else ''}"
        f"{'Moderate variety - consider varying sentence beginnings more.' if 0.5 <= variety_ratio < 0.7 else ''}"
        f"{'Low variety - many sentences start the same way.' if variety_ratio < 0.5 else ''}"
    )
    
    return explanations


def explain_style(style_analysis: Dict[str, Any]) -> Dict[str, str]:
    """Generate explanations for style analysis."""
    explanations = {}
    
    dominant_style = style_analysis.get("dominant_style", "unknown")
    explanations["current_style"] = (
        f"Detected writing style: {dominant_style.capitalize()}. "
        f"{style_analysis.get('recommendation', '')}"
    )
    
    indicators = style_analysis.get("indicators", {})
    if indicators:
        contractions = indicators.get("contractions", 0)
        informal_words = indicators.get("informal_words", 0)
        formal_words = indicators.get("formal_words", 0)
        
        explanations["style_indicators"] = (
            f"Style indicators found: {contractions} contractions, "
            f"{informal_words} informal words, {formal_words} formal words. "
            f"{'High use of contractions suggests casual tone.' if contractions > 5 else ''}"
            f"{'Few contractions and formal vocabulary indicate professional style.' if contractions <= 2 and formal_words > informal_words else ''}"
        )
    
    return explanations


def explain_consistency(consistency: Dict[str, Any]) -> Dict[str, str]:
    """Generate explanations for consistency analysis."""
    explanations = {}
    
    score = consistency.get("overall_consistency_score", 100)
    explanations["consistency_score"] = (
        f"Narrative consistency score: {score}/100. "
        f"{consistency.get('assessment', '')}"
    )
    
    # Entity analysis
    entity_analysis = consistency.get("entity_analysis", {})
    unique_entities = entity_analysis.get("unique_entities", {})
    if unique_entities:
        entity_summary = ", ".join(
            f"{len(v)} {k.lower()}s" for k, v in unique_entities.items() if v
        )
        explanations["entities"] = (
            f"Unique entities tracked: {entity_summary}. "
            "Entity tracking helps ensure consistent references throughout the text."
        )
    
    # Issues
    all_issues = consistency.get("all_issues", [])
    if all_issues:
        issue_types = {}
        for issue in all_issues:
            t = issue.get("type", "unknown")
            issue_types[t] = issue_types.get(t, 0) + 1
        
        issue_summary = ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in issue_types.items())
        explanations["issues"] = (
            f"Consistency issues found: {issue_summary}. "
            "Review these to ensure clear and consistent narrative."
        )
    else:
        explanations["issues"] = "No consistency issues detected. Entity references are clear and consistent."
    
    return explanations


def explain_issues(issues: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate explanations for detected issues."""
    explained_issues = []
    
    # Long sentences
    long_sentences = issues.get("long_sentences", [])
    for issue in long_sentences:
        explained_issues.append({
            "type": "Long Sentence",
            "severity": issue.get("severity", "medium"),
            "location": f"Sentence {issue.get('index', 0) + 1}",
            "explanation": (
                f"This sentence has {issue.get('word_count', 0)} words, "
                f"which is {issue.get('excess', 0)} words over the recommended limit. "
                "Long sentences can be hard to follow. Consider breaking it into smaller sentences."
            ),
            "example": issue.get("sentence", "")[:100] + "..." if len(issue.get("sentence", "")) > 100 else issue.get("sentence", "")
        })
    
    # Repeated words
    repeated_words = issues.get("repeated_words", [])
    for issue in repeated_words:
        explained_issues.append({
            "type": "Repeated Word",
            "severity": issue.get("severity", "medium"),
            "location": "Throughout text",
            "explanation": (
                f"The word '{issue.get('word', '')}' appears {issue.get('count', 0)} times "
                f"({issue.get('frequency', 0)}% of content words). "
                "Consider using synonyms or restructuring sentences to reduce repetition."
            ),
            "suggestion": get_synonym_suggestion(issue.get("word", ""))
        })
    
    return explained_issues


def get_synonym_suggestion(word: str) -> str:
    """Get synonym suggestions for common repeated words."""
    synonyms = {
        "said": "stated, mentioned, expressed, noted, explained, remarked",
        "good": "excellent, great, fine, positive, beneficial, favorable",
        "bad": "poor, negative, unfavorable, detrimental, adverse",
        "big": "large, substantial, significant, considerable, major",
        "small": "little, minor, slight, minimal, modest",
        "important": "significant, crucial, vital, essential, key",
        "very": "extremely, highly, particularly, especially, remarkably",
        "really": "truly, genuinely, actually, indeed, certainly",
        "thing": "item, object, matter, aspect, element",
        "things": "items, objects, matters, aspects, elements",
    }
    
    return synonyms.get(word.lower(), f"Consider alternatives to '{word}'")


def generate_actionable_suggestions(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate prioritized, actionable suggestions."""
    suggestions = []
    
    # From enhancer suggestions if available
    enhancer_suggestions = results.get("suggestions", [])
    for sug in enhancer_suggestions:
        suggestions.append({
            "category": sug.get("category", "general"),
            "priority": sug.get("priority", "medium"),
            "action": sug.get("suggestion", ""),
            "impact": sug.get("impact", ""),
            "how_to": get_how_to(sug.get("category", ""))
        })
    
    # Add suggestions based on issues
    issues = results.get("issues", {})
    
    if issues.get("long_sentences"):
        suggestions.append({
            "category": "sentence_structure",
            "priority": "high" if len(issues["long_sentences"]) > 2 else "medium",
            "action": f"Break down {len(issues['long_sentences'])} long sentences",
            "impact": "Improved readability and comprehension",
            "how_to": "Look for natural break points like conjunctions (and, but, so) or semicolons. Each main idea should typically be its own sentence."
        })
    
    if issues.get("repeated_words"):
        top_repeated = issues["repeated_words"][:3]
        words = ", ".join(r["word"] for r in top_repeated)
        suggestions.append({
            "category": "vocabulary",
            "priority": "medium",
            "action": f"Vary word choice for: {words}",
            "impact": "More engaging and professional writing",
            "how_to": "Use a thesaurus to find synonyms, or restructure sentences to eliminate the need for repeated words."
        })
    
    # Style transformation suggestion
    style = results.get("style_analysis", {})
    if style.get("dominant_style") == "casual":
        suggestions.append({
            "category": "style",
            "priority": "low",
            "action": "Consider formalizing the text if intended for professional use",
            "impact": "More appropriate tone for business or academic contexts",
            "how_to": "Use the style transformation feature to automatically convert casual language to formal."
        })
    
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda x: priority_order.get(x["priority"], 3))
    
    return suggestions


def get_how_to(category: str) -> str:
    """Get how-to guidance for each category."""
    how_tos = {
        "readability": "Use shorter sentences and common words. Aim for 15-20 words per sentence on average.",
        "sentence_length": "Identify the main idea and supporting details. Make the main idea one sentence, and details can be separate sentences.",
        "vocabulary": "Replace complex words with simpler alternatives. Ask: 'Would a 12-year-old understand this word?'",
        "flow": "Add transition words at the beginning of sentences: 'However,' 'Therefore,' 'Additionally,' 'For example,'",
        "variety": "Start sentences with different words: articles (The, A), pronouns (They, It), adverbs (However, Additionally), or nouns.",
    }
    return how_tos.get(category, "Review the specific issue and apply targeted improvements.")


def format_explanation_report(explanations: Dict[str, Any]) -> str:
    """Format explanations as a readable report."""
    lines = []
    
    # Summary
    lines.append("=" * 60)
    lines.append("WRITING ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(explanations.get("summary", "No summary available."))
    lines.append("")
    
    # Readability
    readability = explanations.get("readability", {})
    if readability:
        lines.append("READABILITY")
        lines.append("-" * 40)
        for key, value in readability.items():
            lines.append(f"• {value}")
        lines.append("")
    
    # Flow
    flow = explanations.get("flow", {})
    if flow:
        lines.append("FLOW ANALYSIS")
        lines.append("-" * 40)
        for key, value in flow.items():
            lines.append(f"• {value}")
        lines.append("")
    
    # Issues
    issues = explanations.get("issues", [])
    if issues:
        lines.append("ISSUES FOUND")
        lines.append("-" * 40)
        for issue in issues:
            lines.append(f"[{issue['severity'].upper()}] {issue['type']}")
            lines.append(f"  Location: {issue['location']}")
            lines.append(f"  {issue['explanation']}")
            lines.append("")
    
    # Suggestions
    suggestions = explanations.get("suggestions", [])
    if suggestions:
        lines.append("ACTIONABLE SUGGESTIONS")
        lines.append("-" * 40)
        for i, sug in enumerate(suggestions, 1):
            lines.append(f"{i}. [{sug['priority'].upper()}] {sug['action']}")
            lines.append(f"   Impact: {sug['impact']}")
            lines.append(f"   How to: {sug['how_to']}")
            lines.append("")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
#  Phase 11 — New explanation generators
# ═══════════════════════════════════════════════════════════

def explain_grammar(grammar: Dict[str, Any]) -> Dict[str, str]:
    """Generate writer-friendly explanations for grammar analysis."""
    if not grammar:
        return {"summary": "Grammar analysis was not performed."}

    explanations: Dict[str, str] = {}
    summary = grammar.get("summary", {})
    total = summary.get("total_issues", 0)
    grade = summary.get("overall_grade", "—")

    explanations["grade"] = (
        f"Grammar grade: {grade}. "
        f"{'Excellent — very few issues.' if grade in ('A', 'A+') else ''}"
        f"{'Good — minor issues to address.' if grade == 'B' else ''}"
        f"{'Fair — several issues need attention.' if grade == 'C' else ''}"
        f"{'Needs work — review the flagged items carefully.' if grade in ('D', 'F') else ''}"
    )

    spell = grammar.get("spell_errors", [])
    if spell:
        explanations["spelling"] = (
            f"{len(spell)} spelling error{'s' if len(spell) != 1 else ''} detected. "
            "Misspelled words can undermine credibility. Double-check proper nouns and "
            "technical terms that may be flagged incorrectly."
        )

    tense = grammar.get("tense_consistency", [])
    if tense:
        explanations["tense"] = (
            f"{len(tense)} tense-consistency issue{'s' if len(tense) != 1 else ''}. "
            "Shifting between past, present, and future tenses within the same passage "
            "can confuse readers. Pick one primary tense and stick with it unless a shift is intentional."
        )

    punct = grammar.get("punctuation_issues", [])
    if punct:
        explanations["punctuation"] = (
            f"{len(punct)} punctuation issue{'s' if len(punct) != 1 else ''}. "
            "Proper punctuation guides readers through your ideas. "
            "Common pitfalls include comma splices, missing serial commas, and misplaced semicolons."
        )

    explanations["total"] = f"Total grammar issues: {total}."
    return explanations


def explain_tone(tone: Dict[str, Any]) -> Dict[str, str]:
    """Generate explanations for tone analysis."""
    if not tone or tone.get("error"):
        return {"summary": "Tone analysis was not performed or encountered an error."}

    explanations: Dict[str, str] = {}
    dominant = tone.get("dominant_tone", "neutral")
    label = tone.get("tone_label", dominant)
    desc = tone.get("tone_description", "")

    explanations["dominant"] = (
        f"Dominant tone: {label}. {desc} "
        "Tone shapes how readers feel about your message — make sure it aligns with your intent."
    )

    scores = tone.get("tone_scores", {})
    if scores:
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        breakdown = ", ".join(f"{k} ({v*100:.0f}%)" for k, v in top)
        explanations["scores"] = f"Top tones detected: {breakdown}."

    per_sent = tone.get("per_sentence", [])
    if per_sent:
        shifts = sum(
            1 for i in range(1, len(per_sent))
            if per_sent[i].get("dominant") != per_sent[i - 1].get("dominant")
        )
        explanations["trajectory"] = (
            f"Tone shifted {shifts} time{'s' if shifts != 1 else ''} across {len(per_sent)} sentences. "
            f"{'Consistent tone throughout.' if shifts == 0 else ''}"
            f"{'Some variety — make sure shifts are deliberate.' if 0 < shifts <= 3 else ''}"
            f"{'Frequent tone changes — readers may find this jarring.' if shifts > 3 else ''}"
        )

    return explanations


def explain_antipatterns(ap: Dict[str, Any]) -> Dict[str, str]:
    """Generate explanations for anti-pattern detection."""
    if not ap or ap.get("error"):
        return {"summary": "Anti-pattern analysis was not performed."}

    explanations: Dict[str, str] = {}
    summary = ap.get("summary", {})
    total = summary.get("total", 0)

    explanations["overview"] = (
        f"{total} anti-pattern{'s' if total != 1 else ''} detected across your text. "
        "Anti-patterns are common writing habits that weaken prose. "
        "Fixing them strengthens clarity, immersion, and reader engagement."
    )

    cats = ap.get("categories", {})
    for key, data in cats.items():
        count = data.get("count", 0)
        if count == 0:
            continue
        tip = data.get("educational_tip", "")
        explanations[key] = f"{key.replace('_', ' ').title()}: {count} instance{'s' if count != 1 else ''}. {tip}"

    return explanations


def explain_passive_voice(pv: Dict[str, Any]) -> Dict[str, str]:
    """Generate explanations for passive voice detection."""
    if not pv:
        return {"summary": "Passive voice analysis was not performed."}

    count = pv.get("passive_count", 0)
    pct = pv.get("passive_percentage", 0)

    summary = (
        f"{count} passive-voice construction{'s' if count != 1 else ''} found ({pct:.1f}% of sentences). "
    )
    if pct > 30:
        summary += "This is quite high — active voice is usually more direct and engaging. "
    elif pct > 15:
        summary += "Moderate usage — consider converting some to active voice for stronger prose. "
    else:
        summary += "Good balance — passive voice is used sparingly. "

    summary += (
        "Passive voice is not always wrong; it works well when the action matters more than the actor, "
        "or when the actor is unknown."
    )

    return {"summary": summary}


def explain_filler_words(fw: Dict[str, Any]) -> Dict[str, str]:
    """Generate explanations for filler word detection."""
    if not fw:
        return {"summary": "Filler word analysis was not performed."}

    total = fw.get("total_fillers", 0)
    unique = fw.get("unique_fillers", 0)
    details = fw.get("filler_details", {})

    if total == 0:
        return {"summary": "No filler words detected — your writing is tight and purposeful."}

    top = sorted(details.items(), key=lambda x: x[1], reverse=True)[:5]
    top_str = ", ".join(f"'{w}' ({c}×)" for w, c in top)

    return {
        "summary": (
            f"{total} filler word{'s' if total != 1 else ''} found ({unique} unique). "
            f"Most frequent: {top_str}. "
            "Filler words dilute your message. Removing them makes sentences crisper. "
            "Read each sentence aloud — if a word can be dropped without changing meaning, cut it."
        )
    }


def explain_cliches(cl: Dict[str, Any]) -> Dict[str, str]:
    """Generate explanations for cliché detection."""
    if not cl:
        return {"summary": "Cliché analysis was not performed."}

    count = cl.get("cliches_found", 0)
    if count == 0:
        return {"summary": "No clichés detected — your language feels fresh and original."}

    cliches_list = cl.get("cliches", [])
    examples = ", ".join(f'"{c.get("cliche", "")}"' for c in cliches_list[:3])

    return {
        "summary": (
            f"{count} cliché{'s' if count != 1 else ''} found (e.g. {examples}). "
            "Clichés are overused phrases that have lost their impact. "
            "Replace them with original imagery or direct language to make your writing stand out."
        )
    }


def explain_vocabulary(vc: Dict[str, Any]) -> Dict[str, str]:
    """Generate explanations for vocabulary complexity."""
    if not vc:
        return {"summary": "Vocabulary analysis was not performed."}

    diversity = vc.get("lexical_diversity", 0)
    level = vc.get("complexity_level", "unknown")
    advanced = vc.get("advanced_words", 0)

    return {
        "summary": (
            f"Vocabulary diversity: {diversity*100:.0f}% · Level: {level} · "
            f"Advanced words: {advanced}. "
            f"{'Excellent range — you use a rich variety of words.' if diversity > 0.7 else ''}"
            f"{'Good diversity — room for a few more varied word choices.' if 0.4 <= diversity <= 0.7 else ''}"
            f"{'Low diversity — many repeated words. A thesaurus can help.' if diversity < 0.4 else ''}"
        ),
        "interpretation": vc.get("interpretation", ""),
    }
