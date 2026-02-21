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
        explanations: true
    };
    
    const requestBody = {
        text: text,
        features: features,
        target_style: elements.targetStyle.value,
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
        case 'overview':
            content = renderOverview();
            break;
        case 'issues':
            content = renderIssues();
            break;
        case 'enhancements':
            content = renderEnhancements();
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
    
    // Fade in animation
    elements.tabContent.style.opacity = '0';
    requestAnimationFrame(() => {
        elements.tabContent.style.transition = 'opacity 0.3s ease';
        elements.tabContent.style.opacity = '1';
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
        </div>
    `;
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
