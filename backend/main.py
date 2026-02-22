"""
Writing Assistant API
FastAPI backend server that orchestrates the NLP pipeline
"""

import sys
import os
from contextlib import asynccontextmanager
from typing import Optional, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.models import (
    AnalysisRequest,
    AnalysisResponse,
    TransformRequest,
    TransformResponse,
    ErrorResponse,
    HealthResponse,
    LLMStatusResponse,
    TargetStyle
)

# Import the NLP engine
from nlp_engine import WritingAssistant, analyze_text, NarrativeConsistencyAnalyzer

# Import LLM client
from nlp_engine.llm_client import get_client as get_llm_client, check_ollama_status

# Global instances (loaded once)
assistant: Optional[WritingAssistant] = None
consistency_analyzer: Optional[NarrativeConsistencyAnalyzer] = None
kw_model = None  # KeyBERT model (lazy loaded)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global assistant, consistency_analyzer
    print("Starting Writing Assistant API...")
    print("Loading spaCy model...")
    assistant = WritingAssistant()
    consistency_analyzer = NarrativeConsistencyAnalyzer()
    print("NLP Engine ready!")
    print("Narrative Consistency Analyzer ready!")
    yield
    print("Shutting down Writing Assistant API...")


# Create FastAPI app
app = FastAPI(
    title="Writing Assistant API",
    description="""
    A comprehensive NLP-powered writing assistant API.
    
    ## Features
    - **Text Analysis**: Tokenization, POS tagging, Named Entity Recognition
    - **Readability Scoring**: Flesch Reading Ease, Flesch-Kincaid Grade, and more
    - **Flow Analysis**: Transition words, sentence variety
    - **Style Transformation**: Convert between casual, formal, and academic styles
    - **Consistency Checking**: Entity tracking, pronoun analysis
    - **Explanations**: Human-readable feedback and suggestions
    
    ## Usage
    Send your text to the `/analyze` endpoint and receive comprehensive analysis results.
    """,
    version="1.0.0",
    lifespan=lifespan,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Writing Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "analyze": "/analyze",
            "transform": "/transform"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API health status"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        nlp_model="en_core_web_sm",
        features=[
            "text_analysis",
            "readability",
            "flow_analysis",
            "style_transformation",
            "consistency_checking",
            "explanations"
        ]
    )


@app.get("/llm/status", response_model=LLMStatusResponse, tags=["LLM"])
async def llm_status():
    """
    Check LLM (Ollama) status and availability.
    
    Returns information about:
    - Connection status to Ollama server
    - Configured model availability
    - Model details (size, parameters, quantization)
    - Response time
    
    If status is not 'ok', check the 'error' and 'hint' fields for troubleshooting.
    """
    status = check_ollama_status()
    
    # Convert model_info dict to LLMModelInfo if present
    model_info = None
    if status.get("model_info"):
        from backend.models import LLMModelInfo
        model_info = LLMModelInfo(**status["model_info"])
    
    return LLMStatusResponse(
        status=status.get("status", "error"),
        connected=status.get("connected", False),
        model=status.get("model", "llama3.1:8b"),
        model_available=status.get("model_available", False),
        model_info=model_info,
        available_models=status.get("available_models"),
        response_time_ms=status.get("response_time_ms"),
        error=status.get("error"),
        hint=status.get("hint")
    )


