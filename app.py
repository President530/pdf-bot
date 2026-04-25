import os
import tempfile
import requests
from flask import Flask, request, jsonify
from pdf_processor import PDFProcessor

TOKEN = "8651917334:AAFU4aXbCzqaa72cMwCH04BXPaeSc1C7pLM"  # ВСТАВЬ СВОЙ ТОКЕН
URL = "https://api.telegram.org/bot" + TOKEN

app = Flask(__name__)
processor = PDFProcessor()

# Хранилище для PDF файлов (в реальном боте лучше использовать базу данных)
user_pdfs = {}

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
    chat_id = str(message['chat']['id'])
    
    # Обработка текстовых команд
    if 'text' in message:
        text = message['text']
        
        if text == '/start':
            send_message(chat_id, "Пришли PDF, потом /tables или /explication")
        
        elif text == '/tables':
            if chat_id not in user_pdfs:
                send_message(chat_id, "Сначала отправь PDF")
                return 'OK', 200
            
            pdf_path = user_pdfs[chat_id]
            send_message(chat_id, "Извлекаю таблицы...")
            
            output_excel = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
            count = processor.extract_tables_to_excel(pdf_path, output_excel)
            
            if count == 0:
                send_message(chat_id, "Таблицы не найдены")
            else:
                send_document(chat_id, output_excel, f"tables_{count}.xlsx")
                os.unlink(output_excel)
        
        elif text == '/explication':
            if chat_id not in user_pdfs:
                send_message(chat_id, "Сначала отправь PDF")
                return 'OK', 200
            
            pdf_path = user_pdfs[chat_id]
            result = processor.find_explications(pdf_path)
            
            if result:
                msg = f"Найдено экспликаций: {len(result)}\n"
                for r in result:
                    msg += f"- Страница {r['page']} ({r['rows']} строк)\n"
                send_message(chat_id, msg)
            else:
                send_message(chat_id, "Экспликации не найдены")
    
    # Обработка PDF файлов
    elif 'document' in message:
        doc = message['document']
        if doc.get('mime_type') == 'application/pdf':
            send_message(chat_id, "Скачиваю PDF...")
            
            # Получаем файл
            file_info = requests.get(URL + f"/getFile?file_id={doc['file_id']}").json()
            
            if not file_info.get('ok'):
                send_message(chat_id, "Ошибка получения файла")
                return 'OK', 200
            
            file_path = file_info['result']['file_path']
            file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
            
            # Скачиваем
            r = requests.get(file_url)
            temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            temp_pdf.write(r.content)
            temp_pdf.close()
            
            # Сохраняем путь к PDF для этого пользователя
            user_pdfs[chat_id] = temp_pdf.name
            
            send_message(chat_id, "PDF принят! Используй /tables или /explication")
        else:
            send_message(chat_id, "Присылай только PDF файлы")
    
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
