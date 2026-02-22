/**
 * WriteCraft — Frontend Application
 * Restructured 7-tab layout with NotebookLM-inspired design
 * Tabs: Write | Grammar | Style & Tone | Narrative | Insights | Anti-Patterns | Improve
 */

// ═══════════════════════════════════════════════════════════
// CONFIG & STATE
// ═══════════════════════════════════════════════════════════
const CONFIG = { API_BASE_URL: 'http://localhost:8000', DEBOUNCE_DELAY: 300 };

let analysisResults = null;
let currentTab = 'write';

// ═══════════════════════════════════════════════════════════
// DOM REFERENCES
// ═══════════════════════════════════════════════════════════
const elements = {
    textInput:        document.getElementById('text-input'),
    analyzeBtn:       document.getElementById('analyze-btn'),
    clearBtn:         document.getElementById('clear-btn'),
    charCount:        document.getElementById('char-count'),
    wordCount:        document.getElementById('word-count'),
    resultsContainer: document.getElementById('results-container'),
    tabContent:       document.getElementById('tab-content'),
    scoresContainer:  document.getElementById('scores-container'),
    loadingOverlay:   document.getElementById('loading-overlay'),
    toastContainer:   document.getElementById('toast-container'),
    apiStatus:        document.getElementById('api-status'),
    targetStyle:      document.getElementById('target-style'),
    targetTone:       document.getElementById('target-tone'),
    thresholdSentence:document.getElementById('threshold-sentence'),
    thresholdRepeated:document.getElementById('threshold-repeated'),
    emptyState:       document.getElementById('empty-state'),
    settingsDrawer:   document.getElementById('settings-drawer'),
    settingsToggle:   document.getElementById('settings-toggle'),
    settingsClose:    document.getElementById('settings-close'),
    drawerOverlay:    document.getElementById('drawer-overlay'),
};

const featureToggles = {
    readability:   document.getElementById('feat-readability'),
    flow:          document.getElementById('feat-flow'),
    style:         document.getElementById('feat-style'),
    consistency:   document.getElementById('feat-consistency'),
    transform:     document.getElementById('feat-transform'),
    mindmap:       document.getElementById('feat-mindmap'),
    antipatterns:  document.getElementById('feat-antipatterns'),
    dialogue:      document.getElementById('feat-dialogue'),
};

const writerModeSelect = document.getElementById('writer-mode');

// ═══════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    checkAPIHealth();
    updateCounts();
});

function initEventListeners() {
    elements.textInput.addEventListener('input', debounce(updateCounts, CONFIG.DEBOUNCE_DELAY));
    elements.analyzeBtn.addEventListener('click', analyzeText);
    elements.clearBtn.addEventListener('click', clearAll);

    // Tabs
    document.querySelectorAll('.wc-tab').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Ctrl+Enter to analyze
    elements.textInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') analyzeText();
    });

    // Settings drawer
    if (elements.settingsToggle) elements.settingsToggle.addEventListener('click', openDrawer);
    if (elements.settingsClose)  elements.settingsClose.addEventListener('click', closeDrawer);
    if (elements.drawerOverlay)  elements.drawerOverlay.addEventListener('click', closeDrawer);
}

function openDrawer() { elements.settingsDrawer.classList.remove('hidden'); }
function closeDrawer() { elements.settingsDrawer.classList.add('hidden'); }

// ═══════════════════════════════════════════════════════════
// API COMMUNICATION
// ═══════════════════════════════════════════════════════════
async function checkAPIHealth() {
    try {
        const r = await fetch(`${CONFIG.API_BASE_URL}/health`);
        if (r.ok) {
            elements.apiStatus.innerHTML = '<span class="wc-status-dot"></span> API Connected';
            elements.apiStatus.className = 'wc-api-status connected';
        } else { throw new Error(); }
    } catch {
        elements.apiStatus.innerHTML = '<span class="wc-status-dot"></span> API Offline';
        elements.apiStatus.className = 'wc-api-status disconnected';
        showToast('API is not available. Make sure the server is running on port 8000.', 'error');
    }
}

