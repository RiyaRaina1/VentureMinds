/* ==========================================================================
   VENTUREMIND AI - REAL-TIME BUSINESS SIMULATOR LAB ENGINE
   ========================================================================== */

class BusinessSimulator {
  constructor() {
    this.priceSlider = document.getElementById('sim-price');
    this.mktgSlider = document.getElementById('sim-mktg');
    this.hiringSlider = document.getElementById('sim-hiring');
    this.techSlider = document.getElementById('sim-tech');

    this.init();
  }

  init() {
    [this.priceSlider, this.mktgSlider, this.hiringSlider, this.techSlider].forEach(slider => {
      if (slider) {
        slider.addEventListener('input', () => this.recalculate());
      }
    });

    this.recalculate();
  }

  recalculate() {
    const price = parseFloat(this.priceSlider?.value || 49);
    const mktg = parseFloat(this.mktgSlider?.value || 5000);
    const hiring = parseFloat(this.hiringSlider?.value || 4);
    const tech = parseFloat(this.techSlider?.value || 2500);

    // Update Slider Display Labels
    const valPrice = document.getElementById('val-sim-price');
    const valMktg = document.getElementById('val-sim-mktg');
    const valHiring = document.getElementById('val-sim-hiring');
    const valTech = document.getElementById('val-sim-tech');

    if (valPrice) valPrice.textContent = `$${price}/mo`;
    if (valMktg) valMktg.textContent = `$${mktg.toLocaleString()}/mo`;
    if (valHiring) valHiring.textContent = `${hiring} Engineers`;
    if (valTech) valTech.textContent = `$${tech.toLocaleString()}/mo`;

    // Mathematical Financial Model
    const estCAC = Math.max(35, 120 - (tech / 100));
    const newUsersPerMo = Math.floor(mktg / estCAC);
    const mrr = newUsersPerMo * price * 6; // Cumulative MRR projection
    const monthlyBurn = (hiring * 9500) + mktg + tech + 3000;
    const runway = Math.max(4, Math.floor(500000 / monthlyBurn));
    const netProfit = mrr - monthlyBurn;

    // Update Telemetry Displays
    const elMrr = document.getElementById('sim-res-mrr');
    const elBurn = document.getElementById('sim-res-burn');
    const elRunway = document.getElementById('sim-res-runway');
    const elRisk = document.getElementById('sim-res-risk');

    if (elMrr) elMrr.textContent = `$${Math.round(mrr).toLocaleString()}`;
    if (elBurn) elBurn.textContent = `$${Math.round(monthlyBurn).toLocaleString()}/mo`;
    if (elRunway) elRunway.textContent = `${runway} Months`;

    if (elRisk) {
      if (runway < 8) {
        elRisk.textContent = 'HIGH RISK';
        elRisk.className = 'badge badge-warning';
      } else if (netProfit > 0) {
        elRisk.textContent = 'PROFITABLE';
        elRisk.className = 'badge badge-success';
      } else {
        elRisk.textContent = 'BALANCED';
        elRisk.className = 'badge badge-cyan';
      }
    }

    // Redraw Dynamic Sim Canvas Line
    this.drawSimGraph(mrr, monthlyBurn);

    // Sync with backend deterministic financial calculation API
    this.syncWithBackend({
      price,
      customers: Math.max(1, newUsersPerMo * 6),
      monthly_growth: 15.0,
      churn: 3.5,
      marketing_spend: mktg,
      salaries: hiring * 9500,
      infrastructure_cost: tech,
      other_expenses: 3000,
      cash_balance: 500000
    });
  }

  syncWithBackend(payload) {
    if (this.syncTimeout) clearTimeout(this.syncTimeout);
    this.syncTimeout = setTimeout(async () => {
      try {
        const response = await fetch(`${window.location.protocol}//${window.location.hostname}:8000/api/simulation/run`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (response.ok) {
          const data = await response.json();
          const elMrr = document.getElementById('sim-res-mrr');
          const elBurn = document.getElementById('sim-res-burn');
          const elRunway = document.getElementById('sim-res-runway');
          const elRisk = document.getElementById('sim-res-risk');

          if (elMrr && data.mrr !== undefined) elMrr.textContent = `$${Math.round(data.mrr).toLocaleString()}`;
          if (elBurn && data.monthly_burn !== undefined) elBurn.textContent = `$${Math.round(data.monthly_burn).toLocaleString()}/mo`;
          if (elRunway && data.runway_months !== undefined) elRunway.textContent = `${data.runway_months} Months`;
          if (elRisk && data.status) {
            elRisk.textContent = data.status;
            if (data.status === 'PROFITABLE') elRisk.className = 'badge badge-success';
            else if (data.status === 'HIGH RISK') elRisk.className = 'badge badge-warning';
            else elRisk.className = 'badge badge-cyan';
          }
        }
      } catch (err) {
        // Backend offline or unreachable - local calculation remains active
      }
    }, 300);
  }

  drawSimGraph(mrr, burn) {
    const canvas = document.getElementById('chart-sim-forecast');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width = canvas.parentElement.clientWidth;
    const h = canvas.height = 240;

    ctx.clearRect(0, 0, w, h);

    // Draw grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    for (let y = 30; y < h; y += 40) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    // Draw Revenue Curve
    ctx.beginPath();
    ctx.moveTo(30, h - 30);
    ctx.quadraticCurveTo(w * 0.5, h - 30 - (mrr * 0.0005), w - 30, h - 30 - (mrr * 0.0012));
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 3;
    ctx.stroke();

    // Draw Burn Line
    ctx.beginPath();
    ctx.moveTo(30, h - 30 - (burn * 0.001));
    ctx.lineTo(w - 30, h - 30 - (burn * 0.0011));
    ctx.strokeStyle = '#ec4899';
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 6]);
    ctx.stroke();
    ctx.setLineDash([]);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.VentureMindSimulator = new BusinessSimulator();
});
