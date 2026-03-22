// ============================================
// ADLYTICS v4.1 - SELECT DROPDOWNS FIXED
// All select buttons working properly
// ============================================

// Global variables
let currentContentMode = 'adCopy';
let analysisResults = null;
let audienceConfig = null;

// DOM Elements
let form, analyzeBtn, resultsSection, loadingIndicator;
let platformSelect, industrySelect, countrySelect, regionSelect;
let ageSelect, genderSelect, incomeSelect, educationSelect;
let occupationSelect, psychographicSelect, painPointSelect;
let techSavvinessSelect, purchaseBehaviorSelect;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 ADLYTICS v4.1 Initializing...');

    // Assign ALL DOM elements FIRST
    assignDOMElements();

    console.log('DOM Elements assigned:', { 
        form: !!form, 
        platformSelect: !!platformSelect,
        countrySelect: !!countrySelect,
        ageSelect: !!ageSelect
    });

    // Load audience config and populate dropdowns
    await loadAudienceConfig();

    // Setup all event listeners
    setupEventListeners();
    setupContentTabs();

    console.log('✅ ADLYTICS v4.1 Initialized');
});

// ============================================
// ASSIGN ALL DOM ELEMENTS
// ============================================
function assignDOMElements() {
    // Form elements
    form = document.getElementById('analyzeForm');
    analyzeBtn = document.getElementById('analyzeBtn');
    resultsSection = document.getElementById('resultsSection');
    loadingIndicator = document.getElementById('loadingIndicator');

    // Select dropdowns - CRITICAL FIX: Get all selects by ID
    platformSelect = document.getElementById('platform');
    industrySelect = document.getElementById('industry');
    countrySelect = document.getElementById('country');
    regionSelect = document.getElementById('region');
    ageSelect = document.getElementById('age');
    genderSelect = document.getElementById('gender');
    incomeSelect = document.getElementById('income');
    educationSelect = document.getElementById('education');
    occupationSelect = document.getElementById('occupation');
    psychographicSelect = document.getElementById('psychographic');
    painPointSelect = document.getElementById('pain_point');
    techSavvinessSelect = document.getElementById('tech_savviness');
    purchaseBehaviorSelect = document.getElementById('purchase_behavior');

    console.log('Select elements found:', {
        platform: !!platformSelect,
        industry: !!industrySelect,
        country: !!countrySelect,
        region: !!regionSelect,
        age: !!ageSelect,
        gender: !!genderSelect
    });
}

// ============================================
// LOAD AUDIENCE CONFIG
// ============================================
async function loadAudienceConfig() {
    try {
        console.log('Loading audience config...');
        const response = await fetch('/api/audience-config');
        audienceConfig = await response.json();
        console.log('Audience config loaded:', audienceConfig);

        // Populate ALL dropdowns
        populateAllDropdowns();

    } catch (error) {
        console.error('Failed to load audience config:', error);
        // Use default config
        audienceConfig = getDefaultAudienceConfig();
        populateAllDropdowns();
    }
}

