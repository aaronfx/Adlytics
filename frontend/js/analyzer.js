// ============================================
// ADLYTICS v4.1 - COMPLETE FIXED VERSION
// All tabs working, all data rendering
// ============================================

// Global variables
let currentContentMode = 'adCopy';
let analysisResults = null;
let currentTab = 'behavior';

// DOM Elements
let form, analyzeBtn, resultsSection, loadingIndicator;
let tabButtons, tabContents;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 ADLYTICS v4.1 Initializing...');

    // Assign DOM elements
    form = document.getElementById('analyzeForm');
    analyzeBtn = document.getElementById('analyzeBtn');
    resultsSection = document.getElementById('resultsSection');
    loadingIndicator = document.getElementById('loadingIndicator');

    console.log('DOM Elements assigned:', { 
        form: !!form, 
        analyzeBtn: !!analyzeBtn, 
        resultsSection: !!resultsSection 
    });

    // Setup event listeners
    setupEventListeners();
    setupTabs();

    console.log('✅ ADLYTICS v4.1 Initialized');
});

// ============================================
// TAB SYSTEM (FIXED)
// ============================================
function setupTabs() {
    console.log('Setting up tabs...');

    // Get all tab buttons
    tabButtons = document.querySelectorAll('.tab-btn');
    tabContents = document.querySelectorAll('.tab-content');

    console.log(`Found ${tabButtons.length} tab buttons and ${tabContents.length} tab contents`);

    // Add click handlers to tab buttons
    tabButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const tabId = btn.dataset.tab;
            console.log('Tab clicked:', tabId);
            switchTab(tabId);
        });
    });

    // Show first tab by default
    if (tabButtons.length > 0) {
        switchTab(tabButtons[0].dataset.tab);
    }
}

function switchTab(tabId) {
    console.log('Switching to tab:', tabId);
    currentTab = tabId;

    // Update button states
    tabButtons.forEach(btn => {
        if (btn.dataset.tab === tabId) {
            btn.classList.add('active');
            btn.style.background = '#3b82f6';
            btn.style.color = 'white';
        } else {
            btn.classList.remove('active');
            btn.style.background = '';
            btn.style.color = '';
        }
    });

    // Show/hide content
    tabContents.forEach(content => {
        if (content.id === `tab-${tabId}`) {
            content.style.display = 'block';
            content.classList.add('active');
        } else {
            content.style.display = 'none';
            content.classList.remove('active');
        }
    });
}

// ============================================
// EVENT LISTENERS
// ============================================
function setupEventListeners() {
    console.log('Setting up event listeners...');

    // Form submission
    if (form) {
        form.addEventListener('submit', handleSubmit);
    }

    // Content mode tabs
    document.querySelectorAll('.content-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.dataset.mode;
            console.log('Content mode changed to:', mode);
            currentContentMode = mode;

            // Update active state
            document.querySelectorAll('.content-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Show/hide textareas
            document.getElementById('adCopyContainer').style.display = mode === 'adCopy' ? 'block' : 'none';
            document.getElementById('videoScriptContainer').style.display = mode === 'videoScript' ? 'block' : 'none';
        });
    });
}

// ============================================
// FORM SUBMISSION
// ============================================
async function handleSubmit(e) {
    e.preventDefault();
    console.log('📝 Form submitted');

    // Show loading
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    if (analyzeBtn) analyzeBtn.disabled = true;

    try {
        const formData = new FormData(form);

        // Add content based on mode
        const adCopy = document.getElementById('adCopy')?.value?.trim() || '';
        const videoScript = document.getElementById('videoScript')?.value?.trim() || '';

        console.log('Content mode:', currentContentMode);
        console.log('Ad Copy length:', adCopy.length);
        console.log('Video Script length:', videoScript.length);

        if (currentContentMode === 'adCopy' && adCopy) {
            formData.set('ad_copy', adCopy);
        } else if (currentContentMode === 'videoScript' && videoScript) {
            formData.set('video_script', videoScript);
        }

        // Send request
        console.log('📤 Sending request to:', '/api/analyze');
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        console.log('📥 Response status:', response.status);
        const data = await response.json();
        console.log('📥 Response data:', data);

        if (data.success) {
            analysisResults = data.analysis;
            renderResults(analysisResults);
            if (resultsSection) resultsSection.style.display = 'block';
        } else {
            alert('Analysis failed: ' + (data.error || 'Unknown error'));
        }

    } catch (error) {
        console.error('❌ Error:', error);
        alert('Error: ' + error.message);
    } finally {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (analyzeBtn) analyzeBtn.disabled = false;
    }
}

