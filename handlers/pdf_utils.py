import pdfplumber
import re
from openpyxl import Workbook

def extract_tables_to_excel(pdf_path, output_excel):
    """Извлекает таблицы из PDF в Excel с улучшенным распознаванием"""
    
    wb = Workbook()
    if 'Sheet' in wb.sheetnames:
        wb.remove(wb.active)
    
    table_count = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # Пробуем стандартный метод
            tables = page.extract_tables()
            
            # Если стандартный метод не нашёл таблицы — пробуем найти по координатам
            if not tables or len(tables) == 0:
                # Ищем слова с координатами
                words = page.extract_words()
                if words:
                    # Группируем по Y координате (строки)
                    rows = {}
                    for w in words:
                        y = round(w['y0'] / 5) * 5  # Группировка с точностью 5pt
                        if y not in rows:
                            rows[y] = []
                        rows[y].append(w)
                    
                    # Сортируем колонки по X
                    if rows:
                        table = []
                        for y in sorted(rows.keys()):
                            row_words = sorted(rows[y], key=lambda x: x['x0'])
                            row_text = [w['text'] for w in row_words]
                            table.append(row_text)
                        tables.append(table)
            
            for table_idx, table in enumerate(tables):
                if table and len(table) > 1:
                    # Очищаем от пустых строк
                    cleaned_table = []
                    for row in table:
                        if row and any(cell for cell in row if cell and str(cell).strip()):
                            cleaned_row = [str(cell).strip() if cell else '' for cell in row]
                            cleaned_table.append(cleaned_row)
                    
                    if len(cleaned_table) > 1:
                        table_count += 1
                        sheet_name = f"Page{page_num}_T{table_idx+1}"[:31]
                        ws = wb.create_sheet(title=sheet_name)
                        
                        for row_idx, row in enumerate(cleaned_table):
                            for col_idx, cell in enumerate(row):
                                if cell:
                                    ws.cell(row=row_idx+1, column=col_idx+1, value=cell)
    
    # Если нашли таблицы — сохраняем
    if table_count > 0:
        wb.save(output_excel)
    else:
        # Если таблиц нет — сохраняем весь текст как есть
        full_text = ''
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += f"\n--- Страница {page.page_number} ---\n" + text
        
        ws = wb.create_sheet(title='Raw Text (без таблиц)')
        for i, line in enumerate(full_text.split('\n')):
            if line.strip():
                try:
                    ws.cell(row=i+1, column=1, value=line[:32767])
                except:
                    pass
        wb.save(output_excel)
    
    return table_count

def find_explications_smart(pdf_path):
    """Умный поиск экспликаций по структуре таблицы"""
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
                        
                        # Номера (1., 1), 2., 2)
                        if re.search(r'^\d+[\.\)]?\s*$|^\d+$', cell_str):
                            has_numbers = True
                        
                        # Названия на русском с заглавной
                        if re.search(r'[А-Я][а-я]+', cell_str) and len(cell_str) > 2:
                            has_names = True
                        
                        # Площади (12.5, 12,5, 12 м²)
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
