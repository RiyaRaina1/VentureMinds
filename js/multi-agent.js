/* ==========================================================================
   VENTUREMIND AI - MULTI-AGENT AUTONOMOUS CO-FOUNDER ENGINE
   ========================================================================== */

class MultiAgentSquad {
  constructor() {
    this.agents = [
      { id: 'ceo', name: 'Aria Vane', role: 'Autonomous CEO', avatar: '👑', status: 'Synthesizing Roadmap', confidence: 98, thought: 'Evaluating total addressable market vs. current burn velocity.' },
      { id: 'pm', name: 'Leo Sterling', role: 'Chief Product Officer', avatar: '⚡', status: 'Analyzing Sentiment', confidence: 94, thought: 'Customer retention loop boosted by +18% following v2.4 rollout.' },
      { id: 'tech', name: 'Dr. Orion Vance', role: 'VP of Engineering', avatar: '🛡️', status: 'Auditing Vector DB', confidence: 99, thought: 'Latency down to 14ms across multi-tenant GPU clusters.' },
      { id: 'finance', name: 'Elena Rostova', role: 'Chief Financial Officer', avatar: '📈', status: 'Modeling Cashflow', confidence: 96, thought: 'Series A runway optimized to 22 months with zero debt.' },
      { id: 'mktg', name: 'Kai Thorne', role: 'Head of Growth', avatar: '🚀', status: 'Running Ad Experiments', confidence: 91, thought: 'CAC lowered by $14 via automated LinkedIn AI campaign targeting PMs.' },
      { id: 'investor', name: 'Victoria Cross', role: 'Venture Partner Agent', avatar: '💎', status: 'Preparing Cap Sheet', confidence: 97, thought: 'Valuation multiple estimated at 18x ARR for top-decile AI SaaS.' },
      { id: 'analyst', name: 'Marcus Bell', role: 'Market Intelligence Lead', avatar: '🔍', status: 'Tracking Competitors', confidence: 95, thought: 'Competitor B increased enterprise tier by 25%; opportunity window open.' }
    ];

    this.init();
  }

  init() {
    this.renderSquad();
  }

  renderSquad() {
    const container = document.getElementById('agent-grid-container');
    if (!container) return;

    container.innerHTML = this.agents.map(agent => `
      <div class="glass-card agent-card glass-card-interactive">
        <div class="agent-header">
          <div class="agent-avatar">${agent.avatar}</div>
          <div class="agent-info">
            <h4>${agent.name}</h4>
            <div class="agent-role">${agent.role}</div>
          </div>
          <span class="badge badge-secondary" style="margin-left: auto;">STANDBY</span>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-dim); font-weight: 500;">
          <i class="fas fa-clock" style="font-size: 0.75rem; margin-right: 6px;"></i>Agent Standby (Scheduled for Future Phase)
        </div>
        <div class="agent-thought-box" id="thought-${agent.id}">
          <span style="color: var(--text-dim); margin-right: 6px;">SPECIALIZATION:</span> Autonomous ${agent.role} capabilities configured. Live multi-agent execution will activate after AI integration.
        </div>
        <div style="display: flex; gap: 8px; margin-top: 4px;">
          <button class="btn-secondary" style="padding: 6px 12px; font-size: 0.78rem; flex: 1;" onclick="VentureMindSquad.consultAgent('${agent.id}')">
            <i class="fas fa-info-circle"></i> View Agent Role
          </button>
        </div>
      </div>
    `).join('');
  }

  consultAgent(agentId) {
    const agent = this.agents.find(a => a.id === agentId);
    if (window.VentureMindApp && agent) {
      window.VentureMindApp.showToast(`${agent.name} (${agent.role}) is in standby mode. Autonomous agent execution is scheduled for a future phase.`, 'info');
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.VentureMindSquad = new MultiAgentSquad();
});
