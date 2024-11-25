import discord
import asyncio
import config
import keep_alive
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# HOYOLABのURL
BASE_URL_GENSHIN = "https://www.hoyolab.com/circles/2/27/official?page_type=27&page_sort=news?lang=ja_JP"
BASE_URL_STARRAIL = "https://www.hoyolab.com/circles/6/39/official?page_type=39&page_sort=news?lang=ja_JP"
CHANNEL_ID = []   # 送信先のチャンネルID格納配列
# Discordクライアントの設定
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.messages = True
client = discord.Client(intents=intents)
seen_links = set()  # 確認済みリンクを保持

def initialize_driver():
    global driver
    if driver is None:
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
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.delete_all_cookies()

def close_driver():
    global driver
    if driver is not None:
        driver.quit()
        driver = None

# Seleniumで新しいトピックを取得
async def fetch_new_genshin_topics():
    initialize_driver()
    # Selenium操作を別スレッドで実行
    loop = asyncio.get_event_loop()
    new_genshin_topics = await loop.run_in_executor(None, fetch_genshin_topics_with_selenium)
    return new_genshin_topics

async def fetch_new_starrail_topics():
    initialize_driver()
    # Selenium操作を別スレッドで実行
    loop = asyncio.get_event_loop()
    new_starrail_topics = await loop.run_in_executor(None, fetch_starrail_topics_with_selenium)
    return new_starrail_topics

def fetch_genshin_topics_with_selenium():
    try:
        driver.get(BASE_URL_GENSHIN)
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div[1]/div[1]/a/div/div[1]/h3')
        ))

        # 新着トピックを取得
        topic_elements = driver.find_elements(
            By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div[1]/div[1]/a/div/div[1]/h3'
        )

        new_topics = []
        for element in topic_elements:
            title = element.text
            link = element.find_element(By.XPATH, "../../..").get_attribute("href")
            new_topics.append({"title": title, "link": link})
        return new_topics
    finally:
        driver.quit()

def fetch_starrail_topics_with_selenium():
    try:
        driver.get(BASE_URL_STARRAIL)
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div[1]/div[1]/a/div/div[1]/h3')
        ))

        # 新着トピックを取得
        topic_elements = driver.find_elements(
            By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div[1]/div/div[1]/div[2]/div/div/div/div[2]/div[1]/div[1]/a/div/div[1]/h3'
        )

        new_topics = []
        for element in topic_elements:
            title = element.text
            link = element.find_element(By.XPATH, "../../..").get_attribute("href")
            new_topics.append({"title": title, "link": link})
        return new_topics
    finally:
        driver.quit()
   
@client.event
async def on_ready():
    print(f"Bot {client.user} is now running!")
    # トピック監視タスクを非同期で実行
    asyncio.create_task(check_new_topics())

@client.event
async def on_guild_join(guild):
    # サーバーのシステムメッセージチャンネルを取得
    if guild.system_channel is not None:
        try:
            await guild.system_channel.send("サーバーに追加してくれてありがとう！よろしくお願いします！")
        except discord.Forbidden:
            print("メッセージを送信できませんでした。権限を確認してください。")
    else:
        print("システムチャンネルが設定されていません。")

    for guild in client.guilds:  # Botが属しているサーバーをすべてチェック
        for channel in guild.text_channels:  # サーバー内のテキストチャンネルをループ
            print(f"チャンネル名: {channel.name}, チャンネルID: {channel.id}")
            if channel.name == "通知" and channel.id not in CHANNEL_ID:
                CHANNEL_ID.append(channel.id)

async def check_new_topics():
    global seen_links
    for guild in client.guilds:  # Botが属しているサーバーをすべてチェック
        for channel in guild.text_channels:  # サーバー内のテキストチャンネルをループ
            print(f"チャンネル名: {channel.name}, チャンネルID: {channel.id}")
            if channel.name == "通知" and channel.id not in CHANNEL_ID:
                CHANNEL_ID.append(channel.id)

    while True:
        try:
            topics = await fetch_new_genshin_topics()
            for topic in topics:
                if topic["link"] not in seen_links:
                    for channel_id in CHANNEL_ID:
                        channel = client.get_channel(channel_id)
                        if channel:
                            await channel.send("【原神】新着トピック")
                            embed = discord.Embed(title=topic['title'],description=topic['link'])
                            await channel.send(embed=embed)
                            seen_links.add(topic["link"])
            topics = await fetch_new_starrail_topics()
            for topic in topics:
                if topic["link"] not in seen_links:
                    for channel_id in CHANNEL_ID:
                        channel = client.get_channel(channel_id)
                        if channel:
                            await channel.send("【崩壊：スターレイル】新着トピック")
                            embed = discord.Embed(title=topic['title'],description=topic['link'])
                            await channel.send(embed=embed)
                            seen_links.add(topic["link"])
            print("トピック確認完了、待機中...")
        except Exception as e:
            print(f"エラーが発生しました: {e}")
        await asyncio.sleep(7200)  # ２時間間隔でチェック

# メッセージの検知
@client.event
async def on_message(message):
    # 自身が送信したメッセージには反応しない
    if message.author == client.user:
        return

    # ユーザーからのメンションを受け取った場合、あらかじめ用意された配列からランダムに返信を返す
    if client.user in message.mentions:
        answer = "【原神】と【崩壊：スターレイル】の最新情報をお届けしますね！！"
        print(answer)
        await message.channel.send(answer)

# Bot起動
keep_alive.keep_alive()
client.run(config.DISCORD_TOKEN)

