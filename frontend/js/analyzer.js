/**
 * ADLYTICS Analyzer v5.0 - Frontend Controller
 * Handles all v5 features and region dropdown population
 */

class AdAnalyzer {
    constructor() {
        this.currentAnalysis = null;
        this.audienceConfig = null;
        this.init();
    }

    init() {
        this.cacheElements();
        this.bindEvents();
        this.loadAudienceConfig();
        console.log('✅ ADLYTICS v5.0 Analyzer Initialized');
    }

    cacheElements() {
        // Form elements
        this.elements = {
            form: document.getElementById('analyzerForm'),
            adCopy: document.getElementById('adCopy'),
            videoScript: document.getElementById('videoScript'),
            platform: document.getElementById('platform'),
            industry: document.getElementById('industry'),
            country: document.getElementById('audienceCountry'),
            region: document.getElementById('audienceRegion'),
            age: document.getElementById('audienceAge'),
            income: document.getElementById('audienceIncome'),
            occupation: document.getElementById('audienceOccupation'),
            submitBtn: document.getElementById('analyzeBtn'),
            loading: document.getElementById('loading'),
            results: document.getElementById('results'),
            errorDisplay: document.getElementById('errorDisplay')
        };
    }

    bindEvents() {
        if (this.elements.form) {
            this.elements.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Country change updates regions
        if (this.elements.country) {
            this.elements.country.addEventListener('change', () => this.updateRegions());
        }
    }

    // Load audience configuration including countries and regions
    async loadAudienceConfig() {
        // Default configuration (fallback if API fails)
        this.audienceConfig = {
            countries: [
                { code: "nigeria", name: "Nigeria", regions: ["Lagos", "Abuja", "Kano", "Ibadan", "Port Harcourt"] },
                { code: "us", name: "United States", regions: ["California", "Texas", "New York", "Florida", "Illinois"] },
                { code: "uk", name: "United Kingdom", regions: ["London", "Manchester", "Birmingham"] },
                { code: "canada", name: "Canada", regions: ["Ontario", "Quebec", "British Columbia"] },
                { code: "ghana", name: "Ghana", regions: ["Accra", "Kumasi", "Tamale"] },
                { code: "kenya", name: "Kenya", regions: ["Nairobi", "Mombasa", "Kisumu"] },
                { code: "south_africa", name: "South Africa", regions: ["Gauteng", "Western Cape", "KwaZulu-Natal"] },
                { code: "india", name: "India", regions: ["Maharashtra", "Karnataka", "Delhi"] },
                { code: "australia", name: "Australia", regions: ["New South Wales", "Victoria", "Queensland"] },
                { code: "germany", name: "Germany", regions: ["Bavaria", "North Rhine-Westphalia", "Baden-Württemberg"] }
            ]
        };

        // Try to load from API
        try {
            const response = await fetch('/api/audience-config');
            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data) {
                    this.audienceConfig = result.data;
                    console.log('✅ Audience config loaded from API');
                }
            }
        } catch (error) {
            console.log('Using default audience config');
        }