async function analyzeText() {
    const text = elements.textInput.value.trim();
    if (!text) { showToast('Please enter some text to analyze', 'warning'); return; }

    const features = {
        text_analysis: true,
        readability:   featureToggles.readability?.checked ?? true,
        flow:          featureToggles.flow?.checked ?? true,
        style:         featureToggles.style?.checked ?? true,
        consistency:   featureToggles.consistency?.checked ?? true,
        transform:     featureToggles.transform?.checked ?? false,
        explanations:  true,
        mind_map:      featureToggles.mindmap?.checked ?? true,
        antipatterns:  featureToggles.antipatterns?.checked ?? true,
        dialogue_improver:     featureToggles.dialogue?.checked ?? true,
        scene_feedback:        false,
        writer_mode:   writerModeSelect?.value || 'fiction',
    };

    const body = {
        text,
        features,
        target_style: elements.targetStyle?.value || 'formal',
        target_tone:  elements.targetTone?.value || 'auto',
        long_sentence_threshold:  parseInt(elements.thresholdSentence?.value) || 25,
        repeated_word_min_count:  parseInt(elements.thresholdRepeated?.value) || 3,
        writer_mode:  writerModeSelect?.value || 'fiction',
    };

    elements.loadingOverlay.classList.remove('hidden');
    elements.analyzeBtn.disabled = true;
    elements.analyzeBtn.textContent = '⏳ Analyzing...';

    try {
        const r = await fetch(`${CONFIG.API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!r.ok) { 
            const e = await r.json(); 
            const errorMsg = typeof e.detail === 'string' ? e.detail : (e.detail?.msg || e.message || JSON.stringify(e.detail) || 'Analysis failed');
            throw new Error(errorMsg); 
        }

        analysisResults = await r.json();
        console.log('Analysis Results:', analysisResults);
        displayResults();
        showToast('Analysis complete!', 'success');
    } catch (err) {
        console.error('Analysis error:', err);
        const errorMessage = typeof err === 'string' ? err : (err.message || 'Failed to analyze text');
        showToast(errorMessage, 'error');
    } finally {
        elements.loadingOverlay.classList.add('hidden');
        elements.analyzeBtn.disabled = false;
        elements.analyzeBtn.textContent = '✨ Analyze';
    }
}

// ═══════════════════════════════════════════════════════════
// DISPLAY & SCORES
// ═══════════════════════════════════════════════════════════
function displayResults() {
    if (!analysisResults) return;
    elements.emptyState.classList.add('hidden');
    elements.resultsContainer.classList.remove('hidden');
    updateScores(analysisResults.scores);
    renderTab(currentTab);
}

function updateScores(scores) {
    if (!scores) return;
    const map = {
        overall:     { el: 'score-overall',     bar: 'score-overall-bar' },
        readability: { el: 'score-readability',  bar: 'score-readability-bar' },
        flow:        { el: 'score-flow',         bar: 'score-flow-bar' },
        consistency: { el: 'score-consistency',   bar: 'score-consistency-bar' },
    };
    for (const [key, cfg] of Object.entries(map)) {
        const v = scores[key];
        if (v == null) continue;
        const rounded = Math.round(v);
        const scoreEl = document.getElementById(cfg.el);
        const barEl   = document.getElementById(cfg.bar);
        if (scoreEl) animateNumber(scoreEl, 0, rounded, 800);
        if (barEl) setTimeout(() => {
            barEl.style.width = `${Math.min(100, v)}%`;
            barEl.style.backgroundColor = getScoreColor(v);
        }, 150);
    }
}

function updateCounts() {
    const text = elements.textInput.value;
    elements.charCount.textContent = text.length;
    elements.wordCount.textContent = text.trim() ? text.trim().split(/\s+/).length : 0;
    elements.analyzeBtn.disabled = !text.trim();
}

function clearAll() {
    elements.textInput.value = '';
    updateCounts();
    elements.resultsContainer.classList.add('hidden');
    elements.emptyState.classList.remove('hidden');
    analysisResults = null;
    currentTab = 'write';
}

// ═══════════════════════════════════════════════════════════
// TAB MANAGEMENT
// ═══════════════════════════════════════════════════════════
function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.wc-tab').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    renderTab(tab);
}

function renderTab(tab) {
    if (!analysisResults) return;
    let html = '';
    switch (tab) {
        case 'write':        html = renderWrite(); break;
        case 'grammar':      html = renderGrammar(); break;
        case 'style':        html = renderStyleTone(); break;
        case 'narrative':    html = renderNarrative(); break;
        case 'dialogue':     html = renderDialogue(); break;
        case 'insights':     html = renderInsights(); break;
        case 'antipatterns': html = renderAntiPatterns(); break;
        case 'improve':      html = renderImprove(); break;
    }
    elements.tabContent.innerHTML = html;
    elements.tabContent.style.opacity = '0';
    requestAnimationFrame(() => {
        elements.tabContent.style.transition = 'opacity 0.3s ease';
        elements.tabContent.style.opacity = '1';
    });

    if (tab === 'write')        bindWriteTabEvents();
    if (tab === 'insights')     setTimeout(() => initMindMapNetwork(), 60);
    if (tab === 'antipatterns')  setTimeout(() => bindAntiPatternEvents(), 60);
}


// ═══════════════════════════════════════════════════════════
//  TAB 1 — WRITE (Annotated Manuscript)
// ═══════════════════════════════════════════════════════════

const ANN_CATEGORIES = {
    grammar:     { label: 'Grammar',     icon: '🔤', color: '#EF4444' },
    passive:     { label: 'Passive',     icon: '🔀', color: '#F97316' },
    filler:      { label: 'Filler',      icon: '🗑️', color: '#EAB308' },
    cliche:      { label: 'Cliché',      icon: '🔁', color: '#A855F7' },
    style:       { label: 'Style',       icon: '📏', color: '#3B82F6' },
    tense:       { label: 'Tense',       icon: '⏱️', color: '#14B8A6' },
    perspective: { label: 'Perspective', icon: '👁️', color: '#EC4899' },
    repetition:  { label: 'Repetition',  icon: '🔂', color: '#6B7280' },
};
let annVisibleCategories = new Set(Object.keys(ANN_CATEGORIES));

function renderWrite() {
    const annotations = analysisResults.annotations || [];
    const text = analysisResults.input?.text || '';
    const ta = analysisResults.text_analysis;
    const rd = analysisResults.readability;

    // Counts
    const counts = {};
    for (const a of annotations) counts[a.category] = (counts[a.category] || 0) + 1;
    const total = annotations.length;

    // Quick stats strip
    const statsHtml = `
        <div class="wc-write-summary">
            <div class="wc-stat"><span class="wc-stat-value">${ta?.sentences?.length || 0}</span><span class="wc-stat-label">Sentences</span></div>
            <div class="wc-stat"><span class="wc-stat-value">${ta?.entities?.length || 0}</span><span class="wc-stat-label">Entities</span></div>
            <div class="wc-stat"><span class="wc-stat-value">${rd?.reading_time_minutes || 0}</span><span class="wc-stat-label">Min Read</span></div>
            <div class="wc-stat"><span class="wc-stat-value">${total}</span><span class="wc-stat-label">Annotations</span></div>
        </div>`;

    // Filter bar
    let filterBar = '<div class="ann-filter-bar">';
    for (const [cat, meta] of Object.entries(ANN_CATEGORIES)) {
        const c = counts[cat] || 0;
        if (c === 0) continue;
        const isActive = annVisibleCategories.has(cat);
        filterBar += `<button class="ann-filter-btn ann-filter-${cat} ${isActive ? 'active' : 'inactive'}" data-cat="${cat}" title="Toggle ${meta.label}"><span>${meta.icon} ${meta.label}</span><span class="ann-count">${c}</span></button>`;
    }
    filterBar += '</div>';

    const summaryLine = `<div class="ann-summary"><strong>${total}</strong> annotation${total !== 1 ? 's' : ''} found &middot; Hover highlighted text for details</div>`;
    const annotatedHTML = buildAnnotatedHTML(text, annotations);

    return `<div class="animate-fade-in">
        ${statsHtml}
        ${summaryLine}
        ${filterBar}
        <div class="annotated-text" id="annotated-text-area">${annotatedHTML}</div>
    </div>`;
}

function buildAnnotatedHTML(text, annotations) {
    if (!annotations || annotations.length === 0) return _esc(text);
    const visible = annotations.filter(a => annVisibleCategories.has(a.category));
    const events = [];
    for (let i = 0; i < visible.length; i++) {
        const a = visible[i];
        if (a.start == null || a.end == null || a.start >= a.end) continue;
        const start = Math.max(0, Math.min(a.start, text.length));
        const end   = Math.max(0, Math.min(a.end,   text.length));
        events.push({ pos: start, type: 'open',  ann: a, idx: i });
        events.push({ pos: end,   type: 'close', ann: a, idx: i });
    }
    events.sort((a, b) => a.pos - b.pos || (a.type === 'close' ? -1 : 1));

    let html = '', cursor = 0;
    const activeSet = new Map();
    for (const ev of events) {
        if (ev.pos > cursor) {
            html += activeSet.size > 0 ? wrapAnnotatedSegment(text.slice(cursor, ev.pos), activeSet) : _esc(text.slice(cursor, ev.pos));
            cursor = ev.pos;
        }
        ev.type === 'open' ? activeSet.set(ev.idx, ev.ann) : activeSet.delete(ev.idx);
    }
    if (cursor < text.length) html += _esc(text.slice(cursor));
    return html;
}

function wrapAnnotatedSegment(segment, activeMap) {
    const anns = Array.from(activeMap.values());
    const sevOrder = { error: 0, high: 1, warning: 2, medium: 3, info: 4, low: 5 };
    anns.sort((a, b) => (sevOrder[a.severity] ?? 9) - (sevOrder[b.severity] ?? 9));
    const primary = anns[0];
    const classes = ['ann', `ann-${primary.category}`];

    let tooltipInner = '';
    for (const a of anns) {
        const cat = ANN_CATEGORIES[a.category] || { label: a.category, icon: '📌' };
        tooltipInner += `<div style="margin-bottom:6px"><span class="ann-tooltip-cat ann-tooltip-cat-${a.category}">${cat.icon} ${cat.label}</span><span class="severity-badge severity-${a.severity}">${a.severity}</span><div class="ann-tooltip-msg">${_esc(a.message)}</div>${a.suggestion ? `<div class="ann-tooltip-suggestion">💡 ${_esc(a.suggestion)}</div>` : ''}</div>`;
    }
    let actions = '';
    if (primary.suggestion) {
        actions = `<div class="ann-tooltip-actions"><button class="ann-btn-dismiss" data-action="dismiss" data-ann-start="${primary.start}" data-ann-end="${primary.end}">Dismiss</button></div>`;
    }
    return `<span class="${classes.join(' ')}">${_esc(segment)}<span class="ann-tooltip">${tooltipInner}${actions}</span></span>`;
}

function bindWriteTabEvents() {
    document.querySelectorAll('.ann-filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const cat = btn.dataset.cat;
            annVisibleCategories.has(cat) ? annVisibleCategories.delete(cat) : annVisibleCategories.add(cat);
            elements.tabContent.innerHTML = renderWrite();
            bindWriteTabEvents();
        });
    });
    document.querySelectorAll('.ann-btn-dismiss').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const start = parseInt(btn.dataset.annStart), end = parseInt(btn.dataset.annEnd);
            if (analysisResults.annotations) {
                analysisResults.annotations = analysisResults.annotations.filter(a => !(a.start === start && a.end === end));
            }
            elements.tabContent.innerHTML = renderWrite();
            bindWriteTabEvents();
        });
    });
}


// ═══════════════════════════════════════════════════════════
//  TAB 2 — GRAMMAR
// ═══════════════════════════════════════════════════════════

function renderGrammar() {
    const grammar = analysisResults.grammar_analysis;
    const issues  = analysisResults.issues || {};
    const consistency = analysisResults.consistency;

    const longSentences     = issues.long_sentences || [];
    const repeatedWords     = issues.repeated_words || [];
    const consistencyIssues = consistency?.all_issues || [];

    // Grammar summary
    const summary = grammar?.summary || {};
    const totalGrammar = summary.total_issues || 0;
    const grade = summary.overall_grade || '—';
    const gradeColor = grade === 'A' ? '#34A853' : grade === 'B' ? '#4285F4' : grade === 'C' ? '#FBBC04' : '#EA4335';

    let html = '<div class="animate-fade-in">';

    // Header / grade
    html += `<div class="gram-header">
        <div>
            <h3 class="font-semibold" style="font-size:1.1rem;display:flex;align-items:center;gap:8px">
                🔤 Grammar Analysis
                <span class="wc-badge wc-badge-muted">${totalGrammar + longSentences.length + repeatedWords.length + consistencyIssues.length} issues</span>
            </h3>
        </div>
        <div class="gram-grade" style="background:${gradeColor}" title="Overall Grade">${grade}</div>
    </div>`;

    // Grammar issues from grammar_analysis
    if (grammar) {
        const sections = [
            { key: 'spell_errors',       title: '🔠 Spelling Errors',       items: grammar.spell_errors || [] },
            { key: 'grammar_issues',     title: '📝 Grammar Issues',        items: grammar.grammar_issues || [] },
            { key: 'style_suggestions',  title: '🎨 Style Suggestions',     items: grammar.style_suggestions || [] },
            { key: 'tense_consistency',  title: '⏱️ Tense Consistency',     items: grammar.tense_consistency || [] },
            { key: 'punctuation_issues', title: '✏️ Punctuation Issues',    items: grammar.punctuation_issues || [] },
        ];

        for (const sec of sections) {
            if (sec.items.length === 0) continue;
            html += `<div class="gram-section"><div class="gram-section-title">${sec.title} (${sec.items.length})</div>`;
            for (const item of sec.items.slice(0, 15)) {
                const sev = item.severity || 'info';
                html += `<div class="gram-issue">
                    <div class="gram-issue-header">
                        <span class="gram-issue-type">${_esc(item.type || item.issue || sec.key)}</span>
                        <span class="wc-badge wc-badge-${sev === 'error' || sev === 'high' ? 'error' : sev === 'warning' || sev === 'medium' ? 'warning' : 'primary'}">${sev}</span>
                    </div>
                    ${item.text || item.word || item.sentence ? `<p class="gram-issue-text">"${_esc(truncateText(item.text || item.word || item.sentence, 150))}"</p>` : ''}
                    ${item.suggestion || item.fix ? `<p class="gram-issue-fix">💡 ${_esc(item.suggestion || item.fix)}</p>` : ''}
                </div>`;
            }
            if (sec.items.length > 15) html += `<p class="text-xs text-muted mt-sm">+${sec.items.length - 15} more</p>`;
            html += '</div>';
        }
    }

    // Long Sentences
    if (longSentences.length > 0) {
        html += `<div class="gram-section"><div class="gram-section-title">📏 Long Sentences (${longSentences.length})</div>`;
        for (const ls of longSentences) {
            html += `<div class="gram-issue">
                <div class="gram-issue-header">
                    <span class="gram-issue-type">Sentence ${ls.index + 1}</span>
                    <span class="wc-badge wc-badge-warning">${ls.word_count} words</span>
                </div>
                <p class="gram-issue-text">${_esc(truncateText(ls.sentence, 200))}</p>
                <p class="gram-issue-fix">⚠️ Exceeds threshold by ${ls.excess} words. Consider splitting.</p>
            </div>`;
        }
        html += '</div>';
    }

    // Repeated Words
    if (repeatedWords.length > 0) {
        html += `<div class="gram-section"><div class="gram-section-title">🔁 Repeated Words (${repeatedWords.length})</div>
        <div style="display:flex;flex-wrap:wrap;gap:8px">`;
        for (const rw of repeatedWords) {
            html += `<div class="wc-stat" style="min-width:100px"><span class="wc-stat-value" style="font-size:1.2rem">"${_esc(rw.word)}"</span><span class="wc-stat-label">${rw.count}× (${rw.frequency.toFixed(1)}%)</span></div>`;
        }
        html += '</div></div>';
    }

    // Consistency Issues
    if (consistencyIssues.length > 0) {
        html += `<div class="gram-section"><div class="gram-section-title">🎯 Consistency Issues (${consistencyIssues.length})</div>`;
        for (const ci of consistencyIssues) {
            html += `<div class="gram-issue">
                <div class="gram-issue-header">
                    <span class="gram-issue-type">${_esc(ci.issue || ci.type?.replace(/_/g, ' ') || 'Consistency')}</span>
                    ${ci.severity ? `<span class="wc-badge wc-badge-${ci.severity === 'high' ? 'error' : 'warning'}">${ci.severity}</span>` : ''}
                </div>
                ${ci.original_text ? `<p class="gram-issue-text">"${_esc(truncateText(ci.original_text, 150))}"</p>` : ''}
                ${ci.suggestion ? `<p class="gram-issue-fix">💡 ${_esc(ci.suggestion)}</p>` : ''}
                ${ci.explanation ? `<p class="text-xs text-muted mt-sm">${_esc(ci.explanation)}</p>` : ''}
            </div>`;
        }
        html += '</div>';
    }

    // No issues at all
    if (totalGrammar === 0 && longSentences.length === 0 && repeatedWords.length === 0 && consistencyIssues.length === 0) {
        html += `<div style="text-align:center;padding:48px 0"><div style="font-size:3rem;margin-bottom:8px">✅</div><p class="font-semibold" style="font-size:1.1rem">No Grammar Issues Found!</p><p class="text-muted text-sm">Your text looks great.</p></div>`;
    }

    html += '</div>';
    return html;
}


// ═══════════════════════════════════════════════════════════
//  TAB 3 — STYLE & TONE
// ═══════════════════════════════════════════════════════════

function renderStyleTone() {
    let html = '<div class="animate-fade-in">';

    // ── Tone Analysis ──
    const tone = analysisResults.tone_analysis;
    if (tone && !tone.error) {
        const scores   = tone.tone_scores || {};
        const dominant = tone.dominant_tone || 'professional';
        const label    = tone.tone_label || dominant;
        const desc     = tone.tone_description || '';
        const color    = tone.tone_color || '#3B82F6';
        const defs     = tone.tone_definitions || {};
        const perSent  = tone.per_sentence || [];

        // Dominant badge
        html += `<div class="wc-card mb-md"><div class="wc-card-body">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
                <div><h3 style="font-size:1.05rem;font-weight:600;display:flex;align-items:center;gap:8px">🎭 Tone Analysis</h3>
                <p class="text-sm text-muted mt-sm">${_esc(desc)}</p></div>
                <span class="tone-dominant" style="background:${color}">${_esc(label)}</span>
            </div>
            <div class="tone-meter">`;

        for (const key of Object.keys(scores)) {
            const val = scores[key] || 0;
            const pct = Math.round(val * 100);
            const def = defs[key] || {};
            const c   = def.color || '#6B7280';
            html += `<div class="tone-bar-row">
                <span class="tone-bar-label">${def.label || key}</span>
                <div class="tone-bar-track"><div class="tone-bar-fill" style="width:${pct}%;background:${c}"></div></div>
                <span class="tone-bar-value" style="color:${c}">${pct}%</span>
            </div>`;
        }
        html += '</div></div></div>';

        // Per-sentence trajectory
        if (perSent.length > 0) {
            const toneKeys = Object.keys(scores);
            html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>📈 Tone Trajectory</h3></div><div class="wc-card-body" style="max-height:300px;overflow-y:auto">`;
            for (let i = 0; i < perSent.length; i++) {
                const s = perSent[i];
                const sDef = defs[s.dominant] || {};
                const sColor = sDef.color || '#6B7280';
                html += `<div style="display:flex;align-items:flex-start;gap:10px;padding:6px 0;border-bottom:1px solid var(--wc-border-light)">
                    <span style="flex-shrink:0;width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.7rem;font-weight:700;color:#fff;background:${sColor}">${i + 1}</span>
                    <div style="flex:1;min-width:0"><p class="text-sm" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${_esc(truncateText(s.text, 120))}</p>
                    <span class="text-xs font-semibold" style="color:${sColor}">${sDef.label || s.dominant}</span></div>
                    <div style="display:flex;gap:2px;flex-shrink:0">
                        ${toneKeys.map(k => {
                            const sv = s.scores[k] || 0;
                            const sc = (defs[k] || {}).color || '#E5E7EB';
                            return `<div style="width:3px;height:20px;border-radius:2px;background:${sc};opacity:${Math.max(0.15, sv)}" title="${k}: ${(sv*100).toFixed(0)}%"></div>`;
                        }).join('')}
                    </div>
                </div>`;
            }
            html += '</div></div>';
        }

        // Tone transformation
        const tt = tone.tone_transformation;
        if (tt && tt.transformed && tt.change_count > 0) {
            html += `<div class="wc-card wc-card-accent mb-md"><div class="wc-card-header"><h3>🔄 Tone Transformation → ${_esc(tt.tone_label || tt.target_tone)}</h3><span class="wc-badge wc-badge-primary">${tt.change_count} changes</span></div>
            <div class="wc-card-body"><div class="diff-panel diff-panel-new" style="white-space:pre-wrap">${_esc(tt.transformed)}</div>
            ${tt.changes?.length ? `<div class="mt-md" style="font-size:0.82rem">${tt.changes.slice(0, 10).map(c => `<div class="text-sm"><s style="color:var(--wc-error)">${_esc(c.original)}</s> → <strong style="color:var(--wc-success)">${_esc(c.replacement)}</strong></div>`).join('')}</div>` : ''}
            </div></div>`;
        }
    }

    // ── Style Analysis ──
    const sa = analysisResults.style_analysis;
    if (sa) {
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>✍️ Writing Style</h3>
            <span class="wc-badge wc-badge-primary" style="text-transform:capitalize">${_esc(sa.dominant_style || '—')}</span></div>
            <div class="wc-card-body">${sa.recommendation ? `<p class="text-sm">${_esc(sa.recommendation)}</p>` : ''}
        </div></div>`;
    }

    // ── Style Transformation ──
    const st = analysisResults.style_transformation;
    if (st && st.transformed) {
        const changes = st.changes || [];
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>🔄 Style Transformation</h3>
            <span class="wc-badge wc-badge-success">${st.change_count} changes → ${_esc(st.style)}</span></div>
            <div class="wc-card-body">
                <div class="transformation-diff">
                    <div class="diff-panel diff-panel-orig"><span class="diff-label">Original</span>${_esc(st.original)}</div>
                    <div class="diff-panel diff-panel-new"><span class="diff-label">Transformed</span>${_esc(st.transformed)}</div>
                </div>
                ${changes.length > 0 ? `<div class="mt-md" style="max-height:240px;overflow-y:auto">
                    ${changes.map((c, i) => `<div style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:0.82rem;border-bottom:1px solid var(--wc-border-light)">
                        <span class="text-muted" style="width:20px;text-align:right">${i + 1}</span>
                        <span style="text-decoration:line-through;color:var(--wc-error)">${_esc(c.original)}</span>
                        <span class="text-muted">→</span>
                        <span style="color:var(--wc-success);font-weight:600">${_esc(c.replacement)}</span>
                        <span class="text-muted text-xs" style="margin-left:auto">${_esc(c.type?.replace(/_/g, ' ') || '')}</span>
                    </div>`).join('')}
                </div>` : ''}
                <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:12px">
                    <button onclick="copyOriginal()" class="wc-btn wc-btn-ghost">📋 Copy Original</button>
                    <button onclick="copyTransformed()" class="wc-btn wc-btn-primary">✨ Copy Transformed</button>
                </div>
            </div></div>`;
    }

    // ── Style Heatmap ──
    html += renderStyleHeatmap();

    // ── Sentiment ──
    const sent = analysisResults.sentiment;
    if (sent) {
        const sType  = sent.sentiment || 'neutral';
        const sScore = sent.score || 0;
        const sEmoji = { positive: '😊', negative: '😕', neutral: '😐' }[sType] || '😐';
        html += `<div class="wc-card mt-md"><div class="wc-card-header"><h3>${sEmoji} Sentiment</h3>
            <span class="wc-badge wc-badge-${sType === 'positive' ? 'success' : sType === 'negative' ? 'error' : 'muted'}" style="text-transform:capitalize">${sType} (${sScore.toFixed(2)})</span></div>
            <div class="wc-card-body"><div class="wc-stats wc-stats-2">
                <div class="wc-stat"><span class="wc-stat-value" style="color:var(--wc-success)">${sent.positive_words || 0}</span><span class="wc-stat-label">Positive Words</span></div>
                <div class="wc-stat"><span class="wc-stat-value" style="color:var(--wc-error)">${sent.negative_words || 0}</span><span class="wc-stat-label">Negative Words</span></div>
            </div></div></div>`;
    }

    if (!tone && !sa && !st && !sent) {
        html += `<div style="text-align:center;padding:48px 0"><div style="font-size:3rem;margin-bottom:8px">🎨</div><p class="font-semibold">No Style & Tone Data</p><p class="text-muted text-sm">Submit text to see style and tone analysis.</p></div>`;
    }

    html += '</div>';
    return html;
}

