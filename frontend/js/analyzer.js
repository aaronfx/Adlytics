/**
 * ADLYTICS - Enhanced Analyzer JavaScript
 * Handles detailed audience targeting with dependent dropdowns
 */

const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api' 
    : '/api';

// Global audience config
let audienceConfig = null;

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
});

// Load audience configuration from backend
async function loadAudienceConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/audience-config`);
        if (!response.ok) throw new Error('Failed to load audience config');

        audienceConfig = await response.json();
        populateAudienceFields();
    } catch (error) {
        console.error('Error loading audience config:', error);
        // Fallback to basic options if API fails
        populateBasicAudienceOptions();
    }
}

// Populate all audience dropdowns
function populateAudienceFields() {
    if (!audienceConfig) return;

    // Countries
    const countrySelect = document.getElementById('audienceCountry');
    audienceConfig.countries.forEach(country => {
        const option = document.createElement('option');
        option.value = country.code;
        option.textContent = `${country.name} (${country.currency})`;
        option.dataset.regions = JSON.stringify(country.regions);
        option.dataset.currency = country.currency;
        countrySelect.appendChild(option);
    });

    // Age brackets
    const ageSelect = document.getElementById('audienceAge');
    audienceConfig.age_brackets.forEach(age => {
        const option = document.createElement('option');
        option.value = age.value;
        option.textContent = age.label;
        option.dataset.traits = age.traits;
        ageSelect.appendChild(option);
    });

    // Income levels
    const incomeSelect = document.getElementById('audienceIncome');
    audienceConfig.income_levels.forEach(income => {
        const option = document.createElement('option');
        option.value = income.value;
        option.textContent = income.label;
        option.dataset.description = income.description;
        incomeSelect.appendChild(option);
    });

    // Education levels
    const eduSelect = document.getElementById('audienceEducation');
    audienceConfig.education_levels.forEach(edu => {
        const option = document.createElement('option');
        option.value = edu.value;
        option.textContent = edu.label;
        eduSelect.appendChild(option);
    });

    // Occupations
    const occSelect = document.getElementById('audienceOccupation');
    audienceConfig.occupations.forEach(occ => {
        const option = document.createElement('option');
        option.value = occ.value;
        option.textContent = occ.label;
        option.dataset.painPoints = occ.pain_points;
        occSelect.appendChild(option);
    });

    // Psychographics
    const psychSelect = document.getElementById('audiencePsychographic');
    audienceConfig.psychographics.forEach(psych => {
        const option = document.createElement('option');
        option.value = psych.value;
        option.textContent = psych.label;
        option.dataset.traits = psych.traits;
        psychSelect.appendChild(option);
    });

    // Pain points
    const painSelect = document.getElementById('audiencePainPoint');
    audienceConfig.pain_points.forEach(pain => {
        const option = document.createElement('option');
        option.value = pain.value;
        option.textContent = pain.label;
        option.dataset.description = pain.description;
        painSelect.appendChild(option);
    });
}

// Fallback if API fails
function populateBasicAudienceOptions() {
    const countries = [
        {code: 'NG', name: 'Nigeria', currency: '₦'},
        {code: 'US', name: 'United States', currency: '$'},
        {code: 'GB', name: 'United Kingdom', currency: '£'}
    ];

    const countrySelect = document.getElementById('audienceCountry');
    countries.forEach(c => {
        const option = document.createElement('option');
        option.value = c.code;
        option.textContent = `${c.name} (${c.currency})`;
        countrySelect.appendChild(option);
    });
}

// Load platforms
async function loadPlatforms() {
    try {
        const response = await fetch(`${API_BASE_URL}/platforms`);
        if (!response.ok) return;

        const data = await response.json();
        const select = document.getElementById('platform');

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
    // Country → Region dependency
    const countrySelect = document.getElementById('audienceCountry');
    const regionSelect = document.getElementById('audienceRegion');

    countrySelect?.addEventListener('change', (e) => {
        const selected = e.target.selectedOptions[0];
        const regions = JSON.parse(selected.dataset.regions || '[]');

        regionSelect.innerHTML = '<option value="">Select Region</option>';

        if (regions.length > 0) {
            regionSelect.disabled = false;
            regions.forEach(region => {
                const option = document.createElement('option');
                option.value = region;
                option.textContent = region;
                regionSelect.appendChild(option);
            });
        } else {
            regionSelect.disabled = true;
        }
    });

    // Age traits display
    const ageSelect = document.getElementById('audienceAge');
    const ageTraits = document.getElementById('ageTraits');

    ageSelect?.addEventListener('change', (e) => {
        const traits = e.target.selectedOptions[0]?.dataset.traits;
        if (traits) {
            ageTraits.textContent = traits;
            ageTraits.classList.remove('hidden');
        } else {
            ageTraits.classList.add('hidden');
        }
    });

    // Occupation pain points display
    const occSelect = document.getElementById('audienceOccupation');
    const occPainPoints = document.getElementById('occupationPainPoints');

    occSelect?.addEventListener('change', (e) => {
        const painPoints = e.target.selectedOptions[0]?.dataset.painPoints;
        if (painPoints) {
            occPainPoints.textContent = `Pain points: ${painPoints}`;
            occPainPoints.classList.remove('hidden');
        } else {
            occPainPoints.classList.add('hidden');
        }
    });

    // File uploads
    const imageUpload = document.getElementById('imageUpload');
    const videoUpload = document.getElementById('videoUpload');

    let selectedImage = null;
    let selectedVideo = null;

    imageUpload?.addEventListener('change', (e) => {
        if (e.target.files[0]) {
            selectedImage = e.target.files[0];
            selectedVideo = null;
            updateFilePreview(selectedImage, 'image');
        }
    });

    videoUpload?.addEventListener('change', (e) => {
        if (e.target.files[0]) {
            selectedVideo = e.target.files[0];
            selectedImage = null;
            updateFilePreview(selectedVideo, 'video');
        }
    });

    // Form submission
    form?.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleSubmit(selectedImage, selectedVideo);
    });
}

function updateFilePreview(file, type) {
    const icon = type === 'image' ? '📷' : '🎥';
    filePreview.textContent = `${icon} ${file.name} (${(file.size/1024/1024).toFixed(2)}MB)`;
    filePreview.classList.remove('hidden');
}

async function handleSubmit(selectedImage, selectedVideo) {
    const adCopy = document.getElementById('adCopy').value.trim();
    const platform = document.getElementById('platform').value;
    const country = document.getElementById('audienceCountry').value;
    const age = document.getElementById('audienceAge').value;
    const industry = document.getElementById('industry').value;

    // Validation
    if (!adCopy) { alert('Please enter ad copy'); return; }
    if (!platform) { alert('Please select platform'); return; }
    if (!country) { alert('Please select country'); return; }
    if (!age) { alert('Please select age bracket'); return; }
    if (!industry) { alert('Please select industry'); return; }

    // Show loading
    emptyState.classList.add('hidden');
    resultsContent.classList.add('hidden');
    loadingState.classList.remove('hidden');
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing...';

    try {
        const formData = new FormData();
        formData.append('ad_copy', adCopy);
        formData.append('platform', platform);
        formData.append('audience_country', country);
        formData.append('audience_age', age);
        formData.append('industry', industry);
        formData.append('objective', document.getElementById('objective').value);

        // Optional fields
        const region = document.getElementById('audienceRegion').value;
        const gender = document.getElementById('audienceGender').value;
        const income = document.getElementById('audienceIncome').value;
        const education = document.getElementById('audienceEducation').value;
        const occupation = document.getElementById('audienceOccupation').value;
        const psychographic = document.getElementById('audiencePsychographic').value;
        const painPoint = document.getElementById('audiencePainPoint').value;
        const techSavviness = document.getElementById('techSavviness').value;
        const purchaseBehavior = document.getElementById('purchaseBehavior').value;

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

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }

        const data = await response.json();

        if (data.success) {
            renderResults(data);
        } else {
            throw new Error('Analysis returned unsuccessful');
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

function renderResults(data) {
    const analysis = data.analysis;

    resultsContent.classList.remove('hidden');

    // Audience summary
    const audienceSummary = document.getElementById('audienceSummary');
    const audienceParsed = document.getElementById('audienceParsed');
    if (data.audience_parsed) {
        audienceParsed.textContent = data.audience_parsed;
        audienceSummary.classList.remove('hidden');
    }

    // Overall Score
    const overall = analysis.scores?.overall || 0;
    document.getElementById('overallScore').textContent = overall;

    const circle = document.getElementById('scoreCircle');
    const circumference = 251.2;
    const offset = circumference - (overall / 100) * circumference;
    setTimeout(() => {
        circle.style.strokeDashoffset = offset;
        if (overall >= 70) circle.style.stroke = '#10b981';
        else if (overall >= 50) circle.style.stroke = '#f59e0b';
        else circle.style.stroke = '#ef4444';
    }, 100);

    // Verdict badge
    const verdict = analysis.behavior_summary?.verdict || 'Unknown';
    const badge = document.getElementById('verdictBadge');
    badge.textContent = verdict;
    if (verdict.includes('Explosive') || verdict.includes('Strong')) {
        badge.className = 'px-3 py-1 rounded-full text-sm font-medium bg-green-500/20 text-green-400';
    } else if (verdict.includes('Moderate')) {
        badge.className = 'px-3 py-1 rounded-full text-sm font-medium bg-yellow-500/20 text-yellow-400';
    } else {
        badge.className = 'px-3 py-1 rounded-full text-sm font-medium bg-red-500/20 text-red-400';
    }

    document.getElementById('primaryReason').textContent = analysis.behavior_summary?.primary_reason || '';
    document.getElementById('launchReadiness').textContent = analysis.behavior_summary?.launch_readiness || '0%';
    document.getElementById('failureRisk').textContent = analysis.behavior_summary?.failure_risk || '0%';

    // Detailed Scores
    const scoresGrid = document.getElementById('scoresGrid');
    const scores = analysis.scores || {};
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

    // Phase Breakdown
    const phaseDiv = document.getElementById('phaseBreakdown');
    const phases = analysis.phase_breakdown || {};
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

    // Platform Specific
    const platformDiv = document.getElementById('platformSpecific');
    const platform = analysis.platform_specific || {};
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

    // Critical Weaknesses
    const weaknessesDiv = document.getElementById('criticalWeaknesses');
    const weaknesses = analysis.critical_weaknesses || [];
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

    // Improvements
    const improvementsDiv = document.getElementById('improvements');
    const improvements = analysis.improvements || [];
    if (improvements.length > 0) {
        improvementsDiv.innerHTML = `
            <h4 class="font-semibold mb-3">Additional Improvements</h4>
            <ul class="space-y-2">
                ${improvements.map(imp => `<li class="text-sm text-gray-400 flex items-start"><span class="text-green-400 mr-2">→</span>${imp}</li>`).join('')}
            </ul>
        `;
    }

    // Improved Ad
    const improved = analysis.improved_ad || {};
    document.getElementById('improvedContent').innerHTML = `
        <div class="space-y-3">
            <div>
                <span class="text-xs text-gray-500">HEADLINE</span>
                <p class="font-medium">${improved.headline || 'N/A'}</p>
            </div>
            <div>
                <span class="text-xs text-gray-500">BODY COPY</span>
                <p class="text-sm text-gray-300 whitespace-pre-wrap">${improved.body_copy || 'N/A'}</p>
            </div>
            <div>
                <span class="text-xs text-gray-500">CTA</span>
                <p class="font-medium text-purple-400">${improved.cta || 'N/A'}</p>
            </div>
        </div>
    `;

    // Variations
    const variations = analysis.variations || {};
    const hooks = variations.power_hooks || [];
    document.getElementById('powerHooks').innerHTML = hooks.map(hook => `
        <div class="p-3 bg-gray-900/50 rounded-lg text-sm border-l-2 border-purple-500">${hook}</div>
    `).join('') || '<p class="text-gray-500 text-sm">No variations generated.</p>';

    const ctas = variations.high_conversion_ctas || [];
    document.getElementById('conversionCTAs').innerHTML = ctas.map(cta => `
        <span class="px-3 py-1 bg-purple-500/20 text-purple-400 rounded-full text-sm">${cta}</span>
    `).join('') || '<p class="text-gray-500 text-sm">No CTAs generated.</p>';

    // Persona Reactions
    const personasDiv = document.getElementById('personaReactions');
    const personas = analysis.persona_reactions || [];
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

    // ROI Analysis
    const roiDiv = document.getElementById('roiAnalysis');
    const roi = analysis.roi_analysis || {};
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
    `;
}

// Tab Navigation
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
        document.getElementById(tabId).classList.remove('hidden');
    });
});

console.log('ADLYTICS Enhanced Analyzer loaded');
