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
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.models import (
    AnalysisRequest,
    AnalysisResponse,
    TransformRequest,
    TransformResponse,
    ErrorResponse,
    HealthResponse,
    LLMStatusResponse,
    TargetStyle,
    RewriteRequest,
    RewriteResponse,
    BatchRewriteRequest,
    BatchRewriteResponse,
    StyleTransformRequest,
    StyleTransformResponse,
    # Story continuation models (Phase 4)
    StoryAnalyzeRequest,
    StoryAnalyzeResponse,
    CharacterInfo,
    StoryContinueRequest,
    StoryContinueResponse,
    ContextInfo,
    StoryContinueOptionsRequest,
    StoryContinueOptionsResponse,
    ContinuationOptionInfo
)

# Import the NLP engine
from nlp_engine import WritingAssistant, analyze_text, NarrativeConsistencyAnalyzer

# Import LLM client and enhancer
from nlp_engine.llm_client import get_client as get_llm_client, check_ollama_status
from nlp_engine.llm_enhancer import get_enhancer as get_llm_enhancer

# Import story assistant (Phase 4)
from nlp_engine.story_assistant import get_story_assistant, analyze_story as analyze_story_context

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


class AIMindMapRequest(BaseModel):
    """Request model for AI-powered mind map generation"""
    text: str
    title: Optional[str] = None
    max_concepts: int = 8


@app.post("/mindmap/ai", tags=["Mind Map"])
async def create_ai_mindmap(req: AIMindMapRequest):
    """
    Generate a semantic mind map using LLM for concept extraction.
    
    Returns hierarchical data optimized for animated flowchart visualization:
    - nodes: List of nodes with id, label, type, color
    - edges: List of edges connecting nodes
    - root: Root node information
    
    This uses the LLM to understand relationships between concepts,
    providing deeper semantic understanding than keyword extraction.
    """
    from nlp_engine.llm_client import get_client as get_llm_client
    import time
    
    text = req.text or ''
    title = req.title or (text.strip().split('\n')[0][:60] if text else 'Document')
    start_time = time.time()
    
    # Prompt LLM for concept extraction
    prompt = f"""Analyze this text and extract concepts for a mind map.

TEXT:
{text[:2000]}

Respond with EXACTLY this format (no extra text):
THEME: [main theme, 3-5 words]
CATEGORY1: [category name]
- [concept 1]
- [concept 2]
- [concept 3]
CATEGORY2: [category name]
- [concept 1]
- [concept 2]
CATEGORY3: [category name]
- [concept 1]
- [concept 2]

Example:
THEME: Fantasy Adventure Quest
CATEGORY1: Characters
- Old Wizard
- Village People
- Ancient Dragon
CATEGORY2: Locations
- Misty Mountains
- Dragon Lair
- Village
CATEGORY3: Plot Elements
- Treasure Hunt
- Fear of Beast"""

    try:
        llm_client = get_llm_client()
        result = llm_client.generate(prompt, max_tokens=500)
        
        if not result.success:
            raise Exception(result.error or "LLM generation failed")
        
        # Parse the response text
        lines = result.text.strip().split('\n')
        main_theme = title
        concept_map = {}
        current_category = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse theme
            if line.upper().startswith('THEME:'):
                main_theme = line.split(':', 1)[1].strip()[:60]
            # Parse category headers
            elif line.upper().startswith('CATEGORY') and ':' in line:
                cat_name = line.split(':', 1)[1].strip()
                if cat_name:
                    current_category = cat_name
                    concept_map[current_category] = []
            # Parse concepts (lines starting with -)
            elif line.startswith('-') and current_category:
                concept = line[1:].strip()
                if concept and len(concept_map[current_category]) < 4:
                    concept_map[current_category].append(concept)
        
        # Build vis-network compatible nodes and edges
        nodes = []
        edges = []
        node_id = 0
        
        # Root node (main theme)
        root_id = node_id
        nodes.append({
            "id": node_id,
            "label": main_theme,
            "type": "root",
            "level": 0,
            "color": {"background": "#8B5CF6", "border": "#7C3AED"},
            "size": 35,
            "font_size": 16
        })
        node_id += 1
        
        # Category nodes
        category_colors = [
            {"background": "#EC4899", "border": "#DB2777"},
            {"background": "#F59E0B", "border": "#D97706"},
            {"background": "#10B981", "border": "#059669"},
            {"background": "#3B82F6", "border": "#2563EB"},
            {"background": "#6366F1", "border": "#4F46E5"},
        ]
        
        category_ids = {}
        for idx, cat in enumerate(concept_map.keys()):
            cat_id = node_id
            category_ids[cat] = cat_id
            color = category_colors[idx % len(category_colors)]
            nodes.append({
                "id": cat_id,
                "label": cat,
                "type": "category",
                "level": 1,
                "color": color,
                "size": 28,
                "font_size": 13
            })
            edges.append({
                "from": root_id,
                "to": cat_id,
                "label": "",
                "width": 3,
                "dashes": False
            })
            node_id += 1
        
        # Concept nodes
        concept_color = {"background": "#22C55E", "border": "#16A34A"}
        for cat, concepts in concept_map.items():
            cat_id = category_ids.get(cat)
            if cat_id is None:
                continue
            for concept in concepts:
                nodes.append({
                    "id": node_id,
                    "label": concept,
                    "type": "concept",
                    "level": 2,
                    "color": concept_color,
                    "size": 20,
                    "font_size": 11
                })
                edges.append({
                    "from": cat_id,
                    "to": node_id,
                    "label": "",
                    "width": 2,
                    "dashes": False
                })
                node_id += 1
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "nodes": nodes,
            "edges": edges,
            "root": {"id": root_id, "label": main_theme},
            "meta": {
                "categories": list(concept_map.keys()),
                "total_concepts": sum(len(c) for c in concept_map.values()),
                "generation_time_ms": elapsed_ms,
                "mode": "ai"
            }
        }
        
    except Exception as e:
        # Fallback to simple extraction
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "success": False,
            "nodes": [{"id": 0, "label": title, "type": "root", "level": 0, "color": {"background": "#8B5CF6", "border": "#7C3AED"}, "size": 35, "font_size": 16}],
            "edges": [],
            "root": {"id": 0, "label": title},
            "meta": {
                "categories": [],
                "total_concepts": 0,
                "generation_time_ms": elapsed_ms,
                "mode": "ai",
                "error": str(e)
            }
        }


