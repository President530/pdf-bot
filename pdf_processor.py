import pdfplumber
import openpyxl
from openpyxl import Workbook

class PDFProcessor:
    def extract_tables_to_excel(self, pdf_path, output_excel):
        wb = Workbook()
        wb.remove(wb.active)
        table_count = 0
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                for table_idx, table in enumerate(tables):
                    if table and len(table) > 1:
                        table_count += 1
                        ws = wb.create_sheet(title=f"Page{page_num}_T{table_idx+1}")
                        
                        for row_idx, row in enumerate(table):
                            for col_idx, cell in enumerate(row):
                                if cell:
                                    ws.cell(row=row_idx+1, column=col_idx+1, value=str(cell))
        
        wb.save(output_excel)
        return table_count
    
    def find_explications(self, pdf_path):
        explications = []
        keywords = ['экспликация', 'помещение', 'комната', 'площадь', 'этаж']
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue
                    
                    table_text = ' '.join([' '.join([str(cell) for cell in row if cell]) for row in table]).lower()
                    
                    if any(kw in table_text for kw in keywords):
                        explications.append({
                            "page": page_num,
                            "rows": len(table)
                        })
        return explications