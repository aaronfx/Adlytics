// ============================================
// ADLYTICS v4.1 - FULLY FIXED VERSION
// All selects working + input boxes persistent
// ============================================

// Global state
let currentContentMode = 'adCopy';
let analysisResults = null;
let currentTab = 'behavior';
let audienceConfig = null;
let isInitialized = false;

// ============================================
// INITIALIZATION - Run immediately if DOM ready
// ============================================
function init() {
    if (isInitialized) return;
    isInitialized = true;

    console.log('🚀 ADLYTICS v4.1 Initializing...');

    // Fix selects immediately
    fixAllSelects();

    // Setup content tabs
    setupContentTabs();

    // Setup form
    setupFormHandler();

    // Setup results tabs
    setupResultsTabs();

    // Ensure input boxes are visible
    ensureInputBoxesVisible();

    // Load audience config for regions
    loadAudienceConfig().then(() => {
        setupRegionDependency();
    });

    console.log('✅ ADLYTICS v4.1 Ready');
}

// Run init when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Also run on window load (backup)
window.addEventListener('load', () => {
    if (!isInitialized) init();
    ensureInputBoxesVisible();
});

// ============================================
// FIX ALL SELECTS - Comprehensive fix
// ============================================
function fixAllSelects() {
    console.log('🔧 Fixing all selects...');

    const allSelectData = {
        'platform': [
            ['', 'Select Platform'],
            ['facebook', 'Facebook'],
            ['instagram', 'Instagram'],
            ['tiktok', 'TikTok'],
            ['youtube', 'YouTube'],
            ['google', 'Google Ads'],
            ['linkedin', 'LinkedIn'],
            ['twitter', 'Twitter/X']
        ],
        'industry': [
            ['', 'Select Industry'],
            ['ecommerce', 'E-commerce'],
            ['saas', 'SaaS / Software'],
            ['finance', 'Finance / Crypto'],
            ['health', 'Health & Fitness'],
            ['education', 'Education'],
            ['realestate', 'Real Estate'],
            ['travel', 'Travel'],
            ['food', 'Food & Beverage'],
            ['fashion', 'Fashion'],
            ['technology', 'Technology'],
            ['consulting', 'Consulting'],
            ['other', 'Other']
        ],
        'campaign_objective': [
            ['', 'Select Objective'],
            ['sales', 'Sales / Conversions'],
            ['leads', 'Lead Generation'],
            ['traffic', 'Website Traffic'],
            ['awareness', 'Brand Awareness'],
            ['engagement', 'Engagement']
        ],
        'country': [
            ['', 'Select Country'],
            ['us', 'United States'],
            ['uk', 'United Kingdom'],
            ['ca', 'Canada'],
            ['au', 'Australia'],
            ['ng', 'Nigeria'],
            ['gh', 'Ghana'],
            ['ke', 'Kenya'],
            ['za', 'South Africa'],
            ['in', 'India'],
            ['de', 'Germany']
        ],
        'region': [['', 'Select Region']],
        'age': [
            ['', 'Select Age'],
            ['18-24', '18-24 (Gen Z)'],
            ['25-34', '25-34 (Millennials)'],
            ['35-44', '35-44'],
            ['45-54', '45-54 (Gen X)'],
            ['55-64', '55-64'],
            ['65+', '65+ (Seniors)']
        ],
        'gender': [
            ['any', 'Any'],
            ['male', 'Male'],
            ['female', 'Female']
        ],
        'income': [
            ['', 'Select Income Level'],
            ['low', 'Low (< $30k/year)'],
            ['lower-middle', 'Lower Middle ($30k-$50k)'],
            ['middle', 'Middle ($50k-$75k)'],
            ['upper-middle', 'Upper Middle ($75k-$100k)'],
            ['high', 'High ($100k+)']
        ],
        'education': [
            ['', 'Select Education'],
            ['high-school', 'High School'],
            ['some-college', 'Some College'],
            ['bachelors', "Bachelor's Degree"],
            ['masters', "Master's Degree"],
            ['doctorate', 'Doctorate'],
            ['professional', 'Professional Degree']
        ],
        'occupation': [
            ['', 'Select Occupation'],
            ['professional', 'Professional/White Collar'],
            ['entrepreneur', 'Entrepreneur/Business Owner'],
            ['student', 'Student'],
            ['retired', 'Retired'],
            ['homemaker', 'Homemaker'],
            ['freelancer', 'Freelancer/Creator'],
            ['trades', 'Trades/Blue Collar'],
            ['unemployed', 'Unemployed/Looking for Work']
        ],
        'psychographic': [
            ['', 'Select Psychographic'],
            ['value-seeker', 'Value Seeker'],
            ['quality-focused', 'Quality Focused'],
            ['innovator', 'Innovator'],
            ['pragmatist', 'Pragmatist'],
            ['aspirational', 'Aspirational']
        ],
        'pain_point': [
            ['', 'Select Pain Point'],
            ['saving-time', 'Saving Time'],
            ['saving-money', 'Saving Money'],
            ['reducing-stress', 'Reducing Stress'],
            ['improving-health', 'Improving Health'],
            ['growing-income', 'Growing Income'],
            ['learning-skills', 'Learning New Skills'],
            ['social-status', 'Social Status']
        ],
        'tech_savviness': [
            ['medium', 'Medium'],
            ['low', 'Low'],
            ['high', 'High']
        ],
        'purchase_behavior': [
            ['research', 'Researcher'],
            ['impulse', 'Impulse Buyer'],
            ['loyal', 'Brand Loyal'],
            ['bargain', 'Bargain Hunter']
        ]
    };

    // Find ALL selects on the page and fix them
    const allSelects = document.querySelectorAll('select');
    console.log(`Found ${allSelects.length} select elements`);

    allSelects.forEach(select => {
        const id = select.id || select.name;
        if (!id) {
            console.log('Select has no id/name, skipping');
            return;
        }

        // Find matching data
        let data = allSelectData[id];

        // Try partial match
        if (!data) {
            for (const [key, value] of Object.entries(allSelectData)) {
                if (id.includes(key) || key.includes(id)) {
                    data = value;
                    break;
                }
            }
        }

        if (data) {
            populateSelect(select, data);
            console.log(`✅ Fixed: ${id}`);
        } else {
            console.log(`⚠️ No data for: ${id}`);
        }
    });

    console.log('✅ All selects fixed');
}

