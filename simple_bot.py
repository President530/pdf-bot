import os
import tempfile
import json
import requests
import time
from pdf_processor import PDFProcessor

TOKEN = "8651917334:AAFU4aXbCzqaa72cMwCH04BXPaeSc1C7pLM"  # ВСТАВЬ СЮДА ТОКЕН ОТ BOTFATHER!!!

processor = PDFProcessor()

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)

def send_document(chat_id, file_path, filename):
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    with open(file_path, 'rb') as f:
        files = {'document': (filename, f)}
        data = {'chat_id': chat_id}
        requests.post(url, data=data, files=files)

def get_file_path(file_id):
    url = f"https://api.telegram.org/bot{TOKEN}/getFile"
    r = requests.post(url, data={"file_id": file_id}).json()
    file_path = r['result']['file_path']
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    return file_url

last_update_id = 0
pdf_path = None

print("Бот запущен (упрощённая версия)...")

while True:
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id+1}"
        updates = requests.get(url).json()
        
        for update in updates.get('result', []):
            last_update_id = update['update_id']
            message = update.get('message')
            if not message:
                continue
                
            chat_id = message['chat']['id']
            text = message.get('text', '')
            
            if text == '/start':
                send_message(chat_id, "Пришли PDF, потом команду /tables или /explication")
            
            elif text == '/tables':
                if pdf_path is None or not os.path.exists(pdf_path):
                    send_message(chat_id, "Сначала отправь PDF")
                    continue
                send_message(chat_id, "Извлекаю таблицы...")
                output_excel = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
                count = processor.extract_tables_to_excel(pdf_path, output_excel)
                if count == 0:
                    send_message(chat_id, "Таблицы не найдены")
                else:
                    send_document(chat_id, output_excel, f"tables_{count}.xlsx")
                    os.unlink(output_excel)
            
            elif text == '/explication':
                if pdf_path is None or not os.path.exists(pdf_path):
                    send_message(chat_id, "Сначала отправь PDF")
                    continue
                result = processor.find_explications(pdf_path)
                if result:
                    msg = f"Найдено экспликаций: {len(result)}\n"
                    for r in result:
                        msg += f"- Страница {r['page']} ({r['rows']} строк)\n"
                    send_message(chat_id, msg)
                else:
                    send_message(chat_id, "Экспликации не найдены")
            
            elif message.get('document'):
                doc = message['document']
                if doc.get('mime_type') == 'application/pdf':
                    send_message(chat_id, "Скачиваю PDF...")
                    file_url = get_file_path(doc['file_id'])
                    temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                    pdf_path = temp_pdf.name
                    r = requests.get(file_url)
                    with open(pdf_path, 'wb') as f:
                        f.write(r.content)
                    send_message(chat_id, "PDF принят! Используй /tables или /explication")
                else:
                    send_message(chat_id, "Присылай только PDF файлы")
        
        time.sleep(1)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(3)