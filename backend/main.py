"""
Writing Assistant API
FastAPI backend server that orchestrates the NLP pipeline
"""

import sys
import os
from contextlib import asynccontextmanager
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import (
    AnalysisRequest,
    AnalysisResponse,
    TransformRequest,
    TransformResponse,
    ErrorResponse,
    HealthResponse,
    TargetStyle
)

# Import the NLP engine
from nlp_engine import WritingAssistant, analyze_text

# Global assistant instance (loaded once)
assistant: Optional[WritingAssistant] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global assistant
    print("🚀 Starting Writing Assistant API...")
    print("📚 Loading spaCy model...")
    assistant = WritingAssistant()
    print("✅ NLP Engine ready!")
    yield
    print("👋 Shutting down Writing Assistant API...")


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
            "target_style": request.target_style.value if request.target_style else "formal"
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
            scores=results.get("scores")
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
