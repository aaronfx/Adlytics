/**
 * ADLYTICS Tier 2 Features v2.0
 * ══════════════════════════════════════════════════════════════
 * Reads from window._adlyticsData, window._adlyticsContent,
 * window._adlyticsPlatform, window._adlyticsIndustry, window._adlyticsCountry
 * (set by analyzer.js after every successful analysis)
 *
 * HOW TO INCLUDE:
 *   <script src="/static/tier2_features.js" defer></script>
 *   (after analyzer.js)
 * ══════════════════════════════════════════════════════════════
 */

// ── State ────────────────────────────────────────────────────
let _rewriteFocus      = 'full';
let _voiceoverEnabled  = false;
let _voiceStyle        = 'conversational';

// ── Helpers ───────────────────────────────────────────────────
function getContent()  { return window._adlyticsContent  || ''; }
function getData()     { return window._adlyticsData      || null; }
function getPlatform() { return window._adlyticsPlatform  || document.getElementById('platform')?.value || 'tiktok'; }
function getIndustry() { return window._adlyticsIndustry  || document.getElementById('industry')?.value || 'finance'; }
function getCountry()  { return window._adlyticsCountry   || document.getElementById('audienceCountry')?.value || 'nigeria'; }

function showSpinner(containerId, message) {
    const el = document.getElementById(containerId);
    if (el) el.innerHTML = `
        <div style="text-align:center;padding:40px;color:var(--gray-400,#9ca3af);">
            <div style="width:40px;height:40px;border:3px solid #e5e7eb;border-top-color:#6366f1;
                border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 16px;"></div>
            <p>${message}</p>
        </div>`;
}

function showEmpty(containerId, message) {
    const el = document.getElementById(containerId);
    if (el) el.innerHTML = `<p style="color:var(--gray-400,#9ca3af);padding:16px;">${message}</p>`;
}

function needsAnalysis(containerId) {
    if (!getData()) {
        showEmpty(containerId, '⚠️ Run an analysis first using the form above, then come back to this tab.');
        return true;
    }
    return false;
}

// Listen for analysis completion to auto-populate tabs
window.addEventListener('adlytics:analyzed', (e) => {
    // Auto-load benchmarks for current industry
    const ind = getIndustry();
    const benchInd = document.getElementById('benchIndustry');
    if (benchInd) benchInd.value = ind;
    loadBenchmarks();
    // Auto-run compliance silently
    _runComplianceCheck(true);
    // Load AB history
    loadAbResults();
});

