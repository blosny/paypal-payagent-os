// ==========================================================================
// PayAgent OS — Command Center & Autonomous FinTech Module
// Vault Subscriptions Cleaner, AI FICO Gauges, Telegram Alerts & Voice CFO
// ==========================================================================

import { showToast } from './fleet.js';

let isSpeaking = false;
let currentUtterance = null;

export async function initCommandCenter() {
  await Promise.all([
    loadVaultSubscriptions(),
    loadFICOScores(),
    loadROIMetrics(),
    loadTelegramSettings(),
    loadDepartments(),
    loadDIDCredentials(),
  ]);

  setupVoiceBriefing();
  setupSettingsModals();
}

// --------------------------------------------------------------------------
// 1. PayPal Vault Subscriptions Cleaner
// --------------------------------------------------------------------------
export async function loadVaultSubscriptions() {
  const container = document.getElementById('vault-subscriptions-list');
  if (!container) return;

  try {
    const res = await fetch('/api/v1/vault/subscriptions');
    if (!res.ok) throw new Error('Failed to fetch subscriptions');
    const subs = await res.json();

    container.innerHTML = subs.map(sub => {
      const isUnused = sub.status === 'UNUSED_WARNING';
      const isCanceled = sub.status === 'CANCELED';

      let badgeHtml = '';
      if (isCanceled) {
        badgeHtml = `<span class="vault-unused-badge" style="background: rgba(100,116,139,0.2); color: #94a3b8;">CANCELED ($${sub.monthly_cost.toFixed(2)}/mo saved)</span>`;
      } else if (isUnused) {
        badgeHtml = `<span class="vault-unused-badge">⚠️ Unused for ${sub.days_unused} days</span>`;
      } else {
        badgeHtml = `<span class="vault-unused-badge" style="background: rgba(16,185,129,0.15); color: #10b981;">✓ Active Fleet Tool</span>`;
      }

      let actionHtml = '';
      if (isCanceled) {
        actionHtml = `<span style="font-size: 0.75rem; color: #64748b;">Subscription inactive</span>`;
      } else if (isUnused) {
        actionHtml = `<button class="btn-vault-cancel" onclick="window.cancelVaultSubscription('${sub.id}', ${sub.monthly_cost})">
          Cancel & save $${sub.monthly_cost.toFixed(0)}/mo
        </button>`;
      } else {
        actionHtml = `<span style="font-size: 0.75rem; color: #10b981;">4 calls today</span>`;
      }

      return `
        <div class="vault-item-card ${isUnused ? 'warning-item' : ''} ${isCanceled ? 'canceled-item' : ''}" id="vault-card-${sub.id}">
          <div class="vault-info-col">
            <div class="vault-name">
              ${sub.service_name}
              ${badgeHtml}
            </div>
            <div class="vault-desc">
              Tokenized via PayPal Vault (${sub.paypal_vault_id}) • Tier: ${sub.plan_tier}
            </div>
          </div>
          <div class="vault-action-col">
            <div class="vault-price">$${sub.monthly_cost.toFixed(2)}<span style="font-size: 0.7rem; font-weight: 400; color: #64748b;">/mo</span></div>
            ${actionHtml}
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Error loading vault subscriptions:', err);
    container.innerHTML = `<div style="color: #64748b; font-size: 0.8rem; padding: 1rem;">Vault subscriptions offline</div>`;
  }
}

window.cancelVaultSubscription = async function(subscriptionId, monthlyCost) {
  try {
    const res = await fetch('/api/v1/vault/cancel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subscription_id: subscriptionId,
        reason: 'Unused by AI fleet for >14 days',
        confirmed_by: 'elena_cfo',
      }),
    });
    if (!res.ok) throw new Error('Cancel failed');
    showToast(`✓ PayPal Vault subscription canceled. Saved $${monthlyCost.toFixed(2)}/mo!`, 'success');
    await loadVaultSubscriptions();
  } catch (err) {
    showToast(`Error canceling subscription: ${err.message}`, 'error');
  }
};

// --------------------------------------------------------------------------
// 2. AI Fleet Dynamic FICO Credit Scores (300 - 850)
// --------------------------------------------------------------------------
export async function loadFICOScores() {
  const container = document.getElementById('fico-agents-list');
  if (!container) return;

  try {
    const res = await fetch('/api/v1/credit/scores');
    if (!res.ok) throw new Error('Failed to load credit scores');
    const scores = await res.json();

    container.innerHTML = scores.map(agent => {
      // Calculate fill percent between 300 and 850
      const pct = Math.max(10, Math.min(100, Math.round(((agent.fico_score - 300) / 550) * 100)));

      return `
        <div class="fico-agent-row">
          <div class="fico-row-top">
            <div class="fico-agent-title">
              <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${agent.color_accent};"></span>
              ${agent.agent_name}
            </div>
            <div class="fico-score-tag" style="background: ${agent.color_accent}20; color: ${agent.color_accent}; border: 1px solid ${agent.color_accent}40;">
              ${agent.fico_score} • ${agent.tier}
            </div>
          </div>
          <div class="fico-bar-wrap">
            <div class="fico-bar-fill" style="width: ${pct}%; background: ${agent.color_accent};"></div>
          </div>
          <div class="fico-row-bottom">
            <span>Dynamic Daily Cap: <strong style="color: #f8fafc;">$${agent.dynamic_daily_limit.toFixed(2)}</strong></span>
            <span>${agent.total_settled_debts} settled debts • ${agent.anomalies_count} anomalies</span>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Error loading FICO scores:', err);
    container.innerHTML = `<div style="color: #64748b; font-size: 0.8rem; padding: 1rem;">Credit scoring offline</div>`;
  }
}

// --------------------------------------------------------------------------
// 3. ROI Productivity Multiplier & Deals Harvester
// --------------------------------------------------------------------------
export async function loadROIMetrics() {
  const bigMetric = document.getElementById('roi-multiplier-value');
  const couponsList = document.getElementById('recent-coupons-list');
  if (!bigMetric) return;

  try {
    const res = await fetch('/api/v1/roi/metrics');
    if (!res.ok) throw new Error('Failed to fetch ROI');
    const data = await res.json();

    bigMetric.innerText = `${data.fleet_multiplier.toFixed(1)}x`;

    const trendBadge = document.getElementById('roi-trend-badge');
    if (trendBadge) trendBadge.innerText = `${data.multiplier_trend} alpha`;

    const savingsVal = document.getElementById('kpi-savings-value');
    if (savingsVal) savingsVal.innerText = `+$${data.cumulative_discount_saved.toFixed(2)}`;

    if (couponsList && data.recent_coupons) {
      couponsList.innerHTML = data.recent_coupons.slice(0, 3).map(c => `
        <div class="coupon-row">
          <span class="coupon-title">🏷️ ${c.title}</span>
          <span class="coupon-saving">-$${c.saved_amount.toFixed(2)}</span>
        </div>
      `).join('');
    }

  } catch (err) {
    console.error('Error loading ROI metrics:', err);
  }
}

window.harvestSampleCoupon = async function() {
  try {
    const vendors = [
      { vendor: 'Cloudflare', title: 'Cloudflare Workers 20% Rebate', pct: 20.0, base: 45.0, agent: 'agent-devops' },
      { vendor: 'MongoDB', title: 'MongoDB Atlas Promo Credit', pct: 15.0, base: 60.0, agent: 'agent-research' },
      { vendor: 'OpenAI', title: 'OpenAI Batch Tier 10% Discount', pct: 10.0, base: 120.0, agent: 'agent-research' },
    ];
    const pick = vendors[Math.floor(Math.random() * vendors.length)];

    const res = await fetch('/api/v1/roi/harvest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: pick.title,
        vendor: pick.vendor,
        discount_percentage: pick.pct,
        original_amount: pick.base,
        agent_id: pick.agent,
      }),
    });
    if (!res.ok) throw new Error('Harvest failed');
    const coupon = await res.json();
    showToast(`🎉 PayPal Deal Harvested! Saved $${coupon.saved_amount.toFixed(2)} on ${coupon.vendor}`, 'success');
    await loadROIMetrics();
  } catch (err) {
    showToast(`Error harvesting coupon: ${err.message}`, 'error');
  }
};

