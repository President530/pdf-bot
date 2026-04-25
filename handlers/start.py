from handlers.pdf_utils import extract_tables_to_excel, find_explications_smart
import pdf_utils  # Добавьте эту строку в начало файла

# Хранилище PDF для каждого пользователя (временно)
user_pdfs = {}

def start_command(chat_id, send_message, get_keyboard):
    send_message(
        chat_id, 
        "🤖 *Здрасте, прывет от ВА*\n\n"
        "📌 *Что я умею:*\n"
        "• 📊 Уже извлекать таблицы из PDF в Excel\n"
        "• 📐 Находить экспликации помещений\n\n"
        "🚀 *Как работать:*\n"
        "1. Отправь мне PDF файл\n"
        "2. Нажми нужную кнопку в меню\n\n"
        "🆓 Бесплатно, без ограничений!",
        get_keyboard()
    )

def handle_document(chat_id, doc, send_message):
    """Сохраняет PDF и сообщает пользователю"""
    import requests
    import tempfile
    from app import URL, TOKEN
    
    send_message(chat_id, "📥 *Скачиваю PDF...*")
    
    # Получаем файл
    file_info = requests.get(URL + f"/getFile?file_id={doc['file_id']}").json()
    
    if not file_info.get('ok'):
        send_message(chat_id, "❌ Ошибка получения файла")
        return
    
    file_path = file_info['result']['file_path']
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    
    # Скачиваем
    r = requests.get(file_url)
    temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    temp_pdf.write(r.content)
    temp_pdf.close()
    
    # Сохраняем путь
    user_pdfs[chat_id] = temp_pdf.name
    
    send_message(
        chat_id, 
        "✅ *PDF принят!*\n\n"
        "📌 Теперь выбери действие в меню:",
        get_keyboard()
    )

def handle_text(chat_id, text, send_message, send_document):
    import os
    import tempfile
    
    if chat_id not in user_pdfs:
        send_message(chat_id, "❌ *Сначала отправь PDF файл!*")
        return
    
    pdf_path = user_pdfs[chat_id]
    
    if text == '📊 Таблицы в Excel' or text == '/tables':
        send_message(chat_id, "⏳ *Извлекаю таблицы...*")
        
        output_excel = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
        count = extract_tables_to_excel(pdf_path, output_excel)
        
        if count == 0:
            send_message(chat_id, "❌ *Таблицы не найдены* в этом PDF.")
        else:
            send_document(chat_id, output_excel, f"tables_{count}.xlsx")
            os.unlink(output_excel)
    
    elif text == '📐 Экспликации' or text == '/explication':
        send_message(chat_id, "🔍 *Ищу экспликации помещений...*")
        
        result = find_explications_smart(pdf_path)
        
        if not result:
            send_message(chat_id, "❌ *Экспликации не найдены* в этом PDF.\n\n"
                                  "📌 *Совет:* убедись что в файле есть таблица с номерами, названиями и площадями комнат.")
        else:
            msg = f"🔍 *Найдено {len(result)} таблиц с экспликациями:*\n\n"
            for r in result:
                msg += f"📄 *Страница {r['page']}* — {r['rows_count']} строк\n"
                for row in r['table'][:5]:
                    if any(row):
                        msg += f"  • {' | '.join([str(c)[:20] for c in row if c])}\n"
                msg += "\n"
            
            if len(msg) > 4000:
                msg = msg[:4000] + "\n\n...(обрезано)"
            
            send_message(chat_id, msg)
    
    elif text == '🚀 Excel (PRO)':
        send_message(chat_id, "⏳ PRO-обработка... (это может занять минуту)")
        output_excel = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
        count = pdf_utils.extract_tables_to_excel_pro(pdf_path, output_excel)
        
        if count == 0:
            send_message(chat_id, "❌ Таблицы не найдены. Попробуйте простой режим.")
        else:
            send_document(chat_id, output_excel, f"pro_tables_{count}.xlsx")
            os.unlink(output_excel)

def get_keyboard():
    from keyboards.menu import main_menu_keyboard
    return main_menu_keyboard()
