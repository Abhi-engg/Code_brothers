MindElixir Mind Map Demo

Quick demo: FastAPI backend extracts keywords (KeyBERT) and entities (spaCy), returns hierarchical JSON consumed by a MindElixir frontend.

Files:
- backend/main.py — FastAPI app (POST /mindmap)
- frontend/index.html — UI with Text and Mind Map views
- frontend/style.css — Minimal styling
- frontend/script.js — Fetch + render MindElixir
- requirements.txt — Python deps

Setup (recommended inside a venv):

1. Install deps

```bash
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

2. Run backend

```bash
cd mindelixir_mindmap_demo/backend
uvicorn main:app --reload --port 8000
```

3. Serve frontend (simple) from the frontend folder

```bash
cd mindelixir_mindmap_demo/frontend
python -m http.server 5500
# then open http://localhost:5500
```

Usage:
- Paste text, optional title, click Analyze.
- Switch to "Mind Map View" to explore.

Notes & Extensibility:
- For better sentence->keyword association you can add sentence-transformers clustering.
- MindElixir options allow editing, saving, exporting; this demo keeps it read-only.