function renderStyleHeatmap() {
    const styleScores = analysisResults.style_scores;
    if (!styleScores || styleScores.length === 0) return '';

    const dims = ['formality','casualness','creativity','persuasiveness','journalistic','narrative'];
    const dimColors = { formality:'#3B82F6', casualness:'#10B981', creativity:'#8B5CF6', persuasiveness:'#F59E0B', journalistic:'#6366F1', narrative:'#EC4899' };
    const dimEmojis = { formality:'🏛️', casualness:'😊', creativity:'🎨', persuasiveness:'💪', journalistic:'📰', narrative:'📖' };

    let html = `<div class="wc-card mt-md"><div class="wc-card-header"><h3>🎨 Style Heatmap by Paragraph</h3></div>
        <div class="wc-card-body"><div class="style-heatmap"><table><thead><tr><th style="text-align:left">Para</th>`;
    for (const d of dims) html += `<th>${dimEmojis[d]}<br><span style="font-size:0.65rem">${d.charAt(0).toUpperCase()+d.slice(1)}</span></th>`;
    html += '</tr></thead><tbody>';
    for (let i = 0; i < styleScores.length; i++) {
        const para = styleScores[i];
        html += `<tr><td title="${_esc(para.text_preview)}"><span class="font-semibold text-muted">P${i+1}</span> ${_esc(truncateText(para.text_preview, 40))}</td>`;
        for (const d of dims) {
            const score = para.scores[d] || 0;
            const opacity = Math.max(0.1, score / 100);
            html += `<td><span class="hm-cell" style="background:${dimColors[d]}${Math.round(opacity*255).toString(16).padStart(2,'0')};color:${score > 50 ? '#fff' : 'var(--wc-text)'}">${score}</span></td>`;
        }
        html += '</tr>';
    }
    html += '</tbody></table></div><p class="text-xs text-muted mt-sm">Higher scores = stronger presence of that style (0-100)</p></div></div>';
    return html;
}


