/**
 * PayAgent OS — Fleet Management, HITL Approval Queue & Spending Simulator Module
 */

import { API_BASE, appState, el, showToast } from './state.js';
import { i18n, onLanguageChange } from './i18n.js';

let refreshAllCallback = null;

// Fetch Metrics Summary
export async function fetchSummary() {
  try {
    const res = await fetch(`${API_BASE}/stats/summary`);
    if (!res.ok) return;
    const data = await res.json();

    if (el.statAllocated) {
      el.statAllocated.textContent = data.total_allocated_funds.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    }

    if (el.statPending) {
      el.statPending.textContent = data.pending_approval_count;
      if (data.pending_approval_count > 0) {
        el.statPending.className = 'stat-number text-amber-400';
      } else {
        el.statPending.className = 'stat-number text-muted';
      }
    }

    if (el.statVolume) {
      el.statVolume.textContent = data.total_volume_processed.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    }

    if (el.statAgentsCount) {
      el.statAgentsCount.textContent =
        appState.currentLang === 'tr'
          ? `${data.active_agents_count} Ajan`
          : `${data.active_agents_count} Agents`;
    }

    if (el.badgeHitlCount) {
      if (data.pending_approval_count > 0) {
        el.badgeHitlCount.textContent =
          appState.currentLang === 'tr'
            ? `${data.pending_approval_count} Bekliyor`
            : `${data.pending_approval_count} Pending`;
        el.badgeHitlCount.className = 'count-badge count-badge-amber';
      } else {
        el.badgeHitlCount.textContent = appState.currentLang === 'tr' ? '✓ Temiz' : '✓ Clean';
        el.badgeHitlCount.className = 'count-badge count-badge-clean';
      }
    }

    if (el.tabHitlBadge) {
      if (data.pending_approval_count > 0) {
        el.tabHitlBadge.textContent = data.pending_approval_count;
        el.tabHitlBadge.classList.remove('hidden');
      } else {
        el.tabHitlBadge.classList.add('hidden');
      }
    }

    if (el.paypalConnLabel) {
      if (data.is_live_sandbox) {
        el.paypalConnLabel.textContent =
          appState.currentLang === 'tr'
            ? 'PayPal Sandbox: Canlı Bağlı'
            : 'PayPal Sandbox: Connected';
      } else {
        el.paypalConnLabel.textContent =
          appState.currentLang === 'tr'
            ? 'PayPal Sandbox: Hazır (Simülasyon)'
            : 'PayPal Sandbox: Ready (Dev Simulation)';
      }
    }
  } catch (err) {
    console.error('Failed to fetch summary:', err);
  }
}

// Fetch Agents
export async function fetchAgents() {
  try {
    const res = await fetch(`${API_BASE}/agents`);
    if (!res.ok) return;
    appState.agentsList = await res.json();

    if (el.simAgentSelect) {
      const currentVal = el.simAgentSelect.value;
      el.simAgentSelect.innerHTML = '';
      appState.agentsList.forEach((agent) => {
        const opt = document.createElement('option');
        opt.value = agent.id;
        opt.textContent = `${agent.name} ($${agent.wallet_balance.toFixed(2)})`;
        el.simAgentSelect.appendChild(opt);
      });
      if (currentVal && appState.agentsList.some((a) => a.id === currentVal)) {
        el.simAgentSelect.value = currentVal;
      }
    }

    // Populate P2P Negotiation Selects
    if (el.negRequesterSelect && el.negTargetSelect) {
      const currentReq = el.negRequesterSelect.value || 'agent-research';
      const currentTarget = el.negTargetSelect.value || 'agent-devops';

      el.negRequesterSelect.innerHTML = '';
      el.negTargetSelect.innerHTML = '';

      appState.agentsList.forEach((agent) => {
        const opt1 = document.createElement('option');
        opt1.value = agent.id;
        opt1.textContent = `${agent.name} (Günlük: $${agent.policy.daily_budget.toFixed(2)})`;
        el.negRequesterSelect.appendChild(opt1);

        const surplus = Math.max(0, agent.policy.daily_budget - agent.spent_today);
        const opt2 = document.createElement('option');
        opt2.value = agent.id;
        opt2.textContent = `${agent.name} (Boşta Kalan: $${surplus.toFixed(2)})`;
        el.negTargetSelect.appendChild(opt2);
      });

      if (appState.agentsList.some((a) => a.id === currentReq)) {
        el.negRequesterSelect.value = currentReq;
      }
      if (appState.agentsList.some((a) => a.id === currentTarget)) {
        el.negTargetSelect.value = currentTarget;
      }
    }

    // Populate Arbitrage Bidding Agent Select
    const bidAgentSelect = document.getElementById('bid-agent-select');
    if (bidAgentSelect) {
      const curBidVal = bidAgentSelect.value || 'agent-devops';
      bidAgentSelect.innerHTML = '';
      appState.agentsList.forEach((agent) => {
        const opt = document.createElement('option');
        opt.value = agent.id;
        opt.textContent = `${agent.name} ($${agent.wallet_balance.toFixed(2)})`;
        bidAgentSelect.appendChild(opt);
      });
      if (appState.agentsList.some((a) => a.id === curBidVal)) {
        bidAgentSelect.value = curBidVal;
      }
    }

    renderFleet();
  } catch (err) {
    console.error('Failed to fetch agents:', err);
  }
}

