import pdfplumber
import re
from openpyxl import Workbook

class PDFProcessor:
    def extract_tables_to_excel(self, pdf_path, output_excel):
        wb = Workbook()
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb.active)

        all_data = []
        current_page = 1
        current_table = []
        in_table = False

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split('\n')
                for line in lines:
                    if re.search(r'\d+\s+\d+', line) or ('Категория' in line and 'Название' in line):
                        if not in_table:
                            in_table = True
                            current_table = []
                        current_table.append(line.split())
                    elif in_table and line.strip() == '':
                        if current_table:
                            all_data.append((current_page, current_table))
                            current_table = []
                            in_table = False
                    elif in_table:
                        current_table.append(line.split())
                if current_table:
                    all_data.append((current_page, current_table))
                    current_table = []
                    in_table = False

        if not all_data:
            full_text = ''
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    full_text += page.extract_text() or ''
            wb.create_sheet(title='Raw Text')
            ws = wb.active
            for i, line in enumerate(full_text.split('\n')):
                ws.cell(row=i+1, column=1, value=line[:32767])
            wb.save(output_excel)
            return 0

        for sheet_idx, (page_num, table) in enumerate(all_data):
            sheet_name = f"Page{page_num}_T{sheet_idx+1}"[:31]
            ws = wb.create_sheet(title=sheet_name)
            for row_idx, row in enumerate(table):
                for col_idx, cell in enumerate(row):
                    if cell:
                        ws.cell(row=row_idx+1, column=col_idx+1, value=str(cell))
        wb.save(output_excel)
        return len(all_data)

    def find_explications(self, pdf_path):
        explications = []
        keywords = ['экспликация', 'помещение', 'комната', 'площадь', 'этаж', 'категория', 'название помещения']

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text().lower() if page.extract_text() else ''
                if any(kw in text for kw in keywords):
                    tables = page.extract_tables()
                    if tables:
                        explications.append({
                            'page': page_num,
                            'rows': len(tables[0])
                        })
                    else:
                        explications.append({
                            'page': page_num,
                            'rows': 0
                        })
        return explications
