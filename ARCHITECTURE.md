# WriteCraft — Complete System Architecture & Module Documentation

> A comprehensive technical guide to the WriteCraft AI-powered writing assistant system design, workflow, and modules.

---

## 🏗️ System Overview

WriteCraft is a **full-stack AI-powered writing assistant** that analyzes, enhances, and generates content using a layered architecture:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vanilla JS)                       │
│  index.html + app.js + styles.css — NotebookLM-inspired 7-tab UI   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ HTTP REST API
┌─────────────────────────────────▼───────────────────────────────────┐
│                    BACKEND (FastAPI + Uvicorn)                      │
│         main.py — API routing, CORS, request orchestration          │
│         models.py — Pydantic schemas for validation                 │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ Python imports
┌─────────────────────────────────▼───────────────────────────────────┐
│                      NLP ENGINE (Python Modules)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │ pipeline.py  │──│ text_analyzer│──│ Grammar, Style, Flow     │   │
│  │ Orchestrator │  │    spaCy     │  │ Readability, Consistency │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │        LLM Layer — llm_client.py + llm_enhancer.py           │   │
│  │              story_assistant.py (AI continuation)             │   │
│  └─────────────────────────┬────────────────────────────────────┘   │
└────────────────────────────┼────────────────────────────────────────┘
                             │ HTTP API
┌────────────────────────────▼────────────────────────────────────────┐
│                      OLLAMA LLM SERVER                              │
│              Local AI model (llama3.2:3b)                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
WriteCraft/
├── frontend/                    # Client-side UI
│   ├── index.html              # Two-panel layout, 7 writer-centric tabs
│   ├── styles.css              # CSS custom properties, responsive design
│   ├── app.js                  # Tab renderers, vis.js mind map, annotation engine
│   ├── writer_studio.html      # Standalone LLM tools demo page
│   └── test_llm.html           # LLM feature testing page
│
├── backend/                     # FastAPI REST API
│   ├── main.py                 # /analyze, /transform, /health, /story/* endpoints
│   └── models.py               # Pydantic response schemas
│
├── nlp_engine/                  # Python NLP pipeline
│   ├── __init__.py             # Module exports
│   ├── pipeline.py             # Main orchestrator (WritingAssistant class)
│   ├── text_analyzer.py        # spaCy sentence/token/entity extraction
│   ├── enhancer.py             # Readability, flow, vocabulary analysis
│   ├── style_transformer.py    # Style & tone transformation
│   ├── consistency_checker.py  # Narrative consistency tracking
│   ├── grammar_checker.py      # Spelling, grammar, tense, punctuation
│   ├── explanation.py          # Writer-friendly explanation generator
│   ├── concept_extractor.py    # Mind map graph builder
│   ├── antipatterns.py         # 8-category anti-pattern detector
│   ├── llm_client.py           # Ollama LLM wrapper
│   ├── llm_enhancer.py         # LLM-powered text enhancement
│   └── story_assistant.py      # AI story continuation service
│
├── requirements.txt             # Python dependencies
├── README.md                    # Quick start guide
└── ARCHITECTURE.md              # This file
```

---

## 🔄 Request Workflow

### **1. User Interaction Flow**

```
User types text → Frontend app.js captures input
         ↓
Click "Analyze" → POST /analyze with text + feature flags
         ↓
Backend main.py → Loads WritingAssistant from pipeline.py
         ↓
Pipeline orchestrates all NLP modules in parallel
         ↓
Results returned as JSON → Frontend renders in 7 tabs
```

### **2. LLM Enhancement Flow**

```
User clicks "Continue Story" → Frontend calls /story/continue
         ↓
Backend → story_assistant.py extracts context:
  - POV detection (1st/3rd person)
  - Tense detection (past/present)
  - Character extraction
  - Tone/genre analysis
         ↓
Builds structured prompt → llm_client.py → Ollama API
         ↓
LLM generates continuation maintaining style
         ↓
Result parsed + returned → Frontend displays with append option
```

### **3. Detailed Analysis Pipeline**

```
                    ┌─────────────────┐
                    │   Input Text    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ text_analyzer│  │  enhancer   │  │grammar_check│
    │   (spaCy)   │  │(readability)│  │  (spell)    │
    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
           │                │                │
           └────────────────┼────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  style_     │  │ consistency │  │ antipatterns│
    │ transformer │  │   checker   │  │  detector   │
    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
           │                │                │
           └────────────────┼────────────────┘
                            │
                            ▼
                    ┌─────────────────┐
                    │  Aggregate &    │
                    │ Build Response  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  JSON Response  │
                    └─────────────────┘