// ═══════════════════════════════════════════════════════════
//  TAB 4 — NARRATIVE
// ═══════════════════════════════════════════════════════════

function renderNarrative() {
    const nt = analysisResults.narrative_tracker;
    if (!nt || nt.error) {
        return `<div style="text-align:center;padding:48px 0" class="animate-fade-in">
            <div style="font-size:3rem;margin-bottom:8px">📖</div>
            <p class="font-semibold">Narrative tracking data not available</p>
            <p class="text-sm text-muted">${nt?.error || 'Submit text to generate narrative analysis'}</p></div>`;
    }

    let html = '<div class="animate-fade-in">';
    const summary = nt.narrative_timeline?.summary || {};

    // Summary cards
    html += `<div class="nar-cards">
        ${_narCard('📝','Events',summary.total_events ?? 0)}
        ${_narCard('👤','Characters',summary.unique_characters ?? 0)}
        ${_narCard('📍','Locations',summary.unique_locations ?? 0)}
        ${_narCard('💬','Dialogue',nt.dialogue?.total_quotes ?? 0)}
        ${_narCard('⏱️','Pace',nt.pacing?.pace_score ?? '—')}
    </div>`;

    // Pacing
    if (nt.pacing) {
        const p = nt.pacing;
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>⏱️ Pacing Analysis</h3></div><div class="wc-card-body">
            <p class="text-sm mb-md">${_esc(p.interpretation || '')}</p>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">`;
        for (const [type, ratio] of Object.entries(p.ratios || {})) {
            const pct = (ratio * 100).toFixed(1);
            html += `<div><div style="display:flex;justify-content:space-between;font-size:0.72rem;margin-bottom:4px"><span style="text-transform:capitalize">${type}</span><span>${pct}%</span></div>
            <div style="height:6px;background:var(--wc-border-light);border-radius:3px;overflow:hidden"><div style="height:100%;width:${pct}%;background:var(--wc-primary);border-radius:3px"></div></div></div>`;
        }
        html += `</div><p class="text-xs text-muted mt-sm">Avg block length: ${p.avg_block_length ?? '—'} sentences</p></div></div>`;
    }

    // Dialogue
    if (nt.dialogue && nt.dialogue.total_quotes > 0) {
        const d = nt.dialogue;
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>💬 Dialogue</h3></div><div class="wc-card-body">
            <div style="display:flex;gap:24px;font-size:0.84rem;margin-bottom:12px">
                <span>Dialogue: <strong>${(d.dialogue_ratio*100).toFixed(1)}%</strong></span>
                <span>Narration: <strong>${(d.narration_ratio*100).toFixed(1)}%</strong></span>
            </div>`;
        if (Object.keys(d.speaker_lines || {}).length > 0) {
            html += '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px">';
            for (const [sp, cnt] of Object.entries(d.speaker_lines)) html += `<span class="nar-char-badge">${_esc(sp)}: ${cnt}</span>`;
            html += '</div>';
        }
        if (d.quotes?.length > 0) {
            html += '<div style="max-height:200px;overflow-y:auto">';
            for (const q of d.quotes.slice(0, 15)) html += `<div class="nar-quote"><span class="nar-quote-text">"${_esc(q.content)}"</span>${q.speaker ? `<span class="nar-quote-speaker">— ${_esc(q.speaker)}</span>` : ''}</div>`;
            if (d.quotes.length > 15) html += `<p class="text-xs text-muted">+${d.quotes.length-15} more</p>`;
            html += '</div>';
        }
        html += '</div></div>';
    }

    // Plot Events
    if (nt.plot_events?.length > 0) {
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>📝 Plot Events</h3><span class="wc-badge wc-badge-muted">${nt.plot_events.length}</span></div>
        <div class="wc-card-body" style="max-height:240px;overflow-y:auto">`;
        for (const ev of nt.plot_events.slice(0, 20)) {
            html += `<div class="nar-event"><span class="nar-event-idx">#${ev.sentence_index}</span>
                <span class="font-semibold" style="color:var(--wc-primary)">${_esc(ev.subject || '?')}</span>
                <span>→ <em>${_esc(ev.verb_text)}</em></span>
                ${ev.tense ? `<span class="wc-badge wc-badge-muted">${ev.tense}</span>` : ''}</div>`;
        }
        if (nt.plot_events.length > 20) html += `<p class="text-xs text-muted">+${nt.plot_events.length-20} more</p>`;
        html += '</div></div>';
    }

    // Settings / Locations
    if (nt.settings?.length > 0) {
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>📍 Settings & Locations</h3></div>
        <div class="wc-card-body" style="max-height:200px;overflow-y:auto">`;
        for (const s of nt.settings) {
            const locs = (s.locations || []).map(l => `<span class="entity-tag entity-${l.type?.toLowerCase()}">${_esc(l.text)}</span>`).join(' ');
            html += `<div class="text-sm mb-sm"><span class="text-muted" style="margin-right:6px">#${s.sentence_index}</span>${locs}</div>`;
        }
        html += '</div></div>';
    }

    // Timeline
    if (nt.narrative_timeline?.timeline?.length > 0) {
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>🗺️ Narrative Timeline</h3></div>
        <div class="wc-card-body" style="max-height:280px;overflow-y:auto">`;
        for (const entry of nt.narrative_timeline.timeline.slice(0, 30)) {
            html += `<div style="display:flex;gap:10px;font-size:0.82rem;border-left:2px solid var(--wc-primary-light);padding:6px 0 6px 12px;margin-bottom:4px">
                <span class="text-muted" style="width:24px;text-align:right;flex-shrink:0">#${entry.sentence_index}</span><div>`;
            if (entry.characters) html += `<div>👤 ${entry.characters.map(c => `<strong style="color:var(--wc-primary)">${_esc(c)}</strong>`).join(', ')}</div>`;
            if (entry.events) html += `<div>⚡ ${entry.events.map(e => `${_esc(e.subject||'?')} → <em>${_esc(e.verb)}</em>`).join('; ')}</div>`;
            if (entry.locations) html += `<div>📍 ${entry.locations.map(l => _esc(l.text)).join(', ')}</div>`;
            if (entry.has_dialogue) html += '<div style="color:var(--wc-primary);font-size:0.72rem">💬 dialogue</div>';
            html += '</div></div>';
        }
        if (nt.narrative_timeline.timeline.length > 30) html += `<p class="text-xs text-muted">+${nt.narrative_timeline.timeline.length-30} more</p>`;
        html += '</div></div>';
    }

    // Character Memory
    if (nt.character_memory && Object.keys(nt.character_memory).length > 0) {
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>🧠 Character Memory</h3></div>
        <div class="wc-card-body"><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px">`;
        for (const [, data] of Object.entries(nt.character_memory)) {
            html += `<div class="wc-stat" style="text-align:left;padding:12px">
                <span class="font-semibold">${_esc(data.canonical_name)}</span>
                <span class="wc-stat-label">${data.type} · ${data.mention_count} mention${data.mention_count!==1?'s':''}</span>
                <span class="text-xs text-muted">First: sentence #${data.first_mention_sentence ?? '?'}</span>
            </div>`;
        }
        html += '</div></div></div>';
    }

    html += '</div>';
    return html;
}

