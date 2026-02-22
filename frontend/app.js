/**
 * Writing Assistant - Main Application JavaScript
 * Handles API communication, UI updates, and analysis rendering
 */

// Configuration
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    DEBOUNCE_DELAY: 300
};

// State
let analysisResults = null;
let currentTab = 'overview';

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
    thresholdSentence: document.getElementById('threshold-sentence'),
    thresholdRepeated: document.getElementById('threshold-repeated')
};

// Feature toggles
const featureToggles = {
    readability: document.getElementById('feat-readability'),
    flow: document.getElementById('feat-flow'),
    style: document.getElementById('feat-style'),
    consistency: document.getElementById('feat-consistency'),
    transform: document.getElementById('feat-transform')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    checkAPIHealth();
    updateCounts();
});

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
                <span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
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
        showToast('API is not available. Make sure the server is running.', 'error');
    }
}

// Update character and word counts
function updateCounts() {
    const text = elements.textInput.value;
    elements.charCount.textContent = text.length;
    elements.wordCount.textContent = text.trim() ? text.trim().split(/\s+/).length : 0;
}

// Clear all
function clearAll() {
    elements.textInput.value = '';
    updateCounts();
    elements.resultsContainer.classList.add('hidden');
    elements.scoresContainer.classList.add('hidden');
    analysisResults = null;
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
        explanations: true
    };
    
    const requestBody = {
        text: text,
        features: features,
        target_style: elements.targetStyle.value,
        long_sentence_threshold: parseInt(elements.thresholdSentence.value) || 100,
        repeated_word_min_count: parseInt(elements.thresholdRepeated.value) || 3
    };
    
    // Show loading
    elements.loadingOverlay.classList.remove('hidden');
    elements.analyzeBtn.disabled = true;
    
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
        
        // Display results
        displayResults();
        showToast('Analysis complete!', 'success');
        
    } catch (error) {
        console.error('Analysis error:', error);
        showToast(error.message || 'Failed to analyze text', 'error');
    } finally {
        elements.loadingOverlay.classList.add('hidden');
        elements.analyzeBtn.disabled = false;
    }
}

// Display results
function displayResults() {
    if (!analysisResults) return;
    
    // Show containers
    elements.resultsContainer.classList.remove('hidden');
    elements.scoresContainer.classList.remove('hidden');
    
    // Update scores
    updateScores(analysisResults.scores);
    
    // Render current tab
    renderTab(currentTab);
}

// Update score displays
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
        if (value !== undefined) {
            document.getElementById(config.el).textContent = Math.round(value);
            document.getElementById(config.bar).style.width = `${Math.min(100, value)}%`;
        }
    }
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
    activeBtn.classList.add('active', 'border-primary', 'text-primary');
    activeBtn.classList.remove('border-transparent', 'text-gray-500');
    
    // Render tab content
    renderTab(tabName);
}

// Render tab content
function renderTab(tabName) {
    if (!analysisResults) return;
    
    let content = '';
    
    switch (tabName) {
        case 'overview':
            content = renderOverview();
            break;
        case 'issues':
            content = renderIssues();
            break;
        case 'suggestions':
            content = renderSuggestions();
            break;
        case 'transform':
            content = renderTransform();
            break;
        case 'details':
            content = renderDetails();
            break;
    }
    
    elements.tabContent.innerHTML = content;
}

