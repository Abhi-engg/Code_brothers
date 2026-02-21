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
                - long_sentence_threshold: int (default: 100)
                - repeated_word_min_count: int (default: 3)
                - target_style: str (default: 'formal')
                - enable_parallel: bool (default: True)
        """
        self.config = config or {}
        self.long_sentence_threshold = self.config.get("long_sentence_threshold", 100)
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
            
            results["text_analysis"]["sentence_structures"] = sentence_structures
            results["issues"]["long_sentences"] = long_sentences
            results["issues"]["repeated_words"] = repeated_words
        else:
            # Still need doc for other analyses
            doc = self.nlp(text)
            analysis = {"sentences": [], "tokens": [], "entities": []}
        
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
        
        with ThreadPoolExecutor(max_workers=4) as executor:
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
                    consistency_checker.analyze_narrative_consistency,
                    doc,
                    analysis.get("entities", [])
                )
            
            if features.get("transform"):
                futures["transform"] = executor.submit(
                    style_transformer.transform_style,
                    text,
                    self.target_style
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
        
        if features["consistency"]:
            results["consistency"] = consistency_checker.analyze_narrative_consistency(
                doc,
                analysis.get("entities", [])
            )
        
        if features.get("transform"):
            results["style_transformation"] = style_transformer.transform_style(
                text,
                self.target_style
            )
        
        # Generate improvement suggestions
        if features["readability"] and features["flow"]:
            results["suggestions"] = enhancer.get_improvement_suggestions(
                results.get("readability", {}),
                results.get("flow", {})
            )
        
        return results
    
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
        
        # Consistency score
        consistency = results.get("consistency", {})
        if consistency:
            scores["consistency"] = consistency.get("overall_consistency_score", 100)
        
        # Issues score (inverse - fewer issues = higher score)
        issues = results.get("issues", {})
        issue_count = (
            len(issues.get("long_sentences", [])) +
            len(issues.get("repeated_words", []))
        )
        scores["issues"] = max(0, 100 - (issue_count * 10))
        
        # Overall score (weighted average)
        weights = {
            "readability": 0.3,
            "flow": 0.2,
            "consistency": 0.25,
            "issues": 0.25
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
