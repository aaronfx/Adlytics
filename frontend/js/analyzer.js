// ============================================
// ADLYTICS v4.5 - RESPONSE FORMAT FIX
// Handles both {success, data} and raw response formats
// ============================================

// Global state
let currentContentMode = 'adCopy';
let analysisResults = null;
let currentTab = 'behavior';
let isInitialized = false;

// ============================================
// INITIALIZATION
// ============================================
function init() {
    if (isInitialized) return;
    isInitialized = true;

    console.log('🚀 ADLYTICS v4.5 Initializing...');

    setupContentTabs();
    setupFormHandler();
    setupResultsTabs();
    setupRegionDependency();
    setupCharCounters();

    console.log('✅ ADLYTICS v4.5 Ready');
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// ============================================
// SAFE FORM DATA HELPER
// ============================================
function safeAppend(formData, key, value) {
    if (value !== undefined && value !== null && value !== "") {
        formData.append(key, value);
    }
}

// ============================================
// CONTENT TABS
// ============================================
function setupContentTabs() {
    const tabs = document.querySelectorAll('.content-tab');
    const containers = document.querySelectorAll('.textarea-container');

    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const mode = tab.dataset.mode;
            const targetId = tab.dataset.target;

            if (!mode || !targetId) return;

            currentContentMode = mode;

            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            containers.forEach(c => c.classList.remove('active'));
            const targetContainer = document.getElementById(targetId);
            if (targetContainer) {
                targetContainer.classList.add('active');
            }

            const textareas = targetContainer?.querySelectorAll('textarea');
            textareas?.forEach(ta => {
                ta.style.display = 'block';
                ta.style.width = '100%';
                ta.style.minHeight = '150px';
            });
        });
    });

    const activeTab = document.querySelector('.content-tab.active');
    if (activeTab) {
        currentContentMode = activeTab.dataset.mode || 'adCopy';
    }
}

