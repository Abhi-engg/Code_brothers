"""
Concept Extractor & Mind Map Generator  (Phase 7)
──────────────────────────────────────────────────
Extracts key concepts from text and builds a graph structure
suitable for frontend mind-map visualization.

Functions:
- extract_key_concepts     → top N concepts with importance scores
- build_concept_relationships → edges between concepts
- generate_mind_map_data   → {nodes, edges} ready for vis.js Network
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from itertools import combinations
from typing import Any, Dict, List, Optional, Set, Tuple

# ──────────────────────────────────────────────
# 1.  Extract Key Concepts
# ──────────────────────────────────────────────

# Common stop-chunks that slip through noun-chunk filtering
_STOP_CHUNKS = {
    "it", "this", "that", "these", "those", "which", "who", "what",
    "he", "she", "they", "we", "i", "you", "me", "us", "them",
    "his", "her", "its", "their", "our", "my", "your",
    "one", "ones", "thing", "things", "something", "someone",
    "everything", "nothing", "anyone", "anything", "none",
    "here", "there", "where", "when", "how", "why",
}


def _normalize_chunk(text: str) -> str:
    """Lower-case, strip determiners / leading adjectives for dedup."""
    t = text.lower().strip()
    # strip leading articles
    for prefix in ("the ", "a ", "an ", "this ", "that ", "these ", "those ",
                    "some ", "any ", "every ", "each ", "all "):
        if t.startswith(prefix):
            t = t[len(prefix):]
    return t.strip()


def extract_key_concepts(
    doc,
    text: str,
    max_concepts: int = 20,
) -> List[Dict[str, Any]]:
    """
    Extract key concepts from the spaCy doc.

    Strategy (three signals fused):
    1. Named-entity frequency  (weight × 3)
    2. Noun-chunk frequency    (weight × 2)
    3. Subject/Object verb pairs  (weight × 1.5)

    Returns a list sorted by importance, each dict:
        {label, type, importance, raw_count, group}
    """

    # --- 1. Named entities ---------------------------------------------------
    ent_counter: Counter = Counter()
    ent_type_map: Dict[str, str] = {}

    for ent in doc.ents:
        key = ent.text.strip()
        if len(key) < 2:
            continue
        norm = _normalize_chunk(key)
        if norm in _STOP_CHUNKS:
            continue
        ent_counter[norm] += 1
        # keep last-seen entity type
        ent_type_map[norm] = ent.label_

    # --- 2. Noun chunks -------------------------------------------------------
    chunk_counter: Counter = Counter()

    for chunk in doc.noun_chunks:
        norm = _normalize_chunk(chunk.text)
        if norm in _STOP_CHUNKS or len(norm) < 2:
            continue
        chunk_counter[norm] += 1

    # --- 3. Subject–verb–object triples ----------------------------------------
    svo_counter: Counter = Counter()

    for token in doc:
        if token.dep_ in ("nsubj", "nsubjpass"):
            subj = _normalize_chunk(token.text)
            verb = token.head.lemma_.lower()
            # find direct objects
            objs = [
                _normalize_chunk(child.text)
                for child in token.head.children
                if child.dep_ in ("dobj", "pobj", "attr")
                and _normalize_chunk(child.text) not in _STOP_CHUNKS
            ]
            if subj not in _STOP_CHUNKS:
                svo_counter[subj] += 1.5
            for o in objs:
                svo_counter[o] += 1.5

    # --- Fuse scores ----------------------------------------------------------
    all_keys: Set[str] = set(ent_counter) | set(chunk_counter) | set(svo_counter)

    scored: List[Tuple[str, float]] = []
    for key in all_keys:
        score = (
            ent_counter.get(key, 0) * 3.0
            + chunk_counter.get(key, 0) * 2.0
            + svo_counter.get(key, 0)
        )
        scored.append((key, score))

    scored.sort(key=lambda x: -x[1])
    top = scored[:max_concepts]

    if not top:
        return []

    max_score = top[0][1]

    concepts: List[Dict[str, Any]] = []
    for label, raw_score in top:
        etype = ent_type_map.get(label, "CONCEPT")
        group = _type_to_group(etype)
        concepts.append({
            "label": _title_case(label),
            "type": etype,
            "importance": round(raw_score / max_score * 100, 1) if max_score else 0,
            "raw_count": int(ent_counter.get(label, 0) + chunk_counter.get(label, 0)),
            "group": group,
        })

    return concepts


# ──────────────────────────────────────────────
# 2.  Build Concept Relationships (edges)
# ──────────────────────────────────────────────

def build_concept_relationships(
    doc,
    concepts: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Detect relationships between concepts via:
      - Co-occurrence in the same sentence
      - Dependency-path connections (subj→verb→obj)
      - Entity-type grouping
    """
    labels_lower = {c["label"].lower() for c in concepts}
    label_lookup = {c["label"].lower(): c["label"] for c in concepts}

    edges: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def _add_edge(a: str, b: str, rel: str, w: float = 1.0):
        if a == b:
            return
        key = (min(a, b), max(a, b))
        if key in edges:
            edges[key]["weight"] += w
            if rel not in edges[key]["relationship"]:
                edges[key]["relationship"] += f", {rel}"
        else:
            edges[key] = {
                "source": key[0],
                "target": key[1],
                "relationship": rel,
                "weight": w,
            }

    # --- Co-occurrence per sentence -------------------------------------------
    for sent in doc.sents:
        sent_lower = sent.text.lower()
        present = [lab for lab in labels_lower if lab in sent_lower]
        for a, b in combinations(present, 2):
            _add_edge(
                label_lookup[a], label_lookup[b],
                "co-occurs", 1.0,
            )

    # --- Dependency-path connections ------------------------------------------
    for token in doc:
        if token.dep_ in ("nsubj", "nsubjpass"):
            subj_norm = _normalize_chunk(token.text)
            verb = token.head.lemma_.lower()
            for child in token.head.children:
                if child.dep_ in ("dobj", "pobj", "attr"):
                    obj_norm = _normalize_chunk(child.text)
                    if subj_norm in labels_lower and obj_norm in labels_lower:
                        _add_edge(
                            label_lookup[subj_norm],
                            label_lookup[obj_norm],
                            verb,
                            2.0,
                        )

    # --- Entity-type grouping -------------------------------------------------
    type_groups: Dict[str, List[str]] = defaultdict(list)
    for c in concepts:
        type_groups[c["group"]].append(c["label"])

    for group_members in type_groups.values():
        if len(group_members) < 2:
            continue
        for a, b in combinations(group_members, 2):
            _add_edge(a, b, "same-group", 0.5)

    return list(edges.values())


