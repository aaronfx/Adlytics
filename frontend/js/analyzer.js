/**
 * ADLYTICS Analyzer v5.0 - PRODUCTION GRADE
 * Bulletproof implementation with comprehensive error handling
 */

class AdAnalyzer {
    constructor() {
        this.currentAnalysis = null;
        this.audienceConfig = null;
        this.apiBaseUrl = window.location.origin; // ISSUE 6 FIX: Flexible API URL
        this.requestTimeout = 60000; // ISSUE 7 FIX: 60 second timeout
        this.init();
    }

    init() {
        this.cacheElements();
        this.bindEvents();
        this.loadAudienceConfig();
        console.log('✅ ADLYTICS v5.0 Production Analyzer Initialized');
    }

    cacheElements() {
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

        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        if (this.elements.country) {
            this.elements.country.addEventListener('change', () => this.updateRegions());
        }
    }

    // ISSUE 3 FIX: Response normalization - ensures all fields exist
    normalizeResponse(data) {
        if (!data || typeof data !== 'object') {
            console.error('Invalid data received:', data);
            return this.getDefaultResponse();
        }

        return {
            // Core scores with defaults
            scores: {
                overall: data.scores?.overall ?? 0,
                hook_strength: data.scores?.hook_strength ?? 0,
                clarity: data.scores?.clarity ?? 0,
                trust_building: data.scores?.trust_building ?? 0,
                cta_power: data.scores?.cta_power ?? 0,
                audience_alignment: data.scores?.audience_alignment ?? 0,
                ...data.scores
            },

            // V5 features with safe defaults
            decision_engine: {
                should_run: data.decision_engine?.should_run ?? false,
                confidence: data.decision_engine?.confidence ?? '0%',
                expected_profit: data.decision_engine?.expected_profit ?? 0,
                recommended_budget: data.decision_engine?.recommended_budget ?? 0,
                kill_threshold: data.decision_engine?.kill_threshold ?? 'N/A',
                go_threshold: data.decision_engine?.go_threshold ?? 'N/A',
                ...data.decision_engine
            },

            budget_optimization: {
                break_even_cpc: data.budget_optimization?.break_even_cpc ?? 0,
                safe_test_budget: data.budget_optimization?.safe_test_budget ?? 0,
                scaling_rule: data.budget_optimization?.scaling_rule ?? 'N/A',
                daily_budget_cap: data.budget_optimization?.daily_budget_cap ?? 0,
                expected_cpa: data.budget_optimization?.expected_cpa ?? 0,
                ...data.budget_optimization
            },

            neuro_response: {
                dopamine: data.neuro_response?.dopamine ?? 0,
                fear: data.neuro_response?.fear ?? 0,
                curiosity: data.neuro_response?.curiosity ?? 0,
                urgency: data.neuro_response?.urgency ?? 0,
                trust: data.neuro_response?.trust ?? 0,
                primary_driver: data.neuro_response?.primary_driver ?? 'unknown',
                ...data.neuro_response
            },

            creative_fatigue: {
                fatigue_level: data.creative_fatigue?.fatigue_level ?? 'Unknown',
                estimated_decline_time: data.creative_fatigue?.estimated_decline_time ?? 'N/A',
                refresh_needed: data.creative_fatigue?.refresh_needed ?? false,
                variation_recommendation: data.creative_fatigue?.variation_recommendation ?? 'N/A',
                ...data.creative_fatigue
            },

            objection_detection: {
                scam_triggers: data.objection_detection?.scam_triggers ?? [],
                trust_gaps: data.objection_detection?.trust_gaps ?? [],
                unrealistic_claims: data.objection_detection?.unrealistic_claims ?? [],
                compliance_risks: data.objection_detection?.compliance_risks ?? [],
                ...data.objection_detection
            },

            ad_variants: Array.isArray(data.ad_variants) ? data.ad_variants : [],

            winner_prediction: {
                best_variant_id: data.winner_prediction?.best_variant_id ?? null,
                score: data.winner_prediction?.score ?? 0,
                confidence: data.winner_prediction?.confidence ?? 'low',
                reason: data.winner_prediction?.reason ?? 'N/A',
                ...data.winner_prediction
            },

            cross_platform: data.cross_platform ?? {},
            persona_reactions: Array.isArray(data.persona_reactions) ? data.persona_reactions : [],
            behavior_summary: data.behavior_summary ?? {},
            phase_breakdown: data.phase_breakdown ?? {},
            improvements: Array.isArray(data.improvements) ? data.improvements : [],
            improved_ad: data.improved_ad ?? null,
            video_execution_analysis: data.video_execution_analysis ?? null,
            critical_weaknesses: Array.isArray(data.critical_weaknesses) ? data.critical_weaknesses : [],

            // Preserve any other fields
            ...data
        };
    }

