/**
 * PayAgent OS — Master Application Entrypoint
 * Modular Orchestration Architecture
 */

import { appState } from './modules/state.js';
import { initI18n, applyLanguage } from './modules/i18n.js';
import { initWorkspaceTabs } from './modules/tabs.js';
import { fetchSummary, fetchAgents, fetchTransactions, initFleetEvents } from './modules/fleet.js';
import { fetchAnalytics, runStressSimulation, initAnalyticsEvents } from './modules/analytics.js';
import { fetchDebts, initP2PEvents } from './modules/p2p.js';
import { fetchSpotRates, fetchArbitrageHistory, initArbitrageEvents } from './modules/arbitrage.js';
import { initToolkitEvents } from './modules/toolkit.js';
import { fetchSecurityData, initSecurityEvents } from './modules/security.js';
import { initCommandCenter, loadVaultSubscriptions, loadFICOScores, loadROIMetrics, loadDepartments, loadDIDCredentials, loadDisputeHistory } from './modules/command_center.js';

// Unified Refresh Orchestrator
export async function refreshAll() {
  await Promise.all([
    fetchSummary(),
    fetchAgents(),
    fetchTransactions(),
    fetchAnalytics(),
    fetchDebts(),
    fetchSpotRates(),
    fetchArbitrageHistory(),
    fetchSecurityData(),
    loadVaultSubscriptions(),
    loadFICOScores(),
    loadROIMetrics(),
    loadDepartments(),
    loadDIDCredentials(),
    loadDisputeHistory(),
  ]);
}

// Make accessible to window if needed
window.refreshAll = refreshAll;

// Bootstrap Application
function initApp() {
  initWorkspaceTabs();
  initI18n();
  initFleetEvents(refreshAll);
  initAnalyticsEvents();
  initP2PEvents(refreshAll);
  initArbitrageEvents(refreshAll);
  initToolkitEvents(refreshAll);
  initSecurityEvents(refreshAll);
  initCommandCenter();

  // Initial Data & Language Boot
  applyLanguage(appState.currentLang);
  refreshAll();
  runStressSimulation();

  // Background Polling Loop (6s)
  setInterval(refreshAll, 6000);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
