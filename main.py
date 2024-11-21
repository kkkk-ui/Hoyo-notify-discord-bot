import discord
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import asyncio
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import config

import keep_alive
from selenium.webdriver.chrome.options import Options


# HOYOLABのURL
BASE_URL = "https://www.hoyolab.com/circles/2/27/official?page_type=27&page_sort=news"
CHANNEL_ID = []   # 送信先のチャンネルID格納配列

# Seleniumを使用して新しいトピックを取得する関数
def fetch_new_topics():
    # Chromeのオプションを設定
    chrome_binary_path = "/opt/render/project/.render/chrome/opt/google/chrome/chrome" 
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')  # Headlessモードを有効にする
    chrome_options.add_argument('--no-sandbox')  # サンドボックスを無効にする（Renderで必要）
    chrome_options.add_argument('--disable-dev-shm-usage')  # 一部のシステムで必要
    chrome_options.binary_location = chrome_binary_path 

    # ChromeDriverのパスを指定してWebDriverを起動
    service = Service(ChromeDriverManager(driver_version="131.0.6778.85").install())
    driver = webdriver.Chrome(service=service, options=chrome_options)


    """
    # WebDriverを起動
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    """
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

   
# Discordクライアントの設定
intents = discord.Intents.default()
client = discord.Client(intents=intents)

seen_links = set()  # 確認済みリンクを保持

@client.event
async def on_ready():
    print(f"Bot {client.user} is now running!")
    for guild in client.guilds:  # Botが属しているサーバーをすべてチェック
        for channel in guild.text_channels:  # サーバー内のテキストチャンネルをループ
            print(f"チャンネル名: {channel.name}, チャンネルID: {channel.id}")
            if channel.name == "通知":
                CHANNEL_ID.append(channel.id)


    # 定期的にトピックをチェック
    while True:
        topics = fetch_new_topics()  # トピックを取得
        print(CHANNEL_ID)

        for topic in topics:
            if topic["link"] not in seen_links:
                for channelid in CHANNEL_ID:
                    channel = client.get_channel(channelid)
                    print(f"ここに送信 >> チャンネル名: {channel.name}, チャンネルID: {channel.id}")
                    # 新しいトピックを送信
                    await channel.send(f"新しいトピック: {topic['title']} - {topic['link']}")
                    seen_links.add(topic["link"])

        print("待機中…")
        # 10分間隔でチェック
        await asyncio.sleep(60)


# Bot起動
keep_alive.keep_alive()
client.run(config.DISCORD_TOKEN)