// ============================================
// RENDER RESULTS (COMPLETE)
// ============================================
function renderResults(analysis) {
    console.log('🎨 Rendering results:', analysis);

    if (!analysis) {
        console.error('No analysis data to render');
        return;
    }

    // Get scores
    const scores = analysis.scores || {};
    const overallScore = scores.overall || 0;

    // Update Overall Score
    const overallScoreEl = document.getElementById('overallScore');
    if (overallScoreEl) {
        overallScoreEl.textContent = overallScore;
        overallScoreEl.style.color = overallScore >= 70 ? '#22c55e' : overallScore >= 50 ? '#f59e0b' : '#ef4444';
    }

    // Update Score Circle
    const scoreCircle = document.getElementById('scoreCircle');
    if (scoreCircle) {
        scoreCircle.textContent = overallScore;
        scoreCircle.style.background = overallScore >= 70 ? '#22c55e' : overallScore >= 50 ? '#f59e0b' : '#ef4444';
    }

    // Update Verdict
    const verdictEl = document.getElementById('verdictBadge');
    if (verdictEl) {
        const verdict = analysis.run_decision?.verdict || 'REVIEW';
        verdictEl.textContent = verdict;
        verdictEl.className = `verdict-badge ${verdict.toLowerCase()}`;
    }

    // Update Launch Readiness
    const readinessEl = document.getElementById('launchReadiness');
    if (readinessEl) {
        const readiness = analysis.run_decision?.readiness || 0;
        readinessEl.textContent = readiness + '%';
        readinessEl.style.width = readiness + '%';
    }

    // Update Failure Risk
    const riskEl = document.getElementById('failureRisk');
    if (riskEl) {
        const risk = analysis.run_decision?.risk || 0;
        riskEl.textContent = risk + '%';
        riskEl.style.width = risk + '%';
    }

    // Update Performance Breakdown
    renderPerformanceBreakdown(scores);

    // Update Phase Breakdown
    renderPhaseBreakdown(analysis.phase_breakdown);

    // Update Behavior Summary
    renderBehaviorSummary(analysis.behavior_summary);

    // Update Line by Line Analysis
    renderLineByLine(analysis.line_by_line_analysis);

    // Update Critical Weaknesses
    renderWeaknesses(analysis.critical_weaknesses);

    // Update Improvements
    renderImprovements(analysis.improvements);

    // Update Improved Ad
    renderImprovedAd(analysis.improved_ad);

    // Update Ad Variants
    renderAdVariants(analysis.ad_variants);

    // Update Winner Prediction
    renderWinnerPrediction(analysis.winner_prediction);

    // Update Persona Reactions
    renderPersonaReactions(analysis.persona_reactions);

    // Update ROI Analysis
    renderROIAnalysis(analysis.roi_analysis);

    // Update Video Execution
    renderVideoExecution(analysis.video_execution_analysis);

    console.log('✅ Results rendered');
}

// ============================================
// RENDER HELPERS
// ============================================
function renderPerformanceBreakdown(scores) {
    const container = document.getElementById('performanceBreakdown');
    if (!container) return;

    const metrics = [
        { key: 'hook_strength', label: 'Hook Strength', weight: '25%' },
        { key: 'clarity', label: 'Clarity', weight: '20%' },
        { key: 'trust_building', label: 'Trust Building', weight: '20%' },
        { key: 'cta_power', label: 'CTA Power', weight: '15%' },
        { key: 'audience_alignment', label: 'Audience Alignment', weight: '20%' }
    ];

    container.innerHTML = metrics.map(m => {
        const score = scores[m.key] || 0;
        const color = score >= 70 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444';
        return `
            <div class="metric-row">
                <div class="metric-label">${m.label} <span class="weight">(${m.weight})</span></div>
                <div class="metric-bar-container">
                    <div class="metric-bar" style="width: ${score}%; background: ${color};"></div>
                </div>
                <div class="metric-score" style="color: ${color};">${score}</div>
            </div>
        `;
    }).join('');
}

