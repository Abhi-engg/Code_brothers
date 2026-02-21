/**
 * Writing Assistant - Enhanced Application JavaScript
 * Handles API communication, UI updates, and analysis rendering  
 * Now with 15+ enhanced NLP features!
 */

// Configuration
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    DEBOUNCE_DELAY: 300
};

// State
let analysisResults = null;
let currentTab = 'write';

// DOM Elements
const elements = {
    textInput: document.getElementById('text-input'),
    analyzeBtn: document.getElementById('analyze-btn'),
    clearBtn: document.getElementById('clear-btn'),
    charCount: document.getElementById('char-count'),
    wordCount: document.getElementById('word-count'),
    resultsContainer: document.getElementById('results-container'),
    tabContent: document.getElementById('tab-content'),
    scoresContainer: document.getElementById('scores-container'),
    loadingOverlay: document.getElementById('loading-overlay'),
    toastContainer: document.getElementById('toast-container'),
    apiStatus: document.getElementById('api-status'),
    targetStyle: document.getElementById('target-style'),
    targetTone: document.getElementById('target-tone'),
    thresholdSentence: document.getElementById('threshold-sentence'),
    thresholdRepeated: document.getElementById('threshold-repeated')
};

// Feature toggles
const featureToggles = {
    readability: document.getElementById('feat-readability'),
    flow: document.getElementById('feat-flow'),
    style: document.getElementById('feat-style'),
    consistency: document.getElementById('feat-consistency'),
    transform: document.getElementById('feat-transform'),
    mindmap: document.getElementById('feat-mindmap')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    checkAPIHealth();
    updateCounts();
    addWelcomeAnimation();
});

// Add welcome animation
function addWelcomeAnimation() {
    elements.textInput.style.opacity = '0';
    elements.textInput.style.transform = 'translateY(20px)';
    setTimeout(() => {
        elements.textInput.style.transition = 'all 0.5s ease';
        elements.textInput.style.opacity = '1';
        elements.textInput.style.transform = 'translateY(0)';
    }, 100);
}

// Event Listeners
function initEventListeners() {
    // Text input
    elements.textInput.addEventListener('input', debounce(updateCounts, CONFIG.DEBOUNCE_DELAY));
    
    // Buttons
    elements.analyzeBtn.addEventListener('click', analyzeText);
    elements.clearBtn.addEventListener('click', clearAll);
    
    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => switchTab(e.target.dataset.tab));
    });
    
    // Enter key to analyze
    elements.textInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            analyzeText();
        }
    });
}

