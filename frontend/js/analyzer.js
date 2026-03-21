/**
 * ADLYTICS - Enhanced Analyzer JavaScript v4.0
 * Handles detailed audience targeting, video script support, and v4.0 features:
 * - Line-by-line analysis
 * - Ad variant generation and ranking
 * - Winner prediction
 * - ROI comparison
 * - Run decision engine
 * - IMPROVED AD RE-ANALYSIS (PATCHED + ROBUST MERGE - 2025)
 */

const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api' 
    : '/api';

// Global audience config
let audienceConfig = null;
let currentContentMode = 'adCopy';

// DOM Elements
const form = document.getElementById('analyzeForm');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingState = document.getElementById('loadingState');
const emptyState = document.getElementById('emptyState');
const resultsContent = document.getElementById('resultsContent');
const filePreview = document.getElementById('filePreview');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadAudienceConfig();
    await loadPlatforms();
    await loadIndustries();
    setupEventListeners();
    setupContentTabs();
    setupTextareaCounters();
});

// Setup content type tabs
function setupContentTabs() {
    const tabs = document.querySelectorAll('.content-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const target = tab.dataset.target;
            document.querySelectorAll('.textarea-container').forEach(container => {
                container.classList.remove('active');
            });
            document.getElementById(target).classList.add('active');
            currentContentMode = target.replace('Container', '');
        });
    });
}

// Setup textarea character/word counters
function setupTextareaCounters() {
    const adCopy = document.getElementById('adCopy');
    const videoScript = document.getElementById('videoScript');
    if (adCopy) {
        adCopy.addEventListener('input', (e) => {
            document.getElementById('adCopyCount').textContent = `${e.target.value.length} chars`;
        });
    }
    if (videoScript) {
        videoScript.addEventListener('input', (e) => {
            const words = e.target.value.trim().split(/\s+/).filter(w => w.length > 0).length;
            const readTime = Math.ceil(words / 3);
            document.getElementById('videoScriptCount').textContent = `${words} words (~${readTime}s read)`;
        });
    }
}

// ────────────────────────────────────────────────
// Load & Populate Audience / Platform / Industry
// ────────────────────────────────────────────────

