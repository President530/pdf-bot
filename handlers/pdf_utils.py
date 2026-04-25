import pdfplumber
import re
from openpyxl import Workbook

def extract_tables_to_excel(pdf_path, output_excel):
    """Диагностика — покажет что видит бот"""
    
    # Просто сохраняем весь текст
    full_text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += f"\n=== Страница {page.page_number} ===\n"
                full_text += text + "\n"
    
    # Сохраняем в Excel как текст
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Текст из PDF"
    
    lines = full_text.split('\n')
    for i, line in enumerate(lines[:200]):  # Первые 200 строк
        if line.strip():
            ws.cell(row=i+1, column=1, value=line[:32767])
    
    wb.save(output_excel)
    
    # Отправляем в лог первые 500 символов
    print("=== ПЕРВЫЕ 500 СИМВОЛОВ PDF ===")
    print(full_text[:500])
    print("================================")
    
    return 0  # Говорим что таблиц не найдено, но текст сохранили

def find_explications_smart(pdf_path):
    """Поиск экспликаций по структуре таблицы"""
    explications = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            
            for table in tables:
                if not table or len(table) < 2:
                    continue
                
                has_numbers = False
                has_names = False
                has_areas = False
                
                for row in table[:10]:
                    if not row:
                        continue
                    for cell in row:
                        if not cell:
                            continue
                        cell_str = str(cell).strip()
                        
                        if re.search(r'^\d+[\.\)]?\s*$|^\d+$', cell_str):
                            has_numbers = True
                        if re.search(r'[А-Я][а-я]+', cell_str) and len(cell_str) > 2:
                            has_names = True
                        if re.search(r'\d+[\.,]\d+\s*м?²?|\d+\s*м²', cell_str):
                            has_areas = True
                
                if has_numbers and has_names and has_areas:
                    formatted = []
                    for row in table:
                        if row and any(cell for cell in row):
                            formatted.append([str(cell).strip() if cell else '' for cell in row])
                    
                    explications.append({
                        'page': page_num,
                        'table': formatted,
                        'rows_count': len(formatted)
                    })
    
    return explications
