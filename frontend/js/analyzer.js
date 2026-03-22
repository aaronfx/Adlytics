/**
 * ADLYTICS - Analyzer JavaScript v4.1 FIXED SELECTS
 * Fixed event listeners for dropdown buttons
 */

const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api' 
    : '/api';

// Global audience config
let audienceConfig = null;
let currentContentMode = 'adCopy';

// DOM Elements - will be assigned after DOM loads
let form, analyzeBtn, loadingState, emptyState, resultsContent, filePreview;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 ADLYTICS v4.1 Initializing...');

    // Assign DOM elements
    form = document.getElementById('analyzeForm');
    analyzeBtn = document.getElementById('analyzeBtn');
    loadingState = document.getElementById('loadingState');
    emptyState = document.getElementById('emptyState');
    resultsContent = document.getElementById('resultsContent');
    filePreview = document.getElementById('filePreview');

    console.log('DOM Elements assigned:', {
        form: !!form,
        analyzeBtn: !!analyzeBtn,
        loadingState: !!loadingState,
        emptyState: !!emptyState,
        resultsContent: !!resultsContent,
        filePreview: !!filePreview
    });

    await loadAudienceConfig();
    await loadPlatforms();
    await loadIndustries();
    setupEventListeners();
    setupContentTabs();
    setupTextareaCounters();

    console.log('✅ ADLYTICS v4.1 Initialized');
});

// Setup content type tabs
function setupContentTabs() {
    const tabs = document.querySelectorAll('.content-tab');
    console.log('Setting up content tabs:', tabs.length, 'tabs found');

    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            console.log('Content tab clicked:', tab.dataset.target);

            // Remove active from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            // Add active to clicked tab
            tab.classList.add('active');

            // Show corresponding content
            const target = tab.dataset.target;
            document.querySelectorAll('.textarea-container').forEach(container => {
                container.classList.remove('active');
            });

            const targetContainer = document.getElementById(target);
            if (targetContainer) {
                targetContainer.classList.add('active');
                currentContentMode = target.replace('Container', '');
                console.log('Content mode changed to:', currentContentMode);
            }
        });
    });
}

// Setup textarea character/word counters
function setupTextareaCounters() {
    const adCopy = document.getElementById('adCopy');
    const videoScript = document.getElementById('videoScript');

    if (adCopy) {
        adCopy.addEventListener('input', (e) => {
            const countEl = document.getElementById('adCopyCount');
            if (countEl) {
                countEl.textContent = `${e.target.value.length} chars`;
            }
        });
    }

    if (videoScript) {
        videoScript.addEventListener('input', (e) => {
            const countEl = document.getElementById('videoScriptCount');
            if (countEl) {
                const words = e.target.value.trim().split(/\s+/).filter(w => w.length > 0).length;
                const readTime = Math.ceil(words / 3);
                countEl.textContent = `${words} words (~${readTime}s read)`;
            }
        });
    }
}

// Load audience configuration from backend
async function loadAudienceConfig() {
    try {
        console.log('Loading audience config...');
        const response = await fetch(`${API_BASE_URL}/audience-config`);
        if (!response.ok) throw new Error('Failed to load audience config');
        audienceConfig = await response.json();
        console.log('Audience config loaded:', audienceConfig);
        populateAudienceFields();
    } catch (error) {
        console.error('Error loading audience config:', error);
        populateBasicAudienceOptions();
    }
}

// Populate all audience dropdowns
function populateAudienceFields() {
    if (!audienceConfig) {
        console.warn('No audience config available');
        return;
    }

    console.log('Populating audience fields...');

    // Country select
    const countrySelect = document.getElementById('audienceCountry');
    if (countrySelect && audienceConfig.countries) {
        console.log('Populating countries:', audienceConfig.countries.length);
        countrySelect.innerHTML = '<option value="">Select Country</option>';
        audienceConfig.countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.code;
            option.textContent = `${country.name} (${country.currency})`;
            option.dataset.regions = JSON.stringify(country.regions || []);
            option.dataset.currency = country.currency;
            countrySelect.appendChild(option);
        });
    }

    // Age select
    const ageSelect = document.getElementById('audienceAge');
    if (ageSelect && audienceConfig.age_brackets) {
        ageSelect.innerHTML = '<option value="">Select Age</option>';
        audienceConfig.age_brackets.forEach(age => {
            const option = document.createElement('option');
            option.value = age.value;
            option.textContent = age.label;
            option.dataset.traits = age.traits;
            ageSelect.appendChild(option);
        });
    }

    // Income select
    const incomeSelect = document.getElementById('audienceIncome');
    if (incomeSelect && audienceConfig.income_levels) {
        incomeSelect.innerHTML = '<option value="">Select Income</option>';
        audienceConfig.income_levels.forEach(income => {
            const option = document.createElement('option');
            option.value = income.value;
            option.textContent = income.label;
            option.dataset.description = income.description;
            incomeSelect.appendChild(option);
        });
    }

    // Education select
    const eduSelect = document.getElementById('audienceEducation');
    if (eduSelect && audienceConfig.education_levels) {
        eduSelect.innerHTML = '<option value="">Select Education</option>';
        audienceConfig.education_levels.forEach(edu => {
            const option = document.createElement('option');
            option.value = edu.value;
            option.textContent = edu.label;
            eduSelect.appendChild(option);
        });
    }

    // Occupation select
    const occSelect = document.getElementById('audienceOccupation');
    if (occSelect && audienceConfig.occupations) {
        occSelect.innerHTML = '<option value="">Select Occupation</option>';
        audienceConfig.occupations.forEach(occ => {
            const option = document.createElement('option');
            option.value = occ.value;
            option.textContent = occ.label;
            option.dataset.painPoints = occ.pain_points;
            occSelect.appendChild(option);
        });
    }

    // Psychographic select
    const psychSelect = document.getElementById('audiencePsychographic');
    if (psychSelect && audienceConfig.psychographics) {
        psychSelect.innerHTML = '<option value="">Select Psychographic</option>';
        audienceConfig.psychographics.forEach(psych => {
            const option = document.createElement('option');
            option.value = psych.value;
            option.textContent = psych.label;
            option.dataset.traits = psych.traits;
            psychSelect.appendChild(option);
        });
    }

    // Pain point select
    const painSelect = document.getElementById('audiencePainPoint');
    if (painSelect && audienceConfig.pain_points) {
        painSelect.innerHTML = '<option value="">Select Pain Point</option>';
        audienceConfig.pain_points.forEach(pain => {
            const option = document.createElement('option');
            option.value = pain.value;
            option.textContent = pain.label;
            option.dataset.description = pain.description;
            painSelect.appendChild(option);
        });
    }

    console.log('Audience fields populated');
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
        countrySelect.innerHTML = '<option value="">Select Country</option>';
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
        console.log('Loading platforms...');
        const response = await fetch(`${API_BASE_URL}/platforms`);
        if (!response.ok) return;
        const data = await response.json();
        const select = document.getElementById('platform');
        if (!select) return;

        select.innerHTML = '<option value="">Select Platform</option>';
        data.platforms.forEach(p => {
            const option = document.createElement('option');
            option.value = p.id;
            option.textContent = p.name;
            select.appendChild(option);
        });
        console.log('Platforms loaded:', data.platforms.length);
    } catch (error) {
        console.error('Error loading platforms:', error);
    }
}

