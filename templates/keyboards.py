# Enhanced Keyboard Templates
# UI components for Enhanced MERGE-BOT

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional, Dict, Any

def create_main_keyboard() -> InlineKeyboardMarkup:
    """Create main menu keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings_main"),
            InlineKeyboardButton("❓ Help", callback_data="help_main")
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data="stats_main"),
            InlineKeyboardButton("ℹ️ About", callback_data="about_main")
        ],
        [
            InlineKeyboardButton("🚀 Quick Merge", callback_data="merge_now"),
            InlineKeyboardButton("📋 View Queue", callback_data="queue_view")
        ]
    ])

def create_settings_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Create settings menu keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 Merge Mode", callback_data=f"setting_merge_mode_{user_id}"),
            InlineKeyboardButton("📤 Upload Mode", callback_data=f"setting_upload_mode_{user_id}")
        ],
        [
            InlineKeyboardButton("🖼️ Thumbnail", callback_data=f"setting_thumbnail_{user_id}"),
            InlineKeyboardButton("🗜️ Compression", callback_data=f"setting_compression_{user_id}")
        ],
        [
            InlineKeyboardButton("🌍 Language", callback_data=f"setting_language_{user_id}"),
            InlineKeyboardButton("🧹 Auto Clean", callback_data=f"setting_autoclean_{user_id}")
        ],
        [
            InlineKeyboardButton("🔄 Reset All", callback_data=f"setting_reset_{user_id}"),
            InlineKeyboardButton("🔙 Back", callback_data="start_main")
        ]
    ])

def create_merge_mode_keyboard(user_id: int, current_mode: int) -> InlineKeyboardMarkup:
    """Create merge mode selection keyboard"""
    modes = [
        ("📹 Video Merge", 1),
        ("🎵 Audio Merge", 2),
        ("📄 Subtitle Merge", 3),
        ("🔍 Extract Streams", 4)
    ]
    
    buttons = []
    for mode_name, mode_id in modes:
        if mode_id == current_mode:
            button_text = f"✅ {mode_name}"
        else:
            button_text = mode_name
        
        buttons.append([InlineKeyboardButton(button_text, callback_data=f"set_merge_mode_{user_id}_{mode_id}")])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="settings_main")])
    
    return InlineKeyboardMarkup(buttons)

def create_upload_options_keyboard(user_id: int, file_path: str) -> InlineKeyboardMarkup:
    """Create upload destination selection keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Upload to Telegram", callback_data=f"upload_tg_{user_id}")],
        [InlineKeyboardButton("🔗 Upload to GoFile", callback_data=f"upload_gofile_{user_id}")],
        [InlineKeyboardButton("☁️ Upload to Drive", callback_data=f"upload_drive_{user_id}")],
        [InlineKeyboardButton("📊 File Info", callback_data=f"file_info_{user_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_upload_{user_id}")]
    ])

def create_confirmation_keyboard(action: str, user_id: int, extra_data: str = "") -> InlineKeyboardMarkup:
    """Create confirmation keyboard for actions"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm_{action}_{user_id}_{extra_data}"),
            InlineKeyboardButton("❌ No", callback_data=f"cancel_{action}_{user_id}")
        ]
    ])

def create_queue_management_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Create queue management keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 Merge Now", callback_data=f"merge_start_{user_id}"),
            InlineKeyboardButton("📊 Queue Info", callback_data=f"queue_info_{user_id}")
        ],
        [
            InlineKeyboardButton("🗑️ Clear Queue", callback_data=f"queue_clear_{user_id}"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings_main")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="start_main")
        ]
    ])

def create_admin_keyboard() -> InlineKeyboardMarkup:
    """Create admin control keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👥 User Stats", callback_data="admin_users"),
            InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban")
        ],
        [
            InlineKeyboardButton("✅ Unban User", callback_data="admin_unban"),
            InlineKeyboardButton("📋 Logs", callback_data="admin_logs")
        ],
        [
            InlineKeyboardButton("🔧 Maintenance", callback_data="admin_maintenance"),
            InlineKeyboardButton("🔙 Back", callback_data="start_main")
        ]
    ])