        // Populate country dropdown
        this.populateCountryDropdown();
    }

    populateCountryDropdown() {
        if (!this.elements.country || !this.audienceConfig) return;

        const countries = this.audienceConfig.countries || [];
        this.elements.country.innerHTML = countries
            .map(c => `<option value="${c.code}">${c.name}</option>`)
            .join('');

        // Trigger initial region update
        this.updateRegions();
    }

    // Update regions based on selected country
    updateRegions() {
        const countryCode = this.elements.country?.value;
        const regionSelect = this.elements.region;

        if (!countryCode || !regionSelect || !this.audienceConfig) {
            console.log('Cannot update regions: missing elements');
            return;
        }

        const country = this.audienceConfig.countries.find(c => c.code === countryCode);

        if (country && country.regions && country.regions.length > 0) {
            // Populate regions
            regionSelect.innerHTML = `
                <option value="">Select Region</option>
                ${country.regions.map(r => `<option value="${r.toLowerCase().replace(/\s+/g, '-')}">${r}</option>`).join('')}
            `;
            regionSelect.disabled = false;
            console.log(`✅ Populated ${country.regions.length} regions for ${country.name}`);
        } else {
            // No regions available
            regionSelect.innerHTML = '<option value="">No regions available</option>';
            regionSelect.disabled = true;
            console.log(`No regions for ${countryCode}`);
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        this.showLoading();
        this.hideError();

        const formData = new FormData();

        // Add content
        const adCopy = this.elements.adCopy?.value || '';
        const videoScript = this.elements.videoScript?.value || '';

        if (!adCopy.trim() && !videoScript.trim()) {
            this.showError('Please provide either ad copy or a video script');
            this.hideLoading();
            return;
        }

        formData.append('ad_copy', adCopy);
        formData.append('video_script', videoScript);
        formData.append('platform', this.elements.platform?.value || 'tiktok');
        formData.append('industry', this.elements.industry?.value || 'saas');

        // Add audience targeting
        if (this.elements.country) formData.append('audience_country', this.elements.country.value);
        if (this.elements.region) formData.append('audience_region', this.elements.region.value);
        if (this.elements.age) formData.append('audience_age', this.elements.age.value);
        if (this.elements.income) formData.append('audience_income', this.elements.income.value);
        if (this.elements.occupation) formData.append('audience_occupation', this.elements.occupation.value);

        try {
            console.log('📤 Submitting analysis...');

            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                throw new Error(result.error?.message || `HTTP ${response.status}: Analysis failed`);
            }

            console.log('✅ Analysis received:', result.data);
            this.currentAnalysis = result.data;
            this.renderResults(result.data);

        } catch (error) {
            console.error('❌ Analysis error:', error);
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }

    renderResults(data) {
        this.elements.results?.classList.remove('hidden');

        // Render all sections
        this.renderScores(data.scores);
        this.renderDecisionEngine(data.decision_engine);
        this.renderBudgetOptimization(data.budget_optimization);
        this.renderNeuroResponse(data.neuro_response);
        this.renderCreativeFatigue(data.creative_fatigue);
        this.renderObjectionDetection(data.objection_detection);
        this.renderAdVariants(data.ad_variants, data.winner_prediction);
        this.renderCrossPlatform(data.cross_platform);
        this.renderBehaviorSummary(data.behavior_summary);
        this.renderPhaseBreakdown(data.phase_breakdown);
        this.renderPersonaReactions(data.persona_reactions);
        this.renderImprovements(data.improvements, data.improved_ad);
        this.renderVideoExecution(data.video_execution_analysis);
        this.renderCriticalWeaknesses(data.critical_weaknesses);

        this.switchTab('overview');
    }

    renderScores(scores) {
        if (!scores) return;
        const container = document.getElementById('scoresContainer');
        if (!container) return;

        container.innerHTML = Object.entries(scores).map(([key, value]) => `
            <div class="score-card ${this.getScoreColor(value)}">
                <div class="score-value">${value}</div>
                <div class="score-label">${key.replace(/_/g, ' ').toUpperCase()}</div>
            </div>
        `).join('');
    }

    getScoreColor(score) {
        if (score >= 81) return 'excellent';
        if (score >= 61) return 'good';
        if (score >= 41) return 'average';
        if (score >= 21) return 'poor';
        return 'critical';
    }

    renderDecisionEngine(decision) {
        const container = document.getElementById('decisionEngine');
        if (!container || !decision) return;

        container.innerHTML = `
            <div class="decision-card ${decision.should_run ? 'success' : 'danger'}">
                <h3>${decision.should_run ? '✅ RECOMMENDED TO RUN' : '❌ DO NOT RUN'}</h3>
                <p>Confidence: ${decision.confidence || 'N/A'}</p>
                <p>Expected Profit: $${decision.expected_profit || 0}</p>
                <p>Recommended Budget: $${decision.recommended_budget || 0}</p>
            </div>
        `;
    }

    renderBudgetOptimization(budget) {
        const container = document.getElementById('budgetOptimization');
        if (!container || !budget) return;

        container.innerHTML = `
            <div class="budget-grid">
                <div class="budget-card">
                    <h4>Break-Even CPC</h4>
                    <div class="budget-value">$${budget.break_even_cpc?.toFixed(2) || 'N/A'}</div>
                </div>
                <div class="budget-card">
                    <h4>Safe Test Budget</h4>
                    <div class="budget-value">$${budget.safe_test_budget || 'N/A'}</div>
                </div>
                <div class="budget-card">
                    <h4>Expected CPA</h4>
                    <div class="budget-value">$${budget.expected_cpa?.toFixed(2) || 'N/A'}</div>
                </div>
            </div>
            <p><strong>Scaling Rule:</strong> ${budget.scaling_rule || 'N/A'}</p>
        `;
    }

    renderNeuroResponse(neuro) {
        const container = document.getElementById('neuroResponse');
        if (!container || !neuro) return;

        container.innerHTML = `
            <div class="neuro-container">
                <h4>Primary Driver: ${neuro.primary_driver?.toUpperCase()}</h4>
                ${Object.entries(neuro).filter(([k]) => k !== 'primary_driver').map(([key, value]) => `
                    <div class="neuro-item">
                        <label>${key}</label>
                        <div class="neuro-bar-container">
                            <div class="neuro-bar" style="width: ${value}%"></div>
                            <span>${value}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderCreativeFatigue(fatigue) {
        const container = document.getElementById('creativeFatigue');
        if (!container || !fatigue) return;

        container.innerHTML = `
            <div class="fatigue-card ${fatigue.fatigue_level?.toLowerCase().replace(/\s+/g, '-')}">
                <h4>Fatigue Level: ${fatigue.fatigue_level || 'N/A'}</h4>
                <p>Estimated Decline: ${fatigue.estimated_decline_time || 'N/A'}</p>
                <p>${fatigue.refresh_needed ? '⚠️ Refresh needed' : '✅ No refresh needed'}</p>
            </div>
        `;
    }

    renderObjectionDetection(objections) {
        const container = document.getElementById('objectionDetection');
        if (!container || !objections) return;

        const sections = [
            { key: 'scam_triggers', title: '🚨 Scam Triggers' },
            { key: 'trust_gaps', title: '🛡️ Trust Gaps' },
            { key: 'unrealistic_claims', title: '📢 Unrealistic Claims' },
            { key: 'compliance_risks', title: '⚖️ Compliance Risks' }
        ];

        container.innerHTML = sections.map(section => {
            const items = objections[section.key] || [];
            return `
                <div class="objection-section">
                    <h4>${section.title}</h4>
                    ${items.length > 0 ? `<ul>${items.map(item => `<li>${item}</li>`).join('')}</ul>` : '<p>✅ No issues</p>'}
                </div>
            `;
        }).join('');
    }

    renderAdVariants(variants, winner) {
        const container = document.getElementById('adVariants');
        if (!container || !variants) return;

        container.innerHTML = `
            <div class="winner-prediction">
                <h4>🏆 Predicted Winner: Variant #${winner?.best_variant_id || 'N/A'}</h4>
            </div>
            <div class="variants-grid">
                ${variants.map(variant => `
                    <div class="variant-card ${winner?.best_variant_id === variant.id ? 'winner' : ''}">
                        <h5>Variant #${variant.id} - ${variant.angle}</h5>
                        <p>Score: ${variant.predicted_score}</p>
                        <p>${variant.hook}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderCrossPlatform(cross) {
        const container = document.getElementById('crossPlatform');
        if (!container || !cross) return;

        container.innerHTML = Object.entries(cross).map(([platform, data]) => `
            <div class="platform-card">
                <h4>${platform.toUpperCase()} - Score: ${data.score}</h4>
                <blockquote>${data.adapted_copy}</blockquote>
                <p>${data.changes}</p>
            </div>
        `).join('');
    }

    renderBehaviorSummary(summary) {
        const container = document.getElementById('behaviorSummary');
        if (!container || !summary) return;

        container.innerHTML = `
            <div class="behavior-card">
                <h3>${summary.verdict || 'N/A'}</h3>
                <p>Launch Readiness: ${summary.launch_readiness || 'N/A'}</p>
                <p>Failure Risk: ${summary.failure_risk || 'N/A'}</p>
                <p>${summary.primary_reason || ''}</p>
            </div>
        `;
    }

    renderPhaseBreakdown(phases) {
        const container = document.getElementById('phaseBreakdown');
        if (!container || !phases) return;

        container.innerHTML = Object.entries(phases).map(([phase, description]) => `
            <div class="phase-item">
                <h5>${phase.replace(/_/g, ' ').toUpperCase()}</h5>
                <p>${description}</p>
            </div>
        `).join('');
    }

    renderPersonaReactions(personas) {
        const container = document.getElementById('personaReactions');
        if (!container || !personas) return;

        container.innerHTML = personas.map(persona => `
            <div class="persona-card">
                <h5>${persona.persona}</h5>
                <p>Reaction: ${persona.reaction}</p>
                <p>Objection: "${persona.objection}"</p>
                <p>Behavior: ${persona.behavior}</p>
                <p>Likelihood: ${(persona.likelihood_to_convert * 100).toFixed(0)}%</p>
            </div>
        `).join('');
    }

    renderImprovements(improvements, improvedAd) {
        const container = document.getElementById('improvements');
        if (!container) return;

        let html = '';
        if (improvements) {
            html += `<div class="improvements-list"><h4>Improvements</h4><ul>${improvements.map(i => `<li>${i}</li>`).join('')}</ul></div>`;
        }
        if (improvedAd) {
            html += `
                <div class="improved-ad">
                    <h4>AI-Optimized Version</h4>
                    <div class="improved-headline">${improvedAd.headline}</div>
                    <div class="improved-body">${improvedAd.body_copy}</div>
                    <div class="improved-cta">${improvedAd.cta}</div>
                    <p>Predicted Score: ${improvedAd.predicted_score}</p>
                </div>
            `;
        }
        container.innerHTML = html;
    }

    renderVideoExecution(video) {
        const container = document.getElementById('videoExecution');
        if (!container || !video || video.is_video_script === 'No') return;

        container.innerHTML = `
            <div class="video-analysis">
                <h4>Video Script Analysis</h4>
                <p>Hook Delivery: ${video.hook_delivery_strength}</p>
                <p>Speech Flow: ${video.speech_flow_quality}</p>
                <p>Visual Dependency: ${video.visual_dependency}</p>
                <p>Delivery Risk: ${video.delivery_risk}</p>
                <p>Recommended Format: ${video.recommended_format}</p>
            </div>
        `;
    }

    renderCriticalWeaknesses(weaknesses) {
        const container = document.getElementById('criticalWeaknesses');
        if (!container || !weaknesses) return;

        container.innerHTML = weaknesses.map(w => `
            <div class="weakness-card severity-${w.severity}">
                <span class="severity-badge">${w.severity}</span>
                <h5>${w.issue}</h5>
                <p>${w.behavior_impact}</p>
                <p><strong>Fix:</strong> ${w.precise_fix}</p>
            </div>
        `).join('');
    }

    switchTab(tabName) {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `tab-${tabName}`);
        });
    }

    showLoading() {
        this.elements.loading?.classList.remove('hidden');
        this.elements.submitBtn?.setAttribute('disabled', 'true');
    }

    hideLoading() {
        this.elements.loading?.classList.add('hidden');
        this.elements.submitBtn?.removeAttribute('disabled');
    }

    showError(message) {
        if (this.elements.errorDisplay) {
            this.elements.errorDisplay.textContent = message;
            this.elements.errorDisplay.classList.remove('hidden');
        }
    }

    hideError() {
        this.elements.errorDisplay?.classList.add('hidden');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    window.adAnalyzer = new AdAnalyzer();
});