// Load industries
async function loadIndustries() {
    try {
        console.log('Loading industries...');
        const response = await fetch(`${API_BASE_URL}/industries`);
        if (!response.ok) return;
        const data = await response.json();
        const select = document.getElementById('industry');
        if (!select) return;

        select.innerHTML = '<option value="">Select Industry</option>';
        data.industries.forEach(i => {
            const option = document.createElement('option');
            option.value = i.id;
            option.textContent = i.name;
            select.appendChild(option);
        });
        console.log('Industries loaded:', data.industries.length);
    } catch (error) {
        console.error('Error loading industries:', error);
    }
}

// Setup event listeners - FIXED VERSION
function setupEventListeners() {
    console.log('Setting up event listeners...');

    // Country → Region dependency
    const countrySelect = document.getElementById('audienceCountry');
    const regionSelect = document.getElementById('audienceRegion');

    if (countrySelect) {
        console.log('Adding change listener to country select');
        countrySelect.addEventListener('change', (e) => {
            console.log('Country changed to:', e.target.value);
            const selected = e.target.selectedOptions[0];
            if (!selected || !regionSelect) return;

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

    // Age traits display
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

    // Occupation pain points display
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

    // File uploads
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

    // Form submission
    if (form) {
        console.log('Adding submit listener to form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            console.log('Form submitted');
            await handleSubmit(selectedImage, selectedVideo);
        });
    } else {
        console.error('Form element not found!');
    }

    console.log('Event listeners setup complete');
}

function updateFilePreview(file, type) {
    if (!filePreview) return;
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

    console.log('Submitting with values:', { platform, country, age, industry, hasAdCopy: !!adCopy, hasVideoScript: !!videoScript });

    // Validation
    if (!adCopy && !videoScript) { 
        alert('Please enter ad copy or video script'); 
        return; 
    }
    if (!platform) { 
        alert('Please select platform'); 
        return; 
    }
    if (!country) { 
        alert('Please select country'); 
        return; 
    }
    if (!age) { 
        alert('Please select age bracket'); 
        return; 
    }
    if (!industry) { 
        alert('Please select industry'); 
        return; 
    }

    // Show loading
    if (emptyState) emptyState.classList.add('hidden');
    if (resultsContent) resultsContent.classList.add('hidden');
    if (loadingState) loadingState.classList.remove('hidden');
    if (analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Analyzing...';
    }

    try {
        const formData = new FormData();

        if (adCopy) formData.append('ad_copy', adCopy);
        if (videoScript) formData.append('video_script', videoScript);
        formData.append('platform', platform);
        formData.append('audience_country', country);
        formData.append('audience_age', age);
        formData.append('industry', industry);
        formData.append('objective', document.getElementById('objective')?.value || 'conversions');

        // Optional fields
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

        console.log('📤 Sending request...');

        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            body: formData
        });

        console.log('📥 Response status:', response.status);

        const data = await response.json();

        if (data.success && data.analysis) {
            console.log('✅ Analysis successful');
            renderResults(data);
        } else {
            throw new Error(data.error || 'Analysis returned unsuccessful');
        }
    } catch (error) {
        console.error('💥 Analysis error:', error);
        alert(`Error: ${error.message}`);
        if (emptyState) emptyState.classList.remove('hidden');
    } finally {
        if (loadingState) loadingState.classList.add('hidden');
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Ad →';
        }
    }
}

// Render results function (simplified for this fix)
function renderResults(data) {
    console.log('Rendering results:', data);
    if (resultsContent) {
        resultsContent.classList.remove('hidden');
    }
    // Full render logic would go here...
}

console.log('ADLYTICS v4.1 FIXED SELECTS loaded');
