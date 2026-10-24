/* ==========================================================================
   VENTUREMIND AI - MAIN PLATFORM APPLICATION CONTROLLER
   ========================================================================== */

class VentureMindApp {
  constructor() {
    this.currentView = 'view-landing';
    this.currentTheme = 'dark';
    this.isInvestorMode = false;

    this.init();
  }

  init() {
    this.bindNavigation();
    this.bindCommandPalette();
    this.bindModeToggle();
    this.bindThemeToggle();
    this.checkBackendHealth();

    // Default to Landing Page view
    this.switchView('view-landing');
  }

  async checkBackendHealth() {
    const badge = document.getElementById('backend-health-badge');
    try {
      const res = await fetch(`${window.location.protocol}//${window.location.hostname}:8000/api/health`);
      if (res.ok) {
        const data = await res.json();
        if (badge) {
          badge.className = 'badge badge-success';
          badge.innerHTML = `<i class="fas fa-check-circle"></i> API: ONLINE (v${data.version || '1.0.0'})`;
        }
      } else {
        if (badge) {
          badge.className = 'badge badge-warning';
          badge.innerHTML = `<i class="fas fa-exclamation-triangle"></i> API: ERROR`;
        }
      }
    } catch (err) {
      if (badge) {
        badge.className = 'badge badge-secondary';
        badge.innerHTML = `<i class="fas fa-pause-circle"></i> API: OFFLINE`;
      }
    }
  }

  bindNavigation() {
    document.querySelectorAll('[data-view]').forEach(trigger => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        const viewId = trigger.getAttribute('data-view');
        this.switchView(viewId);
      });
    });
  }

  switchView(viewId) {
    const targetView = document.getElementById(viewId);
    if (!targetView) return;

    // Hide all view sections
    document.querySelectorAll('.view-section').forEach(view => {
      view.classList.remove('active');
    });

    // Show target view
    targetView.classList.add('active');
    this.currentView = viewId;

    // Update Sidebar Navigation Active States
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.remove('active');
      if (item.getAttribute('data-view') === viewId) {
        item.classList.add('active');
      }
    });

    window.scrollTo(0, 0);

    // Trigger chart redraws and view activations if necessary
    if (viewId === 'view-dashboard' && window.ChartEngine) {
      setTimeout(() => ChartEngine.initGauges(), 100);
    } else if (viewId === 'view-simulator' && window.VentureMindSimulator) {
      setTimeout(() => window.VentureMindSimulator.recalculate(), 100);
    } else if (viewId === 'view-results' && window.VentureMindWizard) {
      setTimeout(() => window.VentureMindWizard.onResultsViewActivated(), 50);
    }
  }

  bindCommandPalette() {
    const cmdModal = document.getElementById('cmd-modal');
    const cmdInput = document.getElementById('cmd-input');

    // Ctrl + K / Cmd + K listener
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        this.toggleCommandPalette();
      }
      if (e.key === 'Escape' && cmdModal?.classList.contains('active')) {
        cmdModal.classList.remove('active');
      }
    });

    const triggerBtn = document.getElementById('cmd-palette-trigger');
    if (triggerBtn) {
      triggerBtn.addEventListener('click', () => this.toggleCommandPalette());
    }

    // Command Item Clicks
    document.querySelectorAll('.cmd-item').forEach(item => {
      item.addEventListener('click', () => {
        const targetView = item.getAttribute('data-cmd-view');
        if (targetView) {
          this.switchView(targetView);
          cmdModal?.classList.remove('active');
        }
      });
    });
  }

  toggleCommandPalette() {
    const cmdModal = document.getElementById('cmd-modal');
    const cmdInput = document.getElementById('cmd-input');
    if (!cmdModal) return;

    cmdModal.classList.toggle('active');
    if (cmdModal.classList.contains('active') && cmdInput) {
      cmdInput.value = '';
      cmdInput.focus();
    }
  }

  bindModeToggle() {
    const modeSwitch = document.getElementById('mode-switch-input');
    if (modeSwitch) {
      modeSwitch.addEventListener('change', (e) => {
        this.isInvestorMode = e.target.checked;
        const modeText = document.getElementById('mode-status-text');
        if (modeText) {
          modeText.textContent = this.isInvestorMode ? 'Investor Mode' : 'Founder Mode';
        }
        this.showToast(`Switched to ${this.isInvestorMode ? 'Investor Venture' : 'Founder Operational'} View`, 'info');
      });
    }
  }

  bindThemeToggle() {
    const themeBtn = document.getElementById('theme-toggle-btn');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', this.currentTheme);
        this.showToast(`Theme updated to ${this.currentTheme.toUpperCase()} mode`, 'info');
      });
    }
  }

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';

    const icons = {
      success: 'fa-check-circle',
      warning: 'fa-exclamation-triangle',
      info: 'fa-info-circle'
    };

    const colors = {
      success: '#10b981',
      warning: '#f59e0b',
      info: '#06b6d4'
    };

    toast.innerHTML = `
      <i class="fas ${icons[type] || 'fa-info-circle'}" style="color: ${colors[type]}; font-size: 1.1rem;"></i>
      <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  triggerConfetti() {
    if (window.confetti) {
      window.confetti({
        particleCount: 120,
        spread: 70,
        origin: { y: 0.6 }
      });
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.VentureMindApp = new VentureMindApp();
});
