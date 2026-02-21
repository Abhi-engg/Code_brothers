"""
Demo Script - Enhanced NLP Engine Features
Showcases the new powerful capabilities of the Writing Assistant
"""

from nlp_engine import WritingAssistant

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def demo_passive_voice():
    print_section("1. PASSIVE VOICE DETECTION")
    
    assistant = WritingAssistant()
    text = "The report was written by John. The data was analyzed by our team. Sarah wrote the conclusion."
    
    results = assistant.analyze(text)
    passive = results["text_analysis"]["passive_voice"]
    
    print(f"Text: {text}")
    print(f"\nFound {len(passive)} passive voice instances:")
    for item in passive:
        print(f"  - Sentence {item['index'] + 1}: '{item['sentence']}'")
        print(f"    Construction: {item['passive_constructions']}")

def demo_sentiment():
    print_section("2. SENTIMENT ANALYSIS")
    
    assistant = WritingAssistant()
    texts = [
        "This is an excellent achievement! Great work on this amazing project.",
        "The results are disappointing and problematic. We face difficult challenges.",
        "The data shows typical patterns. Standard procedures were followed."
    ]
    
    for text in texts:
        results = assistant.analyze(text)
        sentiment = results["text_analysis"]["sentiment"]
        print(f"\nText: {text[:60]}...")
        print(f"Sentiment: {sentiment['sentiment']} (score: {sentiment['score']})")
        print(f"Positive words: {sentiment['positive_words']}, Negative: {sentiment['negative_words']}")

def demo_consistency():
    print_section("3. TENSE & PERSPECTIVE CONSISTENCY")
    
    assistant = WritingAssistant()
    text = """John walks to the office. He opened his laptop. 
    He will start working on the project. Yesterday, he finished the report."""
    
    results = assistant.analyze(text)
    tense = results["consistency"]["tense"]
    perspective = results["consistency"]["perspective"]
    
    print(f"Text: {text}")
    print(f"\nTense Analysis:")
    print(f"  Dominant tense: {tense['dominant_tense']}")
    print(f"  Consistency score: {tense['consistency_score']}%")
    print(f"  Tense shifts detected: {len(tense['issues'])}")
    
    print(f"\nPerspective Analysis:")
    print(f"  Dominant perspective: {perspective['dominant_perspective']}")
    print(f"  Consistency score: {perspective['consistency_score']}%")
    print(f"  Shifts detected: {perspective['shift_count']}")

def demo_vocabulary():
    print_section("4. VOCABULARY COMPLEXITY")
    
    assistant = WritingAssistant()
    texts = [
        "The cat sat on the mat. The dog ran to the cat.",
        "The implementation of sophisticated methodologies necessitates comprehensive evaluation."
    ]
    
    for text in texts:
        results = assistant.analyze(text)
        vocab = results["text_analysis"]["vocabulary"]
        print(f"\nText: {text}")
        print(f"Lexical diversity: {vocab['lexical_diversity']}")
        print(f"Complexity level: {vocab['complexity_level']}")
        print(f"Advanced words: {vocab['advanced_words']}")

def demo_fillers():
    print_section("5. FILLER WORD DETECTION")
    
    assistant = WritingAssistant()
    text = "I really just wanted to basically say that this is actually very important and quite significant."
    
    results = assistant.analyze(text)
    fillers = results["text_analysis"]["filler_words"]
    
    print(f"Text: {text}")
    print(f"\nTotal fillers found: {fillers['total_fillers']}")
    print(f"Unique fillers: {fillers['unique_fillers']}")
    print("Most common fillers:")
    for word, count in list(fillers['filler_details'].items())[:5]:
        print(f"  - '{word}': {count} times")