// ============================================
// FORM HANDLER - FIXED RESPONSE HANDLING
// ============================================
function setupFormHandler() {
    const form = document.getElementById('analyzeForm');
    if (!form) {
        console.error('❌ Form not found');
        return;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('📝 Form submitted');

        const analyzeBtn = document.getElementById('analyzeBtn');
        const loadingState = document.getElementById('loadingState');
        const emptyState = document.getElementById('emptyState');
        const resultsContent = document.getElementById('resultsContent');

        if (analyzeBtn) {
            analyzeBtn.disabled = true;
            analyzeBtn.textContent = 'Analyzing...';
        }
        if (loadingState) loadingState.classList.remove('hidden');
        if (emptyState) emptyState.classList.add('hidden');
        if (resultsContent) resultsContent.classList.add('hidden');

        try {
            const formData = new FormData();

            // Get content based on mode
            let adCopy = '';
            let videoScript = '';

            if (currentContentMode === 'adCopy') {
                adCopy = document.getElementById('adCopy')?.value?.trim() || '';
                safeAppend(formData, 'ad_copy', adCopy);
            } else if (currentContentMode === 'videoScript') {
                videoScript = document.getElementById('videoScript')?.value?.trim() || '';
                safeAppend(formData, 'video_script', videoScript);
            } else if (currentContentMode === 'both') {
                adCopy = document.getElementById('adCopyBoth')?.value?.trim() || '';
                videoScript = document.getElementById('videoScriptBoth')?.value?.trim() || '';
                safeAppend(formData, 'ad_copy', adCopy);
                safeAppend(formData, 'video_script', videoScript);
            }

            console.log('Content mode:', currentContentMode);
            console.log('Ad copy length:', adCopy.length);
            console.log('Video script length:', videoScript.length);

            if (!adCopy && !videoScript) {
                throw new Error('Please enter ad copy or video script');
            }

            // Required fields
            const platform = document.getElementById('platform')?.value;
            const industry = document.getElementById('industry')?.value;
            const country = document.getElementById('country')?.value;
            const age = document.getElementById('age')?.value;

            if (!platform || !industry || !country || !age) {
                throw new Error('Please fill in all required fields (Platform, Industry, Country, Age)');
            }

            // Append all form data safely
            safeAppend(formData, 'platform', platform);
            safeAppend(formData, 'industry', industry);
            safeAppend(formData, 'objective', document.getElementById('objective')?.value);
            safeAppend(formData, 'audience_country', country);
            safeAppend(formData, 'audience_region', document.getElementById('region')?.value);
            safeAppend(formData, 'audience_age', age);
            safeAppend(formData, 'audience_gender', document.getElementById('gender')?.value);
            safeAppend(formData, 'audience_income', document.getElementById('income')?.value);
            safeAppend(formData, 'audience_education', document.getElementById('education')?.value);
            safeAppend(formData, 'audience_occupation', document.getElementById('occupation')?.value);
            safeAppend(formData, 'audience_psychographic', document.getElementById('psychographic')?.value);
            safeAppend(formData, 'audience_pain_point', document.getElementById('pain_point')?.value);
            safeAppend(formData, 'tech_savviness', document.getElementById('tech_savviness')?.value);
            safeAppend(formData, 'purchase_behavior', document.getElementById('purchase_behavior')?.value);

            // Debug: log form data
            console.log('=== Form Data ===');
            for (let [key, value] of formData.entries()) {
                if (value instanceof File) {
                    console.log(`${key}: File (${value.name}, ${value.size} bytes)`);
                } else {
                    console.log(`${key}: ${value.toString().substring(0, 100)}`);
                }
            }

            // Send request
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            console.log('Response status:', response.status);

            // Parse response
            let data;
            try {
                data = await response.json();
            } catch (parseError) {
                console.error('Failed to parse JSON:', parseError);
                throw new Error('Invalid response from server');
            }

            console.log('API RESPONSE:', data);

            // CRITICAL FIX: Handle response format properly
            // Check for explicit failure
            if (data && data.success === false) {
                console.error('Backend error:', data);
                alert(data.error || data.detail || 'Analysis failed');
                return;
            }

            // Support both formats: {success: true, data: {...}} and raw {...}
            let result;
            if (data && data.success === true && data.data) {
                // New format: {success: true, data: {...}}
                result = data.data;
            } else if (data && (data.analysis || data.scores)) {
                // Old format: raw result
                result = data;
            } else {
                console.error('Unexpected response structure:', data);
                throw new Error('Invalid response structure from server');
            }

            // Store and render results
            analysisResults = result;
            renderResults(analysisResults);
            
            if (resultsContent) {
                resultsContent.classList.remove('hidden');
                resultsContent.scrollIntoView({ behavior: 'smooth' });
            }

        } catch (error) {
            console.error('❌ Error:', error);
            alert('Error: ' + error.message);
        } finally {
            if (analyzeBtn) {
                analyzeBtn.disabled = false;
                analyzeBtn.textContent = 'Analyze Ad →';
            }
            if (loadingState) loadingState.classList.add('hidden');
        }
    });
}

// ============================================
// RESULTS TABS
// ============================================
function setupResultsTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    if (tabButtons.length === 0) return;

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            if (!tabId) return;

            currentTab = tabId;

            tabButtons.forEach(b => {
                b.classList.toggle('tab-active', b.dataset.tab === tabId);
                b.classList.toggle('text-gray-400', b.dataset.tab !== tabId);
            });

            tabContents.forEach(content => {
                const isActive = content.id === `tab-${tabId}`;
                content.style.display = isActive ? 'block' : 'none';
                content.classList.toggle('hidden', !isActive);
            });
        });
    });

    if (tabButtons[0]) {
        tabButtons[0].click();
    }
}

