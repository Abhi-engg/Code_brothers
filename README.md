# ✍️ WriteCraft — AI-Powered Writing Analysis & Enhancement

> A comprehensive full-stack writing studio that analyzes, annotates, and improves your prose using advanced NLP — all wrapped in a clean, NotebookLM-inspired interface.

---

## 🏗️ Architecture

```
frontend/          → Vanilla JS + CSS (NotebookLM-style UI)
  index.html       → Two-panel layout, 7 writer-centric tabs
  styles.css       → CSS custom properties, responsive, accessible
  app.js           → Tab renderers, vis.js mind map, annotation engine

backend/           → FastAPI REST API
  main.py          → /analyze, /transform, /health endpoints
  models.py        → Pydantic response schemas

nlp_engine/        → Python NLP pipeline
  text_analyzer.py → spaCy sentence/token/entity extraction
  enhancer.py      → Readability, flow, style, issues detection
  style_transformer.py → Style & tone transformation
  consistency_checker.py → Narrative consistency tracking
  grammar_checker.py     → Spelling, grammar, tense, punctuation
  explanation.py         → Writer-friendly explanation generator
  concept_extractor.py   → Mind map graph builder
  antipatterns.py        → 8-category anti-pattern detector
  test_pipeline.py       → End-to-end test suite
```

---

## ✨ Capabilities (8 Areas)

| Area | What it does |
|---|---|
| **Annotated Manuscript** | Inline highlights for grammar, passive voice, fillers, clichés, style, tense, perspective & repetition with hover tooltips |
| **Grammar Analysis** | Spelling errors, grammar issues, tense consistency, punctuation, long sentences, repeated words, consistency checks |
| **Style & Tone** | Tone scoring (professional / casual / academic / creative / persuasive), per-sentence trajectory, style heatmap by paragraph, style transformation with diff view, sentiment analysis |
| **Narrative Tracking** | Plot events, character memory, dialogue breakdown, pacing ratios, settings/locations, narrative timeline |
| **Insights** | Interactive mind map (vis.js), readability scores, flow analysis, vocabulary complexity, lexical density, sentence rhythm, paragraph structure, named entities |
| **Anti-Patterns** | 8 categories: adverb overuse, show-don't-tell, nominalizations, hedge words, redundant modifiers, weak openings, filter words, info dumps — with before/after examples |
| **Improve** | Prioritized suggestions (high / medium / low), passive voice instances, filler word breakdown, cliché list |
| **Explanations** | Human-readable explanations for every analysis component |

---

## ⚡ Quick Start

### Prerequisites

- **Python 3.10+**
- **pip** (package manager)

### 1. Clone & Install

```bash
git clone https://github.com/Abhi-engg/Code_brothers.git
cd Code_brothers

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Start the Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 3. Open the Frontend

Open `frontend/index.html` in your browser, or serve it locally:

```bash
cd frontend
python -m http.server 8080
```

Then visit **http://localhost:8080**.

---

## 🔌 API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET`  | `/health` | API health check |
| `POST` | `/analyze` | Full analysis (all features) |
| `POST` | `/transform` | Style/tone transformation only |
| `POST` | `/analyze/quick` | Fast scan for common issues |
| `POST` | `/analyze/consistency` | Narrative consistency check |

### Example Request

```json
POST /analyze
{
  "text": "The quick brown fox jumped over the lazy dog.",
  "features": {
    "text_analysis": true,
    "readability": true,
    "flow": true,
    "style": true,
    "consistency": true,
    "transform": true,
    "explanations": true,
    "mind_map": true,
    "antipatterns": true
  },
  "target_style": "formal",
  "target_tone": "professional"
}
```

---

## 🎨 UI Design

The frontend takes inspiration from **NotebookLM**:

- **Two-panel layout** — source text on the left, analysis results on the right
- **Score strip** — overall / readability / flow / consistency at a glance
- **7 tabs** — Write · Grammar · Style & Tone · Narrative · Insights · Anti-Patterns · Improve
- **Settings drawer** — feature toggles, style/tone selectors, thresholds
- **Dark canvas mind map** — interactive vis.js network with drag, zoom, filter
- **Responsive** — adapts to tablet and mobile
- **Accessible** — respects `prefers-reduced-motion` and `prefers-contrast`

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `spacy` + `en_core_web_sm` | Core NLP pipeline |
| `nltk` | Tokenization & corpus utilities |
| `scikit-learn` | TF-IDF vectorization |
| `textstat` | Readability formulas |
| `pyspellchecker` | Spell checking |
| `fastapi` | REST API framework |
| `uvicorn` | ASGI server |
| `pydantic` | Data validation & schemas |

---

## 🧪 Testing

```bash
python -m nlp_engine.test_pipeline
```

This runs the end-to-end test suite and prints results for all 8 analysis areas.

---

## 📄 License

MIT

---

> Built with ❤️ by **Code Brothers**