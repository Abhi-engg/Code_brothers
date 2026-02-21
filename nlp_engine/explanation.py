"""
Explanation Generator Module
Generate human-readable explanations for all analysis results
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
        "suggestions": generate_actionable_suggestions(analysis_results)
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