function renderPhaseBreakdown(phases) {
    const container = document.getElementById('phaseBreakdown');
    if (!container || !phases) return;

    const phaseData = phases.phases || [];
    container.innerHTML = phaseData.map((phase, idx) => `
        <div class="phase-item">
            <div class="phase-number">${idx + 1}</div>
            <div class="phase-content">
                <div class="phase-name">${phase.name}</div>
                <div class="phase-score">${phase.score}/100</div>
                <div class="phase-bar">
                    <div class="phase-fill" style="width: ${phase.score}%"></div>
                </div>
            </div>
        </div>
    `).join('');
}

function renderBehaviorSummary(summary) {
    const container = document.getElementById('behaviorSummary');
    if (!container) return;

    container.innerHTML = `
        <div class="summary-section">
            <h4>Attention Capture</h4>
            <p>${summary?.attention_capture || 'N/A'}</p>
        </div>
        <div class="summary-section">
            <h4>Interest Maintenance</h4>
            <p>${summary?.interest_maintenance || 'N/A'}</p>
        </div>
        <div class="summary-section">
            <h4>Desire Generation</h4>
            <p>${summary?.desire_generation || 'N/A'}</p>
        </div>
        <div class="summary-section">
            <h4>Action Motivation</h4>
            <p>${summary?.action_motivation || 'N/A'}</p>
        </div>
    `;
}

function renderLineByLine(lines) {
    const container = document.getElementById('lineByLineAnalysis');
    if (!container || !lines) {
        if (container) container.innerHTML = '<p>No line-by-line analysis available.</p>';
        return;
    }

    container.innerHTML = lines.map(line => `
        <div class="line-item">
            <div class="line-text">"${line.text}"</div>
            <div class="line-analysis">
                <span class="line-score">Score: ${line.score}/100</span>
                <span class="line-issue">${line.issue || 'No issues'}</span>
            </div>
        </div>
    `).join('');
}

function renderWeaknesses(weaknesses) {
    const container = document.getElementById('criticalWeaknesses');
    if (!container) return;

    if (!weaknesses || weaknesses.length === 0) {
        container.innerHTML = '<p class="no-issues">✅ No critical weaknesses found!</p>';
        return;
    }

    container.innerHTML = weaknesses.map(w => `
        <div class="weakness-item">
            <div class="weakness-severity severity-${w.severity}">${w.severity}</div>
            <div class="weakness-content">
                <div class="weakness-title">${w.title}</div>
                <div class="weakness-description">${w.description}</div>
                <div class="weakness-fix">💡 Fix: ${w.fix}</div>
            </div>
        </div>
    `).join('');
}

function renderImprovements(improvements) {
    const container = document.getElementById('improvementsList');
    if (!container) return;

    if (!improvements || improvements.length === 0) {
        container.innerHTML = '<p>No specific improvements suggested.</p>';
        return;
    }

    container.innerHTML = improvements.map((imp, idx) => `
        <div class="improvement-item">
            <div class="improvement-number">${idx + 1}</div>
            <div class="improvement-text">${imp}</div>
        </div>
    `).join('');
}

function renderImprovedAd(improvedAd) {
    const container = document.getElementById('improvedAdContent');
    if (!container || !improvedAd) {
        if (container) container.innerHTML = '<p>No improved ad available.</p>';
        return;
    }

    container.innerHTML = `
        <div class="improved-section">
            <label>Headline/Hook:</label>
            <div class="improved-text">${improvedAd.headline || 'N/A'}</div>
        </div>
        <div class="improved-section">
            <label>Body Copy:</label>
            <div class="improved-text">${improvedAd.body_copy || 'N/A'}</div>
        </div>
        <div class="improved-section">
            <label>CTA:</label>
            <div class="improved-text">${improvedAd.cta || 'N/A'}</div>
        </div>
        <div class="improved-meta">
            <span class="improved-score">Predicted Score: ${improvedAd.predicted_score || 0}/100</span>
            <span class="improved-roi">ROI: ${improvedAd.roi_potential || 'N/A'}</span>
        </div>
        <button class="copy-btn" onclick="copyImprovedAd()">📋 Copy Full Ad</button>
    `;
}

