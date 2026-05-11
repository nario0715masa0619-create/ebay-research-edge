from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Chrome ドライバ初期化
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

url = "https://jp.mercari.com/search?keyword=ポケモンカード&page=1"
print(f"ブラウザを開いています: {url}")
driver.get(url)

print("\n⏳ ページ読み込み待機中... (30秒間、何が表示されるか確認してください)")
print("ブラウザを見て、以下を確認してください：")
print("  1. 商品カードが表示されているか？")
print("  2. 何個表示されているか？")
print("  3. スクロールする必要があるか？")
print("  4. ポップアップやモーダルが表示されているか？")
print()

time.sleep(30)

# ページ内容を保存
with open('manual_check.html', 'w', encoding='utf-8') as f:
    f.write(driver.page_source)

print("\n💾 ページの HTML を manual_check.html に保存しました")
print("ブラウザはそのままにしておきます（確認終了後、閉じてください）")

# ブラウザは開いたままにする
# driver.quit()
