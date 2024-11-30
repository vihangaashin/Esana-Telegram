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

# Path to the database file to keep track of sent news IDs
DATABASE_PATH = './database.json'
database = []
# Load the database file if it exists
if os.path.exists(DATABASE_PATH):
    with open(DATABASE_PATH, 'r') as db_file:
        database = json.load(db_file)

# Function to fetch the latest news from the source
def get_latest_news():
    try:
        # Step 1: Fetch the main page to retrieve CSRF hash and cookies
        main_page = requests.get('https://www.helakuru.lk/esana', headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
        })
        if main_page.status_code != 200:
            print(f"Failed to load main page. Status code: {main_page.status_code}")
            return None

        # Extract the CSRF hash from the response
        csrf_hash = main_page.text.split('csrfHash')[1].split("';")[0].split("'")[1]
        cookies = main_page.cookies.get_dict()

        # Step 2: Post request to fetch news data
        news_response = requests.post(
            'https://www.helakuru.lk/esana/load',
            headers={
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Referer': 'https://www.helakuru.lk/esana',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            },
            cookies=cookies,
            data=f"newsLimit=&esanaWidget=false&csrf={csrf_hash}&category="
        )

        if news_response.status_code != 200:
            print(f"Failed to load news data. Status code: {news_response.status_code}")
            return None

        # Parse the news data as JSON
        news_data = news_response.json()
        if 'NEWS' in news_data and len(news_data['NEWS']) > 0:
            return news_data['NEWS'][0]  # Return the latest news item
        else:
            print("No news found.")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Function to send the latest news to a Telegram chat
def get_latest_news():
    try:
        # Step 1: Get the main page to retrieve the csrfHash and cookies
        main_page = requests.get('https://www.helakuru.lk/esana', headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.33',
        })
        if main_page.status_code != 200:
            print(f"Failed to load main page. Status code: {main_page.status_code}")
            return None

        csrf_hash = main_page.text.split('csrfHash')[1].split("';")[0].split("'")[1]
        cookies = main_page.cookies.get_dict()

        # Step 2: Load the news data using the csrfHash and cookies
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
            print(news_response.text)
            return None

        try:
            news_data = json.loads(news_response.text)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON. Error: {e}")
            print(news_response.text)
            return None

        if 'NEWS' in news_data and len(news_data['NEWS']) > 0:
            return news_data['NEWS'][0]  # Get the latest news item
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

        # Prepare the Sinhala message with timestamps
        message = f"\U0001F4F0 *{news['titleSi'].strip()}*\n\n"

        # Adding the content in Sinhala with timestamps (if available)
        if 'contentSi' in news:
            for content in news['contentSi']:
                if 'keys' in content:
                    for key in content['keys']:
                        message += f"[{key.get('time', '')}] {key.get('text', '')}\n\n"
                elif content.get('type') == 'text':
                    message += f"{content.get('data', '').strip()}\n\n"

        # Handle media (cover image) with the message including timestamps
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

        # Send additional images if available
        if 'contentSi' in news:
            for content in news['contentSi']:
                if content.get('type') == 'image':
                    image_url = content.get('data')
                    if image_url:
                        image_content = requests.get(image_url).content
                        response = requests.post(
                            f"{BASE_URL}/sendPhoto",
                            data={'chat_id': CHAT_ID},
                            files={'photo': ('image.jpg', image_content)}
                        )
                        if response.status_code == 200:
                            print('Additional Image Sent:', image_url)
                        else:
                            print(f'Failed to send additional image. Status code: {response.status_code}')
                            print(response.text)

        # Send voice messages if available
        if 'contentSi' in news:
            for content in news['contentSi']:
                if content.get('type') == 'voice':
                    voice_url = content.get('data')
                    if voice_url:
                        voice_content = requests.get(voice_url).content
                        response = requests.post(
                            f"{BASE_URL}/sendAudio",
                            data={'chat_id': CHAT_ID, 'caption': 'Voice message', 'parse_mode': 'Markdown'},
                            files={'audio': ('voice.mp3', voice_content)}
                        )
                        if response.status_code == 200:
                            print('Voice Message Sent:', voice_url)
                        else:
                            print(f'Failed to send voice message. Status code: {response.status_code}')
                            print(response.text)
    else:
        print('No news found to send.')

# Background task to fetch and send news periodically
def background_task():
    while True:
        news = get_latest_news()
        send_latest_news(news)
        time.sleep(60)  # Fetch news every 60 seconds

# Root route for the Flask app
@app.route("/")
def home():
    return "The Telegram bot is running!"

# Run the Flask app and start the background task
if __name__ == "__main__":
    threading.Thread(target=background_task, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
