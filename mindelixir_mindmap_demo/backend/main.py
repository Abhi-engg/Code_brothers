from fastapi import FastAPI
from pydantic import BaseModel
from keybert import KeyBERT
import spacy
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]) 

# Load spaCy model once
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    # If model not present, raise helpful error at runtime
    raise RuntimeError("spaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")

kw_model = KeyBERT()

class MindRequest(BaseModel):
    text: str
    title: Optional[str] = None
    top_n: int = 8

@app.post('/mindmap')
async def create_mindmap(req: MindRequest):
    text = req.text or ''
    title = req.title or (text.strip().split('\n')[0][:80] if text else 'Document')

    # Extract keywords using KeyBERT
    try:
        kw_results = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), stop_words='english', top_n=req.top_n)
        keywords = [k for k, score in kw_results]
    except Exception:
        # Fallback: simple frequency-based keywords
        words = [w.text.lower() for w in nlp(text) if w.is_alpha and not w.is_stop]
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        keywords = sorted(freq.keys(), key=lambda k: -freq[k])[:req.top_n]

    # Split into sentences and extract entities
    doc = nlp(text)
    sentences = [s.text.strip() for s in doc.sents if s.text.strip()]
    entities = list({ent.text for ent in doc.ents})

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
        # If no direct sentence contains keyword, try simple token overlap
        if not related:
            for s in sentences:
                if s in used_sentences:
                    continue
                s_tokens = set([t.lemma_.lower() for t in nlp(s) if t.is_alpha])
                kw_tokens = set([t.lemma_.lower() for t in nlp(kw) if t.is_alpha])
                if kw_tokens and len(s_tokens & kw_tokens) > 0:
                    related.append({"topic": s})
                    used_sentences.add(s)
        if related:
            children.append({"topic": kw, "children": related})

    # Remaining sentences grouped under Misc if any
    leftovers = [ {"topic": s} for s in sentences if s not in used_sentences ]
    if leftovers:
        children.append({"topic": "Misc", "children": leftovers})

    return {
        "topic": title,
        "children": children,
        "entities": entities,
        "meta": {"keywords": keywords}
    }