```

---

## 📦 Module-by-Module Breakdown

### **1. `nlp_engine/text_analyzer.py`** — Core NLP Foundation

**Purpose:** Foundation layer using spaCy for text processing

**Dependencies:** `spacy`, `en_core_web_sm`

| Function | What It Does |
|----------|--------------|
| `analyze(text)` | Tokenizes text, extracts sentences, entities, POS tags |
| `detect_long_sentences()` | Flags sentences >25 words with char offsets |
| `detect_repeated_words()` | Finds words used 3+ times (excluding stopwords) |
| `get_nlp()` | Returns cached spaCy model (`en_core_web_sm`) |

**Data Flow:**
```
Input text → spaCy doc → {sentences, tokens, entities, pos_tags}
```

**Output Schema:**
```json
{
  "sentences": ["First sentence.", "Second sentence."],
  "tokens": ["First", "sentence", ".", "Second", "sentence", "."],
  "entities": [["John", "PERSON"], ["New York", "GPE"]],
  "pos_tags": [
    {"token": "First", "pos": "ADJ", "tag": "JJ", "lemma": "first"}
  ]
}
```

---

### **2. `nlp_engine/enhancer.py`** — Readability & Flow Analysis

**Purpose:** Measures how easy/hard text is to read and how well it flows

**Dependencies:** `textstat`

| Analysis | Metrics |
|----------|---------|
| **Readability** | Flesch Reading Ease, Flesch-Kincaid Grade, Gunning Fog, SMOG, Coleman-Liau, Dale-Chall |
| **Flow** | Transition word count, sentence variety score |
| **Vocabulary** | Lexical diversity, advanced word count, complexity level |
| **Rhythm** | Sentence length variation, pattern detection |

**Key Functions:**

```python
calculate_readability(text) → {
    scores: {flesch_reading_ease, flesch_kincaid_grade, ...},
    grade_level: 8.5,
    reading_time_minutes: 2.5,
    difficulty: "standard",
    interpretation: "Plain English..."
}

analyze_flow(sentences) → {
    flow_score: 75,
    transition_count: 12,
    sentence_variety_score: 82,
    assessment: "Good variety..."
}

analyze_vocabulary_complexity(text) → {
    lexical_diversity: 0.68,
    complexity_level: "intermediate",
    advanced_words: 15,
    interpretation: "..."
}
```

**Readability Score Interpretation:**
| Flesch Score | Difficulty | Audience |
|--------------|------------|----------|
| 90-100 | Very Easy | 5th grade |
| 80-89 | Easy | 6th grade |
| 70-79 | Fairly Easy | 7th grade |
| 60-69 | Standard | 8th-9th grade |
| 50-59 | Fairly Difficult | High school |
| 30-49 | Difficult | College |
| 0-29 | Very Difficult | Graduate |

---

### **3. `nlp_engine/style_transformer.py`** — Style Conversion

**Purpose:** Transform text between different writing styles

**Supported Styles:**

| Mode | Description | Techniques |
|------|-------------|------------|
| `formal` | Professional, polished | Expand contractions, remove slang |
| `casual` | Relaxed, conversational | Add contractions, simplify vocabulary |
| `academic` | Scholarly, precise | Technical terms, passive voice |
| `creative` | Vivid, expressive | Strong verbs, imagery, metaphors |
| `persuasive` | Compelling, action-driven | Power words, emotional appeal |
| `journalistic` | Clear, concise | Inverted pyramid, active voice |
| `narrative` | Storytelling, immersive | Show don't tell, sensory details |

**Transformation Modes:**
- **Quick (rule-based):** Fast, deterministic transformations using pattern matching
- **Deep (LLM-powered):** AI-driven rewriting for natural, context-aware results

**Example Transformations:**

```
CASUAL → FORMAL:
"gonna" → "going to"
"wanna" → "want to"
"Hey!" → "Greetings,"

FORMAL → CASUAL:
"I am" → "I'm"
"cannot" → "can't"
"Furthermore" → "Also"
```

---

### **4. `nlp_engine/grammar_checker.py`** — Grammar Analysis

**Purpose:** Identify mechanical issues in writing

**Dependencies:** `pyspellchecker`

| Check Category | What It Finds |
|----------------|---------------|
| **Spelling** | Misspelled words with suggestions |
| **Tense Consistency** | Mixed past/present tense in narrative |
| **Punctuation** | Comma splices, missing periods, run-ons |
| **Passive Voice** | "was written by" → "wrote" |
| **Subject-Verb Agreement** | "The dogs runs" → "The dogs run" |

**Output Example:**
```json
{
  "spelling_errors": [
    {"word": "recieve", "suggestions": ["receive"], "position": 45}
  ],
  "tense_issues": [
    {"sentence_idx": 3, "found": "walks", "expected_tense": "past"}
  ],
  "passive_voice": [
    {"text": "The report was written by the team", "start": 120, "end": 155}
  ]
}
```

---

### **5. `nlp_engine/consistency_checker.py`** — Narrative Tracking

**Purpose:** Track entities throughout text and detect inconsistencies

**Features:**

| Feature | Description |
|---------|-------------|
| **Entity Memory** | Tracks all characters, locations, objects mentioned |
| **Name Variations** | Detects "John Smith" vs "Smith" vs "John" |
| **Type Conflicts** | Same name used for different entity types |
| **Pronoun Analysis** | Ensures clear antecedent references |
| **Timeline Tracking** | Tracks narrative events chronologically |

**Narrative Tracking Output:**
```json
{
  "character_memory": {
    "maya": {
      "canonical_name": "Maya",
      "mentions": 12,
      "first_mention_sentence": 0,
      "type": "PERSON"
    }
  },
  "plot_events": [
    {
      "sentence_index": 5,
      "subject": "Maya",
      "verb_text": "discovered",
      "tense": "past"
    }
  ],
  "dialogue": {
    "total_quotes": 8,
    "dialogue_ratio": 0.35,
    "speaker_lines": {"Maya": 5, "Jason": 3}
  },
  "pacing": {
    "pace_score": 72,
    "ratios": {"action": 0.4, "dialogue": 0.35, "description": 0.25}
  }
}
```

---

### **6. `nlp_engine/antipatterns.py`** — Writing Anti-Pattern Detection

**Purpose:** Identify 8 categories of weak writing with educational feedback

**Categories:**

| # | Category | Pattern | Example Fix |
|---|----------|---------|-------------|
| 1 | **Adverb Overuse** | Excessive -ly adverbs | "She said angrily" → "She snapped" |
| 2 | **Show Don't Tell** | Copula + emotion adjective | "She was sad" → "Her shoulders slumped" |
| 3 | **Nominalizations** | -tion/-ment/-ness nouns | "utilization" → "use" |
| 4 | **Hedge Words** | "perhaps", "sort of" | Delete or commit to claim |
| 5 | **Redundant Modifiers** | "very unique" | "unique" |
| 6 | **Weak Openings** | "There was...", "It is..." | Start with subject/action |
| 7 | **Filter Words** | "I saw that...", "I felt..." | Remove filter, show directly |
| 8 | **Info Dumps** | Long exposition paragraphs | Break into dialogue/action |

**Detection Output:**
```json
{
  "adverb_overuse": [
    {
      "text": "quickly",
      "sentence_idx": 3,
      "start": 45,
      "end": 52,
      "before": "She quickly ran to the door.",
      "after": "She dashed to the door.",
      "explanation": "Replace adverb with stronger verb"
    }
  ],
  "show_dont_tell": [
    {
      "text": "was happy",
      "before": "She was happy about the news.",
      "after": "A smile spread across her face as she read the news.",
      "explanation": "Show emotion through actions, not labels"
    }
  ]
}
```

---

### **7. `nlp_engine/llm_client.py`** — Ollama LLM Integration

**Purpose:** Custom wrapper for local LLM communication via Ollama

**Architecture:**
```
┌─────────────────────────────────────┐
│           LLMClient                 │
│  ┌─────────────────────────────┐    │
│  │ Configuration:              │    │
│  │ - base_url: localhost:11434 │    │
│  │ - model: llama3.2:3b        │    │
│  │ - timeout: 60 seconds       │    │
│  │ - max_retries: 3            │    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ Methods:                    │    │
│  │ - generate()   (sync)       │    │
│  │ - stream()     (streaming)  │    │
│  │ - check_status()            │    │
│  └─────────────────────────────┘    │
└──────────────┬──────────────────────┘
               │ HTTP POST
               ▼
