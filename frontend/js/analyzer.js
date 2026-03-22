/**
 * ADLYTICS Analyzer v5.0 - Frontend Controller
 * Handles all v5 features: Decision Engine, Budget Optimization, 
 * Ad Variants, Objection Detection, Creative Fatigue, Neuro Response,
 * Cross-Platform Adaptation, and Enhanced Personas
 */

class AdAnalyzer {
    constructor() {
        this.currentAnalysis = null;
        this.apiBaseUrl = '';
        this.elements = {};
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
        this.elements.form = document.getElementById('analyzerForm');
        this.elements.adCopy = document.getElementById('adCopy');
        this.elements.videoScript = document.getElementById('videoScript');
        this.elements.platform = document.getElementById('platform');
        this.elements.industry = document.getElementById('industry');

        // Audience elements
        this.elements.country = document.getElementById('audienceCountry');
        this.elements.region = document.getElementById('audienceRegion');
        this.elements.age = document.getElementById('audienceAge');
        this.elements.income = document.getElementById('audienceIncome');
        this.elements.occupation = document.getElementById('audienceOccupation');

        // UI elements
        this.elements.submitBtn = document.getElementById('analyzeBtn');
        this.elements.loading = document.getElementById('loading');
        this.elements.results = document.getElementById('results');
        this.elements.errorDisplay = document.getElementById('errorDisplay');

        // Tab containers
        this.elements.tabs = {
            overview: document.getElementById('tab-overview'),
            behavior: document.getElementById('tab-behavior'),
            video: document.getElementById('tab-video'),
            personas: document.getElementById('tab-personas'),
            improvements: document.getElementById('tab-improvements'),
            decision: document.getElementById('tab-decision'),
            budget: document.getElementById('tab-budget'),
            neuro: document.getElementById('tab-neuro'),
            fatigue: document.getElementById('tab-fatigue'),
            objections: document.getElementById('tab-objections'),
            variants: document.getElementById('tab-variants'),
            crossplatform: document.getElementById('tab-crossplatform')
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

    async loadAudienceConfig() {
        try {
            const response = await fetch('/api/audience-config');
            const result = await response.json();
            if (result.success) {
                this.audienceConfig = result.data;
                this.populateAudienceDropdowns();
            }
        } catch (error) {
            console.warn('Could not load audience config:', error);
        }
    }

    populateAudienceDropdowns() {
        if (!this.audienceConfig) return;

        // Populate countries
        if (this.elements.country) {
            this.elements.country.innerHTML = this.audienceConfig.countries
                .map(c => `<option value="${c.code}">${c.name}</option>`)
                .join('');
        }
    }

    updateRegions() {
        const countryCode = this.elements.country?.value;
        if (!countryCode || !this.audienceConfig) return;

        const country = this.audienceConfig.countries.find(c => c.code === countryCode);
        if (country && this.elements.region) {
            this.elements.region.innerHTML = country.regions
                .map(r => `<option value="${r.toLowerCase().replace(/\s+/g, '-')}">${r}</option>`)
                .join('');
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
            console.log('📤 Submitting analysis request...');

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

        // Core scores
        this.renderScores(data.scores);

        // All v5 sections
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

        // Default to overview tab
        this.switchTab('overview');
    }

    renderScores(scores) {
        if (!scores) return;

        const container = document.getElementById('scoresContainer');
        if (!container) return;

        const scoreItems = [
            { key: 'overall', label: 'Overall Score', color: this.getScoreColor(scores.overall) },
            { key: 'hook_strength', label: 'Hook Strength', color: this.getScoreColor(scores.hook_strength) },
            { key: 'clarity', label: 'Clarity', color: this.getScoreColor(scores.clarity) },
            { key: 'trust_building', label: 'Trust Building', color: this.getScoreColor(scores.trust_building) },
            { key: 'cta_power', label: 'CTA Power', color: this.getScoreColor(scores.cta_power) },
            { key: 'audience_alignment', label: 'Audience Alignment', color: this.getScoreColor(scores.audience_alignment) }
        ];

        container.innerHTML = scoreItems.map(item => `
            <div class="score-card ${item.color}">
                <div class="score-value">${scores[item.key] || 0}</div>
                <div class="score-label">${item.label}</div>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${scores[item.key]}%"></div>
                </div>
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

    // ==================== V5 FEATURES ====================

    renderDecisionEngine(decision) {
        if (!decision) return;

        const container = document.getElementById('decisionEngine');
        if (!container) return;

        const verdict = decision.should_run ? '✅ RECOMMENDED TO RUN' : '❌ DO NOT RUN';
        const verdictClass = decision.should_run ? 'success' : 'danger';

        container.innerHTML = `
            <div class="decision-card ${verdictClass}">
                <h3>${verdict}</h3>
                <div class="decision-confidence">Confidence: ${decision.confidence || 'N/A'}</div>

                <div class="decision-metrics">
                    <div class="metric">
                        <label>Expected Profit</label>
                        <value>${this.formatCurrency(decision.expected_profit)}</value>
                    </div>
                    <div class="metric">
                        <label>Recommended Budget</label>
                        <value>${this.formatCurrency(decision.recommended_budget)}</value>
                    </div>
                </div>

                <div class="decision-thresholds">
                    <div class="threshold kill">
                        <strong>🛑 Kill Threshold:</strong> ${decision.kill_threshold || 'N/A'}
                    </div>
                    <div class="threshold go">
                        <strong>🚀 Go Threshold:</strong> ${decision.go_threshold || 'N/A'}
                    </div>
                </div>
            </div>
        `;
    }

    renderBudgetOptimization(budget) {
        if (!budget) return;

        const container = document.getElementById('budgetOptimization');
        if (!container) return;

        container.innerHTML = `
            <div class="budget-grid">
                <div class="budget-card">
                    <h4>Break-Even CPC</h4>
                    <div class="budget-value">$${budget.break_even_cpc?.toFixed(2) || 'N/A'}</div>
                    <small>Max cost per click for profitability</small>
                </div>
                <div class="budget-card">
                    <h4>Safe Test Budget</h4>
                    <div class="budget-value">${this.formatCurrency(budget.safe_test_budget)}</div>
                    <small>Recommended initial spend</small>
                </div>
                <div class="budget-card">
                    <h4>Expected CPA</h4>
                    <div class="budget-value">$${budget.expected_cpa?.toFixed(2) || 'N/A'}</div>
                    <small>Cost per acquisition</small>
                </div>
                <div class="budget-card">
                    <h4>Daily Cap</h4>
                    <div class="budget-value">${this.formatCurrency(budget.daily_budget_cap)}</div>
                    <small>Maximum daily spend</small>
                </div>
            </div>
            <div class="scaling-rule">
                <strong>📈 Scaling Rule:</strong> ${budget.scaling_rule || 'N/A'}
            </div>
        `;
    }

    renderNeuroResponse(neuro) {
        if (!neuro) return;

        const container = document.getElementById('neuroResponse');
        if (!container) return;

        const drivers = ['dopamine', 'fear', 'curiosity', 'urgency', 'trust'];
        const driverLabels = {
            dopamine: '🎯 Dopamine (Reward)',
            fear: '😨 Fear (Loss Aversion)',
            curiosity: '🔍 Curiosity (Info Gap)',
            urgency: '⏰ Urgency (Time Pressure)',
            trust: '🤝 Trust (Credibility)'
        };

        const driverEmojis = {
            dopamine: '🎯',
            fear: '😨',
            curiosity: '🔍',
            urgency: '⏰',
            trust: '🤝'
        };

        container.innerHTML = `
            <div class="neuro-container">
                <div class="neuro-primary">
                    <h4>Primary Driver: ${driverEmojis[neuro.primary_driver] || '🔍'} ${neuro.primary_driver?.toUpperCase()}</h4>
                </div>
                <div class="neuro-bars">
                    ${drivers.map(driver => `
                        <div class="neuro-item">
                            <label>${driverLabels[driver]}</label>
                            <div class="neuro-bar-container">
                                <div class="neuro-bar" style="width: ${neuro[driver] || 0}%; background: ${this.getNeuroColor(driver, neuro[driver])}"></div>
                                <span class="neuro-value">${neuro[driver] || 0}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    getNeuroColor(driver, value) {
        if (driver === 'fear') return value > 70 ? '#ef4444' : value > 40 ? '#f59e0b' : '#10b981';
        if (driver === 'trust') return value > 70 ? '#10b981' : value > 40 ? '#f59e0b' : '#ef4444';
        return value > 70 ? '#8b5cf6' : value > 40 ? '#f59e0b' : '#6b7280';
    }

    renderCreativeFatigue(fatigue) {
        if (!fatigue) return;

        const container = document.getElementById('creativeFatigue');
        if (!container) return;

        const levelClass = fatigue.fatigue_level?.toLowerCase().replace(/\s+/g, '-');

        container.innerHTML = `
            <div class="fatigue-card ${levelClass}">
                <div class="fatigue-header">
                    <h4>Fatigue Level: ${fatigue.fatigue_level || 'N/A'}</h4>
                    ${fatigue.refresh_needed ? '<span class="refresh-badge">⚠️ REFRESH NEEDED</span>' : ''}
                </div>
                <div class="fatigue-details">
                    <div class="fatigue-item">
                        <label>Estimated Decline</label>
                        <value>${fatigue.estimated_decline_time || 'N/A'}</value>
                    </div>
                    <div class="fatigue-item">
                        <label>Recommendation</label>
                        <value>${fatigue.variation_recommendation || 'N/A'}</value>
                    </div>
                </div>
            </div>
        `;
    }

    renderObjectionDetection(objections) {
        if (!objections) return;

        const container = document.getElementById('objectionDetection');
        if (!container) return;

        const sections = [
            { key: 'scam_triggers', title: '🚨 Scam Triggers', icon: '⚠️' },
            { key: 'trust_gaps', title: '🛡️ Trust Gaps', icon: '🔒' },
            { key: 'unrealistic_claims', title: '📢 Unrealistic Claims', icon: '📣' },
            { key: 'compliance_risks', title: '⚖️ Compliance Risks', icon: '⚖️' }
        ];

        container.innerHTML = `
            <div class="objections-container">
                ${sections.map(section => {
                    const items = objections[section.key] || [];
                    return `
                        <div class="objection-section">
                            <h4>${section.icon} ${section.title}</h4>
                            ${items.length > 0 ? `
                                <ul>
                                    ${items.map(item => `<li>${item}</li>`).join('')}
                                </ul>
                            ` : '<p class="no-issues">✅ No issues detected</p>'}
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    renderAdVariants(variants, winner) {
        if (!variants || !Array.isArray(variants)) return;

        const container = document.getElementById('adVariants');
        if (!container) return;

        container.innerHTML = `
            <div class="variants-container">
                <div class="winner-prediction">
                    <h4>🏆 Predicted Winner</h4>
                    <div class="winner-card">
                        <span class="winner-id">Variant #${winner?.best_variant_id || 'N/A'}</span>
                        <span class="winner-score">Score: ${winner?.score || 'N/A'}</span>
                        <span class="winner-confidence">Confidence: ${winner?.confidence || 'N/A'}</span>
                        <p>${winner?.reason || ''}</p>
                    </div>
                </div>

                <div class="variants-grid">
                    ${variants.map((variant, index) => `
                        <div class="variant-card ${winner?.best_variant_id === variant.id ? 'winner' : ''}">
                            <div class="variant-header">
                                <span class="variant-id">#${variant.id}</span>
                                <span class="variant-angle">${variant.angle}</span>
                                <span class="variant-score">${variant.predicted_score}</span>
                            </div>
                            <div class="variant-content">
                                <p><strong>Hook:</strong> ${variant.hook || 'N/A'}</p>
                                <p><strong>Trigger:</strong> ${variant.psychological_trigger || 'N/A'}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderCrossPlatform(cross) {
        if (!cross) return;

        const container = document.getElementById('crossPlatform');
        if (!container) return;

        const platforms = Object.entries(cross).map(([key, data]) => ({
            name: key.charAt(0).toUpperCase() + key.slice(1).replace('_', ' '),
            ...data
        }));

        container.innerHTML = `
            <div class="crossplatform-grid">
                ${platforms.map(platform => `
                    <div class="platform-card">
                        <div class="platform-header">
                            <h4>${platform.name}</h4>
                            <span class="platform-score ${this.getScoreColor(platform.score)}">${platform.score}</span>
                        </div>
                        <div class="platform-copy">
                            <blockquote>${platform.adapted_copy || 'N/A'}</blockquote>
                        </div>
                        <div class="platform-changes">
                            <strong>Changes:</strong> ${platform.changes || 'N/A'}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderBehaviorSummary(summary) {
        if (!summary) return;

        const container = document.getElementById('behaviorSummary');
        if (!container) return;

        const verdictClass = summary.verdict?.toLowerCase().replace(/\s+/g, '-');

        container.innerHTML = `
            <div class="behavior-card ${verdictClass}">
                <div class="verdict">${summary.verdict || 'N/A'}</div>
                <div class="behavior-metrics">
                    <div>
                        <span>Launch Readiness</span>
                        <strong>${summary.launch_readiness || 'N/A'}</strong>
                    </div>
                    <div>
                        <span>Failure Risk</span>
                        <strong>${summary.failure_risk || 'N/A'}</strong>
                    </div>
                </div>
                <div class="primary-reason">
                    <strong>Why:</strong> ${summary.primary_reason || 'N/A'}
                </div>
            </div>
        `;
    }

    renderPhaseBreakdown(phases) {
        if (!phases) return;

        const container = document.getElementById('phaseBreakdown');
        if (!container) return;

        const phaseOrder = [
            { key: 'micro_stop_0_1s', label: '0-1s: Micro-Stop', icon: '👁️' },
            { key: 'scroll_stop_1_2s', label: '1-2s: Scroll Stop', icon: '✋' },
            { key: 'attention_2_5s', label: '2-5s: Attention Hook', icon: '🎯' },
            { key: 'trust_evaluation', label: 'Trust Evaluation', icon: '🛡️' },
            { key: 'click_and_post_click', label: 'Click & Post-Click', icon: '🖱️' }
        ];

        container.innerHTML = `
            <div class="phases-timeline">
                ${phaseOrder.map((phase, index) => `
                    <div class="phase-item">
                        <div class="phase-marker">${index + 1}</div>
                        <div class="phase-content">
                            <h5>${phase.icon} ${phase.label}</h5>
                            <p>${phases[phase.key] || 'N/A'}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderPersonaReactions(personas) {
        if (!personas || !Array.isArray(personas)) return;

        const container = document.getElementById('personaReactions');
        if (!container) return;

        container.innerHTML = `
            <div class="personas-grid">
                ${personas.map(persona => {
                    const behaviorClass = persona.behavior?.toLowerCase().replace(/\s+/g, '-');
                    const likelihood = (persona.likelihood_to_convert || 0) * 100;

                    return `
                        <div class="persona-card ${behaviorClass}">
                            <div class="persona-header">
                                <h5>${persona.persona}</h5>
                                <span class="behavior-badge">${persona.behavior}</span>
                            </div>
                            <div class="persona-content">
                                <p><strong>Reaction:</strong> ${persona.reaction}</p>
                                <p><strong>Objection:</strong> "${persona.objection}"</p>
                                <div class="likelihood-bar">
                                    <label>Conversion Likelihood</label>
                                    <div class="likelihood-track">
                                        <div class="likelihood-fill" style="width: ${likelihood}%"></div>
                                    </div>
                                    <span>${likelihood.toFixed(0)}%</span>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    renderImprovements(improvements, improvedAd) {
        const container = document.getElementById('improvements');
        if (!container) return;

        let html = '';

        if (improvements && Array.isArray(improvements)) {
            html += `
                <div class="improvements-list">
                    <h4>🔧 Suggested Improvements</h4>
                    <ul>
                        ${improvements.map(imp => `<li>${imp}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (improvedAd) {
            html += `
                <div class="improved-ad">
                    <h4>✨ AI-Optimized Version</h4>
                    <div class="improved-card">
                        <div class="improved-headline">${improvedAd.headline || 'N/A'}</div>
                        <div class="improved-body">${improvedAd.body_copy || 'N/A'}</div>
                        <div class="improved-cta">${improvedAd.cta || 'N/A'}</div>
                        <div class="improved-score">
                            Predicted Score: <strong>${improvedAd.predicted_score || 'N/A'}</strong>
                        </div>
                        <div class="improved-angle">
                            Angle: ${improvedAd.angle || 'N/A'}
                        </div>
                    </div>
                </div>
            `;
        }

        container.innerHTML = html;
    }

    renderVideoExecution(video) {
        if (!video || video.is_video_script === 'No') return;

        const container = document.getElementById('videoExecution');
        if (!container) return;

        container.innerHTML = `
            <div class="video-analysis">
                <h4>🎬 Video Script Analysis</h4>
                <div class="video-metrics">
                    <div class="video-metric">
                        <label>Hook Delivery</label>
                        <value class="${video.hook_delivery_strength?.toLowerCase()}">${video.hook_delivery_strength || 'N/A'}</value>
                    </div>
                    <div class="video-metric">
                        <label>Speech Flow</label>
                        <value class="${video.speech_flow_quality?.toLowerCase()}">${video.speech_flow_quality || 'N/A'}</value>
                    </div>
                    <div class="video-metric">
                        <label>Visual Dependency</label>
                        <value>${video.visual_dependency || 'N/A'}</value>
                    </div>
                    <div class="video-metric">
                        <label>Delivery Risk</label>
                        <value class="${video.delivery_risk?.toLowerCase()}">${video.delivery_risk || 'N/A'}</value>
                    </div>
                </div>
                <div class="format-recommendation">
                    <strong>Recommended Format:</strong> ${video.recommended_format || 'N/A'}
                </div>
                <div class="execution-gap">
                    <strong>Biggest Gap:</strong> ${video.biggest_execution_gap || 'N/A'}
                </div>
            </div>
        `;
    }

    renderCriticalWeaknesses(weaknesses) {
        if (!weaknesses || !Array.isArray(weaknesses)) return;

        const container = document.getElementById('criticalWeaknesses');
        if (!container) return;

        const severityOrder = { critical: 1, high: 2, medium: 3, low: 4 };
        const sorted = [...weaknesses].sort((a, b) => 
            (severityOrder[a.severity] || 5) - (severityOrder[b.severity] || 5)
        );

        container.innerHTML = `
            <div class="weaknesses-list">
                ${sorted.map(w => `
                    <div class="weakness-card severity-${w.severity}">
                        <div class="weakness-header">
                            <span class="severity-badge">${w.severity?.toUpperCase()}</span>
                            <h5>${w.issue}</h5>
                        </div>
                        <p><strong>Impact:</strong> ${w.behavior_impact}</p>
                        <p><strong>Fix:</strong> ${w.precise_fix}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // ==================== UTILITY METHODS ====================

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update tab content
        Object.entries(this.elements.tabs).forEach(([name, element]) => {
            if (element) {
                element.classList.toggle('active', name === tabName);
            }
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

    formatCurrency(value) {
        if (value === undefined || value === null) return 'N/A';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.adAnalyzer = new AdAnalyzer();
});

// Export for module systems if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdAnalyzer;
}
