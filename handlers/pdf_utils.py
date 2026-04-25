import pdfplumber
import re
from openpyxl import Workbook

def extract_tables_to_excel(pdf_path, output_excel):
    """Парсит текст по пробелам и создаёт таблицу"""
    
    import re
    from openpyxl import Workbook
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Таблицы"
    
    all_rows = []
    current_row = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            
            for line in lines:
                # Разбиваем строку по 2+ пробелам
                cells = re.split(r'\s{2,}', line)
                cells = [c.strip() for c in cells if c.strip()]
                
                if len(cells) >= 2:  # Строка похожа на таблицу
                    # Если строка с числами и текстом — это данные
                    if any(cell.isdigit() or re.search(r'\d+', cell) for cell in cells):
                        all_rows.append(cells)
                    else:
                        # Это заголовок
                        if not all_rows:
                            all_rows.append(cells)
                        else:
                            all_rows.append(cells)
                elif len(cells) == 1 and cells[0] and not any(char.isdigit() for char in cells[0]):
                    # Возможно заголовок
                    pass
    
    if not all_rows:
        # Если ничего не нашли — сохраняем как есть
        full_text = ''
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                full_text += page.extract_text() or ''
        
        lines = full_text.split('\n')
        for i, line in enumerate(lines[:200]):
            ws.cell(row=i+1, column=1, value=line[:32767])
    else:
        # Сохраняем найденные строки
        for row_idx, row in enumerate(all_rows):
            for col_idx, cell in enumerate(row):
                if cell:
                    ws.cell(row=row_idx+1, column=col_idx+1, value=cell)
    
    wb.save(output_excel)
    return len(all_rows) if all_rows else 0

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