// ============================================
// POPULATE ALL DROPDOWNS
// ============================================
function populateAllDropdowns() {
    console.log('Populating all dropdowns...');

    if (!audienceConfig) {
        console.error('No audience config available');
        return;
    }

    // Platform
    if (platformSelect) {
        populateSelect(platformSelect, [
            { value: '', label: 'Select Platform' },
            { value: 'facebook', label: 'Facebook' },
            { value: 'instagram', label: 'Instagram' },
            { value: 'tiktok', label: 'TikTok' },
            { value: 'youtube', label: 'YouTube' },
            { value: 'google', label: 'Google Ads' },
            { value: 'linkedin', label: 'LinkedIn' },
            { value: 'twitter', label: 'Twitter/X' }
        ]);
        console.log('✅ Platform dropdown populated');
    }

    // Industry
    if (industrySelect) {
        populateSelect(industrySelect, [
            { value: '', label: 'Select Industry' },
            { value: 'ecommerce', label: 'E-commerce' },
            { value: 'saas', label: 'SaaS / Software' },
            { value: 'finance', label: 'Finance / Crypto' },
            { value: 'health', label: 'Health & Fitness' },
            { value: 'education', label: 'Education' },
            { value: 'realestate', label: 'Real Estate' },
            { value: 'travel', label: 'Travel' },
            { value: 'food', label: 'Food & Beverage' },
            { value: 'fashion', label: 'Fashion' },
            { value: 'technology', label: 'Technology' },
            { value: 'consulting', label: 'Consulting' },
            { value: 'other', label: 'Other' }
        ]);
        console.log('✅ Industry dropdown populated');
    }

    // Country
    if (countrySelect && audienceConfig.countries) {
        const countries = Object.keys(audienceConfig.countries).map(code => ({
            value: code,
            label: audienceConfig.countries[code].name
        }));
        populateSelect(countrySelect, [
            { value: '', label: 'Select Country' },
            ...countries
        ]);
        console.log('✅ Country dropdown populated with', countries.length, 'countries');

        // Add change listener for country
        countrySelect.addEventListener('change', handleCountryChange);
    }

    // Age
    if (ageSelect) {
        populateSelect(ageSelect, [
            { value: '', label: 'Select Age' },
            { value: '18-24', label: '18-24 (Gen Z)' },
            { value: '25-34', label: '25-34 (Millennials)' },
            { value: '35-44', label: '35-44' },
            { value: '45-54', label: '45-54 (Gen X)' },
            { value: '55-64', label: '55-64' },
            { value: '65+', label: '65+ (Seniors)' }
        ]);
        console.log('✅ Age dropdown populated');
    }

    // Gender
    if (genderSelect) {
        populateSelect(genderSelect, [
            { value: 'any', label: 'Any' },
            { value: 'male', label: 'Male' },
            { value: 'female', label: 'Female' }
        ]);
        console.log('✅ Gender dropdown populated');
    }

    // Income
    if (incomeSelect) {
        populateSelect(incomeSelect, [
            { value: '', label: 'Select Income Level' },
            { value: 'low', label: 'Low (< $30k/year)' },
            { value: 'lower-middle', label: 'Lower Middle ($30k-$50k)' },
            { value: 'middle', label: 'Middle ($50k-$75k)' },
            { value: 'upper-middle', label: 'Upper Middle ($75k-$100k)' },
            { value: 'high', label: 'High ($100k+)' }
        ]);
        console.log('✅ Income dropdown populated');
    }

    // Education
    if (educationSelect) {
        populateSelect(educationSelect, [
            { value: '', label: 'Select Education' },
            { value: 'high-school', label: 'High School' },
            { value: 'some-college', label: 'Some College' },
            { value: 'bachelors', label: "Bachelor's Degree" },
            { value: 'masters', label: "Master's Degree" },
            { value: 'doctorate', label: 'Doctorate' },
            { value: 'professional', label: 'Professional Degree' }
        ]);
        console.log('✅ Education dropdown populated');
    }

    // Occupation
    if (occupationSelect) {
        populateSelect(occupationSelect, [
            { value: '', label: 'Select Occupation' },
            { value: 'professional', label: 'Professional/White Collar' },
            { value: 'entrepreneur', label: 'Entrepreneur/Business Owner' },
            { value: 'student', label: 'Student' },
            { value: 'retired', label: 'Retired' },
            { value: 'homemaker', label: 'Homemaker' },
            { value: 'freelancer', label: 'Freelancer/Creator' },
            { value: 'trades', label: 'Trades/Blue Collar' },
            { value: 'unemployed', label: 'Unemployed/Looking for Work' }
        ]);
        console.log('✅ Occupation dropdown populated');
    }

    // Psychographic
    if (psychographicSelect) {
        populateSelect(psychographicSelect, [
            { value: '', label: 'Select Psychographic' },
            { value: 'value-seeker', label: 'Value Seeker (price conscious)' },
            { value: 'quality-focused', label: 'Quality Focused (premium buyer)' },
            { value: 'innovator', label: 'Innovator (early adopter)' },
            { value: 'pragmatist', label: 'Pragmatist (practical buyer)' },
            { value: 'aspirational', label: 'Aspirational (status seeker)' }
        ]);
        console.log('✅ Psychographic dropdown populated');
    }

    // Pain Points
    if (painPointSelect) {
        populateSelect(painPointSelect, [
            { value: '', label: 'Select Pain Point' },
            { value: 'saving-time', label: 'Saving Time' },
            { value: 'saving-money', label: 'Saving Money' },
            { value: 'reducing-stress', label: 'Reducing Stress' },
            { value: 'improving-health', label: 'Improving Health' },
            { value: 'growing-income', label: 'Growing Income' },
            { value: 'learning-skills', label: 'Learning New Skills' },
            { value: 'social-status', label: 'Social Status/Recognition' }
        ]);
        console.log('✅ Pain Point dropdown populated');
    }

    // Tech Savviness
    if (techSavvinessSelect) {
        populateSelect(techSavvinessSelect, [
            { value: 'medium', label: 'Medium' },
            { value: 'low', label: 'Low (needs simple UI)' },
            { value: 'high', label: 'High (early adopter)' }
        ]);
        console.log('✅ Tech Savviness dropdown populated');
    }

    // Purchase Behavior
    if (purchaseBehaviorSelect) {
        populateSelect(purchaseBehaviorSelect, [
            { value: 'research', label: 'Researcher (compares options)' },
            { value: 'impulse', label: 'Impulse Buyer (quick decision)' },
            { value: 'loyal', label: 'Brand Loyal (sticks to favorites)' },
            { value: 'bargain', label: 'Bargain Hunter (seeks deals)' }
        ]);
        console.log('✅ Purchase Behavior dropdown populated');
    }

    console.log('✅ All dropdowns populated successfully');
}

