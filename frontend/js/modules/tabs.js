/**
 * PayAgent OS — Workspace Tab Navigation Module
 */

import { el } from './state.js';

export function initWorkspaceTabs() {
  const tabButtons = document.querySelectorAll('.tab-nav-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  function activateTab(tabId) {
    tabButtons.forEach((btn) => {
      if (btn.getAttribute('data-tab') === tabId) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    tabPanes.forEach((pane) => {
      if (pane.id === tabId) {
        pane.classList.remove('hidden-tab');
        pane.classList.add('active');
      } else {
        pane.classList.add('hidden-tab');
        pane.classList.remove('active');
      }
    });

    localStorage.setItem('payagent_active_tab', tabId);
  }

  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const tabId = btn.getAttribute('data-tab');
      activateTab(tabId);
    });
  });

  if (el.btnGotoP2p) {
    el.btnGotoP2p.addEventListener('click', () => {
      activateTab('tab-p2p');
    });
  }

  // Restore saved tab or default to tab-fleet-ops
  const validTabs = ['tab-fleet-ops', 'tab-toolkit', 'tab-treasury'];
  let savedTab = localStorage.getItem('payagent_active_tab') || 'tab-fleet-ops';
  if (!validTabs.includes(savedTab)) {
    savedTab = 'tab-fleet-ops';
  }
  if (document.getElementById(savedTab)) {
    activateTab(savedTab);
  }
}
