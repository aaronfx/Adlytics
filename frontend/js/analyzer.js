// ============================================
// ADLYTICS v4.1 - COMPLETE WORKING VERSION
// All functionality preserved + select fixes
// ============================================

// Global state
let currentContentMode = 'adCopy';
let analysisResults = null;
let currentTab = 'behavior';
let audienceConfig = null;

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 ADLYTICS v4.1 Initializing...');

    try {
        // Initialize all components
        await initializeApp();
        console.log('✅ ADLYTICS v4.1 Ready');
    } catch (error) {
        console.error('❌ Initialization error:', error);
    }
});

async function initializeApp() {
    // Load audience config
    await loadAudienceConfig();

    // Setup all event handlers
    setupContentTabs();
    setupFormHandler();
    setupTabs();

    // Fix any broken selects
    fixSelectDropdowns();
}

// ============================================
// AUDIENCE CONFIG
// ============================================
async function loadAudienceConfig() {
    try {
        const response = await fetch('/api/audience-config');
        if (response.ok) {
            audienceConfig = await response.json();
            console.log('✅ Audience config loaded');
        }
    } catch (e) {
        console.log('Using default config');
        audienceConfig = getDefaultConfig();
    }
}

function getDefaultConfig() {
    return {
        countries: {
            us: { name: 'United States', regions: ['California', 'Texas', 'New York', 'Florida', 'Illinois'] },
            uk: { name: 'United Kingdom', regions: ['England', 'Scotland', 'Wales', 'Northern Ireland'] },
            ca: { name: 'Canada', regions: ['Ontario', 'Quebec', 'British Columbia', 'Alberta'] },
            au: { name: 'Australia', regions: ['New South Wales', 'Victoria', 'Queensland', 'Western Australia'] },
            ng: { name: 'Nigeria', regions: ['Lagos', 'Abuja', 'Kano', 'Rivers', 'Oyo'] },
            gh: { name: 'Ghana', regions: ['Greater Accra', 'Ashanti', 'Western', 'Eastern'] },
            ke: { name: 'Kenya', regions: ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru'] },
            za: { name: 'South Africa', regions: ['Gauteng', 'Western Cape', 'KwaZulu-Natal', 'Eastern Cape'] },
            in: { name: 'India', regions: ['Maharashtra', 'Delhi', 'Karnataka', 'Tamil Nadu'] },
            de: { name: 'Germany', regions: ['Bavaria', 'North Rhine-Westphalia', 'Baden-Württemberg'] }
        }
    };
}

// ============================================
// SELECT DROPDOWN FIXES
// ============================================
function fixSelectDropdowns() {
    console.log('🔧 Fixing select dropdowns...');

    const selectConfigs = {
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

    // Apply fixes to each select
    Object.entries(selectConfigs).forEach(([id, options]) => {
        const select = document.getElementById(id);
        if (select) {
            populateSelect(select, options);
            console.log(`✅ Fixed ${id}`);
        }
    });

    // Setup country -> region dependency
    setupRegionDependency();

    console.log('✅ All selects fixed');
}

function populateSelect(select, options) {
    const currentValue = select.value;
    select.innerHTML = '';

    options.forEach(([value, label]) => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = label;
        select.appendChild(option);
    });

    // Restore selection if valid
    if (currentValue && Array.from(select.options).some(o => o.value === currentValue)) {
        select.value = currentValue;
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
        regions.forEach(region => {
            const option = document.createElement('option');
            option.value = region.toLowerCase().replace(/\s+/g, '-');
            option.textContent = region;
            regionSelect.appendChild(option);
        });
    });
}

// ============================================
// CONTENT TABS (Ad Copy / Video Script / Both)
// ============================================
function setupContentTabs() {
    const tabs = document.querySelectorAll('.content-tab');
    const adCopyContainer = document.getElementById('adCopyContainer');
    const videoScriptContainer = document.getElementById('videoScriptContainer');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.dataset.mode;
            currentContentMode = mode;

            // Update active state
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Show/hide containers
            if (adCopyContainer) {
                adCopyContainer.style.display = mode === 'adCopy' ? 'block' : 'none';
            }
            if (videoScriptContainer) {
                videoScriptContainer.style.display = mode === 'videoScript' ? 'block' : 'none';
            }

            console.log('Content mode:', mode);
        });
    });
}