// ============================================
// RENDER RESULTS
// ============================================
function renderResults(analysis) {
    console.log('🎨 Rendering results...', analysis);

    if (!analysis) {
        console.error('No analysis data');
        return;
    }

    const scores = analysis.scores || {};
    const overallScore = scores.overall || 0;

    updateText('overallScore', overallScore);
    
    const scoreCircle = document.getElementById('scoreCircle');
    if (scoreCircle) {
        const circumference = 2 * Math.PI * 40;
        const offset = circumference - (overallScore / 100) * circumference;
        scoreCircle.style.strokeDashoffset = offset;
        
        let color = '#ef4444';
        if (overallScore >= 70) color = '#22c55e';
        else if (overallScore >= 50) color = '#f59e0b';
        scoreCircle.style.stroke = color;
    }

    const runDecision = analysis.run_decision || {};
    const verdict = runDecision.should_run || 'REVIEW';
    const verdictEl = document.getElementById('verdictBadge');
    if (verdictEl) {
        verdictEl.textContent = verdict;
        let badgeColor = 'bg-gray-700';
        if (verdict.includes('Yes')) badgeColor = 'bg-green-500/20 text-green-400';
        else if (verdict.includes('No')) badgeColor = 'bg-red-500/20 text-red-400';
        else if (verdict.includes('fixes')) badgeColor = 'bg-yellow-500/20 text-yellow-400';
        verdictEl.className = `px-3 py-1 rounded-full text-sm font-medium ${badgeColor}`;
    }

    const behaviorSummary = analysis.behavior_summary || {};
    updateText('launchReadiness', behaviorSummary.launch_readiness || '0%');
    updateText('failureRisk', behaviorSummary.failure_risk || '0%');
    updateText('primaryReason', behaviorSummary.primary_reason || '');

    renderRunDecision(runDecision);
    renderPerformanceBreakdown(scores);
    renderPhaseBreakdown(analysis.phase_breakdown);
    renderBehaviorSummary(analysis.behavior_summary);
    renderLineByLine(analysis.line_by_line_analysis);
    renderWeaknesses(analysis.critical_weaknesses);
    renderImprovements(analysis.improvements);
    renderImprovedAd(analysis.improved_ad);
    renderVariants(analysis.ad_variants);
    renderWinnerPrediction(analysis.winner_prediction);
    renderPersonas(analysis.persona_reactions);
    renderROI(analysis.roi_analysis);
    renderVideoExecution(analysis.video_execution_analysis);
    renderCompetitorAdvantage(analysis.competitor_advantage);

    const audienceEl = document.getElementById('audienceParsed');
    if (audienceEl && analysis.audience_parsed) {
        audienceEl.textContent = analysis.audience_parsed;
        document.getElementById('audienceSummary')?.classList.remove('hidden');
    }

    console.log('✅ Results rendered');
}

function updateText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function renderRunDecision(runDecision) {
    const container = document.getElementById('runDecision');
    if (!container || !runDecision) return;

    const shouldRun = runDecision.should_run || 'Review';
    const riskLevel = runDecision.risk_level || 'Unknown';
    const reason = runDecision.reason || '';

    let bgColor = 'bg-gray-700';
    let textColor = 'text-white';
    
    if (shouldRun.includes('Yes')) {
        bgColor = 'bg-green-500/20';
        textColor = 'text-green-400';
    } else if (shouldRun.includes('No')) {
        bgColor = 'bg-red-500/20';
        textColor = 'text-red-400';
    } else {
        bgColor = 'bg-yellow-500/20';
        textColor = 'text-yellow-400';
    }

    container.innerHTML = `
        <div class="flex items-center justify-between">
            <div>
                <h3 class="text-lg font-semibold ${textColor}">Run Decision: ${shouldRun}</h3>
                <p class="text-sm text-gray-400 mt-1">${reason}</p>
            </div>
            <div class="text-right">
                <span class="text-xs text-gray-500">Risk Level</span>
                <p class="font-semibold ${textColor}">${riskLevel}</p>
            </div>
        </div>
    `;
}