┌──────────────────────────────────────┐
│           Ollama Server              │
│         llama3.2:3b model            │
│    (Local, runs on GPU/CPU)          │
└──────────────────────────────────────┘
```

**Task-Specific Temperatures:**

| Task Type | Temperature | Creativity Level |
|-----------|-------------|------------------|
| `REWRITE` | 0.3 | Low — faithful corrections |
| `STYLE_TRANSFORM` | 0.6 | Medium — style changes |
| `STORY_CONTINUE` | 0.85 | High — creative narrative |
| `EXPLANATION` | 0.4 | Low — clear explanations |

**Usage Example:**
```python
from nlp_engine.llm_client import get_client, TaskType

client = get_client()
result = client.generate(
    prompt="Rewrite this sentence to be more concise: ...",
    task_type=TaskType.REWRITE,
    max_tokens=256
)
print(result.text)  # Rewritten sentence
```

---

### **8. `nlp_engine/story_assistant.py`** — AI Story Continuation

**Purpose:** Continue stories while maintaining author's voice and style

**Processing Pipeline:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    STORY CONTINUATION PIPELINE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. ANALYZE INPUT TEXT                                          │
│     ├── POV Detection                                           │
│     │   ├── first_person ("I walked...")                        │
│     │   ├── second_person ("You walk...")                       │
│     │   ├── third_person_limited ("She thought...")             │
│     │   └── third_person_omniscient (multiple POVs)             │
│     │                                                           │
│     ├── Tense Detection                                         │
│     │   ├── past ("walked", "was running")                      │
│     │   ├── present ("walks", "is running")                     │
│     │   └── mixed (inconsistent)                                │
│     │                                                           │
│     ├── Tone Detection                                          │
│     │   ├── serious, humorous, dark, lighthearted               │
│     │   ├── suspenseful, romantic, melancholic                  │
│     │   └── adventurous, mysterious, neutral                    │
│     │                                                           │
│     └── Genre Hint                                              │
│         └── fantasy, sci-fi, romance, thriller, mystery...      │
│                                                                 │
│  2. EXTRACT CONTEXT                                             │
│     ├── Characters (names, attributes, relationships)           │
│     ├── Plot Elements (events, conflicts, settings)             │
│     ├── Recent Events (last 3-5 sentences)                      │
│     └── Compression (if >2000 tokens, summarize)                │
│                                                                 │
│  3. BUILD CONTINUATION PROMPT                                   │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ SYSTEM: You are a skilled fiction writer...          │     │
│     │                                                      │     │
│     │ CONTEXT:                                             │     │
│     │ - POV: {third_person_limited}                        │     │
│     │ - Tense: {past}                                      │     │
│     │ - Tone: {suspenseful}                                │     │
│     │ - Characters: Maya (protagonist), The Shadow         │     │
│     │ - Recent: Maya discovered the hidden door...         │     │
│     │                                                      │     │
│     │ INSTRUCTION: Continue for ~150 words, maintain       │     │
│     │ the established style. {custom_direction}            │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                 │
│  4. GENERATE (via Ollama)                                       │
│     └── Temperature: 0.85 for creative output                   │
│                                                                 │
│  5. POST-PROCESS                                                │
│     ├── Validate POV consistency                                │
│     ├── Validate tense consistency                              │
│     └── Trim to word target                                     │
│                                                                 │
│  6. RETURN RESULT                                               │
│     └── {continuation, pov, tense, generation_time_ms}          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Multi-Option Generation:**

When generating continuation options, the system provides:

| Option | Direction | Description |
|--------|-----------|-------------|
| A | Continue Scene | Natural progression of current action |
| B | Time Skip | Jump ahead, scene break |
| C | New Tension | Introduce conflict, complication |

---

### **9. `nlp_engine/pipeline.py`** — Central Orchestrator

**Purpose:** Coordinate all NLP modules and aggregate results

**Class: `WritingAssistant`**

```python
class WritingAssistant:
    """
    Main orchestrator that integrates all NLP analysis modules.
    
    Features enabled by default:
    - text_analysis: True
    - readability: True
    - flow: True
    - style: True
    - consistency: True
    - grammar: True
    - transform: False (on-demand)
    - explanations: True
    - mind_map: True
    - antipatterns: True
    """
    
    def __init__(self, config=None):
        self.long_sentence_threshold = 25
        self.repeated_word_min_count = 3
        self.target_style = "formal"
        self.enable_parallel = True
        self.nlp = text_analyzer.get_nlp()
    
    def analyze(self, text, features=None):
        """
        Perform comprehensive text analysis.
        
        Parallel execution via ThreadPoolExecutor for performance.
        """
        # ... orchestration logic