// API Health Check
async function checkAPIHealth() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/health`);
        if (response.ok) {
            const data = await response.json();
            elements.apiStatus.innerHTML = `
                <span class="w-2 h-2 bg-green-500 rounded-full mr-2 pulse-dot"></span>
                API Connected
            `;
            elements.apiStatus.classList.add('text-green-600');
        } else {
            throw new Error('API not responding');
        }
    } catch (error) {
        elements.apiStatus.innerHTML = `
            <span class="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
            API Offline
        `;
        elements.apiStatus.classList.add('text-red-600');
        showToast('API is not available. Make sure the server is running on port 8000.', 'error');
    }
}

// Update character and word counts
function updateCounts() {
    const text = elements.textInput.value;
    elements.charCount.textContent = text.length;
    elements.wordCount.textContent = text.trim() ? text.trim().split(/\s+/).length : 0;
    
    // Enable/disable analyze button
    elements.analyzeBtn.disabled = !text.trim();
}

// Clear all
function clearAll() {
    elements.textInput.value = '';
    updateCounts();
    elements.resultsContainer.classList.add('hidden');
    elements.scoresContainer.classList.add('hidden');
    analysisResults = null;
    currentTab = 'overview';
}

// Analyze text
async function analyzeText() {
    const text = elements.textInput.value.trim();
    
    if (!text) {
        showToast('Please enter some text to analyze', 'warning');
        return;
    }
    
    // Get settings
    const features = {
        text_analysis: true,
        readability: featureToggles.readability.checked,
        flow: featureToggles.flow.checked,
        style: featureToggles.style.checked,
        consistency: featureToggles.consistency.checked,
        transform: featureToggles.transform.checked,
        explanations: true,
        mind_map: featureToggles.mindmap ? featureToggles.mindmap.checked : true
    };
    
    const requestBody = {
        text: text,
        features: features,
        target_style: elements.targetStyle.value,
        target_tone: elements.targetTone ? elements.targetTone.value : 'auto',
        long_sentence_threshold: parseInt(elements.thresholdSentence.value) || 25,
        repeated_word_min_count: parseInt(elements.thresholdRepeated.value) || 3
    };
    
    // Show loading
    elements.loadingOverlay.classList.remove('hidden');
    elements.analyzeBtn.disabled = true;
    elements.analyzeBtn.innerHTML = '<span class="animate-spin">⚙️</span> Analyzing...';
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }
        
        analysisResults = await response.json();
        console.log('Analysis Results:', analysisResults); // Debug
        
        // Display results with animation
        displayResults();
        showToast('✨ Analysis complete! Check out the Enhanced tab for new features!', 'success');
        
    } catch (error) {
        console.error('Analysis error:', error);
        showToast(error.message || 'Failed to analyze text', 'error');
    } finally {
        elements.loadingOverlay.classList.add('hidden');
        elements.analyzeBtn.disabled = false;
        elements.analyzeBtn.innerHTML = 'Analyze Text';
    }
}

// Display results
function displayResults() {
    if (!analysisResults) return;
    
    // Show containers with animation
    elements.resultsContainer.classList.remove('hidden');
    elements.scoresContainer.classList.remove('hidden');
    
    // Animate in
    elements.resultsContainer.style.opacity = '0';
    elements.resultsContainer.style.transform = 'translateY(20px)';
    requestAnimationFrame(() => {
        elements.resultsContainer.style.transition = 'all 0.5s ease';
        elements.resultsContainer.style.opacity = '1';
        elements.resultsContainer.style.transform = 'translateY(0)';
    });
    
    // Update scores
    updateScores(analysisResults.scores);
    
    // Render current tab
    renderTab(currentTab);
}

// Update score displays with animation
function updateScores(scores) {
    if (!scores) return;
    
    const scoreElements = {
        overall: { el: 'score-overall', bar: 'score-overall-bar' },
        readability: { el: 'score-readability', bar: 'score-readability-bar' },
        flow: { el: 'score-flow', bar: 'score-flow-bar' },
        consistency: { el: 'score-consistency', bar: 'score-consistency-bar' }
    };
    
    for (const [key, config] of Object.entries(scoreElements)) {
        const value = scores[key];
        if (value !== undefined && value !== null) {
            const roundedValue = Math.round(value);
            const scoreEl = document.getElementById(config.el);
            const barEl = document.getElementById(config.bar);
            
            if (scoreEl && barEl) {
                // Animate number
                animateNumber(scoreEl, 0, roundedValue, 1000);
                
                // Animate bar
                setTimeout(() => {
                    barEl.style.width = `${Math.min(100, value)}%`;
                    barEl.style.backgroundColor = getScoreColor(value);
                }, 200);
            }
        }
    }
}

// Animate number counting
function animateNumber(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16); // 60fps
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current);
    }, 16);
}

// Get score color
function getScoreColor(score) {
    if (score >= 80) return '#10B981'; // green
    if (score >= 60) return '#3B82F6'; // blue
    if (score >= 40) return '#F59E0B'; // yellow
    return '#EF4444'; // red
}

// Switch tabs
function switchTab(tabName) {
    currentTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active', 'border-primary', 'text-primary');
        btn.classList.add('border-transparent', 'text-gray-500');
    });
    
    const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active', 'border-primary', 'text-primary');
        activeBtn.classList.remove('border-transparent', 'text-gray-500');
    }
    
    // Render tab content
    renderTab(tabName);
}

// Render tab content
function renderTab(tabName) {
    if (!analysisResults) return;
    
    let content = '';
    
    switch (tabName) {
        case 'write':
            content = renderWrite();
            break;
        case 'overview':
            content = renderOverview();
            break;
        case 'issues':
            content = renderIssues();
            break;
        case 'enhancements':
            content = renderEnhancements();
            break;
        case 'tone':
            content = renderTone();
            break;
        case 'suggestions':
            content = renderSuggestions();
            break;
        case 'transform':
            content = renderTransform();
            break;
        case 'narrative':
            content = renderNarrative();
            break;
        case 'mindmap':
            content = renderMindMap();
            break;
        case 'details':
            content = renderDetails();
            break;
    }
    
    elements.tabContent.innerHTML = content;
    
    // Fade in animation
    elements.tabContent.style.opacity = '0';
    requestAnimationFrame(() => {
        elements.tabContent.style.transition = 'opacity 0.3s ease';
        elements.tabContent.style.opacity = '1';
    });
    
    // Post-render binding for Write tab
    if (tabName === 'write') {
        bindWriteTabEvents();
    }
    // Post-render: initialize vis.js mind map
    if (tabName === 'mindmap') {
        setTimeout(() => initMindMapNetwork(), 50);
    }
}

// ════════════════════════════════════════════════════
// Render Write Tab — Inline Annotated Text (Phase 6)
// ════════════════════════════════════════════════════

// Category metadata for display
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

// Track which categories are visible
let annVisibleCategories = new Set(Object.keys(ANN_CATEGORIES));

function renderWrite() {
    const annotations = analysisResults.annotations || [];
    const text = analysisResults.input?.text || '';

    // Count per category
    const counts = {};
    for (const a of annotations) {
        counts[a.category] = (counts[a.category] || 0) + 1;
    }
    const totalCount = annotations.length;

    // Build filter bar
    let filterBar = '<div class="ann-filter-bar">';
    for (const [cat, meta] of Object.entries(ANN_CATEGORIES)) {
        const c = counts[cat] || 0;
        if (c === 0) continue;
        const isActive = annVisibleCategories.has(cat);
        filterBar += `
            <button class="ann-filter-btn ann-filter-${cat} ${isActive ? 'active' : 'inactive'}"
                    data-cat="${cat}" title="Toggle ${meta.label}">
                <span>${meta.icon} ${meta.label}</span>
                <span class="ann-count">${c}</span>
            </button>`;
    }
    filterBar += '</div>';

    // Summary line
    const summaryLine = `
        <div class="ann-summary">
            <strong>${totalCount}</strong> annotation${totalCount !== 1 ? 's' : ''} found
            &nbsp;·&nbsp; Hover highlighted text for details
        </div>`;

    // Build annotated text HTML
    const annotatedHTML = buildAnnotatedHTML(text, annotations);

    return `
        <div class="space-y-4 animate-fade-in">
            <div class="flex items-center justify-between mb-2">
                <h3 class="font-semibold text-gray-900 text-lg flex items-center">
                    <span class="text-2xl mr-2">✍️</span> Annotated Manuscript
                </h3>
                <span class="text-xs text-gray-400">${text.length} chars</span>
            </div>
            ${summaryLine}
            ${filterBar}
            <div class="annotated-text" id="annotated-text-area">
                ${annotatedHTML}
            </div>
        </div>`;
}

/**
 * Build HTML string with annotation spans inserted at the correct positions.
 * Handles overlapping annotations by flattening them — if two annotations
 * overlap the same character range, both CSS classes are applied.
 */
function buildAnnotatedHTML(text, annotations) {
    if (!annotations || annotations.length === 0) return _esc(text);

    // Filter to only visible categories
    const visible = annotations.filter(a => annVisibleCategories.has(a.category));

    // Create sorted, non-overlapping segments with annotation data.
    // Each char position maps to a set of annotations covering it.
    // For performance, we use an event-based sweep approach.
    const events = []; // {pos, type: 'open'|'close', ann}

    for (let i = 0; i < visible.length; i++) {
        const a = visible[i];
        if (a.start == null || a.end == null || a.start >= a.end) continue;
        const start = Math.max(0, Math.min(a.start, text.length));
        const end = Math.max(0, Math.min(a.end, text.length));
        events.push({ pos: start, type: 'open', ann: a, idx: i });
        events.push({ pos: end, type: 'close', ann: a, idx: i });
    }

    // Sort events: by position, then closes before opens at same pos
    events.sort((a, b) => a.pos - b.pos || (a.type === 'close' ? -1 : 1));

    let html = '';
    let cursor = 0;
    const activeSet = new Map(); // idx → ann

    for (const ev of events) {
        // Emit text from cursor to this event position
        if (ev.pos > cursor) {
            if (activeSet.size > 0) {
                html += wrapAnnotatedSegment(text.slice(cursor, ev.pos), activeSet);
            } else {
                html += _esc(text.slice(cursor, ev.pos));
            }
            cursor = ev.pos;
        }

        if (ev.type === 'open') {
            // Close current span if any, re-open with new set
            activeSet.set(ev.idx, ev.ann);
        } else {
            activeSet.delete(ev.idx);
        }
    }

    // Remaining text after last event
    if (cursor < text.length) {
        html += _esc(text.slice(cursor));
    }

    return html;
}

/**
 * Wrap a text segment with annotation span(s).
 * If multiple annotations overlap, we pick the highest-severity one for
 * the primary style but show all in the tooltip.
 */
function wrapAnnotatedSegment(segment, activeMap) {
    const anns = Array.from(activeMap.values());
    // Pick primary annotation (highest severity wins)
    const sevOrder = { error: 0, high: 1, warning: 2, medium: 3, info: 4, low: 5 };
    anns.sort((a, b) => (sevOrder[a.severity] ?? 9) - (sevOrder[b.severity] ?? 9));
    const primary = anns[0];

    const classes = ['ann', `ann-${primary.category}`];

    // Build tooltip content (all overlapping annotations)
    let tooltipInner = '';
    for (const a of anns) {
        const cat = ANN_CATEGORIES[a.category] || { label: a.category, icon: '📌' };
        tooltipInner += `
            <div style="margin-bottom:6px">
                <span class="ann-tooltip-cat ann-tooltip-cat-${a.category}">${cat.icon} ${cat.label}</span>
                <span class="severity-badge severity-${a.severity}">${a.severity}</span>
                <div class="ann-tooltip-msg">${_esc(a.message)}</div>
                ${a.suggestion ? `<div class="ann-tooltip-suggestion">💡 ${_esc(a.suggestion)}</div>` : ''}
            </div>`;
    }

    // Action buttons (only if primary has a suggestion)
    let actions = '';
    if (primary.suggestion) {
        actions = `
            <div class="ann-tooltip-actions">
                <button class="ann-btn-dismiss" data-action="dismiss" data-ann-start="${primary.start}" data-ann-end="${primary.end}">Dismiss</button>
            </div>`;
    }

    return `<span class="${classes.join(' ')}">${_esc(segment)}<span class="ann-tooltip">${tooltipInner}${actions}</span></span>`;
}

/**
 * Bind click events for filter buttons and dismiss/accept actions
 * after the Write tab DOM is rendered.
 */
function bindWriteTabEvents() {
    // Filter buttons
    document.querySelectorAll('.ann-filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const cat = btn.dataset.cat;
            if (annVisibleCategories.has(cat)) {
                annVisibleCategories.delete(cat);
            } else {
                annVisibleCategories.add(cat);
            }
            // Re-render only the annotated area + filters
            const writeHTML = renderWrite();
            elements.tabContent.innerHTML = writeHTML;
            bindWriteTabEvents();
        });
    });

    // Dismiss buttons inside tooltips
    document.querySelectorAll('.ann-btn-dismiss').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const start = parseInt(btn.dataset.annStart);
            const end = parseInt(btn.dataset.annEnd);
            // Remove matching annotation from results
            if (analysisResults.annotations) {
                analysisResults.annotations = analysisResults.annotations.filter(
                    a => !(a.start === start && a.end === end)
                );
            }
            // Re-render
            const writeHTML = renderWrite();
            elements.tabContent.innerHTML = writeHTML;
            bindWriteTabEvents();
        });
    });
}

// ════════════════════════════════════════════════════
// Render Mind Map Tab — NoteLM-style (Phase 7)
// ════════════════════════════════════════════════════

const MIND_MAP_GROUP_META = {
    character:    { label: 'Characters',     icon: '👤', color: '#3B82F6' },
    organization: { label: 'Organizations',  icon: '🏢', color: '#6366F1' },
    location:     { label: 'Locations',       icon: '📍', color: '#10B981' },
    time:         { label: 'Time',            icon: '🕐', color: '#F59E0B' },
    event:        { label: 'Events',          icon: '⚡', color: '#EC4899' },
    theme:        { label: 'Themes',          icon: '💡', color: '#F59E0B' },
    action:       { label: 'Actions',         icon: '🎯', color: '#EF4444' },
    detail:       { label: 'Details',         icon: '📎', color: '#94A3B8' },
    concept:      { label: 'Concepts',        icon: '🔮', color: '#8B5CF6' },
    other:        { label: 'Other',           icon: '📌', color: '#CBD5E1' },
};

// Track which mind map groups are visible
let mindMapVisibleGroups = new Set(Object.keys(MIND_MAP_GROUP_META));
let mindMapNetworkInstance = null;

function renderMindMap() {
    const mapData = analysisResults.mind_map;

    if (!mapData || mapData.error || !mapData.nodes || mapData.nodes.length === 0) {
        return `
            <div class="text-center py-12 text-gray-400 animate-fade-in">
                <div class="text-5xl mb-4">🧠</div>
                <p class="text-lg font-medium mb-2">No Mind Map Data</p>
                <p class="text-sm">The text doesn't contain enough concepts to generate a mind map.<br>
                Try analyzing longer text with named entities, characters, and themes.</p>
                ${mapData?.error ? `<p class="text-xs text-red-400 mt-4">Error: ${_esc(mapData.error)}</p>` : ''}
            </div>`;
    }

    const { nodes, edges, central_node, stats } = mapData;

    // Group counts for legend
    const groupCounts = {};
    for (const n of nodes) {
        groupCounts[n.group] = (groupCounts[n.group] || 0) + 1;
    }

    // Legend / filter bar
    let legendHtml = '<div class="mm-legend">';
    for (const [grp, meta] of Object.entries(MIND_MAP_GROUP_META)) {
        const c = groupCounts[grp] || 0;
        if (c === 0) continue;
        const active = mindMapVisibleGroups.has(grp);
        legendHtml += `
            <button class="mm-legend-btn ${active ? 'active' : 'inactive'}"
                    data-group="${grp}"
                    style="--grp-color: ${meta.color}">
                <span class="mm-legend-dot" style="background:${meta.color}"></span>
                <span>${meta.icon} ${meta.label}</span>
                <span class="mm-legend-count">${c}</span>
            </button>`;
    }
    legendHtml += '</div>';

    // Stats bar
    const statsHtml = `
        <div class="mm-stats">
            <span>🧠 <strong>${stats.total_nodes}</strong> concept${stats.total_nodes !== 1 ? 's' : ''}</span>
            <span class="mm-stats-sep">·</span>
            <span>🔗 <strong>${stats.total_edges}</strong> connection${stats.total_edges !== 1 ? 's' : ''}</span>
            <span class="mm-stats-sep">·</span>
            <span>⭐ Central: <strong>${_esc(central_node || '—')}</strong></span>
        </div>`;

    // Concept list sidebar
    let conceptListHtml = '<div class="mm-concept-list">';
    conceptListHtml += '<h4 class="mm-concept-list-title">Key Concepts</h4>';
    const sortedNodes = [...nodes].sort((a, b) => b.importance - a.importance);
    for (const n of sortedNodes) {
        const meta = MIND_MAP_GROUP_META[n.group] || MIND_MAP_GROUP_META.other;
        const barWidth = Math.max(4, n.importance);
        conceptListHtml += `
            <div class="mm-concept-item" data-node-id="${n.id}" title="${_esc(n.label)} (${n.type})">
                <div class="mm-concept-icon" style="color:${meta.color}">${meta.icon}</div>
                <div class="mm-concept-info">
                    <div class="mm-concept-name">${_esc(n.label)}</div>
                    <div class="mm-concept-bar-track">
                        <div class="mm-concept-bar" style="width:${barWidth}%; background:${meta.color}"></div>
                    </div>
                </div>
                <div class="mm-concept-score">${n.importance}</div>
            </div>`;
    }
    conceptListHtml += '</div>';

    return `
        <div class="mm-container animate-fade-in">
            <div class="flex items-center justify-between mb-3">
                <h3 class="font-semibold text-gray-900 text-lg flex items-center">
                    <span class="text-2xl mr-2">🧠</span> Concept Mind Map
                </h3>
                <div class="flex gap-2">
                    <button id="mm-btn-fit" class="mm-toolbar-btn" title="Fit to view">⊞ Fit</button>
                    <button id="mm-btn-physics" class="mm-toolbar-btn" title="Toggle physics">⚛️ Physics</button>
                </div>
            </div>
            ${statsHtml}
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

