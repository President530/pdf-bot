import os
import tempfile
import requests
from flask import Flask, request
from handlers.start import start_command, handle_document, handle_text
from keyboards.menu import main_menu_keyboard

TOKEN = "8651917334:AAFU4aXbCzqaa72cMwCH04BXPaeSc1C7pLM"
URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(URL + "/sendMessage", json=data)

def send_document(chat_id, file_path, filename):
    with open(file_path, 'rb') as f:
        files = {'document': (filename, f)}
        data = {'chat_id': chat_id}
        requests.post(URL + "/sendDocument", data=data, files=files)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if not update or 'message' not in update:
        return 'OK', 200
    
    message = update['message']
    chat_id = str(message['chat']['id'])
    
    # Обработка команд и кнопок
    if 'text' in message:
        text = message['text']
        
        if text == '/start':
            start_command(chat_id, send_message, main_menu_keyboard)
        
        elif text == '📊 Таблицы в Excel' or text == '/tables':
            handle_text(chat_id, text, send_message, send_document)
        
        elif text == '📐 Экспликации' or text == '/explication':
            handle_text(chat_id, text, send_message, send_document)
        
        elif text == '📰 Новости':
            send_message(chat_id, "🚧 Скоро здесь будут новости! Функция в разработке.")
        
        elif text == '🌤 Погода':
            send_message(chat_id, "🚧 Скоро здесь будет погода! Функция в разработке.")
        
        elif text == 'ℹ️ Помощь':
            help_text = (
                "📌 *Доступные команды:*\n"
                "• /start — Главное меню\n"
                "• /tables — Извлечь таблицы из PDF в Excel\n"
                "• /explication — Найти экспликации помещений\n\n"
                "📌 *Как пользоваться:*\n"
                "1. Отправь PDF файл\n"
                "2. Нажми нужную кнопку в меню"
            )
            send_message(chat_id, help_text)
    
    # Обработка PDF файлов
    elif 'document' in message:
        doc = message['document']
        if doc.get('mime_type') == 'application/pdf':
            handle_document(chat_id, doc, send_message)
        else:
            send_message(chat_id, "❌ Присылай только PDF файлы")
    
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
