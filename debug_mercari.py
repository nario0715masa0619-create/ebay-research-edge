from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    url = "https://jp.mercari.com/search?keyword=ポケモンカード"
    driver.get(url)
    time.sleep(3)
    
    # カード取得
    cards = driver.find_elements(By.CSS_SELECTOR, "li[data-testid='item-cell']")
    print(f"合計 {len(cards)} 件のカードを検出\n")
    
    success_count = 0
    fail_count = 0
    fail_examples = []
    
    for idx, card in enumerate(cards):
        try:
            # aria-label を持つ div を探す
            try:
                img_div = card.find_element(By.CSS_SELECTOR, "div.merItemThumbnail[aria-label]")
                aria_label = img_div.get_attribute('aria-label')
            except:
                # 別のセレクタを試す
                img_divs = card.find_elements(By.CSS_SELECTOR, "[aria-label]")
                if img_divs:
                    aria_label = img_divs[0].get_attribute('aria-label')
                else:
                    aria_label = None
            
            if not aria_label:
                fail_count += 1
                if fail_count <= 3:
                    print(f"❌ カード {idx + 1}: aria-label なし")
                    print(f"   HTML: {card.get_attribute('outerHTML')[:200]}...\n")
                continue
            
            if 'サムネイル' in aria_label:
                fail_count += 1
                if fail_count <= 3:
                    print(f"⚠️ カード {idx + 1}: サムネイルのみ")
                    print(f"   aria-label: {aria_label}\n")
                continue
            
            # 正規表現でマッチするか確認
            match = re.search(r'(.+?)の画像\s+(\d+(?:,\d+)?)円', aria_label)
            if not match:
                fail_count += 1
                if fail_count <= 3:
                    print(f"⚠️ カード {idx + 1}: 正規表現マッチなし")
                    print(f"   aria-label: {aria_label}\n")
                continue
            
            success_count += 1
            
        except Exception as e:
            fail_count += 1
    
    print(f"\n{'='*60}")
    print(f"結果")
    print(f"{'='*60}")
    print(f"成功: {success_count} 件")
    print(f"失敗: {fail_count} 件")
    print(f"失敗率: {fail_count / len(cards) * 100:.1f}%")

finally:
    driver.quit()