// ============================================
// POPULATE SELECT HELPER
// ============================================
function populateSelect(selectElement, options) {
    if (!selectElement) {
        console.warn('Select element not found');
        return;
    }

    // Clear existing options
    selectElement.innerHTML = '';

    // Add new options
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.label;
        selectElement.appendChild(option);
    });

    console.log(`Populated ${selectElement.id} with ${options.length} options`);
}

// ============================================
// HANDLE COUNTRY CHANGE (Update Regions)
// ============================================
function handleCountryChange(e) {
    const countryCode = e.target.value;
    console.log('Country changed to:', countryCode);

    if (!regionSelect || !audienceConfig || !countryCode) {
        if (regionSelect) {
            populateSelect(regionSelect, [{ value: '', label: 'Select Region' }]);
        }
        return;
    }

    const countryData = audienceConfig.countries[countryCode];
    if (countryData && countryData.regions) {
        const regions = countryData.regions.map(r => ({
            value: r.toLowerCase().replace(/\s+/g, '-'),
            label: r
        }));
        populateSelect(regionSelect, [
            { value: '', label: 'Select Region' },
            ...regions
        ]);
        console.log('✅ Regions updated for', countryCode);
    }
}

// ============================================
// CONTENT TABS
// ============================================
function setupContentTabs() {
    const tabs = document.querySelectorAll('.content-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.dataset.mode;
            console.log('Content mode changed to:', mode);
            currentContentMode = mode;

            // Update active state
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Show/hide textareas
            const adCopyContainer = document.getElementById('adCopyContainer');
            const videoScriptContainer = document.getElementById('videoScriptContainer');

            if (adCopyContainer) {
                adCopyContainer.style.display = mode === 'adCopy' ? 'block' : 'none';
            }
            if (videoScriptContainer) {
                videoScriptContainer.style.display = mode === 'videoScript' ? 'block' : 'none';
            }
        });
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
        console.log('✅ Form submit listener added');
    }

    // Log all select changes for debugging
    const allSelects = document.querySelectorAll('select');
    allSelects.forEach(select => {
        select.addEventListener('change', (e) => {
            console.log(`Select ${e.target.id} changed to:`, e.target.value);
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
// RENDER RESULTS
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
    }

    // Update other elements...
    // (Full render code would go here)
}

// ============================================
// DEFAULT CONFIG
// ============================================
function getDefaultAudienceConfig() {
    return {
        countries: {
            us: { name: 'United States', regions: ['California', 'Texas', 'New York', 'Florida', 'Illinois'] },
            uk: { name: 'United Kingdom', regions: ['England', 'Scotland', 'Wales', 'Northern Ireland'] },
            ca: { name: 'Canada', regions: ['Ontario', 'Quebec', 'British Columbia', 'Alberta'] },
            au: { name: 'Australia', regions: ['New South Wales', 'Victoria', 'Queensland', 'Western Australia'] },
            ng: { name: 'Nigeria', regions: ['Lagos', 'Abuja', 'Kano', 'Rivers', 'Oyo'] }
        }
    };
}
