/**
 * ADLYTICS - Analyzer JavaScript v4.1 FIXED VIDEO SCRIPT
 * Properly captures content from all tabs
 */

const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api' 
    : '/api';

// Global audience config
let audienceConfig = null;
let currentContentMode = 'adCopy';

// DOM Elements
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

    await loadAudienceConfig();
    await loadPlatforms();
    await loadIndustries();
    setupEventListeners();
    setupContentTabs();
    setupTextareaCounters();

    console.log('✅ ADLYTICS v4.1 Initialized');
});

// Setup content type tabs - FIXED
function setupContentTabs() {
    const tabs = document.querySelectorAll('.content-tab');
    console.log('Setting up content tabs:', tabs.length, 'tabs found');

    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            console.log('Content tab clicked:', tab.dataset.target);

            // Remove active from all tabs
            tabs.forEach(t => t.classList.remove('active'));
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

// Setup textarea counters
function setupTextareaCounters() {
    const adCopy = document.getElementById('adCopy');
    const videoScript = document.getElementById('videoScript');
    const adCopyBoth = document.getElementById('adCopyBoth');
    const videoScriptBoth = document.getElementById('videoScriptBoth');

    if (adCopy) {
        adCopy.addEventListener('input', (e) => {
            const countEl = document.getElementById('adCopyCount');
            if (countEl) countEl.textContent = `${e.target.value.length} chars`;
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

    if (adCopyBoth) {
        adCopyBoth.addEventListener('input', (e) => {
            const countEl = document.getElementById('adCopyBothCount');
            if (countEl) countEl.textContent = `${e.target.value.length} chars`;
        });
    }

    if (videoScriptBoth) {
        videoScriptBoth.addEventListener('input', (e) => {
            const countEl = document.getElementById('videoScriptBothCount');
            if (countEl) {
                const words = e.target.value.trim().split(/\s+/).filter(w => w.length > 0).length;
                const readTime = Math.ceil(words / 3);
                countEl.textContent = `${words} words (~${readTime}s read)`;
            }
        });
    }
}

// FIXED: Get content values based on current mode
function getContentValues() {
    let adCopy = '';
    let videoScript = '';

    console.log('Getting content values for mode:', currentContentMode);

    if (currentContentMode === 'adCopy') {
        const adCopyEl = document.getElementById('adCopy');
        adCopy = adCopyEl?.value?.trim() || '';
        console.log('Ad Copy mode - value:', adCopy.substring(0, 50));
    } 
    else if (currentContentMode === 'videoScript') {
        const videoScriptEl = document.getElementById('videoScript');
        videoScript = videoScriptEl?.value?.trim() || '';
        console.log('Video Script mode - value:', videoScript.substring(0, 50));
    } 
    else if (currentContentMode === 'both') {
        const adCopyBothEl = document.getElementById('adCopyBoth');
        const videoScriptBothEl = document.getElementById('videoScriptBoth');
        adCopy = adCopyBothEl?.value?.trim() || '';
        videoScript = videoScriptBothEl?.value?.trim() || '';
        console.log('Both mode - adCopy:', adCopy.substring(0, 50), 'videoScript:', videoScript.substring(0, 50));
    }

    return { adCopy, videoScript };
}

// Load audience config
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

// Populate audience fields
function populateAudienceFields() {
    if (!audienceConfig) return;

    const countrySelect = document.getElementById('audienceCountry');
    if (countrySelect && audienceConfig.countries) {
        countrySelect.innerHTML = '<option value="">Select Country</option>';
        audienceConfig.countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.code;
            option.textContent = `${country.name} (${country.currency})`;
            option.dataset.regions = JSON.stringify(country.regions || []);
            countrySelect.appendChild(option);
        });
    }

    const ageSelect = document.getElementById('audienceAge');
    if (ageSelect && audienceConfig.age_brackets) {
        ageSelect.innerHTML = '<option value="">Select Age</option>';
        audienceConfig.age_brackets.forEach(age => {
            const option = document.createElement('option');
            option.value = age.value;
            option.textContent = age.label;
            ageSelect.appendChild(option);
        });
    }
}

// Fallback audience options
function populateBasicAudienceOptions() {
    const countrySelect = document.getElementById('audienceCountry');
    if (countrySelect) {
        countrySelect.innerHTML = '<option value="">Select Country</option>';
        ['nigeria', 'us', 'uk'].forEach(code => {
            const option = document.createElement('option');
            option.value = code;
            option.textContent = code.toUpperCase();
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
        if (select) {
            select.innerHTML = '<option value="">Select Platform</option>';
            data.platforms.forEach(p => {
                const option = document.createElement('option');
                option.value = p.id;
                option.textContent = p.name;
                select.appendChild(option);
            });
        }
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
        if (select) {
            select.innerHTML = '<option value="">Select Industry</option>';
            data.industries.forEach(i => {
                const option = document.createElement('option');
                option.value = i.id;
                option.textContent = i.name;
                select.appendChild(option);
            });
        }
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
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await handleSubmit(selectedImage, selectedVideo);
        });
    }
}

function updateFilePreview(file, type) {
    if (!filePreview) return;
    const icon = type === 'image' ? '📷' : '🎥';
    filePreview.textContent = `${icon} ${file.name} (${(file.size/1024/1024).toFixed(2)}MB)`;
    filePreview.classList.remove('hidden');
}

// FIXED handleSubmit with better validation
async function handleSubmit(selectedImage, selectedVideo) {
    const { adCopy, videoScript } = getContentValues();
    const platform = document.getElementById('platform')?.value;
    const country = document.getElementById('audienceCountry')?.value;
    const age = document.getElementById('audienceAge')?.value;
    const industry = document.getElementById('industry')?.value;

    console.log('Submitting:', { 
        currentContentMode, 
        adCopy: adCopy.substring(0, 50), 
        videoScript: videoScript.substring(0, 50),
        platform, country, age, industry 
    });

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

        // FIXED: Only append if has value
        if (adCopy) formData.append('ad_copy', adCopy);
        if (videoScript) formData.append('video_script', videoScript);

        formData.append('platform', platform);
        formData.append('audience_country', country);
        formData.append('audience_age', age);
        formData.append('industry', industry);
        formData.append('objective', document.getElementById('objective')?.value || 'conversions');

        // Optional fields
        const region = document.getElementById('audienceRegion')?.value;
        if (region) formData.append('audience_region', region);

        if (selectedImage) formData.append('image', selectedImage);
        if (selectedVideo) formData.append('video', selectedVideo);

        console.log('📤 Sending request with FormData...');

        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            body: formData
        });

        console.log('📥 Response status:', response.status);

        const data = await response.json();
        console.log('📥 Response data:', data);

        if (data.success && data.analysis) {
            console.log('✅ Analysis successful');
            renderResults(data);
        } else {
            console.error('❌ Analysis failed:', data.error, data.detail);
            throw new Error(data.error || data.detail || 'Analysis returned unsuccessful');
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

function renderResults(data) {
    console.log('Rendering results:', data);
    if (resultsContent) {
        resultsContent.classList.remove('hidden');
    }
}

console.log('ADLYTICS v4.1 FIXED VIDEO SCRIPT loaded');