// Render Overview Tab
function renderOverview() {
    const { explanations, readability, style_analysis, text_analysis } = analysisResults;
    
    let html = `
        <div class="space-y-6">
            <!-- Summary -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 class="font-semibold text-blue-900 mb-2">Summary</h3>
                <p class="text-blue-800">${explanations?.summary || 'Analysis complete.'}</p>
            </div>
            
            <!-- Quick Stats -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-gray-50 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-gray-900">${text_analysis?.sentences?.length || 0}</div>
                    <div class="text-sm text-gray-500">Sentences</div>
                </div>
                <div class="bg-gray-50 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-gray-900">${text_analysis?.tokens?.length || 0}</div>
                    <div class="text-sm text-gray-500">Words</div>
                </div>
                <div class="bg-gray-50 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-gray-900">${text_analysis?.entities?.length || 0}</div>
                    <div class="text-sm text-gray-500">Entities</div>
                </div>
                <div class="bg-gray-50 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-gray-900">${readability?.reading_time_minutes || 0}</div>
                    <div class="text-sm text-gray-500">Min Read</div>
                </div>
            </div>
            
            <!-- Readability -->
            ${readability ? `
            <div>
                <h3 class="font-semibold text-gray-900 mb-3">Readability</h3>
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm text-gray-600">Grade Level</span>
                        <span class="font-semibold">${readability.grade_level}</span>
                    </div>
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm text-gray-600">Difficulty</span>
                        <span class="font-semibold capitalize">${readability.difficulty}</span>
                    </div>
                    <p class="text-sm text-gray-600 mt-3">${readability.interpretation}</p>
                </div>
            </div>
            ` : ''}
            
            <!-- Style -->
            ${style_analysis ? `
            <div>
                <h3 class="font-semibold text-gray-900 mb-3">Writing Style</h3>
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm text-gray-600">Detected Style</span>
                        <span class="font-semibold capitalize">${style_analysis.dominant_style}</span>
                    </div>
                    <p class="text-sm text-gray-600 mt-3">${style_analysis.recommendation || ''}</p>
                </div>
            </div>
            ` : ''}
            
            <!-- Entities -->
            ${text_analysis?.entities?.length > 0 ? `
            <div>
                <h3 class="font-semibold text-gray-900 mb-3">Named Entities</h3>
                <div class="flex flex-wrap gap-2">
                    ${text_analysis.entities.map(([text, label]) => `
                        <span class="entity-tag entity-${label}">${text} <span class="opacity-60">(${label})</span></span>
                    `).join('')}
                </div>
            </div>
            ` : ''}
        </div>
    `;
    
    return html;
}