// ============================================
// FORM HANDLER
// ============================================
function setupFormHandler() {
    const form = document.getElementById('analyzeForm');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsSection = document.getElementById('resultsSection');

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('📝 Form submitted');

        if (analyzeBtn) analyzeBtn.disabled = true;
        if (loadingIndicator) loadingIndicator.style.display = 'block';

        try {
            const formData = new FormData(form);

            // Add content based on mode
            const adCopy = document.getElementById('adCopy')?.value?.trim() || '';
            const videoScript = document.getElementById('videoScript')?.value?.trim() || '';

            if (currentContentMode === 'adCopy' && adCopy) {
                formData.set('ad_copy', adCopy);
            } else if (currentContentMode === 'videoScript' && videoScript) {
                formData.set('video_script', videoScript);
            }

            console.log('📤 Sending request...');
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            console.log('📥 Response:', data);

            if (data.success) {
                analysisResults = data.analysis;
                renderResults(analysisResults);
                if (resultsSection) resultsSection.style.display = 'block';
                if (resultsSection) resultsSection.scrollIntoView({ behavior: 'smooth' });
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
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    if (tabButtons.length === 0) return;

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            currentTab = tabId;

            // Update buttons
            tabButtons.forEach(b => {
                b.classList.toggle('active', b.dataset.tab === tabId);
            });

            // Update content
            tabContents.forEach(content => {
                const isActive = content.id === `tab-${tabId}`;
                content.style.display = isActive ? 'block' : 'none';
                content.classList.toggle('active', isActive);
            });
        });
    });

    // Activate first tab
    if (tabButtons[0]) {
        tabButtons[0].click();
    }
}

// ============================================
// RENDER RESULTS
// ============================================
function renderResults(analysis) {
    console.log('🎨 Rendering results...');

    if (!analysis) return;

    const scores = analysis.scores || {};
    const overallScore = scores.overall || 0;

    // Score display
    updateElement('overallScore', overallScore);
    updateElement('scoreCircle', overallScore);

    // Color coding
    const scoreColor = overallScore >= 70 ? '#22c55e' : overallScore >= 50 ? '#f59e0b' : '#ef4444';
    const scoreCircle = document.getElementById('scoreCircle');
    if (scoreCircle) {
        scoreCircle.style.background = scoreColor;
    }

    // Verdict
    const verdict = analysis.run_decision?.verdict || 'REVIEW';
    updateElement('verdictBadge', verdict);

    // Readiness & Risk
    const readiness = analysis.run_decision?.readiness || 0;
    const risk = analysis.run_decision?.risk || 0;
    updateElement('launchReadiness', readiness + '%');
    updateElement('failureRisk', risk + '%');

    // Performance breakdown
    renderPerformanceBreakdown(scores);

    // Phase breakdown
    renderPhaseBreakdown(analysis.phase_breakdown);

    // Behavior summary
    renderBehaviorSummary(analysis.behavior_summary);

    // Line by line
    renderLineByLine(analysis.line_by_line_analysis);

    // Weaknesses
    renderWeaknesses(analysis.critical_weaknesses);

    // Improvements
    renderImprovements(analysis.improvements);

    // Improved ad
    renderImprovedAd(analysis.improved_ad);

    // Variants
    renderVariants(analysis.ad_variants);

    // Winner prediction
    renderWinnerPrediction(analysis.winner_prediction);

    // Personas
    renderPersonas(analysis.persona_reactions);

    // ROI
    renderROI(analysis.roi_analysis);

    // Video
    renderVideoExecution(analysis.video_execution_analysis);

    console.log('✅ Results rendered');
}