function _narCard(emoji, label, value) {
    return `<div class="nar-card"><div class="nar-card-icon">${emoji}</div><div class="nar-card-value">${value}</div><div class="nar-card-label">${label}</div></div>`;
}


// ═══════════════════════════════════════════════════════════
//  TAB 5 — INSIGHTS (Mind Map + Readability + Stats)
// ═══════════════════════════════════════════════════════════

const MIND_MAP_GROUP_META = {
    character:    { label: 'Characters',    icon: '👤', color: '#3B82F6' },
    organization: { label: 'Organizations', icon: '🏢', color: '#6366F1' },
    location:     { label: 'Locations',     icon: '📍', color: '#10B981' },
    time:         { label: 'Time',          icon: '🕐', color: '#F59E0B' },
    event:        { label: 'Events',        icon: '⚡', color: '#EC4899' },
    theme:        { label: 'Themes',        icon: '💡', color: '#F59E0B' },
    action:       { label: 'Actions',       icon: '🎯', color: '#EF4444' },
    detail:       { label: 'Details',       icon: '📎', color: '#94A3B8' },
    concept:      { label: 'Concepts',      icon: '🔮', color: '#8B5CF6' },
    other:        { label: 'Other',         icon: '📌', color: '#CBD5E1' },
};
let mindMapVisibleGroups = new Set(Object.keys(MIND_MAP_GROUP_META));
let mindMapNetworkInstance = null;

function renderInsights() {
    let html = '<div class="animate-fade-in">';

    // ── Mind Map ──
    const mapData = analysisResults.mind_map;
    if (mapData && !mapData.error && mapData.nodes?.length > 0) {
        const { nodes, edges, central_node, stats } = mapData;
        const groupCounts = {};
        for (const n of nodes) groupCounts[n.group] = (groupCounts[n.group] || 0) + 1;

        let legendHtml = '<div class="mm-legend">';
        for (const [grp, meta] of Object.entries(MIND_MAP_GROUP_META)) {
            const c = groupCounts[grp] || 0;
            if (c === 0) continue;
            const active = mindMapVisibleGroups.has(grp);
            legendHtml += `<button class="mm-legend-btn ${active ? 'active' : 'inactive'}" data-group="${grp}" style="--grp-color:${meta.color}"><span class="mm-legend-dot" style="background:${meta.color}"></span><span>${meta.icon} ${meta.label}</span><span class="mm-legend-count">${c}</span></button>`;
        }
        legendHtml += '</div>';

        let conceptListHtml = '<div class="mm-concept-list"><h4 class="mm-concept-list-title">Key Concepts</h4>';
        const sortedNodes = [...nodes].sort((a, b) => b.importance - a.importance);
        for (const n of sortedNodes) {
            const meta = MIND_MAP_GROUP_META[n.group] || MIND_MAP_GROUP_META.other;
            conceptListHtml += `<div class="mm-concept-item" data-node-id="${n.id}" title="${_esc(n.label)} (${n.type})">
                <div class="mm-concept-icon" style="color:${meta.color}">${meta.icon}</div>
                <div class="mm-concept-info"><div class="mm-concept-name">${_esc(n.label)}</div>
                <div class="mm-concept-bar-track"><div class="mm-concept-bar" style="width:${Math.max(4,n.importance)}%;background:${meta.color}"></div></div></div>
                <div class="mm-concept-score">${n.importance}</div>
            </div>`;
        }
        conceptListHtml += '</div>';

        html += `<div class="mm-container">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
                <h3 style="font-size:1.05rem;font-weight:600;display:flex;align-items:center;gap:8px">🧠 Concept Mind Map</h3>
                <div style="display:flex;gap:6px">
                    <button id="mm-btn-fit" class="mm-toolbar-btn">⊞ Fit</button>
                    <button id="mm-btn-physics" class="mm-toolbar-btn">⚛️ Physics</button>
                </div>
            </div>
            <div class="mm-stats"><span>🧠 <strong>${stats.total_nodes}</strong> concepts</span><span class="mm-stats-sep">·</span><span>🔗 <strong>${stats.total_edges}</strong> connections</span><span class="mm-stats-sep">·</span><span>⭐ Central: <strong>${_esc(central_node || '—')}</strong></span></div>
            ${legendHtml}
            <div class="mm-layout">
                <div class="mm-graph-wrap">
                    <div id="mm-network" class="mm-network"></div>
                    <div class="mm-hint">Drag to pan · Scroll to zoom · Click node to highlight</div>
                </div>
                ${conceptListHtml}
            </div>
        </div>`;
    }

    // ── Readability & Stats Grid ──
    const rd = analysisResults.readability;
    const ps = analysisResults.paragraph_structure;
    const ld = analysisResults.lexical_density;
    const sr = analysisResults.sentence_rhythm;
    const vc = analysisResults.vocabulary_complexity;
    const fl = analysisResults.flow;

    html += '<div class="ins-grid mt-lg">';

    // Readability
    if (rd) {
        html += `<div class="wc-card"><div class="wc-card-header"><h3>📖 Readability</h3></div><div class="wc-card-body">
            <div class="ins-readability">
                <div class="ins-read-item"><span class="ins-read-label">Grade Level</span><span class="ins-read-value">${rd.grade_level || '—'}</span></div>
                <div class="ins-read-item"><span class="ins-read-label">Difficulty</span><span class="ins-read-value" style="text-transform:capitalize">${rd.difficulty || '—'}</span></div>
                <div class="ins-read-item"><span class="ins-read-label">Reading Time</span><span class="ins-read-value">${rd.reading_time_minutes || 0} min</span></div>
                <div class="ins-read-item"><span class="ins-read-label">Flesch Score</span><span class="ins-read-value">${rd.scores?.flesch_reading_ease?.toFixed(1) || '—'}</span></div>
            </div>
            ${rd.interpretation ? `<p class="text-sm text-muted mt-sm">${_esc(rd.interpretation)}</p>` : ''}
        </div></div>`;
    }

    // Flow
    if (fl) {
        html += `<div class="wc-card"><div class="wc-card-header"><h3>🌊 Flow</h3><span class="wc-badge wc-badge-primary">${fl.flow_score?.toFixed(0) || 0}/100</span></div><div class="wc-card-body">
            <div class="wc-stats wc-stats-2 mb-sm">
                <div class="wc-stat"><span class="wc-stat-value">${fl.transition_count || 0}</span><span class="wc-stat-label">Transitions</span></div>
                <div class="wc-stat"><span class="wc-stat-value">${fl.sentence_variety_score?.toFixed(0) || '—'}</span><span class="wc-stat-label">Variety Score</span></div>
            </div>
            ${fl.assessment ? `<p class="text-sm text-muted">${_esc(fl.assessment)}</p>` : ''}
        </div></div>`;
    }

    // Vocabulary Complexity
    if (vc) {
        html += `<div class="wc-card"><div class="wc-card-header"><h3>📚 Vocabulary</h3></div><div class="wc-card-body">
            <div class="wc-stats wc-stats-3">
                <div class="wc-stat"><span class="wc-stat-value">${((vc.lexical_diversity || 0)*100).toFixed(0)}%</span><span class="wc-stat-label">Diversity</span></div>
                <div class="wc-stat"><span class="wc-stat-value" style="text-transform:capitalize">${vc.complexity_level || '—'}</span><span class="wc-stat-label">Level</span></div>
                <div class="wc-stat"><span class="wc-stat-value">${vc.advanced_words || 0}</span><span class="wc-stat-label">Advanced</span></div>
            </div>
            ${vc.interpretation ? `<p class="text-sm text-muted mt-sm">${_esc(vc.interpretation)}</p>` : ''}
        </div></div>`;
    }

    // Paragraph Structure
    if (ps) {
        html += `<div class="wc-card"><div class="wc-card-header"><h3>📄 Paragraph Structure</h3></div><div class="wc-card-body">
            <div class="wc-stats wc-stats-2">
                <div class="wc-stat"><span class="wc-stat-value">${ps.paragraph_count || 0}</span><span class="wc-stat-label">Paragraphs</span></div>
                <div class="wc-stat"><span class="wc-stat-value">${(ps.average_words_per_paragraph || 0).toFixed(0)}</span><span class="wc-stat-label">Avg Words</span></div>
            </div>
            ${ps.interpretation ? `<p class="text-sm text-muted mt-sm">${_esc(ps.interpretation)}</p>` : ''}
        </div></div>`;
    }

    // Lexical Density
    if (ld) {
        html += `<div class="wc-card"><div class="wc-card-header"><h3>📊 Lexical Density</h3><span class="wc-badge wc-badge-primary">${((ld.lexical_density||0)*100).toFixed(1)}%</span></div><div class="wc-card-body">
            <div class="wc-stats wc-stats-2">
                <div class="wc-stat"><span class="wc-stat-value">${ld.content_words || 0}</span><span class="wc-stat-label">Content Words</span></div>
                <div class="wc-stat"><span class="wc-stat-value">${ld.total_words || 0}</span><span class="wc-stat-label">Total Words</span></div>
            </div>
            ${ld.interpretation ? `<p class="text-sm text-muted mt-sm">${_esc(ld.interpretation)}</p>` : ''}
        </div></div>`;
    }

    // Sentence Rhythm
    if (sr) {
        html += `<div class="wc-card"><div class="wc-card-header"><h3>🎵 Sentence Rhythm</h3></div><div class="wc-card-body">
            <div class="wc-stats wc-stats-2">
                <div class="wc-stat"><span class="wc-stat-value" style="text-transform:capitalize">${sr.pattern || '—'}</span><span class="wc-stat-label">Pattern</span></div>
                <div class="wc-stat"><span class="wc-stat-value">${(sr.rhythm_score || 0).toFixed(0)}</span><span class="wc-stat-label">Rhythm Score</span></div>
            </div>
            ${sr.interpretation ? `<p class="text-sm text-muted mt-sm">${_esc(sr.interpretation)}</p>` : ''}
        </div></div>`;
    }

    html += '</div>'; // close ins-grid

    // ── Named Entities ──
    const ta = analysisResults.text_analysis;
    if (ta?.entities?.length > 0) {
        html += `<div class="wc-card mt-md"><div class="wc-card-header"><h3>🏷️ Named Entities</h3><span class="wc-badge wc-badge-muted">${ta.entities.length}</span></div>
        <div class="wc-card-body" style="display:flex;flex-wrap:wrap;gap:6px">`;
        for (const [text, label] of ta.entities.slice(0, 25)) {
            html += `<span class="entity-tag entity-${label}">${_esc(text)} <span style="opacity:0.6;font-size:0.68rem">(${label})</span></span>`;
        }
        if (ta.entities.length > 25) html += `<span class="text-sm text-muted">+${ta.entities.length-25} more</span>`;
        html += '</div></div>';
    }

    html += '</div>';
    return html;
}

