# Enhanced Admin Plugin
# Admin controls and management functions

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message
from config import Config
from helpers.utils import UserSettings
from __init__ import LOGGER, queueDB

@Client.on_callback_query(filters.regex(r"admin_main"))
async def admin_main_callback(c: Client, cb: CallbackQuery):
    """Show admin panel (owner only)"""
    if cb.from_user.id != int(Config.OWNER):
        await cb.answer("🔒 Owner only!", show_alert=True)
        return
    
    admin_text = """👨‍💼 **Enhanced MERGE-BOT Admin Panel**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**System Management:**
• Monitor bot statistics and performance
• Manage user access and permissions
• Broadcast messages to all users
• View system logs and errors

**User Management:**
• Ban/unban users
• View user statistics
• Reset user settings
• Monitor active sessions

Choose an option below:"""
    
    from templates.keyboards import create_admin_keyboard
    keyboard = create_admin_keyboard()
    await cb.edit_message_text(admin_text, reply_markup=keyboard)

# Export admin functions
__all__ = ['admin_main_callback']
