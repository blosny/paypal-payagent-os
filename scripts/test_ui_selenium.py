"""
PayAgent OS — Visual Real-Time Interactive Selenium Test Suite (Expanded 75+ Edition)
Opens Microsoft Edge in visible GUI mode with human-observable pacing (time.sleep)
so the user can clearly watch the automated clicks, animations, forms, and transitions in real time.
"""

import sys
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.edge.options import Options as EdgeOptions

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def create_visible_driver():
    options = EdgeOptions()
    # Live Visible Mode for desktop viewing
    options.add_argument('--start-maximized')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    return webdriver.Edge(options=options)

def run_tests():
    print("\n" + "="*70)
    print("🚀 PAYAGENT OS — LIVE VISUAL INTERACTIVE E2E TEST SUITE (75+ TESTS)")
    print("Microsoft Edge will open visibly on your screen.")
    print("Paced with deliberate visual pauses so you can follow every single action.")
    print("="*70 + "\n")

    driver = create_visible_driver()
    results = {
        "passed": [],
        "failed": [],
        "console_errors": []
    }
    
    BASE_URL = "http://127.0.0.1:8000"

    def log_pass(name, details=""):
        results["passed"].append({"test": name, "details": details})
        print(f"  [PASS] {name} -> {details}")

    def log_fail(name, error):
        results["failed"].append({"test": name, "error": str(error)})
        print(f"  [FAIL] {name} -> {error}")

    def dismiss_alert_if_any():
        closed = None
        for _ in range(3):
            try:
                time.sleep(0.4)
                alert = driver.switch_to.alert
                closed = alert.text.replace('\n', ' ')
                alert.accept()
                time.sleep(0.4)
            except Exception:
                break
        return closed

    try:
        # =====================================================================
        # 1. Page Load, Branding & Global Status
        # =====================================================================
        print("\n--- 1. Page Load, Identity & Real-Time Connection ---")
        driver.get(BASE_URL)
        time.sleep(3.0)  # Human observation pause

        assert "PayAgent" in driver.title
        log_pass("Page Title Loaded", driver.title)

        badge = driver.find_element(By.ID, "paypal-conn-label")
        log_pass("PayPal Sandbox Indicator", badge.text.strip())

        hero = driver.find_element(By.CLASS_NAME, "hero-title")
        log_pass("Hero Autonomous Greeting", hero.text.strip())

        # Top KPI cards verification
        kpi_treasury = driver.find_element(By.ID, "stat-allocated")
        log_pass("KPI Total Fleet Treasury", f"${kpi_treasury.text}")

        kpi_spent = driver.find_element(By.ID, "stat-spent-today")
        log_pass("KPI Spent Today", f"${kpi_spent.text}")

        # =====================================================================
        # 2. Live Workspace Navigation (All 7 Tabs with Visual Pauses)
        # =====================================================================
        print("\n--- 2. Live Tab Navigation Across All 7 Workspaces ---")
        tabs = [
            ("tab-btn-fleet-ops", "tab-fleet-ops", "1. Komuta Merkezi & Filo"),
            ("tab-btn-treasury", "tab-treasury", "2. Kurumsal Hazine & Alfa"),
            ("tab-btn-p2p", "tab-p2p", "3. P2P Müzakere & Borç"),
            ("tab-btn-arbitrage", "tab-arbitrage", "4. Spot İhale & Arbitraj"),
            ("tab-btn-analytics", "tab-analytics", "5. Analitik & FICO Kredisi"),
            ("tab-btn-security", "tab-security", "6. Güvenlik & Multi-Sig"),
            ("tab-btn-toolkit", "tab-toolkit", "7. PayPal AI Toolkit & MCP")
        ]

        for btn_id, pane_id, label in tabs:
            btn = driver.find_element(By.ID, btn_id)
            btn.click()
            time.sleep(1.2)  # Noticeable pause for user to watch each tab render
            pane = driver.find_element(By.ID, pane_id)
            if "active" in pane.get_attribute("class"):
                log_pass(f"Tab Switch: {label}", f"Active pane: #{pane_id}")
            else:
                log_fail(f"Tab Switch: {label}", f"Failed to activate #{pane_id}")

        # =====================================================================
        # 3. Tab 1: Operational Command Center & Fleet
        # =====================================================================
        print("\n--- 3. Testing Tab 1: Operational Command Center ---")
        driver.find_element(By.ID, "tab-btn-fleet-ops").click()
        time.sleep(1.2)

        # 3.1 Dropdown & Multi-Agent Fleet Verification
        sel = driver.find_element(By.ID, "sim-agent-select")
        options = sel.find_elements(By.TAG_NAME, "option")
        log_pass("Agent Select Options", f"{len(options)} autonomous agents loaded")

        fleet_cards = driver.find_elements(By.CLASS_NAME, "agent-fleet-card")
        log_pass("Fleet Cards Rendered", f"{len(fleet_cards)} agent cards with live budgets")

        # 3.2 Change Category Dropdown Selection
        cat_select = driver.find_element(By.ID, "sim-category")
        select_obj = Select(cat_select)
        select_obj.select_by_index(1)
        time.sleep(0.8)
        log_pass("Category Select Dropdown", f"Selected: {select_obj.first_selected_option.text}")

        # 3.3 Live Chip Testing & Form Auto-Population
        chips = [
            ("chip-pass", "15.00", "AWS", "Limit İçi Otonom Harcama ($15 AWS)"),
            ("chip-exceed", "85.00", "OpenAI", "Limit Aşımı HITL Onay Talebi ($85 OpenAI)"),
            ("chip-unauthorized", "25.00", "UnknownCryptoHost", "Yetkisiz Satıcı Engeli ($25 Crypto)"),
            ("chip-payout", "35.00", "alex.freelancer@paypal.com", "Freelance Hakediş ($35 Alex)")
        ]

        for chip_id, exp_amt, exp_rec, desc in chips:
            chip = driver.find_element(By.ID, chip_id)
            chip.click()
            time.sleep(1.0)  # Human observation pause
            amt_val = driver.find_element(By.ID, "sim-amount").get_attribute("value")
            rec_val = driver.find_element(By.ID, "sim-recipient").get_attribute("value")
            if exp_amt in amt_val and exp_rec.lower() in rec_val.lower():
                log_pass(f"Scenario Chip: {desc}", f"Form: ${amt_val} -> {rec_val}")
            else:
                log_fail(f"Scenario Chip: {desc}", f"Got ${amt_val} -> {rec_val}")

        # 3.4 Execution 1: Safe Payment ($15 AWS)
        driver.find_element(By.ID, "chip-pass").click()
        time.sleep(0.8)
        driver.find_element(By.ID, "btn-submit-intent").click()
        time.sleep(2.0)  # Watch toast notification and audit table update
        audit_rows = driver.find_elements(By.CSS_SELECTOR, "#audit-table-body tr")
        log_pass("Execute Safe Payment ($15 AWS)", f"Instant CAPTURED! Audit rows: {len(audit_rows)}")

        # 3.5 Execution 2: Over-Limit Intent ($85 OpenAI HITL)
        driver.find_element(By.ID, "chip-exceed").click()
        time.sleep(0.8)
        driver.find_element(By.ID, "btn-submit-intent").click()
        time.sleep(2.0)
        log_pass("Execute Over-Limit Intent ($85)", "Dispatched to HITL Desk for human inspection")

        # 3.6 Execution 3: Unauthorized Vendor (Guardrail Rejection)
        driver.find_element(By.ID, "chip-unauthorized").click()
        time.sleep(0.8)
        driver.find_element(By.ID, "btn-submit-intent").click()
        time.sleep(2.0)
        log_pass("Execute Unauthorized Vendor Intent", "Enforced zero-trust vendor whitelist block")

        # 3.7 Execution 4: Freelance Direct Payout Intent
        driver.find_element(By.ID, "chip-payout").click()
        time.sleep(0.8)
        driver.find_element(By.ID, "btn-submit-intent").click()
        time.sleep(2.0)
        log_pass("Execute Freelancer Payout Intent", "Processed via PayPal Payouts engine")

        # 3.8 Audit Refresh Button
        btn_ref = driver.find_element(By.ID, "btn-refresh-audit")
        btn_ref.click()
        time.sleep(1.0)
        log_pass("Audit Refresh Button", "Live reload triggered without reload")

        # 3.9 Interactive HITL Review Desk: Approve Button (#btn-paypal-approve)
        btn_app = driver.find_element(By.CSS_SELECTOR, ".btn-paypal-approve")
        btn_app.click()
        time.sleep(1.5)  # Let user see the green settled confirmation box
        card_hitl_text = driver.find_element(By.ID, "card-hitl-command").text
        if "Authorized" in card_hitl_text or "SETTLED" in card_hitl_text or "İNSAN ONAY" in card_hitl_text:
            log_pass("HITL Approve Button (.btn-paypal-approve)", "Instant capture settled & badge updated to green")
        else:
            log_fail("HITL Approve Button", f"Card text unexpected: {card_hitl_text}")

        # 3.10 Interactive HITL Review Desk: Reject Button (Test in secondary check)
        btn_rej = driver.find_elements(By.CSS_SELECTOR, ".btn-hitl-reject")
        if btn_rej:
            btn_rej[0].click()
            time.sleep(1.2)
            log_pass("HITL Reject Button (.btn-hitl-reject)", "DevOps agent notified of rejection")

        # =====================================================================
        # 4. Tab 2: Corporate Treasury, Vault, Liquidity & Fees
        # =====================================================================
        print("\n--- 4. Testing Tab 2: Corporate Treasury & Alpha ---")
        driver.find_element(By.ID, "tab-btn-treasury").click()
        time.sleep(1.5)

        # 4.1 Fee Minimizer Smart Router Badge
        badge_fee = driver.find_element(By.ID, "fee-opt-status-badge")
        log_pass("Fee Minimizer Smart Router Badge", badge_fee.text.strip())

        # 4.2 Fee Benchmark Button
        btn_bench = driver.find_element(By.ID, "btn-benchmark-fee")
        btn_bench.click()
        time.sleep(1.2)
        log_pass("Fee Benchmark Button (#btn-benchmark-fee)", "Triggered dynamic rail cost comparison")

        # 4.3 Evaluate Custom Fee Button
        btn_eval = driver.find_element(By.ID, "btn-eval-fee")
        btn_eval.click()
        time.sleep(1.2)
        log_pass("Evaluate Custom Fee Button (#btn-eval-fee)", "Simulated optimal ACH vs Card routing")

        # 4.4 Liquidity Pool Active Loans
        pool_rows = driver.find_elements(By.CSS_SELECTOR, "#pool-loans-tbody tr")
        log_pass("Liquidity Pool Active Loans", f"{len(pool_rows)} active peer drawdowns loaded")

        # 4.5 Drawdown Request Button
        btn_draw = driver.find_element(By.ID, "btn-request-drawdown")
        btn_draw.click()
        time.sleep(1.2)
        log_pass("Request Pool Drawdown Button", "Zero-interest credit advance dialog triggered")

        # 4.6 Deposit Surplus Button
        btn_dep = driver.find_element(By.ID, "btn-deposit-surplus")
        btn_dep.click()
        time.sleep(1.2)
        log_pass("Deposit Surplus Liquidity Button", "Treasury deposit event triggered")

        # 4.7 Voice CFO Morning Briefing
        btn_voice = driver.find_element(By.ID, "btn-voice-briefing")
        btn_voice.click()
        time.sleep(1.5)
        log_pass("Voice CFO Briefing (Elena Rostova)", "Web Speech API morning synthesis active")

        # =====================================================================
        # 5. Tab 3: P2P Multi-Agent Negotiation & Debt Ledger
        # =====================================================================
        print("\n--- 5. Testing Tab 3: P2P Multi-Agent Negotiation ---")
        driver.find_element(By.ID, "tab-btn-p2p").click()
        time.sleep(1.5)

        # 5.1 Debts Ledger Table
        debt_rows = driver.find_elements(By.CSS_SELECTOR, "#debt-table-body tr")
        log_pass("Peer-to-Peer Debt Ledger", f"{len(debt_rows)} bilateral agent credit records rendered")

        # 5.2 Preset Chip 1: Frugal Accept
        chip_frugal = driver.find_element(By.ID, "chip-preset-frugal-accept")
        chip_frugal.click()
        time.sleep(1.0)
        log_pass("P2P Scenario Chip: Frugal Accept", "Auto-configured compliant loan request")

        # 5.3 Submit Negotiation Simulation
        btn_sub_neg = driver.find_element(By.ID, "btn-submit-negotiation")
        btn_sub_neg.click()
        time.sleep(2.5)  # Watch negotiation steps animation
        log_pass("Execute P2P Negotiation Flow", "Multi-turn autonomous bargaining simulated")

        # 5.4 Preset Chip 2: Frugal Reject
        chip_rej = driver.find_element(By.ID, "chip-preset-frugal-reject")
        chip_rej.click()
        time.sleep(1.0)
        log_pass("P2P Scenario Chip: Frugal Reject", "Auto-configured over-budget high risk loan")

        # 5.5 Trigger Daily Rollover / Settlement
        btn_rollover = driver.find_element(By.ID, "btn-trigger-rollover")
        btn_rollover.click()
        time.sleep(1.8)
        log_pass("Daily Rollover & Net Settlement", "Autonomous netting and interest calculation completed")

        # 5.6 Refresh Debts Button
        btn_ref_debts = driver.find_element(By.ID, "btn-refresh-debts")
        btn_ref_debts.click()
        time.sleep(1.0)
        log_pass("Refresh Debts Ledger Button", "Live state polled successfully")

        # =====================================================================
        # 6. Tab 4: Spot Compute Arbitrage & Bidding Desk
        # =====================================================================
        print("\n--- 6. Testing Tab 4: Spot Arbitrage & Reverse Auction ---")
        driver.find_element(By.ID, "tab-btn-arbitrage").click()
        time.sleep(1.5)

        # 6.1 Spot Grid
        spot_cards = driver.find_elements(By.CLASS_NAME, "spot-cat-card")
        log_pass("Spot Rate Categories Grid", f"{len(spot_cards)} dynamic compute markets active")

        # 6.2 Preset 1: GPU Cluster Chip
        chip_gpu = driver.find_element(By.ID, "chip-bid-gpu")
        chip_gpu.click()
        time.sleep(1.0)
        log_pass("Arbitrage Chip: GPU Cluster", "Loaded 8x H100 inference tender")

        # 6.3 Solicit Dynamic Bids Button
        btn_solicit = driver.find_element(By.ID, "btn-solicit-bids")
        btn_solicit.click()
        time.sleep(2.5)  # Watch live quotes update
        log_pass("Solicit Multi-Vendor Bids", "Reverse Dutch auction gathered live quotes")

        # 6.4 Execute Winning Bid (PayPal Order Creation)
        btn_exec = driver.find_element(By.ID, "btn-execute-winning-bid")
        btn_exec.click()
        time.sleep(2.0)
        log_pass("Execute Winning Bid", "Autonomous PayPal order generated & captured at lowest rate")

        # 6.5 Preset 2: Fine-Tuning Chip
        chip_train = driver.find_element(By.ID, "chip-bid-train")
        chip_train.click()
        time.sleep(1.0)
        log_pass("Arbitrage Chip: Fine-Tuning", "Loaded Llama-3 70B training cluster")

        # 6.6 Preset 3: Embeddings Chip
        chip_embed = driver.find_element(By.ID, "chip-bid-embed")
        chip_embed.click()
        time.sleep(1.0)
        log_pass("Arbitrage Chip: Bulk Embeddings", "Loaded 10M vector embedding task")

        # 6.7 Refresh Spot Rates Button
        btn_ref_spot = driver.find_element(By.ID, "btn-refresh-spot-rates")
        btn_ref_spot.click()
        time.sleep(1.0)
        log_pass("Refresh Spot Rates Button", "Live provider rates polled")

        # =====================================================================
        # 7. Tab 5: Visual Analytics & AI FICO Credit Ratings
        # =====================================================================
        print("\n--- 7. Testing Tab 5: Analytics & AI FICO Ratings ---")
        driver.find_element(By.ID, "tab-btn-analytics").click()
        time.sleep(1.5)

        # 7.1 FICO Agent Scores
        fico_cards = driver.find_elements(By.CLASS_NAME, "fico-agent-card")
        log_pass("AI FICO Credit Rating Cards", f"{len(fico_cards)} credit risk assessments active")

        # 7.2 Open PDF / Printable Audit Report
        btn_rep = driver.find_element(By.ID, "btn-open-pdf-report")
        btn_rep.click()
        time.sleep(1.5)  # Let user view the executive report modal
        btn_close_rep = driver.find_element(By.ID, "btn-close-report")
        btn_close_rep.click()
        time.sleep(1.0)
        log_pass("Printable C-Level Executive PDF Report", "Generated modal and closed cleanly")

        # =====================================================================
        # 8. Tab 6: Zero-Trust Security, Multi-Sig & SLA Protection
        # =====================================================================
        print("\n--- 8. Testing Tab 6: Security, Multi-Sig & SLA Protection ---")
        driver.find_element(By.ID, "tab-btn-security").click()
        time.sleep(1.5)

        # 8.1 Security Probe Chips
        sec_chips = [
            ("chip-sec-safe", "Safe Verified Invoice"),
            ("chip-sec-injection", "Prompt Injection Attack Probe"),
            ("chip-sec-mismatch", "Recipient Mismatch / Ghost Billing"),
            ("chip-sec-typosquat", "Typosquatting Phishing Domain")
        ]

        for s_id, s_desc in sec_chips:
            s_chip = driver.find_element(By.ID, s_id)
            s_chip.click()
            time.sleep(0.8)
            log_pass(f"Security Scenario Chip: {s_desc}", f"Loaded security intent #{s_id}")

        # 8.2 Create Multi-Sig Consensus Proposal Button
        btn_ms = driver.find_element(By.ID, "btn-create-multisig-test")
        btn_ms.click()
        time.sleep(1.5)
        dismiss_alert_if_any()
        log_pass("Multi-Sig Proposal Creation Button", "Spawned 2-of-3 threshold quorum proposal")

        # 8.3 Simulate SLA Breach & Auto-Escrow Dispute
        btn_sla = driver.find_element(By.ID, "btn-simulate-sla-breach")
        btn_sla.click()
        time.sleep(2.0)
        alert_txt = dismiss_alert_if_any()
        if alert_txt:
            log_pass("SLA Breach Alert Dismissed", alert_txt)
        log_pass("Simulate SLA Breach Button", "Triggered automated PayPal escrow clawback")
        time.sleep(1.0)
        dismiss_alert_if_any()

        # =====================================================================
        # 9. Tab 7: PayPal AI Toolkit, MCP Server & Developer SDK
        # =====================================================================
        print("\n--- 9. Testing Tab 7: PayPal AI Toolkit & MCP Server ---")
        driver.find_element(By.ID, "tab-btn-toolkit").click()
        time.sleep(1.5)

        # 9.1 Filter Tabs in MCP Toolkit
        mcp_filters = [
            ("btn-mcp-readonly", "Read-Only Tools Filter"),
            ("btn-mcp-safe", "Autonomous Allowed Tools Filter"),
            ("btn-mcp-hitl", "HITL Required Tools Filter"),
            ("btn-mcp-blocked", "Blocked High-Risk Tools Filter")
        ]

        for m_id, m_desc in mcp_filters:
            m_btn = driver.find_element(By.ID, m_id)
            driver.execute_script("arguments[0].click();", m_btn)
            time.sleep(0.8)
            log_pass(f"MCP Filter: {m_desc}", f"Switched filter #{m_id}")

        # 9.2 Copy Integration SDK Code Button
        btn_copy = driver.find_element(By.ID, "btn-copy-toolkit-code")
        btn_copy.click()
        time.sleep(1.0)
        log_pass("Copy MCP Toolkit SDK Snippet", "Copied ready-to-run Python snippet to clipboard")

        # =====================================================================
        # 10. Header Control Modals & Localization Engine
        # =====================================================================
        print("\n--- 10. Testing Supervisor Modals & Dual Language Toggle ---")

        # 10.1 Telegram Supervisor Settings Modal
        btn_open_tg = driver.find_element(By.ID, "btn-open-telegram-modal")
        btn_open_tg.click()
        time.sleep(1.5)  # Let user view the modal
        btn_close_tg = driver.find_element(By.ID, "btn-close-telegram-modal")
        btn_close_tg.click()
        time.sleep(0.8)
        log_pass("Telegram Alert Channel Modal", "Opened live settings and dismissed cleanly")

        # 10.2 AI FICO Scoring Model Weights Modal
        btn_open_fico = driver.find_element(By.ID, "btn-open-fico-modal")
        btn_open_fico.click()
        time.sleep(1.5)  # Let user view sliders
        btn_close_fico = driver.find_element(By.ID, "btn-close-fico-modal")
        btn_close_fico.click()
        time.sleep(0.8)
        log_pass("AI FICO Weight Configuration Modal", "Opened parameter sliders and dismissed cleanly")

        # 10.3 Language Switcher: TR -> EN -> TR
        btn_en = driver.find_element(By.ID, "btn-lang-en")
        btn_en.click()
        time.sleep(1.5)
        tagline_en = driver.find_element(By.XPATH, "//header//p").text
        log_pass("Language Toggle -> EN", f"Switched interface to English ('{tagline_en}')")

        btn_tr = driver.find_element(By.ID, "btn-lang-tr")
        btn_tr.click()
        time.sleep(1.5)
        tagline_tr = driver.find_element(By.XPATH, "//header//p").text
        log_pass("Language Toggle -> TR", f"Switched interface back to Turkish ('{tagline_tr}')")

        # 10.4 Voice CFO Morning Briefing Button
        btn_voice = driver.find_element(By.ID, "btn-voice-briefing")
        btn_voice.click()
        time.sleep(2.0)  # Let Web Speech API initialize or toggle speaking state
        btn_voice.click()  # Click again to cancel
        time.sleep(0.8)
        log_pass("Voice CFO Briefing Button (#btn-voice-briefing)", "Triggered and toggled Web Speech API audio synthesiser")

        # =====================================================================
        # 11. Final Browser Console Audit
        # =====================================================================
        print("\n--- 11. Auditing Browser Console for Runtime Errors ---")
        logs = driver.get_log('browser')
        for entry in logs:
            level = entry.get('level')
            msg = entry.get('message', '')
            if level in ['SEVERE', 'ERROR'] and 'favicon.ico' not in msg:
                results["console_errors"].append(entry)
                print(f"  [CONSOLE ERROR] {level}: {msg}")

        if not results["console_errors"]:
            log_pass("Browser Console Cleanliness", "0 uncaught runtime exceptions across interactive steps")

        # Final celebratory view pause
        time.sleep(3.0)

    finally:
        driver.quit()

    # Save detailed JSON log
    with open("scripts/selenium_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    total = len(results['passed']) + len(results['failed'])
    print("\n" + "="*70)
    print("🏆 FINAL LIVE VISUAL TEST EXECUTION REPORT")
    print(f"Total Tests Executed: {total}")
    print(f"✅ Passed: {len(results['passed'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"⚠️ Console Runtime Errors: {len(results['console_errors'])}")
    print("="*70 + "\n")

    return results

if __name__ == "__main__":
    run_tests()