function initMindMapNetwork() {
    const container = document.getElementById('mm-network');
    if (!container) return;
    const mapData = analysisResults.mind_map;
    if (!mapData || !mapData.nodes || mapData.nodes.length === 0) return;

    const visibleNodes = mapData.nodes.filter(n => mindMapVisibleGroups.has(n.group));
    const visibleIds = new Set(visibleNodes.map(n => n.id));
    const visibleEdges = mapData.edges.filter(e => visibleIds.has(e.from) && visibleIds.has(e.to));

    const nodesData = visibleNodes.map(n => ({
        id: n.id, label: n.label, size: n.size,
        color: { background: n.color.background, border: n.color.border, highlight: { background: n.color.background, border: '#1E293B' }, hover: { background: n.color.background, border: '#1E293B' } },
        font: { size: n.font_size, color: n.color.fontColor || '#ffffff', strokeWidth: 2, strokeColor: 'rgba(0,0,0,0.3)', face: "'Inter', system-ui, sans-serif", bold: n.is_central ? { color: n.color.fontColor || '#ffffff', size: n.font_size + 2 } : undefined },
        shape: n.is_central ? 'star' : 'dot', borderWidth: n.is_central ? 3 : 2,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.15)', size: 8, x: 2, y: 2 },
        title: `${n.label}\nType: ${n.type}\nImportance: ${n.importance}%`,
    }));

    const edgesData = visibleEdges.map((e, i) => ({
        id: i, from: e.from, to: e.to,
        label: e.label.length > 18 ? e.label.slice(0, 16) + '…' : e.label, width: e.width,
        color: { color: '#94A3B8', highlight: '#3B82F6', hover: '#64748B' },
        font: { size: 9, color: '#64748B', strokeWidth: 0, align: 'middle', face: 'system-ui' },
        arrows: { to: { enabled: false } },
        smooth: { type: 'continuous', roundness: 0.3 },
    }));

    const options = {
        physics: { enabled: true, solver: 'forceAtlas2Based', forceAtlas2Based: { gravitationalConstant: -40, centralGravity: 0.008, springLength: 140, springConstant: 0.04, damping: 0.4, avoidOverlap: 0.6 }, stabilization: { iterations: 200, updateInterval: 25 } },
        interaction: { hover: true, tooltipDelay: 200, zoomView: true, dragView: true, dragNodes: true, navigationButtons: false, keyboard: false },
        layout: { improvedLayout: true, randomSeed: 42 },
        nodes: { shape: 'dot', scaling: { min: 15, max: 55 } },
        edges: { smooth: { type: 'continuous' } },
    };

    if (mindMapNetworkInstance) { mindMapNetworkInstance.destroy(); mindMapNetworkInstance = null; }
    const network = new vis.Network(container, { nodes: nodesData, edges: edgesData }, options);
    mindMapNetworkInstance = network;

    network.on('selectNode', (params) => {
        const nodeId = params.nodes[0];
        document.querySelectorAll('.mm-concept-item').forEach(el => el.classList.toggle('mm-concept-active', parseInt(el.dataset.nodeId) === nodeId));
        network.selectEdges(network.getConnectedEdges(nodeId));
    });
    network.on('deselectNode', () => {
        document.querySelectorAll('.mm-concept-item').forEach(el => el.classList.remove('mm-concept-active'));
    });

    document.querySelectorAll('.mm-legend-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const grp = btn.dataset.group;
            mindMapVisibleGroups.has(grp) ? mindMapVisibleGroups.delete(grp) : mindMapVisibleGroups.add(grp);
            elements.tabContent.innerHTML = renderInsights();
            setTimeout(() => initMindMapNetwork(), 60);
        });
    });

    document.querySelectorAll('.mm-concept-item').forEach(el => {
        el.addEventListener('click', () => {
            const nodeId = parseInt(el.dataset.nodeId);
            network.selectNodes([nodeId]);
            network.focus(nodeId, { scale: 1.2, animation: { duration: 400, easingFunction: 'easeInOutQuad' } });
            document.querySelectorAll('.mm-concept-item').forEach(e => e.classList.remove('mm-concept-active'));
            el.classList.add('mm-concept-active');
        });
    });

    const fitBtn = document.getElementById('mm-btn-fit');
    const physicsBtn = document.getElementById('mm-btn-physics');
    if (fitBtn) fitBtn.addEventListener('click', () => network.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } }));
    let physicsOn = true;
    if (physicsBtn) physicsBtn.addEventListener('click', () => {
        physicsOn = !physicsOn;
        network.setOptions({ physics: { enabled: physicsOn } });
        physicsBtn.textContent = physicsOn ? '⚛️ Physics' : '📌 Locked';
    });
    network.once('stabilizationIterationsDone', () => network.fit({ animation: { duration: 300, easingFunction: 'easeInOutQuad' } }));
}


// ═══════════════════════════════════════════════════════════
//  TAB 6 — ANTI-PATTERNS
// ═══════════════════════════════════════════════════════════

const AP_CATEGORY_META = {
    adverb_overuse:      { label: 'Adverb Overuse',     icon: '📝', color: '#F59E0B' },
    show_dont_tell:      { label: "Show Don't Tell",    icon: '🎭', color: '#EC4899' },
    nominalizations:     { label: 'Nominalizations',    icon: '📦', color: '#8B5CF6' },
    hedge_words:         { label: 'Hedge Words',        icon: '🌫️', color: '#6366F1' },
    redundant_modifiers: { label: 'Redundant Modifiers', icon: '♻️', color: '#EF4444' },
    weak_openings:       { label: 'Weak Openings',      icon: '🚪', color: '#F97316' },
    filter_words:        { label: 'Filter Words',       icon: '🔍', color: '#14B8A6' },
    info_dumps:          { label: 'Info Dumps',          icon: '📚', color: '#64748B' },
};
const _SEV_COLORS = {
    critical: { badge: '#EF4444' },
    moderate: { badge: '#F59E0B' },
    minor:    { badge: '#22C55E' },
};