def create_help_keyboard() -> InlineKeyboardMarkup:
    """Create help navigation keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📹 Video Guide", callback_data="help_video"),
            InlineKeyboardButton("🎵 Audio Guide", callback_data="help_audio")
        ],
        [
            InlineKeyboardButton("📄 Subtitle Guide", callback_data="help_subtitle"),
            InlineKeyboardButton("🔍 Extract Guide", callback_data="help_extract")
        ],
        [
            InlineKeyboardButton("⚙️ Settings Guide", callback_data="help_settings"),
            InlineKeyboardButton("🚀 Quick Start", callback_data="help_quickstart")
        ],
        [
            InlineKeyboardButton("❓ FAQ", callback_data="help_faq"),
            InlineKeyboardButton("🔙 Back", callback_data="start_main")
        ]
    ])

def create_pagination_keyboard(
    items: List[Any], 
    current_page: int, 
    items_per_page: int,
    callback_prefix: str,
    extra_data: str = ""
) -> InlineKeyboardMarkup:
    """Create pagination keyboard for lists"""
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    
    buttons = []
    
    # Navigation buttons
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"{callback_prefix}_page_{current_page-1}_{extra_data}"))
    
    nav_buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop"))
    
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"{callback_prefix}_page_{current_page+1}_{extra_data}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Back button
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="start_main")])
    
    return InlineKeyboardMarkup(buttons)

def create_file_type_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Create file type selection keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 Videos", callback_data=f"filetype_video_{user_id}"),
            InlineKeyboardButton("🎵 Audio", callback_data=f"filetype_audio_{user_id}")
        ],
        [
            InlineKeyboardButton("📄 Subtitles", callback_data=f"filetype_subtitle_{user_id}"),
            InlineKeyboardButton("📋 All Files", callback_data=f"filetype_all_{user_id}")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="start_main")
        ]
    ])

def create_quality_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Create quality selection keyboard for compression"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔥 Best Quality", callback_data=f"quality_best_{user_id}"),
            InlineKeyboardButton("⚡ Balanced", callback_data=f"quality_balanced_{user_id}")
        ],
        [
            InlineKeyboardButton("💾 Small Size", callback_data=f"quality_compress_{user_id}"),
            InlineKeyboardButton("🎛️ Custom", callback_data=f"quality_custom_{user_id}")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="settings_main")
        ]
    ])

def create_language_keyboard(user_id: int, current_lang: str = "en") -> InlineKeyboardMarkup:
    """Create language selection keyboard"""
    languages = [
        ("🇺🇸 English", "en"),
        ("🇮🇳 हिन्दी", "hi"),
        ("🇪🇸 Español", "es"),
        ("🇫🇷 Français", "fr"),
        ("🇩🇪 Deutsch", "de"),
        ("🇷🇺 Русский", "ru"),
        ("🇯🇵 日本語", "ja"),
        ("🇰🇷 한국어", "ko"),
        ("🇨🇳 中文", "zh")
    ]
    
    buttons = []
    for lang_name, lang_code in languages:
        if lang_code == current_lang:
            button_text = f"✅ {lang_name}"
        else:
            button_text = lang_name
        
        buttons.append([InlineKeyboardButton(button_text, callback_data=f"set_lang_{user_id}_{lang_code}")])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="settings_main")])
    
    return InlineKeyboardMarkup(buttons)

def create_progress_keyboard(operation_id: str, user_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for ongoing operations"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_operation_{operation_id}_{user_id}")]
    ])

def create_error_keyboard(error_type: str, user_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for error messages"""
    buttons = [
        [InlineKeyboardButton("🔄 Retry", callback_data=f"retry_{error_type}_{user_id}")],
        [InlineKeyboardButton("❓ Get Help", callback_data="help_main")],
        [InlineKeyboardButton("🔙 Back", callback_data="start_main")]
    ]
    
    return InlineKeyboardMarkup(buttons)

# Utility functions for keyboard management

def add_back_button(keyboard: InlineKeyboardMarkup, callback_data: str = "start_main") -> InlineKeyboardMarkup:
    """Add back button to existing keyboard"""
    buttons = keyboard.inline_keyboard.copy()
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data=callback_data)])
    return InlineKeyboardMarkup(buttons)

def create_custom_keyboard(button_config: List[List[Dict[str, str]]]) -> InlineKeyboardMarkup:
    """Create custom keyboard from configuration"""
    buttons = []
    for row in button_config:
        button_row = []
        for button in row:
            button_row.append(InlineKeyboardButton(button['text'], callback_data=button['callback']))
        buttons.append(button_row)
    
    return InlineKeyboardMarkup(buttons)

# Export all keyboard functions
__all__ = [
    'create_main_keyboard',
    'create_settings_keyboard', 
    'create_merge_mode_keyboard',
    'create_upload_options_keyboard',
    'create_confirmation_keyboard',
    'create_queue_management_keyboard',
    'create_admin_keyboard',
    'create_help_keyboard',
    'create_pagination_keyboard',
    'create_file_type_keyboard',
    'create_quality_keyboard',
    'create_language_keyboard',
    'create_progress_keyboard',
    'create_error_keyboard',
    'add_back_button',
    'create_custom_keyboard'
]