    getDefaultResponse() {
        return {
            scores: { overall: 0, hook_strength: 0, clarity: 0, trust_building: 0, cta_power: 0, audience_alignment: 0 },
            decision_engine: { should_run: false, confidence: '0%', expected_profit: 0, recommended_budget: 0 },
            budget_optimization: { break_even_cpc: 0, safe_test_budget: 0, expected_cpa: 0 },
            neuro_response: { dopamine: 0, fear: 0, curiosity: 0, urgency: 0, trust: 0, primary_driver: 'unknown' },
            creative_fatigue: { fatigue_level: 'Unknown', refresh_needed: false },
            objection_detection: { scam_triggers: [], trust_gaps: [] },
            ad_variants: [],
            winner_prediction: { best_variant_id: null, score: 0 },
            cross_platform: {},
            persona_reactions: [],
            improvements: [],
            critical_weaknesses: []
        };
    }

    async loadAudienceConfig() {
        // Default config with regions
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

        this.populateCountryDropdown();
    }

    populateCountryDropdown() {
        if (!this.elements.country || !this.audienceConfig) return;

        const countries = this.audienceConfig.countries || [];
        this.elements.country.innerHTML = countries
            .map(c => `<option value="${c.code}">${c.name}</option>`)
            .join('');

        this.updateRegions();
    }

    updateRegions() {
        const countryCode = this.elements.country?.value;
        const regionSelect = this.elements.region;

        if (!countryCode || !regionSelect || !this.audienceConfig) return;

        const country = this.audienceConfig.countries.find(c => c.code === countryCode);

        if (country && country.regions && country.regions.length > 0) {
            regionSelect.innerHTML = `
                <option value="">Select Region</option>
                ${country.regions.map(r => `<option value="${r.toLowerCase().replace(/\s+/g, '-')}">${r}</option>`).join('')}
            `;
            regionSelect.disabled = false;
        } else {
            regionSelect.innerHTML = '<option value="">No regions available</option>';
            regionSelect.disabled = true;
        }
    }

