import os
import tempfile
import requests
import json
from flask import Flask, request
from handlers.start import start_command, handle_document, handle_text
from keyboards.menu import main_menu_keyboard

TOKEN = "8651917334:AAFU4aXbCzqaa72cMwCH04BXPaeSc1C7pLM"
URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

def send_message(chat_id, text, reply_markup=None):
    """Отправка сообщения с отладкой"""
    print(f"📤 SENDING to {chat_id}: {text[:50]}...")
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = reply_markup
    
    try:
        response = requests.post(URL + "/sendMessage", json=data)
        print(f"   Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
        return response
    except Exception as e:
        print(f"   EXCEPTION: {e}")
        return None

def send_document(chat_id, file_path, filename):
    """Отправка документа с отладкой"""
    print(f"📎 SENDING DOC to {chat_id}: {filename}")
    with open(file_path, 'rb') as f:
        files = {'document': (filename, f)}
        data = {'chat_id': chat_id}
        try:
            response = requests.post(URL + "/sendDocument", data=data, files=files)
            print(f"   Response status: {response.status_code}")
            return response
        except Exception as e:
            print(f"   EXCEPTION: {e}")
            return None

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    
    # ПЕЧАТАЕМ ВЕСЬ UPDATE В КОНСОЛЬ
    print("\n" + "="*50)
    print("📨 NEW WEBHOOK RECEIVED:")
    print(json.dumps(update, indent=2, ensure_ascii=False))
    print("="*50 + "\n")
    
    if not update or 'message' not in update:
        print("⚠️ No message in update")
        return 'OK', 200
    
    message = update['message']
    chat_id = str(message['chat']['id'])
    
    print(f"👤 Chat ID: {chat_id}")
    
    # Обработка команд и кнопок
    if 'text' in message:
        text = message['text']
        print(f"💬 Text received: '{text}'")
        
        if text == '/start':
            print("➡️ Calling start_command")
            start_command(chat_id, send_message, main_menu_keyboard)
        
        elif text == '📊 Таблицы в Excel' or text == '/tables':
            print("➡️ Calling handle_text (tables)")
            handle_text(chat_id, text, send_message, send_document)
        
        elif text == '📐 Экспликации' or text == '/explication':
            print("➡️ Calling handle_text (explication)")
            handle_text(chat_id, text, send_message, send_document)
        
        elif text == '🚀 Excel (PRO)':
            print("➡️ Calling handle_text (PRO mode)")
            # Отправляем немедленный ответ для проверки
            send_message(chat_id, "✅ Кнопка PRO нажата! Начинаю обработку...")
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
        else:
            print(f"⚠️ Unknown text: '{text}'")
            send_message(chat_id, f"❓ Неизвестная команда: {text}\nИспользуй /start")
    
    # Обработка PDF файлов
    elif 'document' in message:
        doc = message['document']
        print(f"📄 Document received: {doc.get('file_name', 'unknown')}")
        if doc.get('mime_type') == 'application/pdf':
            handle_document(chat_id, doc, send_message)
        else:
            send_message(chat_id, "❌ Присылай только PDF файлы")
    
    else:
        print("⚠️ No text or document in message")
    
    print("✅ Webhook processed\n")
    return 'OK', 200

if __name__ == '__main__':
    print("🚀 Starting bot on port", int(os.environ.get('PORT', 10000)))
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