function renderPerformanceBreakdown(scores) {
    const container = document.getElementById('scoresGrid');
    if (!container) return;

    const metrics = [
        ['hook_strength', 'Hook Strength', 'How well the opening captures attention'],
        ['clarity', 'Clarity', 'How clear the message is'],
        ['trust_building', 'Trust Building', 'Credibility and proof elements'],
        ['cta_power', 'CTA Power', 'Call-to-action effectiveness'],
        ['audience_alignment', 'Audience Alignment', 'Match with target demographic']
    ];

    container.innerHTML = metrics.map(([key, label, description]) => {
        const score = scores[key] || 0;
        let color = '#ef4444';
        if (score >= 70) color = '#22c55e';
        else if (score >= 50) color = '#f59e0b';
        
        return `
            <div class="flex items-center justify-between mb-2">
                <div class="flex-1">
                    <div class="flex items-center justify-between mb-1">
                        <span class="text-sm font-medium">${label}</span>
                        <span class="text-sm font-bold">${score}/100</span>
                    </div>
                    <div class="metric-bar">
                        <div class="metric-fill" style="width: ${score}%; background: ${color};"></div>
                    </div>
                    <p class="text-xs text-gray-500 mt-1">${description}</p>
                </div>
            </div>
        `;
    }).join('');
}

function renderPhaseBreakdown(phases) {
    const container = document.getElementById('phaseBreakdown');
    if (!container) return;

    if (!phases || typeof phases !== 'object') {
        container.innerHTML = '<p class="text-gray-500">No phase breakdown available</p>';
        return;
    }

    const phaseOrder = [
        ['micro_stop_0_1s', '0-1s: Micro-Stop'],
        ['scroll_stop_1_2s', '1-2s: Scroll-Stop'],
        ['attention_2_5s', '2-5s: Attention'],
        ['trust_evaluation', 'Trust Evaluation'],
        ['click_and_post_click', 'Click & Post-Click']
    ];

    container.innerHTML = phaseOrder.map(([key, label]) => {
        const text = phases[key] || 'N/A';
        return `<div class="p-3 bg-gray-900/50 rounded-lg"><strong>${label}:</strong> ${text}</div>`;
    }).join('');
}

function renderBehaviorSummary(summary) {
    const container = document.getElementById('platformSpecific');
    if (!container) return;

    if (!summary) {
        container.innerHTML = '<p class="text-gray-500">No behavior summary available</p>';
        return;
    }

    container.innerHTML = `
        <h4 class="font-semibold mb-3 text-purple-400">📊 Behavior Summary</h4>
        <div class="space-y-2 text-sm">
            <div><strong>Verdict:</strong> ${summary.verdict || 'N/A'}</div>
            <div><strong>Launch Readiness:</strong> ${summary.launch_readiness || 'N/A'}</div>
            <div><strong>Failure Risk:</strong> ${summary.failure_risk || 'N/A'}</div>
            <div><strong>Primary Reason:</strong> ${summary.primary_reason || 'N/A'}</div>
        </div>
    `;
}

function renderLineByLine(lines) {
    const container = document.getElementById('lineByLineAnalysis');
    if (!container) return;

    if (!lines || !Array.isArray(lines) || lines.length === 0) {
        container.innerHTML = '<p class="text-gray-500">No line-by-line analysis available</p>';
        return;
    }

    container.innerHTML = lines.map((l, i) => {
        const score = l.score || 0;
        let color = 'text-red-400';
        if (score >= 70) color = 'text-green-400';
        else if (score >= 50) color = 'text-yellow-400';
        
        return `
            <div class="line-analysis-item p-3 bg-gray-900/30 rounded-lg border-l-4 ${score >= 70 ? 'border-green-500' : score >= 50 ? 'border-yellow-500' : 'border-red-500'}">
                <div class="flex items-center justify-between mb-1">
                    <span class="text-xs text-gray-500">Line ${i + 1}</span>
                    <span class="text-sm font-bold ${color}">${score}/100</span>
                </div>
                <p class="text-sm text-white">"${l.text || 'N/A'}"</p>
                <p class="text-xs text-gray-400 mt-1">${l.analysis || ''}</p>
            </div>
        `;
    }).join('');
}