// --------------------------------------------------------------------------
// 4. Web Speech API — Voice CFO Morning Briefing
// --------------------------------------------------------------------------
function setupVoiceBriefing() {
  const btn = document.getElementById('btn-voice-briefing');
  if (!btn) return;

  btn.addEventListener('click', () => {
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      isSpeaking = false;
      btn.classList.remove('speaking');
      btn.innerHTML = `<span>🎙️</span> <span>Listen to CFO Briefing</span>`;
      return;
    }

    if (!('speechSynthesis' in window)) {
      showToast('Web Speech API is not supported in this browser.', 'warning');
      return;
    }

    const text = `Good morning Elena. This is your PayAgent OS financial command summary. 
Total fleet treasury stands at 3,200 dollars. 
128 dollars and 50 cents spent today across 12 transactions. 
One transaction for AWS compute requires your review in the human in the loop queue. 
Notion AI subscription has been flagged as unused for 28 days with 49 dollars monthly savings available. 
Fleet productivity multiplier is operating at 3.4x with 84 dollars in harvested PayPal deals. 
Your agent fleet is safe and compliant.`;

    currentUtterance = new SpeechSynthesisUtterance(text);
    currentUtterance.rate = 1.0;
    currentUtterance.pitch = 1.0;
    currentUtterance.lang = 'en-US';

    currentUtterance.onstart = () => {
      isSpeaking = true;
      btn.classList.add('speaking');
      btn.innerHTML = `<span>⏹️</span> <span>Speaking Morning Briefing...</span>`;
    };

    currentUtterance.onend = () => {
      isSpeaking = false;
      btn.classList.remove('speaking');
      btn.innerHTML = `<span>🎙️</span> <span>Listen to CFO Briefing</span>`;
    };

    currentUtterance.onerror = () => {
      isSpeaking = false;
      btn.classList.remove('speaking');
      btn.innerHTML = `<span>🎙️</span> <span>Listen to CFO Briefing</span>`;
    };

    window.speechSynthesis.speak(currentUtterance);
  });
}