```

**Parallel Execution:**
```python
with ThreadPoolExecutor(max_workers=6) as executor:
    futures = {
        executor.submit(text_analyzer.analyze, text): "text_analysis",
        executor.submit(enhancer.calculate_readability, text): "readability",
        executor.submit(grammar_checker.analyze, doc): "grammar",
        executor.submit(antipatterns.detect_all, doc): "antipatterns",
        executor.submit(consistency_checker.analyze, doc): "consistency",
        executor.submit(concept_extractor.extract, doc): "mind_map",
    }
    
    for future in as_completed(futures):
        key = futures[future]
        results[key] = future.result()
```

---

## 🤖 LLM Integration — How Llama Works in Our Project

### **What is an LLM (Large Language Model)?**

A Large Language Model is a neural network trained on massive amounts of text data to understand and generate human-like text. At its core:

```
┌─────────────────────────────────────────────────────────────────┐
│                    HOW LLMs WORK (Simplified)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. TOKENIZATION                                                │
│     "The cat sat" → [464, 3797, 3290]  (token IDs)             │
│                                                                 │
│  2. EMBEDDING                                                   │
│     [464, 3797, 3290] → [[0.1, 0.3, ...], [0.2, 0.1, ...], ...]│
│     (Each token becomes a high-dimensional vector)              │
│                                                                 │
│  3. TRANSFORMER LAYERS (Attention Mechanism)                    │
│     ┌─────────────────────────────────────────┐                 │
│     │ Self-Attention: "cat" attends to "The"  │                 │
│     │ to understand context and relationships │                 │
│     └─────────────────────────────────────────┘                 │
│                                                                 │
│  4. PREDICTION                                                  │
│     Model predicts next token probabilities:                    │
│     "on" (0.35), "down" (0.28), "quietly" (0.15), ...          │
│                                                                 │
│  5. SAMPLING (Temperature Controls Randomness)                  │
│     Low temp (0.3): Picks highest probability → deterministic  │
│     High temp (0.8): More random → creative/diverse            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### **Why Llama 3.2:3b?**

We chose **Llama 3.2 3B** (3 billion parameters) for several strategic reasons:

| Factor | Llama 3.2:3b | Larger Models (7B+) |
|--------|--------------|---------------------|
| **VRAM Required** | ~4GB | 8-16GB+ |
| **Speed** | Fast (~2-5 sec/response) | Slower |
| **Quality** | Excellent for writing tasks | Marginally better |
| **Local Deployment** | ✅ Runs on consumer GPUs | ❌ Needs expensive hardware |
| **Privacy** | ✅ 100% local, no data leaves | Same |

### **Our LLM System Design**

```
┌─────────────────────────────────────────────────────────────────┐
│                    WRITECRAFT LLM ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FRONTEND (app.js)                                              │
│  ├── User clicks "Continue Story" / "Enhance" / "Transform"    │
│  ├── Collects: text, settings (word target, style, direction)  │
│  └── Sends POST request to backend                              │
│                                                                 │
│         │                                                       │
│         ▼                                                       │
│                                                                 │
│  BACKEND (main.py)                                              │
│  ├── Receives request with text + parameters                    │
│  ├── Routes to appropriate handler:                             │
│  │   ├── /story/continue → story_assistant.py                  │
│  │   ├── /enhance/rewrite → llm_enhancer.py                    │
│  │   ├── /transform/style → style_transformer.py + LLM         │
│  │   └── /improve/ai → llm_enhancer.py                         │
│  └── Returns JSON response                                      │
│                                                                 │
│         │                                                       │
│         ▼                                                       │
│                                                                 │
│  NLP ENGINE LAYER                                               │
│  ├── story_assistant.py (Story Continuation)                   │
│  │   ├── Extracts: POV, tense, tone, characters, plot          │
│  │   ├── Builds context-aware prompt                           │
│  │   └── Calls llm_client.py                                    │
│  │                                                              │
│  ├── llm_enhancer.py (Text Enhancement)                        │
│  │   ├── Detects issue type (passive, wordy, etc.)             │
│  │   ├── Builds targeted rewrite prompt                        │
│  │   └── Calls llm_client.py                                    │
│  │                                                              │
│  └── llm_client.py (Ollama Wrapper)                            │
│      ├── Manages connection to Ollama server                   │
│      ├── Handles retries, timeouts, errors                     │
│      ├── Sets temperature based on task type                   │
│      └── Parses and returns LLM response                       │
│                                                                 │
│         │                                                       │
│         ▼                                                       │
│                                                                 │
│  OLLAMA SERVER (localhost:11434)                               │
│  ├── Runs llama3.2:3b model                                    │
│  ├── Receives prompt via HTTP POST /api/generate               │
│  ├── Performs inference on GPU/CPU                             │
│  └── Streams or returns generated text                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### **What We Built — Custom Components**

We built **everything custom** except for the core LLM inference (Ollama). Here's what we implemented:

#### **1. llm_client.py — Custom Ollama Wrapper**

```python
# NOT using any LLM library — pure HTTP requests to Ollama API

