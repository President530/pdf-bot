def main_menu_keyboard():
    """Главное меню с кнопками"""
    return {
        "keyboard": [
            ["📊 Таблицы в Excel", "📐 Экспликации"],
            ["📰 Новости", "🌤 Погода"],
            ["ℹ️ Помощь"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