function populateSelect(select, options) {
    // Save current value
    const currentValue = select.value;

    // Clear and rebuild
    select.innerHTML = '';

    options.forEach(([value, label]) => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = label;
        select.appendChild(option);
    });

    // Restore value if valid
    if (currentValue) {
        const exists = Array.from(select.options).some(o => o.value === currentValue);
        if (exists) {
            select.value = currentValue;
        }
    }

    // Ensure select is enabled and visible
    select.disabled = false;
    select.style.display = 'block';
}

// ============================================
// ENSURE INPUT BOXES VISIBLE
// ============================================
function ensureInputBoxesVisible() {
    console.log('👁️ Ensuring input boxes visible...');

    const adCopyContainer = document.getElementById('adCopyContainer');
    const videoScriptContainer = document.getElementById('videoScriptContainer');
    const adCopy = document.getElementById('adCopy');
    const videoScript = document.getElementById('videoScript');

    // Make sure containers exist
    if (!adCopyContainer) {
        console.log('Creating adCopyContainer...');
        createInputContainer('adCopyContainer', 'adCopy', 'Enter your ad copy here...');
    }
    if (!videoScriptContainer) {
        console.log('Creating videoScriptContainer...');
        createInputContainer('videoScriptContainer', 'videoScript', 'Enter your video script here...');
    }

    // Show correct container based on mode
    if (adCopyContainer) {
        adCopyContainer.style.display = currentContentMode === 'adCopy' ? 'block' : 'none';
    }
    if (videoScriptContainer) {
        videoScriptContainer.style.display = currentContentMode === 'videoScript' ? 'block' : 'none';
    }

    // Ensure textareas exist and are visible
    if (adCopy) {
        adCopy.style.display = 'block';
        adCopy.style.width = '100%';
        adCopy.style.minHeight = '150px';
    }
    if (videoScript) {
        videoScript.style.display = 'block';
        videoScript.style.width = '100%';
        videoScript.style.minHeight = '150px';
    }

    console.log('✅ Input boxes visible');
}