/**
 * Initialize the vis.js Network after the DOM is rendered.
 */
function initMindMapNetwork() {
    const container = document.getElementById('mm-network');
    if (!container) return;

    const mapData = analysisResults.mind_map;
    if (!mapData || !mapData.nodes || mapData.nodes.length === 0) return;

    // Filter by visible groups
    const visibleNodes = mapData.nodes.filter(n => mindMapVisibleGroups.has(n.group));
    const visibleIds = new Set(visibleNodes.map(n => n.id));
    const visibleEdges = mapData.edges.filter(e => visibleIds.has(e.from) && visibleIds.has(e.to));

    // Build vis.js DataSets
    const nodesData = visibleNodes.map(n => ({
        id: n.id,
        label: n.label,
        size: n.size,
        color: {
            background: n.color.background,
            border: n.color.border,
            highlight: { background: n.color.background, border: '#1E293B' },
            hover: { background: n.color.background, border: '#1E293B' },
        },
        font: {
            size: n.font_size,
            color: n.color.fontColor || '#ffffff',
            strokeWidth: 2,
            strokeColor: 'rgba(0,0,0,0.3)',
            face: "'Inter', 'Segoe UI', system-ui, sans-serif",
            bold: n.is_central ? { color: n.color.fontColor || '#ffffff', size: n.font_size + 2 } : undefined,
        },
        shape: n.is_central ? 'star' : 'dot',
        borderWidth: n.is_central ? 3 : 2,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.15)', size: 8, x: 2, y: 2 },
        title: `${n.label}\nType: ${n.type}\nImportance: ${n.importance}%`,
    }));

    const edgesData = visibleEdges.map((e, i) => ({
        id: i,
        from: e.from,
        to: e.to,
        label: e.label.length > 18 ? e.label.slice(0, 16) + '…' : e.label,
        width: e.width,
        color: { color: '#94A3B8', highlight: '#3B82F6', hover: '#64748B' },
        font: { size: 9, color: '#64748B', strokeWidth: 0, align: 'middle', face: 'system-ui' },
        arrows: { to: { enabled: false } },
        smooth: { type: 'continuous', roundness: 0.3 },
    }));

    const options = {
        physics: {
            enabled: true,
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {
                gravitationalConstant: -40,
                centralGravity: 0.008,
                springLength: 140,
                springConstant: 0.04,
                damping: 0.4,
                avoidOverlap: 0.6,
            },
            stabilization: { iterations: 200, updateInterval: 25 },
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            zoomView: true,
            dragView: true,
            dragNodes: true,
            navigationButtons: false,
            keyboard: false,
        },
        layout: {
            improvedLayout: true,
            randomSeed: 42,
        },
        nodes: {
            shape: 'dot',
            scaling: { min: 15, max: 55 },
        },
        edges: {
            smooth: { type: 'continuous' },
        },
    };

    // Destroy previous instance
    if (mindMapNetworkInstance) {
        mindMapNetworkInstance.destroy();
        mindMapNetworkInstance = null;
    }

    const network = new vis.Network(container, { nodes: nodesData, edges: edgesData }, options);
    mindMapNetworkInstance = network;

    // Click node → highlight in concept list
    network.on('selectNode', (params) => {
        const nodeId = params.nodes[0];
        // highlight concept-list item
        document.querySelectorAll('.mm-concept-item').forEach(el => {
            el.classList.toggle('mm-concept-active', parseInt(el.dataset.nodeId) === nodeId);
        });
        // highlight connected edges
        const connectedEdges = network.getConnectedEdges(nodeId);
        network.selectEdges(connectedEdges);
    });

    network.on('deselectNode', () => {
        document.querySelectorAll('.mm-concept-item').forEach(el => {
            el.classList.remove('mm-concept-active');
        });
    });

    // Bind legend filter buttons
    document.querySelectorAll('.mm-legend-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const grp = btn.dataset.group;
            if (mindMapVisibleGroups.has(grp)) {
                mindMapVisibleGroups.delete(grp);
            } else {
                mindMapVisibleGroups.add(grp);
            }
            // Re-render
            elements.tabContent.innerHTML = renderMindMap();
            setTimeout(() => initMindMapNetwork(), 50);
        });
    });

    // Concept list click → focus node
    document.querySelectorAll('.mm-concept-item').forEach(el => {
        el.addEventListener('click', () => {
            const nodeId = parseInt(el.dataset.nodeId);
            network.selectNodes([nodeId]);
            network.focus(nodeId, { scale: 1.2, animation: { duration: 400, easingFunction: 'easeInOutQuad' } });
            document.querySelectorAll('.mm-concept-item').forEach(e => e.classList.remove('mm-concept-active'));
            el.classList.add('mm-concept-active');
        });
    });

    // Toolbar buttons
    const fitBtn = document.getElementById('mm-btn-fit');
    const physicsBtn = document.getElementById('mm-btn-physics');

    if (fitBtn) {
        fitBtn.addEventListener('click', () => {
            network.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
        });
    }

    let physicsOn = true;
    if (physicsBtn) {
        physicsBtn.addEventListener('click', () => {
            physicsOn = !physicsOn;
            network.setOptions({ physics: { enabled: physicsOn } });
            physicsBtn.textContent = physicsOn ? '⚛️ Physics' : '📌 Locked';
        });
    }

    // Fit after stabilization
    network.once('stabilizationIterationsDone', () => {
        network.fit({ animation: { duration: 300, easingFunction: 'easeInOutQuad' } });
    });
}