function renderAntiPatterns() {
    const ap = analysisResults.antipatterns;
    if (!ap || ap.error || !ap.categories) {
        return `<div style="text-align:center;padding:48px 0" class="animate-fade-in">
            <div style="font-size:3rem;margin-bottom:8px">🚫</div>
            <p class="font-semibold">No Anti-Pattern Data</p>
            <p class="text-sm text-muted">Submit text to detect writing anti-patterns.</p>
            ${ap?.error ? `<p class="text-xs" style="color:var(--wc-error);margin-top:12px">Error: ${_esc(ap.error)}</p>` : ''}
        </div>`;
    }

    const { categories, summary } = ap;

    let summaryHtml = `<div class="ap-summary-bar">
        <span class="ap-summary-label">Anti-Patterns Found:</span>
        ${summary.critical > 0 ? `<span class="ap-sev-chip ap-sev-critical">${summary.critical} critical</span>` : ''}
        ${summary.moderate > 0 ? `<span class="ap-sev-chip ap-sev-moderate">${summary.moderate} moderate</span>` : ''}
        ${summary.minor > 0 ? `<span class="ap-sev-chip ap-sev-minor">${summary.minor} minor</span>` : ''}
        ${summary.total === 0 ? '<span style="color:var(--wc-success);font-weight:600">✅ No anti-patterns detected!</span>' : ''}
        <span class="ap-summary-total">${summary.total} total</span>
    </div>`;

    let cardsHtml = '';
    for (const [catKey, catData] of Object.entries(categories)) {
        const meta = AP_CATEGORY_META[catKey] || { label: catKey, icon: '📌', color: '#94A3B8' };
        const count = catData.count || 0;
        const expanded = count > 0;

        let instancesHtml = '';
        if (count > 0) {
            instancesHtml = '<div class="ap-instances">';
            for (const inst of catData.instances) {
                const sev = _SEV_COLORS[inst.severity] || _SEV_COLORS.minor;
                instancesHtml += `<div class="ap-instance" style="border-left-color:${sev.badge}">
                    <div class="ap-inst-header">
                        <span class="ap-sev-dot" style="background:${sev.badge}"></span>
                        <span class="ap-inst-text">${_esc(inst.text)}</span>
                        <span class="ap-inst-sev" style="color:${sev.badge}">${inst.severity}</span>
                    </div>
                    <p class="ap-inst-location">${_esc(inst.location)}</p>
                    <p class="ap-inst-suggestion">💡 ${_esc(inst.suggestion)}</p>
                    ${inst.before_after_example ? `<div class="ap-before-after">
                        <div class="ap-ba-bad"><span class="ap-ba-label">✗ Before</span><span class="ap-ba-text">${_esc(inst.before_after_example.before)}</span></div>
                        <span class="ap-ba-arrow">→</span>
                        <div class="ap-ba-good"><span class="ap-ba-label">✓ After</span><span class="ap-ba-text">${_esc(inst.before_after_example.after)}</span></div>
                    </div>` : ''}
                </div>`;
            }
            instancesHtml += '</div>';
        }

        cardsHtml += `<div class="ap-card ${count === 0 ? 'ap-card-clean' : ''}">
            <div class="ap-card-header" data-ap-toggle="${catKey}">
                <div class="ap-card-title">
                    <span class="ap-card-icon" style="color:${meta.color}">${meta.icon}</span>
                    <span>${meta.label}</span>
                    <span class="ap-card-count" style="background:${count > 0 ? meta.color : '#CBD5E1'}">${count}</span>
                </div>
                <div class="ap-card-right">
                    ${catData.educational_tip ? `<span class="ap-learn-more" title="${_esc(catData.educational_tip)}">📖 Learn</span>` : ''}
                    <span class="ap-card-chevron ${expanded && count > 0 ? 'ap-open' : ''}">${count > 0 ? '▾' : '—'}</span>
                </div>
            </div>
            ${catData.educational_tip && count > 0 ? `<div class="ap-tip">${_esc(catData.educational_tip)}</div>` : ''}
            <div class="ap-card-body ${count > 0 ? 'ap-expanded' : 'ap-collapsed'}" id="ap-body-${catKey}">${instancesHtml}</div>
        </div>`;
    }

    return `<div class="ap-container animate-fade-in">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
            <h3 style="font-size:1.05rem;font-weight:600;display:flex;align-items:center;gap:8px">🚫 Writing Anti-Patterns</h3>
            <div style="display:flex;gap:6px">
                <button id="ap-expand-all" class="ap-toolbar-btn">▸ Expand All</button>
                <button id="ap-collapse-all" class="ap-toolbar-btn">▾ Collapse All</button>
            </div>
        </div>
        ${summaryHtml}
        <div class="ap-cards">${cardsHtml}</div>
    </div>`;
}

function bindAntiPatternEvents() {
    document.querySelectorAll('[data-ap-toggle]').forEach(header => {
        header.addEventListener('click', () => {
            const catKey = header.dataset.apToggle;
            const body = document.getElementById('ap-body-' + catKey);
            const chevron = header.querySelector('.ap-card-chevron');
            if (!body) return;
            const isExpanded = body.classList.contains('ap-expanded');
            body.classList.toggle('ap-expanded', !isExpanded);
            body.classList.toggle('ap-collapsed', isExpanded);
            if (chevron) { chevron.classList.toggle('ap-open', !isExpanded); chevron.textContent = isExpanded ? '▸' : '▾'; }
        });
    });
    const expandBtn = document.getElementById('ap-expand-all');
    const collapseBtn = document.getElementById('ap-collapse-all');
    if (expandBtn) expandBtn.addEventListener('click', () => {
        document.querySelectorAll('.ap-card-body').forEach(b => { b.classList.remove('ap-collapsed'); b.classList.add('ap-expanded'); });
        document.querySelectorAll('.ap-card-chevron').forEach(c => { c.classList.add('ap-open'); c.textContent = '▾'; });
    });
    if (collapseBtn) collapseBtn.addEventListener('click', () => {
        document.querySelectorAll('.ap-card-body').forEach(b => { b.classList.remove('ap-expanded'); b.classList.add('ap-collapsed'); });
        document.querySelectorAll('.ap-card-chevron').forEach(c => { c.classList.remove('ap-open'); c.textContent = '▸'; });
    });
}


// ═══════════════════════════════════════════════════════════
//  TAB 7 — IMPROVE (Suggestions + Enhanced Features)
// ═══════════════════════════════════════════════════════════