// Render Fleet with Budget Progress Bars
export function renderFleet() {
  if (!el.fleetContainer) return;
  el.fleetContainer.innerHTML = '';
  appState.agentsList.forEach((agent) => {
    const card = document.createElement('div');
    card.className = 'agent-fleet-card';

    const spent = agent.spent_today;
    const dailyCap = agent.policy.daily_budget;
    const pct = Math.min(100, Math.round((spent / dailyCap) * 100));
    const isWarning = pct > 75;

    const vendorTagLabel =
      appState.currentLang === 'tr' ? 'Onaylı Satıcılar:' : 'Approved Vendors:';
    const vendorList = agent.policy.allowed_vendors.length
      ? agent.policy.allowed_vendors.join(' · ')
      : appState.currentLang === 'tr'
      ? 'Tüm Satıcılar (Açık Payout)'
      : 'Open Payout';

    const vendorsHtml = `
      <span class="vendor-meta-label">${vendorTagLabel}</span>
      <span class="vendor-meta-list font-mono">${vendorList}</span>
    `;

    const limitLabel = appState.currentLang === 'tr' ? 'Tekil Limit' : 'Max Per Tx';
    const dailyLabel = appState.currentLang === 'tr' ? 'Günlük Kota' : 'Daily Cap';
    const spentLabel = appState.currentLang === 'tr' ? 'Kullanılan' : 'Spent';

    let persClass = 'pers-balanced';
    let persIcon = '⚖️';
    let persLabel = appState.currentLang === 'tr' ? 'Dengeli Hazine' : 'Balanced';
    if (agent.personality === 'FRUGAL_VAULT') {
      persClass = 'pers-frugal';
      persIcon = '🏦';
      persLabel =
        appState.currentLang === 'tr' ? 'Cimri Kasa (Zor Borç Verir)' : 'Frugal Vault (Strict)';
    } else if (agent.personality === 'GROWTH_EXPLORER') {
      persClass = 'pers-growth';
      persIcon = '🚀';
      persLabel =
        appState.currentLang === 'tr' ? 'Büyüme & Ar-Ge (Cömert)' : 'Growth Explorer';
    }

    card.innerHTML = `
      <div class="agent-card-top">
        <div class="agent-title-row" style="flex-wrap: wrap; gap: 0.45rem;">
          <span class="fleet-status-dot" title="Active"></span>
          <span class="agent-card-title">${agent.name}</span>
          <span class="agent-personality-badge ${persClass}" title="${
      agent.personality_description || ''
    }">
            <span>${persIcon}</span>
            <span>${persLabel}</span>
          </span>
        </div>
        <span class="agent-card-balance font-mono">$${agent.wallet_balance.toFixed(2)}</span>
      </div>

      <div class="budget-bar-wrap">
        <div class="budget-bar-labels font-mono">
          <span>${limitLabel}: $${agent.policy.max_per_transaction.toFixed(2)}</span>
          <span>${spentLabel}: $${spent.toFixed(2)} / $${dailyCap.toFixed(2)} (${pct}%)</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill ${isWarning ? 'warning' : ''}" style="width: ${pct}%;"></div>
        </div>
      </div>

      <div class="vendor-pills-row">
        ${vendorsHtml}
      </div>
    `;
    el.fleetContainer.appendChild(card);
  });
}

// Fetch Transactions
export async function fetchTransactions() {
  try {
    const res = await fetch(`${API_BASE}/payments`);
    if (!res.ok) return;
    appState.transactionsList = await res.json();

    renderHITLQueue();
    renderAuditTable();
  } catch (err) {
    console.error('Failed to fetch transactions:', err);
  }
}