// ══════════════════════════════════════════════════════════════
// REWRITE ENGINE
// ══════════════════════════════════════════════════════════════
window.setRewriteFocus = function(btn) {
    document.querySelectorAll('.rewrite-focus-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    _rewriteFocus = btn.dataset.focus;
};

window.toggleVoiceover = function(checkbox) {
    _voiceoverEnabled = checkbox.checked;
    const opts = document.getElementById('voiceStyleOptions');
    if (opts) opts.style.display = _voiceoverEnabled ? 'flex' : 'none';
};

window.runRewrite = async function() {
    const content = getContent();
    if (!content) {
        alert('Run an analysis first — the rewrite engine needs analysed content to work with.');
        return;
    }

    const data   = getData();
    const btn    = document.getElementById('rewriteRunBtn');
    const out    = document.getElementById('rewriteOutput');

    btn.disabled = true;
    btn.textContent = '⏳ Rewriting...';
    showSpinner('rewriteOutput', 'AI is rewriting your ad…');

    try {
        const fd = new FormData();
        fd.append('original_ad',      content);
        fd.append('platform',         getPlatform());
        fd.append('industry',         getIndustry());
        fd.append('audience_country', getCountry());
        fd.append('original_scores',  JSON.stringify(data?.scores || {}));
        fd.append('weaknesses',       JSON.stringify(data?.critical_weaknesses || []));
        fd.append('rewrite_focus',    _rewriteFocus);
        fd.append('prepare_voiceover', _voiceoverEnabled ? 'true' : 'false');
        fd.append('voice_style',      _voiceStyle);

        const r = await fetch('/api/rewrite', { method: 'POST', body: fd });
        if (!r.ok) {
            const err = await r.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${r.status}`);
        }
        const result = await r.json();
        if (!result.success) throw new Error(result.detail || 'Rewrite failed');
        _renderRewriteResult(result.data);
    } catch(e) {
        out.innerHTML = `<p style="color:#ef4444;margin-top:16px;">❌ ${e.message}</p>`;
    } finally {
        btn.disabled = false;
        btn.textContent = '✨ Rewrite Now';
    }
};

function _renderRewriteResult(d) {
    const before   = d.before_scores || {};
    const after    = d.after_scores  || {};
    const delta    = d.score_delta   || {};
    const dims     = ['overall','hook_strength','clarity','credibility','emotional_pull','cta_strength'];
    const labels   = {overall:'Overall',hook_strength:'Hook',clarity:'Clarity',credibility:'Cred',emotional_pull:'Emotion',cta_strength:'CTA'};
    const content  = getContent();

    const deltaChips = dims.map(k => {
        const dv = delta[k];
        if (dv === null || dv === undefined) {
            // masked dim — not changed by this focus
            return `<span class="delta-chip flat" data-dim="${k}" style="opacity:.3" title="Not affected by this focus">${labels[k]}: —</span>`;
        }
        const cls = dv > 0 ? 'up' : dv < 0 ? 'down' : 'flat';
        const arrow = dv > 0 ? '▲' : dv < 0 ? '▼' : '→';
        return `<span class="delta-chip ${cls}" data-dim="${k}">${labels[k]}: ${arrow}${Math.abs(dv)}</span>`;
    }).join('');

    const beforeBadges = dims.map(k =>
        `<span class="rewrite-score-badge">${labels[k]}: ${before[k] ?? 50}</span>`).join('');
    const afterBadges = dims.map(k => {
        const dv = delta[k] || 0;
        return `<span class="rewrite-score-badge ${dv > 0 ? 'positive' : dv < 0 ? 'negative' : ''}">${labels[k]}: ${after[k] ?? 50}${dv !== 0 ? ` (${dv > 0 ? '+' : ''}${dv})` : ''}</span>`;
    }).join('');

    const changes = (d.changes_summary || []).map(c => `<li style="padding:4px 0;">• ${c}</li>`).join('');

    let voiceoverHTML = '';
    if (d.voiceover && !d.voiceover.error) {
        const vo = d.voiceover;
        voiceoverHTML = `
            <div style="margin-top:20px;padding:20px;background:#f0fdf4;border:2px solid #10b981;border-radius:12px;">
                <div style="font-weight:700;margin-bottom:12px;color:#065f46;">🎙️ Voiceover Script Ready</div>
                <div style="margin-bottom:10px;">
                    <strong>Est. Duration:</strong> ${vo.estimated_duration_seconds || '—'}s &nbsp;|&nbsp;
                    <strong>Words:</strong> ${vo.word_count || '—'} &nbsp;|&nbsp;
                    <strong>Recommended Voice:</strong> ${vo.recommended_voice_style || '—'}
                </div>
                <div style="margin-bottom:10px;">
                    <strong>Director Notes:</strong>
                    ${vo.director_notes ? Object.entries(vo.director_notes).map(([k,v]) => `<span style="display:block;font-size:.87rem;padding:4px 0;"><em>${k}:</em> ${v}</span>`).join('') : ''}
                </div>
                <div style="background:white;padding:14px;border-radius:8px;font-family:monospace;font-size:.88rem;line-height:1.7;white-space:pre-wrap;border:1px solid #d1fae5;">${vo.voiceover_script || ''}</div>
                <div style="margin-top:10px;">
                    <strong>ElevenLabs Settings:</strong>
                    ${vo.elevenlabs_settings ? `Stability: ${vo.elevenlabs_settings.stability}, Similarity: ${vo.elevenlabs_settings.similarity_boost}, Speaker Boost: ${vo.elevenlabs_settings.use_speaker_boost}` : 'See settings above'}
                </div>
                <button onclick="copyVoiceScript()" style="margin-top:10px;padding:8px 16px;background:#10b981;color:white;border:none;border-radius:6px;cursor:pointer;font-weight:600;">📋 Copy Clean Script for ElevenLabs</button>
                <div id="cleanScriptStore" style="display:none">${vo.clean_script || ''}</div>
            </div>`;
    }

    document.getElementById('rewriteOutput').innerHTML = `
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin:12px 0;">${deltaChips}</div>
        <div class="rewrite-comparison">
            <div class="rewrite-col">
                <div class="rewrite-col-label">📄 Before</div>
                <div class="rewrite-ad-text">${content.replace(/\n/g,'<br>')}</div>
                <div class="rewrite-score-row">${beforeBadges}</div>
            </div>
            <div class="rewrite-col after">
                <div class="rewrite-col-label">✨ After (${_rewriteFocus.replace(/_/g,' ')} focus)</div>
                <div class="rewrite-ad-text" id="rewrittenText">${(d.rewritten_ad||'').replace(/\n/g,'<br>')}</div>
                <div class="rewrite-score-row">${afterBadges}</div>
                ${d.why_it_works ? `<div style="margin-top:12px;padding:12px;background:#f9fafb;border-radius:8px;font-size:.88rem;"><strong>Why it works:</strong> ${d.why_it_works}</div>` : ''}
                ${changes ? `<ul style="margin-top:10px;font-size:.85rem;">${changes}</ul>` : ''}
                <div style="background:#fef3c7;border-left:3px solid #f59e0b;padding:8px 12px;border-radius:0 6px 6px 0;font-size:.8rem;color:#92400e;margin-top:12px;">
                    ⚠️ Scores above are the AI's self-estimate. Click <strong>Verify Scores</strong> below for the real rating.
                </div>
                <button class="use-rewrite-btn" onclick="useRewrittenAd(false)" style="margin-top:10px;">📋 Use This Version</button>
                <button onclick="useRewrittenAd(true)" style="display:block;width:100%;padding:11px;background:#6366f1;color:white;border:none;border-radius:8px;font-weight:700;cursor:pointer;margin-top:8px;font-size:.92rem;">
                    🔬 Use &amp; Verify Scores
                </button>
            </div>
        </div>
        ${voiceoverHTML}`;

    // Apply scam warning / scores warning / delta masking via patch hook
    if (typeof window._onRewriteResultPatch === 'function') {
        window._onRewriteResultPatch(d);
    }
}

window.copyVoiceScript = function() {
    const text = document.getElementById('cleanScriptStore')?.textContent || '';
    navigator.clipboard.writeText(text).then(() => {
        const btn = document.querySelector('[onclick="copyVoiceScript()"]');
        if (btn) { btn.textContent = '✅ Copied!'; setTimeout(() => btn.textContent = '📋 Copy Clean Script for ElevenLabs', 2000); }
    });
};

window.useRewrittenAd = function(andVerify = false) {
    const text = document.getElementById('rewrittenText')?.innerText || '';
    const vs = document.getElementById('videoScript');
    const ac = document.getElementById('adCopy');
    // Put text into whichever field has content, or default to ad copy
    if (vs && vs.value.trim()) vs.value = text;
    else if (ac) ac.value = text;

    if (andVerify) {
        // Expand form so user can see it, then auto-submit
        const wrapper = document.getElementById('formWrapper');
        if (wrapper && wrapper.classList.contains('collapsed')) toggleForm();
        window.scrollTo({ top: 0, behavior: 'smooth' });
        // Short delay so the form is visible before submit
        setTimeout(() => {
            const form = document.getElementById('analyzerForm');
            if (form) form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
        }, 400);
    } else {
        window.scrollTo({ top: 0, behavior: 'smooth' });
        const btn = document.querySelector('.use-rewrite-btn');
        if (btn) { btn.textContent = '✅ Loaded into form!'; setTimeout(() => btn.textContent = '📋 Use This Version', 2500); }
    }
};

// ══════════════════════════════════════════════════════════════
// HOOKS LIBRARY
// ══════════════════════════════════════════════════════════════
window.loadHooks = async function() {
    const industry = document.getElementById('hooksIndustryFilter')?.value || '';
    const type     = document.getElementById('hooksTypeFilter')?.value || '';
    const platform = document.getElementById('hooksPlatformFilter')?.value || '';
    const diff     = document.getElementById('hooksDiffFilter')?.value || '';

    if (!industry && !type && !platform && !diff) {
        showEmpty('hooksContainer', 'Select at least one filter above to browse hooks.');
        return;
    }

    const params = new URLSearchParams();
    if (industry) params.append('industry', industry);
    if (type)     params.append('type', type);
    if (platform) params.append('platform', platform);
    if (diff)     params.append('difficulty', diff);

    showSpinner('hooksContainer', 'Loading hooks…');

    try {
        const r = await fetch('/api/hooks?' + params.toString());
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const result = await r.json();
        if (!result.success) throw new Error('Hooks API error');
        _renderHooks(result.data.grouped, result.data.total);
    } catch(e) {
        showEmpty('hooksContainer', `❌ Could not load hooks: ${e.message}`);
    }
};

window.loadRandomHooks = async function() {
    const industry = document.getElementById('hooksIndustryFilter')?.value || '';
    const url = '/api/hooks/random?count=8' + (industry ? `&industry=${industry}` : '');
    showSpinner('hooksContainer', 'Picking random hooks…');
    try {
        const r = await fetch(url);
        const result = await r.json();
        if (!result.success) throw new Error('Failed');
        _renderHooks({ '🎲 Random Selection': result.data.hooks }, result.data.hooks.length);
    } catch(e) {
        showEmpty('hooksContainer', `❌ ${e.message}`);
    }
};

function _renderHooks(grouped, total) {
    const c = document.getElementById('hooksContainer');
    if (!c) return;
    if (!grouped || Object.keys(grouped).length === 0) {
        c.innerHTML = '<p style="color:#9ca3af;">No hooks match your filters. Try broadening the search.</p>';
        return;
    }
    const typeColors = {
        fear:             '#fee2e2',
        curiosity:        '#ede9fe',
        social_proof:     '#d1fae5',
        pattern_interrupt:'#fef3c7',
        authority:        '#dbeafe',
    };
    let html = `<p style="color:#9ca3af;font-size:.85rem;margin-bottom:16px;">${total} hook${total!==1?'s':''} — click to copy</p>`;
    for (const [groupName, hooks] of Object.entries(grouped)) {
        html += `<div style="font-weight:700;margin:20px 0 10px;padding-bottom:8px;border-bottom:2px solid #f3f4f6;">${groupName} (${hooks.length})</div>`;
        hooks.forEach(h => {
            const bg = typeColors[h.type] || '#f3f4f6';
            const safeText = (h.text||'').replace(/'/g,"&#39;").replace(/"/g,"&quot;");
            html += `
                <div class="hook-card" onclick="copyHook(this)" data-text="${safeText}"
                     style="background:white;border:2px solid #e5e7eb;border-radius:12px;padding:18px;margin-bottom:10px;cursor:pointer;position:relative;transition:all .2s;"
                     onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='#e5e7eb'">
                    <span style="position:absolute;top:12px;right:14px;font-size:.72rem;color:#9ca3af;">Click to copy</span>
                    <div style="font-size:1rem;font-weight:500;color:#111827;line-height:1.5;margin-bottom:10px;">${h.text||''}</div>
                    <div style="display:flex;gap:6px;flex-wrap:wrap;">
                        <span style="background:${bg};padding:3px 10px;border-radius:12px;font-size:.74rem;font-weight:600;">${(h.type||'').replace(/_/g,' ')}</span>
                        <span style="background:#f3f4f6;padding:3px 10px;border-radius:12px;font-size:.74rem;">${h.platform||''}</span>
                        <span style="background:#f3f4f6;padding:3px 10px;border-radius:12px;font-size:.74rem;">${h.difficulty||''}</span>
                    </div>
                    ${h.why_it_works ? `<div style="font-size:.82rem;color:#9ca3af;margin-top:8px;font-style:italic;">💡 ${h.why_it_works}</div>` : ''}
                </div>`;
        });
    }
    c.innerHTML = html;
}

window.copyHook = function(card) {
    const text = card.dataset.text;
    navigator.clipboard.writeText(text).then(() => {
        card.style.borderColor = '#10b981';
        card.style.background  = '#ecfdf5';
        const hint = card.querySelector('span:first-child') || card.querySelector('[style*="position:absolute"]');
        const origHint = hint?.textContent || 'Click to copy';
        if (hint) hint.textContent = '✅ Copied!';
        setTimeout(() => {
            card.style.borderColor = '#e5e7eb';
            card.style.background  = 'white';
            if (hint) hint.textContent = origHint;
        }, 2000);
    });
};

// ══════════════════════════════════════════════════════════════
// COMPLIANCE CHECKER
// ══════════════════════════════════════════════════════════════
async function _runComplianceCheck(silent = false) {
    const content = getContent();
    if (!content) {
        if (!silent) showEmpty('complianceOutput', '⚠️ Run an analysis first to scan compliance.');
        return;
    }

    const btn = document.getElementById('complianceRunBtn');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Scanning…'; }
    if (!silent) showSpinner('complianceOutput', 'Scanning compliance rules…');

    try {
        const fd = new FormData();
        fd.append('ad_copy',        content);
        fd.append('platform',       getPlatform());
        fd.append('industry',       getIndustry());
        fd.append('target_country', getCountry());

        const r = await fetch('/api/compliance', { method: 'POST', body: fd });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const result = await r.json();
        if (!result.success) throw new Error('Compliance check failed');
        _renderComplianceResult(result.data);
    } catch(e) {
        showEmpty('complianceOutput', `❌ ${e.message}`);
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = '🔍 Run Compliance Scan'; }
    }
}

window.runComplianceCheck = () => _runComplianceCheck(false);

function _renderComplianceResult(d) {
    const out = document.getElementById('complianceOutput');
    if (!out) return;
    const risk       = d.overall_risk || 'Low';
    const pct        = parseInt(d.approval_likelihood) || 80;
    const violations = d.violations || [];
    const sevOrder   = { critical: 0, high: 1, medium: 2, low: 3 };
    violations.sort((a,b) => (sevOrder[a.severity]||3) - (sevOrder[b.severity]||3));

    const sevColors  = { critical:'#7f1d1d', high:'#ef4444', medium:'#f59e0b', low:'#10b981' };
    const riskColors = { Low:'#d1fae5;color:#065f46', Medium:'#fef3c7;color:#92400e', High:'#fee2e2;color:#991b1b', Critical:'#7f1d1d;color:white' };

    const vHtml = violations.length
        ? violations.map(v => `
            <div style="border-left:4px solid ${sevColors[v.severity]||'#6b7280'};background:white;border-radius:0 8px 8px 0;padding:14px;margin-bottom:8px;">
                <span style="background:${sevColors[v.severity]};color:white;padding:2px 8px;border-radius:4px;font-size:.72rem;font-weight:700;">${v.severity.toUpperCase()}</span>
                <div style="font-weight:600;margin:6px 0;">${v.rule}</div>
                <div style="font-size:.85rem;color:#374151;">Platform: ${v.platform}</div>
                <div style="font-size:.85rem;color:#10b981;margin-top:4px;">✅ Fix: ${v.fix}</div>
            </div>`).join('')
        : '<p style="color:#10b981;">✅ No violations detected.</p>';

    out.innerHTML = `
        <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:16px;">
            <span style="display:inline-block;padding:8px 20px;border-radius:20px;font-weight:700;font-size:1.05rem;background:${riskColors[risk]||riskColors.Low};">${risk} Risk</span>
            <div style="flex:1;">
                <div style="font-size:.85rem;color:#9ca3af;margin-bottom:4px;">Approval likelihood: <strong>${d.approval_likelihood}</strong></div>
                <div style="height:18px;background:#e5e7eb;border-radius:10px;overflow:hidden;">
                    <div style="height:100%;width:${pct}%;background:linear-gradient(90deg,#ef4444 0%,#f59e0b 50%,#10b981 100%);border-radius:10px;transition:width .6s;"></div>
                </div>
            </div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:16px;">
            <div style="background:white;padding:14px;border:1px solid #e5e7eb;border-radius:8px;text-align:center;">
                <div style="font-size:.72rem;color:#9ca3af;text-transform:uppercase;">Total Issues</div>
                <div style="font-size:1.4rem;font-weight:700;">${d.violation_count||0}</div>
            </div>
            <div style="background:white;padding:14px;border:1px solid #e5e7eb;border-radius:8px;text-align:center;">
                <div style="font-size:.72rem;color:#9ca3af;text-transform:uppercase;">Critical</div>
                <div style="font-size:1.4rem;font-weight:700;color:#ef4444;">${d.critical_count||0}</div>
            </div>
            <div style="background:white;padding:14px;border:1px solid #e5e7eb;border-radius:8px;text-align:center;">
                <div style="font-size:.72rem;color:#9ca3af;text-transform:uppercase;">Platform</div>
                <div style="font-size:.95rem;font-weight:700;">${d.platform_checked||''}</div>
            </div>
        </div>
        ${d.required_disclaimer && d.required_disclaimer !== 'None required for this industry/platform combination.' ? `
            <div style="background:#fef3c7;border-left:4px solid #f59e0b;padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:16px;">
                <strong>Required Disclaimer:</strong> ${d.required_disclaimer}
                ${!d.disclaimer_found ? ' <strong style="color:#ef4444;">(⚠ NOT FOUND in your ad)</strong>' : ' <strong style="color:#10b981;">(✅ found)</strong>'}
            </div>` : ''}
        <div style="font-weight:700;margin-bottom:10px;">Violations</div>
        ${vHtml}`;
}

// ══════════════════════════════════════════════════════════════
// PSYCHOGRAPHIC PROFILER
// ══════════════════════════════════════════════════════════════
window.runPsychographic = async function() {
    const niche = document.getElementById('psychoNiche')?.value?.trim();
    if (!niche) { alert('Enter a niche to profile.'); return; }

    const btn = document.getElementById('psychoRunBtn');
    btn.disabled = true; btn.textContent = '⏳ Profiling…';
    showSpinner('psychographicOutput', `Generating deep profiles for "${niche}"…`);

    try {
        const fd = new FormData();
        fd.append('niche',        niche);
        fd.append('country',      document.getElementById('psychoCountry')?.value || getCountry());
        fd.append('age_range',    document.getElementById('psychoAge')?.value || '25-34');
        fd.append('income_level', 'middle');
        fd.append('platform',     getPlatform());

        const r = await fetch('/api/psychographic', { method: 'POST', body: fd });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const result = await r.json();
        if (!result.success) throw new Error('Profiler failed');
        _renderPsychographic(result.data);
    } catch(e) {
        showEmpty('psychographicOutput', `❌ ${e.message}`);
    } finally {
        btn.disabled = false; btn.textContent = '🧬 Generate Profiles';
    }
};

function _renderPsychographic(d) {
    const out = document.getElementById('psychographicOutput');
    if (!out) return;
    const profiles = d.profiles || [];
    const html = profiles.map(p => `
        <div style="background:white;border:2px solid #e5e7eb;border-radius:12px;padding:20px;margin-bottom:14px;">
            <div style="font-size:1.05rem;font-weight:700;">${p.name||''}, ${p.age||''}</div>
            <div style="color:#9ca3af;font-size:.85rem;margin-bottom:12px;">${p.occupation||''} — ${p.city||''}</div>
            <div style="font-style:italic;color:#6366f1;border-left:3px solid #6366f1;padding-left:10px;margin:10px 0;">"${p.their_exact_words||''}"</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px;">
                <div><div style="font-size:.72rem;text-transform:uppercase;color:#9ca3af;font-weight:600;margin-bottom:4px;">Deepest Fear</div><div>${p.deepest_fear||''}</div></div>
                <div><div style="font-size:.72rem;text-transform:uppercase;color:#9ca3af;font-weight:600;margin-bottom:4px;">Dream Outcome</div><div>${p.dream_outcome||''}</div></div>
                <div><div style="font-size:.72rem;text-transform:uppercase;color:#9ca3af;font-weight:600;margin-bottom:4px;">Instant Buy Trigger</div><div style="color:#10b981;font-weight:600;">${p.instant_buy_trigger||''}</div></div>
                <div><div style="font-size:.72rem;text-transform:uppercase;color:#9ca3af;font-weight:600;margin-bottom:4px;">Willingness to Pay</div><div style="font-weight:700;">${p.willingness_to_pay||''}</div></div>
            </div>
            ${p.top_objections?.length ? `<div style="margin-top:12px;"><div style="font-size:.72rem;text-transform:uppercase;color:#9ca3af;font-weight:600;margin-bottom:4px;">Top Objections</div><ul style="margin-left:16px;font-size:.88rem;">${p.top_objections.map(o=>`<li>${o}</li>`).join('')}</ul></div>` : ''}
        </div>`).join('');
    out.innerHTML = html + (d.market_insight ? `<div style="padding:14px;background:#f0f9ff;border-left:4px solid #3b82f6;border-radius:0 8px 8px 0;margin-top:8px;"><strong>Market Insight:</strong> ${d.market_insight}</div>` : '');
}

// ══════════════════════════════════════════════════════════════
// STORYBOARD GENERATOR
// ══════════════════════════════════════════════════════════════
window.runStoryboard = async function() {
    const script = getContent();
    if (!script) {
        showEmpty('storyboardOutput', '⚠️ Run an analysis first — the storyboard generator uses your analysed script.');
        return;
    }

    const btn = document.getElementById('storyboardRunBtn');
    btn.disabled = true; btn.textContent = '⏳ Building…';
    showSpinner('storyboardOutput', 'Building your shot-by-shot storyboard…');

    try {
        const fd = new FormData();
        fd.append('script',            script);
        fd.append('platform',          getPlatform());
        fd.append('style',             document.getElementById('storyboardStyle')?.value || 'ugc');
        fd.append('duration_seconds',  document.getElementById('storyboardDuration')?.value || '30');

        const r = await fetch('/api/storyboard', { method: 'POST', body: fd });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const result = await r.json();
        if (!result.success) throw new Error('Storyboard failed');
        _renderStoryboard(result.data);
    } catch(e) {
        showEmpty('storyboardOutput', `❌ ${e.message}`);
    } finally {
        btn.disabled = false; btn.textContent = '🎬 Generate Storyboard';
    }
};

function _renderStoryboard(d) {
    const out = document.getElementById('storyboardOutput');
    if (!out) return;
    const shots = (d.shots || []).map(s => `
        <div style="background:white;border:2px solid #e5e7eb;border-radius:12px;padding:20px;margin-bottom:12px;display:grid;grid-template-columns:56px 1fr;gap:16px;">
            <div style="background:#6366f1;color:white;border-radius:50%;width:44px;height:44px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:1.1rem;flex-shrink:0;">${s.shot_number}</div>
            <div>
                <div style="font-size:.72rem;color:#9ca3af;font-weight:600;margin-bottom:4px;">${s.timecode||''}</div>
                <span style="background:#f3f4f6;padding:3px 10px;border-radius:6px;font-size:.8rem;margin-bottom:8px;display:inline-block;">📷 ${s.shot_type||''}</span>
                <div style="margin:6px 0;font-size:.9rem;">${s.visual_description||''}</div>
                ${s.script_line ? `<div style="font-style:italic;color:#6366f1;margin:4px 0;">🎙 "${s.script_line}"</div>` : ''}
                ${s.on_screen_text ? `<span style="background:#111827;color:white;padding:4px 10px;border-radius:4px;font-size:.82rem;display:inline-block;margin:4px 0;">💬 ${s.on_screen_text}</span>` : ''}
                ${s.broll ? `<div style="font-size:.82rem;color:#3b82f6;margin-top:4px;">📹 B-Roll: ${s.broll}</div>` : ''}
                ${s.director_note ? `<div style="color:#f59e0b;font-weight:600;font-size:.82rem;margin-top:4px;">🎬 ${s.director_note}</div>` : ''}
            </div>
        </div>`).join('');

    const equip = (d.equipment_needed||[]).map(e => `<span style="background:#f3f4f6;padding:4px 10px;border-radius:6px;font-size:.82rem;margin:3px;display:inline-block;">${e}</span>`).join('');
    out.innerHTML = `
        ${d.opening_direction ? `<div style="padding:14px;background:#f0f9ff;border-left:4px solid #3b82f6;border-radius:0 8px 8px 0;margin-bottom:20px;"><strong>Director's Note:</strong> ${d.opening_direction}</div>` : ''}
        ${shots}
        ${equip ? `<div style="margin-top:16px;"><strong>Equipment:</strong><br>${equip}</div>` : ''}
        ${d.editing_notes ? `<div style="margin-top:14px;padding:14px;background:#f9fafb;border-radius:8px;font-size:.9rem;"><strong>Editing Notes:</strong> ${d.editing_notes}</div>` : ''}
        ${d.caption_strategy ? `<div style="margin-top:10px;padding:14px;background:#eff6ff;border-radius:8px;font-size:.9rem;"><strong>Caption Strategy:</strong> ${d.caption_strategy}</div>` : ''}`;
}

// ══════════════════════════════════════════════════════════════
// BENCHMARKS
// ══════════════════════════════════════════════════════════════
window.loadBenchmarks = async function() {
    const country  = document.getElementById('benchCountry')?.value  || 'nigeria';
    const industry = document.getElementById('benchIndustry')?.value || 'finance';
    showSpinner('benchmarksOutput', 'Loading market benchmarks…');
    try {
        const r = await fetch(`/api/benchmarks?country=${country}&industry=${industry}`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const result = await r.json();
        if (!result.success) throw new Error(result.error || 'No data');
        _renderBenchmarks(result.data.benchmarks);
    } catch(e) {
        showEmpty('benchmarksOutput', `❌ ${e.message}`);
    }
};

function _renderBenchmarks(b) {
    const out = document.getElementById('benchmarksOutput');
    if (!out) return;
    const data    = getData();
    const score   = data?.scores?.overall || null;
    const yourRoas = score ? (score / 35).toFixed(1) : null;

    const cards = [
        { val: b.avg_ctr,             label: 'Industry Avg CTR' },
        { val: b.avg_cpm,             label: 'Avg CPM' },
        { val: b.avg_cpa,             label: 'Avg CPA' },
        { val: b.avg_roas,            label: 'Industry Avg ROAS' },
        { val: b.top_performer_roas,  label: 'Top Performer ROAS' },
        { val: b.hook_stop_rate,      label: 'Hook Stop Rate' },
        { val: b.avg_watch_time,      label: 'Avg Watch Time' },
        { val: b.best_day,            label: 'Best Day' },
        { val: b.best_time,           label: 'Best Time' },
    ].filter(c => c.val);

    const yourCard = yourRoas ? `
        <div style="background:white;border:2px solid #6366f1;border-radius:12px;padding:18px;text-align:center;">
            <div style="font-size:1.6rem;font-weight:700;color:#6366f1;">${yourRoas}×</div>
            <div style="font-size:.76rem;color:#9ca3af;text-transform:uppercase;margin-top:4px;">Your Prediction</div>
            <div style="font-size:.82rem;color:${parseFloat(yourRoas)>=1.5?'#10b981':'#ef4444'};margin-top:6px;">${parseFloat(yourRoas)>=1.5?'✅ Above avg':'⚠ Below avg'}</div>
        </div>` : '';

    const cardsHtml = cards.map(c => `
        <div style="background:white;border:2px solid #e5e7eb;border-radius:12px;padding:18px;text-align:center;">
            <div style="font-size:1.55rem;font-weight:700;color:#6366f1;">${c.val}</div>
            <div style="font-size:.76rem;color:#9ca3af;text-transform:uppercase;margin-top:4px;">${c.label}</div>
        </div>`).join('');

    out.innerHTML = `
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-bottom:16px;">${yourCard}${cardsHtml}</div>
        ${b.audience_size_estimate ? `<div style="padding:12px 16px;background:#f9fafb;border-radius:8px;font-size:.88rem;margin-bottom:12px;"><strong>Audience Size:</strong> ${b.audience_size_estimate}</div>` : ''}
        ${b.notes ? `<div style="padding:14px 16px;background:#eff6ff;border-left:4px solid #3b82f6;border-radius:0 8px 8px 0;font-size:.9rem;"><strong>Market Insight:</strong> ${b.notes}</div>` : ''}`;
}

// ══════════════════════════════════════════════════════════════
// A/B RESULT TRACKER
// ══════════════════════════════════════════════════════════════
window.saveAbResult = async function() {
    const content = document.getElementById('abAdContent')?.value?.trim();
    if (!content) { alert('Paste the ad content first.'); return; }

    const fd = new FormData();
    fd.append('ad_content',      content);
    fd.append('platform',        document.getElementById('abPlatform')?.value || 'tiktok');
    fd.append('industry',        getIndustry());
    fd.append('predicted_score', document.getElementById('abPredScore')?.value || '50');
    fd.append('actual_ctr',      document.getElementById('abCtr')?.value   || '');
    fd.append('actual_roas',     document.getElementById('abRoas')?.value  || '');
    fd.append('spend_amount',    document.getElementById('abSpend')?.value || '');
    fd.append('result_label',    document.getElementById('abLabel')?.value || 'testing');

    try {
        const r = await fetch('/api/ab-result', { method: 'POST', body: fd });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const result = await r.json();
        if (!result.success) throw new Error('Save failed');
        // Clear inputs
        ['abAdContent','abCtr','abRoas','abSpend'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
        await loadAbResults();
    } catch(e) { alert('Could not save: ' + e.message); }
};

window.loadAbResults = async function() {
    try {
        const r = await fetch('/api/ab-results');
        if (!r.ok) return;
        const result = await r.json();
        if (!result.success) return;
        _renderAbResults(result.data);
    } catch(_) {}
};

function _renderAbResults(d) {
    const out = document.getElementById('abResultsContainer');
    if (!out) return;
    const results = d.results || [];
    if (!results.length) {
        out.innerHTML = '<p style="color:#9ca3af;">No results logged yet.</p>';
        return;
    }
    const stats = d.stats || {};
    const labelStyle = { winner:'background:#d1fae5;color:#065f46', loser:'background:#fee2e2;color:#991b1b', testing:'background:#fef3c7;color:#92400e' };

    out.innerHTML = `
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin-bottom:16px;">
            <div style="background:white;padding:14px;border:1px solid #e5e7eb;border-radius:8px;text-align:center;"><div style="font-size:.72rem;color:#9ca3af;text-transform:uppercase;">Total</div><div style="font-size:1.3rem;font-weight:700;">${d.total}</div></div>
            <div style="background:white;padding:14px;border:1px solid #e5e7eb;border-radius:8px;text-align:center;"><div style="font-size:.72rem;color:#9ca3af;text-transform:uppercase;">Winners</div><div style="font-size:1.3rem;font-weight:700;color:#10b981;">${stats.winners||0}</div></div>
            <div style="background:white;padding:14px;border:1px solid #e5e7eb;border-radius:8px;text-align:center;"><div style="font-size:.72rem;color:#9ca3af;text-transform:uppercase;">Losers</div><div style="font-size:1.3rem;font-weight:700;color:#ef4444;">${stats.losers||0}</div></div>
            ${stats.avg_actual_roas ? `<div style="background:white;padding:14px;border:1px solid #e5e7eb;border-radius:8px;text-align:center;"><div style="font-size:.72rem;color:#9ca3af;text-transform:uppercase;">Avg ROAS</div><div style="font-size:1.3rem;font-weight:700;">${stats.avg_actual_roas}×</div></div>` : ''}
        </div>
        ${results.slice(0,20).map(r => `
            <div style="display:grid;grid-template-columns:1fr auto auto auto auto;gap:10px;align-items:center;background:white;border:1px solid #e5e7eb;border-radius:8px;padding:12px 16px;margin-bottom:8px;">
                <div style="font-size:.88rem;color:#374151;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${r.ad_snippet}</div>
                <div style="text-align:center;"><div style="font-weight:700;">${r.predicted_score}</div><div style="font-size:.7rem;color:#9ca3af;">Score</div></div>
                <div style="text-align:center;"><div style="font-weight:700;">${r.actual_ctr ? r.actual_ctr+'%' : '—'}</div><div style="font-size:.7rem;color:#9ca3af;">CTR</div></div>
                <div style="text-align:center;"><div style="font-weight:700;">${r.actual_roas ? r.actual_roas+'×' : '—'}</div><div style="font-size:.7rem;color:#9ca3af;">ROAS</div></div>
                <span style="padding:4px 10px;border-radius:12px;font-size:.78rem;font-weight:700;${labelStyle[r.result_label]||labelStyle.testing}">${r.result_label}</span>
            </div>`).join('')}`;
}

// ══════════════════════════════════════════════════════════════
// LANDING PAGE ANALYZER
// ══════════════════════════════════════════════════════════════
window.runLandingAnalysis = async function() {
    const url = document.getElementById('landingUrl')?.value?.trim();
    if (!url) { alert('Enter a URL to analyze.'); return; }

    const btn = document.getElementById('landingRunBtn');
    btn.disabled = true; btn.textContent = '⏳ Analyzing…';
    showSpinner('landingOutput', 'Fetching and analyzing the page…');

    try {
        const fd = new FormData();
        fd.append('url',              url);
        fd.append('industry',         getIndustry());
        fd.append('audience_country', getCountry());

        const r = await fetch('/api/landing-page', { method: 'POST', body: fd });
        if (!r.ok) {
            const err = await r.json().catch(()=>({}));
            throw new Error(err.detail || `HTTP ${r.status}`);
        }
        const result = await r.json();
        if (!result.success) throw new Error(result.detail || 'Analysis failed');
        _renderLandingResult(result.data);
    } catch(e) {
        showEmpty('landingOutput', `❌ ${e.message}`);
    } finally {
        btn.disabled = false; btn.textContent = '🔍 Analyze Page';
    }
};

function _renderLandingResult(d) {
    const out = document.getElementById('landingOutput');
    if (!out) return;
    const scoreCards = [
        { val: d.headline_score,      label: 'Headline' },
        { val: d.cta_score,           label: 'CTA' },
        { val: d.above_fold_score,    label: 'Above Fold' },
        { val: d.trust_signal_score,  label: 'Trust' },
        { val: d.ad_congruence_score, label: 'Ad Match' },
        { val: d.overall_score,       label: 'Overall' },
    ].filter(s => s.val !== undefined);

    const getC = v => v >= 75 ? '#10b981' : v >= 50 ? '#f59e0b' : '#ef4444';
    const scoresHtml = `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin-bottom:16px;">
        ${scoreCards.map(s => `<div style="background:white;border:2px solid ${getC(s.val)};border-radius:10px;padding:14px;text-align:center;"><div style="font-size:1.35rem;font-weight:700;color:${getC(s.val)};">${s.val}</div><div style="font-size:.76rem;color:#9ca3af;">${s.label}</div></div>`).join('')}
    </div>`;

    const blockers = (d.conversion_blockers||[]).map(b => `
        <div style="border-left:4px solid #ef4444;background:white;border-radius:0 8px 8px 0;padding:12px 14px;margin-bottom:8px;">
            <span style="background:#ef4444;color:white;padding:2px 8px;border-radius:4px;font-size:.72rem;font-weight:700;">${b.severity}</span>
            <div style="font-weight:600;margin:4px 0;">${b.issue}</div>
            <div style="font-size:.85rem;color:#10b981;">Fix: ${b.fix}</div>
        </div>`).join('') || '<p style="color:#10b981;">✅ No major blockers.</p>';

    const wins = (d.quick_wins||[]).map(w =>
        `<div style="background:#ecfdf5;border-left:4px solid #10b981;border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:6px;font-size:.9rem;">⚡ ${w}</div>`
    ).join('');

    out.innerHTML = `${scoresHtml}
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:14px 0;">
            <div><strong>Headline:</strong><p style="font-style:italic;color:#374151;margin:4px 0;">"${d.headline_text||'Not extracted'}"</p><p style="font-size:.88rem;">${d.headline_verdict||''}</p></div>
            <div><strong>CTA:</strong><p style="font-style:italic;color:#6366f1;margin:4px 0;">"${d.cta_text||'Not found'}"</p><p style="font-size:.88rem;">${d.cta_verdict||''}</p></div>
        </div>
        ${d.congruence_verdict ? `<div style="background:#fef3c7;padding:12px 16px;border-radius:8px;margin-bottom:14px;"><strong>Ad-to-Page Match:</strong> ${d.congruence_verdict}</div>` : ''}
        <div style="font-weight:700;margin-bottom:8px;">🚧 Conversion Blockers</div>${blockers}
        ${wins ? `<div style="margin-top:14px;"><div style="font-weight:700;margin-bottom:8px;">⚡ Quick Wins</div>${wins}</div>` : ''}`;
}

// ── CSS for spin animation (injected once) ────────────────────
if (!document.getElementById('adlytics-spin-style')) {
    const s = document.createElement('style');
    s.id = 'adlytics-spin-style';
    s.textContent = '@keyframes spin{to{transform:rotate(360deg)}}';
    document.head.appendChild(s);
}

console.log('✅ ADLYTICS Tier 2 Features v2.0 loaded');