function renderWeaknesses(weaknesses) {
    const container = document.getElementById('criticalWeaknesses');
    if (!container) return;

    if (!weaknesses || !Array.isArray(weaknesses) || weaknesses.length === 0) {
        container.innerHTML = '<p class="text-green-400">✅ No critical weaknesses found</p>';
        return;
    }

    container.innerHTML = weaknesses.map((w, i) => `
        <div class="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
            <div class="flex items-center justify-between mb-2">
                <span class="text-red-400 font-semibold">Priority Issue</span>
                <span class="text-xs text-gray-500">Issue #${i + 1}</span>
            </div>
            <h5 class="font-medium mb-1">${w.issue || w.title || 'Unknown Issue'}</h5>
            <p class="text-sm text-gray-400 mb-2">${w.impact || w.behavior_impact || ''}</p>
            <div class="text-sm text-green-400">
                <strong>Fix:</strong> ${w.fix || w.precise_fix || 'Review and revise'}
            </div>
        </div>
    `).join('');
}

function renderImprovements(improvements) {
    const container = document.getElementById('improvements');
    if (!container) return;

    if (!improvements || !Array.isArray(improvements) || improvements.length === 0) {
        container.innerHTML = '<p class="text-gray-500">No specific improvements suggested</p>';
        return;
    }

    container.innerHTML = `
        <h4 class="font-semibold mb-3 text-yellow-400">💡 Suggested Improvements</h4>
        <ul class="space-y-2">
            ${improvements.map((imp, i) => `
                <li class="flex items-start">
                    <span class="text-purple-400 mr-2">${i + 1}.</span>
                    <span class="text-sm">${typeof imp === 'string' ? imp : imp.description || JSON.stringify(imp)}</span>
                </li>
            `).join('')}
        </ul>
    `;
}

function renderImprovedAd(ad) {
    const container = document.getElementById('improvedContent');
    if (!container) return;

    if (!ad) {
        container.innerHTML = '<p class="text-gray-500">No improved ad generated</p>';
        return;
    }

    container.innerHTML = `
        <div class="space-y-3">
            <div class="p-3 bg-gray-800 rounded-lg">
                <span class="text-xs text-gray-500 uppercase">Headline</span>
                <p class="text-lg font-semibold text-white mt-1">${ad.headline || 'N/A'}</p>
            </div>
            <div class="p-3 bg-gray-800 rounded-lg">
                <span class="text-xs text-gray-500 uppercase">Body Copy</span>
                <p class="text-sm text-gray-300 mt-1 whitespace-pre-wrap">${ad.body_copy || 'N/A'}</p>
            </div>
            <div class="p-3 bg-gray-800 rounded-lg border border-purple-500/30">
                <span class="text-xs text-gray-500 uppercase">Call to Action</span>
                <p class="text-md font-semibold text-purple-400 mt-1">${ad.cta || 'N/A'}</p>
            </div>
            ${ad.video_script_version ? `
                <div class="p-3 bg-gray-800 rounded-lg border border-blue-500/30">
                    <span class="text-xs text-gray-500 uppercase">Video Script Version</span>
                    <p class="text-sm text-gray-300 mt-1 whitespace-pre-wrap">${ad.video_script_version}</p>
                </div>
            ` : ''}
            <div class="flex items-center justify-between pt-2">
                <span class="text-sm text-gray-400">Predicted Score: <strong class="text-white">${ad.predicted_score || 0}/100</strong></span>
                <span class="text-sm text-gray-400">ROI: <strong class="text-green-400">${ad.roi_potential || 'N/A'}</strong></span>
            </div>
            <button onclick="copyImprovedAd()" class="w-full py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium transition">
                📋 Copy Improved Ad
            </button>
        </div>
    `;
}