// Render HITL Queue
export function renderHITLQueue() {
  if (!el.hitlContainer) return;
  const pending = appState.transactionsList.filter((t) => t.status === 'PENDING_APPROVAL');
  el.hitlContainer.innerHTML = '';

  if (pending.length === 0) {
    el.hitlContainer.innerHTML = `
      <div class="empty-placeholder">
        <span class="empty-icon">✓</span>
        <span>${i18n[appState.currentLang].noPending}</span>
      </div>
    `;
    return;
  }

  pending.forEach((tx) => {
    const agent = appState.agentsList.find((a) => a.id === tx.agent_id);
    const limit = agent ? agent.policy.max_per_transaction : 0;
    const overAmount = Math.max(0, tx.amount - limit);

    const diffHtml =
      limit > 0
        ? `<div class="diff-breakdown font-mono">
           <span>${appState.currentLang === 'tr' ? 'Talep:' : 'Req:'} <strong>$${tx.amount.toFixed(
            2
          )}</strong></span>
           <span>•</span>
           <span>${appState.currentLang === 'tr' ? 'Limit:' : 'Limit:'} $${limit.toFixed(2)}</span>
           <span>•</span>
           <span style="color: #f87171;">(+$${overAmount.toFixed(2)} ${
            appState.currentLang === 'tr' ? 'Aşım' : 'Over'
          })</span>
         </div>`
        : '';

    const borrowingBannerHtml =
      tx.shortfall_amount && tx.proposed_donor_agent_name
        ? `<div class="borrowing-proposal-banner">
           <div class="proposal-banner-title">
             <span>🤝</span>
             <span>${
               appState.currentLang === 'tr'
                 ? 'Kardeş Karttan Otonom Fonlama Teklifi'
                 : 'Peer Shortfall Borrowing Proposal'
             }</span>
           </div>
           <div class="proposal-banner-text">
             ${
               appState.currentLang === 'tr'
                 ? `Bu harcama ajanın limitini aşıyor (<strong>$${tx.shortfall_amount.toFixed(
                     2
                   )} eksik</strong>). Sistem, boşta bütçesi olan <span class="proposal-banner-highlight">${
                     tx.proposed_donor_agent_name
                   }</span> kartından aktarım yapmayı öneriyor.`
                 : `This intent exceeds agent limit (<strong>$${tx.shortfall_amount.toFixed(
                     2
                   )} shortfall</strong>). System proposes transferring quota from <span class="proposal-banner-highlight">${
                     tx.proposed_donor_agent_name
                   }</span>.`
             }
           </div>
         </div>`
        : '';

    const approveBtnLabel = tx.shortfall_amount
      ? appState.currentLang === 'tr'
        ? `✓ $${tx.shortfall_amount.toFixed(2)} Aktar ve PayPal İle Öde`
        : `✓ Transfer $${tx.shortfall_amount.toFixed(2)} & Settle`
      : i18n[appState.currentLang].btnAuthorize;

    const card = document.createElement('div');
    card.className = 'invoice-review-card';
    card.innerHTML = `
      <div class="invoice-header">
        <div class="hitl-agent-wrap">
          <div class="agent-avatar-icon">🤖</div>
          <span class="invoice-agent">${tx.agent_name}</span>
        </div>
        <span class="invoice-amount font-mono">$${tx.amount.toFixed(
          2
        )} <span style="font-size: 0.8rem; color: #a1a1aa;">${tx.currency}</span></span>
      </div>
      ${diffHtml}
      ${borrowingBannerHtml}
      <div class="invoice-body">
        <strong>${
          appState.currentLang === 'tr' ? 'Gerekçe (Prompt):' : 'Reasoning:'
        }</strong> ${tx.reasoning}
        <br><strong>${appState.currentLang === 'tr' ? 'Alıcı:' : 'Payee:'}</strong> ${
      tx.recipient
    } (${tx.category})
      </div>
      <div class="invoice-footer">
        <button class="fin-btn fin-btn-reject" onclick="resolveHITL('${tx.id}', 'REJECT')">${
      i18n[appState.currentLang].btnReject
    }</button>
        <button class="fin-btn fin-btn-approve-paypal" onclick="resolveHITL('${tx.id}', 'APPROVE')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M7 21h4.5l1.1-7h1.5c3.1 0 5.4-1.8 5.9-5.2.6-3.9-1.8-5.8-5.3-5.8H6.5a.8.8 0 0 0-.8.7L2.4 20.6c-.1.4.2.7.6.7H7z" fill="#ffffff"/>
          </svg>
          ${approveBtnLabel}
        </button>
      </div>
    `;
    el.hitlContainer.appendChild(card);
  });
}

