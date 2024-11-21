from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

# HOYOLABのURL
BASE_URL = "https://www.hoyolab.com/circles/2/27/official?page_type=27&page_sort=news"

# Seleniumを使用して新しいトピックを取得する関数
def fetch_new_topics():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')  # Headlessモードを有効にする
    chrome_options.add_argument('--no-sandbox')  # サンドボックスを無効にする（Renderで必要）
    chrome_options.add_argument('--disable-dev-shm-usage')  # 一部のシステムで必要
    chrome_options.add_argument('--lang=ja')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    # WebDriverを起動
    service = Service(ChromeDriverManager(driver_version="131.0.6778.85").install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.delete_all_cookies()

    try:
        # HOYOLABのページを開く
        driver.get(BASE_URL)

        # 要素がロードされるまで待機（最大10秒）
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="__layout"]/div/div[3]/div[2]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div[1]/div[1]/a/div/div[1]/h3/span[2]')
        ))

        # XPathで特定のトピック要素を探す
        topic_elements = driver.find_elements(
            By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div[1]/div[1]/a/div/div[1]/h3'
        )
        #'//*[@id="__layout"]/div/div[3]/div[2]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div/div/a/div/div[1]/h3'

        # トピックデータを収集
        new_topics = []
        for element in topic_elements:
            try:
                # タイトルを取得
                title = element.text
                # 親要素からリンクを取得
                link = element.find_element(By.XPATH, "../../..").get_attribute('href')
                new_topics.append({'title': title, 'link': link})
            except Exception as e:
                print(f"要素の解析中にエラーが発生: {e}")
        
        return new_topics
    finally:
        # ドライバを閉じる
        driver.quit()

# 定期的に新しいトピックをチェックする
def monitor_topics(interval=300):
    seen_links = set()  # 確認済みリンクを保持
    while True:
        print("新しいトピックをチェック中...")
        topics = fetch_new_topics()
        for topic in topics:
            if topic['link'] not in seen_links:
                print(f"新しいトピック発見: {topic['title']} - {topic['link']}")
                seen_links.add(topic['link'])
        
        print("次のチェックまで待機中...")
        time.sleep(interval)

# 実行
if __name__ == "__main__":
    monitor_topics(interval=60)  # 1分間隔でチェック