// --------------------------------------------------------------------------
// 5. Telegram & FICO Configuration Modals
// --------------------------------------------------------------------------
async function loadTelegramSettings() {
  try {
    const res = await fetch('/api/v1/telegram/settings');
    if (!res.ok) return;
    const data = await res.json();
    const handleEl = document.getElementById('tg-account-handle');
    if (handleEl) handleEl.innerText = data.connected_account;

    const t1 = document.getElementById('tg-toggle-hitl');
    const t2 = document.getElementById('tg-toggle-risk');
    const t3 = document.getElementById('tg-toggle-summary');
    if (t1) t1.checked = data.hitl_approval_requests;
    if (t2) t2.checked = data.blocked_risk_events;
    if (t3) t3.checked = data.daily_treasury_summary;
  } catch (err) {
    console.error('Error loading Telegram settings:', err);
  }
}

function setupSettingsModals() {
  // Telegram Modal triggers
  const tgBtn = document.getElementById('btn-open-telegram-modal');
  const tgModal = document.getElementById('telegram-settings-modal');
  const tgClose = document.getElementById('btn-close-telegram-modal');
  const tgSave = document.getElementById('btn-save-telegram-settings');
  const tgTest = document.getElementById('btn-test-telegram-ping');

  if (tgBtn && tgModal) {
    tgBtn.addEventListener('click', () => tgModal.classList.add('active'));
    if (tgClose) tgClose.addEventListener('click', () => tgModal.classList.remove('active'));
  }

  if (tgSave) {
    tgSave.addEventListener('click', async () => {
      const t1 = document.getElementById('tg-toggle-hitl')?.checked ?? true;
      const t2 = document.getElementById('tg-toggle-risk')?.checked ?? true;
      const t3 = document.getElementById('tg-toggle-summary')?.checked ?? false;
      try {
        await fetch('/api/v1/telegram/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            connected_account: '@elena_cfo',
            hitl_approval_requests: t1,
            blocked_risk_events: t2,
            daily_treasury_summary: t3,
            is_connected: true,
          }),
        });
        showToast('✓ Telegram supervisor preferences saved', 'success');
        if (tgModal) tgModal.classList.remove('active');
      } catch (err) {
        showToast(`Save failed: ${err.message}`, 'error');
      }
    });
  }

  if (tgTest) {
    tgTest.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/v1/telegram/test-alert', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: '🔔 Test ping from PayAgent OS Command Center.' }),
        });
        if (res.ok) {
          showToast('✓ Test alert dispatched to Telegram @elena_cfo', 'success');
        }
      } catch (err) {
        showToast(`Ping failed: ${err.message}`, 'error');
      }
    });
  }

  // FICO Modal triggers
  const ficoBtn = document.getElementById('btn-open-fico-modal');
  const ficoModal = document.getElementById('fico-config-modal');
  const ficoClose = document.getElementById('btn-close-fico-modal');
  const ficoSave = document.getElementById('btn-save-fico-config');

  if (ficoBtn && ficoModal) {
    ficoBtn.addEventListener('click', async () => {
      ficoModal.classList.add('active');
      try {
        const res = await fetch('/api/v1/credit/config');
        if (res.ok) {
          const cfg = await res.json();
          document.getElementById('fico-inp-on-time').value = cfg.on_time_repayment_bonus;
          document.getElementById('fico-inp-discipline').value = cfg.budget_discipline_bonus;
          document.getElementById('fico-inp-anomaly').value = cfg.policy_anomaly_penalty;
          document.getElementById('fico-inp-prime').value = cfg.prime_threshold;
        }
      } catch (e) {
        console.error(e);
      }
    });
    if (ficoClose) ficoClose.addEventListener('click', () => ficoModal.classList.remove('active'));
  }

  if (ficoSave) {
    ficoSave.addEventListener('click', async () => {
      try {
        const onTime = parseInt(document.getElementById('fico-inp-on-time').value) || 45;
        const discipline = parseInt(document.getElementById('fico-inp-discipline').value) || 25;
        const anomaly = parseInt(document.getElementById('fico-inp-anomaly').value) || 40;
        const prime = parseInt(document.getElementById('fico-inp-prime').value) || 800;

        await fetch('/api/v1/credit/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            on_time_repayment_bonus: onTime,
            budget_discipline_bonus: discipline,
            policy_anomaly_penalty: anomaly,
            high_risk_penalty: 75,
            prime_threshold: prime,
            trusted_threshold: 740,
            monitored_threshold: 670,
          }),
        });
        showToast('✓ AI FICO scoring model updated', 'success');
        if (ficoModal) ficoModal.classList.remove('active');
        await loadFICOScores();
      } catch (err) {
        showToast(`Save failed: ${err.message}`, 'error');
      }
    });
  }
}

