from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    """Asosiy menyu — pastdagi tugmalar."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Balans"), KeyboardButton(text="📅 Davomat")],
            [KeyboardButton(text="💳 To'lovlar"), KeyboardButton(text="📚 Kurs")],
            [KeyboardButton(text="ℹ️ Ma'lumot")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Buyruqni tanlang yoki yozing..."
    )
    return keyboard


def admin_menu():
    """Admin uchun qo'shimcha menyu."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Balans"), KeyboardButton(text="📅 Davomat")],
            [KeyboardButton(text="💳 To'lovlar"), KeyboardButton(text="📚 Kurs")],
            [KeyboardButton(text="⚠️ Qarzdorlar"), KeyboardButton(text="📢 Xabar yuborish")],
            [KeyboardButton(text="ℹ️ Ma'lumot")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Admin buyruqlari..."
    )
    return keyboard
