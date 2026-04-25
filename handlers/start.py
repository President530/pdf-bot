from handlers.pdf_utils import extract_tables_to_excel, find_explications_smart

# Хранилище PDF для каждого пользователя (временно)
user_pdfs = {}

def start_command(chat_id, send_message, get_keyboard):
    send_message(
        chat_id, 
        "🤖 *Здрасте, прывет от ВА*\n\n"
        "📌 *Что я умею:*\n"
        "• 📊 Извлекать таблицы из PDF в Excel\n"
        "• 📐 Находить экспликации помещений\n\n"
        "🚀 *Как работать:*\n"
        "1. Отправь мне PDF файл\n"
        "2. Нажми нужную кнопку в меню\n\n"
        "🆓 Бесплатно, без ограничений!",
        get_keyboard()
    )

def handle_document(chat_id, doc, send_message):
    import requests
    import tempfile
    from app import URL, TOKEN
    
    send_message(chat_id, "📥 *Скачиваю PDF...*")
    
    file_info = requests.get(URL + f"/getFile?file_id={doc['file_id']}").json()
    
    if not file_info.get('ok'):
        send_message(chat_id, "❌ Ошибка получения файла")
        return
    
    file_path = file_info['result']['file_path']
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    
    r = requests.get(file_url)
    temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    temp_pdf.write(r.content)
    temp_pdf.close()
    
    user_pdfs[chat_id] = temp_pdf.name
    
    send_message(chat_id, "✅ *PDF принят!*\n\n📌 Теперь выбери действие в меню:", get_keyboard())

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
            send_message(chat_id, "❌ *Экспликации не найдены*")
        else:
            msg = f"🔍 *Найдено {len(result)} таблиц:*\n\n"
            for r in result:
                msg += f"📄 *Страница {r['page']}* — {r['rows_count']} строк\n"
            send_message(chat_id, msg[:4000])
    
    elif text == '🚀 Excel (PRO)':
        send_message(chat_id, "⏳ *PRO-обработка...*")
        output_excel = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
        count = extract_tables_to_excel_pro(pdf_path, output_excel)
        
        if count == 0:
            send_message(chat_id, "❌ Таблицы не найдены")
        else:
            send_document(chat_id, output_excel, f"pro_tables_{count}.xlsx")
            os.unlink(output_excel)

def get_keyboard():
    from keyboards.menu import main_menu_keyboard
    return main_menu_keyboard()

# PRO функция
import pdfplumber
import re
from openpyxl import Workbook

def extract_tables_to_excel_pro(pdf_path, output_excel):
    wb = Workbook()
    wb.remove(wb.active)
    sheet_count = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            words = page.extract_words(keep_blank_chars=False)
            if not words:
                continue
            
            rows = {}
            threshold = 3
            
            for w in words:
                y0 = round(w['y0'] / threshold) * threshold
                if y0 not in rows:
                    rows[y0] = []
                rows[y0].append(w)
            
            table_rows = []
            for y in sorted(rows.keys()):
                row_words = sorted(rows[y], key=lambda x: x['x0'])
                row_text = [w['text'] for w in row_words]
                
                expanded_row = []
                for cell in row_text:
                    if re.search(r'\d+\s+\d+', cell):
                        expanded_row.extend(re.findall(r'\d+', cell))
                    else:
                        expanded_row.append(cell)
                table_rows.append(expanded_row)
            
            if len(table_rows) > 2:
                sheet_count += 1
                ws = wb.create_sheet(title=f"Страница_{page_num}")
                for row_idx, row in enumerate(table_rows):
                    for col_idx, cell in enumerate(row):
                        if cell:
                            ws.cell(row=row_idx+1, column=col_idx+1, value=cell)
    
    if sheet_count == 0:
        return extract_tables_to_excel(pdf_path, output_excel)
    
    wb.save(output_excel)
    return sheet_count
