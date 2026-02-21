"""
Writing Assistant Pipeline
Main orchestrator that integrates all NLP modules into a unified analysis pipeline
"""

import json
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import all modules
from . import text_analyzer
from . import enhancer
from . import style_transformer
from . import consistency_checker
from . import explanation
from . import grammar_checker


class WritingAssistant:
    """
    Main writing assistant class that orchestrates all NLP analysis modules.
    
    Features:
    - Text analysis (tokenization, POS tagging, NER)
    - Readability scoring
    - Flow analysis
    - Style transformation
    - Consistency checking
    - Explanation generation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the WritingAssistant.
        
        Args:
            config: Optional configuration dictionary with settings:
                - long_sentence_threshold: int (default: 25)
                - repeated_word_min_count: int (default: 3)
                - target_style: str (default: 'formal')
                - enable_parallel: bool (default: True)
        """
        self.config = config or {}
        self.long_sentence_threshold = self.config.get("long_sentence_threshold", 25)
        self.repeated_word_min_count = self.config.get("repeated_word_min_count", 3)
        self.target_style = self.config.get("target_style", "formal")
        self.enable_parallel = self.config.get("enable_parallel", True)
        
        # Get the spaCy model reference
        self.nlp = text_analyzer.get_nlp()
    
    def analyze(self, text: str, features: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive text analysis.
        
        Args:
            text: Input text to analyze
            features: Optional dictionary to enable/disable specific features:
                - text_analysis: bool (default: True)
                - readability: bool (default: True)
                - flow: bool (default: True)
                - style: bool (default: True)
                - consistency: bool (default: True)
                - transform: bool (default: False)
                - explanations: bool (default: True)
        
        Returns:
            Structured JSON-compatible dictionary with all analysis results
        """
        # Default features
        default_features = {
            "text_analysis": True,
            "readability": True,
            "flow": True,
            "style": True,
            "consistency": True,
            "grammar": True,
            "transform": False,
            "explanations": True
        }
        features = {**default_features, **(features or {})}
        
        # Initialize results
        results = {
            "input": {
                "text": text,
                "character_count": len(text),
                "features_enabled": features
            },
            "text_analysis": {},
            "readability": {},
            "flow": {},
            "style_analysis": {},
            "style_transformation": {},
            "consistency": {},
            "issues": {},
            "suggestions": [],
            "explanations": {},
            "scores": {}
        }
        
        # Step 1: Core text analysis (required for other steps)
        if features["text_analysis"]:
            analysis = text_analyzer.analyze(text)
            doc = analysis.pop("doc")  # Extract doc for reuse
            results["text_analysis"] = analysis
            
            # Detect issues
            long_sentences = text_analyzer.detect_long_sentences(
                analysis["sentences"], 
                self.long_sentence_threshold
            )
            repeated_words = text_analyzer.detect_repeated_words(
                analysis["tokens"],
                self.repeated_word_min_count
            )
            sentence_structures = text_analyzer.analyze_sentence_structure(doc)
            
            # NEW: Advanced text analysis features
            passive_voice = text_analyzer.detect_passive_voice(doc)
            sentiment = text_analyzer.analyze_sentiment(doc)
            vocabulary_complexity = text_analyzer.analyze_vocabulary_complexity(doc, analysis["tokens"])
            filler_words = text_analyzer.detect_filler_words(analysis["tokens"])
            
            results["text_analysis"]["sentence_structures"] = sentence_structures
            
            # Store enhanced features at top level for API response
            # Wrap passive voice list in dict with stats for frontend
            sentence_count = len(list(doc.sents))
            results["passive_voice"] = {
                "passive_count": len(passive_voice),
                "passive_percentage": round((len(passive_voice) / sentence_count * 100) if sentence_count > 0 else 0, 1),
                "passive_instances": passive_voice
            }
            results["sentiment"] = sentiment
            results["vocabulary_complexity"] = vocabulary_complexity
            results["filler_words"] = filler_words
            
            # Store only list-type issues in issues dict
            results["issues"]["long_sentences"] = long_sentences
            results["issues"]["repeated_words"] = repeated_words
        else:
            # Still need doc for other analyses
            doc = self.nlp(text)
            analysis = {"sentences": [], "tokens": [], "entities": []}
        
        # Grammar analysis (needs doc)
        if features.get("grammar", True):
            try:
                results["grammar_analysis"] = grammar_checker.check_grammar(doc, text)
                # Add grammar issues to the issues dict
                grammar_issues = results["grammar_analysis"].get("all_issues", [])
                if grammar_issues:
                    results["issues"]["grammar"] = grammar_issues
            except Exception as e:
                results["grammar_analysis"] = {"error": str(e), "total_issues": 0, "grammar_score": 100}
        
        # Tone analysis (needs doc)
        try:
            results["tone_analysis"] = style_transformer.analyze_tone(doc, text)
        except Exception as e:
            results["tone_analysis"] = {"error": str(e), "dominant_tone": "unknown", "tone_scores": {}}
        
        # Tone transformation (if a specific target tone was requested)
        target_tone = self.config.get("target_tone_value")
        if target_tone and target_tone != "auto":
            try:
                results["tone_analysis"]["tone_transformation"] = style_transformer.transform_tone(text, doc, target_tone)
            except Exception as e:
                results["tone_analysis"]["tone_transformation"] = {"error": str(e)}
        
        # Parallel processing of independent analyses
        if self.enable_parallel:
            results = self._run_parallel_analyses(
                text, doc, analysis, features, results
            )
        else:
            results = self._run_sequential_analyses(
                text, doc, analysis, features, results
            )
        
        # Generate explanations (depends on all other results)
        if features["explanations"]:
            results["explanations"] = explanation.generate_explanations(results)
        
        # Calculate aggregate scores
        results["scores"] = self._calculate_scores(results)
        
        return results
    
    def _run_parallel_analyses(
        self, 
        text: str, 
        doc, 
        analysis: Dict, 
        features: Dict[str, bool],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run independent analyses in parallel using ThreadPoolExecutor."""
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {}
            
            # Submit parallel tasks
            if features["readability"]:
                futures["readability"] = executor.submit(
                    enhancer.calculate_readability, text
                )
            
            if features["flow"]:
                futures["flow"] = executor.submit(
                    enhancer.check_flow, 
                    analysis.get("sentences", []), 
                    doc
                )
            
            if features["style"]:
                futures["style"] = executor.submit(
                    style_transformer.analyze_current_style, text
                )
            
            if features["consistency"]:
                futures["consistency"] = executor.submit(
                    self._analyze_consistency_combined,
                    text,
                    doc,
                    analysis.get("entities", [])
                )
            
            if features.get("transform"):
                futures["transform"] = executor.submit(
                    style_transformer.transform_style,
                    text,
                    self.target_style
                )
            
            # NEW: Advanced analysis features
            futures["paragraph_structure"] = executor.submit(
                enhancer.analyze_paragraph_structure, text
            )
            futures["lexical_density"] = executor.submit(
                enhancer.calculate_lexical_density, doc
            )
            futures["sentence_rhythm"] = executor.submit(
                enhancer.analyze_sentence_rhythm, analysis.get("sentences", [])
            )
            futures["tense_consistency"] = executor.submit(
                consistency_checker.check_tense_consistency, doc
            )
            futures["perspective_consistency"] = executor.submit(
                consistency_checker.check_perspective_consistency, doc
            )
            futures["cliches"] = executor.submit(
                style_transformer.detect_cliches, text
            )
            futures["style_scores"] = executor.submit(
                style_transformer.score_style_per_paragraph, text, doc
            )
            
            # Collect results
            for key, future in futures.items():
                try:
                    result = future.result()
                    if key == "readability":
                        results["readability"] = result
                    elif key == "flow":
                        results["flow"] = result
                    elif key == "style":
                        results["style_analysis"] = result
                    elif key == "consistency":
                        results["consistency"] = result
                    elif key == "transform":
                        results["style_transformation"] = result
                    elif key == "paragraph_structure":
                        results["paragraph_structure"] = result
                    elif key == "lexical_density":
                        results["lexical_density"] = result
                    elif key == "sentence_rhythm":
                        results["sentence_rhythm"] = result
                    elif key == "tense_consistency":
                        results["consistency"]["tense"] = result
                        if result.get("issues"):
                            results["issues"]["tense_shifts"] = result["issues"]
                    elif key == "perspective_consistency":
                        results["consistency"]["perspective"] = result
                        if result.get("perspective_shifts"):
                            results["issues"]["perspective_shifts"] = result["perspective_shifts"]
                    elif key == "cliches":
                        results["cliches"] = result
                        # Store cliche list in issues if any found
                        if result.get("cliches") and isinstance(result["cliches"], list):
                            results["issues"]["cliches"] = result["cliches"]
                    elif key == "style_scores":
                        results["style_scores"] = result
                except Exception as e:
                    results[key] = {"error": str(e)}
        
        # Generate improvement suggestions (depends on readability and flow)
        if features["readability"] and features["flow"]:
            results["suggestions"] = enhancer.get_improvement_suggestions(
                results.get("readability", {}),
                results.get("flow", {})
            )
        
        return results
    
    def _run_sequential_analyses(
        self,
        text: str,
        doc,
        analysis: Dict,
        features: Dict[str, bool],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run analyses sequentially (fallback mode)."""
        
        if features["readability"]:
            results["readability"] = enhancer.calculate_readability(text)
        
        if features["flow"]:
            results["flow"] = enhancer.check_flow(
                analysis.get("sentences", []),
                doc
            )
        
        if features["style"]:
            results["style_analysis"] = style_transformer.analyze_current_style(text)
            results["style_scores"] = style_transformer.score_style_per_paragraph(text, doc)
        
        if features["consistency"]:
            results["consistency"] = self._analyze_consistency_combined(
                text,
                doc,
                analysis.get("entities", [])
            )
        
        if features.get("transform"):
            results["style_transformation"] = style_transformer.transform_style(
                text,
                self.target_style
            )
        
        # NEW: Advanced analysis features
        results["paragraph_structure"] = enhancer.analyze_paragraph_structure(text)
        results["lexical_density"] = enhancer.calculate_lexical_density(doc)
        results["sentence_rhythm"] = enhancer.analyze_sentence_rhythm(analysis.get("sentences", []))
        
        # Consistency enhancements
        tense_result = consistency_checker.check_tense_consistency(doc)
        perspective_result = consistency_checker.check_perspective_consistency(doc)
        
        if "consistency" not in results:
            results["consistency"] = {}
        results["consistency"]["tense"] = tense_result
        results["consistency"]["perspective"] = perspective_result
        
        if tense_result.get("issues"):
            results["issues"]["tense_shifts"] = tense_result["issues"]
        if perspective_result.get("perspective_shifts"):
            results["issues"]["perspective_shifts"] = perspective_result["perspective_shifts"]
        
        # Style enhancements - store at top level
        cliches_result = style_transformer.detect_cliches(text)
        results["cliches"] = cliches_result
        # Store cliche list in issues if any found
        if cliches_result.get("cliches") and isinstance(cliches_result["cliches"], list):
            results["issues"]["cliches"] = cliches_result["cliches"]
        
        # Generate improvement suggestions
        if features["readability"] and features["flow"]:
            results["suggestions"] = enhancer.get_improvement_suggestions(
                results.get("readability", {}),
                results.get("flow", {})
            )
        
        return results
    
    def _analyze_consistency_combined(self, text: str, doc, entities: List) -> Dict[str, Any]:
        """
        Combined consistency analysis using both methods.
        
        Returns results in the new format with issue, original_text, suggestion, explanation.
        """
        # Get traditional analysis
        base_analysis = consistency_checker.analyze_narrative_consistency(doc, entities)
        
        # Create NarrativeConsistencyAnalyzer for enhanced analysis
        analyzer = consistency_checker.NarrativeConsistencyAnalyzer()
        enhanced_issues = analyzer.analyze_consistency(text)
        
        # Merge results - use enhanced issues format for all_issues
        base_analysis["all_issues"] = enhanced_issues
        base_analysis["narrative_issues"] = enhanced_issues
        
        # Update total count
        base_analysis["total_issue_count"] = len(enhanced_issues)
        
        return base_analysis
    
    def _calculate_scores(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate aggregate scores from analysis results."""
        scores = {}
        
        # Readability score (0-100, higher is easier to read)
        readability = results.get("readability", {})
        if readability:
            fre = readability.get("scores", {}).get("flesch_reading_ease", 50)
            scores["readability"] = round(max(0, min(100, fre)), 2)
        
        # Flow score
        flow = results.get("flow", {})
        if flow:
            scores["flow"] = flow.get("flow_score", 50)
        
        # Consistency score (weighted average of multiple checks)
        consistency = results.get("consistency", {})
        if consistency:
            entity_score = consistency.get("overall_consistency_score", 100)
            tense_score = consistency.get("tense", {}).get("consistency_score", 100)
            perspective_score = consistency.get("perspective", {}).get("consistency_score", 100)
            
            # Weighted average
            scores["consistency"] = round((entity_score * 0.4 + tense_score * 0.3 + perspective_score * 0.3), 2)
        
        # Issues score (inverse - fewer issues = higher score)
        issues = results.get("issues", {})
        issue_count = (
            len(issues.get("long_sentences", [])) +
            len(issues.get("repeated_words", [])) +
            len(issues.get("passive_voice", [])) +
            len(issues.get("tense_shifts", [])) +
            len(issues.get("perspective_shifts", [])) +
            len(issues.get("cliches", []))
        )
        
        # Factor in filler words
        filler_data = results.get("text_analysis", {}).get("filler_words", {})
        if filler_data:
            issue_count += min(10, filler_data.get("total_fillers", 0) // 2)
        
        scores["issues"] = max(0, 100 - (issue_count * 5))
        
        # NEW: Vocabulary score (based on lexical diversity and complexity)
        vocab_data = results.get("text_analysis", {}).get("vocabulary", {})
        if vocab_data:
            diversity = vocab_data.get("lexical_diversity", 0.5)
            scores["vocabulary"] = round(diversity * 100, 2)
        
        # NEW: Sentiment score (neutral = 100, positive/negative = varies)
        sentiment_data = results.get("text_analysis", {}).get("sentiment", {})
        if sentiment_data:
            sentiment_score = sentiment_data.get("score", 0)
            # Convert -1 to +1 scale to 0-100 (where 0 = neutral = 100)
            scores["sentiment_balance"] = round(100 - abs(sentiment_score * 50), 2)
        
        # NEW: Rhythm score
        rhythm_data = results.get("sentence_rhythm", {})
        if rhythm_data:
            scores["rhythm"] = rhythm_data.get("rhythm_score", 50)
        
        # Overall score (weighted average of all metrics)
        weights = {
            "readability": 0.25,
            "flow": 0.15,
            "consistency": 0.20,
            "issues": 0.20,
            "vocabulary": 0.10,
            "rhythm": 0.10
        }
        
        total_weight = sum(weights[k] for k in weights if k in scores)
        if total_weight > 0:
            overall = sum(
                scores.get(k, 0) * w 
                for k, w in weights.items() 
                if k in scores
            ) / total_weight
            scores["overall"] = round(overall, 2)
        
        return scores
    
    def transform(self, text: str, target_style: str = "formal") -> Dict[str, Any]:
        """
        Transform text to a specific style.
        
        Args:
            text: Input text to transform
            target_style: Target style ('formal', 'casual', 'academic')
        
        Returns:
            Transformation results including original, transformed text and changes
        """
        return style_transformer.transform_style(text, target_style)
    
    def simplify_technical(self, text: str) -> Dict[str, Any]:
        """
        Simplify technical jargon to plain language.
        
        Args:
            text: Technical text to simplify
        
        Returns:
            Simplified text with changes tracked
        """
        return style_transformer.transform_technical_to_plain(text)
    
    def improve_conciseness(self, text: str) -> Dict[str, Any]:
        """
        Make text more concise by removing redundancies.
        
        Args:
            text: Text to make concise
        
        Returns:
            Concise text with changes tracked
        """
        return style_transformer.enhance_conciseness(text)
    
    def strengthen_writing(self, text: str) -> Dict[str, Any]:
        """
        Strengthen writing by replacing weak verbs.
        
        Args:
            text: Text to strengthen
        
        Returns:
            Strengthened text with changes tracked
        """
        return style_transformer.strengthen_verbs(text)
    
    def quick_check(self, text: str) -> Dict[str, Any]:
        """
        Perform a quick check focusing on common issues.
        
        Args:
            text: Text to check
        
        Returns:
            Dictionary with quick analysis results
        """
        doc = self.nlp(text)
        
        passive_list = text_analyzer.detect_passive_voice(doc)
        sentence_count = len(list(doc.sents))
        return {
            "passive_voice": {
                "passive_count": len(passive_list),
                "passive_percentage": round((len(passive_list) / sentence_count * 100) if sentence_count > 0 else 0, 1),
                "passive_instances": passive_list
            },
            "filler_words": text_analyzer.detect_filler_words(text.split()),
            "cliches": style_transformer.detect_cliches(text),
            "sentiment": text_analyzer.analyze_sentiment(doc),
            "summary": f"Quick scan found potential improvements in {len(text.split())} words"
        }
    
    def get_report(self, text: str, features: Optional[Dict[str, bool]] = None) -> str:
        """
        Generate a formatted text report of the analysis.
        
        Args:
            text: Input text to analyze
            features: Optional feature toggles
        
        Returns:
            Formatted text report string
        """
        results = self.analyze(text, features)
        return explanation.format_explanation_report(results.get("explanations", {}))
    
    def to_json(self, text: str, features: Optional[Dict[str, bool]] = None) -> str:
        """
        Return analysis results as JSON string.
        
        Args:
            text: Input text to analyze
            features: Optional feature toggles
        
        Returns:
            JSON string of analysis results
        """
        results = self.analyze(text, features)
        
        # Remove non-serializable objects
        if "text_analysis" in results:
            results["text_analysis"].pop("doc", None)
        
        return json.dumps(results, indent=2, default=str)


def analyze_text(text: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to analyze text without instantiating the class.
    
    Args:
        text: Input text to analyze
        config: Optional configuration dictionary
    
    Returns:
        Analysis results dictionary
    """
    assistant = WritingAssistant(config)
    return assistant.analyze(text)


# Quick test when run directly
if __name__ == "__main__":
    sample_text = """
    John Smith walked into the office. He was gonna present his findings to the team.
    The meeting was really important because it would determine the project's future.
    Smith had worked on this for months. John was confident about the results.
    
    The data shows that our approach is totally awesome and will definitely help us 
    achieve our goals. We've got lots of evidence to support this conclusion.
    However, there are some challenges we need to address.
    """
    
    assistant = WritingAssistant({
        "long_sentence_threshold": 25,  # Lower for testing
        "repeated_word_min_count": 2
    })
    
    print("=" * 60)
    print("WRITING ASSISTANT - ANALYSIS DEMO")
    print("=" * 60)
    
    results = assistant.analyze(sample_text)
    
    print(f"\nInput: {len(sample_text)} characters")
    print(f"\nScores:")
    for score_name, score_value in results.get("scores", {}).items():
        print(f"  - {score_name}: {score_value}")
    
    print(f"\nIssues Found:")
    issues = results.get("issues", {})
    print(f"  - Long sentences: {len(issues.get('long_sentences', []))}")
    print(f"  - Repeated words: {len(issues.get('repeated_words', []))}")
    
    print(f"\nStyle Analysis:")
    style = results.get("style_analysis", {})
    print(f"  - Dominant style: {style.get('dominant_style', 'unknown')}")
    
    print(f"\nConsistency:")
    consistency = results.get("consistency", {})
    print(f"  - Score: {consistency.get('overall_consistency_score', 'N/A')}")
    print(f"  - Issues: {consistency.get('total_issue_count', 0)}")
    
    print("\n" + "=" * 60)
    print("Full JSON output saved to analysis_results.json")
    print("=" * 60)