@app.post("/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_endpoint(request: AnalysisRequest):
    """
    Analyze text and return comprehensive writing metrics.
    
    This endpoint performs:
    - Basic text analysis (tokenization, sentences, entities)
    - Readability scoring
    - Flow analysis
    - Style detection
    - Consistency checking
    - Issue detection (long sentences, repeated words)
    - Improvement suggestions
    
    Toggle specific features using the `features` parameter.
    """
    global assistant
    
    if assistant is None:
        assistant = WritingAssistant()
    
    try:
        # Configure assistant with request parameters
        config = {
            "long_sentence_threshold": request.long_sentence_threshold,
            "repeated_word_min_count": request.repeated_word_min_count,
            "target_style": request.target_style.value if request.target_style else "formal",
            "target_tone_value": request.target_tone.value if request.target_tone else "auto"
        }
        
        # Create configured assistant
        configured_assistant = WritingAssistant(config)
        
        # Convert features to dict if provided
        features = None
        if request.features:
            features = request.features.model_dump()
        
        # Run analysis
        results = configured_assistant.analyze(request.text, features)
        
        # Clean up non-serializable objects
        if "text_analysis" in results:
            results["text_analysis"].pop("doc", None)
        
        return AnalysisResponse(
            success=True,
            input=results.get("input", {}),
            text_analysis=results.get("text_analysis"),
            readability=results.get("readability"),
            flow=results.get("flow"),
            style_analysis=results.get("style_analysis"),
            style_transformation=results.get("style_transformation"),
            consistency=results.get("consistency"),
            issues=results.get("issues"),
            suggestions=results.get("suggestions"),
            explanations=results.get("explanations"),
            scores=results.get("scores"),
            # Grammar analysis
            grammar_analysis=results.get("grammar_analysis"),
            # Tone analysis
            tone_analysis=results.get("tone_analysis"),
            # Style scores per paragraph
            style_scores=results.get("style_scores"),
            # New enhanced features
            passive_voice=results.get("passive_voice"),
            sentiment=results.get("sentiment"),
            vocabulary_complexity=results.get("vocabulary_complexity"),
            filler_words=results.get("filler_words"),
            cliches=results.get("cliches"),
            paragraph_structure=results.get("paragraph_structure"),
            lexical_density=results.get("lexical_density"),
            sentence_rhythm=results.get("sentence_rhythm"),
            # Narrative tracker (Phase 5)
            narrative_tracker=results.get("narrative_tracker"),
            # Inline annotations (Phase 6)
            annotations=results.get("annotations"),
            # Mind map (Phase 7)
            mind_map=results.get("mind_map"),
            # Anti-patterns (Phase 8)
            antipatterns=results.get("antipatterns"),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/transform", response_model=TransformResponse, tags=["Transformation"])
async def transform_endpoint(request: TransformRequest):
    """
    Transform text to a different writing style.
    
    Available styles:
    - **formal**: Expand contractions, use formal vocabulary
    - **casual**: Use contractions, informal vocabulary
    - **academic**: Formal style with academic conventions
    
    Returns the original text, transformed text, and a list of all changes made.
    """
    global assistant
    
    if assistant is None:
        assistant = WritingAssistant()
    
    try:
        result = assistant.transform(request.text, request.target_style.value)
        
        return TransformResponse(
            success=True,
            original=result["original"],
            transformed=result["transformed"],
            changes=result["changes"],
            change_count=result["change_count"],
            target_style=result["style"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transformation failed: {str(e)}"
        )


@app.get("/analyze/quick", tags=["Analysis"])
async def quick_analyze(
    text: str = Query(..., min_length=1, max_length=10000, description="Text to analyze"),
    style: Optional[TargetStyle] = Query(default=None, description="Target style for transformation")
):
    """
    Quick analysis endpoint using query parameters.
    
    For simple use cases where you want to analyze text via GET request.
    Limited to 10,000 characters.
    """
    global assistant
    
    if assistant is None:
        assistant = WritingAssistant()
    
    try:
        features = {"transform": style is not None}
        
        if style:
            config_assistant = WritingAssistant({"target_style": style.value})
            results = config_assistant.analyze(text, features)
        else:
            results = assistant.analyze(text, features)
        
        # Clean up and return simplified response
        if "text_analysis" in results:
            results["text_analysis"].pop("doc", None)
        
        return {
            "success": True,
            "scores": results.get("scores", {}),
            "issues_count": {
                "long_sentences": len(results.get("issues", {}).get("long_sentences", [])),
                "repeated_words": len(results.get("issues", {}).get("repeated_words", []))
            },
            "style": results.get("style_analysis", {}).get("dominant_style"),
            "readability_grade": results.get("readability", {}).get("grade_level"),
            "suggestions_count": len(results.get("suggestions", []))
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Quick analysis failed: {str(e)}"
        )


@app.post("/analyze/consistency", tags=["Analysis"])
async def analyze_consistency_endpoint(request: AnalysisRequest):
    """
    Analyze text for narrative consistency issues.
    
    Detects:
    - Same character referenced with different names
    - Pronoun confusion
    - Sudden new entities without introduction
    - Entity type conflicts
    
    Returns a list of issues with suggestions and explanations.
    """
    global consistency_analyzer
    
    if consistency_analyzer is None:
        consistency_analyzer = NarrativeConsistencyAnalyzer()
    
    try:
        # Run narrative consistency analysis
        issues = consistency_analyzer.analyze_consistency(request.text)
        summary = consistency_analyzer.get_analysis_summary(request.text)
        character_memory = consistency_analyzer.get_character_memory()
        
        return {
            "success": True,
            "issues": issues,
            "total_issues": summary["total_issues"],
            "issue_breakdown": summary["issue_breakdown"],
            "characters_tracked": summary["characters_tracked"],
            "consistency_score": summary["consistency_score"],
            "character_memory": {
                name: {
                    "canonical_name": data["canonical_name"],
                    "type": data["type"],
                    "mention_count": len(data["mentions"])
                }
                for name, data in character_memory.items()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Consistency analysis failed: {str(e)}"
        )


# ── MindElixir Mind Map Endpoint ────────────────────────────────────────────

class MindMapRequest(BaseModel):
    text: str
    title: Optional[str] = None
    top_n: int = 8


@app.post("/mindmap", tags=["Mind Map"])
async def create_mindmap(req: MindMapRequest):
    """
    Generate a hierarchical mind map from text using KeyBERT keywords.
    
    Returns data in a format suitable for MindElixir visualization:
    - topic: Root topic (title or first line of text)
    - children: Keyword nodes, each with related sentence children
    - entities: Named entities found in text
    - meta: Keywords and other metadata
    """
    global kw_model, assistant
    
    if assistant is None:
        assistant = WritingAssistant()
    
    text = req.text or ''
    title = req.title or (text.strip().split('\n')[0][:80] if text else 'Document')
    
    # Get spaCy doc for NER and sentences
    doc = assistant.nlp(text)
    sentences = [s.text.strip() for s in doc.sents if s.text.strip()]
    entities = list({ent.text for ent in doc.ents})
    
    # Extract keywords using KeyBERT (with fallback)
    keywords = []
    try:
        # Lazy load KeyBERT
        if kw_model is None:
            from keybert import KeyBERT
            kw_model = KeyBERT()
        
        kw_results = kw_model.extract_keywords(
            text, 
            keyphrase_ngram_range=(1, 2), 
            stop_words='english', 
            top_n=req.top_n
        )
        keywords = [k for k, score in kw_results]
    except Exception as e:
        # Fallback: simple frequency-based keywords
        print(f"KeyBERT fallback due to: {e}")
        words = [w.text.lower() for w in doc if w.is_alpha and not w.is_stop]
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        keywords = sorted(freq.keys(), key=lambda k: -freq[k])[:req.top_n]
    
    # Build hierarchical JSON: root -> keywords -> related sentences
    children = []
    used_sentences = set()
    
    for kw in keywords:
        related = []
        for s in sentences:
            if s in used_sentences:
                continue
            if kw.lower() in s.lower():
                related.append({"topic": s})
                used_sentences.add(s)
        
        # If no direct match, try token overlap
        if not related:
            for s in sentences:
                if s in used_sentences:
                    continue
                s_tokens = set([t.lemma_.lower() for t in assistant.nlp(s) if t.is_alpha])
                kw_tokens = set([t.lemma_.lower() for t in assistant.nlp(kw) if t.is_alpha])
                if kw_tokens and len(s_tokens & kw_tokens) > 0:
                    related.append({"topic": s})
                    used_sentences.add(s)
        
        if related:
            children.append({"topic": kw, "children": related})
    
    # Remaining sentences under Misc
    leftovers = [{"topic": s} for s in sentences if s not in used_sentences]
    if leftovers:
        children.append({"topic": "Misc", "children": leftovers})
    
    return {
        "topic": title,
        "children": children,
        "entities": entities,
        "meta": {"keywords": keywords}
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
