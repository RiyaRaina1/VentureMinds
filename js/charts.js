/* ==========================================================================
   VENTUREMIND AI - FUTURISTIC CHART & GAUGE RENDERER ENGINE
   ========================================================================== */

class ChartEngine {
  static initGauges() {
    this.renderGauge('gauge-health', 94, '#3b82f6', '#8b5cf6');
    this.renderGauge('gauge-confidence', 98, '#06b6d4', '#10b981');
    this.renderGauge('gauge-growth', 88, '#8b5cf6', '#ec4899');
    this.renderGauge('gauge-readiness', 92, '#10b981', '#3b82f6');
  }

  static renderGauge(containerId, score, color1, color2) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // SVG Circular Gauge Math
    const radius = 60;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;

    container.innerHTML = `
      <svg class="gauge-svg" viewBox="0 0 160 160">
        <defs>
          <linearGradient id="grad-${containerId}" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="${color1}" />
            <stop offset="100%" stop-color="${color2}" />
          </linearGradient>
        </defs>
        <circle class="gauge-bg" cx="80" cy="80" r="${radius}" />
        <circle class="gauge-fill" cx="80" cy="80" r="${radius}"
                stroke="url(#grad-${containerId})"
                style="stroke-dasharray: ${circumference}; stroke-dashoffset: ${offset};" />
      </svg>
      <div class="gauge-value">
        <div class="gauge-number">${score}</div>
        <div class="gauge-label">INDEX</div>
      </div>
    `;
  }

  static animateCounter(elementId, targetValue, prefix = '', suffix = '') {
    const el = document.getElementById(elementId);
    if (!el) return;

    let start = 0;
    const duration = 1200;
    const startTime = performance.now();

    function step(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(start + easeProgress * (targetValue - start));

      el.textContent = `${prefix}${current.toLocaleString()}${suffix}`;

      if (progress < 1) {
        requestAnimationFrame(step);
      }
    }

    requestAnimationFrame(step);
  }

  // Draw Competitor Radar Chart on HTML5 Canvas
  static drawRadarChart(canvasId, datasets, labels) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement.clientWidth;
    const height = canvas.height = canvas.parentElement.clientHeight || 320;

    ctx.clearRect(0, 0, width, height);

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(centerX, centerY) - 50;
    const numSides = labels.length;

    // Draw Web Grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.lineWidth = 1;

    for (let level = 1; level <= 4; level++) {
      let r = (radius / 4) * level;
      ctx.beginPath();
      for (let i = 0; i < numSides; i++) {
        let angle = (i * 2 * Math.PI) / numSides - Math.PI / 2;
        let x = centerX + r * Math.cos(angle);
        let y = centerY + r * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.stroke();
    }

    // Draw Axes & Labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = '12px Space Grotesk';
    ctx.textAlign = 'center';

    for (let i = 0; i < numSides; i++) {
      let angle = (i * 2 * Math.PI) / numSides - Math.PI / 2;
      let x = centerX + radius * Math.cos(angle);
      let y = centerY + radius * Math.sin(angle);

      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(x, y);
      ctx.stroke();

      let labelX = centerX + (radius + 24) * Math.cos(angle);
      let labelY = centerY + (radius + 20) * Math.sin(angle);
      ctx.fillText(labels[i], labelX, labelY);
    }

    // Draw Datasets
    datasets.forEach(ds => {
      ctx.beginPath();
      ds.values.forEach((val, i) => {
        let angle = (i * 2 * Math.PI) / numSides - Math.PI / 2;
        let r = (val / 100) * radius;
        let x = centerX + r * Math.cos(angle);
        let y = centerY + r * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.fillStyle = ds.fillColor;
      ctx.fill();
      ctx.strokeStyle = ds.strokeColor;
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  }

  // Draw Animated Multi-Line Growth Chart
  static drawGrowthChart(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement.clientWidth;
    const height = canvas.height = 260;

    ctx.clearRect(0, 0, width, height);

    const data = [12, 28, 45, 62, 95, 140, 210, 340];
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'];

    const padding = 40;
    const graphWidth = width - padding * 2;
    const graphHeight = height - padding * 2;

    const maxVal = Math.max(...data) * 1.1;

    // Gradient Area Fill
    const grad = ctx.createLinearGradient(0, padding, 0, height - padding);
    grad.addColorStop(0, 'rgba(59, 130, 246, 0.4)');
    grad.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

    ctx.beginPath();
    data.forEach((val, i) => {
      let x = padding + (i / (data.length - 1)) * graphWidth;
      let y = height - padding - (val / maxVal) * graphHeight;
      if (i === 0) ctx.moveTo(x, y);
      else {
        let prevX = padding + ((i - 1) / (data.length - 1)) * graphWidth;
        let prevY = height - padding - (data[i - 1] / maxVal) * graphHeight;
        let cx = (prevX + x) / 2;
        ctx.bezierCurveTo(cx, prevY, cx, y, x, y);
      }
    });

    ctx.lineTo(width - padding, height - padding);
    ctx.lineTo(padding, height - padding);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Draw Smooth Line
    ctx.beginPath();
    data.forEach((val, i) => {
      let x = padding + (i / (data.length - 1)) * graphWidth;
      let y = height - padding - (val / maxVal) * graphHeight;
      if (i === 0) ctx.moveTo(x, y);
      else {
        let prevX = padding + ((i - 1) / (data.length - 1)) * graphWidth;
        let prevY = height - padding - (data[i - 1] / maxVal) * graphHeight;
        let cx = (prevX + x) / 2;
        ctx.bezierCurveTo(cx, prevY, cx, y, x, y);
      }
    });
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 35;
    ctx.lineWidth = 3;
    ctx.shadowBlur = 15;
    ctx.shadowColor = '#3b82f6';
    ctx.stroke();

    // Draw Data Dots & Labels
    data.forEach((val, i) => {
      let x = padding + (i / (data.length - 1)) * graphWidth;
      let y = height - padding - (val / maxVal) * graphHeight;

      ctx.beginPath();
      ctx.arc(x, y, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#06b6d4';
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Month Label
      ctx.fillStyle = '#64748b';
      ctx.font = '11px Inter';
      ctx.textAlign = 'center';
      ctx.fillText(months[i], x, height - 12);
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  ChartEngine.initGauges();
  ChartEngine.drawGrowthChart('chart-growth-line');

  // Competitor Radar Initial Call
  ChartEngine.drawRadarChart('chart-competitor-radar', [
    {
      values: [85, 90, 75, 95, 80],
      fillColor: 'rgba(59, 130, 246, 0.25)',
      strokeColor: '#3b82f6'
    },
    {
      values: [60, 70, 85, 65, 90],
      fillColor: 'rgba(236, 72, 153, 0.25)',
      strokeColor: '#ec4899'
    }
  ], ['Market Share', 'Tech Velocity', 'Pricing Power', 'AI Capability', 'CSAT Index']);
});