# ──────────────────────────────────────────────
# 3.  Generate Mind Map Data (nodes + edges)
# ──────────────────────────────────────────────

def generate_mind_map_data(
    doc,
    text: str,
    max_concepts: int = 20,
) -> Dict[str, Any]:
    """
    Produce a graph structure for vis.js Network:

        {
          nodes: [{id, label, type, importance, group, size, color}],
          edges: [{source, target, relationship, weight}],
          central_node: str,
          stats: {total_nodes, total_edges, groups: {...}}
        }
    """
    concepts = extract_key_concepts(doc, text, max_concepts=max_concepts)
    if not concepts:
        return {
            "nodes": [],
            "edges": [],
            "central_node": None,
            "stats": {"total_nodes": 0, "total_edges": 0, "groups": {}},
        }

    edges = build_concept_relationships(doc, concepts)

    # Central node = highest importance
    central = concepts[0]["label"]

    # Build node list with vis.js-friendly fields
    group_colors = _group_color_map()
    nodes = []
    for i, c in enumerate(concepts):
        grp = c["group"]
        col = group_colors.get(grp, group_colors["other"])
        # Size proportional to importance  (range 15 → 55)
        size = 15 + (c["importance"] / 100) * 40
        nodes.append({
            "id": i,
            "label": c["label"],
            "type": c["type"],
            "importance": c["importance"],
            "group": grp,
            "size": round(size, 1),
            "color": col,
            "font_size": max(12, int(10 + (c["importance"] / 100) * 14)),
            "is_central": c["label"] == central,
        })

    # Map labels → ids for edges
    label_to_id = {n["label"]: n["id"] for n in nodes}

    vis_edges = []
    for e in edges:
        src_id = label_to_id.get(e["source"])
        tgt_id = label_to_id.get(e["target"])
        if src_id is not None and tgt_id is not None:
            vis_edges.append({
                "from": src_id,
                "to": tgt_id,
                "label": e["relationship"],
                "weight": round(e["weight"], 1),
                "width": max(1, min(5, e["weight"])),
            })

    # Group stats
    group_counts: Dict[str, int] = Counter(n["group"] for n in nodes)

    return {
        "nodes": nodes,
        "edges": vis_edges,
        "central_node": central,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(vis_edges),
            "groups": dict(group_counts),
        },
    }


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _type_to_group(etype: str) -> str:
    """Map NER / concept type to a display group."""
    mapping = {
        "PERSON": "character",
        "ORG": "organization",
        "GPE": "location",
        "LOC": "location",
        "FAC": "location",
        "DATE": "time",
        "TIME": "time",
        "EVENT": "event",
        "WORK_OF_ART": "theme",
        "PRODUCT": "theme",
        "LAW": "theme",
        "NORP": "theme",
        "LANGUAGE": "theme",
        "MONEY": "detail",
        "QUANTITY": "detail",
        "ORDINAL": "detail",
        "CARDINAL": "detail",
        "PERCENT": "detail",
    }
    return mapping.get(etype, "concept")


def _group_color_map() -> Dict[str, Dict[str, str]]:
    """Colors keyed by group, each with background + border."""
    return {
        "character":    {"background": "#3B82F6", "border": "#2563EB", "fontColor": "#ffffff"},
        "organization": {"background": "#6366F1", "border": "#4F46E5", "fontColor": "#ffffff"},
        "location":     {"background": "#10B981", "border": "#059669", "fontColor": "#ffffff"},
        "time":         {"background": "#F59E0B", "border": "#D97706", "fontColor": "#1E293B"},
        "event":        {"background": "#EC4899", "border": "#DB2777", "fontColor": "#ffffff"},
        "theme":        {"background": "#F59E0B", "border": "#B45309", "fontColor": "#1E293B"},
        "action":       {"background": "#EF4444", "border": "#DC2626", "fontColor": "#ffffff"},
        "detail":       {"background": "#94A3B8", "border": "#64748B", "fontColor": "#ffffff"},
        "concept":      {"background": "#8B5CF6", "border": "#7C3AED", "fontColor": "#ffffff"},
        "other":        {"background": "#CBD5E1", "border": "#94A3B8", "fontColor": "#1E293B"},
    }


def _title_case(s: str) -> str:
    """Smart title-case that preserves all-caps abbreviations."""
    if s.isupper() and len(s) <= 5:
        return s  # likely acronym
    return s.title()
