"""
Example usage of the Text Clarity and Structure Analyzer
"""

from nlp_engine.clarity_analyzer import (
    analyze_clarity,
    detect_long_sentences,
    detect_passive_voice,
    detect_repetition,
    readability_score,
    detect_complex_sentences
)

# Example 1: Quick analysis
print("="*80)
print("EXAMPLE 1: Quick Clarity Analysis")
print("="*80)

sample_text = """
The meeting was scheduled by the manager for next Tuesday. The meeting will 
discuss important topics. Everyone should attend the meeting to hear the updates.
"""

results = analyze_clarity(sample_text)

print(f"\nOverall: {results['summary']['overall_assessment']}")
print(f"Total Issues: {results['summary']['total_issues']}")
print(f"Readability: {results['interpretation']['difficulty']}")

# Example 2: Checking specific issues
print("\n" + "="*80)
print("EXAMPLE 2: Check Specific Issues")
print("="*80)

long_text = """
The comprehensive evaluation of the newly implemented software system that was 
developed by our team over the past six months has revealed several significant 
performance improvements and efficiency gains that will substantially benefit our 
organization's operations and contribute to achieving our strategic objectives 
while maintaining the highest standards of quality and reliability.
"""

# Check for long sentences
long_sents = detect_long_sentences(long_text, threshold=30)
print(f"\nLong sentences found: {len(long_sents)}")
if long_sents:
    print(f"  Word count: {long_sents[0]['word_count']}")
    print(f"  Suggestion: {long_sents[0]['suggestion']}")

# Check for passive voice
passive = detect_passive_voice(long_text)
print(f"\nPassive voice instances: {len(passive)}")
if passive:
    print(f"  Phrase: '{passive[0]['passive_phrase']}'")

# Check readability
readability = readability_score(long_text)
print(f"\nReadability Score: {readability['scores']['flesch_reading_ease']}")
print(f"Grade Level: {readability['scores']['average_grade_level']}")

# Example 3: Detailed suggestions
print("\n" + "="*80)
print("EXAMPLE 3: Get All Suggestions")
print("="*80)

text_with_issues = """
The report was written by the team. The team worked hard. The team delivered 
excellent results. The analysis was performed carefully and the data was 
collected systematically.
"""

results = analyze_clarity(text_with_issues)

print(f"\nSuggestions ({len(results['suggestions'])}):")
for i, suggestion in enumerate(results['suggestions'], 1):
    print(f"\n{i}. [{suggestion['category']}]")
    print(f"   {suggestion['issue']}")
    print(f"   💡 {suggestion['suggestion']}")

# Example 4: Custom thresholds
print("\n" + "="*80)
print("EXAMPLE 4: Custom Thresholds")
print("="*80)

# More strict analysis (shorter threshold for long sentences)
strict_results = analyze_clarity(
    "This is a moderately long sentence with quite a few words in it that might be considered too long.",
    long_sentence_threshold=15,
    repetition_proximity=100
)

print(f"With threshold=15 words: {strict_results['summary']['issue_breakdown']['long_sentences']} long sentences")

# Example 5: Professional writing check
print("\n" + "="*80)
print("EXAMPLE 5: Professional Writing Check")
print("="*80)

professional_text = """
We analyzed customer feedback and found three key insights. First, users want 
faster response times. Second, they value clear communication. Third, they 
appreciate proactive support.
"""

results = analyze_clarity(professional_text)

print(f"Assessment: {results['summary']['overall_assessment']}")
print(f"Priority: {results['summary']['priority']}")
print(f"Readability: {results['interpretation']['difficulty']} ({results['interpretation']['target_audience']})")
print(f"Issues: {results['summary']['total_issues']}")

if results['summary']['total_issues'] == 0:
    print("✅ This text is clear and well-structured!")

print("\n" + "="*80)
print("Analysis complete!")
print("="*80)