class LLMClient:
    """
    Custom-built Ollama client with:
    - Connection pooling and retry logic
    - Task-specific temperature presets
    - Streaming support for real-time output
    - Timeout handling and error recovery
    """
    
    def generate(self, prompt, task_type, max_tokens=512):
        # Set temperature based on task
        temp = TASK_TEMPERATURES[task_type]
        
        # Build request payload
        payload = {
            "model": "llama3.2:3b",
            "prompt": prompt,
            "options": {
                "temperature": temp,
                "num_predict": max_tokens
            },
            "stream": False
        }
        
        # Send to Ollama
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=60.0
        )
        
        return self._parse_response(response)
```

**Why Custom?** 
- No dependency on langchain/llamaindex (simpler, faster)
- Full control over prompts and parameters
- Smaller codebase, easier to debug

#### **2. story_assistant.py — Intelligent Context Extraction**

```python
# Custom narrative analysis — no external AI for this part

class StoryAssistant:
    """
    Extracts writing context using rule-based NLP BEFORE calling LLM.
    This reduces LLM load and improves consistency.
    """
    
    def analyze_story(self, text):
        # 1. Detect POV using pronoun analysis (rule-based)
        pov = self._detect_pov(text)  # "first_person", "third_person_limited"
        
        # 2. Detect tense using verb analysis (spaCy)
        tense = self._detect_tense(text)  # "past", "present"
        
        # 3. Extract characters using NER + heuristics
        characters = self._extract_characters(text)
        
        # 4. Detect tone using keyword matching + sentiment
        tone = self._detect_tone(text)  # "suspenseful", "romantic"
        
        return NarrativeContext(pov, tense, characters, tone)
    
    def continue_story(self, text, word_target=150, direction=""):
        # Extract context FIRST (fast, deterministic)
        context = self.analyze_story(text)
        
        # Build prompt with extracted context
        prompt = self._build_continuation_prompt(text, context, direction)
        
        # THEN call LLM (slow, but now well-informed)
        return llm_client.generate(prompt, TaskType.STORY_CONTINUE)
```

**Design Decision:** We do heavy preprocessing BEFORE calling the LLM:
- POV, tense, tone detection → **Rule-based (fast, reliable)**
- Character extraction → **spaCy NER (deterministic)**
- Actual text generation → **LLM (creative)**

This hybrid approach gives us:
- ✅ Consistent POV/tense maintenance
- ✅ Faster response times
- ✅ Lower token usage
- ✅ More control over output

#### **3. llm_enhancer.py — Targeted Rewriting**

```python
# Custom prompt engineering for each issue type

REWRITE_PROMPTS = {
    "passive_voice": """
        Rewrite this sentence to use active voice.
        Keep the meaning identical. Be concise.
        
        Original: {text}
        Active version:
    """,
    
    "show_dont_tell": """
        Rewrite this sentence to SHOW the emotion through actions,
        body language, or sensory details instead of stating it directly.
        
        Original: {text}
        Rewritten:
    """,
    
    "wordy": """
        Make this sentence more concise while preserving meaning.
        Remove unnecessary words.
        
        Original: {text}
        Concise version:
    """
}

def enhance_text(text, issue_type, context=""):
    # Select appropriate prompt template
    template = REWRITE_PROMPTS[issue_type]
    
    # Build final prompt with context
    prompt = template.format(text=text) + f"\nContext: {context}"
    
    # Call LLM with low temperature for faithful rewriting
    result = llm_client.generate(prompt, TaskType.REWRITE)
    
    return {
        "original": text,
        "suggestion": result.text,
        "issue_type": issue_type,
        "confidence": calculate_confidence(result)
    }
```

### **Temperature Strategy — Our Design Decision**

Temperature controls LLM creativity. We use different temperatures for different tasks:

```
┌──────────────────────────────────────────────────────────────┐
│                    TEMPERATURE STRATEGY                       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Task: REWRITE (fixing passive voice, wordiness)             │
│  Temperature: 0.3 (LOW)                                      │
│  Why: Need faithful corrections, not creative rewrites       │
│  Example: "was written by John" → "John wrote"               │
│                                                              │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  Task: STYLE_TRANSFORM (formal ↔ casual)                     │
│  Temperature: 0.6 (MEDIUM)                                   │
│  Why: Need some creativity for natural phrasing              │
│  Example: "gonna" → "going to" (but natural flow)            │
│                                                              │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  Task: STORY_CONTINUE (narrative generation)                 │
│  Temperature: 0.85 (HIGH)                                    │
│  Why: Want creative, diverse continuations                   │
│  Example: Generate unique plot developments                  │
│                                                              │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  Task: EXPLANATION (why this suggestion?)                    │
│  Temperature: 0.4 (LOW-MEDIUM)                               │
│  Why: Clear explanations, but some natural variation         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### **Prompt Engineering — How We Talk to the LLM**