function renderVariants(variants) {
    const container = document.getElementById('adVariants');
    if (!container) return;

    if (!variants || !Array.isArray(variants) || variants.length === 0) {
        container.innerHTML = '<p class="text-gray-500">No variants generated</p>';
        return;
    }

    container.innerHTML = variants.map((v, i) => `
        <div class="variant-card p-4 bg-gray-900/50 rounded-xl border ${i === 0 ? 'border-purple-500/50 bg-purple-500/10' : 'border-white/5'}">
            <div class="flex items-center justify-between mb-2">
                <div class="flex items-center">
                    <span class="text-lg font-bold ${i === 0 ? 'text-purple-400' : 'text-gray-400'} mr-2">#${v.id || i + 1}</span>
                    <span class="text-sm font-medium">${v.angle || 'Variant'}</span>
                    ${i === 0 ? '<span class="ml-2 px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs rounded">🏆 Best</span>' : ''}
                </div>
                <span class="text-xl font-bold ${v.predicted_score >= 70 ? 'text-green-400' : v.predicted_score >= 50 ? 'text-yellow-400' : 'text-red-400'}">${v.predicted_score || 0}/100</span>
            </div>
            <p class="text-sm text-gray-400 mb-2">${v.reason || ''}</p>
            <div class="p-3 bg-gray-800 rounded-lg text-sm text-gray-300 whitespace-pre-wrap">${v.copy || v.hook || 'N/A'}</div>
            <div class="mt-2 text-xs text-gray-500">ROI Potential: ${v.roi_potential || 'N/A'}</div>
        </div>
    `).join('');
}

function renderWinnerPrediction(prediction) {
    const container = document.getElementById('winnerPrediction');
    if (!container) return;

    if (!prediction) {
        container.innerHTML = '<p class="text-gray-500">No winner prediction available</p>';
        return;
    }

    const confidence = prediction.confidence || 'Unknown';
    let color = 'text-gray-400';
    if (confidence === 'high') color = 'text-green-400';
    else if (confidence === 'medium') color = 'text-yellow-400';
    else if (confidence === 'low') color = 'text-red-400';

    container.innerHTML = `
        <h3 class="text-lg font-semibold mb-4">🏆 Winner Prediction</h3>
        <div class="flex items-center justify-between mb-3">
            <span class="text-gray-400">Confidence</span>
            <span class="font-bold ${color}">${confidence}</span>
        </div>
        <p class="text-sm text-gray-300 mb-3">${prediction.reason || 'N/A'}</p>
        <div class="flex items-center justify-between text-sm">
            <span class="text-gray-500">Best Variant: #${prediction.best_variant_id || 'N/A'}</span>
            <span class="text-purple-400 font-semibold">${prediction.expected_lift || 'N/A'}</span>
        </div>
    `;
}

function renderPersonas(personas) {
    const container = document.getElementById('personaReactions');
    if (!container) return;

    if (!personas || !Array.isArray(personas) || personas.length === 0) {
        container.innerHTML = '<p class="text-gray-500">No persona reactions available</p>';
        return;
    }

    container.innerHTML = personas.map(p => `
        <div class="p-4 bg-gray-900/50 rounded-xl border border-white/5">
            <div class="flex items-center justify-between mb-2">
                <span class="font-semibold text-purple-400">${p.persona || p.name || 'Unknown'}</span>
                <span class="text-xs text-gray-500">${p.reaction || 'Neutral'}</span>
            </div>
            <p class="text-sm text-gray-300 italic">"${p.exact_quote || p.thought || p.quote || 'No reaction'}"</p>
        </div>
    `).join('');
}

