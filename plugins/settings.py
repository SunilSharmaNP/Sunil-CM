# Enhanced Settings Plugin
# User settings and preferences management

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from helpers.utils import UserSettings
from templates.keyboards import create_settings_keyboard, create_merge_mode_keyboard
from templates.messages import SETTINGS_MAIN, format_message_template
from config import Config
from __init__ import LOGGER

@Client.on_callback_query(filters.regex(r"settings_main"))
async def settings_main_callback(c: Client, cb: CallbackQuery):
    """Show main settings menu"""
    user = UserSettings(cb.from_user.id, cb.from_user.first_name)
    
    settings_text = format_message_template(
        SETTINGS_MAIN,
        merge_mode=user.get_merge_mode_text(),
        upload_mode="Document" if user.upload_as_doc else "Video",
        thumbnail_status="Custom" if user.custom_thumbnail else "Auto-generated",
        compression_status="Enabled" if user.compression_enabled else "Disabled",
        language=user.language.upper(),
        autoclean_status="Enabled" if user.auto_delete else "Disabled",
        user_name=user.name,
        user_id=user.user_id,
        join_date="Recently",
        user_status="Premium" if Config.IS_PREMIUM else "Free"
    )
    
    keyboard = create_settings_keyboard(user.user_id)
    await cb.edit_message_text(settings_text, reply_markup=keyboard)

# Export settings functions
__all__ = ['settings_main_callback']
