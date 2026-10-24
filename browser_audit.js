/**
 * VentureMind AI - Headless Browser Automation Audit (Step 15)
 * Connects to Headless Chrome via CDP over native WebSocket.
 * Monitors Console Errors, Page Exceptions, Network Failures,
 * and executes navigation across all platform views.
 */

const { spawn } = require('child_process');
const http = require('http');

async function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function getJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); } catch (e) { reject(e); }
      });
    }).on('error', reject);
  });
}

async function runAudit() {
  console.log("Launching Headless Chrome for Step 15 Browser Audit...");

  const targetUrl = "http://127.0.0.1:5500/index.html";
  const chromePath = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
  const chromeProc = spawn(chromePath, [
    "--headless=new",
    "--remote-debugging-port=9222",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    targetUrl
  ]);

  let closed = false;
  chromeProc.on('exit', () => { closed = true; });

  // Wait for Chrome to bind port 9222
  let targets = null;
  for (let i = 0; i < 20; i++) {
    await wait(400);
    try {
      targets = await getJson("http://127.0.0.1:9222/json");
      if (targets && targets.length > 0) break;
    } catch (e) {}
  }

  if (!targets || targets.length === 0) {
    console.error("Could not find Chrome CDP target");
    chromeProc.kill();
    process.exit(1);
  }

  const pageTarget = targets.find(t => t.type === 'page') || targets[0];
  console.log("Found Page Target:", pageTarget.title, pageTarget.url);

  const wsUrl = pageTarget.webSocketDebuggerUrl;
  const ws = new WebSocket(wsUrl);

  const consoleLogs = [];
  const errors = [];
  const networkResponses = [];
  let reqId = 1;
  const pending = new Map();

  function sendCmd(method, params = {}) {
    return new Promise((resolve) => {
      const id = reqId++;
      pending.set(id, resolve);
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  await new Promise(resolve => ws.onopen = resolve);

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg.result);
      pending.delete(msg.id);
    }
    if (msg.method === 'Runtime.consoleAPICalled') {
      const text = msg.params.args.map(a => a.value || a.description).join(' ');
      consoleLogs.push(`[${msg.params.type}] ${text}`);
      if (msg.params.type === 'error') {
        errors.push(`Console Error: ${text}`);
      }
    }
    if (msg.method === 'Runtime.exceptionThrown') {
      errors.push(`JS Exception: ${msg.params.exceptionDetails.text} at ${msg.params.exceptionDetails.url}:${msg.params.exceptionDetails.lineNumber}`);
    }
    if (msg.method === 'Network.responseReceived') {
      networkResponses.push({
        url: msg.params.response.url,
        status: msg.params.response.status
      });
      if (msg.params.response.status >= 400 && !msg.params.response.url.includes('favicon')) {
        errors.push(`HTTP ${msg.params.response.status} on ${msg.params.response.url}`);
      }
    }
  };

  // Enable CDP domains
  await sendCmd('Runtime.enable');
  await sendCmd('Page.enable');
  await sendCmd('Network.enable');

  console.log("Navigating to target URL and awaiting full initialization...");
  await sendCmd('Page.navigate', { url: targetUrl });

  async function evaluate(expression) {
    const res = await sendCmd('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    return res?.result?.value;
  }

  // Poll until VentureMindApp is ready
  for (let i = 0; i < 30; i++) {
    await wait(300);
    const ready = await evaluate('document.readyState === "complete" && !!window.VentureMindApp');
    if (ready) break;
  }
  await wait(500);

  // 1. Audit View Switching & Navigations
  console.log("\nAuditing Platform Navigation & Views...");
  const views = [
    'view-landing',
    'view-dashboard',
    'view-validation',
    'view-digital-twin',
    'view-competitors',
    'view-product',
    'view-simulator',
    'view-agents',
    'view-chat',
    'view-reports',
    'view-settings'
  ];

  for (const v of views) {
    const switchRes = await evaluate(`(function() {
      if (window.VentureMindApp) {
        window.VentureMindApp.switchView('${v}');
        return document.getElementById('${v}').classList.contains('active');
      }
      return false;
    })()`);
    console.log(`   - Navigation to '${v}': ${switchRes ? 'SUCCESS' : 'FAILED'}`);
  }

  // 2. Audit Theme Switching
  console.log("\nAuditing Theme Switcher...");
  const themeRes = await evaluate(`(function() {
    const btn = document.getElementById('theme-toggle-btn');
    if (btn) btn.click();
    return document.documentElement.getAttribute('data-theme');
  })()`);
  console.log(`   - Theme toggle switched to: ${themeRes}`);

  // 3. Audit Command Palette
  console.log("\nAuditing Command Palette (Ctrl+K)...");
  const cmdRes = await evaluate(`(function() {
    window.VentureMindApp.toggleCommandPalette();
    const active = document.getElementById('cmd-modal').classList.contains('active');
    window.VentureMindApp.toggleCommandPalette();
    return active;
  })()`);
  console.log(`   - Command Palette toggle: ${cmdRes ? 'FUNCTIONAL' : 'FAILED'}`);

  // 4. Audit Backend Health Indicator in Dashboard
  console.log("\nAuditing Backend Health Connectivity Badge...");
  await evaluate(`window.VentureMindApp.switchView('view-dashboard');`);
  await evaluate(`window.VentureMindApp.checkBackendHealth();`);
  await wait(600);
  const healthBadgeText = await evaluate(`document.getElementById('backend-health-badge')?.innerText`);
  console.log(`   - Backend Health Badge in UI: "${healthBadgeText}"`);

  // 5. Audit Business Simulator Lab & Backend Calculation Sync
  console.log("\nAuditing Business Simulator Lab & Live Calculation...");
  await evaluate(`window.VentureMindApp.switchView('view-simulator');`);
  const simResult = await evaluate(`(function() {
    const price = document.getElementById('sim-price');
    if (price) {
      price.value = 99;
      price.dispatchEvent(new Event('input'));
    }
    return {
      priceLabel: document.getElementById('val-sim-price')?.innerText,
      mrrLabel: document.getElementById('sim-res-mrr')?.innerText,
      burnLabel: document.getElementById('sim-res-burn')?.innerText
    };
  })()`);
  console.log(`   - Simulator calculation updated:`, simResult);
  await wait(500);

  // 6. Audit AI Chat Studio Phase 2 Integration
  console.log("\nAuditing AI Chat Studio Phase 2 Behavior & Session List...");
  await evaluate(`window.VentureMindApp.switchView('view-chat');`);
  const chatState = await evaluate(`(function() {
    return {
      hasSessions: document.querySelectorAll('#chat-sessions-list .chat-session-item').length,
      model: document.getElementById('chat-model-select')?.value,
      hasGreeting: document.querySelectorAll('#chat-messages .chat-msg.ai').length > 0
    };
  })()`);
  console.log(`   - AI Chat Studio State:`, chatState);

  // 7. Audit Startup Validation Submission & Persistence
  console.log("\nAuditing Startup Validator Database Persistence...");
  await evaluate(`window.VentureMindApp.switchView('view-validation');`);
  const wizardRes = await evaluate(`(async function() {
    const name = document.getElementById('wizard-startup-name');
    if (name) name.value = "Automated Browser Audit Startup";
    await window.VentureMindWizard.runCinematicScan();
    return true;
  })()`);
  await wait(1800);
  const resultsCardId = await evaluate(`document.getElementById('results-project-id')?.innerText`);
  console.log(`   - Validation Results DB record status: "${resultsCardId}"`);

  // Summary Report
  console.log("\n============================================================");
  console.log("BROWSER AUDIT RESULTS");
  console.log("============================================================");
  console.log(`Total Network Responses Captured: ${networkResponses.length}`);
  console.log(`Total Console Messages: ${consoleLogs.length}`);
  console.log(`Total JavaScript / Runtime Errors: ${errors.length}`);
  if (errors.length > 0) {
    console.log("Errors detected:");
    errors.forEach(e => console.log("  - ", e));
  } else {
    console.log("[PERFECT AUDIT] ZERO JavaScript exceptions, ZERO 404/500 network errors!");
  }
  console.log("============================================================\n");

  ws.close();
  chromeProc.kill();
  process.exit(errors.length > 0 ? 1 : 0);
}

runAudit().catch(err => {
  console.error("Audit runner failed:", err);
  process.exit(1);
});