function renderROI(roi) {
    const container = document.getElementById('roiAnalysis');
    if (!container) return;

    if (!roi) {
        container.innerHTML = '<p class="text-gray-500">No ROI analysis available</p>';
        return;
    }

    container.innerHTML = `
        <div class="space-y-4">
            <div class="grid grid-cols-3 gap-4">
                <div class="p-3 bg-gray-900/50 rounded-lg text-center">
                    <div class="text-xs text-gray-500 mb-1">ROI Potential</div>
                    <div class="font-bold text-green-400">${roi.roi_potential || 'N/A'}</div>
                </div>
                <div class="p-3 bg-gray-900/50 rounded-lg text-center">
                    <div class="text-xs text-gray-500 mb-1">Break-even</div>
                    <div class="font-bold text-blue-400">${roi.break_even_probability || 'N/A'}</div>
                </div>
                <div class="p-3 bg-gray-900/50 rounded-lg text-center">
                    <div class="text-xs text-gray-500 mb-1">Risk</div>
                    <div class="font-bold ${(roi.risk_classification || '').includes('Low') ? 'text-green-400' : (roi.risk_classification || '').includes('High') ? 'text-red-400' : 'text-yellow-400'}">${roi.risk_classification || 'N/A'}</div>
                </div>
            </div>
            ${roi.key_metrics ? `
                <div class="p-3 bg-gray-900/30 rounded-lg">
                    <h5 class="text-sm font-semibold mb-2">Key Metrics</h5>
                    <div class="grid grid-cols-3 gap-2 text-xs">
                        <div>CTR: ${roi.key_metrics.expected_ctr_range || 'N/A'}</div>
                        <div>CPC: ${roi.key_metrics.realistic_cpc_range || 'N/A'}</div>
                        <div>Conv: ${roi.key_metrics.conversion_rate_range || 'N/A'}</div>
                    </div>
                </div>
            ` : ''}
            ${roi.roi_scenarios ? `
                <div class="p-3 bg-gray-900/30 rounded-lg">
                    <h5 class="text-sm font-semibold mb-2">ROI Scenarios</h5>
                    <div class="space-y-1 text-sm">
                        <div class="flex justify-between"><span class="text-gray-500">Worst:</span> <span class="text-red-400">${roi.roi_scenarios.worst_case || 'N/A'}</span></div>
                        <div class="flex justify-between"><span class="text-gray-500">Expected:</span> <span class="text-yellow-400">${roi.roi_scenarios.expected_case || 'N/A'}</span></div>
                        <div class="flex justify-between"><span class="text-gray-500">Best:</span> <span class="text-green-400">${roi.roi_scenarios.best_case || 'N/A'}</span></div>
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

function renderVideoExecution(video) {
    const container = document.getElementById('videoAnalysis');
    if (!container) return;

    if (!video) {
        container.innerHTML = '<p class="text-gray-500">No video execution analysis available</p>';
        return;
    }

    container.innerHTML = `
        <div class="space-y-3">
            <div class="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                <span class="text-gray-400">Hook Delivery</span>
                <span class="font-semibold ${(video.hook_delivery_strength || '').includes('Strong') ? 'text-green-400' : 'text-yellow-400'}">${video.hook_delivery_strength || 'N/A'}</span>
            </div>
            <div class="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                <span class="text-gray-400">Speech Flow</span>
                <span class="font-semibold ${(video.speech_flow_quality || '').includes('Natural') ? 'text-green-400' : 'text-yellow-400'}">${video.speech_flow_quality || 'N/A'}</span>
            </div>
            <div class="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                <span class="text-gray-400">Visual Dependency</span>
                <span class="font-semibold">${video.visual_dependency || 'N/A'}</span>
            </div>
            <div class="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                <span class="text-gray-400">Delivery Risk</span>
                <span class="font-semibold ${(video.delivery_risk || '').includes('Low') ? 'text-green-400' : 'text-red-400'}">${video.delivery_risk || 'N/A'}</span>
            </div>
            <div class="p-3 bg-gray-900/30 rounded-lg">
                <span class="text-gray-500 text-sm">Recommended Format:</span>
                <span class="ml-2 px-2 py-1 bg-purple-500/20 text-purple-400 rounded text-sm">${video.recommended_format || 'N/A'}</span>
            </div>
            ${video.biggest_execution_gap && video.biggest_execution_gap !== 'None identified' ? `
                <div class="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                    <span class="text-yellow-400 text-sm font-semibold">Execution Gap:</span>
                    <p class="text-sm text-gray-400 mt-1">${video.biggest_execution_gap}</p>
                </div>
            ` : ''}
        </div>
    `;
}

function renderCompetitorAdvantage(competitor) {
    const container = document.getElementById('competitorAdvantage');
    if (!container) return;

    if (!competitor) {
        container.innerHTML = '<p class="text-gray-500">No competitor analysis available</p>';
        return;
    }

    container.innerHTML = `
        <div class="space-y-4">
            <div class="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                <h5 class="text-red-400 font-semibold mb-2">⚠️ Why Users Might Choose Competitor</h5>
                <p class="text-sm text-gray-300">${competitor.why_user_might_choose_competitor || 'N/A'}</p>
            </div>
            <div class="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                <h5 class="text-yellow-400 font-semibold mb-2">📊 What Competitor Does Better</h5>
                <p class="text-sm text-gray-300">${competitor.what_competitor_is_doing_better || 'N/A'}</p>
            </div>
            <div class="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                <h5 class="text-green-400 font-semibold mb-2">🎯 How to Outperform</h5>
                <p class="text-sm text-gray-300">${competitor.how_to_outperform || 'N/A'}</p>
            </div>
        </div>
    `;
}

// ============================================
// UTILITIES
// ============================================
function copyImprovedAd() {
    if (!analysisResults?.improved_ad) return;
    const ad = analysisResults.improved_ad;
    const text = `${ad.headline || ''}\n\n${ad.body_copy || ''}\n\n${ad.cta || ''}`;
    navigator.clipboard.writeText(text).then(() => alert('✅ Copied to clipboard!'));
}

function setupRegionDependency() {
    const countrySelect = document.getElementById('country');
    const regionSelect = document.getElementById('region');

    if (!countrySelect || !regionSelect) return;

    const regions = {
        nigeria: ['Lagos', 'Abuja', 'Kano', 'Ibadan', 'Port Harcourt'],
        us: ['California', 'Texas', 'New York', 'Florida', 'Illinois'],
        uk: ['London', 'Manchester', 'Birmingham', 'Glasgow', 'Liverpool'],
        canada: ['Ontario', 'Quebec', 'British Columbia', 'Alberta'],
        australia: ['New South Wales', 'Victoria', 'Queensland'],
        ghana: ['Accra', 'Kumasi', 'Tamale'],
        kenya: ['Nairobi', 'Mombasa', 'Kisumu'],
        south_africa: ['Gauteng', 'Western Cape', 'KwaZulu-Natal'],
        india: ['Maharashtra', 'Karnataka', 'Delhi', 'Tamil Nadu'],
        germany: ['Bavaria', 'North Rhine-Westphalia', 'Baden-Württemberg']
    };

    countrySelect.addEventListener('change', () => {
        const country = countrySelect.value;
        const countryRegions = regions[country] || [];

        regionSelect.innerHTML = '<option value="">Select Region</option>';
        countryRegions.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.toLowerCase().replace(/\s+/g, '-');
            opt.textContent = r;
            regionSelect.appendChild(opt);
        });

        regionSelect.disabled = countryRegions.length === 0;
    });
}

function setupCharCounters() {
    const adCopy = document.getElementById('adCopy');
    const adCopyCount = document.getElementById('adCopyCount');
    const videoScript = document.getElementById('videoScript');
    const videoScriptCount = document.getElementById('videoScriptCount');

    if (adCopy && adCopyCount) {
        adCopy.addEventListener('input', () => {
            adCopyCount.textContent = `${adCopy.value.length} chars`;
        });
    }

    if (videoScript && videoScriptCount) {
        videoScript.addEventListener('input', () => {
            const words = videoScript.value.trim().split(/\s+/).filter(w => w.length > 0).length;
            const readTime = Math.ceil(words / 3);
            videoScriptCount.textContent = `${words} words (~${readTime}s)`;
        });
    }
}