// --------------------------------------------------------------------------
// 6. Interactive Command Center HITL Quick Actions
// --------------------------------------------------------------------------
window.approveSimulatedHitl = async function() {
  const card = document.getElementById('card-hitl-command');
  if (card) {
    card.innerHTML = `
      <div class="cc-card-header">
        <span class="cc-card-title">
          <span style="color: #10b981;">✓</span>
          <span>HUMAN-IN-THE-LOOP REVIEW QUEUE</span>
        </span>
        <span class="top-kpi-badge badge-success">ALL RESOLVED</span>
      </div>
      <div style="background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); border-radius: 0.75rem; padding: 1.5rem; text-align: center;">
        <div style="font-size: 1.75rem; margin-bottom: 0.5rem;">🎉</div>
        <div style="font-weight: 700; color: #10b981; font-size: 1rem; margin-bottom: 0.25rem;">
          Transaction Authorized & Settled via PayPal Orders v2
        </div>
        <div style="font-size: 0.8125rem; color: #94a3b8;">
          $240.00 captured to AWS Spot Fleet • Status: SETTLED • Telegram notification updated
        </div>
      </div>
    `;
  }

  // Update top KPI numbers
  const pendingEl = document.getElementById('stat-pending');
  if (pendingEl) pendingEl.innerText = '0';
  const spentEl = document.getElementById('stat-spent-today');
  if (spentEl) spentEl.innerText = '368.50';

  showToast('✓ Authorized $240.00 via PayPal. AWS spot cluster captured!', 'success');

  // Trigger FICO bonus for discipline
  try {
    await fetch('/api/v1/credit/adjust', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_id: 'agent-devops',
        event_type: 'BUDGET_DISCIPLINE',
        reason: 'Authorized high-priority workload within acceptable risk bounds',
      }),
    });
    await loadFICOScores();
  } catch (e) {
    console.error(e);
  }
};