function createInputContainer(containerId, textareaId, placeholder) {
    // Find the content tabs container
    const contentTabs = document.querySelector('.content-tabs') || document.querySelector('[class*="tab"]');
    if (!contentTabs) {
        console.log('Could not find content tabs container');
        return;
    }

    // Create container
    const container = document.createElement('div');
    container.id = containerId;
    container.style.marginTop = '20px';
    container.style.display = containerId === 'adCopyContainer' ? 'block' : 'none';

    // Create textarea
    const textarea = document.createElement('textarea');
    textarea.id = textareaId;
    textarea.name = textareaId;
    textarea.placeholder = placeholder;
    textarea.style.width = '100%';
    textarea.style.minHeight = '150px';
    textarea.style.padding = '12px';
    textarea.style.borderRadius = '8px';
    textarea.style.border = '1px solid #475569';
    textarea.style.background = '#1e293b';
    textarea.style.color = '#f8fafc';
    textarea.style.fontSize = '14px';
    textarea.style.resize = 'vertical';

    container.appendChild(textarea);
    contentTabs.parentNode.insertBefore(container, contentTabs.nextSibling);
}

// ============================================
// CONTENT TABS
// ============================================
function setupContentTabs() {
    const tabs = document.querySelectorAll('.content-tab');

    if (tabs.length === 0) {
        console.log('No content tabs found');
        return;
    }

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.dataset.mode;
            if (!mode) return;

            currentContentMode = mode;
            console.log('Content mode:', mode);

            // Update active state
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Show/hide containers
            ensureInputBoxesVisible();
        });
    });

    // Set initial active tab
    const activeTab = document.querySelector('.content-tab.active') || tabs[0];
    if (activeTab) {
        currentContentMode = activeTab.dataset.mode || 'adCopy';
        activeTab.classList.add('active');
    }
}

// ============================================
// FORM HANDLER
// ============================================
function setupFormHandler() {
    const form = document.getElementById('analyzeForm');
    if (!form) {
        console.log('Form not found');
        return;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('📝 Form submitted');

        const analyzeBtn = document.getElementById('analyzeBtn');
        const loadingIndicator = document.getElementById('loadingIndicator');
        const resultsSection = document.getElementById('resultsSection');

        if (analyzeBtn) analyzeBtn.disabled = true;
        if (loadingIndicator) loadingIndicator.style.display = 'block';

        try {
            const formData = new FormData(form);

            // Get content based on mode
            const adCopy = document.getElementById('adCopy')?.value?.trim() || '';
            const videoScript = document.getElementById('videoScript')?.value?.trim() || '';

            console.log('Mode:', currentContentMode);
            console.log('Ad copy length:', adCopy.length);
            console.log('Video script length:', videoScript.length);

            // Add to form data
            if (currentContentMode === 'adCopy' && adCopy) {
                formData.set('ad_copy', adCopy);
            } else if (currentContentMode === 'videoScript' && videoScript) {
                formData.set('video_script', videoScript);
            } else if (currentContentMode === 'both') {
                if (adCopy) formData.set('ad_copy', adCopy);
                if (videoScript) formData.set('video_script', videoScript);
            }

            // Debug: log form data
            for (let [key, value] of formData.entries()) {
                console.log(`${key}: ${value.toString().substring(0, 50)}...`);
            }

            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            console.log('Response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Server error:', errorText);
                throw new Error(`Server error: ${response.status}`);
            }

            const data = await response.json();
            console.log('Response:', data);

            if (data.success) {
                analysisResults = data.analysis;
                renderResults(analysisResults);
                if (resultsSection) {
                    resultsSection.style.display = 'block';
                    resultsSection.scrollIntoView({ behavior: 'smooth' });
                }
            } else {
                alert('Analysis failed: ' + (data.error || 'Unknown error'));
            }

        } catch (error) {
            console.error('❌ Error:', error);
            alert('Error: ' + error.message);
        } finally {
            if (analyzeBtn) analyzeBtn.disabled = false;
            if (loadingIndicator) loadingIndicator.style.display = 'none';
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

            // Update buttons
            tabButtons.forEach(b => {
                b.classList.toggle('active', b.dataset.tab === tabId);
            });

            // Update content
            tabContents.forEach(content => {
                const isActive = content.id === `tab-${tabId}`;
                content.style.display = isActive ? 'block' : 'none';
            });
        });
    });

    // Activate first tab
    if (tabButtons[0]) {
        tabButtons[0].click();
    }
}

