from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

options = Options()
options.add_argument('--headless=new')
driver = webdriver.Edge(options=options)

def run_tests_on(url, label):
    print(f"\n==========================================")
    print(f" TESTING ON {label}: {url}")
    print(f"==========================================")
    driver.get(url)
    time.sleep(1)

    # 1. Talebi yapan ajan dropdown kontrolü
    sel = driver.find_element(By.ID, 'sim-agent-select')
    opts = sel.find_elements(By.TAG_NAME, 'option')
    print(f"[TEST 1] Talebi Yapan Ajan Options Sayısı: {len(opts)}")
    for o in opts:
        print(f"         - {o.get_attribute('value')}: {o.text}")
    assert len(opts) >= 3, "Agent seçenekleri boş olmamalı!"

    # 2. Hızlı test senaryoları butonları
    chip_pass = driver.find_element(By.ID, 'chip-pass')
    chip_pass.click()
    time.sleep(0.3)
    amt_1 = driver.find_element(By.ID, 'sim-amount').get_attribute('value')
    rec_1 = driver.find_element(By.ID, 'sim-recipient').get_attribute('value')
    print(f"[TEST 2A] Limit İçi ($15 AWS) tıklandı -> Tutar: {amt_1}, Alıcı: {rec_1}")
    assert amt_1 == '15.00' and rec_1 == 'AWS', "Limit İçi çipi formu dolduramadı!"

    chip_exceed = driver.find_element(By.ID, 'chip-exceed')
    chip_exceed.click()
    time.sleep(0.3)
    amt_2 = driver.find_element(By.ID, 'sim-amount').get_attribute('value')
    rec_2 = driver.find_element(By.ID, 'sim-recipient').get_attribute('value')
    print(f"[TEST 2B] Limit Aşımı ($85 OpenAI) tıklandı -> Tutar: {amt_2}, Alıcı: {rec_2}")
    assert amt_2 == '85.00' and rec_2 == 'OpenAI', "Limit Aşımı çipi formu dolduramadı!"

    # 3. Onaylama ve Reddetme Butonları
    approve_btn = driver.find_element(By.CSS_SELECTOR, '.btn-paypal-approve')
    approve_btn.click()
    time.sleep(0.3)
    card_text = driver.find_element(By.ID, 'card-hitl-command').text
    print(f"[TEST 3] Onayla butonuna basıldı -> Kart Durumu Güncellendi:")
    print(f"         {card_text.splitlines()[:2]}")
    assert ('ONAY' in card_text or 'Authorized' in card_text or 'Settled' in card_text), "Onay butonu çalışmadı!"

    # 4. Üst bardaki butonlar (Sandbox Rozeti, Telegram Modal, Ses, TR/EN)
    sandbox_badge = driver.find_element(By.ID, 'badge-sandbox-verified')
    assert sandbox_badge.is_displayed(), "Sandbox rozeti görüntülenemedi!"
    print(f"[TEST 4A] Üst Bar PayPal Sandbox Verified Rozeti: ÇALIŞIYOR")

    tg_btn = driver.find_element(By.ID, 'btn-open-telegram-modal')
    tg_btn.click()
    time.sleep(0.3)
    tg_modal = driver.find_element(By.ID, 'telegram-settings-modal')
    assert 'active' in tg_modal.get_attribute('class'), "Telegram modal açılamadı!"
    driver.find_element(By.ID, 'btn-close-telegram-modal').click()
    time.sleep(0.2)
    print(f"[TEST 4B] Üst Bar Telegram Butonu ve Modalı: ÇALIŞIYOR")

    # 5. Sekmeler arası geçiş butonları
    tabs = driver.find_elements(By.CSS_SELECTOR, '.tab-nav-btn')
    print(f"[TEST 5] Sekmeler Arası Geçiş Testi ({len(tabs)} sekme):")
    for t in tabs:
        tid = t.get_attribute('data-tab')
        title = t.text.replace('\n', ' ')
        t.click()
        time.sleep(0.15)
        pane = driver.find_element(By.ID, tid)
        assert 'active' in pane.get_attribute('class') and 'hidden-tab' not in pane.get_attribute('class'), f"{tid} aktifleşmedi!"
        print(f"         ✓ Sekme '{title}' başarıyla açıldı")

import socket

def is_server_running(host='127.0.0.1', port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

try:
    run_tests_on('file:///c:/projects/paypal-ai-hackathon/frontend/index.html', 'STANDALONE FILE MODE')
    if is_server_running():
        run_tests_on('http://127.0.0.1:8000', 'LIVE BACKEND HTTP MODE')
    else:
        print("\n[BİLGİ] Canlı backend (port 8000) çalışmadığı için canlı HTTP modu atlandı (File modu %100 başarılı).")
    print("\n=======================================================")
    print(" >>> TÜM ARAYÜZ VE ODAK TESTLERİ BAŞARIYLA GEÇTİ! <<<")
    print("=======================================================")
finally:
    driver.quit()