function renderAdVariants(variants) {
    const container = document.getElementById('adVariantsList');
    if (!container || !variants) {
        if (container) container.innerHTML = '<p>No variants generated.</p>';
        return;
    }

    container.innerHTML = variants.map((v, idx) => `
        <div class="variant-card ${idx === 0 ? 'best' : ''}">
            <div class="variant-header">
                <span class="variant-number">Variant #${v.id}</span>
                <span class="variant-angle">${v.angle}</span>
                <span class="variant-score">${v.predicted_score}/100</span>
            </div>
            <div class="variant-hook">${v.hook}</div>
            <div class="variant-copy">${v.copy}</div>
            <div class="variant-roi">ROI Potential: ${v.roi_potential}</div>
            <div class="variant-reason">${v.reason}</div>
            ${idx === 0 ? '<div class="variant-badge">🏆 BEST</div>' : ''}
        </div>
    `).join('');
}

function renderWinnerPrediction(prediction) {
    const container = document.getElementById('winnerPrediction');
    if (!container || !prediction) {
        if (container) container.innerHTML = '<p>No winner prediction available.</p>';
        return;
    }

    container.innerHTML = `
        <div class="winner-card">
            <div class="winner-confidence">${prediction.confidence} Confidence</div>
            <div class="winner-reason">${prediction.reason}</div>
            <div class="winner-expected">Expected Lift: ${prediction.expected_lift || 'N/A'}</div>
        </div>
    `;
}

function renderPersonaReactions(personas) {
    const container = document.getElementById('personaReactions');
    if (!container || !personas) {
        if (container) container.innerHTML = '<p>No persona data available.</p>';
        return;
    }

    container.innerHTML = personas.map(p => `
        <div class="persona-card">
            <div class="persona-name">${p.name}</div>
            <div class="persona-reaction ${p.reaction.toLowerCase()}">${p.reaction}</div>
            <div class="persona-thought">"${p.thought}"</div>
        </div>
    `).join('');
}

function renderROIAnalysis(roi) {
    const container = document.getElementById('roiAnalysis');
    if (!container || !roi) {
        if (container) container.innerHTML = '<p>No ROI analysis available.</p>';
        return;
    }

    container.innerHTML = `
        <div class="roi-grid">
            <div class="roi-item">
                <label>Expected ROAS:</label>
                <value>${roi.roas || 'N/A'}</value>
            </div>
            <div class="roi-item">
                <label>Break-even:</label>
                <value>${roi.break_even || 'N/A'}</value>
            </div>
            <div class="roi-item">
                <label>Risk Level:</label>
                <value class="risk-${(roi.risk || '').toLowerCase()}">${roi.risk || 'N/A'}</value>
            </div>
            <div class="roi-item">
                <label>Confidence:</label>
                <value>${roi.confidence || 'N/A'}</value>
            </div>
        </div>
    `;
}

function renderVideoExecution(videoAnalysis) {
    const container = document.getElementById('videoExecution');
    if (!container) return;

    if (!videoAnalysis) {
        container.innerHTML = '<p>No video execution analysis available.</p>';
        return;
    }

    container.innerHTML = `
        <div class="video-analysis">
            <div class="video-section">
                <h4>Hook Delivery</h4>
                <p>${videoAnalysis.hook_delivery || 'N/A'}</p>
            </div>
            <div class="video-section">
                <h4>Speech Flow</h4>
                <p>${videoAnalysis.speech_flow || 'N/A'}</p>
            </div>
            <div class="video-section">
                <h4>Visual Dependency</h4>
                <p>${videoAnalysis.visual_dependency || 'N/A'}</p>
            </div>
            <div class="video-section">
                <h4>Delivery Risk</h4>
                <p>${videoAnalysis.delivery_risk || 'N/A'}</p>
            </div>
            <div class="video-section">
                <h4>Format Recommendation</h4>
                <p>${videoAnalysis.format_recommendation || 'N/A'}</p>
            </div>
        </div>
    `;
}

// ============================================
// UTILITY FUNCTIONS
// ============================================
function copyImprovedAd() {
    if (!analysisResults?.improved_ad) return;

    const ad = analysisResults.improved_ad;
    const text = `${ad.headline}\n\n${ad.body_copy}\n\n${ad.cta}`;

    navigator.clipboard.writeText(text).then(() => {
        alert('✅ Ad copied to clipboard!');
    });
}

function copyVariant(variantId) {
    const variant = analysisResults?.ad_variants?.find(v => v.id === variantId);
    if (!variant) return;

    navigator.clipboard.writeText(variant.copy).then(() => {
        alert(`✅ Variant ${variantId} copied!`);
    });
}
