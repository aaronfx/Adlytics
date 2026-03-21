/**
 * ADLYTICS - Analyzer JavaScript v4.1 DEBUG VERSION
 * Enhanced error logging to diagnose 500 errors
 */

const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api' 
    : '/api';

// ... (keep all existing code until handleSubmit) ...

async function handleSubmit(selectedImage, selectedVideo) {
    const { adCopy, videoScript } = getContentValues();
    const platform = document.getElementById('platform')?.value;
    const country = document.getElementById('audienceCountry')?.value;
    const age = document.getElementById('audienceAge')?.value;
    const industry = document.getElementById('industry')?.value;

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

        console.log('📤 Sending request to:', `${API_BASE_URL}/analyze`);
        console.log('📤 FormData contents:');
        for (let [key, value] of formData.entries()) {
            console.log(`  ${key}: ${value}`);
        }

        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            body: formData
        });

        console.log('📥 Response status:', response.status);
        console.log('📥 Response headers:', Object.fromEntries(response.headers.entries()));

        const responseText = await response.text();
        console.log('📥 Raw response:', responseText);

        let data;
        try {
            data = JSON.parse(responseText);
        } catch (e) {
            console.error('❌ Failed to parse JSON:', e);
            throw new Error(`Server returned invalid JSON: ${responseText.substring(0, 200)}`);
        }

        if (!response.ok) {
            console.error('❌ HTTP Error:', response.status, data);
            throw new Error(data.detail || data.error || `HTTP ${response.status}: ${responseText}`);
        }

        if (data.success && data.analysis) {
            console.log('✅ Analysis successful:', data);
            renderResults(data);
        } else {
            console.error('❌ Analysis returned unsuccessful:', data);
            throw new Error(data.error || 'Analysis returned unsuccessful');
        }
    } catch (error) {
        console.error('💥 Analysis error:', error);
        console.error('💥 Error stack:', error.stack);
        alert(`Error: ${error.message}`);
        emptyState.classList.remove('hidden');
    } finally {
        loadingState.classList.add('hidden');
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze Ad →';
    }
}

// ... (rest of existing code) ...

console.log('ADLYTICS v4.1 DEBUG Analyzer loaded - Enhanced error logging enabled');