We carefully craft prompts for each use case:

#### **Story Continuation Prompt Structure:**

```
┌─────────────────────────────────────────────────────────────┐
│                  CONTINUATION PROMPT                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SYSTEM MESSAGE (Sets behavior):                            │
│  "You are a skilled fiction writer who seamlessly           │
│   continues stories while maintaining the author's          │
│   voice, style, and narrative consistency."                 │
│                                                             │
│  CONTEXT BLOCK (Extracted by our code, not LLM):           │
│  - POV: third_person_limited                                │
│  - Tense: past                                              │
│  - Tone: suspenseful                                        │
│  - Main Characters: Maya (protagonist), The Shadow (antagonist)
│  - Recent Events: Maya discovered the hidden door...        │
│                                                             │
│  STORY EXCERPT (Last 500-1000 words):                      │
│  "Maya's heart pounded as she pushed open the door.         │
│   The room beyond was dark, but she could sense             │
│   something waiting in the shadows..."                      │
│                                                             │
│  INSTRUCTION:                                               │
│  "Continue this story for approximately 150 words.          │
│   Maintain the established POV and tense.                   │
│   {user_direction: 'Build tension, don't reveal villain'}   │
│   Write ONLY the continuation, no commentary."              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### **Why This Structure?**

1. **System message** → Sets the LLM's "persona" and goals
2. **Context block** → Gives extracted facts (not asking LLM to analyze)
3. **Story excerpt** → Provides immediate context
4. **Clear instruction** → Specific word count, constraints, format

### **Request/Response Flow — Detailed**

```
┌─────────────────────────────────────────────────────────────┐
│         COMPLETE LLM REQUEST FLOW (Story Continuation)      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. USER ACTION                                             │
│     User clicks "✦ Continue Story" with:                    │
│     - Text: 500 words of their story                        │
│     - Word target: 150                                      │
│     - Direction: "Build tension"                            │
│                                                             │
│  2. FRONTEND (app.js)                                       │
│     continueStoryFromUI() {                                 │
│       POST /story/continue {                                │
│         text: "Maya's heart pounded...",                    │
│         word_target: 150,                                   │
│         custom_instruction: "Build tension",                │
│         stream: false                                       │
│       }                                                     │
│     }                                                       │
│                                                             │
│  3. BACKEND (main.py)                                       │
│     @app.post("/story/continue")                            │
│     async def continue_story(request):                      │
│       assistant = get_story_assistant()                     │
│       result = assistant.continue_story(                    │
│         text=request.text,                                  │
│         word_target=request.word_target,                    │
│         instruction=request.custom_instruction              │
│       )                                                     │
│       return StoryContinueResponse(...)                     │
│                                                             │
│  4. STORY ASSISTANT (story_assistant.py)                    │
│     def continue_story(text, word_target, instruction):     │
│       # Step A: Analyze context (rule-based, ~50ms)         │
│       context = self.analyze_story(text)                    │
│       # → {pov: "third_person", tense: "past", ...}        │
│                                                             │
│       # Step B: Build prompt (~1ms)                         │
│       prompt = self._build_prompt(text, context, instruction)
│                                                             │
│       # Step C: Call LLM (~2-5 seconds)                     │
│       result = llm_client.generate(                         │
│         prompt=prompt,                                      │
│         task_type=TaskType.STORY_CONTINUE,                  │
│         max_tokens=word_target * 2                          │
│       )                                                     │
│                                                             │
│       # Step D: Post-process (~10ms)                        │
│       return self._clean_output(result, context)            │
│                                                             │
│  5. LLM CLIENT (llm_client.py)                             │
│     def generate(prompt, task_type, max_tokens):            │
│       # Set temperature for story = 0.85                    │
│       response = httpx.post(                                │
│         "http://localhost:11434/api/generate",              │
│         json={                                              │
│           "model": "llama3.2:3b",                           │
│           "prompt": prompt,                                 │
│           "options": {"temperature": 0.85, "num_predict": 300}
│         }                                                   │
│       )                                                     │
│       return GenerationResult(text=response["response"])    │
│                                                             │
│  6. OLLAMA SERVER (localhost:11434)                        │
│     - Receives prompt (system + context + story + instruction)
│     - Runs Llama 3.2 inference on GPU                       │
│     - Generates ~150 words token by token                   │
│     - Returns complete text                                 │
│                                                             │
│  7. RESPONSE FLOW BACK                                      │
│     Ollama → llm_client → story_assistant → main.py → app.js│
│                                                             │
│     Final Response JSON:                                    │
│     {                                                       │
│       "success": true,                                      │
│       "continuation": "The shadow moved. Maya froze...",    │
│       "pov": "third_person_limited",                        │
│       "tense": "past",                                      │
│       "generation_time_ms": 2847                            │
│     }                                                       │
│                                                             │
│  8. FRONTEND RENDERS                                        │
│     - Shows continuation in result box                      │
│     - "Copy" and "Append to Text" buttons                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **Error Handling & Resilience**