# ==================== LLM Enhancement Endpoints ====================

@app.post("/enhance/rewrite", response_model=RewriteResponse, tags=["LLM Enhancement"])
async def enhance_rewrite(request: RewriteRequest):
    """
    Generate an LLM-enhanced rewrite for a writing issue.
    
    This endpoint uses the local LLM (Ollama) to generate intelligent
    rewrite suggestions for various writing issues like:
    - Passive voice → Active voice
    - Show don't tell → Descriptive writing
    - Wordy sentences → Concise versions
    - And more...
    
    The core detection logic is rule-based (custom-built).
    The LLM is used only for natural language generation of suggestions.
    """
    try:
        enhancer = get_llm_enhancer()
        result = await enhancer.generate_rewrite_async(
            text=request.text,
            issue_type=request.issue_type.value,
            context=request.context or "",
            word=request.word or ""
        )
        
        return RewriteResponse(
            success=result.success,
            original=result.original,
            suggestion=result.suggestion,
            explanation=result.explanation,
            issue_type=result.issue_type,
            confidence=result.confidence,
            generation_time_ms=result.generation_time_ms,
            error=result.error
        )
        
    except Exception as e:
        return RewriteResponse(
            success=False,
            original=request.text,
            suggestion="",
            explanation="",
            issue_type=request.issue_type.value,
            confidence=0.0,
            error=str(e)
        )


@app.post("/enhance/batch", response_model=BatchRewriteResponse, tags=["LLM Enhancement"])
async def enhance_batch(request: BatchRewriteRequest):
    """
    Generate LLM-enhanced rewrites for multiple issues in a single call.
    
    More efficient than calling /enhance/rewrite multiple times.
    Maximum 5 issues per batch.
    """
    import time
    start_time = time.time()
    
    try:
        enhancer = get_llm_enhancer()
        results = enhancer.generate_batch_rewrites(request.issues)
        
        response_results = [
            RewriteResponse(
                success=r.success,
                original=r.original,
                suggestion=r.suggestion,
                explanation=r.explanation,
                issue_type=r.issue_type,
                confidence=r.confidence,
                generation_time_ms=r.generation_time_ms,
                error=r.error
            )
            for r in results
        ]
        
        total_time = (time.time() - start_time) * 1000
        
        return BatchRewriteResponse(
            success=True,
            results=response_results,
            total_time_ms=total_time
        )
        
    except Exception as e:
        return BatchRewriteResponse(
            success=False,
            results=[],
            total_time_ms=0.0
        )


