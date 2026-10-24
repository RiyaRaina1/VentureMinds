/* ==========================================================================
   VENTUREMIND AI - 3-STAGE AI CO-FOUNDER STARTUP VALIDATOR (PHASE 3A)
   ========================================================================== */

class ValidationWizard {
  constructor() {
    this.currentStage = 1; // 1: Idea Input, 2: AI Synthesis, 3: Full Report
    this.backendUrl = `${window.location.protocol}//${window.location.hostname}:8000`;
    this.activeReport = null;
    this.synthesisData = null;
    this.followUpAnswers = {};

    this.bindEvents();
  }

  bindEvents() {
    // Stage 1: Starter Prompt Chips
    document.querySelectorAll('.starter-chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        const prompt = chip.getAttribute('data-prompt');
        const ideaInput = document.getElementById('input-idea-description');
        if (ideaInput && prompt) {
          ideaInput.value = prompt;
          ideaInput.focus();
        }
      });
    });

    // Stage 1: Spark AI Button
    const sparkBtn = document.getElementById('btn-spark-ai');
    if (sparkBtn) {
      sparkBtn.addEventListener('click', () => this.synthesizeIdea());
    }

    // Stage 2: Back to Idea Button
    const backBtn = document.getElementById('btn-back-to-idea');
    if (backBtn) {
      backBtn.addEventListener('click', () => this.goToStage(1));
    }

    // Stage 2: Collapsible Advanced Drawer Toggle
    const toggleAdvancedBtn = document.getElementById('btn-toggle-advanced');
    if (toggleAdvancedBtn) {
      toggleAdvancedBtn.addEventListener('click', () => this.toggleAdvancedDrawer());
    }

    // Stage 2: Generate Full Validation Report Button
    const generateBtn = document.getElementById('btn-generate-full-report');
    if (generateBtn) {
      generateBtn.addEventListener('click', () => this.runFullValidation());
    }

    // Global History Buttons
    const historyBtn = document.getElementById('results-history-btn');
    const valHistoryBtn = document.getElementById('validation-history-btn');
    if (historyBtn) {
      historyBtn.addEventListener('click', () => this.showReportHistoryModal());
    }
    if (valHistoryBtn) {
      valHistoryBtn.addEventListener('click', () => this.showReportHistoryModal());
    }
  }

  toggleAdvancedDrawer() {
    const drawer = document.getElementById('synth-advanced-drawer');
    const chevron = document.getElementById('advanced-chevron');
    if (drawer) {
      drawer.classList.toggle('open');
      if (chevron) {
        chevron.style.transform = drawer.classList.contains('open') ? 'rotate(180deg)' : 'rotate(0deg)';
      }
    }
  }

  goToStage(stageNum) {
    this.currentStage = stageNum;
    const stage1 = document.getElementById('stage-idea-input');
    const stage2 = document.getElementById('stage-ai-synthesis');
    const step1 = document.getElementById('stepper-stage-1');
    const step2 = document.getElementById('stepper-stage-2');
    const step3 = document.getElementById('stepper-stage-3');

    const setStepState = (el, badgeNum, state) => {
      if (!el) return;
      el.className = `stage-step ${state}`.trim();
      const badge = el.querySelector('.stage-badge');
      if (badge) {
        if (state === 'completed') {
          badge.innerHTML = '<i class="fas fa-check"></i>';
        } else {
          badge.textContent = badgeNum;
        }
      }
    };

    if (stageNum === 1) {
      if (stage1) stage1.style.display = 'block';
      if (stage2) stage2.style.display = 'none';
      setStepState(step1, '1', 'active');
      setStepState(step2, '2', '');
      setStepState(step3, '3', '');
    } else if (stageNum === 2) {
      if (stage1) stage1.style.display = 'none';
      if (stage2) stage2.style.display = 'block';
      setStepState(step1, '1', 'completed');
      setStepState(step2, '2', 'active');
      setStepState(step3, '3', '');
    } else if (stageNum === 3) {
      setStepState(step1, '1', 'completed');
      setStepState(step2, '2', 'completed');
      setStepState(step3, '3', 'active');
    }
  }

  /**
   * STAGE 1 -> STAGE 2: Call AI Co-Founder Synthesis Engine
   */
  async synthesizeIdea() {
    const ideaInput = document.getElementById('input-idea-description');
    const nameInput = document.getElementById('input-startup-name');
    const sparkBtn = document.getElementById('btn-spark-ai');

    const ideaText = ideaInput?.value.trim() || '';
    const customName = nameInput?.value.trim() || null;

    if (ideaText.length < 5) {
      if (window.VentureMindApp) {
        window.VentureMindApp.showToast('Please provide at least a few words describing your startup idea.', 'warning');
      }
      ideaInput?.focus();
      return;
    }

    if (sparkBtn) {
      sparkBtn.disabled = true;
      sparkBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Synthesizing Co-Founder Model...';
    }

    try {
      const res = await fetch(`${this.backendUrl}/api/validation/synthesize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          idea_description: ideaText,
          startup_name: customName
        })
      });

      if (!res.ok) {
        let errorMsg = `Synthesis failed (${res.status})`;
        try {
          const errData = await res.json();
          errorMsg = errData.detail || errorMsg;
        } catch (_) { }
        throw new Error(errorMsg);
      }

      const data = await res.json();
      this.synthesisData = data;
      this.followUpAnswers = {};

      // Populate Stage 2 fields
      const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.value = val || '';
      };

      setVal('synth-startup-name', data.startup_name);
      setVal('synth-audience', data.target_customers);
      setVal('synth-problem', data.problem_statement);
      setVal('synth-solution', data.proposed_solution);
      setVal('synth-uvp', data.unique_value_proposition);
      setVal('synth-bizmodel', data.business_model);
      setVal('synth-market', data.geography_market);

      // Render Dynamic Follow-Up Questions
      this.renderFollowUpQuestions(data.follow_up_questions || []);

      // Transition to Stage 2
      this.goToStage(2);

      if (window.VentureMindApp) {
        window.VentureMindApp.showToast('AI Co-Founder understanding synthesized! Review and customize your parameters.', 'success');
      }

    } catch (err) {
      console.error('Synthesis error:', err);
      if (window.VentureMindApp) {
        window.VentureMindApp.showToast(`Synthesis error: ${err.message}`, 'warning');
      }
    } finally {
      if (sparkBtn) {
        sparkBtn.disabled = false;
        sparkBtn.innerHTML = '<i class="fas fa-sparkles"></i> Spark AI Co-Founder Analysis <i class="fas fa-arrow-right" style="margin-left: 6px;"></i>';
      }
    }
  }

  renderFollowUpQuestions(questions) {
    const container = document.getElementById('synth-followups-container');
    const section = document.getElementById('synth-followups-section');
    if (!container) return;

    if (!Array.isArray(questions) || questions.length === 0) {
      if (section) section.style.display = 'none';
      container.innerHTML = '';
      return;
    }

    if (section) section.style.display = 'block';

    container.innerHTML = questions.map((q, qIdx) => {
      const optionsHtml = (Array.isArray(q.options) && q.options.length > 0)
        ? `<div class="followup-pills-row">
            ${q.options.map((opt, optIdx) => `
              <button type="button" class="followup-pill" data-q-idx="${qIdx}" data-option="${this.escapeHtml(opt)}">
                <i class="fas fa-circle-notch" style="font-size: 0.65rem; opacity: 0.6;"></i>
                <span>${this.escapeHtml(opt)}</span>
              </button>
            `).join('')}
          </div>`
        : '';

      const suggestionHtml = q.suggestion
        ? `<div class="followup-suggestion-card" data-q-idx="${qIdx}">
            <div class="followup-suggestion-header">
              <span class="followup-suggestion-label"><i class="fas fa-sparkles"></i> AI Suggestion:</span>
              <span style="color: var(--text-main); font-size: 0.85rem;">${this.escapeHtml(q.suggestion)}</span>
            </div>
            <button type="button" class="btn-apply-suggestion" data-q-idx="${qIdx}" data-suggestion="${this.escapeHtml(q.suggestion)}">
              <i class="fas fa-check"></i> Use Suggestion
            </button>
          </div>`
        : '';

      return `
        <div class="followup-question-box" data-q-idx="${qIdx}">
          <div class="followup-question-text">
            <span class="followup-q-badge">Q${qIdx + 1}</span>
            <span>${this.escapeHtml(q.question)}</span>
          </div>
          ${suggestionHtml}
          ${optionsHtml}
          <input type="text" class="synth-input followup-custom-input" data-q-idx="${qIdx}" placeholder="Or enter your custom clarification / answer...">
        </div>
      `;
    }).join('');

    // Bind click handlers for pills
    container.querySelectorAll('.followup-pill').forEach(pill => {
      pill.addEventListener('click', (e) => {
        const qIdx = pill.getAttribute('data-q-idx');
        const optVal = pill.getAttribute('data-option');
        const customInput = container.querySelector(`.followup-custom-input[data-q-idx="${qIdx}"]`);

        // Deselect sibling pills in this question box
        const siblingPills = container.querySelectorAll(`.followup-pill[data-q-idx="${qIdx}"]`);
        siblingPills.forEach(p => {
          p.classList.remove('selected');
          const icon = p.querySelector('i');
          if (icon) icon.className = 'fas fa-circle-notch';
        });

        pill.classList.add('selected');
        const activeIcon = pill.querySelector('i');
        if (activeIcon) activeIcon.className = 'fas fa-check-circle';

        if (customInput) customInput.value = optVal;
        this.followUpAnswers[qIdx] = {
          question: questions[qIdx]?.question || `Question ${Number(qIdx) + 1}`,
          field_key: questions[qIdx]?.field_key || 'additional_context',
          answer: optVal
        };
      });
    });

    // Bind click handlers for "Use Suggestion" buttons
    container.querySelectorAll('.btn-apply-suggestion').forEach(btn => {
      btn.addEventListener('click', () => {
        const qIdx = btn.getAttribute('data-q-idx');
        const suggestionText = btn.getAttribute('data-suggestion');
        const customInput = container.querySelector(`.followup-custom-input[data-q-idx="${qIdx}"]`);

        if (customInput) {
          customInput.value = suggestionText;
          customInput.focus();
        }

        // Deselect pills since suggestion is used
        const siblingPills = container.querySelectorAll(`.followup-pill[data-q-idx="${qIdx}"]`);
        siblingPills.forEach(p => {
          p.classList.remove('selected');
          const icon = p.querySelector('i');
          if (icon) icon.className = 'fas fa-circle-notch';
        });

        this.followUpAnswers[qIdx] = {
          question: questions[qIdx]?.question || `Question ${Number(qIdx) + 1}`,
          field_key: questions[qIdx]?.field_key || 'additional_context',
          answer: suggestionText
        };

        btn.innerHTML = '<i class="fas fa-check"></i> Applied';
        setTimeout(() => {
          btn.innerHTML = '<i class="fas fa-check"></i> Use Suggestion';
        }, 1500);
      });
    });

    // Bind custom input change
    container.querySelectorAll('.followup-custom-input').forEach(input => {
      input.addEventListener('input', (e) => {
        const qIdx = input.getAttribute('data-q-idx');
        const val = input.value.trim();

        // Deselect pills if user types custom
        const siblingPills = container.querySelectorAll(`.followup-pill[data-q-idx="${qIdx}"]`);
        siblingPills.forEach(p => {
          if (p.getAttribute('data-option') !== val) {
            p.classList.remove('selected');
            const icon = p.querySelector('i');
            if (icon) icon.className = 'fas fa-circle-notch';
          }
        });

        if (val) {
          this.followUpAnswers[qIdx] = {
            question: questions[qIdx]?.question || `Question ${Number(qIdx) + 1}`,
            field_key: questions[qIdx]?.field_key || 'additional_context',
            answer: val
          };
        } else {
          delete this.followUpAnswers[qIdx];
        }
      });
    });
  }

  collectConfirmedData() {
    const getVal = (id) => document.getElementById(id)?.value.trim() || '';

    const name = getVal('synth-startup-name') || 'My Startup';
    const problem = getVal('synth-problem');
    const solution = getVal('synth-solution');
    const audience = getVal('synth-audience');
    const uvp = getVal('synth-uvp');
    const bizmodel = getVal('synth-bizmodel');
    const market = getVal('synth-market');
    const stage = getVal('synth-stage') || 'Pre-product / Idea Validation';
    const competitors = getVal('synth-competitors');
    const tech = getVal('synth-tech');
    const additionalNotes = getVal('synth-additional');

    // Combine advanced info and follow-up answers into rich additional_context
    const contextLines = [];
    if (tech) contextLines.push(`Tech Stack / Architecture: ${tech}`);
    if (additionalNotes) contextLines.push(`Founder Notes / Resources: ${additionalNotes}`);

    // Add follow-up responses
    const answersList = Object.values(this.followUpAnswers);
    if (answersList.length > 0) {
      contextLines.push('Founder Clarifications:');
      answersList.forEach(ans => {
        contextLines.push(`- ${ans.question}: ${ans.answer}`);
      });
    }

    return {
      startup_name: name,
      problem_statement: problem || null,
      proposed_solution: solution || null,
      target_customers: audience || null,
      unique_value_proposition: uvp || null,
      business_model: bizmodel || null,
      budget_resources: null,
      geography_market: market || null,
      startup_stage: stage || null,
      known_competitors: competitors || null,
      additional_context: contextLines.length > 0 ? contextLines.join('\n') : null
    };
  }

  /**
   * STAGE 2 -> STAGE 3: Run Full Validation Pipeline (POST /api/validation/analyze)
   */
  async runFullValidation() {
    const modal = document.getElementById('scanner-modal');
    const statusText = document.getElementById('scan-status-text');
    const generateBtn = document.getElementById('btn-generate-full-report');

    const payload = this.collectConfirmedData();

    if (!payload.startup_name) {
      if (window.VentureMindApp) {
        window.VentureMindApp.showToast('Please provide a startup name.', 'warning');
      }
      return;
    }

    if (generateBtn) generateBtn.disabled = true;
    if (modal) modal.classList.add('active');

    const scanSteps = [
      "Connecting to VentureMind AI Engine...",
      "Analyzing Problem-Solution Fit & ICP Profile...",
      "Stress-Testing Business Model & Unit Economics...",
      "Evaluating Operational Feasibility & Risk Vector...",
      "Computing Deterministic 5-Dimension Score Breakdown...",
      "Persisting Analysis to MySQL Database..."
    ];

    let currentScanIdx = 0;
    if (statusText) statusText.textContent = scanSteps[0];

    const scanInterval = setInterval(() => {
      currentScanIdx++;
      if (currentScanIdx < scanSteps.length) {
        if (statusText) statusText.textContent = scanSteps[currentScanIdx];
      }
    }, 1200);

    try {
      const response = await fetch(`${this.backendUrl}/api/validation/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      clearInterval(scanInterval);

      if (!response.ok) {
        let errorMsg = `Server error (${response.status})`;
        try {
          const errData = await response.json();
          errorMsg = errData.detail || errData.message || errorMsg;
        } catch (_) { }
        throw new Error(errorMsg);
      }

      const reportResponse = await response.json();
      const normalized = this.normalizeReport(reportResponse);
      this.activeReport = normalized;

      if (modal) modal.classList.remove('active');

      this.goToStage(3);
      this.renderResults(normalized);

      if (window.VentureMindApp) {
        const displayScore = normalized.score != null ? (Number.isInteger(normalized.score) ? normalized.score : normalized.score.toFixed(1)) : 0;
        window.VentureMindApp.showToast(
          `AI Validation complete! Overall Score: ${displayScore}/100`,
          'success'
        );
        window.VentureMindApp.switchView('view-results');
        window.VentureMindApp.triggerConfetti();
      }

    } catch (err) {
      clearInterval(scanInterval);
      if (modal) modal.classList.remove('active');

      console.error('Validation engine error:', err);
      if (window.VentureMindApp) {
        window.VentureMindApp.showToast(
          `Validation failed: ${err.message}`,
          'warning'
        );
      }
    } finally {
      if (generateBtn) generateBtn.disabled = false;
    }
  }

  /**
   * Safely normalize the response from either POST /analyze or GET /reports/{id}
   */
  normalizeReport(rawReport) {
    if (!rawReport || typeof rawReport !== 'object') {
      throw new Error('Invalid report payload: Expected an object');
    }

    const report = { ...rawReport };
    let analysis = report.analysis;

    // Handle case where analysis is a serialized JSON string
    if (typeof analysis === 'string') {
      try {
        analysis = JSON.parse(analysis);
      } catch (e) {
        throw new Error(`Failed to parse analysis JSON string: ${e.message}`);
      }
    }

    // Handle case where report itself contains analysis properties directly
    if (!analysis && (report.executive_summary || report.problem_clarity)) {
      analysis = { ...report };
    }

    if (!analysis || typeof analysis !== 'object') {
      throw new Error('Report is missing structured analysis content');
    }

    // Ensure score_breakdown exists
    if (!analysis.score_breakdown || typeof analysis.score_breakdown !== 'object') {
      analysis.score_breakdown = {
        dimensions: [],
        total_score: report.score != null ? report.score : 0,
        score_label: 'Evaluated'
      };
    }

    // Ensure score_breakdown.dimensions is an array
    if (!Array.isArray(analysis.score_breakdown.dimensions)) {
      if (typeof analysis.score_breakdown.dimensions === 'object' && analysis.score_breakdown.dimensions !== null) {
        analysis.score_breakdown.dimensions = Object.values(analysis.score_breakdown.dimensions);
      } else {
        analysis.score_breakdown.dimensions = [];
      }
    }

    // Ensure all list fields are true arrays
    const listFields = [
      'key_risks',
      'strengths',
      'weaknesses',
      'recommended_next_steps',
      'customer_discovery_questions',
      'low_cost_validation_experiments',
      'metrics_to_measure',
      'missing_information',
      'uncertain_assumptions'
    ];

    for (const field of listFields) {
      if (!Array.isArray(analysis[field])) {
        if (typeof analysis[field] === 'string' && analysis[field].trim()) {
          analysis[field] = [analysis[field].trim()];
        } else {
          analysis[field] = [];
        }
      }
    }

    report.analysis = analysis;
    return report;
  }

  renderResults(report) {
    try {
      const normalized = this.normalizeReport(report);
      const analysis = normalized.analysis;

      const setText = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text || '--';
      };

      const setHtml = (id, html) => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = html;
      };

      // Header & Meta
      setText('results-startup-title', analysis.startup_name || normalized.input_summary || 'Startup Validation Report');

      let dateStr = 'Recent';
      if (normalized.created_at) {
        try {
          dateStr = new Date(normalized.created_at).toLocaleString();
        } catch (_) { }
      }
      setText('results-startup-subtitle', `AI Validation Report #${normalized.id || 'N/A'} — Analyzed on ${dateStr}`);

      const statusLabel = (normalized.status || 'completed').toUpperCase();
      setHtml('results-db-status', `<i class="fas fa-check-circle"></i> REPORT #${normalized.id || 'N/A'} PERSISTED (${this.escapeHtml(statusLabel)})`);
      setText('results-project-id', `#${normalized.id || 'N/A'}`);
      setText('results-model-used', normalized.model_used || 'Groq LPU Core');

      // Disclaimer & Evidence
      if (analysis.ai_disclaimer) {
        setText('results-ai-disclaimer', analysis.ai_disclaimer);
      }
      if (analysis.evidence_notes) {
        setHtml('results-evidence-notes', `<i class="fas fa-info-circle"></i> <strong>Evidence & Sources:</strong> ${this.escapeHtml(analysis.evidence_notes)}`);
      }

      // Score & Confidence
      const scoreBreakdown = analysis.score_breakdown || {};
      const totalScore = scoreBreakdown.total_score != null ? scoreBreakdown.total_score : normalized.score;
      const formattedScore = totalScore != null ? (Number.isInteger(totalScore) ? totalScore : totalScore.toFixed(1)) : '--';
      setText('results-score-value', `${formattedScore}/100`);

      const scoreLabel = scoreBreakdown.score_label || 'Evaluated';
      const scoreBadgeEl = document.getElementById('results-score-label');
      if (scoreBadgeEl) {
        scoreBadgeEl.textContent = scoreLabel.toUpperCase();
        if (totalScore >= 80) scoreBadgeEl.className = 'badge badge-success';
        else if (totalScore >= 60) scoreBadgeEl.className = 'badge badge-cyan';
        else if (totalScore >= 40) scoreBadgeEl.className = 'badge badge-warning';
        else scoreBadgeEl.className = 'badge badge-pink';
      }

      // Determine overall confidence
      const dims = Array.isArray(scoreBreakdown.dimensions) ? scoreBreakdown.dimensions : [];
      let avgConfidence = 'MEDIUM';
      if (dims.length > 0) {
        const highCount = dims.filter(d => d.confidence === 'HIGH').length;
        const lowCount = dims.filter(d => d.confidence === 'LOW').length;
        if (highCount >= 3) avgConfidence = 'HIGH';
        else if (lowCount >= 3) avgConfidence = 'LOW';
      }
      setText('results-confidence-value', avgConfidence);

      // 5-Dimension Scoring Breakdown Grid
      const dimContainer = document.getElementById('results-dimensions-grid');
      if (dimContainer) {
        if (dims.length > 0) {
          dimContainer.innerHTML = dims.map(dim => {
            const rawScore = typeof dim.score === 'number' ? dim.score : 0;
            const pct = Math.min(100, Math.max(0, Math.round((rawScore / 20) * 100)));
            const conf = dim.confidence || 'MEDIUM';
            const confColor = conf === 'HIGH' ? 'var(--accent-emerald)' : conf === 'MEDIUM' ? 'var(--accent-cyan)' : 'var(--accent-pink)';
            const weightPct = dim.weight != null ? Math.round(dim.weight * 100) : 20;
            const weightedPts = dim.weighted_score != null ? dim.weighted_score : Math.round(rawScore * (weightPct / 20));

            return `
              <div style="padding: 14px; background: rgba(5, 8, 22, 0.6); border-radius: 12px; border: 1px solid var(--border-color); display: flex; flex-direction: column; justify-content: space-between;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                  <span style="font-weight: 700; font-size: 0.85rem; color: var(--text-main);">${this.escapeHtml(dim.name || 'Dimension')}</span>
                  <span style="font-size: 0.7rem; font-weight: 600; color: ${confColor}; border: 1px solid ${confColor}; padding: 1px 6px; border-radius: 10px;">${this.escapeHtml(conf)}</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px;">
                  <span style="font-size: 1.3rem; font-weight: 800; color: var(--accent-cyan);">${rawScore}<span style="font-size: 0.8rem; color: var(--text-muted);">/20</span></span>
                  <span style="font-size: 0.75rem; color: var(--text-muted);">Weight: ${weightPct}% (+${weightedPts} pts)</span>
                </div>
                <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden; margin-bottom: 8px;">
                  <div style="width: ${pct}%; height: 100%; background: var(--grad-primary); border-radius: 4px;"></div>
                </div>
                <p style="font-size: 0.78rem; color: var(--text-muted); line-height: 1.4; margin: 0;">${this.escapeHtml(dim.rationale || 'No rationale provided.')}</p>
              </div>
            `;
          }).join('');
        } else {
          dimContainer.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No dimension scores available.</p>';
        }
      }

      // Executive Summary
      setText('results-startup-summary', analysis.executive_summary);

      // Deep Analysis Sections
      setText('results-problem-clarity', analysis.problem_clarity);
      setText('results-target-customer', analysis.target_customer_analysis);
      setText('results-value-prop', analysis.value_proposition_assessment);
      setText('results-business-model', analysis.business_model_feasibility);
      setText('results-market-assumptions', analysis.market_assumptions);
      setText('results-tech-feasibility', analysis.technical_operational_feasibility);

      // Lists with type-checked guard
      this.renderList('results-strengths-list', analysis.strengths, 'fa-check', 'var(--accent-emerald)');
      this.renderList('results-weaknesses-list', analysis.weaknesses, 'fa-times', 'var(--accent-pink)');
      this.renderList('results-risks-list', analysis.key_risks, 'fa-exclamation-triangle', 'var(--accent-amber)');
      this.renderList('results-next-steps-list', analysis.recommended_next_steps, 'fa-arrow-right', 'var(--accent-cyan)', true);
      this.renderList('results-questions-list', analysis.customer_discovery_questions, 'fa-question', 'var(--accent-purple)');
      this.renderList('results-experiments-list', analysis.low_cost_validation_experiments, 'fa-vial', 'var(--accent-emerald)');
      this.renderList('results-metrics-list', analysis.metrics_to_measure, 'fa-chart-line', 'var(--accent-blue)');

      // Missing info & uncertain assumptions
      this.renderList('results-missing-info-list', analysis.missing_information, 'fa-info', 'var(--accent-amber)');
      this.renderList('results-uncertain-assumptions-list', analysis.uncertain_assumptions, 'fa-lightbulb', 'var(--accent-pink)');

      // Link startup context to AI Chat Studio
      if (window.VentureMindChat && normalized.startup_id) {
        window.VentureMindChat.setStartupContext(normalized.startup_id, analysis.startup_name || 'Active Startup');
      }

    } catch (err) {
      console.error('Error in renderResults:', err);
      this.renderFallback(report, err.message);
    }
  }

  renderList(elementId, items, iconClass, iconColor, isOrdered = false) {
    const el = document.getElementById(elementId);
    if (!el) return;

    const safeItems = Array.isArray(items) ? items : (typeof items === 'string' && items.trim() ? [items.trim()] : []);

    if (!safeItems.length) {
      el.innerHTML = '<li style="color: var(--text-dim); list-style: none;">None identified.</li>';
      return;
    }

    el.innerHTML = safeItems.map((item, idx) => {
      const prefix = isOrdered
        ? `<span style="font-weight: 700; color: ${iconColor}; margin-right: 6px;">${idx + 1}.</span>`
        : `<i class="fas ${iconClass}" style="color: ${iconColor}; margin-right: 8px; font-size: 0.75rem;"></i>`;
      return `<li style="margin-bottom: 6px; list-style: none;">${prefix}${this.escapeHtml(item)}</li>`;
    }).join('');
  }

  renderFallback(report, errorMessage = null) {
    const setText = (id, text) => {
      const el = document.getElementById(id);
      if (el) el.textContent = text || '--';
    };

    setText('results-startup-title', report?.input_summary || 'Validation Report');
    setText('results-project-id', report?.id ? `#${report.id}` : '--');
    setText('results-db-status', report?.id ? `REPORT #${report.id} (PARTIAL)` : 'NO REPORT LOADED');
    setText('results-score-value', report?.score != null ? `${report.score}/100` : '--/100');

    if (errorMessage) {
      setText('results-startup-summary', `Rendering Notice: ${errorMessage}. Full analysis data could not be parsed.`);
    }
  }

  /**
   * Called whenever the view-results section becomes active
   */
  async onResultsViewActivated() {
    if (this.activeReport && this.activeReport.analysis) {
      this.renderResults(this.activeReport);
      return;
    }
    // If no active report in memory, attempt to fetch the latest full report from MySQL
    await this.loadLatestReport();
  }

  async loadLatestReport() {
    try {
      const listRes = await fetch(`${this.backendUrl}/api/validation/reports?limit=1`);
      if (!listRes.ok) return;
      const reports = await listRes.json();
      if (!Array.isArray(reports) || reports.length === 0) return;

      const latestId = reports[0].id;
      const fullRes = await fetch(`${this.backendUrl}/api/validation/reports/${latestId}`);
      if (!fullRes.ok) return;
      const fullReport = await fullRes.json();
      this.activeReport = this.normalizeReport(fullReport);
      this.renderResults(this.activeReport);
    } catch (err) {
      console.warn('Could not auto-hydrate latest validation report:', err);
    }
  }

  async showReportHistoryModal() {
    try {
      const res = await fetch(`${this.backendUrl}/api/validation/reports?limit=20`);
      if (!res.ok) throw new Error('Failed to fetch reports list');
      const reports = await res.json();

      if (!Array.isArray(reports) || !reports.length) {
        if (window.VentureMindApp) {
          window.VentureMindApp.showToast('No saved validation reports found in MySQL.', 'info');
        }
        return;
      }

      // Fetch the full report for the most recent entry
      const latest = reports[0];
      const fullRes = await fetch(`${this.backendUrl}/api/validation/reports/${latest.id}`);
      if (!fullRes.ok) throw new Error(`Failed to load full report #${latest.id}`);

      const fullReport = await fullRes.json();
      this.activeReport = this.normalizeReport(fullReport);
      this.renderResults(this.activeReport);

      if (window.VentureMindApp) {
        window.VentureMindApp.showToast(`Loaded Report #${latest.id} (${reports.length} total saved)`, 'info');
        window.VentureMindApp.switchView('view-results');
      }
    } catch (err) {
      if (window.VentureMindApp) {
        window.VentureMindApp.showToast(`Error loading reports: ${err.message}`, 'warning');
      }
    }
  }

  escapeHtml(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.VentureMindWizard = new ValidationWizard();
});
