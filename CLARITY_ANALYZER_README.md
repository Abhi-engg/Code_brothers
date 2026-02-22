# Text Clarity and Structure Analyzer

A comprehensive Python tool for analyzing text clarity, readability, and structure.

## 🎯 Purpose
Help writers improve readability and flow by detecting common writing issues.

## 📦 Libraries Used
- **nltk** - Natural Language Processing
- **textstat** - Readability metrics
- **re** - Pattern matching

## ✨ Features

### 1. Long Sentence Detection
Identifies sentences exceeding a word count threshold (default: 100 words).

```python
from nlp_engine.clarity_analyzer import detect_long_sentences

text = "Your long text here..."
issues = detect_long_sentences(text, threshold=100)
```

### 2. Passive Voice Detection
Finds passive voice constructions (e.g., "was done by").

```python
from nlp_engine.clarity_analyzer import detect_passive_voice

issues = detect_passive_voice(text)
```

### 3. Word Repetition Detection
Catches words repeated within close proximity (default: 50 characters).

```python
from nlp_engine.clarity_analyzer import detect_repetition

issues = detect_repetition(text, proximity=50, min_word_length=4)
```

### 4. Readability Scoring
Calculates multiple readability metrics:
- Flesch Reading Ease
- Flesch-Kincaid Grade Level
- Gunning Fog Index
- SMOG Index
- Automated Readability Index
- Coleman-Liau Index

```python
from nlp_engine.clarity_analyzer import readability_score

scores = readability_score(text)
print(scores['scores']['flesch_reading_ease'])
print(scores['interpretation']['difficulty'])
```

### 5. Complex Sentence Detection
Identifies sentences with many long words or high syllable counts.

```python
from nlp_engine.clarity_analyzer import detect_complex_sentences

issues = detect_complex_sentences(text)
```

### 6. Complete Analysis (Main Function)
Runs all checks and provides comprehensive results.

```python
from nlp_engine.clarity_analyzer import analyze_clarity

results = analyze_clarity(
    text,
    long_sentence_threshold=100,
    repetition_proximity=50
)
```

## 📊 Output Format

All issues follow this structured format:

```python
{
    "issue": "Description of the problem",
    "original_text": "The problematic text segment",
    "suggestion": "How to fix it",
    "explanation": "Why this matters"
}
```

### Complete Analysis Output

```python
{
    "success": True,
    "input": {
        "text": "...",
        "character_count": 1234,
        "word_count": 200,
        "sentence_count": 10
    },
    "analysis": {
        "long_sentences": [...],
        "passive_voice": [...],
        "repetitions": [...],
        "complex_sentences": [...],
        "readability": {...}
    },
    "summary": {
        "total_issues": 5,
        "issue_breakdown": {
            "long_sentences": 1,
            "passive_voice": 2,
            "repetitions": 1,
            "complex_sentences": 0,
            "low_readability": 1
        },
        "overall_assessment": "Moderate clarity issues detected...",
        "priority": "medium"
    },
    "suggestions": [...],
    "readability_scores": {...},
    "interpretation": {
        "difficulty": "Easy",
        "target_audience": "6th-8th grade"
    }
}
```

## 🚀 Quick Start

```python
from nlp_engine.clarity_analyzer import analyze_clarity

# Analyze your text
text = """
Your text here. It can be as long as you want.
The analyzer will check for various clarity issues.
"""

results = analyze_clarity(text)

# Check results
print(f"Total Issues: {results['summary']['total_issues']}")
print(f"Assessment: {results['summary']['overall_assessment']}")
print(f"Readability: {results['interpretation']['difficulty']}")

# View suggestions
for suggestion in results['suggestions']:
    print(f"\n{suggestion['category']}: {suggestion['issue']}")
    print(f"Suggestion: {suggestion['suggestion']}")
```

## 📈 Readability Scale

**Flesch Reading Ease Score (0-100)**
- 80-100: Very Easy (5th grade)
- 60-80: Easy (6th-8th grade)
- 50-60: Fairly Difficult (High school)
- 30-50: Difficult (College)
- 0-30: Very Difficult (College graduate+)

## 🎛️ Customization

### Adjust Thresholds

```python
# Stricter analysis
results = analyze_clarity(
    text,
    long_sentence_threshold=50,  # Flag sentences > 50 words
    repetition_proximity=30       # Flag repetitions within 30 chars
)
```

### Individual Checks

```python
# Run only specific checks
from nlp_engine.clarity_analyzer import (
    detect_long_sentences,
    detect_passive_voice,
    readability_score
)

long_sents = detect_long_sentences(text, threshold=75)
passive = detect_passive_voice(text)
scores = readability_score(text)
```

## 💡 Use Cases

1. **Content Writing** - Ensure blog posts are readable
2. **Academic Writing** - Check for overly complex sentences
3. **Technical Documentation** - Improve clarity
4. **Email Communication** - Make messages clearer
5. **Marketing Copy** - Optimize for target audience

## 🔍 Detection Details

### Long Sentences
- Counts alphanumeric words only
- Excludes punctuation from count
- Provides exact word count and sentence number

### Passive Voice
- Uses POS tagging to identify patterns
- Detects "be" verb + past participle
- Suggests active voice alternatives

### Word Repetition
- Case-insensitive matching
- Ignores common words (that, this, with, etc.)
- Shows exact character distance
- Provides context around repetition

### Complex Sentences
- Counts words > 10 characters
- Calculates average syllables per word
- Flags: 3+ long words OR 2.5+ syllables/word

### Readability
- Multiple established metrics
- U.S. grade level equivalents
- Target audience recommendations

## 📝 Example Output

```
[PASSIVE VOICE]
Issue: Passive voice detected
Text: "The report was written by the team."
Suggestion: Consider rewriting in active voice to make the sentence more direct.
Explanation: Passive voice is less direct than active voice. Active voice makes 
writing clearer by emphasizing who performs the action.

[WORD REPETITION]
Issue: Word repetition detected
Repeated Word: "team"
Distance: 22 characters
Suggestion: Consider using a synonym or rephrasing to avoid repeating 'team'.
Explanation: Repeating the same word close together can make writing monotonous.
```

## 🧪 Testing

Run the built-in test:

```bash
python nlp_engine/clarity_analyzer.py
```

Or use the examples:

```bash
python example_clarity_usage.py
```

## ⚙️ Requirements

Install dependencies:

```bash
pip install nltk textstat
```

NLTK data is downloaded automatically on first use.

## 📚 API Reference

See [example_clarity_usage.py](example_clarity_usage.py) for comprehensive usage examples.

---

**Created for:** Code_brothers Project  
**Date:** February 22, 2026