// Render Issues Tab
function renderIssues() {
    const { issues, explanations } = analysisResults;
    
    const longSentences = issues?.long_sentences || [];
    const repeatedWords = issues?.repeated_words || [];
    const consistencyIssues = analysisResults.consistency?.all_issues || [];
    
    const totalIssues = longSentences.length + repeatedWords.length + consistencyIssues.length;
    
    if (totalIssues === 0) {
        return `
            <div class="text-center py-12">
                <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                    </svg>
                </div>
                <h3 class="font-semibold text-gray-900">No Issues Found</h3>
                <p class="text-gray-500 mt-2">Your text looks great!</p>
            </div>
        `;
    }
    
    let html = `<div class="space-y-6">`;
    
    // Long Sentences
    if (longSentences.length > 0) {
        html += `
            <div>
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="w-6 h-6 bg-yellow-100 rounded-full flex items-center justify-center mr-2">
                        <span class="text-yellow-600 text-sm font-bold">${longSentences.length}</span>
                    </span>
                    Long Sentences
                </h3>
                <div class="space-y-3">
                    ${longSentences.map((issue, idx) => `
                        <div class="border-l-4 border-yellow-400 bg-yellow-50 p-4 rounded-r-lg">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-sm font-medium text-yellow-800">Sentence ${issue.index + 1}</span>
                                <span class="text-xs px-2 py-1 bg-yellow-200 text-yellow-800 rounded-full">${issue.word_count} words</span>
                            </div>
                            <p class="text-sm text-gray-700">${truncateText(issue.sentence, 200)}</p>
                            <p class="text-xs text-yellow-700 mt-2">Exceeds threshold by ${issue.excess} words</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Repeated Words
    if (repeatedWords.length > 0) {
        html += `
            <div>
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mr-2">
                        <span class="text-blue-600 text-sm font-bold">${repeatedWords.length}</span>
                    </span>
                    Repeated Words
                </h3>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                    ${repeatedWords.map(issue => `
                        <div class="bg-blue-50 border border-blue-200 rounded-lg p-3">
                            <div class="font-medium text-blue-900">"${issue.word}"</div>
                            <div class="text-sm text-blue-700">${issue.count} occurrences (${issue.frequency}%)</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Consistency Issues
    if (consistencyIssues.length > 0) {
        html += `
            <div>
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center mr-2">
                        <span class="text-purple-600 text-sm font-bold">${consistencyIssues.length}</span>
                    </span>
                    Narrative Consistency Issues
                </h3>
                <div class="space-y-3">
                    ${consistencyIssues.map(issue => `
                        <div class="border-l-4 border-purple-400 bg-purple-50 p-4 rounded-r-lg">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-sm font-medium text-purple-800">${issue.issue || issue.type?.replace(/_/g, ' ') || 'Consistency Issue'}</span>
                                ${issue.severity ? `<span class="text-xs px-2 py-1 severity-${issue.severity} rounded-full">${issue.severity}</span>` : ''}
                            </div>
                            ${issue.original_text ? `
                                <div class="bg-white bg-opacity-50 rounded p-2 mb-2">
                                    <span class="text-xs text-purple-600 font-medium">Original:</span>
                                    <p class="text-sm text-gray-800">"${truncateText(issue.original_text, 150)}"</p>
                                </div>
                            ` : ''}
                            ${issue.suggestion ? `
                                <div class="mb-2">
                                    <span class="text-xs text-green-600 font-medium">Suggestion:</span>
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

// Render Suggestions Tab
function renderSuggestions() {
    const suggestions = analysisResults.suggestions || [];
    const explanationSuggestions = analysisResults.explanations?.suggestions || [];
    
    const allSuggestions = [...suggestions, ...explanationSuggestions];
    
    if (allSuggestions.length === 0) {
        return `
            <div class="text-center py-12">
                <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                    </svg>
                </div>
                <h3 class="font-semibold text-gray-900">No Suggestions</h3>
                <p class="text-gray-500 mt-2">Your writing is in good shape!</p>
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
    
    let html = `<div class="space-y-6">`;
    
    for (const [priority, items] of Object.entries(byPriority)) {
        if (items.length === 0) continue;
        
        html += `
            <div>
                <h3 class="font-semibold text-gray-900 mb-3 flex items-center">
                    <span class="px-2 py-1 text-xs rounded-full priority-${priority} mr-2">${priority.toUpperCase()}</span>
                    Priority Suggestions
                </h3>
                <div class="space-y-3">
                    ${items.map(sug => `
                        <div class="bg-white border border-gray-200 rounded-lg p-4 hover-lift">
                            <div class="flex items-start justify-between mb-2">
                                <span class="text-sm font-medium text-gray-900">${sug.action || sug.suggestion}</span>
                                <span class="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full">${sug.category}</span>
                            </div>
                            ${sug.impact ? `<p class="text-sm text-gray-600 mb-2"><strong>Impact:</strong> ${sug.impact}</p>` : ''}
                            ${sug.how_to ? `<p class="text-sm text-gray-500"><strong>How to:</strong> ${sug.how_to}</p>` : ''}
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
            <div class="text-center py-12">
                <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/>
                    </svg>
                </div>
                <h3 class="font-semibold text-gray-900">Style Transformation Disabled</h3>
                <p class="text-gray-500 mt-2">Enable "Style Transformation" in the feature toggles and re-analyze to see results.</p>
            </div>
        `;
    }
    
    const changes = transformation.changes || [];
    
    return `
        <div class="space-y-6">
            <!-- Transformation Summary -->
            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 class="font-semibold text-green-900 mb-2">Transformation Complete</h3>
                <p class="text-green-800">Made ${transformation.change_count} changes to convert to ${transformation.style} style.</p>
            </div>
            
            <!-- Side by Side Comparison -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <h4 class="font-medium text-gray-700 mb-2">Original</h4>
                    <div class="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap">${escapeHtml(transformation.original)}</div>
                </div>
                <div>
                    <h4 class="font-medium text-gray-700 mb-2">Transformed</h4>
                    <div class="bg-blue-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap">${escapeHtml(transformation.transformed)}</div>
                </div>
            </div>
            
            <!-- Changes Made -->
            ${changes.length > 0 ? `
            <div>
                <h4 class="font-medium text-gray-700 mb-3">Changes Made (${changes.length})</h4>
                <div class="space-y-2 max-h-64 overflow-y-auto">
                    ${changes.map(change => `
                        <div class="flex items-center text-sm bg-gray-50 rounded-lg p-3">
                            <span class="diff-removed">${change.original}</span>
                            <svg class="w-4 h-4 text-gray-400 mx-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/>
                            </svg>
                            <span class="diff-added">${change.replacement}</span>
                            <span class="ml-auto text-xs text-gray-500 capitalize">${change.type.replace(/_/g, ' ')}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            <!-- Copy Button -->
            <div class="flex justify-end">
                <button onclick="copyTransformed()" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-600 transition">
                    Copy Transformed Text
                </button>
            </div>
        </div>
    `;
}

// Render Details Tab
function renderDetails() {
    const { readability, flow, consistency, text_analysis } = analysisResults;
    
    let html = `<div class="space-y-6">`;
    
    // Readability Details
    if (readability) {
        html += `
            <div>
                <h3 class="font-semibold text-gray-900 mb-3">Readability Scores</h3>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                    ${Object.entries(readability.scores || {}).map(([key, value]) => `
                        <div class="bg-gray-50 rounded-lg p-3">
                            <div class="text-xs text-gray-500 capitalize">${key.replace(/_/g, ' ')}</div>
                            <div class="text-lg font-semibold text-gray-900">${typeof value === 'number' ? value.toFixed(1) : value}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div>
                <h3 class="font-semibold text-gray-900 mb-3">Text Statistics</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                    ${Object.entries(readability.statistics || {}).map(([key, value]) => `
                        <div class="bg-gray-50 rounded-lg p-3">
                            <div class="text-xs text-gray-500 capitalize">${key.replace(/_/g, ' ')}</div>
                            <div class="text-lg font-semibold text-gray-900">${typeof value === 'number' ? value.toFixed(1) : value}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Flow Details
    if (flow) {
        html += `
            <div>
                <h3 class="font-semibold text-gray-900 mb-3">Flow Analysis</h3>
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <div class="text-sm text-gray-500">Flow Score</div>
                            <div class="text-2xl font-bold text-gray-900">${flow.flow_score}/100</div>
                        </div>
                        <div>
                            <div class="text-sm text-gray-500">Transition Words</div>
                            <div class="text-2xl font-bold text-gray-900">${flow.transition_count}</div>
                        </div>
                    </div>
                    ${flow.transitions_found?.length > 0 ? `
                        <div class="text-sm text-gray-600">
                            <strong>Transitions found:</strong> ${flow.transitions_found.slice(0, 10).join(', ')}${flow.transitions_found.length > 10 ? '...' : ''}
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
            <div>
                <h3 class="font-semibold text-gray-900 mb-3">Consistency Analysis</h3>
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <div class="text-sm text-gray-500">Consistency Score</div>
                            <div class="text-2xl font-bold text-gray-900">${consistency.overall_consistency_score}/100</div>
                        </div>
                        <div>
                            <div class="text-sm text-gray-500">Issues Found</div>
                            <div class="text-2xl font-bold text-gray-900">${consistency.total_issue_count || 0}</div>
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
            <div>
                <h3 class="font-semibold text-gray-900 mb-3">Sentence Complexity</h3>
                <div class="grid grid-cols-3 gap-3">
                    <div class="bg-green-50 rounded-lg p-3 text-center">
                        <div class="text-2xl font-bold text-green-600">${typeCounts.simple || 0}</div>
                        <div class="text-sm text-gray-600">Simple</div>
                    </div>
                    <div class="bg-yellow-50 rounded-lg p-3 text-center">
                        <div class="text-2xl font-bold text-yellow-600">${typeCounts.compound || 0}</div>
                        <div class="text-sm text-gray-600">Compound</div>
                    </div>
                    <div class="bg-purple-50 rounded-lg p-3 text-center">
                        <div class="text-2xl font-bold text-purple-600">${typeCounts.complex || 0}</div>
                        <div class="text-sm text-gray-600">Complex</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    html += `</div>`;
    return html;
}

// Copy transformed text
function copyTransformed() {
    if (analysisResults?.style_transformation?.transformed) {
        navigator.clipboard.writeText(analysisResults.style_transformation.transformed)
            .then(() => showToast('Copied to clipboard!', 'success'))
            .catch(() => showToast('Failed to copy', 'error'));
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
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function generatePlot() {
    const text = document.getElementById("inputText").value;

    const response = await fetch("http://localhost:8000/generate-plot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ previous_plots: text })
    });

    const data = await response.json();

    document.getElementById("plotOutput").innerText =
        data.generated_plot + "\nTension Score: " + data.tension_score;
}
