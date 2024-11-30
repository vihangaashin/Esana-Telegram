from flask import Flask
import threading
import time
import requests
import json
import os

app = Flask(__name__)

# Replace 'YOUR_BOT_TOKEN' with your actual bot token from BotFather
BOT_TOKEN = 'YOUR_BOT_TOKEN'
# Replace 'CHAT_ID' with the actual chat ID you want to send a message to
CHAT_ID = 'YOUR_CHAT_ID'

# Telegram API URL
BASE_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

# Database to keep track of sent news IDs
DATABASE_PATH = './database.json'
database = []
if os.path.exists(DATABASE_PATH):
    with open(DATABASE_PATH, 'r') as db_file:
        database = json.load(db_file)

# Function to get the latest news
def get_latest_news():
    try:
        main_page = requests.get('https://www.helakuru.lk/esana', headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.33',
        })
        if main_page.status_code != 200:
            print(f"Failed to load main page. Status code: {main_page.status_code}")
            return None

        csrf_hash = main_page.text.split('csrfHash')[1].split("';")[0].split("'")[1]
        cookies = main_page.cookies.get_dict()

        news_response = requests.post(
            'https://www.helakuru.lk/esana/load',
            headers={
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en-US,en;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://www.helakuru.lk',
                'Referer': 'https://www.helakuru.lk/esana',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.33',
                'X-Requested-With': 'XMLHttpRequest',
            },
            cookies=cookies,
            data=f"newsLimit=&esanaWidget=false&csrf={csrf_hash}&category="
        )

        if news_response.status_code != 200:
            print(f"Failed to load news data. Status code: {news_response.status_code}")
            return None

        news_data = json.loads(news_response.text)
        if 'NEWS' in news_data and len(news_data['NEWS']) > 0:
            return news_data['NEWS'][0]
        else:
            print("No news found in the response.")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Function to send the latest news to Telegram
def send_latest_news(news):
    if news:
        news_id = news.get('id')
        if news_id in database:
            return

        message = f"\U0001F4F0 *{news['titleSi'].strip()}*\n\n"
        if 'contentSi' in news:
            for content in news['contentSi']:
                if 'keys' in content:
                    for key in content['keys']:
                        message += f"[{key.get('time', '')}] {key.get('text', '')}\n\n"
                elif content.get('type') == 'text':
                    message += f"{content.get('data', '').strip()}\n\n"

        if news.get('thumb'):
            image_url = news['thumb']
            image_content = requests.get(image_url).content
            response = requests.post(
                f"{BASE_URL}/sendPhoto",
                data={'chat_id': CHAT_ID, 'caption': message.strip(), 'parse_mode': 'Markdown'},
                files={'photo': ('image.jpg', image_content)}
            )
        else:
            response = requests.post(
                f"{BASE_URL}/sendMessage",
                json={'chat_id': CHAT_ID, 'text': message.strip(), 'parse_mode': 'Markdown'}
            )

        if response.status_code == 200:
            print('Sinhala News Sent:', news['titleSi'])
            database.append(news_id)
            with open(DATABASE_PATH, 'w') as db_file:
                json.dump(database, db_file)
        else:
            print(f'Failed to send news. Status code: {response.status_code}')
            print(response.text)
    else:
        print('No news found to send.')

# Background thread to periodically fetch and send news
def background_task():
    while True:
        news = get_latest_news()
        send_latest_news(news)
        time.sleep(60)

@app.route("/")
def home():
    return "The Telegram bot is running!"

if __name__ == "__main__":
    threading.Thread(target=background_task, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