def demo_transformations():
    print_section("6. STYLE TRANSFORMATIONS")
    
    assistant = WritingAssistant()
    
    # Technical to plain
    tech_text = "We need to leverage our core competencies to optimize the paradigm and facilitate synergy."
    plain = assistant.simplify_technical(tech_text)
    print("\nTechnical → Plain Language:")
    print(f"Original: {tech_text}")
    print(f"Simplified: {plain['transformed']}")
    print(f"Changes: {plain['change_count']}")
    
    # Conciseness
    wordy = "Due to the fact that we need to make a decision at this point in time"
    concise = assistant.improve_conciseness(wordy)
    print("\nConciseness Enhancement:")
    print(f"Original: {wordy}")
    print(f"Concise: {concise['transformed']}")
    
    # Strengthen verbs
    weak = "The team is able to provide assistance with the implementation"
    strong = assistant.strengthen_writing(weak)
    print("\nVerb Strengthening:")
    print(f"Original: {weak}")
    print(f"Strengthened: {strong['transformed']}")

def demo_cliches():
    print_section("7. CLICHÉ DETECTION")
    
    assistant = WritingAssistant()
    text = "At the end of the day, we need to think outside the box and leverage our low hanging fruit to move the needle."
    
    results = assistant.analyze(text)
    cliches = results["style_analysis"]["cliches"]
    
    print(f"Text: {text}")
    print(f"\nClichés found: {cliches['cliches_found']}")
    for cliche_item in cliches['cliches'][:3]:
        print(f"  - '{cliche_item['cliche']}' at position {cliche_item['position']}")

def demo_quick_check():
    print_section("8. QUICK CHECK (Fast Scan)")
    
    assistant = WritingAssistant()
    text = "The data was analyzed by the team. We're gonna present really important findings that leverage best practices."
    
    quick = assistant.quick_check(text)
    
    print(f"Text: {text}")
    print(f"\nQuick Scan Results:")
    print(f"  Passive voice instances: {len(quick['passive_voice'])}")
    print(f"  Filler words: {quick['filler_words']['total_fillers']}")
    print(f"  Clichés: {quick['cliches']['cliches_found']}")
    print(f"  Sentiment: {quick['sentiment']['sentiment']}")

def demo_comprehensive_scores():
    print_section("9. COMPREHENSIVE SCORING")
    
    assistant = WritingAssistant()
    text = """
    Dr. Sarah Johnson presented her findings at MIT yesterday. She explained 
    why the results are important for the industry. Johnson worked on this 
    research for three years and the team is excited about the breakthrough.
    
    The methodology was comprehensive and the data analysis was thorough.
    Future research will build on these foundations.
    """
    
    results = assistant.analyze(text)
    scores = results["scores"]
    
    print("Text analysis complete!\n")
    print("📊 Comprehensive Scores:")
    print(f"  Overall Score:        {scores.get('overall', 'N/A')}/100")
    print(f"  Readability:          {scores.get('readability', 'N/A')}/100")
    print(f"  Flow:                 {scores.get('flow', 'N/A')}/100")
    print(f"  Consistency:          {scores.get('consistency', 'N/A')}/100")
    print(f"  Vocabulary:           {scores.get('vocabulary', 'N/A')}/100")
    print(f"  Rhythm:               {scores.get('rhythm', 'N/A')}/100")
    print(f"  Issues Score:         {scores.get('issues', 'N/A')}/100")

def main():
    """Run all demonstrations"""
    print("\n" + "🎨"*35)
    print("  WRITING ASSISTANT - ENHANCED NLP ENGINE DEMO")
    print("  Showcasing 15+ New Powerful Features")
    print("🎨"*35)
    
    try:
        demo_passive_voice()
        demo_sentiment()
        demo_consistency()
        demo_vocabulary()
        demo_fillers()
        demo_transformations()
        demo_cliches()
        demo_quick_check()
        demo_comprehensive_scores()
        
        print("\n" + "="*70)
        print("  ✨ Demo Complete! All enhanced features working perfectly!")
        print("="*70)
        print("\n📖 For more information:")
        print("   - ENHANCEMENTS.md - Detailed feature documentation")
        print("   - QUICK_START.md - Usage examples and best practices")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        print("   Make sure spaCy model is installed: python -m spacy download en_core_web_sm")

if __name__ == "__main__":
    main()