    // ISSUE 7 FIX: Timeout handling
    async handleSubmit(e) {
        e.preventDefault();

        this.showLoading();
        this.hideError();

        const formData = new FormData();

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

        if (this.elements.country) formData.append('audience_country', this.elements.country.value);
        if (this.elements.region) formData.append('audience_region', this.elements.region.value);
        if (this.elements.age) formData.append('audience_age', this.elements.age.value);
        if (this.elements.income) formData.append('audience_income', this.elements.income.value);
        if (this.elements.occupation) formData.append('audience_occupation', this.elements.occupation.value);

        // ISSUE 7 FIX: AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            controller.abort();
            console.error('Request timed out after 60 seconds');
        }, this.requestTimeout);

        try {
            console.log(`📤 Submitting to: ${this.apiBaseUrl}/api/analyze`);

            const response = await fetch(`${this.apiBaseUrl}/api/analyze`, {
                method: 'POST',
                body: formData,
                signal: controller.signal // ISSUE 7 FIX: Timeout signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.error?.message || errorMsg;
                } catch (e) {
                    // If can't parse JSON, use status text
                }
                throw new Error(errorMsg);
            }

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error?.message || 'Analysis failed');
            }

            // ISSUE 3 FIX: Normalize response before rendering
            this.currentAnalysis = this.normalizeResponse(result.data);
            console.log('✅ Analysis normalized:', this.currentAnalysis);

            this.renderResults(this.currentAnalysis);

        } catch (error) {
            if (error.name === 'AbortError') {
                this.showError('Request timed out. Please try again.');
                console.error('Request aborted due to timeout');
            } else {
                console.error('❌ Analysis error:', error);
                this.showError(error.message || 'An unexpected error occurred');
            }
        } finally {
            clearTimeout(timeoutId);
            this.hideLoading();
        }
    }

    renderResults(data) {
        this.elements.results?.classList.remove('hidden');

        // All render methods now receive normalized data
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

        const scoreItems = [
            { key: 'overall', label: 'Overall' },
            { key: 'hook_strength', label: 'Hook' },
            { key: 'clarity', label: 'Clarity' },
            { key: 'trust_building', label: 'Trust' },
            { key: 'cta_power', label: 'CTA' },
            { key: 'audience_alignment', label: 'Audience' }
        ];

        container.innerHTML = scoreItems.map(item => {
            const value = scores[item.key] ?? 0;
            return `
                <div class="score-card ${this.getScoreColor(value)}">
                    <div class="score-value">${value}</div>
                    <div class="score-label">${item.label}</div>
                </div>
            `;
        }).join('');
    }

    getScoreColor(score) {
        if (score >= 81) return 'excellent';
        if (score >= 61) return 'good';
        if (score >= 41) return 'average';
        if (score >= 21) return 'poor';
        return 'critical';
    }

    // ISSUE 2 FIX: Null-safe rendering with optional chaining and defaults
    renderDecisionEngine(decision) {
        const container = document.getElementById('decisionEngine');
        if (!container) return;

        // Safe access with defaults
        const shouldRun = decision?.should_run ?? false;
        const confidence = decision?.confidence ?? '0%';
        const expectedProfit = decision?.expected_profit ?? 0;
        const recommendedBudget = decision?.recommended_budget ?? 0;
        const killThreshold = decision?.kill_threshold ?? 'N/A';
        const goThreshold = decision?.go_threshold ?? 'N/A';

        container.innerHTML = `
            <div class="decision-card ${shouldRun ? 'success' : 'danger'}">
                <h3>${shouldRun ? '✅ RECOMMENDED TO RUN' : '❌ DO NOT RUN'}</h3>
                <p>Confidence: ${confidence}</p>
                <p>Expected Profit: ${this.formatCurrency(expectedProfit)}</p>
                <p>Recommended Budget: ${this.formatCurrency(recommendedBudget)}</p>
                <p>Kill Threshold: ${killThreshold}</p>
                <p>Go Threshold: ${goThreshold}</p>
            </div>
        `;
    }

    // ISSUE 2 FIX: Safe rendering
    renderBudgetOptimization(budget) {
        const container = document.getElementById('budgetOptimization');
        if (!container) return;

        const breakEvenCpc = budget?.break_even_cpc ?? 0;
        const safeTestBudget = budget?.safe_test_budget ?? 0;
        const expectedCpa = budget?.expected_cpa ?? 0;
        const scalingRule = budget?.scaling_rule ?? 'N/A';

        container.innerHTML = `
            <div class="budget-grid">
                <div class="budget-card">
                    <h4>Break-Even CPC</h4>
                    <div class="budget-value">${this.formatCurrency(breakEvenCpc)}</div>
                </div>
                <div class="budget-card">
                    <h4>Safe Test Budget</h4>
                    <div class="budget-value">${this.formatCurrency(safeTestBudget)}</div>
                </div>
                <div class="budget-card">
                    <h4>Expected CPA</h4>
                    <div class="budget-value">${this.formatCurrency(expectedCpa)}</div>
                </div>
            </div>
            <p><strong>Scaling Rule:</strong> ${scalingRule}</p>
        `;
    }

    renderNeuroResponse(neuro) {
        const container = document.getElementById('neuroResponse');
        if (!container || !neuro) return;

        const drivers = ['dopamine', 'fear', 'curiosity', 'urgency', 'trust'];
        const primaryDriver = neuro?.primary_driver ?? 'unknown';

        container.innerHTML = `
            <div class="neuro-container">
                <h4>Primary Driver: ${primaryDriver.toUpperCase()}</h4>
                ${drivers.map(driver => {
                    const value = neuro?.[driver] ?? 0;
                    return `
                        <div class="neuro-item">
                            <label>${driver}</label>
                            <div class="neuro-bar-container">
                                <div class="neuro-bar" style="width: ${value}%; background: ${this.getNeuroColor(driver, value)}"></div>
                                <span>${value}</span>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    getNeuroColor(driver, value) {
        if (driver === 'fear') return value > 70 ? '#ef4444' : value > 40 ? '#f59e0b' : '#10b981';
        if (driver === 'trust') return value > 70 ? '#10b981' : value > 40 ? '#f59e0b' : '#ef4444';
        return value > 70 ? '#8b5cf6' : value > 40 ? '#f59e0b' : '#6b7280';
    }

    renderCreativeFatigue(fatigue) {
        const container = document.getElementById('creativeFatigue');
        if (!container) return;

        const fatigueLevel = fatigue?.fatigue_level ?? 'Unknown';
        const declineTime = fatigue?.estimated_decline_time ?? 'N/A';
        const refreshNeeded = fatigue?.refresh_needed ?? false;

        container.innerHTML = `
            <div class="fatigue-card ${fatigueLevel.toLowerCase().replace(/\s+/g, '-')}">
                <h4>Fatigue Level: ${fatigueLevel}</h4>
                <p>Estimated Decline: ${declineTime}</p>
                <p>${refreshNeeded ? '⚠️ Refresh needed' : '✅ No refresh needed'}</p>
            </div>
        `;
    }

    renderObjectionDetection(objections) {
        const container = document.getElementById('objectionDetection');
        if (!container) return;

        const sections = [
            { key: 'scam_triggers', title: '🚨 Scam Triggers' },
            { key: 'trust_gaps', title: '🛡️ Trust Gaps' },
            { key: 'unrealistic_claims', title: '📢 Unrealistic Claims' },
            { key: 'compliance_risks', title: '⚖️ Compliance Risks' }
        ];

        container.innerHTML = sections.map(section => {
            const items = objections?.[section.key] ?? [];
            return `
                <div class="objection-section">
                    <h4>${section.title}</h4>
                    ${items.length > 0 ? `<ul>${items.map(item => `<li>${item}</li>`).join('')}</ul>` : '<p>✅ No issues detected</p>'}
                </div>
            `;
        }).join('');
    }

    renderAdVariants(variants, winner) {
        const container = document.getElementById('adVariants');
        if (!container) return;

        const safeVariants = Array.isArray(variants) ? variants : [];
        const bestVariantId = winner?.best_variant_id ?? null;

        container.innerHTML = `
            <div class="winner-prediction">
                <h4>🏆 Predicted Winner: Variant #${bestVariantId ?? 'N/A'}</h4>
            </div>
            <div class="variants-grid">
                ${safeVariants.map(variant => `
                    <div class="variant-card ${bestVariantId === variant?.id ? 'winner' : ''}">
                        <h5>Variant #${variant?.id} - ${variant?.angle}</h5>
                        <p>Score: ${variant?.predicted_score ?? 0}</p>
                        <p>${variant?.hook ?? 'N/A'}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderCrossPlatform(cross) {
        const container = document.getElementById('crossPlatform');
        if (!container) return;

        const platforms = cross ?? {};

        container.innerHTML = Object.entries(platforms).map(([platform, data]) => `
            <div class="platform-card">
                <h4>${platform.toUpperCase()} - Score: ${data?.score ?? 0}</h4>
                <blockquote>${data?.adapted_copy ?? 'N/A'}</blockquote>
                <p>${data?.changes ?? 'N/A'}</p>
            </div>
        `).join('');
    }

    renderBehaviorSummary(summary) {
        const container = document.getElementById('behaviorSummary');
        if (!container) return;

        container.innerHTML = `
            <div class="behavior-card">
                <h3>${summary?.verdict ?? 'N/A'}</h3>
                <p>Launch Readiness: ${summary?.launch_readiness ?? 'N/A'}</p>
                <p>Failure Risk: ${summary?.failure_risk ?? 'N/A'}</p>
                <p>${summary?.primary_reason ?? ''}</p>
            </div>
        `;
    }

    renderPhaseBreakdown(phases) {
        const container = document.getElementById('phaseBreakdown');
        if (!container) return;

        const phaseOrder = [
            'micro_stop_0_1s', 'scroll_stop_1_2s', 'attention_2_5s', 
            'trust_evaluation', 'click_and_post_click'
        ];

        container.innerHTML = phaseOrder.map(phase => `
            <div class="phase-item">
                <h5>${phase.replace(/_/g, ' ').toUpperCase()}</h5>
                <p>${phases?.[phase] ?? 'N/A'}</p>
            </div>
        `).join('');
    }

    renderPersonaReactions(personas) {
        const container = document.getElementById('personaReactions');
        if (!container) return;

        const safePersonas = Array.isArray(personas) ? personas : [];

        container.innerHTML = safePersonas.map(persona => `
            <div class="persona-card">
                <h5>${persona?.persona ?? 'Unknown'}</h5>
                <p>Reaction: ${persona?.reaction ?? 'N/A'}</p>
                <p>Objection: "${persona?.objection ?? 'N/A'}"</p>
                <p>Behavior: ${persona?.behavior ?? 'N/A'}</p>
                <p>Likelihood: ${((persona?.likelihood_to_convert ?? 0) * 100).toFixed(0)}%</p>
            </div>
        `).join('');
    }

    renderImprovements(improvements, improvedAd) {
        const container = document.getElementById('improvements');
        if (!container) return;

        const safeImprovements = Array.isArray(improvements) ? improvements : [];

        let html = '';
        if (safeImprovements.length > 0) {
            html += `<div class="improvements-list"><h4>Improvements</h4><ul>${safeImprovements.map(i => `<li>${i}</li>`).join('')}</ul></div>`;
        }

        if (improvedAd) {
            html += `
                <div class="improved-ad">
                    <h4>AI-Optimized Version</h4>
                    <div class="improved-headline">${improvedAd?.headline ?? 'N/A'}</div>
                    <div class="improved-body">${improvedAd?.body_copy ?? 'N/A'}</div>
                    <div class="improved-cta">${improvedAd?.cta ?? 'N/A'}</div>
                    <p>Predicted Score: ${improvedAd?.predicted_score ?? 0}</p>
                </div>
            `;
        }

        container.innerHTML = html;
    }

    renderVideoExecution(video) {
        const container = document.getElementById('videoExecution');
        if (!container || !video || video?.is_video_script === 'No') return;

        container.innerHTML = `
            <div class="video-analysis">
                <h4>Video Script Analysis</h4>
                <p>Hook Delivery: ${video?.hook_delivery_strength ?? 'N/A'}</p>
                <p>Speech Flow: ${video?.speech_flow_quality ?? 'N/A'}</p>
                <p>Visual Dependency: ${video?.visual_dependency ?? 'N/A'}</p>
                <p>Delivery Risk: ${video?.delivery_risk ?? 'N/A'}</p>
            </div>
        `;
    }

    renderCriticalWeaknesses(weaknesses) {
        const container = document.getElementById('criticalWeaknesses');
        if (!container) return;

        const safeWeaknesses = Array.isArray(weaknesses) ? weaknesses : [];

        container.innerHTML = safeWeaknesses.map(w => `
            <div class="weakness-card severity-${w?.severity ?? 'medium'}">
                <span class="severity-badge">${w?.severity ?? 'MEDIUM'}</span>
                <h5>${w?.issue ?? 'Unknown Issue'}</h5>
                <p>${w?.behavior_impact ?? 'N/A'}</p>
                <p><strong>Fix:</strong> ${w?.precise_fix ?? 'N/A'}</p>
            </div>
        `).join('');
    }

    // ISSUE 2 FIX: Safe currency formatting
    formatCurrency(value) {
        // Handle undefined, null, or non-numeric values
        if (value === undefined || value === null || value === '') return 'N/A';

        const num = Number(value);
        if (isNaN(num)) return 'N/A';

        // Format as currency
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(num);
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

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdAnalyzer;
}