// ============================================
// RENDER RESULTS (Full implementation)
// ============================================
function renderResults(analysis) {
    console.log('🎨 Rendering results...');

    if (!analysis) {
        console.error('No analysis data');
        return;
    }

    const scores = analysis.scores || {};
    const overallScore = scores.overall || 0;

    // Update score displays
    updateText('overallScore', overallScore);
    updateText('scoreCircle', overallScore);

    // Color code the score
    const scoreColor = overallScore >= 70 ? '#22c55e' : overallScore >= 50 ? '#f59e0b' : '#ef4444';
    const scoreCircle = document.getElementById('scoreCircle');
    if (scoreCircle) scoreCircle.style.background = scoreColor;

    // Verdict
    const verdict = analysis.run_decision?.verdict || 'REVIEW';
    updateText('verdictBadge', verdict);

    // Readiness and risk
    updateText('launchReadiness', (analysis.run_decision?.readiness || 0) + '%');
    updateText('failureRisk', (analysis.run_decision?.risk || 0) + '%');

    // Render all sections
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

    console.log('✅ Results rendered');
}

function updateText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

// [All render helper functions from previous version...]
// Including: renderPerformanceBreakdown, renderPhaseBreakdown, etc.

function renderPerformanceBreakdown(scores) {
    const container = document.getElementById('performanceBreakdown');
    if (!container) return;

    const metrics = [
        ['hook_strength', 'Hook Strength'],
        ['clarity', 'Clarity'],
        ['trust_building', 'Trust Building'],
        ['cta_power', 'CTA Power'],
        ['audience_alignment', 'Audience Alignment']
    ];

    container.innerHTML = metrics.map(([key, label]) => {
        const score = scores[key] || 0;
        const color = score >= 70 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444';
        return `<div class="metric"><span>${label}</span><div class="bar" style="width:${score}%;background:${color}"></div><span>${score}</span></div>`;
    }).join('');
}

function renderPhaseBreakdown(phases) {
    const container = document.getElementById('phaseBreakdown');
    if (!container || !phases?.phases) return;
    container.innerHTML = phases.phases.map((p, i) => 
        `<div>${i+1}. ${p.name}: ${p.score}/100</div>`
    ).join('');
}

function renderBehaviorSummary(summary) {
    const container = document.getElementById('behaviorSummary');
    if (!container || !summary) return;
    container.innerHTML = `
        <div>Attention: ${summary.attention_capture || 'N/A'}</div>
        <div>Interest: ${summary.interest_maintenance || 'N/A'}</div>
        <div>Desire: ${summary.desire_generation || 'N/A'}</div>
        <div>Action: ${summary.action_motivation || 'N/A'}</div>
    `;
}

function renderLineByLine(lines) {
    const container = document.getElementById('lineByLineAnalysis');
    if (!container) return;
    if (!lines || lines.length === 0) {
        container.innerHTML = '<p>No line analysis</p>';
        return;
    }
    container.innerHTML = lines.map(l => 
        `<div>"${l.text}" - Score: ${l.score}</div>`
    ).join('');
}

function renderWeaknesses(weaknesses) {
    const container = document.getElementById('criticalWeaknesses');
    if (!container) return;
    if (!weaknesses || weaknesses.length === 0) {
        container.innerHTML = '<p>✅ No critical weaknesses</p>';
        return;
    }
    container.innerHTML = weaknesses.map(w => 
        `<div><strong>${w.severity}:</strong> ${w.title} - ${w.fix}</div>`
    ).join('');
}

function renderImprovements(improvements) {
    const container = document.getElementById('improvementsList');
    if (!container) return;
    if (!improvements || improvements.length === 0) {
        container.innerHTML = '<p>No improvements</p>';
        return;
    }
    container.innerHTML = improvements.map((imp, i) => 
        `<div>${i+1}. ${imp}</div>`
    ).join('');
}