function updateElement(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

// ============================================
// RENDER HELPERS
// ============================================
function renderPerformanceBreakdown(scores) {
    const container = document.getElementById('performanceBreakdown');
    if (!container) return;

    const metrics = [
        { key: 'hook_strength', label: 'Hook Strength', weight: 25 },
        { key: 'clarity', label: 'Clarity', weight: 20 },
        { key: 'trust_building', label: 'Trust Building', weight: 20 },
        { key: 'cta_power', label: 'CTA Power', weight: 15 },
        { key: 'audience_alignment', label: 'Audience Alignment', weight: 20 }
    ];

    container.innerHTML = metrics.map(m => {
        const score = scores[m.key] || 0;
        const color = score >= 70 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444';
        return `
            <div class="metric-row">
                <span class="metric-label">${m.label}</span>
                <div class="metric-bar-bg">
                    <div class="metric-bar" style="width: ${score}%; background: ${color}"></div>
                </div>
                <span class="metric-score" style="color: ${color}">${score}</span>
            </div>
        `;
    }).join('');
}

function renderPhaseBreakdown(phases) {
    const container = document.getElementById('phaseBreakdown');
    if (!container || !phases?.phases) {
        if (container) container.innerHTML = '<p>No phase data</p>';
        return;
    }

    container.innerHTML = phases.phases.map((phase, i) => `
        <div class="phase-item">
            <span class="phase-num">${i + 1}</span>
            <span class="phase-name">${phase.name}</span>
            <div class="phase-bar-bg">
                <div class="phase-bar" style="width: ${phase.score}%"></div>
            </div>
            <span class="phase-score">${phase.score}</span>
        </div>
    `).join('');
}

function renderBehaviorSummary(summary) {
    const container = document.getElementById('behaviorSummary');
    if (!container) return;

    const sections = [
        ['Attention Capture', summary?.attention_capture],
        ['Interest Maintenance', summary?.interest_maintenance],
        ['Desire Generation', summary?.desire_generation],
        ['Action Motivation', summary?.action_motivation]
    ];

    container.innerHTML = sections.map(([title, content]) => `
        <div class="summary-section">
            <h4>${title}</h4>
            <p>${content || 'N/A'}</p>
        </div>
    `).join('');
}

function renderLineByLine(lines) {
    const container = document.getElementById('lineByLineAnalysis');
    if (!container) return;

    if (!lines || lines.length === 0) {
        container.innerHTML = '<p>No line-by-line analysis</p>';
        return;
    }

    container.innerHTML = lines.map(line => `
        <div class="line-item">
            <p class="line-text">"${line.text}"</p>
            <span class="line-score">Score: ${line.score}/100</span>
            <p class="line-issue">${line.issue || 'No issues'}</p>
        </div>
    `).join('');
}

function renderWeaknesses(weaknesses) {
    const container = document.getElementById('criticalWeaknesses');
    if (!container) return;

    if (!weaknesses || weaknesses.length === 0) {
        container.innerHTML = '<p class="no-issues">✅ No critical weaknesses</p>';
        return;
    }

    container.innerHTML = weaknesses.map(w => `
        <div class="weakness-item severity-${w.severity}">
            <span class="weakness-severity">${w.severity}</span>
            <h4>${w.title}</h4>
            <p>${w.description}</p>
            <p class="weakness-fix">💡 ${w.fix}</p>
        </div>
    `).join('');
}

function renderImprovements(improvements) {
    const container = document.getElementById('improvementsList');
    if (!container) return;

    if (!improvements || improvements.length === 0) {
        container.innerHTML = '<p>No improvements suggested</p>';
        return;
    }

    container.innerHTML = improvements.map((imp, i) => `
        <div class="improvement-item">
            <span class="imp-num">${i + 1}</span>
            <p>${imp}</p>
        </div>
    `).join('');
}

function renderImprovedAd(ad) {
    const container = document.getElementById('improvedAdContent');
    if (!container) return;

    if (!ad) {
        container.innerHTML = '<p>No improved ad available</p>';
        return;
    }

    container.innerHTML = `
        <div class="improved-ad-display">
            <div class="ad-section">
                <label>Headline/Hook:</label>
                <p>${ad.headline || 'N/A'}</p>
            </div>
            <div class="ad-section">
                <label>Body Copy:</label>
                <p>${ad.body_copy || 'N/A'}</p>
            </div>
            <div class="ad-section">
                <label>CTA:</label>
                <p>${ad.cta || 'N/A'}</p>
            </div>
            <div class="ad-meta">
                <span>Score: ${ad.predicted_score || 0}/100</span>
                <span>ROI: ${ad.roi_potential || 'N/A'}</span>
            </div>
            <button onclick="copyImprovedAd()" class="copy-btn">📋 Copy</button>
        </div>
    `;
}

function renderVariants(variants) {
    const container = document.getElementById('adVariantsList');
    if (!container) return;

    if (!variants || variants.length === 0) {
        container.innerHTML = '<p>No variants generated</p>';
        return;
    }

    container.innerHTML = variants.map((v, i) => `
        <div class="variant-card ${i === 0 ? 'best' : ''}">
            <div class="variant-header">
                <span>Variant #${v.id}</span>
                <span class="variant-angle">${v.angle}</span>
                <span class="variant-score">${v.predicted_score}/100</span>
            </div>
            <p class="variant-hook">${v.hook}</p>
            <p class="variant-copy">${v.copy}</p>
            <p class="variant-roi">ROI: ${v.roi_potential}</p>
            ${i === 0 ? '<span class="best-badge">🏆 BEST</span>' : ''}
        </div>
    `).join('');
}

function renderWinnerPrediction(prediction) {
    const container = document.getElementById('winnerPrediction');
    if (!container) return;

    if (!prediction) {
        container.innerHTML = '<p>No prediction available</p>';
        return;
    }

    container.innerHTML = `
        <div class="winner-card">
            <h4>${prediction.confidence} Confidence</h4>
            <p>${prediction.reason}</p>
            <p>Expected Lift: ${prediction.expected_lift || 'N/A'}</p>
        </div>
    `;
}

function renderPersonas(personas) {
    const container = document.getElementById('personaReactions');
    if (!container) return;

    if (!personas || personas.length === 0) {
        container.innerHTML = '<p>No persona data</p>';
        return;
    }

    container.innerHTML = personas.map(p => `
        <div class="persona-card">
            <h4>${p.name}</h4>
            <span class="reaction ${p.reaction.toLowerCase()}">${p.reaction}</span>
            <p>"${p.thought}"</p>
        </div>
    `).join('');
}

function renderROI(roi) {
    const container = document.getElementById('roiAnalysis');
    if (!container) return;

    if (!roi) {
        container.innerHTML = '<p>No ROI analysis</p>';
        return;
    }

    container.innerHTML = `
        <div class="roi-grid">
            <div class="roi-item">
                <span>Expected ROAS</span>
                <strong>${roi.roas || 'N/A'}</strong>
            </div>
            <div class="roi-item">
                <span>Break-even</span>
                <strong>${roi.break_even || 'N/A'}</strong>
            </div>
            <div class="roi-item">
                <span>Risk Level</span>
                <strong class="risk-${(roi.risk || '').toLowerCase()}">${roi.risk || 'N/A'}</strong>
            </div>
            <div class="roi-item">
                <span>Confidence</span>
                <strong>${roi.confidence || 'N/A'}</strong>
            </div>
        </div>
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
        <div class="video-analysis">
            <div class="video-section">
                <h4>Hook Delivery</h4>
                <p>${video.hook_delivery || 'N/A'}</p>
            </div>
            <div class="video-section">
                <h4>Speech Flow</h4>
                <p>${video.speech_flow || 'N/A'}</p>
            </div>
            <div class="video-section">
                <h4>Visual Dependency</h4>
                <p>${video.visual_dependency || 'N/A'}</p>
            </div>
            <div class="video-section">
                <h4>Format Recommendation</h4>
                <p>${video.format_recommendation || 'N/A'}</p>
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
    const text = `${ad.headline}\n\n${ad.body_copy}\n\n${ad.cta}`;

    navigator.clipboard.writeText(text).then(() => {
        alert('✅ Copied to clipboard!');
    }).catch(() => {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        alert('✅ Copied to clipboard!');
    });
}
