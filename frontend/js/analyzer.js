/**
 * ADLYTICS Analyzer v6.1 - PRODUCTION GRADE
 * Patched: exposes currentAnalysis + currentContent globally after each render
 * so all Tier 2 feature scripts can access live data without any coupling.
 */

class AdAnalyzer {
    constructor() {
        this.currentAnalysis = null;
        this.audienceConfig = null;
        this.apiBaseUrl = window.location.origin;
        this.requestTimeout = 60000;
        this.init();
    }

    init() {
        this.cacheElements();
        this.bindEvents();
        this.loadAudienceConfig();
        console.log('✅ ADLYTICS v6.1 Analyzer Initialized');
    }

    cacheElements() {
        this.elements = {
            form:         document.getElementById('analyzerForm'),
            adCopy:       document.getElementById('adCopy'),
            videoScript:  document.getElementById('videoScript'),
            platform:     document.getElementById('platform'),
            industry:     document.getElementById('industry'),
            country:      document.getElementById('audienceCountry'),
            region:       document.getElementById('audienceRegion'),
            age:          document.getElementById('audienceAge'),
            income:       document.getElementById('audienceIncome'),
            occupation:   document.getElementById('audienceOccupation'),
            submitBtn:    document.getElementById('analyzeBtn'),
            loading:      document.getElementById('loading'),
            results:      document.getElementById('results'),
            errorDisplay: document.getElementById('errorDisplay')
        };
    }

    bindEvents() {
        if (this.elements.form) {
            this.elements.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Tab switching — handles both original and new tabs
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.tab-btn');
            if (btn && btn.dataset.tab) {
                this.switchTab(btn.dataset.tab);
            }
        });