```python
# Our custom error handling in llm_client.py

class LLMClient:
    def generate(self, prompt, task_type, max_tokens):
        for attempt in range(self.max_retries):
            try:
                response = httpx.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return self._parse_response(response)
                    
            except httpx.TimeoutException:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                
            except httpx.ConnectError:
                raise ConnectionError("Ollama server not running. Start with: ollama serve")
        
        raise GenerationError(f"Failed after {self.max_retries} attempts")
```

### **Performance Optimizations We Implemented**

| Optimization | What We Did | Impact |
|--------------|-------------|--------|
| **Context Compression** | Summarize stories >2000 tokens before sending to LLM | 2x faster for long texts |
| **Pre-extraction** | Extract POV/tense/characters with rules, not LLM | Saves ~500 tokens per request |
| **Temperature Tuning** | Different temps for different tasks | Better quality, fewer retries |
| **Lazy Loading** | LLM client created only when needed | Faster startup |
| **Connection Pooling** | Reuse HTTP connections to Ollama | ~100ms savings per request |
| **Streaming Option** | SSE for real-time output | Better UX for long generations |

### **Security & Privacy Design**

```
┌─────────────────────────────────────────────────────────────┐
│                    PRIVACY-FIRST DESIGN                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ 100% LOCAL PROCESSING                                   │
│     - Ollama runs on your machine                           │
│     - No text sent to cloud APIs                            │
│     - No OpenAI, no Anthropic, no external services         │
│                                                             │
│  ✅ NO DATA STORAGE                                         │
│     - Text analyzed in memory only                          │
│     - Nothing saved to disk                                 │
│     - No logs of user content                               │
│                                                             │
│  ✅ OPEN SOURCE MODEL                                       │
│     - Llama 3.2 is Meta's open model                        │
│     - Weights are public, auditable                         │
│     - No hidden behaviors                                   │
│                                                             │
│  NETWORK DIAGRAM:                                           │
│                                                             │
│  [Browser] ←→ [localhost:8000] ←→ [localhost:11434]        │
│              (Your Backend)       (Your Ollama)             │
│                                                             │
│  ❌ NO external connections for LLM features                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🖥️ Backend API (`backend/main.py`)

### **Endpoint Reference**

| Endpoint | Method | Purpose | Request Body |
|----------|--------|---------|--------------|
| `/` | GET | API info | — |
| `/health` | GET | Health check | — |
| `/llm/status` | GET | Ollama status | — |
| `/analyze` | POST | Full analysis | `AnalysisRequest` |
| `/transform` | POST | Style transform | `TransformRequest` |
| `/enhance/rewrite` | POST | LLM rewrite | `RewriteRequest` |
| `/enhance/batch` | POST | Batch rewrite | `BatchRewriteRequest` |
| `/transform/style` | POST | Style transform | `StyleTransformRequest` |
| `/story/analyze` | POST | Story context | `StoryAnalyzeRequest` |
| `/story/continue` | POST | Continue story | `StoryContinueRequest` |
| `/story/options` | POST | Get options | `StoryContinueOptionsRequest` |
| `/improve/ai` | POST | AI suggestions | `AIImproveRequest` |

### **Request/Response Schemas**

**AnalysisRequest:**
```json
{
  "text": "Your text here...",
  "features": {
    "text_analysis": true,
    "readability": true,
    "flow": true,
    "style": true,
    "consistency": true,
    "grammar": true,
    "transform": false,
    "explanations": true,
    "mind_map": true,
    "antipatterns": true
  },
  "target_style": "formal",
  "target_tone": "professional"
}
```

**AnalysisResponse:**
```json
{
  "input": {
    "text": "...",
    "character_count": 1250,
    "features_enabled": {...}
  },
  "text_analysis": {
    "sentences": [...],
    "tokens": [...],
    "entities": [...],
    "pos_tags": [...]
  },
  "readability": {
    "scores": {...},
    "grade_level": 8.5,
    "difficulty": "standard"
  },
  "flow": {
    "flow_score": 75,
    "transition_count": 12
  },
  "style_analysis": {
    "tone_scores": {...},
    "trajectory": [...]
  },
  "narrative_tracker": {
    "plot_events": [...],
    "character_memory": {...},
    "dialogue": {...}
  },
  "antipatterns": {...},
  "suggestions": [...],
  "annotations": [...],
  "explanations": {...}
}
```

---

## 🎨 Frontend Architecture (`frontend/`)

### **File Structure**

| File | Purpose |
|------|---------|
| `index.html` | Main app shell, two-panel layout |
| `app.js` | Tab renderers, API calls, event handlers |
| `styles.css` | NotebookLM-inspired design system |

### **Tab System**

| Tab | Icon | Data Source | Renderer Function |
|-----|------|-------------|-------------------|
| Write | ✍️ | annotations[] | `renderWrite()` |
| Grammar | 🔤 | grammar_issues | `renderGrammar()` |
| Style & Tone | 🎨 | tone_scores, heatmap | `renderStyleTone()` |
| Narrative | 📖 | narrative_tracker | `renderNarrative()` |
| Mind Map | 🧠 | concept_graph | `renderMindMap()` |
| Insights | 💡 | readability, flow | `renderInsights()` |
| Anti-Patterns | 🚫 | antipatterns | `renderAntiPatterns()` |
| Improve | 🎯 | suggestions | `renderImprove()` |

### **UI Components**

```
┌─────────────────────────────────────────────────────────────────┐
│                          TOP BAR                                │
│  ✏️ WriteCraft    AI Writing Assistant    [API●] [LLM●] [⚙️]  │
├─────────────────────────────────────────────────────────────────┤
│                        MAIN LAYOUT                              │
│ ┌──────────────────────┬────────────────────────────────────┐  │
│ │   SOURCE PANEL       │        RESULTS AREA                │  │
│ │                      │                                    │  │
│ │  📝 Source Text      │  ┌── Score Strip ─────────────┐   │  │
│ │  ─────────────────   │  │ Overall│Read│Flow│Consist  │   │  │
│ │  [Textarea]          │  │  78    │ 72 │ 85 │  90     │   │  │
│ │                      │  └────────────────────────────┘   │  │
│ │                      │                                    │  │
│ │  342 chars · 52 words│  ┌── Tab Navigation ──────────┐   │  │
│ │                      │  │✍️│🔤│🎨│📖│🧠│💡│🚫│🎯│   │  │
│ │  [Clear] [✨Analyze] │  └────────────────────────────┘   │  │
│ │                      │                                    │  │
│ └──────────────────────│  ┌── Tab Content ─────────────┐   │  │
│                        │  │                            │   │  │
│                        │  │  [Dynamic content based    │   │  │
│                        │  │   on selected tab]         │   │  │
│                        │  │                            │   │  │
│                        │  └────────────────────────────┘   │  │
│                        └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### **JavaScript Architecture**