async function loadAudienceConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/audience-config`);
        if (!response.ok) throw new Error('Failed to load audience config');
        audienceConfig = await response.json();
        populateAudienceFields();
    } catch (error) {
        console.error('Error loading audience config:', error);
        populateBasicAudienceOptions();
    }
}

function populateAudienceFields() {
    if (!audienceConfig) return;
    // ... (your existing population logic remains unchanged)
    // countries, age_brackets, income_levels, education_levels, occupations, psychographics, pain_points
}

function populateBasicAudienceOptions() {
    // ... (your fallback logic remains unchanged)
}

async function loadPlatforms() {
    // ... (unchanged)
}

async function loadIndustries() {
    // ... (unchanged)
}

// ────────────────────────────────────────────────
// Event Listeners & File Handling
// ────────────────────────────────────────────────

function setupEventListeners() {
    // ... (country → region, age traits, occupation pain points, file uploads)
    // your existing code remains here

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await handleSubmit(selectedImage, selectedVideo);
        });
    }
}

function updateFilePreview(file, type) {
    const icon = type === 'image' ? '📷' : '🎥';
    filePreview.textContent = `${icon} ${file.name} (${(file.size/1024/1024).toFixed(2)}MB)`;
    filePreview.classList.remove('hidden');
}

function getContentValues() {
    let adCopy = '';
    let videoScript = '';
    if (currentContentMode === 'adCopy' || currentContentMode === 'both') {
        const adCopyEl = document.getElementById('adCopy');
        const adCopyBothEl = document.getElementById('adCopyBoth');
        adCopy = adCopyEl?.value?.trim() || adCopyBothEl?.value?.trim() || '';
    }
    if (currentContentMode === 'videoScript' || currentContentMode === 'both') {
        const videoScriptEl = document.getElementById('videoScript');
        const videoScriptBothEl = document.getElementById('videoScriptBoth');
        videoScript = videoScriptEl?.value?.trim() || videoScriptBothEl?.value?.trim() || '';
    }
    return { adCopy, videoScript };
}

async function handleSubmit(selectedImage, selectedVideo) {
    // ... (your existing submit logic remains unchanged)
    // formData construction, fetch /analyze, renderResults(data)
}

// ────────────────────────────────────────────────
// IMPROVED ANALYSIS RENDER (unchanged)
// ────────────────────────────────────────────────

function renderImprovedAnalysis(data) {
    // ... (your existing renderImprovedAnalysis function remains unchanged)
}

// ────────────────────────────────────────────────
// MAIN RESULTS RENDER + ROBUST MERGE LOGIC
// ────────────────────────────────────────────────

function renderResults(data) {
    const analysis = data.analysis;
    if (!analysis) {
        console.error('No analysis data received');
        return;
    }

    const improved = analysis.improved_ad_analysis || null;

    // ── ROBUST MERGE ────────────────────────────────────────────────
    const primary = improved
        ? {
            ...analysis,
            ...improved,

            // Critical scalar/nested objects ── prefer improved when present
            scores: improved?.scores
                ? { ...analysis.scores, ...improved.scores }
                : (analysis.scores || {}),

            run_decision: improved.run_decision || analysis.run_decision,
            behavior_summary: improved.behavior_summary || analysis.behavior_summary,

            roi_analysis: improved?.roi_analysis
                ? {
                    ...analysis.roi_analysis,
                    ...improved.roi_analysis,
                    key_metrics: improved.roi_analysis.key_metrics
                        ? { ...(analysis.roi_analysis?.key_metrics || {}), ...improved.roi_analysis.key_metrics }
                        : (analysis.roi_analysis?.key_metrics || {}),
                    roi_scenarios: improved.roi_analysis.roi_scenarios
                        ? { ...(analysis.roi_analysis?.roi_scenarios || {}), ...improved.roi_analysis.roi_scenarios }
                        : (analysis.roi_analysis?.roi_scenarios || {})
                  }
                : (analysis.roi_analysis || {}),

            // Array / content fields ── only take improved if clearly has content
            variations: (improved?.variations && Object.keys(improved.variations).length > 0)
                ? improved.variations
                : (analysis.variations || {}),

            line_by_line_analysis: improved?.line_by_line_analysis?.length > 0
                ? improved.line_by_line_analysis
                : (analysis.line_by_line_analysis || []),

            critical_weaknesses: improved?.critical_weaknesses?.length > 0
                ? improved.critical_weaknesses
                : (analysis.critical_weaknesses || []),

            improvements: improved?.improvements?.length > 0
                ? improved.improvements
                : (analysis.improvements || []),

            ad_variants: improved?.ad_variants?.length > 0
                ? improved.ad_variants
                : (analysis.ad_variants || []),

            persona_reactions: improved?.persona_reactions?.length > 0
                ? improved.persona_reactions
                : (analysis.persona_reactions || []),

            // Keep original fallback for less critical / complex fields
            phase_breakdown: improved?.phase_breakdown || analysis.phase_breakdown,
            platform_specific: improved?.platform_specific || analysis.platform_specific,
            video_execution_analysis: improved?.video_execution_analysis || analysis.video_execution_analysis,
            winner_prediction: improved?.winner_prediction || analysis.winner_prediction,
            roi_comparison: improved?.roi_comparison || analysis.roi_comparison,
            competitor_advantage: improved?.competitor_advantage || analysis.competitor_advantage
          }
        : analysis;

    const isImprovedPrimary = !!improved;

    console.log("PRIMARY SCORE:", primary?.scores?.overall);
    console.log("ORIGINAL SCORE:", analysis?.scores?.overall); 
    console.log("IMPROVED EXISTS:", !!improved);

    resultsContent.classList.remove('hidden');

    // ── The rest of your renderResults function remains mostly unchanged ──
    // Just make sure to use `primary.xxx` everywhere instead of `analysis.xxx`

    // Run Decision
    const runDecisionDiv = document.getElementById('runDecision');
    if (runDecisionDiv) {
        const decision = primary.run_decision || {};
        const shouldRun = decision.should_run || 'Only after fixes';
        const decisionColor = shouldRun === 'Yes' ? 'green' : shouldRun === 'No' ? 'red' : 'yellow';

        runDecisionDiv.innerHTML = `
            <div class="p-4 bg-${decisionColor}-500/10 border border-${decisionColor}-500/20 rounded-xl">
                <div class="flex items-center space-x-3 mb-3">
                    <span class="text-2xl">${shouldRun === 'Yes' ? '✅' : shouldRun === 'No' ? '🚫' : '⚠️'}</span>
                    <div>
                        <h4 class="font-semibold text-${decisionColor}-400">${isImprovedPrimary ? 'AI-Optimized Ad' : 'Original Ad'} - Run Decision</h4>
                        <p class="text-xs text-gray-400">Risk Level: ${decision.risk_level || 'Unknown'}</p>
                    </div>
                </div>
                <div class="p-3 bg-gray-900/50 rounded-lg mb-3">
                    <span class="text-xs text-gray-500">VERDICT:</span>
                    <p class="text-lg font-bold text-${decisionColor}-400 mt-1">${shouldRun}</p>
                </div>
                <p class="text-sm text-gray-300">${decision.reason || 'No decision reason provided'}</p>
                ${isImprovedPrimary ? `
                <div class="mt-3 p-2 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                    <span class="text-xs text-blue-400">Baseline was: ${analysis.run_decision?.should_run || 'Unknown'}</span>
                </div>
                ` : ''}
            </div>
        `;
    }

    // Overall Score
    const overall = primary.scores?.overall || 0;
    const scoreEl = document.getElementById('overallScore');
    if (scoreEl) scoreEl.textContent = overall;
    const circle = document.getElementById('scoreCircle');
    if (circle) {
        const circumference = 251.2;
        const offset = circumference - (overall / 100) * circumference;
        setTimeout(() => {
            circle.style.strokeDashoffset = offset;
            if (overall >= 70) circle.style.stroke = '#10b981';
            else if (overall >= 50) circle.style.stroke = '#f59e0b';
            else circle.style.stroke = '#ef4444';
        }, 100);
    }

    // ... (continue with the rest of your rendering logic using primary. instead of analysis.)
    // Audience Summary, Verdict Badge, Detailed Scores, Phase Breakdown, Platform Specific,
    // Line-by-Line, Critical Weaknesses, Improvements, Improved Content, Variations,
    // Persona Reactions, ROI Analysis, Video Analysis, Winner Prediction, Ad Variants,
    // ROI Comparison, Competitor Advantage — all should now use primary.xxx

    // Example for scores grid (update similarly for others):
    const scoresGrid = document.getElementById('scoresGrid');
    if (scoresGrid) {
        const scores = primary.scores || {};
        const scoreItems = [
            { key: 'hook_strength', label: 'Hook Strength' },
            { key: 'clarity', label: 'Clarity' },
            // ... rest of items
        ];
        scoresGrid.innerHTML = scoreItems.map(item => {
            const value = scores[item.key] || 0;
            const color = value >= 70 ? 'bg-green-500' : value >= 50 ? 'bg-yellow-500' : 'bg-red-500';
            return `
                <div class="flex items-center space-x-3">
                    <span class="text-sm text-gray-400 w-32">${item.label}</span>
                    <div class="flex-1 bg-gray-700 rounded-full h-2">
                        <div class="${color} h-2 rounded-full transition-all duration-500" style="width: ${value}%"></div>
                    </div>
                    <span class="text-sm font-medium w-8">${value}</span>
                </div>
            `;
        }).join('');
    }

    // ... (rest of your render code)
}

// Tab Navigation (unchanged)
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => {
            b.classList.remove('tab-active');
            b.classList.add('text-gray-400');
        });
        document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
        btn.classList.add('tab-active');
        btn.classList.remove('text-gray-400');
        const tabId = `tab-${btn.dataset.tab}`;
        const tabContent = document.getElementById(tabId);
        if (tabContent) tabContent.classList.remove('hidden');
    });
});

console.log('ADLYTICS v4.0 Enhanced Analyzer loaded (ROBUST MERGE - nested fields protected)');