        if (this.elements.country) {
            this.elements.country.addEventListener('change', () => this.updateRegions());
        }
    }

    normalizeResponse(data) {
        if (!data || typeof data !== 'object') {
            return this.getDefaultResponse();
        }
        return {
            scores: {
                overall: 0, hook_strength: 0, clarity: 0,
                credibility: 0, emotional_pull: 0, cta_strength: 0,
                audience_match: 0, platform_fit: 0,
                // legacy aliases
                trust_building: 0, cta_power: 0, audience_alignment: 0,
                ...data.scores
            },
            decision_engine: {
                should_run: false, confidence: '0%', expected_profit: 0,
                recommended_budget: 0, kill_threshold: 'N/A', go_threshold: 'N/A',
                ...data.decision_engine
            },
            budget_optimization: {
                break_even_cpc: 0, safe_test_budget: 0, scaling_rule: 'N/A',
                daily_budget_cap: 0, expected_cpa: 0, days_to_profit: 0,
                risk_level: 'Unknown', worst_case_loss: 0, budget_tip: '',
                budget_phases: [],
                ...data.budget_optimization
            },
            neuro_response: {
                dopamine: 0, fear: 0, curiosity: 0, urgency: 0, trust: 0,
                primary_driver: 'unknown', emotional_triggers: [], psychological_gaps: [],
                ...data.neuro_response
            },
            creative_fatigue: {
                fatigue_level: 'Unknown', estimated_decline_days: 14,
                refresh_needed: false, explanation: '', refresh_recommendations: [],
                ...data.creative_fatigue
            },
            objection_detection: {
                scam_triggers: [], trust_gaps: [],
                unrealistic_claims: [], compliance_risks: [],
                ...data.objection_detection
            },
            ad_variants:         Array.isArray(data.ad_variants) ? data.ad_variants : [],
            winner_prediction:   { winner_id: null, angle: '', confidence: '0%', reasoning: '', ...data.winner_prediction },
            cross_platform:      data.cross_platform ?? {},
            persona_reactions:   Array.isArray(data.persona_reactions) ? data.persona_reactions : [],
            behavior_summary:    data.behavior_summary ?? data.strategic_summary ?? {},
            phase_breakdown:     data.phase_breakdown ?? {},
            improvements:        Array.isArray(data.improvements) ? data.improvements : [],
            improved_ad:         data.improved_ad ?? null,
            video_execution_analysis: data.video_execution_analysis ?? null,
            critical_weaknesses: Array.isArray(data.critical_weaknesses) ? data.critical_weaknesses : [],
            line_by_line_analysis: Array.isArray(data.line_by_line_analysis) ? data.line_by_line_analysis : [],
            roi_comparison:      data.roi_comparison ?? null,
            competitor_advantage: data.competitor_advantage ?? null,
            ...data
        };
    }

    getDefaultResponse() {
        return {
            scores: { overall: 0, hook_strength: 0, clarity: 0, credibility: 0, emotional_pull: 0, cta_strength: 0 },
            decision_engine: { should_run: false, confidence: '0%', expected_profit: 0 },
            budget_optimization: { break_even_cpc: 0, safe_test_budget: 0 },
            neuro_response: { dopamine: 0, fear: 0, curiosity: 0, primary_driver: 'unknown', emotional_triggers: [], psychological_gaps: [] },
            creative_fatigue: { fatigue_level: 'Unknown', refresh_needed: false, refresh_recommendations: [] },
            objection_detection: { scam_triggers: [], trust_gaps: [], compliance_risks: [] },
            ad_variants: [], winner_prediction: {}, cross_platform: {},
            persona_reactions: [], improvements: [], critical_weaknesses: []
        };
    }

    async loadAudienceConfig() {
        this.audienceConfig = {
            countries: [
                { code: "nigeria",      name: "Nigeria",       regions: ["Lagos", "Abuja", "Kano", "Ibadan", "Port Harcourt"] },
                { code: "ghana",        name: "Ghana",         regions: ["Accra", "Kumasi", "Tamale"] },
                { code: "us",           name: "United States", regions: ["California", "Texas", "New York", "Florida", "Illinois"] },
                { code: "uk",           name: "United Kingdom",regions: ["London", "Manchester", "Birmingham", "Glasgow"] },
                { code: "canada",       name: "Canada",        regions: ["Ontario", "Quebec", "British Columbia", "Alberta"] },
                { code: "kenya",        name: "Kenya",         regions: ["Nairobi", "Mombasa", "Kisumu"] },
                { code: "south_africa", name: "South Africa",  regions: ["Gauteng", "Western Cape", "KwaZulu-Natal"] },
                { code: "india",        name: "India",         regions: ["Maharashtra", "Karnataka", "Delhi"] },
                { code: "australia",    name: "Australia",     regions: ["New South Wales", "Victoria", "Queensland"] },
                { code: "germany",      name: "Germany",       regions: ["Bavaria", "North Rhine-Westphalia"] }
            ]
        };
        this.populateCountryDropdown();
    }

    populateCountryDropdown() {
        if (!this.elements.country || !this.audienceConfig) return;
        this.elements.country.innerHTML = this.audienceConfig.countries
            .map(c => `<option value="${c.code}">${c.name}</option>`)
            .join('');
        this.updateRegions();
    }

    updateRegions() {
        const code = this.elements.country?.value;
        const sel  = this.elements.region;
        if (!code || !sel || !this.audienceConfig) return;
        const country = this.audienceConfig.countries.find(c => c.code === code);
        if (country?.regions?.length) {
            sel.innerHTML = `<option value="">Select Region</option>` +
                country.regions.map(r =>
                    `<option value="${r.toLowerCase().replace(/\s+/g,'-')}">${r}</option>`
                ).join('');
            sel.disabled = false;
        } else {
            sel.innerHTML = '<option value="">No regions available</option>';
            sel.disabled = true;
        }
    }

    async handleSubmit(e) {
        e.preventDefault();
        this.showLoading();
        this.hideError();

        const adCopy      = this.elements.adCopy?.value     || '';
        const videoScript = this.elements.videoScript?.value || '';

        if (!adCopy.trim() && !videoScript.trim()) {
            this.showError('Please provide either ad copy or a video script');
            this.hideLoading();
            return;
        }

        const formData = new FormData();
        formData.append('ad_copy',          adCopy);
        formData.append('video_script',     videoScript);
        formData.append('platform',         this.elements.platform?.value    || 'tiktok');
        formData.append('industry',         this.elements.industry?.value    || 'finance');
        formData.append('audience_country', this.elements.country?.value     || 'nigeria');
        formData.append('audience_region',  this.elements.region?.value      || '');
        formData.append('audience_age',     this.elements.age?.value         || '25-34');
        formData.append('audience_income',  this.elements.income?.value      || '');
        formData.append('audience_occupation', this.elements.occupation?.value || '');

        const controller = new AbortController();
        const timeoutId  = setTimeout(() => controller.abort(), this.requestTimeout);

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/analyze`, {
                method: 'POST',
                body:   formData,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                let msg = `HTTP ${response.status}`;
                try { const d = await response.json(); msg = d.detail || d.error?.message || msg; } catch(_) {}
                throw new Error(msg);
            }

            const result = await response.json();
            if (!result.success) throw new Error(result.error?.message || 'Analysis failed');

            this.currentAnalysis = this.normalizeResponse(result.data);

            // ── GLOBAL EXPOSURE for Tier 2 features ──────────────────
            window._adlyticsData    = this.currentAnalysis;
            window._adlyticsContent = videoScript.trim() || adCopy.trim();
            window._adlyticsPlatform  = this.elements.platform?.value || 'tiktok';
            window._adlyticsIndustry  = this.elements.industry?.value || 'finance';
            window._adlyticsCountry   = this.elements.country?.value  || 'nigeria';
            // ─────────────────────────────────────────────────────────

            this.renderResults(this.currentAnalysis);

            // Notify Tier 2 features that a fresh analysis is available
            window.dispatchEvent(new CustomEvent('adlytics:analyzed', { detail: this.currentAnalysis }));

        } catch (error) {
            if (error.name === 'AbortError') {
                this.showError('Request timed out. Please try again.');
            } else {
                this.showError(error.message || 'An unexpected error occurred');
                console.error('❌ Analysis error:', error);
            }
        } finally {
            clearTimeout(timeoutId);
            this.hideLoading();
        }
    }

    renderResults(data) {
        this.elements.results?.classList.remove('hidden');
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
        const container = document.getElementById('scoresContainer');
        if (!container || !scores) return;
        const items = [
            { key: 'overall',        label: 'Overall' },
            { key: 'hook_strength',  label: 'Hook' },
            { key: 'clarity',        label: 'Clarity' },
            { key: 'credibility',    label: 'Credibility' },
            { key: 'emotional_pull', label: 'Emotional' },
            { key: 'cta_strength',   label: 'CTA' },
            { key: 'audience_match', label: 'Audience' },
            { key: 'platform_fit',   label: 'Platform' }
        ];
        container.innerHTML = items.map(item => {
            const v = scores[item.key] ?? scores[item.key.replace('strength','power').replace('pull','_')] ?? 0;
            return `<div class="score-card ${this.getScoreColor(v)}">
                        <div class="score-value">${v}</div>
                        <div class="score-label">${item.label}</div>
                    </div>`;
        }).join('');
    }

    getScoreColor(s) {
        if (s >= 81) return 'excellent';
        if (s >= 61) return 'good';
        if (s >= 41) return 'average';
        if (s >= 21) return 'poor';
        return 'critical';
    }

    renderDecisionEngine(decision) {
        const container = document.getElementById('decisionEngine');
        if (!container) return;
        const run = decision?.should_run ?? false;
        container.innerHTML = `
            <div class="decision-card ${run ? 'success' : 'danger'}">
                <h3>${run ? '✅ RECOMMENDED TO RUN' : '❌ DO NOT RUN'}</h3>
                <p>Confidence: ${decision?.confidence ?? '0%'}</p>
                <p>Expected Profit: ${this.formatCurrency(decision?.expected_profit)}</p>
                <p>ROI Prediction: ${decision?.roi_prediction ?? 'N/A'}</p>
                <p>${decision?.reasoning ?? ''}</p>
            </div>`;
    }

    renderBudgetOptimization(budget) {
        const container = document.getElementById('budgetOptimization');
        if (!container) return;
        const phases = Array.isArray(budget?.budget_phases) ? budget.budget_phases : [];
        container.innerHTML = `
            <div class="budget-grid">
                <div class="budget-card"><h4>Break-Even CPC</h4><div class="budget-value">${this.formatCurrency(budget?.break_even_cpc)}</div></div>
                <div class="budget-card"><h4>Safe Test Budget</h4><div class="budget-value">${this.formatCurrency(budget?.safe_test_budget)}</div></div>
                <div class="budget-card"><h4>Days to Profit</h4><div class="budget-value">${budget?.days_to_profit ?? 'N/A'}</div></div>
            </div>
            <p><strong>Risk:</strong> ${budget?.risk_level ?? 'N/A'} &nbsp;|&nbsp; <strong>Worst Case Loss:</strong> ${this.formatCurrency(budget?.worst_case_loss)}</p>
            <p><strong>Scaling Rule:</strong> ${budget?.scaling_rule ?? 'N/A'}</p>
            ${phases.length ? `<ul>${phases.map(p=>`<li>${p}</li>`).join('')}</ul>` : ''}
            ${budget?.budget_tip ? `<p style="margin-top:10px;"><strong>💡 Tip:</strong> ${budget.budget_tip}</p>` : ''}`;
    }

    renderNeuroResponse(neuro) {
        const container = document.getElementById('neuroResponse');
        if (!container || !neuro) return;
        const drivers = ['dopamine','fear','curiosity','urgency','trust'];
        const triggers = Array.isArray(neuro.emotional_triggers) ? neuro.emotional_triggers : [];
        const gaps     = Array.isArray(neuro.psychological_gaps) ? neuro.psychological_gaps : [];
        container.innerHTML = `
            <div class="neuro-container">
                <h4>Primary Driver: ${(neuro.primary_driver ?? 'unknown').toUpperCase()}</h4>
                ${drivers.map(d => {
                    const v = neuro[d] ?? 0;
                    return `<div class="neuro-item"><label>${d}</label>
                        <div class="neuro-bar-container">
                            <div class="neuro-bar" style="width:${v}%;background:${this.getNeuroColor(d,v)}"></div>
                            <span>${v}</span>
                        </div></div>`;
                }).join('')}
                ${triggers.length ? `<div style="margin-top:12px;"><strong>Emotional Triggers:</strong><ul>${triggers.map(t=>`<li>${t}</li>`).join('')}</ul></div>` : ''}
                ${gaps.length ? `<div style="margin-top:8px;"><strong>Psychological Gaps:</strong><ul>${gaps.map(g=>`<li>${g}</li>`).join('')}</ul></div>` : ''}
            </div>`;
    }

    getNeuroColor(d, v) {
        if (d === 'fear')  return v > 70 ? '#ef4444' : v > 40 ? '#f59e0b' : '#10b981';
        if (d === 'trust') return v > 70 ? '#10b981' : v > 40 ? '#f59e0b' : '#ef4444';
        return v > 70 ? '#8b5cf6' : v > 40 ? '#f59e0b' : '#6b7280';
    }

    renderCreativeFatigue(fatigue) {
        const container = document.getElementById('creativeFatigue');
        if (!container) return;
        const level = fatigue?.fatigue_level ?? 'Unknown';
        const recs  = Array.isArray(fatigue?.refresh_recommendations) ? fatigue.refresh_recommendations : [];
        container.innerHTML = `
            <div class="fatigue-card ${level.toLowerCase().replace(/\s+/g,'-')}">
                <h4>Fatigue Level: ${level}</h4>
                <p>Est. decline in <strong>${fatigue?.estimated_decline_days ?? fatigue?.estimated_decline_time ?? 'N/A'} days</strong></p>
                <p>${fatigue?.refresh_needed ? '⚠️ Refresh recommended' : '✅ No refresh needed yet'}</p>
                <p>${fatigue?.explanation ?? ''}</p>
                ${recs.length ? `<ul>${recs.map(r=>`<li>${r}</li>`).join('')}</ul>` : ''}
            </div>`;
    }

    renderObjectionDetection(obj) {
        const container = document.getElementById('objectionDetection');
        if (!container) return;
        const renderItems = (arr) => {
            if (!Array.isArray(arr) || arr.length === 0) return '<p>✅ No issues detected</p>';
            return `<ul>${arr.map(item => {
                if (typeof item === 'object') {
                    return `<li><strong>${item.trigger || item.gap || item.risk || item.issue || 'Issue'}</strong>
                        ${item.fix ? ` — <em>Fix: ${item.fix}</em>` : ''}
                        ${item.severity ? ` <span style="color:#ef4444;">[${item.severity}]</span>` : ''}</li>`;
                }
                return `<li>${item}</li>`;
            }).join('')}</ul>`;
        };
        container.innerHTML = `
            <div class="objection-section"><h4>🚩 Scam Triggers</h4>${renderItems(obj?.scam_triggers)}</div>
            <div class="objection-section"><h4>🔍 Trust Gaps</h4>${renderItems(obj?.trust_gaps)}</div>
            <div class="objection-section"><h4>⚖️ Compliance Risks</h4>${renderItems(obj?.compliance_risks)}</div>`;
    }

    renderAdVariants(variants, winner) {
        const container = document.getElementById('adVariants');
        if (!container) return;
        const safe = Array.isArray(variants) ? variants : [];
        const winnerId = winner?.winner_id ?? winner?.best_variant_id ?? null;
        container.innerHTML = `
            ${winnerId ? `<div class="winner-prediction"><h4>🏆 Predicted Winner: ${winner?.angle ?? 'Variant #'+winnerId} — ${winner?.confidence ?? ''} confidence</h4></div>` : ''}
            <div class="variants-grid">
                ${safe.map(v => `
                    <div class="variant-card ${winnerId === v?.id ? 'winner' : ''}">
                        <h5>Variant #${v?.id} — ${v?.angle ?? ''}</h5>
                        <p><strong>Score:</strong> ${v?.predicted_score ?? 0}</p>
                        <p><strong>Hook:</strong> ${v?.hook ?? 'N/A'}</p>
                        <p><strong>Body:</strong> ${v?.body ?? ''}</p>
                        <p><strong>CTA:</strong> ${v?.cta ?? ''}</p>
                        ${v?.why_it_works ? `<p><em>${v.why_it_works}</em></p>` : ''}
                    </div>`).join('')}
            </div>`;
    }

    renderCrossPlatform(cross) {
        const container = document.getElementById('crossPlatform');
        if (!container) return;
        const platforms = cross ?? {};
        container.innerHTML = Object.entries(platforms).map(([p, d]) => `
            <div class="platform-card">
                <h4>${p.toUpperCase()} — Score: ${d?.score ?? 0}</h4>
                <blockquote>${d?.adapted_copy ?? d?.adapted_copy ?? 'N/A'}</blockquote>
                <p>${d?.changes_needed ?? d?.changes ?? ''}</p>
            </div>`).join('');
    }

    renderBehaviorSummary(summary) {
        const container = document.getElementById('behaviorSummary');
        if (!container) return;
        if (typeof summary === 'string') {
            container.innerHTML = `<div class="behavior-card"><p>${summary}</p></div>`;
            return;
        }
        container.innerHTML = `
            <div class="behavior-card">
                <h3>${summary?.verdict ?? ''}</h3>
                <p>${summary?.launch_readiness ?? ''}</p>
                <p>${summary?.primary_reason ?? summary?.failure_risk ?? ''}</p>
            </div>`;
    }

    renderPhaseBreakdown(phases) {
        const container = document.getElementById('phaseBreakdown');
        if (!container) return;
        if (typeof phases === 'object' && !Array.isArray(phases)) {
            container.innerHTML = Object.entries(phases).map(([k,v]) => `
                <div class="phase-item">
                    <h5>${k.replace(/_/g,' ').toUpperCase()}</h5>
                    <p>${v ?? 'N/A'}</p>
                </div>`).join('');
        }
    }

    renderPersonaReactions(personas) {
        const container = document.getElementById('personaReactions');
        if (!container) return;
        const safe = Array.isArray(personas) ? personas : [];
        container.innerHTML = safe.map(p => `
            <div class="persona-card">
                <h5>${p?.name ?? p?.persona ?? 'Unknown'}</h5>
                <p style="color:#6b7280;font-size:.85rem;">${p?.demographic ?? ''}</p>
                <p><strong>Reaction:</strong> ${p?.reaction ?? 'N/A'}</p>
                <p><strong>Conversion:</strong> ${p?.conversion_likelihood ?? ((p?.likelihood_to_convert ?? 0) * 100).toFixed(0)+'%'}</p>
                ${Array.isArray(p?.pain_points) ? `<ul>${p.pain_points.map(x=>`<li>${x}</li>`).join('')}</ul>` : ''}
                ${Array.isArray(p?.objections) ? `<ul>${p.objections.map(x=>`<li><em>${x}</em></li>`).join('')}</ul>` : ''}
            </div>`).join('');
    }

    renderImprovements(improvements, improvedAd) {
        const container = document.getElementById('improvements');
        if (!container) return;
        const safe = Array.isArray(improvements) ? improvements : [];
        let html = '';
        if (safe.length) {
            html += `<div class="improvements-list"><ul>${safe.map(i => {
                if (typeof i === 'object') return `<li><strong>${i.change ?? i.issue ?? ''}</strong> — ${i.expected_impact ?? ''} — <em>${i.implementation ?? i.fix ?? ''}</em></li>`;
                return `<li>${i}</li>`;
            }).join('')}</ul></div>`;
        }
        if (improvedAd) {
            html += `<div class="improved-ad">
                <h4>AI-Optimized Version</h4>
                <p>${improvedAd?.headline ?? improvedAd?.hook ?? 'N/A'}</p>
                <p>${improvedAd?.body_copy ?? improvedAd?.body ?? ''}</p>
                <p>${improvedAd?.cta ?? ''}</p>
                <p>Predicted Score: ${improvedAd?.predicted_score ?? improvedAd?.improved_score ?? 0}</p>
            </div>`;
        }
        container.innerHTML = html;
    }

    renderVideoExecution(video) {
        const container = document.getElementById('videoExecution');
        if (!container || !video) return;
        container.innerHTML = `
            <div class="video-analysis">
                <h4>Video Script Analysis</h4>
                <p>Hook Delivery: ${video?.hook_delivery ?? video?.hook_delivery_strength ?? 'N/A'}</p>
                <p>Speech Flow: ${video?.speech_flow ?? video?.speech_flow_quality ?? 'N/A'}</p>
                <p>Visual Dependency: ${video?.visual_dependency ?? 'N/A'}</p>
                <p>Format: ${video?.recommended_format ?? 'N/A'}</p>
                <p>Delivery Risk: ${video?.delivery_risk ?? 'N/A'}</p>
            </div>`;
    }

    renderCriticalWeaknesses(weaknesses) {
        const container = document.getElementById('criticalWeaknesses');
        if (!container) return;
        const safe = Array.isArray(weaknesses) ? weaknesses : [];
        container.innerHTML = safe.map(w => `
            <div class="weakness-card severity-${(w?.severity ?? 'medium').toLowerCase()}">
                <span class="severity-badge">${w?.severity ?? 'MEDIUM'}</span>
                <h5>${w?.issue ?? 'Unknown Issue'}</h5>
                <p>${w?.impact ?? w?.behavior_impact ?? 'N/A'}</p>
                <p><strong>Fix:</strong> ${w?.fix ?? w?.precise_fix ?? 'N/A'}</p>
            </div>`).join('');
    }

    formatCurrency(value) {
        if (value === undefined || value === null || value === '') return 'N/A';
        const num = Number(value);
        if (isNaN(num)) return 'N/A';
        return new Intl.NumberFormat('en-US', { style:'currency', currency:'USD', maximumFractionDigits:0 }).format(num);
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

document.addEventListener('DOMContentLoaded', () => {
    window.adAnalyzer = new AdAnalyzer();
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdAnalyzer;
}