// Render Overview Tab
function renderOverview() {
    const { explanations, readability, style_analysis, text_analysis, scores } = analysisResults;
    
    return `
        <div class="space-y-6 animate-fade-in">
            <!-- Summary -->
            <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
                <h3 class="font-semibold text-blue-900 mb-2 flex items-center">
                    <span class="text-2xl mr-2">📝</span> Summary
                </h3>
                <p class="text-blue-800">${explanations?.summary || 'Analysis complete. Check the tabs for detailed insights!'}</p>
            </div>
            
            <!-- Overall Score Card -->
            <div class="bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl p-6 text-white shadow-lg">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="text-lg font-medium opacity-90">Overall Writing Score</h3>
                        <p class="text-sm opacity-75 mt-1">Comprehensive quality assessment</p>
                    </div>
                    <div class="text-right">
                        <div class="text-5xl font-bold">${scores?.overall ? Math.round(scores.overall) : 'N/A'}</div>
                        <div class="text-sm opacity-75">out of 100</div>
                    </div>
                </div>
            </div>
            
            <!-- Quick Stats -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="stat-card bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 text-center hover-lift">
                    <div class="text-3xl font-bold text-blue-600">${text_analysis?.sentences?.length || 0}</div>
                    <div class="text-sm text-gray-600 mt-1">Sentences</div>
                </div>
                <div class="stat-card bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 text-center hover-lift">
                    <div class="text-3xl font-bold text-green-600">${text_analysis?.tokens?.length || 0}</div>
                    <div class="text-sm text-gray-600 mt-1">Words</div>
                </div>
                <div class="stat-card bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 text-center hover-lift">
                    <div class="text-3xl font-bold text-purple-600">${text_analysis?.entities?.length || 0}</div>
                    <div class="text-sm text-gray-600 mt-1">Entities</div>
                </div>
                <div class="stat-card bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4 text-center hover-lift">
                    <div class="text-3xl font-bold text-orange-600">${readability?.reading_time_minutes || 0}</div>
                    <div class="text-sm text-gray-600 mt-1">Min Read</div>
                </div>
            </div>
            
            <!-- Readability -->
            ${readability ? `
            <div class="feature-card">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="text-2xl mr-2">📖</span> Readability
                </h3>
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <span class="text-sm text-gray-600">Grade Level</span>
                            <div class="text-2xl font-bold text-gray-900">${readability.grade_level}</div>
                        </div>
                        <div>
                            <span class="text-sm text-gray-600">Difficulty</span>
                            <div class="text-2xl font-bold text-gray-900 capitalize">${readability.difficulty}</div>
                        </div>
                    </div>
                    <p class="text-sm text-gray-600">${readability.interpretation}</p>
                </div>
            </div>
            ` : ''}
            
            <!-- Style -->
            ${style_analysis ? `
            <div class="feature-card">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="text-2xl mr-2">✍️</span> Writing Style
                </h3>
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm text-gray-600">Detected Style</span>
                        <span class="px-3 py-1 bg-purple-100 text-purple-700 rounded-full font-semibold capitalize">${style_analysis.dominant_style}</span>
                    </div>
                    <p class="text-sm text-gray-600 mt-3">${style_analysis.recommendation || ''}</p>
                </div>
            </div>
            ` : ''}
            
            <!-- Entities -->
            ${text_analysis?.entities?.length > 0 ? `
            <div class="feature-card">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="text-2xl mr-2">🏷️</span> Named Entities
                </h3>
                <div class="flex flex-wrap gap-2">
                    ${text_analysis.entities.slice(0, 20).map(([text, label]) => `
                        <span class="entity-tag entity-${label}">${escapeHtml(text)} <span class="opacity-60 text-xs">(${label})</span></span>
                    `).join('')}
                    ${text_analysis.entities.length > 20 ? `<span class="text-sm text-gray-500">+${text_analysis.entities.length - 20} more</span>` : ''}
                </div>
            </div>
            ` : ''}
        </div>
    `;
}

