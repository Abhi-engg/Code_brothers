"""
Pydantic Models for API Request/Response validation
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from enum import Enum


class TargetStyle(str, Enum):
    """Available style transformation targets"""
    FORMAL = "formal"
    CASUAL = "casual"
    ACADEMIC = "academic"
    CREATIVE = "creative"
    PERSUASIVE = "persuasive"
    JOURNALISTIC = "journalistic"
    NARRATIVE = "narrative"


class ToneType(str, Enum):
    """Available tone types for analysis and transformation"""
    AUTO = "auto"
    ASSERTIVE = "assertive"
    EMPATHETIC = "empathetic"
    PERSUASIVE = "persuasive"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    URGENT = "urgent"
    NARRATIVE = "narrative"


class FeatureToggles(BaseModel):
    """Feature toggles for analysis"""
    text_analysis: bool = Field(default=True, description="Enable basic text analysis (tokens, sentences, entities)")
    readability: bool = Field(default=True, description="Enable readability scoring")
    flow: bool = Field(default=True, description="Enable flow analysis")
    style: bool = Field(default=True, description="Enable style analysis")
    consistency: bool = Field(default=True, description="Enable consistency checking")
    grammar: bool = Field(default=True, description="Enable grammar checking")
    transform: bool = Field(default=False, description="Enable style transformation")
    explanations: bool = Field(default=True, description="Generate explanations")


class AnalysisRequest(BaseModel):
    """Request model for text analysis"""
    text: str = Field(..., min_length=1, max_length=50000, description="Text to analyze")
    features: Optional[FeatureToggles] = Field(default=None, description="Feature toggles")
    target_style: Optional[TargetStyle] = Field(default=TargetStyle.FORMAL, description="Target style for transformation")
    target_tone: Optional[ToneType] = Field(default=ToneType.AUTO, description="Target tone for tone transformation")
    long_sentence_threshold: Optional[int] = Field(default=25, ge=10, le=200, description="Word count threshold for long sentences")
    repeated_word_min_count: Optional[int] = Field(default=3, ge=2, le=10, description="Minimum count for repeated word detection")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "This is a sample text. It's gonna be analyzed for various writing metrics.",
                "features": {
                    "text_analysis": True,
                    "readability": True,
                    "flow": True,
                    "style": True,
                    "consistency": True,
                    "transform": False,
                    "explanations": True
                },
                "target_style": "formal",
                "long_sentence_threshold": 25,
                "repeated_word_min_count": 3
            }
        }


class TransformRequest(BaseModel):
    """Request model for style transformation"""
    text: str = Field(..., min_length=1, max_length=50000, description="Text to transform")
    target_style: TargetStyle = Field(default=TargetStyle.FORMAL, description="Target style")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hey, I'm gonna tell you about this awesome project we've been working on.",
                "target_style": "formal"
            }
        }


class ScoreDetail(BaseModel):
    """Individual score detail"""
    value: float
    interpretation: Optional[str] = None


class AnalysisScores(BaseModel):
    """Analysis scores"""
    readability: Optional[float] = Field(None, ge=0, le=100)
    flow: Optional[float] = Field(None, ge=0, le=100)
    consistency: Optional[float] = Field(None, ge=0, le=100)
    issues: Optional[float] = Field(None, ge=0, le=100)
    overall: Optional[float] = Field(None, ge=0, le=100)


class Issue(BaseModel):
    """Detected issue"""
    type: str
    severity: str
    location: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None


class Suggestion(BaseModel):
    """Improvement suggestion"""
    category: str
    priority: str
    action: str
    impact: Optional[str] = None
    how_to: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Response model for text analysis"""
    success: bool = True
    input: Dict[str, Any]
    text_analysis: Optional[Dict[str, Any]] = None
    readability: Optional[Dict[str, Any]] = None
    flow: Optional[Dict[str, Any]] = None
    style_analysis: Optional[Dict[str, Any]] = None
    style_transformation: Optional[Dict[str, Any]] = None
    consistency: Optional[Dict[str, Any]] = None
    issues: Optional[Dict[str, List[Any]]] = None
    suggestions: Optional[List[Dict[str, Any]]] = None
    explanations: Optional[Dict[str, Any]] = None
    scores: Optional[AnalysisScores] = None
    # Grammar analysis
    grammar_analysis: Optional[Dict[str, Any]] = None
    # Tone analysis
    tone_analysis: Optional[Dict[str, Any]] = None
    # Style scores per paragraph
    style_scores: Optional[List[Dict[str, Any]]] = None
    # New enhanced features
    passive_voice: Optional[Dict[str, Any]] = None
    sentiment: Optional[Dict[str, Any]] = None
    vocabulary_complexity: Optional[Dict[str, Any]] = None
    filler_words: Optional[Dict[str, Any]] = None
    cliches: Optional[Dict[str, Any]] = None
    paragraph_structure: Optional[Dict[str, Any]] = None
    lexical_density: Optional[Dict[str, Any]] = None
    sentence_rhythm: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "input": {"text": "Sample text...", "character_count": 15},
                "scores": {
                    "readability": 65.5,
                    "flow": 72.0,
                    "consistency": 90.0,
                    "issues": 80.0,
                    "overall": 76.8
                }
            }
        }


class TransformResponse(BaseModel):
    """Response model for style transformation"""
    success: bool = True
    original: str
    transformed: str
    changes: List[Dict[str, Any]]
    change_count: int
    target_style: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "original": "I'm gonna do this.",
                "transformed": "I am going to do this.",
                "changes": [
                    {"type": "contraction", "original": "I'm", "replacement": "I am"},
                    {"type": "word_replacement", "original": "gonna", "replacement": "going to"}
                ],
                "change_count": 2,
                "target_style": "formal"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Analysis failed",
                "detail": "Text is empty or invalid"
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str
    nlp_model: str
    features: List[str]
