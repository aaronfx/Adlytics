/**
 * ADLYTICS - Enhanced Analyzer JavaScript v4.0
 * Handles detailed audience targeting, video script support, and v4.0 features:
 * - Line-by-line analysis
 * - Ad variant generation and ranking
 * - Winner prediction
 * - ROI comparison
 * - Run decision engine
 * - IMPROVED AD RE-ANALYSIS (PATCHED)
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

// Load audience configuration from backend
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

// Populate all audience dropdowns
function populateAudienceFields() {
    if (!audienceConfig) return;
    const countrySelect = document.getElementById('audienceCountry');
    if (countrySelect && audienceConfig.countries) {
        audienceConfig.countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.code;
            option.textContent = `${country.name} (${country.currency})`;
            option.dataset.regions = JSON.stringify(country.regions || []);
            option.dataset.currency = country.currency;
            countrySelect.appendChild(option);
        });
    }
    const ageSelect = document.getElementById('audienceAge');
    if (ageSelect && audienceConfig.age_brackets) {
        audienceConfig.age_brackets.forEach(age => {
            const option = document.createElement('option');
            option.value = age.value;
            option.textContent = age.label;
            option.dataset.traits = age.traits;
            ageSelect.appendChild(option);
        });
    }
    const incomeSelect = document.getElementById('audienceIncome');
    if (incomeSelect && audienceConfig.income_levels) {
        audienceConfig.income_levels.forEach(income => {
            const option = document.createElement('option');
            option.value = income.value;
            option.textContent = income.label;
            option.dataset.description = income.description;
            incomeSelect.appendChild(option);
        });
    }
    const eduSelect = document.getElementById('audienceEducation');
    if (eduSelect && audienceConfig.education_levels) {
        audienceConfig.education_levels.forEach(edu => {
            const option = document.createElement('option');
            option.value = edu.value;
            option.textContent = edu.label;
            eduSelect.appendChild(option);
        });
    }
    const occSelect = document.getElementById('audienceOccupation');
    if (occSelect && audienceConfig.occupations) {
        audienceConfig.occupations.forEach(occ => {
            const option = document.createElement('option');
            option.value = occ.value;
            option.textContent = occ.label;
            option.dataset.painPoints = occ.pain_points;
            occSelect.appendChild(option);
        });
    }
    const psychSelect = document.getElementById('audiencePsychographic');
    if (psychSelect && audienceConfig.psychographics) {
        audienceConfig.psychographics.forEach(psych => {
            const option = document.createElement('option');
            option.value = psych.value;
            option.textContent = psych.label;
            option.dataset.traits = psych.traits;
            psychSelect.appendChild(option);
        });
    }
    const painSelect = document.getElementById('audiencePainPoint');
    if (painSelect && audienceConfig.pain_points) {
        audienceConfig.pain_points.forEach(pain => {
            const option = document.createElement('option');
            option.value = pain.value;
            option.textContent = pain.label;
            option.dataset.description = pain.description;
            painSelect.appendChild(option);
        });
    }
}

// Fallback if API fails
function populateBasicAudienceOptions() {
    const countries = [
        {code: 'nigeria', name: 'Nigeria', currency: '₦', regions: ['Lagos', 'Abuja', 'Port Harcourt']},
        {code: 'us', name: 'United States', currency: '$', regions: ['New York', 'California', 'Texas']},
        {code: 'uk', name: 'United Kingdom', currency: '£', regions: ['London', 'Manchester']}
    ];
    const countrySelect = document.getElementById('audienceCountry');
    if (countrySelect) {
        countries.forEach(c => {
            const option = document.createElement('option');
            option.value = c.code;
            option.textContent = `${c.name} (${c.currency})`;
            option.dataset.regions = JSON.stringify(c.regions);
            countrySelect.appendChild(option);
        });
    }
}

// Load platforms
async function loadPlatforms() {
    try {
        const response = await fetch(`${API_BASE_URL}/platforms`);
        if (!response.ok) return;
        const data = await response.json();
        const select = document.getElementById('platform');
        if (!select) return;
        data.platforms.forEach(p => {
            const option = document.createElement('option');
            option.value = p.id;
            option.textContent = p.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading platforms:', error);
    }
}

// Load industries
async function loadIndustries() {
    try {
        const response = await fetch(`${API_BASE_URL}/industries`);
        if (!response.ok) return;
        const data = await response.json();
        const select = document.getElementById('industry');
        if (!select) return;
        data.industries.forEach(i => {
            const option = document.createElement('option');
            option.value = i.id;
            option.textContent = i.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading industries:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    const countrySelect = document.getElementById('audienceCountry');
    const regionSelect = document.getElementById('audienceRegion');
    if (countrySelect && regionSelect) {
        countrySelect.addEventListener('change', (e) => {
            const selected = e.target.selectedOptions[0];
            if (!selected) return;
            const regions = JSON.parse(selected.dataset.regions || '[]');
            regionSelect.innerHTML = '<option value="">Select Region</option>';
            if (regions.length > 0) {
                regionSelect.disabled = false;
                regions.forEach(region => {
                    const option = document.createElement('option');
                    option.value = region.toLowerCase().replace(/\s+/g, '_');
                    option.textContent = region;
                    regionSelect.appendChild(option);
                });
            } else {
                regionSelect.disabled = true;
            }
        });
    }
    const ageSelect = document.getElementById('audienceAge');
    const ageTraits = document.getElementById('ageTraits');
    if (ageSelect && ageTraits) {
        ageSelect.addEventListener('change', (e) => {
            const traits = e.target.selectedOptions[0]?.dataset.traits;
            if (traits) {
                ageTraits.textContent = traits;
                ageTraits.classList.remove('hidden');
            } else {
                ageTraits.classList.add('hidden');
            }
        });
    }
    const occSelect = document.getElementById('audienceOccupation');
    const occPainPoints = document.getElementById('occupationPainPoints');
    if (occSelect && occPainPoints) {
        occSelect.addEventListener('change', (e) => {
            const painPoints = e.target.selectedOptions[0]?.dataset.painPoints;
            if (painPoints) {
                occPainPoints.textContent = `Pain points: ${painPoints}`;
                occPainPoints.classList.remove('hidden');
            } else {
                occPainPoints.classList.add('hidden');
            }
        });
    }
    const imageUpload = document.getElementById('imageUpload');
    const videoUpload = document.getElementById('videoUpload');
    let selectedImage = null;
    let selectedVideo = null;
    if (imageUpload) {
        imageUpload.addEventListener('change', (e) => {
            if (e.target.files[0]) {
                selectedImage = e.target.files[0];
                selectedVideo = null;
                updateFilePreview(selectedImage, 'image');
            }
        });
    }
    if (videoUpload) {
        videoUpload.addEventListener('change', (e) => {
            if (e.target.files[0]) {
                selectedVideo = e.target.files[0];
                selectedImage = null;
                updateFilePreview(selectedVideo, 'video');
            }
        });
    }
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
    const { adCopy, videoScript } = getContentValues();
    const platform = document.getElementById('platform')?.value;
    const country = document.getElementById('audienceCountry')?.value;
    const age = document.getElementById('audienceAge')?.value;
    const industry = document.getElementById('industry')?.value;
    if (!adCopy && !videoScript) { alert('Please enter ad copy or video script'); return; }
    if (!platform) { alert('Please select platform'); return; }
    if (!country) { alert('Please select country'); return; }
    if (!age) { alert('Please select age bracket'); return; }
    if (!industry) { alert('Please select industry'); return; }
    emptyState.classList.add('hidden');
    resultsContent.classList.add('hidden');
    loadingState.classList.remove('hidden');
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing...';
    try {
        const formData = new FormData();
        if (adCopy) formData.append('ad_copy', adCopy);
        if (videoScript) formData.append('video_script', videoScript);
        formData.append('platform', platform);
        formData.append('audience_country', country);
        formData.append('audience_age', age);
        formData.append('industry', industry);
        formData.append('objective', document.getElementById('objective')?.value || 'conversions');
        const region = document.getElementById('audienceRegion')?.value;
        const gender = document.getElementById('audienceGender')?.value;
        const income = document.getElementById('audienceIncome')?.value;
        const education = document.getElementById('audienceEducation')?.value;
        const occupation = document.getElementById('audienceOccupation')?.value;
        const psychographic = document.getElementById('audiencePsychographic')?.value;
        const painPoint = document.getElementById('audiencePainPoint')?.value;
        const techSavviness = document.getElementById('techSavviness')?.value;
        const purchaseBehavior = document.getElementById('purchaseBehavior')?.value;
        if (region) formData.append('audience_region', region);
        if (gender) formData.append('audience_gender', gender);
        if (income) formData.append('audience_income', income);
        if (education) formData.append('audience_education', education);
        if (occupation) formData.append('audience_occupation', occupation);
        if (psychographic) formData.append('audience_psychographic', psychographic);
        if (painPoint) formData.append('audience_pain_point', painPoint);
        if (techSavviness) formData.append('tech_savviness', techSavviness);
        if (purchaseBehavior) formData.append('purchase_behavior', purchaseBehavior);
        if (selectedImage) formData.append('image', selectedImage);
        if (selectedVideo) formData.append('video', selectedVideo);
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.success && data.analysis) {
            renderResults(data);
        } else {
            throw new Error(data.error || 'Analysis returned unsuccessful');
        }
    } catch (error) {
        console.error('Analysis error:', error);
        alert(`Error: ${error.message}`);
        emptyState.classList.remove('hidden');
    } finally {
        loadingState.classList.add('hidden');
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze Ad →';
    }
}

// ===================================================================
// PATCH: NEW FUNCTION - Render Improved Ad Analysis
// ===================================================================
function renderImprovedAnalysis(data) {
    const container = document.getElementById('improvedAnalysis');
    if (!container) return;

    const score = data?.scores?.overall ?? 'N/A';
    const roi = data?.roi_analysis?.roi_potential ?? 'Unknown';
    const decision = data?.run_decision?.should_run ?? 'Unknown';
    const verdict = data?.behavior_summary?.verdict ?? 'No assessment';
    const readiness = data?.behavior_summary?.launch_readiness ?? '0%';
    
    // Determine colors based on values
    const scoreColor = score >= 70 ? 'text-green-400' : score >= 50 ? 'text-yellow-400' : 'text-red-400';
    const decisionColor = decision === 'Yes' ? 'text-green-400' : decision === 'No' ? 'text-red-400' : 'text-yellow-400';
    const roiColor = roi?.includes('High') ? 'text-green-400' : 'text-yellow-400';

    container.innerHTML = `
        <div class="bg-gradient-to-r from-green-900/20 to-blue-900/20 border border-green-500/30 rounded-xl p-5 mt-4">
            <div class="flex items-center space-x-2 mb-4">
                <span class="text-2xl">✨</span>
                <h3 class="text-green-400 text-lg font-bold">Improved Ad Performance (Re-analyzed)</h3>
            </div>
            
            <div class="grid grid-cols-2 gap-4 mb-4">
                <div class="bg-gray-900/50 rounded-lg p-3 text-center">
                    <span class="text-xs text-gray-500 block mb-1">New Score</span>
                    <span class="text-2xl font-bold ${scoreColor}">${score}</span>
                </div>
                <div class="bg-gray-900/50 rounded-lg p-3 text-center">
                    <span class="text-xs text-gray-500 block mb-1">ROI Potential</span>
                    <span class="text-lg font-bold ${roiColor}">${roi}</span>
                </div>
            </div>
            
            <div class="space-y-3">
                <div class="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                    <span class="text-sm text-gray-400">Run Decision</span>
                    <span class="font-semibold ${decisionColor}">${decision}</span>
                </div>
                
                <div class="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                    <span class="text-sm text-gray-400">Launch Readiness</span>
                    <span class="font-semibold text-white">${readiness}</span>
                </div>
                
                <div class="p-3 bg-gray-900/50 rounded-lg">
                    <span class="text-xs text-gray-500 block mb-1">Verdict</span>
                    <p class="text-sm text-gray-300">${verdict}</p>
                </div>
            </div>
            
            ${data?._fallback ? `
            <div class="mt-3 p-2 bg-yellow-500/10 border border-yellow-500/20 rounded text-center">
                <span class="text-xs text-yellow-400">⚠️ Re-analysis used fallback values</span>
            </div>
            ` : ''}
        </div>
    `;
}
// ===================================================================

// ✅ REBIND UI EVENTS AFTER DOM UPDATE (CRITICAL FIX)
function rebindUIEvents() {
    // Tabs
    const tabBtns = document.querySelectorAll('.tab-btn');
    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.onclick = () => {
                document.querySelectorAll('.tab-btn').forEach(b => {
                    b.classList.remove('tab-active');
                    b.classList.add('text-gray-400');
                });

                document.querySelectorAll('.tab-content').forEach(c => {
                    c.classList.add('hidden');
                });

                btn.classList.add('tab-active');
                btn.classList.remove('text-gray-400');

                const tabId = `tab-${btn.dataset.tab}`;
                const tabContent = document.getElementById(tabId);
                if (tabContent) tabContent.classList.remove('hidden');
            };
        });
    }

    // Dropdowns / Selects
    const selects = document.querySelectorAll('select');
    if (selects.length > 0) {
        selects.forEach(select => {
            select.onchange = (e) => {
                console.log('Selection changed:', e.target.value);
            };
        });
    }

    // Buttons with actions
    const actionBtns = document.querySelectorAll('[data-action]');
    if (actionBtns.length > 0) {
        actionBtns.forEach(btn => {
            btn.onclick = () => {
                console.log('Action triggered:', btn.dataset.action);
            };
        });
    }
}

function renderResults(data) {
    const analysis = data.analysis;
    if (!analysis) {
        console.error('No analysis data received');
        return;
    }

    const improved = analysis.improved_ad_analysis || null;

    // ✅ SAFE DEEP MERGE (CRITICAL FIX)
    const primary = improved
        ? {
            ...analysis,

            scores: {
                ...analysis.scores,
                ...improved.scores
            },

            behavior_analysis: improved.behavior_analysis || analysis.behavior_analysis,

            line_analysis: improved.line_analysis || analysis.line_analysis,

            roi_analysis: {
                ...analysis.roi_analysis,
                ...improved.roi_analysis
            },

            variants: improved.variants || analysis.variants,

            personas: improved.personas || analysis.personas,

            competitor_analysis: improved.competitor_analysis || analysis.competitor_analysis,

            run_decision: improved.run_decision || analysis.run_decision
        }
        : analysis;

    const isImprovedPrimary = !!improved;

    console.log("PRIMARY SCORE:", primary?.scores?.overall);
    console.log("ORIGINAL SCORE:", analysis?.scores?.overall); 
    console.log("IMPROVED EXISTS:", !!improved);

    resultsContent.classList.remove('hidden');

    // Run Decision (v4.0) - Display at top - USES PRIMARY
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

    // Audience Summary
    const audienceSummary = document.getElementById('audienceSummary');
    const audienceParsed = document.getElementById('audienceParsed');
    if (data.audience_parsed && audienceParsed && audienceSummary) {
        audienceParsed.textContent = data.audience_parsed;
        audienceSummary.classList.remove('hidden');
    }

    // Overall Score - USES PRIMARY
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

    // Verdict Badge - USES PRIMARY
    const verdict = primary.behavior_summary?.verdict || 'Unknown';
    const badge = document.getElementById('verdictBadge');
    if (badge) {
        badge.textContent = verdict;
        if (verdict.includes('Explosive') || verdict.includes('Strong') || verdict.includes('Win')) {
            badge.className = 'px-3 py-1 rounded-full text-sm font-medium bg-green-500/20 text-green-400';
        } else if (verdict.includes('Moderate') || verdict.includes('Medium')) {
            badge.className = 'px-3 py-1 rounded-full text-sm font-medium bg-yellow-500/20 text-yellow-400';
        } else {
            badge.className = 'px-3 py-1 rounded-full text-sm font-medium bg-red-500/20 text-red-400';
        }
    }

    // Primary Reason & Metrics - USES PRIMARY
    const primaryReasonEl = document.getElementById('primaryReason');
    if (primaryReasonEl) primaryReasonEl.textContent = primary.behavior_summary?.primary_reason || '';
    const launchReadinessEl = document.getElementById('launchReadiness');
    if (launchReadinessEl) launchReadinessEl.textContent = primary.behavior_summary?.launch_readiness || '0%';
    const failureRiskEl = document.getElementById('failureRisk');
    if (failureRiskEl) failureRiskEl.textContent = primary.behavior_summary?.failure_risk || '0%';

    // Detailed Scores - USES PRIMARY
    const scoresGrid = document.getElementById('scoresGrid');
    if (scoresGrid) {
        const scores = primary.scores || {};
        const scoreItems = [
            { key: 'hook_strength', label: 'Hook Strength' },
            { key: 'clarity', label: 'Clarity' },
            { key: 'trust_building', label: 'Trust Building' },
            { key: 'cta_power', label: 'CTA Power' },
            { key: 'audience_alignment', label: 'Audience Alignment' },
            { key: 'cultural_resonance', label: 'Cultural Resonance' },
            { key: 'decision_friction', label: 'Decision Friction (lower is better)' }
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

    // Phase Breakdown - USES PRIMARY
    const phaseDiv = document.getElementById('phaseBreakdown');
    if (phaseDiv) {
        const phases = primary.phase_breakdown || {};
        phaseDiv.innerHTML = `
            <div class="p-3 bg-gray-900/50 rounded-lg">
                <span class="text-xs text-purple-400 font-medium">0-1s MICRO-STOP</span>
                <p class="text-sm mt-1">${phases.micro_stop_0_1s || 'N/A'}</p>
            </div>
            <div class="p-3 bg-gray-900/50 rounded-lg">
                <span class="text-xs text-pink-400 font-medium">1-2s SCROLL STOP</span>
                <p class="text-sm mt-1">${phases.scroll_stop_1_2s || 'N/A'}</p>
            </div>
            <div class="p-3 bg-gray-900/50 rounded-lg">
                <span class="text-xs text-blue-400 font-medium">2-5s ATTENTION</span>
                <p class="text-sm mt-1">${phases.attention_2_5s || 'N/A'}</p>
            </div>
            <div class="p-3 bg-gray-900/50 rounded-lg">
                <span class="text-xs text-yellow-400 font-medium">5-15s TRUST EVAL</span>
                <p class="text-sm mt-1">${phases.trust_evaluation || 'N/A'}</p>
            </div>
            <div class="p-3 bg-gray-900/50 rounded-lg">
                <span class="text-xs text-green-400 font-medium">CLICK + POST-CLICK</span>
                <p class="text-sm mt-1">${phases.click_and_post_click || 'N/A'}</p>
            </div>
        `;
    }

    // Platform Specific - USES PRIMARY
    const platformDiv = document.getElementById('platformSpecific');
    if (platformDiv) {
        const platform = primary.platform_specific || {};
        platformDiv.innerHTML = `
            <h4 class="font-semibold mb-2">Platform Analysis: ${platform.platform || 'Unknown'}</h4>
            <p class="text-sm text-gray-400 mb-2">${platform.core_behavior || ''}</p>
            <div class="p-3 bg-red-500/10 border border-red-500/20 rounded-lg mt-3">
                <span class="text-red-400 font-medium text-sm">⚠️ Fatal Flaw:</span>
                <p class="text-sm mt-1">${platform.fatal_flaw || 'None detected'}</p>
            </div>
            <div class="p-3 bg-green-500/10 border border-green-500/20 rounded-lg mt-2">
                <span class="text-green-400 font-medium text-sm">✓ Fix:</span>
                <p class="text-sm mt-1">${platform['platform-specific_fix'] || 'No specific fix provided'}</p>
            </div>
        `;
    }

    // Line-by-Line Analysis - USES PRIMARY
    const lineByLineDiv = document.getElementById('lineByLineAnalysis');
    if (lineByLineDiv) {
        const lines = primary.line_by_line_analysis || [];
        if (lines.length > 0) {
            lineByLineDiv.innerHTML = lines.map((line, i) => `
                <div class="p-4 bg-gray-900/50 rounded-xl border-l-4 ${line.issue ? 'border-red-500' : 'border-green-500'} line-analysis-item">
                    <div class="flex items-start justify-between mb-2">
                        <span class="text-xs text-gray-500 font-mono">Line ${i + 1}</span>
                        ${line.impact ? `<span class="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">${line.impact}</span>` : ''}
                    </div>
                    <p class="text-sm font-medium mb-2 text-white">"${line.line || ''}"</p>
                    ${line.issue ? `
                        <div class="space-y-2">
                            <div class="p-2 bg-red-500/10 rounded-lg">
                                <span class="text-xs text-red-400 font-medium">ISSUE:</span>
                                <p class="text-sm text-gray-300">${line.issue}</p>
                            </div>
                            <div class="p-2 bg-gray-800 rounded-lg">
                                <span class="text-xs text-gray-500">WHY IT FAILS:</span>
                                <p class="text-sm text-gray-400">${line.why_it_fails || ''}</p>
                            </div>
                            <div class="p-2 bg-green-500/10 rounded-lg border border-green-500/20">
                                <span class="text-xs text-green-400 font-medium">✓ PRECISE FIX:</span>
                                <p class="text-sm text-gray-300">${line.precise_fix || ''}</p>
                            </div>
                        </div>
                    ` : '<span class="text-xs text-green-400">✓ No issues detected</span>'}
                </div>
            `).join('');
        } else {
            lineByLineDiv.innerHTML = '<p class="text-gray-500">No line-by-line analysis available.</p>';
        }
    }

    // Critical Weaknesses - USES PRIMARY
    const weaknessesDiv = document.getElementById('criticalWeaknesses');
    if (weaknessesDiv) {
        const weaknesses = primary.critical_weaknesses || [];
        if (weaknesses.length > 0) {
            weaknessesDiv.innerHTML = weaknesses.map((w, i) => `
                <div class="p-4 bg-red-500/5 border border-red-500/10 rounded-xl">
                    <div class="flex items-start justify-between">
                        <h4 class="font-semibold text-red-400">${i + 1}. ${w.issue || 'Unknown Issue'}</h4>
                        <span class="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded">${w.estimated_lift || '+0%'}</span>
                    </div>
                    <p class="text-sm text-gray-400 mt-2">${w.behavior_impact || ''}</p>
                    <div class="mt-3 p-3 bg-gray-900/50 rounded-lg">
                        <span class="text-xs text-green-400 font-medium">PRECISE FIX:</span>
                        <p class="text-sm mt-1">${w.precise_fix || 'No fix provided'}</p>
                    </div>
                </div>
            `).join('');
        } else {
            weaknessesDiv.innerHTML = '<p class="text-gray-500">No critical weaknesses detected.</p>';
        }
    }

    // Improvements - USES PRIMARY
    const improvementsDiv = document.getElementById('improvements');
    if (improvementsDiv) {
        const improvements = primary.improvements || [];
        if (improvements.length > 0) {
            improvementsDiv.innerHTML = `
                <h4 class="font-semibold mb-3">Additional Improvements</h4>
                <ul class="space-y-2">
                    ${improvements.map(imp => `<li class="text-sm text-gray-400 flex items-start"><span class="text-green-400 mr-2">→</span>${imp}</li>`).join('')}
                </ul>
            `;
        } else {
            improvementsDiv.innerHTML = '';
        }
    }

    // Improved Ad Content - USES ORIGINAL analysis.improved_ad (this is the rewrite suggestion)
    const improvedAdData = analysis.improved_ad || {};
    const improvedContent = document.getElementById('improvedContent');
    if (improvedContent) {
        improvedContent.innerHTML = `
            <div class="space-y-3">
                <div>
                    <span class="text-xs text-gray-500">HEADLINE</span>
                    <p class="font-medium">${improvedAdData.headline || 'N/A'}</p>
                </div>
                <div>
                    <span class="text-xs text-gray-500">BODY COPY</span>
                    <p class="text-sm text-gray-300 whitespace-pre-wrap">${improvedAdData.body_copy || 'N/A'}</p>
                </div>
                <div>
                    <span class="text-xs text-gray-500">CTA</span>
                    <p class="font-medium text-purple-400">${improvedAdData.cta || 'N/A'}</p>
                </div>
                ${improvedAdData.video_script_version ? `
                <div>
                    <span class="text-xs text-gray-500">VIDEO SCRIPT VERSION</span>
                    <p class="text-sm text-gray-300 whitespace-pre-wrap">${improvedAdData.video_script_version}</p>
                </div>
                ` : ''}
            </div>
        `;
    }

    // Render improved analysis section if it exists (this shows the re-analysis of the improved ad)
    if (improved) {
        renderImprovedAnalysis(improved);
    }

    // Variations - USES PRIMARY
    const variations = primary.variations || {};
    const powerHooks = variations.power_hooks || [];
    const powerHooksDiv = document.getElementById('powerHooks');
    if (powerHooksDiv) {
        powerHooksDiv.innerHTML = powerHooks.map(hook => `
            <div class="p-3 bg-gray-900/50 rounded-lg text-sm border-l-2 border-purple-500">${hook}</div>
        `).join('') || '<p class="text-gray-500 text-sm">No variations generated.</p>';
    }
    const ctas = variations.high_conversion_ctas || [];
    const conversionCTAsDiv = document.getElementById('conversionCTAs');
    if (conversionCTAsDiv) {
        conversionCTAsDiv.innerHTML = ctas.map(cta => `
            <span class="px-3 py-1 bg-purple-500/20 text-purple-400 rounded-full text-sm">${cta}</span>
        `).join('') || '<p class="text-gray-500 text-sm">No CTAs generated.</p>';
    }

    // Persona Reactions - USES PRIMARY
    const personasDiv = document.getElementById('personaReactions');
    if (personasDiv) {
        const personas = primary.persona_reactions || [];
        personasDiv.innerHTML = personas.map(p => `
            <div class="p-4 bg-gray-900/50 rounded-xl border border-white/5">
                <h4 class="font-semibold text-purple-400 mb-2">${p.persona || 'Unknown'}</h4>
                <p class="text-sm text-gray-400 mb-2">${p.reaction || ''}</p>
                <div class="p-3 bg-gray-800 rounded-lg">
                    <span class="text-xs text-gray-500">QUOTE:</span>
                    <p class="text-sm italic mt-1">"${p.exact_quote || '...'}"</p>
                </div>
            </div>
        `).join('') || '<p class="text-gray-500">No persona data available.</p>';
    }

    // ROI Analysis - USES PRIMARY
    const roiDiv = document.getElementById('roiAnalysis');
    if (roiDiv) {
        const roi = primary.roi_analysis || {};
        roiDiv.innerHTML = `
            <div class="grid grid-cols-3 gap-4">
                <div class="p-4 bg-gray-900/50 rounded-xl text-center">
                    <span class="text-xs text-gray-500">ROI Potential</span>
                    <p class="text-lg font-bold ${(roi.roi_potential || '').includes('High') ? 'text-green-400' : 'text-yellow-400'}">${roi.roi_potential || 'Unknown'}</p>
                </div>
                <div class="p-4 bg-gray-900/50 rounded-xl text-center">
                    <span class="text-xs text-gray-500">Break-Even Probability</span>
                    <p class="text-lg font-bold text-blue-400">${roi.break_even_probability || '0%'}</p>
                </div>
                <div class="p-4 bg-gray-900/50 rounded-xl text-center">
                    <span class="text-xs text-gray-500">Risk Level</span>
                    <p class="text-lg font-bold ${(roi.risk_classification || '') === 'High' ? 'text-red-400' : 'text-green-400'}">${roi.risk_classification || 'Unknown'}</p>
                </div>
            </div>
            <div class="p-4 bg-gray-900/50 rounded-xl">
                <h4 class="font-semibold mb-3">Key Metrics</h4>
                <div class="grid grid-cols-3 gap-4 text-sm">
                    <div>
                        <span class="text-gray-500">Expected CTR</span>
                        <p class="font-medium">${roi.key_metrics?.expected_ctr_range || 'N/A'}</p>
                    </div>
                    <div>
                        <span class="text-gray-500">Realistic CPC</span>
                        <p class="font-medium">${roi.key_metrics?.realistic_cpc_range || 'N/A'}</p>
                    </div>
                    <div>
                        <span class="text-gray-500">Conversion Rate</span>
                        <p class="font-medium">${roi.key_metrics?.conversion_rate_range || 'N/A'}</p>
                    </div>
                </div>
            </div>
            <div class="p-4 bg-gray-900/50 rounded-xl">
                <h4 class="font-semibold mb-3">ROI Scenarios</h4>
                <div class="space-y-2 text-sm">
                    <div class="flex justify-between">
                        <span class="text-red-400">Worst Case:</span>
                        <span class="text-gray-400">${roi.roi_scenarios?.worst_case || 'N/A'}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-yellow-400">Expected:</span>
                        <span class="text-gray-400">${roi.roi_scenarios?.expected_case || 'N/A'}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-green-400">Best Case:</span>
                        <span class="text-gray-400">${roi.roi_scenarios?.best_case || 'N/A'}</span>
                    </div>
                </div>
            </div>
            <div class="p-4 bg-purple-500/10 border border-purple-500/20 rounded-xl">
                <h4 class="font-semibold text-purple-400 mb-2">Primary ROI Lever</h4>
                <p class="text-sm">${roi.primary_roi_lever || 'N/A'}</p>
            </div>
            <div class="p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                <h4 class="font-semibold text-red-400 mb-2">⚠️ Biggest Financial Risk</h4>
                <p class="text-sm">${roi.biggest_financial_risk || 'N/A'}</p>
            </div>
            ${roi.optimization_priority ? `
            <div class="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                <h4 class="font-semibold text-blue-400 mb-2">Optimization Priority</h4>
                <p class="text-sm">${roi.optimization_priority}</p>
            </div>
            ` : ''}
        `;
    }

    // Video Analysis - USES PRIMARY
    const videoDiv = document.getElementById('videoAnalysis');
    if (videoDiv) {
        const video = primary.video_execution_analysis || {};
        videoDiv.innerHTML = `
            <div class="p-4 bg-gray-900/50 rounded-xl">
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <span class="text-xs text-purple-400 font-medium">Hook Delivery</span>
                        <p class="text-sm mt-1">${video.hook_delivery_strength || 'N/A'}</p>
                    </div>
                    <div>
                        <span class="text-xs text-blue-400 font-medium">Speech Flow</span>
                        <p class="text-sm mt-1">${video.speech_flow_quality || 'N/A'}</p>
                    </div>
                    <div>
                        <span class="text-xs text-yellow-400 font-medium">Pattern Interrupt</span>
                        <p class="text-sm mt-1">${video.pattern_interrupt_strength || 'N/A'}</p>
                    </div>
                    <div>
                        <span class="text-xs text-pink-400 font-medium">Visual Dependency</span>
                        <p class="text-sm mt-1">${video.visual_dependency || 'N/A'}</p>
                    </div>
                </div>
                <div class="p-3 bg-red-500/10 border border-red-500/20 rounded-lg mb-3">
                    <span class="text-red-400 font-medium text-xs">⚠️ Delivery Risk</span>
                    <p class="text-sm mt-1">${video.delivery_risk || 'N/A'}</p>
                </div>
                <div class="p-3 bg-green-500/10 border border-green-500/20 rounded-lg mb-3">
                    <span class="text-green-400 font-medium text-xs">✓ Recommended Format</span>
                    <p class="text-sm mt-1">${video.recommended_format || 'talking head'}</p>
                </div>
                ${video.execution_gaps?.length ? `
                <div class="space-y-2">
                    <span class="text-xs text-gray-500">Execution Gaps:</span>
                    ${video.execution_gaps.map(gap => `
                        <div class="p-2 bg-gray-800 rounded text-sm text-gray-400">• ${gap}</div>
                    `).join('')}
                </div>
                ` : ''}
                ${video.exact_fix_direction ? `
                <div class="mt-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                    <span class="text-blue-400 font-medium text-xs">Exact Fix Direction</span>
                    <p class="text-sm mt-1">${video.exact_fix_direction}</p>
                </div>
                ` : ''}
            </div>
        `;
    }

    // Winner Prediction - USES PRIMARY
    const winnerDiv = document.getElementById('winnerPrediction');
    if (winnerDiv) {
        const winner = primary.winner_prediction || {};
        winnerDiv.innerHTML = `
            <div class="p-4 bg-gradient-to-r from-green-500/10 to-purple-500/10 rounded-xl border border-green-500/20">
                <div class="flex items-center space-x-3 mb-3">
                    <span class="text-2xl">🏆</span>
                    <div>
                        <h4 class="font-semibold text-green-400">Winner Prediction</h4>
                        <p class="text-xs text-gray-400">Confidence: ${winner.confidence || 'Unknown'}</p>
                    </div>
                </div>
                <p class="text-sm text-gray-300 mb-3">${winner.reason || 'No prediction available'}</p>
                <div class="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                    <span class="text-sm text-gray-400">Best Variant ID</span>
                    <span class="text-lg font-bold text-green-400">#${winner.best_variant_id || 'N/A'}</span>
                </div>
                ${winner.expected_lift ? `
                <div class="mt-3 p-3 bg-green-500/20 rounded-lg text-center">
                    <span class="text-green-400 font-medium">Expected Lift: ${winner.expected_lift}</span>
                </div>
                ` : ''}
            </div>
        `;
    }

    // Ad Variants - USES PRIMARY
    const variantsDiv = document.getElementById('adVariants');
    if (variantsDiv) {
        const variants = primary.ad_variants || [];
        if (variants.length > 0) {
            variantsDiv.innerHTML = `
                <div class="space-y-4">
                    ${variants.map((v, i) => `
                        <div class="variant-card p-4 bg-gray-900/50 rounded-xl border ${v.id === primary.winner_prediction?.best_variant_id ? 'border-green-500/50 bg-green-500/5' : 'border-white/5'}">
                            <div class="flex items-start justify-between mb-3">
                                <div class="flex items-center space-x-3">
                                    <span class="w-8 h-8 rounded-full ${v.id === primary.winner_prediction?.best_variant_id ? 'bg-green-500 text-white' : 'bg-gray-700 text-gray-400'} flex items-center justify-center font-bold text-sm">${v.id}</span>
                                    <div>
                                        <h4 class="font-semibold ${v.id === primary.winner_prediction?.best_variant_id ? 'text-green-400' : 'text-white'}">${v.angle || `Variant ${v.id}`}</h4>
                                        <span class="text-xs text-gray-500">ROI: ${v.roi_potential || 'Unknown'}</span>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <span class="text-lg font-bold ${v.predicted_score >= 70 ? 'text-green-400' : v.predicted_score >= 50 ? 'text-yellow-400' : 'text-red-400'}">${v.predicted_score || 0}</span>
                                    <p class="text-xs text-gray-500">predicted score</p>
                                </div>
                            </div>
                            <div class="p-3 bg-gray-800 rounded-lg mb-3">
                                <span class="text-xs text-purple-400 font-medium">HOOK:</span>
                                <p class="text-sm mt-1 italic">"${v.hook || ''}"</p>
                            </div>
                            <div class="p-3 bg-gray-800 rounded-lg mb-3">
                                <span class="text-xs text-gray-500">FULL COPY:</span>
                                <p class="text-sm mt-1 text-gray-300">${v.copy || ''}</p>
                            </div>
                            <p class="text-xs text-gray-400">${v.reason || ''}</p>
                            ${v.id === primary.winner_prediction?.best_variant_id ? `
                            <div class="mt-3 p-2 bg-green-500/20 rounded-lg text-center">
                                <span class="text-green-400 text-sm font-medium">🏆 PREDICTED WINNER</span>
                            </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            variantsDiv.innerHTML = '<p class="text-gray-500">No ad variants generated.</p>';
        }
    }

    // ROI Comparison - USES PRIMARY
    const roiCompareDiv = document.getElementById('roiComparison');
    if (roiCompareDiv) {
        const comparisons = primary.roi_comparison || [];
        if (comparisons.length > 0) {
            roiCompareDiv.innerHTML = `
                <div class="space-y-3">
                    ${comparisons.map(c => `
                        <div class="p-3 bg-gray-900/50 rounded-lg">
                            <div class="flex items-center justify-between mb-2">
                                <div class="flex items-center space-x-3">
                                    <span class="w-6 h-6 rounded-full bg-gray-700 text-gray-400 flex items-center justify-center text-xs font-bold">${c.variant_id}</span>
                                    <span class="text-sm font-medium">Variant ${c.variant_id}</span>
                                </div>
                                <div class="text-right">
                                    <p class="text-sm ${c.roi_potential?.includes('High') ? 'text-green-400' : 'text-yellow-400'}">${c.roi_potential || 'Unknown'}</p>
                                    <p class="text-xs text-gray-500">Risk: ${c.risk || 'Unknown'}</p>
                                </div>
                            </div>
                            <p class="text-xs text-gray-400">${c.summary || ''}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            roiCompareDiv.innerHTML = '<p class="text-gray-500">No ROI comparison available.</p>';
        }
    }

    // Competitor Advantage - USES PRIMARY
    const competitorDiv = document.getElementById('competitorAdvantage');
    if (competitorDiv) {
        const comp = primary.competitor_advantage || {};
        competitorDiv.innerHTML = `
            <div class="space-y-4">
                <div class="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <span class="text-xs text-red-400 font-medium">Why Users Choose Competitor:</span>
                    <p class="text-sm mt-1 text-gray-300">${comp.why_user_might_choose_competitor || 'N/A'}</p>
                </div>
                <div class="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                    <span class="text-xs text-yellow-400 font-medium">What They Do Better:</span>
                    <p class="text-sm mt-1 text-gray-300">${comp.what_competitor_is_doing_better || 'N/A'}</p>
                </div>
                <div class="p-3 bg-gray-800 rounded-lg">
                    <span class="text-xs text-gray-500">Execution Difference:</span>
                    <p class="text-sm mt-1 text-gray-400">${comp.execution_difference || 'N/A'}</p>
                </div>
                <div class="p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                    <span class="text-xs text-green-400 font-medium">✓ How to Outperform:</span>
                    <p class="text-sm mt-1 text-gray-300">${comp.how_to_outperform || 'N/A'}</p>
                </div>
            </div>
        `;
    }

    // ✅ CRITICAL: Rebind all UI events after DOM update
    rebindUIEvents();
}// Tab Navigation - Event binding handled by rebindUIEvents() after render

console.log('ADLYTICS v4.0 Enhanced Analyzer loaded (PATCHED with Improved Ad Re-analysis)');
