import pdfplumber
import re
from openpyxl import Workbook

def extract_tables_to_excel(pdf_path, output_excel):
    """Извлекает таблицы из PDF в Excel"""
    
    wb = Workbook()
    if 'Sheet' in wb.sheetnames:
        wb.remove(wb.active)
    
    table_count = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            
            for table_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue
                
                # Очищаем от пустых строк
                cleaned_rows = []
                for row in table:
                    if row and any(str(cell).strip() for cell in row if cell):
                        cleaned_rows.append([str(cell).strip() if cell else '' for cell in row])
                
                if len(cleaned_rows) >= 2:
                    table_count += 1
                    sheet_name = f"Page{page_num}_T{table_idx+1}"[:31]
                    ws = wb.create_sheet(title=sheet_name)
                    
                    for row_idx, row in enumerate(cleaned_rows):
                        for col_idx, cell in enumerate(row):
                            if cell:
                                ws.cell(row=row_idx+1, column=col_idx+1, value=cell)
    
    if table_count > 0:
        wb.save(output_excel)
    else:
        # Если таблиц нет — сохраняем весь текст
        full_text = ''
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        
        ws = wb.create_sheet(title='Текст из PDF')
        lines = full_text.split('\n')
        for i, line in enumerate(lines):
            if line.strip():
                ws.cell(row=i+1, column=1, value=line[:32767])
        wb.save(output_excel)
    
    return table_count

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