// Render Enhanced Features Tab (NEW!)
function renderEnhancements() {
    const { passive_voice, sentiment, vocabulary_complexity, filler_words, cliches, paragraph_structure, lexical_density, sentence_rhythm } = analysisResults;
    
    let html = '<div class="space-y-6 animate-fade-in">';
    
    // Passive Voice Detection
    if (passive_voice) {
        const passiveCount = passive_voice.passive_count || 0;
        const passivePercent = passive_voice.passive_percentage || 0;
        const instances = passive_voice.passive_instances || [];
        
        html += `
            <div class="feature-card border-l-4 border-orange-500">
                <div class="flex items-center justify-between mb-3">
                    <h3 class="font-semibold text-gray-900 flex items-center">
                        <span class="text-2xl mr-2">🎯</span> Passive Voice Detection
                    </h3>
                    <span class="px-3 py-1 ${passiveCount === 0 ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'} text-sm font-semibold rounded-full">
                        ${passiveCount} found (${passivePercent.toFixed(1)}%)
                    </span>
                </div>
                ${passiveCount > 0 ? `
                    <div class="space-y-3">
                        ${instances.slice(0, 5).map((inst, idx) => `
                            <div class="bg-orange-50 border border-orange-200 rounded-lg p-3">
                                <div class="text-sm font-medium text-orange-800 mb-1">Sentence ${inst.sentence_index + 1}</div>
                                <p class="text-sm text-gray-700 italic">"${truncateText(inst.sentence, 150)}"</p>
                                <div class="mt-2 text-xs text-orange-600">Passive construction: <span class="font-semibold">${inst.passive_constructions.join(', ')}</span></div>
                            </div>
                        `).join('')}
                        ${instances.length > 5 ? `<p class="text-sm text-gray-500 text-center">+ ${instances.length - 5} more instances</p>` : ''}
                    </div>
                    <div class="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <p class="text-sm text-blue-800"><strong>💡 Tip:</strong> Consider converting passive voice to active voice for clearer, more direct writing.</p>
                    </div>
                ` : `
                    <div class="flex items-center justify-center py-8">
                        <div class="text-center">
                            <div class="text-4xl mb-2">✅</div>
                            <p class="text-gray-600">No passive voice detected! Your writing is direct and active.</p>
                        </div>
                    </div>
                `}
            </div>
        `;
    }
    
    // Sentiment Analysis
    if (sentiment) {
        const sentimentType = sentiment.sentiment || 'neutral';
        const score = sentiment.score || 0;
        const positive = sentiment.positive_words || 0;
        const negative = sentiment.negative_words || 0;
        
        const sentimentColors = {
            positive: 'green',
            negative: 'red',
            neutral: 'gray'
        };
        const color = sentimentColors[sentimentType] || 'gray';
        
        const sentimentEmojis = {
            positive: '😊',
            negative: '😕',
            neutral: '😐'
        };
        
        html += `
            <div class="feature-card border-l-4 border-${color}-500">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="text-2xl mr-2">${sentimentEmojis[sentimentType]}</span> Sentiment Analysis
                </h3>
                <div class="bg-${color}-50 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-4">
                        <div>
                            <div class="text-sm text-gray-600 mb-1">Overall Sentiment</div>
                            <div class="text-3xl font-bold text-${color}-600 capitalize">${sentimentType}</div>
                        </div>
                        <div class="text-right">
                            <div class="text-sm text-gray-600 mb-1">Sentiment Score</div>
                            <div class="text-3xl font-bold text-${color}-600">${score.toFixed(2)}</div>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-white bg-opacity-70 rounded-lg p-3 text-center">
                            <div class="text-2xl font-bold text-green-600">${positive}</div>
                            <div class="text-xs text-gray-600">Positive Words</div>
                        </div>
                        <div class="bg-white bg-opacity-70 rounded-lg p-3 text-center">
                            <div class="text-2xl font-bold text-red-600">${negative}</div>
                            <div class="text-xs text-gray-600">Negative Words</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Vocabulary Complexity
    if (vocabulary_complexity) {
        const diversity = vocabulary_complexity.lexical_diversity || 0;
        const level = vocabulary_complexity.complexity_level || 'basic';
        const advancedWords = vocabulary_complexity.advanced_words || 0;
        
        html += `
            <div class="feature-card border-l-4 border-purple-500">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="text-2xl mr-2">📚</span> Vocabulary Complexity
                </h3>
                <div class="bg-purple-50 rounded-lg p-4">
                    <div class="grid grid-cols-3 gap-4 mb-3">
                        <div class="bg-white rounded-lg p-3 text-center">
                            <div class="text-2xl font-bold text-purple-600">${(diversity * 100).toFixed(0)}%</div>
                            <div class="text-xs text-gray-600">Lexical Diversity</div>
                        </div>
                        <div class="bg-white rounded-lg p-3 text-center">
                            <div class="text-2xl font-bold text-purple-600 capitalize">${level}</div>
                            <div class="text-xs text-gray-600">Complexity Level</div>
                        </div>
                        <div class="bg-white rounded-lg p-3 text-center">
                            <div class="text-2xl font-bold text-purple-600">${advancedWords}</div>
                            <div class="text-xs text-gray-600">Advanced Words</div>
                        </div>
                    </div>
                    ${vocabulary_complexity.interpretation ? `
                        <p class="text-sm text-purple-800 bg-white bg-opacity-70 rounded p-2">${vocabulary_complexity.interpretation}</p>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    // Filler Words
    if (filler_words) {
        const totalFillers = filler_words.total_fillers || 0;
        const uniqueFillers = filler_words.unique_fillers || 0;
        const fillersList = filler_words.filler_details || {};
        
        html += `
            <div class="feature-card border-l-4 border-yellow-500">
                <div class="flex items-center justify-between mb-3">
                    <h3 class="font-semibold text-gray-900 flex items-center">
                        <span class="text-2xl mr-2">🚫</span> Filler Words
                    </h3>
                    <span class="px-3 py-1 ${totalFillers === 0 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'} text-sm font-semibold rounded-full">
                        ${totalFillers} found
                    </span>
                </div>
                ${totalFillers > 0 ? `
                    <div class="bg-yellow-50 rounded-lg p-4">
                        <div class="mb-3 text-sm text-yellow-800">
                            <strong>${uniqueFillers}</strong> unique filler words detected
                        </div>
                        <div class="flex flex-wrap gap-2">
                            ${Object.entries(fillersList).slice(0, 15).map(([word, count]) => `
                                <span class="px-3 py-1 bg-yellow-200 text-yellow-900 rounded-full text-sm">
                                    ${word} <span class="font-bold ml-1">×${count}</span>
                                </span>
                            `).join('')}
                        </div>
                    </div>
                ` : `
                    <div class="text-center py-6">
                        <div class="text-4xl mb-2">✨</div>
                        <p class="text-gray-600">No filler words detected! Your writing is concise.</p>
                    </div>
                `}
            </div>
        `;
    }
    
    // Clichés
    if (cliches) {
        const clichesList = cliches.cliches || [];
        const clicheCount = cliches.cliches_found || 0;
        
        html += `
            <div class="feature-card border-l-4 border-pink-500">
                <div class="flex items-center justify-between mb-3">
                    <h3 class="font-semibold text-gray-900 flex items-center">
                        <span class="text-2xl mr-2">💭</span> Cliché Detection
                    </h3>
                    <span class="px-3 py-1 ${clicheCount === 0 ? 'bg-green-100 text-green-700' : 'bg-pink-100 text-pink-700'} text-sm font-semibold rounded-full">
                        ${clicheCount} found
                    </span>
                </div>
                ${clicheCount > 0 ? `
                    <div class="space-y-2">
                        ${clichesList.slice(0, 8).map(cliche => `
                            <div class="bg-pink-50 border border-pink-200 rounded-lg p-3">
                                <div class="flex items-center justify-between">
                                    <span class="text-sm font-medium text-pink-900">"${cliche.cliche}"</span>
                                    <span class="text-xs text-pink-600">Position: ${cliche.start}</span>
                                </div>
                            </div>
                        `).join('')}
                        ${clichesList.length > 8 ? `<p class="text-sm text-gray-500 text-center">+ ${clichesList.length - 8} more</p>` : ''}
                    </div>
                    <div class="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <p class="text-sm text-blue-800"><strong>💡 Tip:</strong> Replace clichés with fresh, original expressions to make your writing more engaging.</p>
                    </div>
                ` : `
                    <div class="text-center py-6">
                        <div class="text-4xl mb-2">🎨</div>
                        <p class="text-gray-600">No clichés detected! Your writing is original.</p>
                    </div>
                `}
            </div>
        `;
    }
    
    // Paragraph Structure
    if (paragraph_structure) {
        const avgLength = paragraph_structure.average_words_per_paragraph || 0;
        const paragraphs = paragraph_structure.paragraph_count || 0;
        
        html += `
            <div class="feature-card border-l-4 border-indigo-500">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="text-2xl mr-2">📄</span> Paragraph Structure
                </h3>
                <div class="bg-indigo-50 rounded-lg p-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-white rounded-lg p-3 text-center">
                            <div class="text-2xl font-bold text-indigo-600">${paragraphs}</div>
                            <div class="text-xs text-gray-600">Paragraphs</div>
                        </div>
                        <div class="bg-white rounded-lg p-3 text-center">
                            <div class="text-2xl font-bold text-indigo-600">${avgLength.toFixed(0)}</div>
                            <div class="text-xs text-gray-600">Avg Sentences</div>
                        </div>
                    </div>
                    ${paragraph_structure.interpretation ? `
                        <p class="text-sm text-indigo-800 mt-3 bg-white bg-opacity-70 rounded p-2">${paragraph_structure.interpretation}</p>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    // Lexical Density
    if (lexical_density) {
        const density = lexical_density.lexical_density || 0;
        const contentWords = lexical_density.content_words || 0;
        const totalWords = lexical_density.total_words || 0;
        
        html += `
            <div class="feature-card border-l-4 border-teal-500">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="text-2xl mr-2">📊</span> Lexical Density
                </h3>
                <div class="bg-teal-50 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-4">
                        <div>
                            <div class="text-sm text-gray-600 mb-1">Density Score</div>
                            <div class="text-3xl font-bold text-teal-600">${(density * 100).toFixed(1)}%</div>
                        </div>
                        <div class="text-right text-sm text-gray-600">
                            <div>${contentWords} content words</div>
                            <div>out of ${totalWords} total</div>
                        </div>
                    </div>
                    <div class="relative h-4 bg-white rounded-full overflow-hidden">
                        <div class="absolute h-full bg-teal-500 transition-all duration-1000" style="width: ${density * 100}%"></div>
                    </div>
                    ${lexical_density.interpretation ? `
                        <p class="text-sm text-teal-800 mt-3">${lexical_density.interpretation}</p>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    // Sentence Rhythm
    if (sentence_rhythm) {
        const pattern = sentence_rhythm.pattern || 'unknown';
        const score = sentence_rhythm.rhythm_score || 0;
        
        html += `
            <div class="feature-card border-l-4 border-cyan-500">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="text-2xl mr-2">🎵</span> Sentence Rhythm
                </h3>
                <div class="bg-cyan-50 rounded-lg p-4">
                    <div class="grid grid-cols-2 gap-4 mb-3">
                        <div class="bg-white rounded-lg p-3 text-center">
                            <div class="text-2xl font-bold text-cyan-600 capitalize">${pattern}</div>
                            <div class="text-xs text-gray-600">Rhythm Pattern</div>
                        </div>
                        <div class="bg-white rounded-lg p-3 text-center">
                            <div class="text-2xl font-bold text-cyan-600">${score.toFixed(0)}</div>
                            <div class="text-xs text-gray-600">Rhythm Score</div>
                        </div>
                    </div>
                    ${sentence_rhythm.interpretation ? `
                        <p class="text-sm text-cyan-800 bg-white bg-opacity-70 rounded p-2">${sentence_rhythm.interpretation}</p>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

// ── Render Tone Tab ──
function renderTone() {
    const tone = analysisResults.tone_analysis;
    if (!tone || tone.error) {
        return `<div class="text-center py-12 text-gray-500">
            <div class="text-4xl mb-2">🎭</div>
            <p>Tone analysis unavailable${tone && tone.error ? ': ' + tone.error : ''}</p>
        </div>`;
    }

    const scores = tone.tone_scores || {};
    const dominant = tone.dominant_tone || 'professional';
    const label = tone.tone_label || dominant;
    const description = tone.tone_description || '';
    const color = tone.tone_color || '#3B82F6';
    const perSentence = tone.per_sentence || [];
    const defs = tone.tone_definitions || {};

    // Build radar-style bar chart
    const toneKeys = Object.keys(scores);
    const maxScore = Math.max(...Object.values(scores), 0.01);

    let barsHtml = toneKeys.map(key => {
        const val = scores[key] || 0;
        const pct = Math.round((val / 1) * 100); // 0-1 → 0-100
        const def = defs[key] || {};
        const c = def.color || '#6B7280';
        const active = key === dominant ? 'ring-2 ring-offset-1' : '';
        return `
            <div class="flex items-center gap-3 ${active} rounded-lg p-2" style="${key === dominant ? 'ring-color:' + c : ''}">
                <span class="w-28 text-sm font-medium text-gray-700 capitalize">${def.label || key}</span>
                <div class="flex-1 bg-gray-200 rounded-full h-3 relative overflow-hidden">
                    <div class="h-3 rounded-full transition-all duration-700" style="width:${pct}%; background:${c}"></div>
                </div>
                <span class="w-12 text-right text-sm font-semibold" style="color:${c}">${(val * 100).toFixed(0)}%</span>
            </div>
        `;
    }).join('');

    // Per-sentence tone trajectory
    let trajectoryHtml = '';
    if (perSentence.length > 0) {
        const sentRows = perSentence.map((s, idx) => {
            const sDef = defs[s.dominant] || {};
            const sColor = sDef.color || '#6B7280';
            return `
                <div class="flex items-start gap-3 py-2 border-b border-gray-100 last:border-0">
                    <span class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white" style="background:${sColor}">${idx + 1}</span>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm text-gray-700 truncate" title="${s.text}">${truncateText(s.text, 120)}</p>
                        <span class="text-xs font-medium capitalize" style="color:${sColor}">${sDef.label || s.dominant}</span>
                    </div>
                    <div class="flex-shrink-0 flex gap-0.5">
                        ${toneKeys.map(k => {
                            const sv = s.scores[k] || 0;
                            const sc = (defs[k] || {}).color || '#E5E7EB';
                            const opacity = Math.max(0.15, sv);
                            return `<div class="w-2 h-6 rounded-sm" style="background:${sc}; opacity:${opacity}" title="${k}: ${(sv*100).toFixed(0)}%"></div>`;
                        }).join('')}
                    </div>
                </div>
            `;
        }).join('');

        trajectoryHtml = `
            <div class="mt-6">
                <h4 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="text-lg mr-2">📈</span> Tone Trajectory (per sentence)
                </h4>
                <div class="bg-gray-50 rounded-lg p-4 max-h-80 overflow-y-auto space-y-0">
                    ${sentRows}
                </div>
            </div>
        `;
    }

    // Tone transformation result (if target tone was set)
    let transformHtml = '';
    const tt = analysisResults.tone_transformation || analysisResults.tone_analysis?.tone_transformation;
    if (tt && tt.transformed && tt.change_count > 0) {
        transformHtml = `
            <div class="mt-6 border-l-4 border-amber-500 rounded-lg bg-amber-50 p-4">
                <h4 class="font-semibold text-amber-900 mb-2 flex items-center">
                    <span class="text-lg mr-2">🔄</span> Tone Transformation → ${tt.tone_label || tt.target_tone}
                </h4>
                <p class="text-sm text-gray-700 mb-3">${tt.change_count} change(s) applied</p>
                <div class="bg-white rounded-lg p-3 text-sm text-gray-800 whitespace-pre-wrap">${tt.transformed}</div>
                ${tt.changes && tt.changes.length ? `
                    <div class="mt-3 space-y-1">
                        ${tt.changes.slice(0, 10).map(c => `
                            <div class="text-xs text-amber-800"><span class="line-through">${c.original}</span> → <span class="font-semibold">${c.replacement}</span></div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    return `
        <div class="space-y-6 animate-fade-in">
            <!-- Dominant Tone Header -->
            <div class="rounded-xl p-6" style="background: linear-gradient(135deg, ${color}15, ${color}30)">
                <div class="flex items-center justify-between mb-4">
                    <div>
                        <h3 class="text-xl font-bold text-gray-900 flex items-center">
                            <span class="text-3xl mr-3">🎭</span> Tone Analysis
                        </h3>
                        <p class="text-sm text-gray-600 mt-1">${description}</p>
                    </div>
                    <div class="text-center">
                        <div class="text-3xl font-bold capitalize" style="color:${color}">${label}</div>
                        <div class="text-xs text-gray-500">Dominant Tone</div>
                    </div>
                </div>

                <!-- Tone Scores Bar Chart -->
                <div class="space-y-2 mt-4">
                    ${barsHtml}
                </div>
            </div>

            ${trajectoryHtml}
            ${transformHtml}
        </div>
    `;
}

// Render Issues Tab
function renderIssues() {
    const { issues, consistency } = analysisResults;
    
    const longSentences = issues?.long_sentences || [];
    const repeatedWords = issues?.repeated_words || [];
    const consistencyIssues = consistency?.all_issues || [];
    
    const totalIssues = longSentences.length + repeatedWords.length + consistencyIssues.length;
    
    if (totalIssues === 0) {
        return `
            <div class="text-center py-12 animate-fade-in">
                <div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                    </svg>
                </div>
                <h3 class="text-2xl font-semibold text-gray-900">No Issues Found! 🎉</h3>
                <p class="text-gray-500 mt-2">Your text looks great!</p>
            </div>
        `;
    }
    
    let html = `<div class="space-y-6 animate-fade-in">`;
    
    // Long Sentences
    if (longSentences.length > 0) {
        html += `
            <div class="issue-section">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center mr-2">
                        <span class="text-yellow-600 font-bold">${longSentences.length}</span>
                    </span>
                    Long Sentences
                </h3>
                <div class="space-y-3">
                    ${longSentences.map((issue, idx) => `
                        <div class="border-l-4 border-yellow-400 bg-yellow-50 p-4 rounded-r-lg hover-lift">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-sm font-medium text-yellow-800">Sentence ${issue.index + 1}</span>
                                <span class="text-xs px-3 py-1 bg-yellow-200 text-yellow-800 rounded-full font-semibold">${issue.word_count} words</span>
                            </div>
                            <p class="text-sm text-gray-700">${truncateText(issue.sentence, 200)}</p>
                            <p class="text-xs text-yellow-700 mt-2">⚠️ Exceeds threshold by ${issue.excess} words. Consider breaking it into shorter sentences.</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Repeated Words
    if (repeatedWords.length > 0) {
        html += `
            <div class="issue-section">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-2">
                        <span class="text-blue-600 font-bold">${repeatedWords.length}</span>
                    </span>
                    Repeated Words
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                    ${repeatedWords.map(issue => `
                        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 hover-lift">
                            <div class="font-medium text-blue-900 text-lg">"${issue.word}"</div>
                            <div class="text-sm text-blue-700 mt-1">
                                <span class="font-semibold">${issue.count}</span> occurrences
                                <span class="text-blue-600 ml-2">(${issue.frequency.toFixed(1)}%)</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Consistency Issues
    if (consistencyIssues.length > 0) {
        html += `
            <div class="issue-section">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center mr-2">
                        <span class="text-purple-600 font-bold">${consistencyIssues.length}</span>
                    </span>
                    Narrative Consistency Issues
                </h3>
                <div class="space-y-3">
                    ${consistencyIssues.map(issue => `
                        <div class="border-l-4 border-purple-400 bg-purple-50 p-4 rounded-r-lg hover-lift">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-sm font-medium text-purple-800">${issue.issue || issue.type?.replace(/_/g, ' ') || 'Consistency Issue'}</span>
                                ${issue.severity ? `<span class="text-xs px-2 py-1 severity-${issue.severity} rounded-full">${issue.severity.toUpperCase()}</span>` : ''}
                            </div>
                            ${issue.original_text ? `
                                <div class="bg-white bg-opacity-70 rounded p-2 mb-2">
                                    <span class="text-xs text-purple-600 font-medium">Context:</span>
                                    <p class="text-sm text-gray-800">"${truncateText(issue.original_text, 150)}"</p>
                                </div>
                            ` : ''}
                            ${issue.suggestion ? `
                                <div class="mb-2">
                                    <span class="text-xs text-green-600 font-medium">💡 Suggestion:</span>
                                    <p class="text-sm text-gray-700">${issue.suggestion}</p>
                                </div>
                            ` : ''}
                            ${issue.explanation ? `
                                <div class="border-t border-purple-200 pt-2 mt-2">
                                    <span class="text-xs text-gray-500 font-medium">Why:</span>
                                    <p class="text-sm text-gray-600">${issue.explanation}</p>
                                </div>
                            ` : issue.message ? `<p class="text-sm text-gray-700">${issue.message}</p>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    html += `</div>`;
    return html;
}

// Render Suggestions Tab (continues from previous code)
function renderSuggestions() {
    const suggestions = analysisResults.suggestions || [];
    const explanationSuggestions = analysisResults.explanations?.suggestions || [];
    
    const allSuggestions = [...suggestions, ...explanationSuggestions];
    
    if (allSuggestions.length === 0) {
        return `
            <div class="text-center py-12 animate-fade-in">
                <div class="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-10 h-10 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                    </svg>
                </div>
                <h3 class="text-2xl font-semibold text-gray-900">No Suggestions</h3>
                <p class="text-gray-500 mt-2">Your writing is in excellent shape!</p>
            </div>
        `;
    }
    
    // Group by priority
    const byPriority = { high: [], medium: [], low: [] };
    allSuggestions.forEach(sug => {
        const priority = sug.priority || 'medium';
        if (byPriority[priority]) {
            byPriority[priority].push(sug);
        }
    });
    
    let html = `<div class="space-y-6 animate-fade-in">`;
    
    for (const [priority, items] of Object.entries(byPriority)) {
        if (items.length === 0) continue;
        
        const priorityIcons = {
            high: '🔴',
            medium: '🟡',
            low: '🟢'
        };
        
        html += `
            <div class="suggestion-section">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="px-3 py-1 text-sm rounded-full priority-${priority} mr-2">
                        ${priorityIcons[priority]} ${priority.toUpperCase()}
                    </span>
                    Priority Suggestions
                </h3>
                <div class="space-y-3">
                    ${items.map(sug => `
                        <div class="bg-white border border-gray-200 rounded-lg p-4 hover-lift">
                            <div class="flex items-start justify-between mb-2">
                                <span class="text-sm font-medium text-gray-900">${sug.action || sug.suggestion}</span>
                                <span class="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full whitespace-nowrap ml-2">${sug.category}</span>
                            </div>
                            ${sug.impact ? `
                                <div class="mb-2">
                                    <span class="text-xs text-blue-600 font-medium">📈 Impact:</span>
                                    <p class="text-sm text-gray-600">${sug.impact}</p>
                                </div>
                            ` : ''}
                            ${sug.how_to ? `
                                <div class="bg-blue-50 border-l-2 border-blue-400 pl-3 py-2 mt-2">
                                    <span class="text-xs text-blue-700 font-medium">ℹ️ How to:</span>
                                    <p class="text-sm text-blue-800">${sug.how_to}</p>
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    html += `</div>`;
    return html;
}

// Render Transform Tab
function renderTransform() {
    const transformation = analysisResults.style_transformation;
    
    if (!transformation || !transformation.transformed) {
        return `
            <div class="text-center py-12 animate-fade-in">
                <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/>
                    </svg>
                </div>
                <h3 class="text-2xl font-semibold text-gray-900">Style Transformation Disabled</h3>
                <p class="text-gray-500 mt-2">Enable "Style Transformation" in the feature toggles and re-analyze to see results.</p>
                ${renderStyleHeatmap()}
            </div>
        `;
    }
    
    const changes = transformation.changes || [];
    
    return `
        <div class="space-y-6 animate-fade-in">
            <!-- Transformation Summary -->
            <div class="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-4">
                <h3 class="font-semibold text-green-900 mb-2 flex items-center">
                    <span class="text-2xl mr-2">✅</span> Transformation Complete
                </h3>
                <p class="text-green-800">Made <strong>${transformation.change_count}</strong> changes to convert to <strong>${transformation.style}</strong> style.</p>
            </div>
            
            <!-- Side by Side Comparison -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <h4 class="font-medium text-gray-700 mb-2 flex items-center">
                        <span class="mr-2">📄</span> Original
                    </h4>
                    <div class="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap min-h-[200px] border-2 border-gray-200">${escapeHtml(transformation.original)}</div>
                </div>
                <div>
                    <h4 class="font-medium text-gray-700 mb-2 flex items-center">
                        <span class="mr-2">✨</span> Transformed
                    </h4>
                    <div class="bg-blue-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap min-h-[200px] border-2 border-blue-300">${escapeHtml(transformation.transformed)}</div>
                </div>
            </div>
            
            <!-- Changes Made -->
            ${changes.length > 0 ? `
            <div>
                <h4 class="font-medium text-gray-700 mb-3 flex items-center">
                    <span class="mr-2">🔄</span> Changes Made (${changes.length})
                </h4>
                <div class="space-y-2 max-h-96 overflow-y-auto custom-scrollbar">
                    ${changes.map((change, idx) => `
                        <div class="flex items-center text-sm bg-white rounded-lg p-3 border border-gray-200 hover-lift">
                            <span class="flex-shrink-0 w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center text-xs font-bold text-gray-600 mr-3">${idx + 1}</span>
                            <span class="diff-removed flex-shrink-0">${escapeHtml(change.original)}</span>
                            <svg class="w-5 h-5 text-gray-400 mx-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/>
                            </svg>
                            <span class="diff-added flex-shrink-0">${escapeHtml(change.replacement)}</span>
                            <span class="ml-auto text-xs text-gray-500 capitalize flex-shrink-0 pl-3">${change.type.replace(/_/g, ' ')}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            <!-- Copy Button -->
            <div class="flex justify-end space-x-3">
                <button onclick="copyOriginal()" class="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition">
                    📋 Copy Original
                </button>
                <button onclick="copyTransformed()" class="px-6 py-2 bg-primary text-white rounded-lg hover:bg-blue-600 transition shadow-lg">
                    ✨ Copy Transformed
                </button>
            </div>

            ${renderStyleHeatmap()}
        </div>
    `;
}

// Render Style Heatmap
function renderStyleHeatmap() {
    const styleScores = analysisResults.style_scores;
    if (!styleScores || styleScores.length === 0) return '';

    const dimensions = ['formality', 'casualness', 'creativity', 'persuasiveness', 'journalistic', 'narrative'];
    const dimColors = {
        formality: '#3B82F6',
        casualness: '#10B981',
        creativity: '#8B5CF6',
        persuasiveness: '#F59E0B',
        journalistic: '#6366F1',
        narrative: '#EC4899'
    };
    const dimEmojis = {
        formality: '🏛️',
        casualness: '😊',
        creativity: '🎨',
        persuasiveness: '💪',
        journalistic: '📰',
        narrative: '📖'
    };

    return `
        <div class="mt-8">
            <h4 class="font-semibold text-gray-900 mb-4 flex items-center text-lg">
                <span class="mr-2">🎨</span> Style Heatmap by Paragraph
            </h4>
            <div class="overflow-x-auto">
                <table class="w-full text-sm border-collapse">
                    <thead>
                        <tr>
                            <th class="text-left p-2 text-gray-600 font-medium border-b border-gray-200">Paragraph</th>
                            ${dimensions.map(d => `
                                <th class="p-2 text-center text-gray-600 font-medium border-b border-gray-200" title="${d}">
                                    ${dimEmojis[d]}<br><span class="text-xs">${d.charAt(0).toUpperCase() + d.slice(1)}</span>
                                </th>
                            `).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${styleScores.map((para, idx) => `
                            <tr class="hover:bg-gray-50">
                                <td class="p-2 border-b border-gray-100 max-w-[200px] truncate text-gray-700" title="${escapeHtml(para.text_preview)}">
                                    <span class="font-medium text-gray-500">P${idx + 1}</span> ${escapeHtml(para.text_preview)}
                                </td>
                                ${dimensions.map(d => {
                                    const score = para.scores[d] || 0;
                                    const opacity = Math.max(0.1, score / 100);
                                    const color = dimColors[d];
                                    return `
                                        <td class="p-2 border-b border-gray-100 text-center">
                                            <div class="inline-flex items-center justify-center w-10 h-10 rounded-lg text-xs font-bold"
                                                 style="background-color: ${color}${Math.round(opacity * 255).toString(16).padStart(2, '0')}; color: ${score > 50 ? 'white' : '#374151'}">
                                                ${score}
                                            </div>
                                        </td>
                                    `;
                                }).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <p class="text-xs text-gray-500 mt-2">Higher scores indicate stronger presence of that style dimension (0-100)</p>
        </div>
    `;
}

            </div>
            <p class="text-xs text-gray-500 mt-2">Higher scores indicate stronger presence of that style dimension (0-100)</p>
        </div>
    `;
}

// ── Render Narrative Tab (Phase 5) ──────────────────────────────────
function renderNarrative() {
    const nt = analysisResults.narrative_tracker;
    if (!nt || nt.error) {
        return `<div class="text-center py-12 text-gray-500">
            <p class="text-4xl mb-3">📖</p>
            <p class="font-medium">Narrative tracking data not available</p>
            <p class="text-sm mt-1">${nt?.error || 'Submit text to generate narrative analysis'}</p>
        </div>`;
    }

    let html = `<div class="space-y-6 animate-fade-in">`;

    // ── Summary Cards ─────────────────────────────────────────────
    const summary = nt.narrative_timeline?.summary || {};
    html += `
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
            ${_narrativeCard('📝', 'Events', summary.total_events ?? 0)}
            ${_narrativeCard('👤', 'Characters', summary.unique_characters ?? 0)}
            ${_narrativeCard('📍', 'Locations', summary.unique_locations ?? 0)}
            ${_narrativeCard('💬', 'Dialogue Lines', nt.dialogue?.total_quotes ?? 0)}
            ${_narrativeCard('⏱️', 'Pace Score', nt.pacing?.pace_score ?? '—')}
        </div>
    `;

    // ── Pacing ────────────────────────────────────────────────────
    if (nt.pacing) {
        const p = nt.pacing;
        html += `<div class="bg-white rounded-lg border p-4">
            <h3 class="font-semibold text-gray-900 mb-3">⏱️ Pacing Analysis</h3>
            <p class="text-sm text-gray-600 mb-3">${p.interpretation || ''}</p>
            <div class="grid grid-cols-3 gap-4 mb-2">`;
        for (const [type, ratio] of Object.entries(p.ratios || {})) {
            const pct = (ratio * 100).toFixed(1);
            const color = type === 'dialogue' ? 'blue' : type === 'action' ? 'red' : 'gray';
            html += `<div>
                <div class="flex justify-between text-xs mb-1">
                    <span class="capitalize">${type}</span><span>${pct}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-${color}-500 h-2 rounded-full" style="width:${pct}%"></div>
                </div>
            </div>`;
        }
        html += `</div>
            <p class="text-xs text-gray-400">Avg block length: ${p.avg_block_length ?? '—'} sentences</p>
        </div>`;
    }

    // ── Dialogue ──────────────────────────────────────────────────
    if (nt.dialogue && nt.dialogue.total_quotes > 0) {
        const d = nt.dialogue;
        html += `<div class="bg-white rounded-lg border p-4">
            <h3 class="font-semibold text-gray-900 mb-3">💬 Dialogue Breakdown</h3>
            <div class="flex gap-6 text-sm text-gray-600 mb-3">
                <span>Dialogue ratio: <strong>${(d.dialogue_ratio * 100).toFixed(1)}%</strong></span>
                <span>Narration ratio: <strong>${(d.narration_ratio * 100).toFixed(1)}%</strong></span>
            </div>`;
        if (Object.keys(d.speaker_lines || {}).length > 0) {
            html += `<h4 class="text-xs font-semibold text-gray-500 uppercase mb-2">Speaker Attribution</h4>
            <div class="flex flex-wrap gap-2">`;
            for (const [speaker, count] of Object.entries(d.speaker_lines)) {
                html += `<span class="px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-sm">${speaker}: ${count} line${count > 1 ? 's' : ''}</span>`;
            }
            html += `</div>`;
        }
        if (d.quotes && d.quotes.length > 0) {
            html += `<div class="mt-3 space-y-2 max-h-48 overflow-y-auto">`;
            for (const q of d.quotes.slice(0, 15)) {
                html += `<div class="text-sm border-l-2 border-blue-300 pl-3 py-1">
                    <span class="text-gray-800">"${_esc(q.content)}"</span>
                    ${q.speaker ? `<span class="text-xs text-gray-400 ml-2">— ${_esc(q.speaker)}</span>` : ''}
                </div>`;
            }
            if (d.quotes.length > 15) html += `<p class="text-xs text-gray-400">+${d.quotes.length - 15} more quotes</p>`;
            html += `</div>`;
        }
        html += `</div>`;
    }

    // ── Plot Events ───────────────────────────────────────────────
    if (nt.plot_events && nt.plot_events.length > 0) {
        html += `<div class="bg-white rounded-lg border p-4">
            <h3 class="font-semibold text-gray-900 mb-3">📝 Plot Events (${nt.plot_events.length})</h3>
            <div class="space-y-2 max-h-64 overflow-y-auto">`;
        for (const ev of nt.plot_events.slice(0, 20)) {
            const tenseBadge = ev.tense ? `<span class="text-xs px-1.5 py-0.5 rounded bg-purple-50 text-purple-600">${ev.tense}</span>` : '';
            html += `<div class="flex items-start gap-2 text-sm">
                <span class="text-gray-400 w-6 text-right shrink-0">#${ev.sentence_index}</span>
                <span class="font-medium text-indigo-700">${_esc(ev.subject || '?')}</span>
                <span class="text-gray-800">→ ${_esc(ev.verb_text)}</span>
                ${tenseBadge}
            </div>`;
        }
        if (nt.plot_events.length > 20) html += `<p class="text-xs text-gray-400 mt-1">+${nt.plot_events.length - 20} more events</p>`;
        html += `</div></div>`;
    }

    // ── Settings / Locations ──────────────────────────────────────
    if (nt.settings && nt.settings.length > 0) {
        html += `<div class="bg-white rounded-lg border p-4">
            <h3 class="font-semibold text-gray-900 mb-3">📍 Settings & Locations</h3>
            <div class="space-y-2 max-h-48 overflow-y-auto">`;
        for (const s of nt.settings) {
            const locs = (s.locations || []).map(l => `<span class="entity-tag entity-${l.type.toLowerCase()}">${_esc(l.text)}</span>`).join(' ');
            const spatial = (s.spatial_phrases || []).map(p => `<span class="text-xs text-gray-500 italic">${_esc(p)}</span>`).join(', ');
            html += `<div class="text-sm">
                <span class="text-gray-400 mr-2">#${s.sentence_index}</span>${locs} ${spatial}
            </div>`;
        }
        html += `</div></div>`;
    }

    // ── Narrative Timeline ────────────────────────────────────────
    if (nt.narrative_timeline?.timeline && nt.narrative_timeline.timeline.length > 0) {
        html += `<div class="bg-white rounded-lg border p-4">
            <h3 class="font-semibold text-gray-900 mb-3">🗺️ Narrative Timeline</h3>
            <div class="space-y-3 max-h-72 overflow-y-auto">`;
        for (const entry of nt.narrative_timeline.timeline.slice(0, 30)) {
            html += `<div class="flex gap-3 text-sm border-l-2 border-indigo-200 pl-3 py-1">
                <span class="text-gray-400 shrink-0 w-7 text-right">#${entry.sentence_index}</span>
                <div class="space-y-0.5">`;
            if (entry.characters) html += `<div>👤 ${entry.characters.map(c => `<span class="font-medium text-indigo-700">${_esc(c)}</span>`).join(', ')}</div>`;
            if (entry.events) html += `<div>⚡ ${entry.events.map(e => `${_esc(e.subject || '?')} → <em>${_esc(e.verb)}</em>`).join('; ')}</div>`;
            if (entry.locations) html += `<div>📍 ${entry.locations.map(l => _esc(l.text)).join(', ')}</div>`;
            if (entry.has_dialogue) html += `<div class="text-blue-500 text-xs">💬 dialogue</div>`;
            html += `</div></div>`;
        }
        if (nt.narrative_timeline.timeline.length > 30) html += `<p class="text-xs text-gray-400 mt-1">+${nt.narrative_timeline.timeline.length - 30} more entries</p>`;
        html += `</div></div>`;
    }

    // ── Character Memory ──────────────────────────────────────────
    if (nt.character_memory && Object.keys(nt.character_memory).length > 0) {
        html += `<div class="bg-white rounded-lg border p-4">
            <h3 class="font-semibold text-gray-900 mb-3">🧠 Character Memory</h3>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-3">`;
        for (const [key, data] of Object.entries(nt.character_memory)) {
            html += `<div class="p-3 rounded-lg bg-gray-50 border">
                <p class="font-medium text-gray-900">${_esc(data.canonical_name)}</p>
                <p class="text-xs text-gray-500">${data.type} · ${data.mention_count} mention${data.mention_count !== 1 ? 's' : ''}</p>
                <p class="text-xs text-gray-400">First seen: sentence #${data.first_mention_sentence ?? '?'}</p>
            </div>`;
        }
        html += `</div></div>`;
    }

    html += `</div>`;
    return html;
}

function _narrativeCard(emoji, label, value) {
    return `<div class="bg-white rounded-lg border p-3 text-center">
        <p class="text-2xl mb-1">${emoji}</p>
        <p class="text-lg font-bold text-gray-900">${value}</p>
        <p class="text-xs text-gray-500">${label}</p>
    </div>`;
}

function _esc(str) {
    if (!str) return '';
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Render Details Tab
function renderDetails() {
    const { readability, flow, consistency, text_analysis, scores } = analysisResults;
    
    let html = `<div class="space-y-6 animate-fade-in">`;
    
    // All Scores Overview
    if (scores) {
        html += `
            <div class="feature-card">
                <h3 class="font-semibold text-gray-900 mb-4 flex items-center">
                    <span class="text-2xl mr-2">🎯</span> All Scores
                </h3>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                    ${Object.entries(scores).map(([key, value]) => `
                        <div class="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 text-center">
                            <div class="text-3xl font-bold" style="color: ${getScoreColor(value)}">${value ? Math.round(value) : 'N/A'}</div>
                            <div class="text-xs text-gray-600 mt-1 capitalize">${key.replace(/_/g, ' ')}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Readability Details
    if (readability) {
        html += `
            <div class="feature-card">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="text-2xl mr-2">📖</span> Readability Scores
                </h3>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                    ${Object.entries(readability.scores || {}).map(([key, value]) => `
                        <div class="bg-gray-50 rounded-lg p-3 hover-lift">
                            <div class="text-xs text-gray-500 capitalize mb-1">${key.replace(/_/g, ' ')}</div>
                            <div class="text-xl font-semibold text-gray-900">${typeof value === 'number' ? value.toFixed(1) : value}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="feature-card">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="text-2xl mr-2">📊</span> Text Statistics
                </h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                    ${Object.entries(readability.statistics || {}).map(([key, value]) => `
                        <div class="bg-gray-50 rounded-lg p-3 hover-lift">
                            <div class="text-xs text-gray-500 capitalize mb-1">${key.replace(/_/g, ' ')}</div>
                            <div class="text-xl font-semibold text-gray-900">${typeof value === 'number' ? value.toFixed(2) : value}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Flow Details
    if (flow) {
        html += `
            <div class="feature-card">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="text-2xl mr-2">🌊</span> Flow Analysis
                </h3>
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <div class="text-sm text-gray-500">Flow Score</div>
                            <div class="text-3xl font-bold text-gray-900">${flow.flow_score ? flow.flow_score.toFixed(0) : 0}/100</div>
                        </div>
                        <div>
                            <div class="text-sm text-gray-500">Transition Words</div>
                            <div class="text-3xl font-bold text-gray-900">${flow.transition_count || 0}</div>
                        </div>
                    </div>
                    ${flow.transitions_found?.length > 0 ? `
                        <div class="text-sm text-gray-600 bg-white rounded p-3">
                            <strong>Transitions found:</strong> ${flow.transitions_found.slice(0, 15).join(', ')}${flow.transitions_found.length > 15 ? '...' : ''}
                        </div>
                    ` : ''}
                    <p class="text-sm text-gray-600 mt-3">${flow.assessment || ''}</p>
                </div>
            </div>
        `;
    }
    
    // Consistency Details
    if (consistency) {
        html += `
            <div class="feature-card">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="text-2xl mr-2">🎯</span> Consistency Analysis
                </h3>
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                        <div class="bg-white rounded p-3 text-center">
                            <div class="text-sm text-gray-500">Consistency Score</div>
                            <div class="text-3xl font-bold text-gray-900">${consistency.overall_consistency_score ? Math.round(consistency.overall_consistency_score) : 0}/100</div>
                        </div>
                        <div class="bg-white rounded p-3 text-center">
                            <div class="text-sm text-gray-500">Issues Found</div>
                            <div class="text-3xl font-bold text-gray-900">${consistency.total_issue_count || 0}</div>
                        </div>
                        <div class="bg-white rounded p-3 text-center">
                            <div class="text-sm text-gray-500">Entities Tracked</div>
                            <div class="text-3xl font-bold text-gray-900">${consistency.unique_entity_count || 0}</div>
                        </div>
                    </div>
                    <p class="text-sm text-gray-600">${consistency.assessment || ''}</p>
                </div>
            </div>
        `;
    }
    
    // Sentence Structures
    if (text_analysis?.sentence_structures) {
        const structures = text_analysis.sentence_structures;
        const typeCounts = structures.reduce((acc, s) => {
            acc[s.complexity] = (acc[s.complexity] || 0) + 1;
            return acc;
        }, {});
        
        html += `
            <div class="feature-card">
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="text-2xl mr-2">🏗️</span> Sentence Complexity Distribution
                </h3>
                <div class="grid grid-cols-3 gap-4">
                    <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 text-center hover-lift">
                        <div class="text-4xl font-bold text-green-600">${typeCounts.simple || 0}</div>
                        <div class="text-sm text-gray-600 mt-1">Simple</div>
                        <div class="text-xs text-gray-500">${structures.length ? ((typeCounts.simple || 0) / structures.length * 100).toFixed(0) : 0}%</div>
                    </div>
                    <div class="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg p-4 text-center hover-lift">
                        <div class="text-4xl font-bold text-yellow-600">${typeCounts.compound || 0}</div>
                        <div class="text-sm text-gray-600 mt-1">Compound</div>
                        <div class="text-xs text-gray-500">${structures.length ? ((typeCounts.compound || 0) / structures.length * 100).toFixed(0) : 0}%</div>
                    </div>
                    <div class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 text-center hover-lift">
                        <div class="text-4xl font-bold text-purple-600">${typeCounts.complex || 0}</div>
                        <div class="text-sm text-gray-600 mt-1">Complex</div>
                        <div class="text-xs text-gray-500">${structures.length ? ((typeCounts.complex || 0) / structures.length * 100).toFixed(0) : 0}%</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    html += `</div>`;
    return html;
}

// Copy functions
function copyOriginal() {
    if (analysisResults?.style_transformation?.original) {
        navigator.clipboard.writeText(analysisResults.style_transformation.original)
            .then(() => showToast(' Copied original text to clipboard!', 'success'))
            .catch(() => showToast('❌ Failed to copy', 'error'));
    }
}

function copyTransformed() {
    if (analysisResults?.style_transformation?.transformed) {
        navigator.clipboard.writeText(analysisResults.style_transformation.transformed)
            .then(() => showToast('✨ Copied transformed text to clipboard!', 'success'))
            .catch(() => showToast('❌ Failed to copy', 'error'));
    }
}

// Toast notification
function showToast(message, type = 'info') {
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    };
    
    const toast = document.createElement('div');
    toast.className = `${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg toast-enter`;
    toast.textContent = message;
    
    elements.toastContainer.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    }, 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('toast-enter');
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
