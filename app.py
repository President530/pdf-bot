import os
import tempfile
import requests
import time
import threading
from flask import Flask, request, jsonify
from pdf_processor import PDFProcessor

TOKEN = "ТВОЙ_ТОКЕН"  # ВСТАВЬ ТОКЕН БОТА
URL = "https://api.telegram.org/bot" + TOKEN

app = Flask(__name__)
processor = PDFProcessor()

def send_message(chat_id, text):
    data = {"chat_id": chat_id, "text": text}
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
    chat_id = message['chat']['id']
    
    if 'text' in message:
        text = message['text']
        if text == '/start':
            send_message(chat_id, "Пришли PDF, потом /tables или /explication")
        elif text == '/tables':
            if 'pdf_path' not in app.config:
                send_message(chat_id, "Сначала отправь PDF")
                return 'OK', 200
            send_message(chat_id, "Извлекаю таблицы...")
            output_excel = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
            count = processor.extract_tables_to_excel(app.config['pdf_path'], output_excel)
            if count == 0:
                send_message(chat_id, "Таблицы не найдены")
            else:
                send_document(chat_id, output_excel, f"tables_{count}.xlsx")
                os.unlink(output_excel)
        elif text == '/explication':
            if 'pdf_path' not in app.config:
                send_message(chat_id, "Сначала отправь PDF")
                return 'OK', 200
            result = processor.find_explications(app.config['pdf_path'])
            if result:
                msg = f"Найдено экспликаций: {len(result)}\n"
                for r in result:
                    msg += f"- Страница {r['page']} ({r['rows']} строк)\n"
                send_message(chat_id, msg)
            else:
                send_message(chat_id, "Экспликации не найдены")
    
    elif 'document' in message:
        doc = message['document']
        if doc.get('mime_type') == 'application/pdf':
            send_message(chat_id, "Скачиваю PDF...")
            file_info = requests.get(URL + f"/getFile?file_id={doc['file_id']}").json()
            file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info['result']['file_path']}"
            r = requests.get(file_url)
            pdf_path = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
            with open(pdf_path, 'wb') as f:
                f.write(r.content)
            app.config['pdf_path'] = pdf_path
            send_message(chat_id, "PDF принят! Используй /tables или /explication")
    
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))