// Render Audit Trail
export function renderAuditTable() {
  if (!el.auditTableBody) return;
  el.auditTableBody.innerHTML = '';
  if (appState.transactionsList.length === 0) {
    el.auditTableBody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">
          ${i18n[appState.currentLang].noAudit}
        </td>
      </tr>
    `;
    return;
  }

  appState.transactionsList.slice(0, 15).forEach((tx) => {
    const tr = document.createElement('tr');
    const timeStr = new Date(tx.created_at).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });

    let tagClass = 'auto';
    let statusText = i18n[appState.currentLang].statusAuto;

    if (tx.status === 'APPROVED_BY_HUMAN') {
      tagClass = 'human';
      statusText = i18n[appState.currentLang].statusHuman;
    } else if (tx.status === 'PENDING_APPROVAL') {
      tagClass = 'pending';
      statusText = i18n[appState.currentLang].statusPending;
    } else if (tx.status.includes('REJECTED')) {
      tagClass = 'rejected';
      statusText = i18n[appState.currentLang].statusRejected;
    }

    const ref = tx.paypal_order_id || tx.paypal_payout_batch_id || tx.id;

    tr.innerHTML = `
      <td class="font-mono text-zinc-400">${timeStr}</td>
      <td style="font-weight: 600; color: #ffffff;">${tx.agent_name}</td>
      <td class="font-mono" style="font-weight: 700; color: #f4f4f5;">$${tx.amount.toFixed(2)}</td>
      <td class="text-zinc-300">${tx.recipient}</td>
      <td>
        <span class="status-tag ${tagClass}">
          <span class="status-dot-indicator"></span>
          ${statusText}
        </span>
      </td>
      <td>
        <div class="ref-code-wrap">
          <span class="ref-code font-mono">${ref}</span>
          ${(tx.paypal_order_id || tx.status.includes('APPROVED')) ? `<span class="badge-sandbox-tag" title="PayPal Sandbox REST API v2 Live Verified">✓ Sandbox</span>` : ''}
          <button class="btn-copy-ref" onclick="copyRef('${ref}')" title="Copy ID">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>
        </div>
      </td>
    `;
    el.auditTableBody.appendChild(tr);
  });
}

// Resolve HITL
export async function resolveHITL(txId, decision) {
  try {
    const res = await fetch(`${API_BASE}/payments/${txId}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, reviewer_notes: 'Reviewed by supervisor' }),
    });
    if (!res.ok) {
      const err = await res.json();
      showToast(err.detail || 'Hata oluştu', 'danger');
      return;
    }

    const resolvedTx = await res.json();

    if (decision === 'APPROVE') {
      if (resolvedTx.shortfall_amount && resolvedTx.proposed_donor_agent_name) {
        showToast(
          appState.currentLang === 'tr'
            ? `🤝 $${resolvedTx.shortfall_amount.toFixed(2)} ${
                resolvedTx.proposed_donor_agent_name
              }'den aktarıldı ve PayPal ile capture edildi!`
            : `🤝 $${resolvedTx.shortfall_amount.toFixed(2)} transferred from ${
                resolvedTx.proposed_donor_agent_name
              } and settled via PayPal!`,
          'success'
        );
      } else {
        showToast(i18n[appState.currentLang].toastApproveSuccess, 'success');
      }

      // Update Negotiation Chat feed with the latest negotiation log
      try {
        const negRes = await fetch(`${API_BASE}/negotiations`);
        if (negRes.ok) {
          const negs = await negRes.json();
          if (negs.length > 0 && el.negotiationChatFeed) {
            const latest = negs[0];
            const timeNow = new Date().toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            });
            el.negotiationChatFeed.innerHTML = `
              <div class="chat-bubble-agent req">
                <div class="chat-header-row">
                  <div class="chat-author">
                    <span>🤖</span>
                    <span>${latest.requester_name}</span>
                  </div>
                  <div style="display: flex; gap: 0.4rem; align-items: center;">
                    <span class="chat-badge chat-badge-req">Talep (${latest.urgency})</span>
                    <span class="chat-meta-time font-mono">${timeNow}</span>
                  </div>
                </div>
                <div class="chat-body-text">
                  "${latest.justification}" — <strong>$${latest.amount.toFixed(
              2
            )} USD</strong> günlük kota aktarımı talep edildi.
                </div>
              </div>

              <div class="chat-bubble-agent target">
                <div class="chat-header-row">
                  <div class="chat-author">
                    <span>🛡️</span>
                    <span>${latest.target_name}</span>
                  </div>
                  <div style="display: flex; gap: 0.4rem; align-items: center;">
                    <span class="chat-badge chat-badge-approved">✓ SÜPERVİZÖR ONAYLADI</span>
                    <span class="chat-meta-time font-mono">${timeNow}</span>
                  </div>
                </div>
                <div class="chat-body-text font-mono" style="font-size: 0.74rem;">
                  ${latest.transcript.split('\n')[1] || latest.transcript}
                </div>
              </div>
            `;
          }
        }
      } catch (e) {
        console.error('Failed to update negotiation feed:', e);
      }
    } else {
      showToast(i18n[appState.currentLang].toastRejectSuccess, 'warning');
    }

    if (refreshAllCallback) await refreshAllCallback();
  } catch (err) {
    showToast('Bağlantı hatası', 'danger');
  }
}