function renderImprove() {
    let html = '<div class="animate-fade-in">';

    // ── Enhanced Features Quick Cards ──
    const pv = analysisResults.passive_voice;
    const fw = analysisResults.filler_words;
    const cl = analysisResults.cliches;

    const pvCount = pv?.passive_count || 0;
    const fwCount = fw?.total_fillers || 0;
    const clCount = cl?.cliches_found || 0;

    html += `<div class="imp-feat-grid mb-md">
        <div class="imp-feat"><div class="imp-feat-icon">🎯</div><div class="imp-feat-value">${pvCount}</div><div class="imp-feat-label">Passive Voice</div></div>
        <div class="imp-feat"><div class="imp-feat-icon">🗑️</div><div class="imp-feat-value">${fwCount}</div><div class="imp-feat-label">Filler Words</div></div>
        <div class="imp-feat"><div class="imp-feat-icon">💭</div><div class="imp-feat-value">${clCount}</div><div class="imp-feat-label">Clichés</div></div>
    </div>`;

    // ── Prioritized Suggestions ──
    const suggestions = analysisResults.suggestions || [];
    const explSuggestions = analysisResults.explanations?.suggestions || [];
    const allSuggestions = [...suggestions, ...explSuggestions];

    if (allSuggestions.length > 0) {
        const byPriority = { high: [], medium: [], low: [] };
        allSuggestions.forEach(s => { const p = s.priority || 'medium'; if (byPriority[p]) byPriority[p].push(s); });

        for (const [priority, items] of Object.entries(byPriority)) {
            if (items.length === 0) continue;
            html += `<div class="imp-section"><div class="imp-section-title">
                <span class="imp-priority imp-priority-${priority}">${priority === 'high' ? '🔴' : priority === 'medium' ? '🟡' : '🟢'} ${priority.toUpperCase()}</span>
                Priority (${items.length})
            </div>`;
            for (const sug of items) {
                html += `<div class="imp-item">
                    <div class="imp-item-header">
                        <span class="imp-item-action">${_esc(sug.action || sug.suggestion)}</span>
                        <span class="wc-badge wc-badge-muted">${_esc(sug.category)}</span>
                    </div>
                    ${sug.impact ? `<p class="imp-item-impact">📈 ${_esc(sug.impact)}</p>` : ''}
                    ${sug.how_to ? `<div class="imp-item-howto">ℹ️ ${_esc(sug.how_to)}</div>` : ''}
                </div>`;
            }
            html += '</div>';
        }
    }

    // ── Passive Voice Detail ──
    if (pv && pvCount > 0) {
        const instances = pv.passive_instances || [];
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>🎯 Passive Voice Instances</h3>
            <span class="wc-badge wc-badge-warning">${pvCount} found (${(pv.passive_percentage || 0).toFixed(1)}%)</span></div>
            <div class="wc-card-body" style="max-height:240px;overflow-y:auto">`;
        for (const inst of instances.slice(0, 8)) {
            html += `<div class="gram-issue"><div class="gram-issue-header"><span class="gram-issue-type">Sentence ${inst.sentence_index + 1}</span></div>
            <p class="gram-issue-text">"${_esc(truncateText(inst.sentence, 150))}"</p>
            <p class="gram-issue-fix">Passive: ${_esc(inst.passive_constructions?.join(', ') || '')}</p></div>`;
        }
        if (instances.length > 8) html += `<p class="text-xs text-muted">+${instances.length-8} more</p>`;
        html += '</div></div>';
    }

    // ── Filler Words Detail ──
    if (fw && fwCount > 0) {
        const fillerDetails = fw.filler_details || {};
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>🗑️ Filler Words</h3>
            <span class="wc-badge wc-badge-warning">${fwCount} found (${fw.unique_fillers || 0} unique)</span></div>
            <div class="wc-card-body"><div style="display:flex;flex-wrap:wrap;gap:6px">`;
        for (const [word, count] of Object.entries(fillerDetails).slice(0, 15)) {
            html += `<span class="wc-badge wc-badge-warning">${_esc(word)} ×${count}</span>`;
        }
        html += '</div></div></div>';
    }

    // ── Clichés Detail ──
    if (cl && clCount > 0) {
        const clichesList = cl.cliches || [];
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>💭 Clichés</h3>
            <span class="wc-badge wc-badge-warning">${clCount} found</span></div>
            <div class="wc-card-body">`;
        for (const c of clichesList.slice(0, 10)) {
            html += `<div class="gram-issue"><p class="gram-issue-text">"${_esc(c.cliche)}"</p></div>`;
        }
        if (clichesList.length > 10) html += `<p class="text-xs text-muted">+${clichesList.length-10} more</p>`;
        html += '</div></div>';
    }

    // Nothing to improve
    if (allSuggestions.length === 0 && pvCount === 0 && fwCount === 0 && clCount === 0) {
        html += `<div style="text-align:center;padding:48px 0"><div style="font-size:3rem;margin-bottom:8px">🎉</div>
        <p class="font-semibold" style="font-size:1.1rem">No Improvements Needed!</p>
        <p class="text-muted text-sm">Your writing is in excellent shape.</p></div>`;
    }

    html += '</div>';
    return html;
}



// ═══════════════════════════════════════════════════════════
//  TAB — DIALOGUE (Dialogue Analysis)
// ═══════════════════════════════════════════════════════════

function renderDialogue() {
    const da = analysisResults.dialogue_analysis;
    if (!da || da.error || !da.dialogues || da.dialogues.length === 0) {
        return `<div style="text-align:center;padding:48px 0" class="animate-fade-in">
            <div style="font-size:3rem;margin-bottom:8px">💬</div>
            <p class="font-semibold">No Dialogue Detected</p>
            <p class="text-sm text-muted">Submit text with dialogue (quoted speech) for analysis.</p>
            ${da?.error ? `<p class="text-xs" style="color:var(--wc-error);margin-top:12px">Error: ${_esc(da.error)}</p>` : ''}
        </div>`;
    }

    const { dialogues, tag_analysis, pacing, issues, suggestions, authenticity, quality_score } = da;
    let html = '<div class="animate-fade-in">';

    // Calculate summary stats
    const avgWords = dialogues.length > 0 ? Math.round(dialogues.reduce((a, d) => a + (d.word_count || 0), 0) / dialogues.length) : 0;
    
    // Summary
    html += `<div class="wc-write-summary">
        <div class="wc-stat"><span class="wc-stat-value">${dialogues.length}</span><span class="wc-stat-label">Dialogue Lines</span></div>
        <div class="wc-stat"><span class="wc-stat-value">${avgWords}</span><span class="wc-stat-label">Avg Words</span></div>
        <div class="wc-stat"><span class="wc-stat-value">${quality_score || '--'}</span><span class="wc-stat-label">Quality</span></div>
        <div class="wc-stat"><span class="wc-stat-value">${issues?.length || 0}</span><span class="wc-stat-label">Issues</span></div>
    </div>`;

    // Tag Analysis
    if (tag_analysis) {
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>🏷️ Speech Tag Analysis</h3></div><div class="wc-card-body">
            <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px">
                <span class="wc-badge wc-badge-primary">Unique tags: ${tag_analysis.unique_tag_count || 0}</span>
                <span class="wc-badge ${tag_analysis.variety_score > 60 ? 'wc-badge-success' : 'wc-badge-warning'}">Variety score: ${tag_analysis.variety_score || 0}</span>
            </div>
            ${tag_analysis.tag_categories ? `<div class="text-sm" style="margin-bottom:8px">
                <span class="wc-badge wc-badge-muted">Basic: ${tag_analysis.tag_categories.basic || 0}</span>
                <span class="wc-badge wc-badge-muted">Expressive: ${tag_analysis.tag_categories.expressive || 0}</span>
                <span class="wc-badge wc-badge-muted">No tag: ${tag_analysis.tag_categories.none || 0}</span>
            </div>` : ''}
            ${tag_analysis.recommendation ? `<p class="text-sm text-muted">💡 ${_esc(tag_analysis.recommendation)}</p>` : ''}
            ${tag_analysis.overused_tags?.length > 0 ? `<p class="text-xs text-muted">⚠️ Overused: ${tag_analysis.overused_tags.join(', ')}</p>` : ''}
        </div></div>`;
    }

    // Pacing Analysis
    if (pacing) {
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>⏱️ Dialogue Pacing</h3></div><div class="wc-card-body">
            <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px">
                <span class="wc-badge wc-badge-primary">Density: ${(pacing.dialogue_density || 0).toFixed(0)}%</span>
                <span class="wc-badge wc-badge-muted">${_esc(pacing.pacing || 'balanced')}</span>
            </div>
            <p class="text-sm">Dialogue sentences: <strong>${pacing.dialogue_sentences || 0}</strong> | Narrative: <strong>${pacing.narrative_sentences || 0}</strong></p>
            ${pacing.avg_dialogue_gap ? `<p class="text-xs text-muted">Avg gap between dialogues: ${pacing.avg_dialogue_gap.toFixed(0)} chars</p>` : ''}
        </div></div>`;
    }

    // Authenticity
    if (authenticity) {
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>🎭 Authenticity</h3></div><div class="wc-card-body">
            <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px">
                <span class="wc-badge wc-badge-primary">Style: ${_esc(authenticity.style || 'neutral')}</span>
            </div>
            ${authenticity.feedback ? `<p class="text-sm">${_esc(authenticity.feedback)}</p>` : ''}
            ${authenticity.tip ? `<p class="text-xs text-muted">💡 ${_esc(authenticity.tip)}</p>` : ''}
        </div></div>`;
    }

    // Suggestions
    if (suggestions && suggestions.length > 0) {
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>💡 Suggestions</h3></div><div class="wc-card-body">`;
        for (const sug of suggestions.slice(0, 5)) {
            const priorityBadge = sug.priority === 'high' ? 'wc-badge-error' : sug.priority === 'medium' ? 'wc-badge-warning' : 'wc-badge-muted';
            html += `<div class="gram-issue">
                <div class="gram-issue-header">
                    <span class="gram-issue-type">${_esc(sug.title || sug.category)}</span>
                    <span class="wc-badge ${priorityBadge}">${_esc(sug.priority)}</span>
                </div>
                <p class="gram-issue-text">${_esc(sug.description)}</p>
                ${sug.examples ? `<p class="text-xs text-muted">Examples: ${_esc(sug.examples)}</p>` : ''}
            </div>`;
        }
        html += '</div></div>';
    }

    // Dialogue Issues
    if (issues && issues.length > 0) {
        html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>⚠️ Dialogue Issues</h3>
            <span class="wc-badge wc-badge-warning">${issues.length} issues</span></div><div class="wc-card-body">`;
        for (const issue of issues.slice(0, 8)) {
            const sevColor = issue.severity === 'high' ? '--wc-error' : issue.severity === 'medium' ? '--wc-warning' : '--wc-success';
            html += `<div class="gram-issue" style="border-left-color:var(${sevColor})">
                <div class="gram-issue-header">
                    <span class="gram-issue-type">${_esc(issue.type || 'Issue')}</span>
                    <span class="wc-badge wc-badge-${issue.severity === 'high' ? 'error' : 'warning'}">${_esc(issue.severity)}</span>
                </div>
                <p class="gram-issue-text">"${_esc(truncateText(issue.text || issue.dialogue, 120))}"</p>
                ${issue.suggestion ? `<p class="gram-issue-fix">💡 ${_esc(issue.suggestion)}</p>` : ''}
            </div>`;
        }
        html += '</div></div>';
    }

    // Sample Dialogues
    html += `<div class="wc-card mb-md"><div class="wc-card-header"><h3>💬 Dialogue Samples</h3></div><div class="wc-card-body" style="max-height:300px;overflow-y:auto">`;
    for (const d of dialogues.slice(0, 10)) {
        html += `<div class="gram-issue">
            <p class="gram-issue-text">"${_esc(truncateText(d.text || d.content, 150))}"</p>
            <div style="display:flex;gap:6px;margin-top:4px">
                <span class="wc-badge wc-badge-muted">${d.word_count || 0} words</span>
                ${d.speech_tag ? `<span class="wc-badge wc-badge-muted">${_esc(d.speech_tag)}</span>` : '<span class="wc-badge wc-badge-muted">no tag</span>'}
                ${d.has_action_beat ? '<span class="wc-badge wc-badge-success">action beat</span>' : ''}
            </div>
        </div>`;
    }
    if (dialogues.length > 10) html += `<p class="text-xs text-muted">+${dialogues.length - 10} more dialogue lines</p>`;
    html += '</div></div>';

    html += '</div>';
    return html;
}


// ═══════════════════════════════════════════════════════════
//  UTILITIES
// ═══════════════════════════════════════════════════════════

function _esc(str) {
    if (!str) return '';
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncateText(text, max) {
    if (!text) return '';
    return text.length <= max ? text : text.substring(0, max) + '...';
}

function debounce(fn, wait) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), wait); };
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `wc-toast wc-toast-${type}`;
    toast.textContent = message;
    elements.toastContainer.appendChild(toast);
    setTimeout(() => { toast.classList.add('wc-toast-exit'); setTimeout(() => toast.remove(), 300); }, 3000);
}

function animateNumber(el, start, end, duration) {
    const range = end - start;
    const inc = range / (duration / 16);
    let cur = start;
    const timer = setInterval(() => {
        cur += inc;
        if ((inc > 0 && cur >= end) || (inc < 0 && cur <= end)) { cur = end; clearInterval(timer); }
        el.textContent = Math.round(cur);
    }, 16);
}

function getScoreColor(score) {
    if (score >= 80) return '#34A853';
    if (score >= 60) return '#4285F4';
    if (score >= 40) return '#FBBC04';
    return '#EA4335';
}

function copyOriginal() {
    if (analysisResults?.style_transformation?.original) {
        navigator.clipboard.writeText(analysisResults.style_transformation.original)
            .then(() => showToast('Copied original text!', 'success'))
            .catch(() => showToast('Failed to copy', 'error'));
    }
}

function copyTransformed() {
    if (analysisResults?.style_transformation?.transformed) {
        navigator.clipboard.writeText(analysisResults.style_transformation.transformed)
            .then(() => showToast('Copied transformed text!', 'success'))
            .catch(() => showToast('Failed to copy', 'error'));
    }
}
