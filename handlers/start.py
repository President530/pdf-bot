from handlers.pdf_utils import extract_tables_to_excel, find_explications_smart
import pdfplumber
import re
from openpyxl import Workbook
import os
import tempfile
import gc

# Хранилище PDF для каждого пользователя
user_pdfs = {}

def start_command(chat_id, send_message, get_keyboard):
    send_message(
        chat_id, 
        "🤖 *Бот для извлечения таблиц из PDF*\n\n"
        "📌 *Что умею:*\n"
        "• 📊 Извлекать таблицы в Excel\n"
        "• 📐 Находить экспликации помещений\n"
        "• 🚀 PRO-режим с разбивкой чисел\n\n"
        "⚠️ *Ограничения:*\n"
        "• Файлы до 2 МБ - быстро\n"
        "• Файлы 2-5 МБ - медленно\n"
        "• Файлы >5 МБ - используйте стандартный режим\n\n"
        "📌 *Как работать:*\n"
        "1. Отправьте PDF\n"
        "2. Выберите режим",
        get_keyboard()
    )

def handle_document(chat_id, doc, send_message):
    import requests
    from app import URL, TOKEN
    
    send_message(chat_id, "📥 Скачиваю PDF...")
    
    file_info = requests.get(URL + f"/getFile?file_id={doc['file_id']}").json()
    if not file_info.get('ok'):
        send_message(chat_id, "❌ Ошибка получения файла")
        return
    
    file_path = file_info['result']['file_path']
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    
    file_data = requests.get(file_url)
    file_size_mb = len(file_data.content) / (1024 * 1024)
    
    temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    temp_pdf.write(file_data.content)
    temp_pdf.close()
    
    user_pdfs[chat_id] = {
        'path': temp_pdf.name,
        'size_mb': file_size_mb
    }
    
    warning = ""
    if file_size_mb > 3:
        warning = f"\n\n⚠️ Файл {file_size_mb:.1f} МБ! Рекомендую стандартный режим."
    
    send_message(
        chat_id, 
        f"✅ PDF принят! {file_size_mb:.1f} МБ{warning}\n\n📌 Выберите действие в меню:",
        get_keyboard()
    )

def handle_text(chat_id, text, send_message, send_document):
    if chat_id not in user_pdfs:
        send_message(chat_id, "❌ Сначала отправьте PDF файл!")
        return
    
    pdf_info = user_pdfs[chat_id]
    pdf_path = pdf_info['path']
    file_size_mb = pdf_info['size_mb']
    
    if text == '📊 Таблицы в Excel' or text == '/tables':
        send_message(chat_id, "⏳ Извлекаю таблицы...")
        output_excel = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
        count = extract_tables_to_excel(pdf_path, output_excel)
        
        if count == 0:
            send_message(chat_id, "❌ Таблицы не найдены")
        else:
            send_document(chat_id, output_excel, f"tables_{count}.xlsx")
            os.unlink(output_excel)
    
    elif text == '📐 Экспликации' or text == '/explication':
        send_message(chat_id, "🔍 Ищу экспликации...")
        result = find_explications_smart(pdf_path)
        
        if not result:
            send_message(chat_id, "❌ Экспликации не найдены")
        else:
            msg = f"🔍 Найдено {len(result)} таблиц:\n\n"
            for r in result:
                msg += f"📄 Страница {r['page']} — {r['rows_count']} строк\n"
            send_message(chat_id, msg[:4000])
    
    elif text == '🚀 Excel (PRO)':
        if file_size_mb > 5:
            send_message(chat_id, f"❌ Файл {file_size_mb:.1f} МБ слишком большой для PRO-режима.\n\nИспользуйте стандартный режим 'Таблицы в Excel'.")
            return
        
        if file_size_mb > 2:
            send_message(chat_id, f"⚠️ Файл {file_size_mb:.1f} МБ. Обработка может занять 1-2 минуты...")
        
        send_message(chat_id, "⏳ PRO-обработка...")
        output_excel = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
        
        count = extract_tables_to_excel_pro_economic(pdf_path, output_excel, send_message, chat_id)
        
        if count == 0:
            send_message(chat_id, "❌ Таблицы не найдены. Попробуйте стандартный режим.")
        else:
            send_document(chat_id, output_excel, f"pro_tables_{count}.xlsx")
            os.unlink(output_excel)
            send_message(chat_id, "✅ Готово!")

def get_keyboard():
    from keyboards.menu import main_menu_keyboard
    return main_menu_keyboard()

def extract_tables_to_excel_pro_economic(pdf_path, output_excel, send_message=None, chat_id=None):
    """Экономичная PRO версия для больших файлов"""
    wb = Workbook()
    wb.remove(wb.active)
    sheet_count = 0
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = min(len(pdf.pages), 30)
            
            for page_num in range(total_pages):
                if send_message and chat_id and page_num % 5 == 0 and page_num > 0:
                    send_message(chat_id, f"📄 Обработано {page_num}/{total_pages} страниц...")
                
                page = pdf.pages[page_num]
                tables = page.extract_tables()
                
                for table_idx, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue
                    
                    processed_rows = []
                    for row in table[:100]:
                        if not row or not any(cell for cell in row):
                            continue
                        
                        new_row = []
                        for cell in row[:15]:
                            if cell and isinstance(cell, str):
                                cell_clean = cell.strip()
                                if re.match(r'^[\d\s]+$', cell_clean) and ' ' in cell_clean:
                                    parts = cell_clean.split()
                                    new_row.extend(parts)
                                else:
                                    new_row.append(cell_clean)
                            elif cell:
                                new_row.append(str(cell))
                            else:
                                new_row.append('')
                        
                        if new_row and any(new_row):
                            processed_rows.append(new_row)
                    
                    if len(processed_rows) >= 2:
                        sheet_count += 1
                        ws = wb.create_sheet(title=f"P{page_num+1}_T{table_idx+1}")
                        for i, row in enumerate(processed_rows):
                            for j, val in enumerate(row):
                                if val:
                                    try:
                                        ws.cell(row=i+1, column=j+1, value=val)
                                    except:
                                        pass
                
                del page
                if page_num % 5 == 0:
                    gc.collect()
    
    except Exception as e:
        print(f"PRO error: {e}")
        return 0
    
    if sheet_count == 0:
        return extract_tables_to_excel(pdf_path, output_excel)
    
    try:
        wb.save(output_excel)
    except:
        return 0
    
    return sheet_count