@app.post("/transform/style", response_model=StyleTransformResponse, tags=["LLM Enhancement"])
async def transform_style_endpoint(request: StyleTransformRequest):
    """
    Transform text to a different writing style.
    
    Two modes available:
    - **quick**: Rule-based transformation (instant, deterministic)
    - **deep**: LLM-powered transformation (2-5s, more natural)
    
    Available styles:
    - formal: Professional, business-appropriate language
    - casual: Conversational, friendly tone
    - academic: Scholarly, objective, hedged language
    - creative: Vivid, artistic expression
    - persuasive: Compelling, motivating language
    - journalistic: Objective, concise reporting
    - narrative: Storytelling prose
    
    The core style detection logic is custom-built.
    LLM is used only for natural sentence generation in deep mode.
    """
    import time
    start_time = time.time()
    
    try:
        if request.mode.value == "quick":
            # Use rule-based transformer
            from nlp_engine.style_transformer import transform_style
            result = transform_style(request.text, request.target_style.value)
            
            total_time = (time.time() - start_time) * 1000
            
            return StyleTransformResponse(
                success=True,
                original=result.get("original", request.text),
                transformed=result.get("transformed", ""),
                source_style=request.source_style or "auto",
                target_style=request.target_style.value,
                mode="quick",
                changes_summary=f"{result.get('change_count', 0)} rule-based changes applied",
                confidence=0.9 if result.get("transformed") else 0.5,
                generation_time_ms=total_time,
                error=result.get("error")
            )
        else:
            # Use LLM-powered deep transform
            enhancer = get_llm_enhancer()
            result = await enhancer.transform_style_async(
                text=request.text,
                target_style=request.target_style.value,
                source_style=request.source_style or "auto"
            )
            
            return StyleTransformResponse(
                success=result.success,
                original=result.original,
                transformed=result.transformed,
                source_style=result.source_style,
                target_style=result.target_style,
                mode="deep",
                changes_summary=result.changes_summary,
                confidence=result.confidence,
                generation_time_ms=result.generation_time_ms,
                error=result.error
            )
            
    except Exception as e:
        return StyleTransformResponse(
            success=False,
            original=request.text,
            transformed="",
            source_style=request.source_style or "auto",
            target_style=request.target_style.value,
            mode=request.mode.value,
            changes_summary="",
            confidence=0.0,
            error=str(e)
        )


# ==================== Story Continuation Endpoints (Phase 4) ====================

@app.post("/story/analyze", response_model=StoryAnalyzeResponse, tags=["Story Continuation"])
async def analyze_story_endpoint(request: StoryAnalyzeRequest):
    """
    Analyze story text to extract narrative context.
    
    Extracts:
    - Point of view (first person, third person, etc.)
    - Tense (past, present, mixed)
    - Tone (serious, humorous, suspenseful, etc.)
    - Genre hints
    - Characters and their mentions
    - Themes
    - Setting description
    - Recent events
    
    This analysis is used by the continuation endpoint to maintain consistency.
    All extraction logic is custom-built using pattern matching and NLP.
    """
    try:
        result = analyze_story_context(request.text)
        
        return StoryAnalyzeResponse(
            success=True,
            pov=result["pov"],
            tense=result["tense"],
            tone=result["tone"],
            genre_hint=result["genre_hint"],
            characters=[
                CharacterInfo(
                    name=c["name"],
                    mentions=c["mentions"],
                    is_protagonist=c["is_protagonist"]
                )
                for c in result["characters"]
            ],
            themes=result["themes"],
            setting=result["setting"],
            recent_events=result["recent_events"],
            word_count=result["word_count"],
            plot_element_count=result["plot_element_count"]
        )
        
    except Exception as e:
        return StoryAnalyzeResponse(
            success=False,
            pov="unknown",
            tense="unknown",
            tone="unknown",
            genre_hint="unknown",
            error=str(e)
        )


