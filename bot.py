import os
import tempfile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from pdf_processor import PDFProcessor

TOKEN = "ТВОЙ_ТОКЕН"  # ВСТАВЬ СЮДА ТОКЕН!!!

processor = PDFProcessor()

def start(update, context):
    update.message.reply_text("Пришли PDF, потом /tables или /explication")

def handle_pdf(update, context):
    doc = update.message.document
    temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    file = doc.get_file()
    file.download(temp_pdf.name)
    context.user_data['pdf_path'] = temp_pdf.name
    update.message.reply_text("PDF принят! Команды: /tables  /explication")

def tables(update, context):
    pdf_path = context.user_data.get('pdf_path')
    if not pdf_path:
        update.message.reply_text("Сначала отправь PDF")
        return
    
    update.message.reply_text("Извлекаю таблицы...")
    output_excel = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
    count = processor.extract_tables_to_excel(pdf_path, output_excel)
    
    if count == 0:
        update.message.reply_text("Таблицы не найдены")
        return
        
    with open(output_excel, 'rb') as f:
        update.message.reply_document(f, filename=f"tables_{count}.xlsx")
    
    os.unlink(output_excel)

def explication(update, context):
    pdf_path = context.user_data.get('pdf_path')
    if not pdf_path:
        update.message.reply_text("Сначала отправь PDF")
        return
    
    result = processor.find_explications(pdf_path)
    if result:
        msg = f"Найдено экспликаций: {len(result)}\n"
        for r in result:
            msg += f"- Страница {r['page']} ({r['rows']} строк)\n"
        update.message.reply_text(msg)
    else:
        update.message.reply_text("Экспликации не найдены")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("tables", tables))
    dp.add_handler(CommandHandler("explication", explication))
    dp.add_handler(MessageHandler(Filters.document.pdf, handle_pdf))
    
    print("Бот запущен! Жду PDF...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()