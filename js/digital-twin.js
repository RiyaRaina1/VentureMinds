/* ==========================================================================
   VENTUREMIND AI - HOLOGRAPHIC 3D STARTUP DIGITAL TWIN ENGINE
   Aesthetics: Iron Man Jarvis HUD / Mission Control Network Graph
   ========================================================================== */

class StartupDigitalTwin {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.angleX = 0;
    this.angleY = 0;
    this.rotationSpeed = 0.006;
    this.hoveredNode = null;

    this.nodes = [
      { id: 'core', label: 'AI CORE HUB', value: '100% Synced', type: 'core', radius: 30, color: '#8b5cf6', x: 0, y: 0, z: 0 },
      { id: 'revenue', label: 'MRR Growth', value: '$124,500/mo', type: 'finance', radius: 18, color: '#10b981', x: 180, y: -60, z: 40 },
      { id: 'customers', label: 'Active Users', value: '42,800', type: 'product', radius: 16, color: '#3b82f6', x: -160, y: 80, z: -30 },
      { id: 'competitors', label: 'Market Share', value: '28.4%', type: 'market', radius: 16, color: '#ec4899', x: 140, y: 120, z: -80 },
      { id: 'tech', label: 'System Uptime', value: '99.99%', type: 'tech', radius: 15, color: '#06b6d4', x: -180, y: -90, z: 60 },
      { id: 'investors', label: 'Runway Left', value: '18 Months', type: 'investor', radius: 17, color: '#f59e0b', x: 0, y: 190, z: 20 },
      { id: 'talent', label: 'AI Agents', value: '7 Active', type: 'agents', radius: 14, color: '#a855f7', x: 0, y: -190, z: -40 }
    ];

    this.init();
    this.animate();
    this.bindEvents();
  }

  init() {
    this.resize();
  }

  resize() {
    this.canvas.width = this.canvas.parentElement.clientWidth;
    this.canvas.height = this.canvas.parentElement.clientHeight || 520;
    this.centerX = this.canvas.width / 2;
    this.centerY = this.canvas.height / 2;
  }

  bindEvents() {
    window.addEventListener('resize', () => this.resize());

    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      let found = null;
      this.nodes.forEach(node => {
        if (node.projX && node.projY) {
          const dx = mouseX - node.projX;
          const dy = mouseY - node.projY;
          if (Math.sqrt(dx * dx + dy * dy) < node.radius + 6) {
            found = node;
          }
        }
      });

      this.hoveredNode = found;
      this.canvas.style.cursor = found ? 'pointer' : 'default';
    });

    this.canvas.addEventListener('click', () => {
      if (this.hoveredNode) {
        this.openNodeTelemetry(this.hoveredNode);
      }
    });
  }

  openNodeTelemetry(node) {
    const titleEl = document.getElementById('twin-node-title');
    const valEl = document.getElementById('twin-node-value');
    const descEl = document.getElementById('twin-node-desc');
    const panel = document.getElementById('twin-node-panel');

    if (titleEl && valEl && panel) {
      titleEl.textContent = node.label;
      valEl.textContent = node.value;

      const descriptions = {
        core: 'Central Neural Co-Founder synthesizing multi-agent data streams in real time.',
        revenue: 'MRR expanded +14.2% MoM. Projection engine anticipates $150K next quarter.',
        customers: 'User retention rate at 91.2%. High sentiment score across enterprise cohort.',
        competitors: 'Outperforming nearest 3 rivals in AI deployment speed and pricing efficiency.',
        tech: 'Automated CI/CD pipelines and high-availability vector embeddings active.',
        investors: 'Series A readiness index estimated at 92/100. Valuations scaling smoothly.',
        talent: '7 Autonomous AI Co-Founder agents operational with 99.8% decision alignment.'
      };

      if (descEl) descEl.textContent = descriptions[node.id] || 'Node operating within optimal boundaries.';
      panel.style.display = 'block';
    }
  }

  animate() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    this.angleY += this.rotationSpeed;
    this.angleX += this.rotationSpeed * 0.4;

    const cosY = Math.cos(this.angleY);
    const sinY = Math.sin(this.angleY);
    const cosX = Math.cos(this.angleX);
    const sinX = Math.sin(this.angleX);

    // Calculate 3D Projection for each node
    this.nodes.forEach(node => {
      // Rotate Y
      let x1 = node.x * cosY - node.z * sinY;
      let z1 = node.z * cosY + node.x * sinY;

      // Rotate X
      let y2 = node.y * cosX - z1 * sinX;
      let z2 = z1 * cosX + node.y * sinX;

      // Perspective Scale
      let fov = 400;
      let scale = fov / (fov + z2);

      node.projX = this.centerX + x1 * scale;
      node.projY = this.centerY + y2 * scale;
      node.scale = scale;
      node.zDepth = z2;
    });

    // Sort by Z Depth (Painter's Algorithm)
    const sortedNodes = [...this.nodes].sort((a, b) => b.zDepth - a.zDepth);

    // Draw Connecting Beams to Core
    const coreNode = this.nodes.find(n => n.id === 'core');
    sortedNodes.forEach(node => {
      if (node.id !== 'core') {
        this.ctx.beginPath();
        this.ctx.moveTo(coreNode.projX, coreNode.projY);
        this.ctx.lineTo(node.projX, node.projY);

        const isHovered = this.hoveredNode === node;
        this.ctx.strokeStyle = isHovered ? node.color : 'rgba(59, 130, 246, 0.2)';
        this.ctx.lineWidth = isHovered ? 2.5 : 1;
        this.ctx.setLineDash([4, 4]);
        this.ctx.stroke();
        this.ctx.setLineDash([]);
      }
    });

    // Draw Nodes
    sortedNodes.forEach(node => {
      const isHovered = this.hoveredNode === node;
      const r = node.radius * node.scale * (isHovered ? 1.3 : 1);

      // Glowing Aura
      const grad = this.ctx.createRadialGradient(node.projX, node.projY, 0, node.projX, node.projY, r * 2.5);
      grad.addColorStop(0, node.color);
      grad.addColorStop(1, 'transparent');

      this.ctx.beginPath();
      this.ctx.arc(node.projX, node.projY, r * 2.5, 0, Math.PI * 2);
      this.ctx.fillStyle = grad;
      this.ctx.globalAlpha = 0.4;
      this.ctx.fill();
      this.ctx.globalAlpha = 1.0;

      // Core Solid Dot
      this.ctx.beginPath();
      this.ctx.arc(node.projX, node.projY, r, 0, Math.PI * 2);
      this.ctx.fillStyle = node.color;
      this.ctx.fill();
      this.ctx.strokeStyle = '#ffffff';
      this.ctx.lineWidth = 1.5;
      this.ctx.stroke();

      // Label Text
      this.ctx.fillStyle = isHovered ? '#ffffff' : 'rgba(248, 250, 252, 0.8)';
      this.ctx.font = `${Math.max(10, 12 * node.scale)}px Space Grotesk`;
      this.ctx.textAlign = 'center';
      this.ctx.fillText(node.label, node.projX, node.projY + r + 14);
    });

    requestAnimationFrame(() => this.animate());
  }
}

document.addEventListener('DOMContentLoaded', () => {
  new StartupDigitalTwin('twin-canvas');
});