@app.post("/story/continue", tags=["Story Continuation"])
async def continue_story_endpoint(request: StoryContinueRequest):
    """
    Continue a story using LLM.
    
    Two modes:
    - **Non-streaming** (stream=false): Returns complete continuation
    - **Streaming** (stream=true): Returns Server-Sent Events (SSE) stream
    
    The endpoint:
    1. Analyzes the story context (POV, tense, tone, characters)
    2. Builds a custom prompt with all context
    3. Generates continuation matching the original style
    
    For SSE streaming, connect with EventSource and handle 'token' events.
    
    Custom-built components:
    - Context extraction and analysis
    - Prompt engineering for style matching
    - Response cleaning and validation
    
    External: Ollama LLM for text generation only.
    """
    import time
    import json
    
    if request.stream:
        # SSE Streaming response
        async def generate_sse():
            """Generate SSE events for streaming continuation"""
            start_time = time.time()
            tokens_generated = 0
            full_text = ""
            
            try:
                story_assistant = get_story_assistant()
                context = story_assistant.analyze_story(request.text)
                
                # Send initial context event
                context_data = {
                    "pov": context.pov.value,
                    "tense": context.tense.value,
                    "tone": context.tone.value,
                    "characters": [c.name for c in context.characters[:5]]
                }
                yield f"event: context\ndata: {json.dumps(context_data)}\n\n"
                
                # Stream tokens
                async for token in story_assistant.continue_story_stream_async(
                    text=request.text,
                    word_target=request.word_target,
                    custom_instruction=request.custom_instruction,
                    context=context,
                    temperature=request.temperature
                ):
                    tokens_generated += 1
                    full_text += token
                    yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
                
                # Send completion event
                elapsed_ms = (time.time() - start_time) * 1000
                completion_data = {
                    "success": True,
                    "generation_time_ms": elapsed_ms,
                    "tokens_generated": tokens_generated,
                    "full_text": full_text
                }
                yield f"event: done\ndata: {json.dumps(completion_data)}\n\n"
                
            except Exception as e:
                error_data = {"success": False, "error": str(e)}
                yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate_sse(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    else:
        # Non-streaming response
        start_time = time.time()
        
        try:
            story_assistant = get_story_assistant()
            result = await story_assistant.continue_story_async(
                text=request.text,
                word_target=request.word_target,
                custom_instruction=request.custom_instruction,
                temperature=request.temperature
            )
            
            return StoryContinueResponse(
                success=result.success,
                continuation=result.continuation,
                context=ContextInfo(
                    characters=result.context_used.get("characters", []),
                    setting=result.context_used.get("setting", ""),
                    themes=result.context_used.get("themes", []),
                    genre=result.context_used.get("genre", "")
                ),
                pov=result.pov,
                tense=result.tense,
                tone=result.tone,
                generation_time_ms=result.generation_time_ms,
                tokens_generated=result.tokens_generated,
                error=result.error
            )
            
        except Exception as e:
            return StoryContinueResponse(
                success=False,
                continuation="",
                context=ContextInfo(),
                pov="unknown",
                tense="unknown",
                tone="unknown",
                generation_time_ms=(time.time() - start_time) * 1000,
                tokens_generated=0,
                error=str(e)
            )


@app.post("/story/options", response_model=StoryContinueOptionsResponse, tags=["Story Continuation"])
async def continue_story_options_endpoint(request: StoryContinueOptionsRequest):
    """
    Generate multiple continuation options for user to choose from.
    
    Options typically include different directions:
    1. **Action/plot advancement** - Move the story forward
    2. **Character development/dialogue** - Deepen character interactions
    3. **Atmospheric/descriptive** - Build mood and setting
    4. **Plot twist** (if 4 options requested) - Unexpected development
    
    This gives writers creative choices while maintaining story consistency.
    
    Custom-built: Option categorization and prompt assembly.
    External: Ollama LLM for generation.
    """
    import time
    start_time = time.time()
    
    try:
        story_assistant = get_story_assistant()
        context = story_assistant.analyze_story(request.text)
        options = story_assistant.generate_continuation_options(
            text=request.text,
            num_options=request.num_options,
            context=context
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return StoryContinueOptionsResponse(
            success=len(options) > 0,
            options=[
                ContinuationOptionInfo(
                    text=opt.text,
                    direction=opt.direction,
                    confidence=opt.confidence
                )
                for opt in options
            ],
            context=ContextInfo(
                characters=[c.name for c in context.characters[:5]],
                setting=context.setting_description,
                themes=context.themes,
                genre=context.genre_hint.value
            ),
            generation_time_ms=elapsed_ms,
            error=None if options else "Failed to generate options"
        )
        
    except Exception as e:
        return StoryContinueOptionsResponse(
            success=False,
            options=[],
            context=ContextInfo(),
            generation_time_ms=(time.time() - start_time) * 1000,
            error=str(e)
        )


# ==================== AI Improvement Endpoint ====================

from backend.models import AIImproveRequest, AIImproveResponse, AIImprovementSuggestion

@app.post("/improve/ai", response_model=AIImproveResponse, tags=["LLM Enhancement"])
async def ai_improve_text(request: AIImproveRequest):
    """
    Get AI-powered improvement suggestions for text.
    
    Uses the local LLM (Ollama + llama3.2:3b) to analyze text and provide
    actionable improvement suggestions across multiple categories:
    - **clarity**: Make meaning clearer
    - **conciseness**: Remove unnecessary words
    - **engagement**: Make text more compelling
    - **flow**: Improve sentence transitions
    - **word_choice**: Suggest better vocabulary
    
    The AI analyzes the text holistically and provides specific,
    sentence-level suggestions with explanations.
    """
    import time
    start_time = time.time()
    
    try:
        # Check LLM availability
        llm_client = get_llm_client()
        if not llm_client:
            return AIImproveResponse(
                success=False,
                suggestions=[],
                overall_score=0,
                summary="",
                generation_time_ms=0,
                error="LLM not available. Please ensure Ollama is running."
            )
        
        # Build the prompt for improvement analysis
        focus = request.focus_areas or ["clarity", "conciseness", "engagement", "flow", "word_choice"]
        focus_str = ", ".join(focus)
        
        prompt = f"""Analyze this text and provide specific improvement suggestions.

TEXT:
\"\"\"
{request.text}
\"\"\"

Focus areas: {focus_str}

Provide 3-6 specific, actionable suggestions. For each suggestion use this EXACT format:

SUGGESTION:
CATEGORY: [one of: clarity, conciseness, engagement, flow, word_choice]
PRIORITY: [high, medium, or low]
ISSUE: [describe the specific issue in 1 sentence]
ORIGINAL: [exact text that needs improvement]
IMPROVED: [your improved version]
EXPLANATION: [why this improvement helps, 1-2 sentences]

Also provide:
OVERALL_SCORE: [0-100 quality score]
SUMMARY: [2-3 sentence summary of main improvements needed]

Be specific and provide actual text improvements, not general advice."""
        
        # Generate with LLM
        result = llm_client.generate(prompt, max_tokens=2000)
        response_text = result.text.strip() if hasattr(result, 'text') else str(result).strip()
        
        # Parse the response
        suggestions = []
        overall_score = 70
        summary = ""
        
        # Parse suggestions
        suggestion_blocks = response_text.split("SUGGESTION:")[1:] if "SUGGESTION:" in response_text else []
        
        for block in suggestion_blocks:
            try:
                lines = block.strip().split("\n")
                data = {}
                current_key = None
                
                for line in lines:
                    line = line.strip()
                    if line.startswith("CATEGORY:"):
                        data["category"] = line.replace("CATEGORY:", "").strip().lower()
                    elif line.startswith("PRIORITY:"):
                        data["priority"] = line.replace("PRIORITY:", "").strip().lower()
                    elif line.startswith("ISSUE:"):
                        data["issue"] = line.replace("ISSUE:", "").strip()
                    elif line.startswith("ORIGINAL:"):
                        data["original"] = line.replace("ORIGINAL:", "").strip()
                    elif line.startswith("IMPROVED:"):
                        data["suggestion"] = line.replace("IMPROVED:", "").strip()
                    elif line.startswith("EXPLANATION:"):
                        data["explanation"] = line.replace("EXPLANATION:", "").strip()
                
                if all(k in data for k in ["category", "issue", "original", "suggestion", "explanation"]):
                    suggestions.append(AIImprovementSuggestion(
                        category=data.get("category", "clarity"),
                        issue=data.get("issue", ""),
                        original=data.get("original", ""),
                        suggestion=data.get("suggestion", ""),
                        explanation=data.get("explanation", ""),
                        priority=data.get("priority", "medium")
                    ))
            except Exception:
                continue
        
        # Parse overall score
        if "OVERALL_SCORE:" in response_text:
            try:
                score_line = response_text.split("OVERALL_SCORE:")[1].split("\n")[0]
                overall_score = int(''.join(filter(str.isdigit, score_line[:5])))
                overall_score = max(0, min(100, overall_score))
            except:
                pass
        
        # Parse summary
        if "SUMMARY:" in response_text:
            try:
                summary = response_text.split("SUMMARY:")[1].split("\n\n")[0].strip()
            except:
                pass
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return AIImproveResponse(
            success=len(suggestions) > 0,
            suggestions=suggestions,
            overall_score=overall_score,
            summary=summary or f"Found {len(suggestions)} areas for improvement.",
            generation_time_ms=elapsed_ms,
            error=None if suggestions else "No suggestions generated"
        )
        
    except Exception as e:
        return AIImproveResponse(
            success=False,
            suggestions=[],
            overall_score=0,
            summary="",
            generation_time_ms=(time.time() - start_time) * 1000,
            error=str(e)
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
