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
import { initCommandCenter, loadVaultSubscriptions, loadFICOScores, loadROIMetrics, loadDepartments, loadDIDCredentials, loadDisputeHistory, loadFeeSummaryAndHistory, loadLiquidityPoolStatus } from './modules/command_center.js';

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
    loadFeeSummaryAndHistory(),
    loadLiquidityPoolStatus(),
  ]);
}

// Make accessible to window if needed
window.refreshAll = refreshAll;

// Bootstrap Application
function initApp() {
  try { initWorkspaceTabs(); } catch (e) { console.error('WorkspaceTabs init error:', e); }
  try { initI18n(); } catch (e) { console.error('I18n init error:', e); }
  try { initFleetEvents(refreshAll); } catch (e) { console.error('FleetEvents init error:', e); }
  try { initAnalyticsEvents(); } catch (e) { console.error('AnalyticsEvents init error:', e); }
  try { initP2PEvents(refreshAll); } catch (e) { console.error('P2PEvents init error:', e); }
  try { initArbitrageEvents(refreshAll); } catch (e) { console.error('ArbitrageEvents init error:', e); }
  try { initToolkitEvents(refreshAll); } catch (e) { console.error('ToolkitEvents init error:', e); }
  try { initSecurityEvents(refreshAll); } catch (e) { console.error('SecurityEvents init error:', e); }
  try { initCommandCenter(); } catch (e) { console.error('CommandCenter init error:', e); }

  // Initial Data & Language Boot
  try { applyLanguage(appState.currentLang); } catch (e) { console.error('Language boot error:', e); }
  try { refreshAll(); } catch (e) { console.error('RefreshAll initial error:', e); }
  try { runStressSimulation(); } catch (e) { console.error('Stress simulation error:', e); }

  // Background Polling Loop (6s)
  setInterval(() => {
    refreshAll().catch((e) => console.warn('Polling error:', e));
  }, 6000);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
