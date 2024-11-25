import discord
import config
import keep_alive
import asyncio
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# HOYOLABのURL
BASE_URL_GENSHIN = "https://www.hoyolab.com/circles/2/27/official?page_type=27&page_sort=news?lang=ja_JP"
BASE_URL_STARRAIL = "https://www.hoyolab.com/circles/6/39/official?page_type=39&page_sort=news?lang=ja_JP"
CHANNEL_ID = []  # 送信先のチャンネルID格納配列
MAX_SEEN_LINKS = 100  # 履歴の最大保持数

# グローバル変数
driver = None
g_seen_links = set()  # 原神の確認済みリンク
s_seen_links = set()  # スターレイルの確認済みリンク

# Discordクライアントの設定
intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

# ドライバ初期化と終了
def initialize_driver():
    global driver
    if driver is None:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--lang=ja-JP")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

def close_driver():
    global driver
    if driver:
        driver.quit()
        driver = None

# トピックを取得
def fetch_topics(url):
    initialize_driver()
    global driver
    driver.get(url)
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located(
        (By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div[1]/div[1]/a/div/div[1]/h3')
    ))
    topic_elements = driver.find_elements(
        By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div[1]/div[1]/a/div/div[1]/h3'
    )

    topics = []
    for element in topic_elements:
        title = element.text
        link = element.find_element(By.XPATH, "../../..").get_attribute("href")
        topics.append({"title": title, "link": link})
    return topics

# トピックの監視
async def check_new_topics():
    global g_seen_links, s_seen_links
    try:
        genshin_topics = fetch_topics(BASE_URL_GENSHIN)
        for topic in genshin_topics:
            if topic["link"] not in g_seen_links:
                for channel_id in CHANNEL_ID:
                    channel = client.get_channel(channel_id)
                    if channel:
                        await channel.send("【原神】新着トピック")
                        embed = discord.Embed(title=topic['title'], description=topic['link'])
                        await channel.send(embed=embed)
                g_seen_links.add(topic["link"])

        starrail_topics = fetch_topics(BASE_URL_STARRAIL)
        for topic in starrail_topics:
            if topic["link"] not in s_seen_links:
                for channel_id in CHANNEL_ID:
                    channel = client.get_channel(channel_id)
                    if channel:
                        await channel.send("【崩壊：スターレイル】新着トピック")
                        embed = discord.Embed(title=topic['title'], description=topic['link'])
                        await channel.send(embed=embed)
                s_seen_links.add(topic["link"])

        # 古いリンクを削除
        if len(g_seen_links) > MAX_SEEN_LINKS:
            g_seen_links.pop()
        if len(s_seen_links) > MAX_SEEN_LINKS:
            s_seen_links.pop()

        print("トピック確認完了")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        traceback.print_exc()

# Botの準備完了イベント
@client.event
async def on_ready():
    print(f"Bot {client.user} が起動しました！")

# メッセージイベント
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if client.user in message.mentions:
        await message.channel.send("【原神】と【崩壊：スターレイル】の最新情報をお届けします！")

# スケジューラーの設定
scheduler = AsyncIOScheduler()
scheduler.add_job(check_new_topics, 'interval', hours=3)  # 3時間ごとに実行
scheduler.start()

# プログラム終了時にドライバを閉じる
import atexit
atexit.register(close_driver)

# Botを起動
keep_alive.keep_alive()
client.run(config.DISCORD_TOKEN)