// Bind to window for HTML onclick
window.resolveHITL = resolveHITL;

export function initFleetEvents(refreshCb) {
  refreshAllCallback = refreshCb;

  // Language change listener to re-render fleet and tables
  onLanguageChange(() => {
    renderHITLQueue();
    renderFleet();
    renderAuditTable();
  });

  // Submit Simulator Intent
  if (el.simForm) {
    el.simForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        agent_id: el.simAgentSelect.value,
        amount: parseFloat(el.simAmount.value),
        recipient: el.simRecipient.value.trim(),
        category: el.simCategory.value,
        reasoning: el.simReasoning.value.trim(),
      };

      try {
        const res = await fetch(`${API_BASE}/payments/intent`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const err = await res.json();
          showToast(err.detail || 'İşlem başarısız', 'danger');
          return;
        }

        const record = await res.json();
        if (record.status === 'APPROVED_AUTONOMOUS') {
          showToast(i18n[appState.currentLang].toastSuccessAuto, 'success');
        } else if (record.status === 'PENDING_APPROVAL') {
          showToast(i18n[appState.currentLang].toastWarningHitl, 'warning');
        }

        if (refreshAllCallback) await refreshAllCallback();
      } catch (err) {
        showToast('Sunucu bağlantı hatası', 'danger');
      }
    });
  }

  // Preset Chips
  if (el.chipPass) {
    el.chipPass.addEventListener('click', () => {
      el.simAgentSelect.value = 'agent-devops';
      el.simAmount.value = '15.00';
      el.simRecipient.value = 'AWS';
      el.simCategory.value = 'CLOUD_COMPUTE';
      el.simReasoning.value =
        appState.currentLang === 'tr'
          ? 'Toplu ses deşifre işlemi için AWS spot çalışan düğümü tahsis ediliyor.'
          : 'Provisioning AWS spot worker node for batch audio transcription.';
    });
  }

  if (el.chipExceed) {
    el.chipExceed.addEventListener('click', () => {
      el.simAgentSelect.value = 'agent-research';
      el.simAmount.value = '85.00';
      el.simRecipient.value = 'OpenAI';
      el.simCategory.value = 'API_QUOTA';
      el.simReasoning.value =
        appState.currentLang === 'tr'
          ? '50.000 akademik makale için yüksek hacimli embedding modeli kota alımı.'
          : 'High-volume embedding batch job for 50k research papers.';
    });
  }

  if (el.chipUnauthorized) {
    el.chipUnauthorized.addEventListener('click', () => {
      el.simAgentSelect.value = 'agent-devops';
      el.simAmount.value = '25.00';
      el.simRecipient.value = 'UnknownCryptoHost';
      el.simCategory.value = 'CLOUD_COMPUTE';
      el.simReasoning.value =
        appState.currentLang === 'tr'
          ? 'Beyaz listede olmayan harici sunucudan GPU kiralama denemesi.'
          : 'Attempting off-market compute procurement from unapproved merchant.';
    });
  }

  if (el.chipPayout) {
    el.chipPayout.addEventListener('click', () => {
      el.simAgentSelect.value = 'agent-payout';
      el.simAmount.value = '35.00';
      el.simRecipient.value = 'alex.freelancer@paypal.com';
      el.simCategory.value = 'FREELANCE_PAYOUT';
      el.simReasoning.value =
        appState.currentLang === 'tr'
          ? 'Grafik tasarım ve UI bileşen teslimi için serbest çalışana hakediş ödemesi.'
          : 'Milestone payment disbursement to external freelancer for UI asset delivery.';
    });
  }

  if (el.btnRefreshAudit) {
    el.btnRefreshAudit.addEventListener('click', () => {
      if (refreshAllCallback) refreshAllCallback();
      showToast(i18n[appState.currentLang].toastRefreshed, 'success');
    });
  }
}
