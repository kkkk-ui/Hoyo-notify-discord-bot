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
import re

import keep_alive
from selenium.webdriver.chrome.options import Options


# HOYOLABのURL
BASE_URL = "https://www.hoyolab.com/circles/2/27/official?page_type=27&page_sort=news?lang=ja_JP"
CHANNEL_ID = []   # 送信先のチャンネルID格納配列
# Discordクライアントの設定
intents = discord.Intents.default()
client = discord.Client(intents=intents)
seen_links = set()  # 確認済みリンクを保持

# Seleniumで新しいトピックを取得
async def fetch_new_topics():
    chrome_binary_path = "/opt/render/project/.render/chrome/opt/google/chrome/chrome"
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--lang=ja-JP")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.binary_location = chrome_binary_path

    service = Service(ChromeDriverManager(driver_version="131.0.6778.85").install())
    
    # Selenium操作を別スレッドで実行
    loop = asyncio.get_event_loop()
    new_topics = await loop.run_in_executor(None, fetch_topics_with_selenium, service, chrome_options)
    return new_topics

def fetch_topics_with_selenium(service, chrome_options):
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.delete_all_cookies()

    try:
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div[1]/div[1]/a/div/div[1]/h3')
        ))

        # 新着トピックを取得
        topic_elements = driver.find_elements(
            By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div[1]/div[1]/a/div/div[1]/h3'
        )

        # 新着トピックの画像を取得
        element = driver.find_element(By.CSS_SELECTOR, "div.mhy-news-card__img")
        style = element.get_attribute("style")
        url = re.search(r'url\((.*?)\)', style).group(1)

        new_topics = []
        for element in topic_elements:
            title = element.text
            link = element.find_element(By.XPATH, "../../..").get_attribute("href")
            new_topics.append({"title": title, "link": link})
        return new_topics, url
    finally:
        driver.quit()

   
@client.event
async def on_ready():
    print(f"Bot {client.user} is now running!")
    for guild in client.guilds:  # Botが属しているサーバーをすべてチェック
        for channel in guild.text_channels:  # サーバー内のテキストチャンネルをループ
            print(f"チャンネル名: {channel.name}, チャンネルID: {channel.id}")
            if channel.name == "通知":
                CHANNEL_ID.append(channel.id)

    # トピック監視タスクを非同期で実行
    asyncio.create_task(check_new_topics())

async def check_new_topics():
    global seen_links
    while True:
        try:
            topics, url = await fetch_new_topics()
            for topic in topics:
                if topic["link"] not in seen_links:
                    for channel_id in CHANNEL_ID:
                        channel = client.get_channel(channel_id)
                        if channel:
                            await channel.send(f"新着トピック: {topic['title']} - {topic['link']}")
                            embed = discord.Embed(title=topic['title'],description=topic['link'])
                            embed.set_thumbnail(url=url)
                            await channel.send(embed=embed)
                            seen_links.add(topic["link"])
            print("トピック確認完了、待機中...")
        except Exception as e:
            print(f"エラーが発生しました: {e}")
        await asyncio.sleep(60)  # 60秒間隔でチェック

# メッセージの検知
@client.event
async def on_message(message):
    # 自身が送信したメッセージには反応しない
    if message.author == client.user:
        return

    # ユーザーからのメンションを受け取った場合、あらかじめ用意された配列からランダムに返信を返す
    if client.user in message.mentions:
        answer = "どうされましたか？"
        print(answer)
        await message.channel.send(answer)


# Bot起動
keep_alive.keep_alive()
client.run(config.DISCORD_TOKEN)