```javascript
// State Management
let analysisResults = null;      // Full analysis response
let currentTab = 'write';        // Active tab
let llmAvailable = false;        // LLM status
let storyAnalysisData = null;    // Story context cache
let storyContinuationData = null;// Last continuation

// Core Functions
analyzeText()       → POST /analyze → updateUI()
switchTab(tab)      → renderTab(tab) → bind events
renderTab(tab)      → switch(tab) { case 'write': renderWrite() }

// Tab Renderers
renderWrite()       → Annotated manuscript with highlights
renderGrammar()     → Issue cards with suggestions
renderStyleTone()   → Tone graph + heatmap + transform UI
renderNarrative()   → Story continuation + timeline
renderMindMap()     → vis.js network visualization
renderInsights()    → Stat cards grid
renderAntiPatterns()→ Category accordion with examples
renderImprove()     → AI suggestions + prioritized list
```

---

## 📊 Data Schemas (`backend/models.py`)

### **Core Models**

```python
class AnalysisRequest(BaseModel):
    text: str
    features: Optional[Dict[str, bool]] = None
    target_style: Optional[TargetStyle] = "formal"
    target_tone: Optional[str] = "auto"

class AnalysisResponse(BaseModel):
    input: InputInfo
    text_analysis: TextAnalysisOutput
    readability: ReadabilityOutput
    flow: FlowOutput
    style_analysis: StyleAnalysisOutput
    narrative_tracker: NarrativeTrackerOutput
    antipatterns: Dict[str, List[AntipatternItem]]
    suggestions: List[SuggestionItem]
    annotations: List[AnnotationItem]
    explanations: ExplanationsOutput

class StoryAnalyzeResponse(BaseModel):
    success: bool
    pov: str           # "first_person", "third_person_limited", etc.
    tense: str         # "past", "present", "mixed"
    tone: str          # "suspenseful", "romantic", etc.
    genre_hint: str    # "fantasy", "thriller", etc.
    characters: List[CharacterInfo]
    themes: List[str]

class StoryContinueResponse(BaseModel):
    success: bool
    continuation: str
    pov: str
    tense: str
    generation_time_ms: float
```

---

## 🚀 Performance Optimizations

| Optimization | Description |
|--------------|-------------|
| **Parallel Processing** | ThreadPoolExecutor for independent NLP modules |
| **Lazy Loading** | LLM models loaded on first use, not startup |
| **Model Caching** | spaCy model loaded once at module level |
| **Input Debouncing** | 300ms delay on character count updates |
| **Response Streaming** | SSE support for story continuation |
| **Batch Processing** | `/enhance/batch` for multiple rewrites |

---

## 🧪 Testing

### **Running Tests**

```bash
# Full pipeline test
python -m nlp_engine.test_pipeline

# Anti-pattern detection test
python test_antipatterns.py

# Tone analysis test
python test_tone.py
```

### **Manual Testing**

1. Start backend: `uvicorn backend.main:app --reload --port 8000`
2. Open `frontend/index.html` in browser
3. Paste sample text and click "Analyze"
4. Navigate through all 7 tabs to verify features

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `spacy` | 3.x | Core NLP pipeline |
| `en_core_web_sm` | — | English language model |
| `nltk` | 3.x | Tokenization utilities |
| `textstat` | 0.7+ | Readability formulas |
| `scikit-learn` | 1.x | TF-IDF vectorization |
| `pyspellchecker` | 0.7+ | Spell checking |
| `fastapi` | 0.100+ | REST API framework |
| `uvicorn` | 0.22+ | ASGI server |
| `pydantic` | 2.x | Data validation |
| `httpx` | 0.24+ | HTTP client (for Ollama) |

---

## 🔧 Configuration

### **Environment Setup**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### **Ollama Setup (for LLM features)**

```bash
# Install Ollama (https://ollama.ai)
# Then pull the model:
ollama pull llama3.2:3b

# Verify it's running:
curl http://localhost:11434/api/tags
```

---

## 📄 License

MIT License — Built by **Code Brothers**

---

> For quick start instructions, see [README.md](README.md)