function renderImprovedAd(ad) {
    const container = document.getElementById('improvedAdContent');
    if (!container) return;
    if (!ad) {
        container.innerHTML = '<p>No improved ad</p>';
        return;
    }
    container.innerHTML = `
        <div><strong>Headline:</strong> ${ad.headline || 'N/A'}</div>
        <div><strong>Body:</strong> ${ad.body_copy || 'N/A'}</div>
        <div><strong>CTA:</strong> ${ad.cta || 'N/A'}</div>
        <div>Score: ${ad.predicted_score || 0}/100 | ROI: ${ad.roi_potential || 'N/A'}</div>
        <button onclick="copyImprovedAd()">Copy</button>
    `;
}

function renderVariants(variants) {
    const container = document.getElementById('adVariantsList');
    if (!container) return;
    if (!variants || variants.length === 0) {
        container.innerHTML = '<p>No variants</p>';
        return;
    }
    container.innerHTML = variants.map((v, i) => 
        `<div class="${i===0?'best':''}">Variant #${v.id}: ${v.angle} - ${v.predicted_score}/100 ${i===0?'🏆':''}</div>`
    ).join('');
}

function renderWinnerPrediction(prediction) {
    const container = document.getElementById('winnerPrediction');
    if (!container) return;
    if (!prediction) {
        container.innerHTML = '<p>No prediction</p>';
        return;
    }
    container.innerHTML = `
        <div>${prediction.confidence} Confidence</div>
        <div>${prediction.reason}</div>
        <div>Lift: ${prediction.expected_lift || 'N/A'}</div>
    `;
}

function renderPersonas(personas) {
    const container = document.getElementById('personaReactions');
    if (!container) return;
    if (!personas || personas.length === 0) {
        container.innerHTML = '<p>No personas</p>';
        return;
    }
    container.innerHTML = personas.map(p => 
        `<div>${p.name}: ${p.reaction} - "${p.thought}"</div>`
    ).join('');
}

function renderROI(roi) {
    const container = document.getElementById('roiAnalysis');
    if (!container) return;
    if (!roi) {
        container.innerHTML = '<p>No ROI data</p>';
        return;
    }
    container.innerHTML = `
        <div>ROAS: ${roi.roas || 'N/A'}</div>
        <div>Break-even: ${roi.break_even || 'N/A'}</div>
        <div>Risk: ${roi.risk || 'N/A'}</div>
    `;
}

function renderVideoExecution(video) {
    const container = document.getElementById('videoExecution');
    if (!container) return;
    if (!video) {
        container.innerHTML = '<p>No video analysis</p>';
        return;
    }
    container.innerHTML = `
        <div>Hook: ${video.hook_delivery || 'N/A'}</div>
        <div>Flow: ${video.speech_flow || 'N/A'}</div>
        <div>Visual: ${video.visual_dependency || 'N/A'}</div>
    `;
}

// ============================================
// UTILITIES
// ============================================
function copyImprovedAd() {
    if (!analysisResults?.improved_ad) return;
    const ad = analysisResults.improved_ad;
    const text = `${ad.headline}\n\n${ad.body_copy}\n\n${ad.cta}`;
    navigator.clipboard.writeText(text).then(() => alert('✅ Copied!'));
}

async function loadAudienceConfig() {
    try {
        const response = await fetch('/api/audience-config');
        if (response.ok) {
            audienceConfig = await response.json();
        }
    } catch (e) {
        audienceConfig = {
            countries: {
                us: { regions: ['California', 'Texas', 'New York'] },
                uk: { regions: ['England', 'Scotland'] },
                ng: { regions: ['Lagos', 'Abuja', 'Kano'] }
            }
        };
    }
}

function setupRegionDependency() {
    const countrySelect = document.getElementById('country');
    const regionSelect = document.getElementById('region');
    if (!countrySelect || !regionSelect) return;

    countrySelect.addEventListener('change', () => {
        const country = countrySelect.value;
        const regions = audienceConfig?.countries?.[country]?.regions || [];
        regionSelect.innerHTML = '<option value="">Select Region</option>';
        regions.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.toLowerCase().replace(/\s+/g, '-');
            opt.textContent = r;
            regionSelect.appendChild(opt);
        });
    });
}