window.rejectSimulatedHitl = function() {
  const card = document.getElementById('card-hitl-command');
  if (card) {
    card.innerHTML = `
      <div class="cc-card-header">
        <span class="cc-card-title">
          <span style="color: #ef4444;">✕</span>
          <span>HUMAN-IN-THE-LOOP REVIEW QUEUE</span>
        </span>
        <span class="top-kpi-badge" style="background: rgba(239,68,68,0.2); color: #ef4444;">REJECTED</span>
      </div>
      <div style="background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); border-radius: 0.75rem; padding: 1.5rem; text-align: center;">
        <div style="font-weight: 700; color: #ef4444; font-size: 1rem; margin-bottom: 0.25rem;">
          Request Rejected by Supervisor Elena
        </div>
        <div style="font-size: 0.8125rem; color: #94a3b8;">
          DevOps Agent informed to scale down instance to c6i.large.
        </div>
      </div>
    `;
  }
  const pendingEl = document.getElementById('stat-pending');
  if (pendingEl) pendingEl.innerText = '0';
  showToast('✕ Transaction rejected. DevOps agent notified to use smaller instance.', 'warning');
};

// --------------------------------------------------------------------------
// 7. Multi-Tenant Department Hierarchy & Quota Management
// --------------------------------------------------------------------------
export async function loadDepartments() {
  const container = document.getElementById('departments-list-grid');
  if (!container) return;

  try {
    const res = await fetch('/api/v1/tenants/departments');
    if (!res.ok) throw new Error('Failed to load departments');
    const depts = await res.json();

    container.innerHTML = depts.map(dept => {
      const pct = Math.min(100, Math.round((dept.spent_today / (dept.allocated_budget || 1)) * 100));

      const agentChips = dept.assigned_agent_ids.map(id => `
        <span class="dept-agent-chip">🤖 ${id.replace('agent-', '')}</span>
      `).join('');

      return `
        <div class="dept-card" id="dept-card-${dept.id}">
          <div>
            <div class="dept-card-top">
              <span class="dept-name">${dept.name}</span>
              <span class="dept-badge">${dept.code}</span>
            </div>
            <div class="dept-lead">👤 Lead: ${dept.lead_name}</div>
            
            <div class="dept-bar-wrap">
              <div class="dept-bar-fill" style="width: ${pct}%;"></div>
            </div>

            <div class="dept-meta-row">
              <span>Spent Today: <strong style="color: #f8fafc;">$${dept.spent_today.toFixed(2)}</strong></span>
              <span>Allocated: <strong style="color: #38bdf8;">$${dept.allocated_budget.toFixed(2)}</strong></span>
            </div>
          </div>

          <div>
            <div style="font-size: 0.6875rem; color: #64748b; margin-bottom: 0.35rem;">Assigned AI Fleet:</div>
            <div class="dept-agents-row">${agentChips}</div>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Error loading departments:', err);
    container.innerHTML = `<div style="color: #64748b; font-size: 0.8rem; padding: 1rem;">Department hierarchy offline</div>`;
  }
}

window.openDeptTransferModal = function() {
  const modal = document.getElementById('dept-transfer-modal');
  if (modal) modal.classList.add('active');
};

window.closeDeptTransferModal = function() {
  const modal = document.getElementById('dept-transfer-modal');
  if (modal) modal.classList.remove('active');
};

window.submitDeptTransfer = async function() {
  const fromDept = document.getElementById('dept-transfer-from')?.value;
  const toDept = document.getElementById('dept-transfer-to')?.value;
  const amount = parseFloat(document.getElementById('dept-transfer-amount')?.value);
  const reason = document.getElementById('dept-transfer-reason')?.value;

  if (!fromDept || !toDept || isNaN(amount) || amount <= 0) {
    showToast('Please specify valid departments and transfer amount', 'warning');
    return;
  }

  if (fromDept === toDept) {
    showToast('Source and destination departments cannot be the same', 'warning');
    return;
  }

  try {
    const res = await fetch('/api/v1/tenants/transfer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from_dept_id: fromDept,
        to_dept_id: toDept,
        amount: amount,
        reason: reason || 'Departmental budget rebalance',
        authorized_by: 'Elena Rostova (CFO)',
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Transfer failed');
    }

    const data = await res.json();
    showToast(`✓ Transferred $${data.amount.toFixed(2)} from ${data.from_dept_name} to ${data.to_dept_name}!`, 'success');
    window.closeDeptTransferModal();
    await loadDepartments();
  } catch (err) {
    showToast(`Transfer error: ${err.message}`, 'error');
  }
};

// --------------------------------------------------------------------------
// 8. W3C DID & Decentralized Agent Wallet Passports
// --------------------------------------------------------------------------
export async function loadDIDCredentials() {
  const container = document.getElementById('did-passports-grid');
  if (!container) return;

  try {
    const res = await fetch('/api/v1/identity/credentials');
    if (!res.ok) throw new Error('Failed to load credentials');
    const creds = await res.json();

    container.innerHTML = creds.map(cred => {
      const isRevoked = cred.status === 'REVOKED';

      const statusBadge = isRevoked
        ? `<span class="top-kpi-badge" style="background:rgba(239,68,68,0.2); color:#ef4444;">REVOKED</span>`
        : `<span class="top-kpi-badge badge-success">ACTIVE SEAL</span>`;

      const actionBtn = isRevoked
        ? `<span style="font-size:0.7rem; color:#ef4444; font-weight:600;">KILLSWITCH ACTIVE</span>`
        : `<button type="button" class="btn-killswitch" onclick="window.revokeDIDCredential('${cred.credential_id}', '${cred.agent_name}')">
            ⚠️ Killswitch / Revoke
          </button>`;

      return `
        <div class="passport-card ${isRevoked ? 'revoked-passport' : ''}" id="passport-card-${cred.credential_id}">
          <div>
            <div class="passport-card-top">
              <div class="passport-agent-name">
                <span>🪪</span>
                ${cred.agent_name}
              </div>
              ${statusBadge}
            </div>

            <div class="did-uri-pill" title="${cred.subject_did}">
              ${cred.subject_did}
            </div>

            <div class="passport-specs-row">
              <div>Single Limit: <strong style="color:#f8fafc;">$${cred.max_single_spend.toFixed(2)}</strong></div>
              <div>Daily Cap: <strong style="color:#38bdf8;">$${cred.daily_spend_cap.toFixed(2)}</strong></div>
            </div>

            <div style="font-size:0.7rem; color:#94a3b8; margin-bottom:0.4rem;">
              Categories: <span style="color:#cbd5e1;">${cred.allowed_categories.join(', ')}</span>
            </div>
          </div>

          <div>
            <div class="passport-seal-row">
              <span style="display:flex; align-items:center; gap:0.25rem;">
                <span>🛡️</span> ${cred.proof_type}
              </span>
              <button type="button" class="preset-chip" style="font-size:0.65rem; padding:0.15rem 0.4rem;" onclick="window.verifyDIDCredential('${cred.credential_id}')">
                ✓ Verify Signature
              </button>
            </div>

            <div style="display:flex; align-items:center; justify-content:space-between; margin-top:0.5rem; font-size:0.7rem; color:#64748b;">
              <span>Mühürleyen: <strong>${cred.issuer_name}</strong></span>
              ${actionBtn}
            </div>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Error loading DID credentials:', err);
    container.innerHTML = `<div style="color: #64748b; font-size: 0.8rem; padding: 1rem;">DID identity registry offline</div>`;
  }
}

window.verifyDIDCredential = async function(credentialId) {
  try {
    const res = await fetch('/api/v1/identity/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential_id: credentialId }),
    });
    if (!res.ok) throw new Error('Verification call failed');
    const data = await res.json();
    if (data.is_valid) {
      showToast(`✓ Cryptographic Signature Verified! Validated by CFO Elena Rostova.`, 'success');
    } else {
      showToast(`✕ Verification Failed: ${data.reason}`, 'warning');
    }
  } catch (err) {
    showToast(`Verification error: ${err.message}`, 'error');
  }
};

window.revokeDIDCredential = async function(credentialId, agentName) {
  const confirmed = confirm(`Are you sure you want to trigger the EMERGENCY KILLSWITCH for ${agentName}? This will immediately revoke their PayPal spending authority.`);
  if (!confirmed) return;

  try {
    const res = await fetch(`/api/v1/identity/revoke/${credentialId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: 'Emergency killswitch activated by CFO Elena' }),
    });
    if (!res.ok) throw new Error('Revoke failed');
    showToast(`🚨 Killswitch Triggered! Spending credential revoked for ${agentName}.`, 'warning');
    await loadDIDCredentials();
  } catch (err) {
    showToast(`Revoke error: ${err.message}`, 'error');
  }
};



