# Enhanced Broadcast Plugin
# Advanced message broadcasting system with progress tracking and user management

import asyncio
import time
from typing import List, Dict, Any, Optional
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait, UserIsBlocked, UserDeactivated, PeerIdInvalid

from config import Config
from helpers.utils import UserSettings, get_readable_time
from helpers.database import database
from helpers.msg_utils import MessageHandler, BroadcastManager, message_handler
from templates.keyboards import create_confirmation_keyboard, create_admin_keyboard
from templates.messages import BROADCAST_TEMPLATE, format_message_template
from __init__ import LOGGER, queueDB

# Global broadcast state
broadcast_state = {
    "active": False,
    "total_users": 0,
    "sent": 0,
    "failed": 0,
    "blocked": 0,
    "progress_message": None
}

@Client.on_message(filters.command(["broadcast"]) & filters.private)
async def broadcast_command(c: Client, m: Message):
    """Handle broadcast command (owner only)"""
    if m.from_user.id != int(Config.OWNER):
        await m.reply_text(
            "🔒 **Owner Only Command!**\n"
            "This command is restricted to the bot owner.",
            quote=True
        )
        return
    
    if broadcast_state["active"]:
        await m.reply_text(
            "🔄 **Broadcast Already Running!**\n"
            "Please wait for the current broadcast to complete.",
            quote=True
        )
        return
    
    # Check for message text
    try:
        broadcast_text = m.text.split(" ", 1)[1].strip()
        if not broadcast_text:
            raise IndexError
    except IndexError:
        await m.reply_text(
            "📝 **Usage:** `/broadcast <message>`\n\n"
            "**Example:** `/broadcast 🎉 New features available! Check out the latest update.`\n\n"
            "**Features:**\n"
            "• Supports text formatting (markdown)\n"
            "• Real-time progress tracking\n"
            "• Automatic retry for failed sends\n"
            "• Detailed delivery statistics",
            quote=True
        )
        return
    
    # Get user count
    if database.connected:
        total_users = await database.get_user_count()
    else:
        total_users = len(queueDB) if queueDB else 0
    
    if total_users == 0:
        await m.reply_text(
            "👥 **No Users Found!**\n"
            "There are no users to broadcast to.",
            quote=True
        )
        return
    
    # Confirmation message
    confirmation_text = f"""📢 **Broadcast Confirmation**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Message Preview:**
{broadcast_text[:200]}{'...' if len(broadcast_text) > 200 else ''}

**📊 Statistics:**
• **Total Users:** {total_users}
• **Estimated Time:** {total_users * 0.1:.1f} seconds
• **Message Length:** {len(broadcast_text)} characters

⚠️ **This will send the message to ALL users!**"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Start Broadcast", callback_data=f"confirm_broadcast_{m.id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")
        ]
    ])
    
    # Store broadcast data temporarily
    broadcast_state["pending_message"] = broadcast_text
    broadcast_state["message_id"] = m.id
    
    await m.reply_text(confirmation_text, reply_markup=keyboard, quote=True)

@Client.on_callback_query(filters.regex(r"confirm_broadcast_(\d+)"))
async def confirm_broadcast_callback(c: Client, cb: CallbackQuery):
    """Confirm and start broadcast"""
    message_id = int(cb.matches[0].group(1))
    
    if cb.from_user.id != int(Config.OWNER):
        await cb.answer("🔒 Owner only!", show_alert=True)
        return
    
    if broadcast_state["active"]:
        await cb.answer("🔄 Broadcast already running!", show_alert=True)
        return
    
    if "pending_message" not in broadcast_state:
        await cb.answer("❌ No pending broadcast found!", show_alert=True)
        return
    
    await cb.answer("🚀 Starting broadcast...")
    await start_broadcast_process(c, cb, broadcast_state["pending_message"])

@Client.on_callback_query(filters.regex(r"cancel_broadcast"))
async def cancel_broadcast_callback(c: Client, cb: CallbackQuery):
    """Cancel pending broadcast"""
    if cb.from_user.id != int(Config.OWNER):
        await cb.answer("🔒 Owner only!", show_alert=True)
        return
    
    # Clear pending broadcast
    if "pending_message" in broadcast_state:
        del broadcast_state["pending_message"]
    if "message_id" in broadcast_state:
        del broadcast_state["message_id"]
    
    await cb.edit_message_text(
        "❌ **Broadcast Cancelled**\n\n"
        "The broadcast operation has been cancelled."
    )
    
    await cb.answer("Broadcast cancelled", show_alert=True)

async def start_broadcast_process(c: Client, cb: CallbackQuery, message_text: str):
    """Start the enhanced broadcast process"""
    try:
        # Mark broadcast as active
        broadcast_state["active"] = True
        broadcast_state["sent"] = 0
        broadcast_state["failed"] = 0
        broadcast_state["blocked"] = 0
        broadcast_state["start_time"] = time.time()
        
        # Get all users
        if database.connected:
            users = await database.get_all_users()
            user_ids = [user["user_id"] for user in users]
        else:
            user_ids = list(queueDB.keys()) if queueDB else []
        
        broadcast_state["total_users"] = len(user_ids)
        
        if not user_ids:
            await cb.edit_message_text(
                "👥 **No Users Found!**\n"
                "There are no users to broadcast to."
            )
            broadcast_state["active"] = False
            return
        
        # Create progress message
        progress_text = f"""🚀 **Broadcast Started**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **Progress:** 0 / {len(user_ids)}
✅ **Sent:** 0
❌ **Failed:** 0
🚫 **Blocked:** 0
⏱️ **Elapsed:** 0s
📈 **Rate:** 0 msg/min

🔄 **Status:** Initializing broadcast..."""
        
        await cb.edit_message_text(progress_text)
        broadcast_state["progress_message"] = cb.message
        
        # Format broadcast message
        formatted_message = format_message_template(
            BROADCAST_TEMPLATE,
            message_content=message_text,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            owner_username=Config.OWNER_USERNAME
        )
        
        # Initialize broadcast manager
        broadcast_manager = BroadcastManager(c)
        
        # Start broadcast with progress tracking
        results = await broadcast_manager.broadcast_message(
            user_ids, 
            formatted_message,
            progress_callback=update_broadcast_progress
        )
        
        # Update final results
        broadcast_state["sent"] = results["sent"]
        broadcast_state["failed"] = results["failed"]
        broadcast_state["blocked"] = results["blocked"]
        
        # Show completion message
        await show_broadcast_completion()
        
    except Exception as e:
        LOGGER.error(f"Broadcast process error: {e}")
        await cb.edit_message_text(
            f"❌ **Broadcast Failed!**\n\n"
            f"**Error:** `{str(e)}`\n"
            f"**Action:** Process terminated"
        )
    finally:
        broadcast_state["active"] = False
        # Clean up pending data
        if "pending_message" in broadcast_state:
            del broadcast_state["pending_message"]

async def update_broadcast_progress(current: int, total: int, results: Dict[str, int]):
    """Update broadcast progress in real-time"""
    if not broadcast_state.get("progress_message"):
        return
    
    try:
        elapsed = time.time() - broadcast_state["start_time"]
        progress_percent = (current / total * 100) if total > 0 else 0
        rate = (current / (elapsed / 60)) if elapsed > 0 else 0
        
        # Create progress bar
        bar_length = 20
        filled_length = int(bar_length * (current / total)) if total > 0 else 0
        progress_bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        progress_text = f"""🚀 **Broadcasting in Progress**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{progress_bar} `{progress_percent:.1f}%`

📊 **Progress:** {current} / {total}
✅ **Sent:** {results['sent']}
❌ **Failed:** {results['failed']}
🚫 **Blocked:** {results['blocked']}
⏱️ **Elapsed:** {get_readable_time(int(elapsed))}
📈 **Rate:** {rate:.1f} msg/min

🔄 **Status:** Broadcasting messages..."""
        
        await message_handler.safe_edit_message(
            broadcast_state["progress_message"], 
            progress_text
        )
        
    except Exception as e:
        LOGGER.warning(f"Progress update failed: {e}")

async def show_broadcast_completion():
    """Show final broadcast completion message"""
    if not broadcast_state.get("progress_message"):
        return
    
    try:
        elapsed = time.time() - broadcast_state["start_time"]
        total = broadcast_state["total_users"]
        sent = broadcast_state["sent"]
        failed = broadcast_state["failed"]
        blocked = broadcast_state["blocked"]
        
        success_rate = (sent / total * 100) if total > 0 else 0
        
        completion_text = f"""✅ **Broadcast Completed!**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Final Statistics:**
• **Total Users:** {total}
• **Successfully Sent:** {sent} ({success_rate:.1f}%)
• **Failed:** {failed}
• **Blocked/Inactive:** {blocked}
• **Total Time:** {get_readable_time(int(elapsed))}
• **Average Rate:** {(sent / (elapsed / 60)):.1f} msg/min

🎯 **Delivery Status:**
{"🟢 Excellent" if success_rate >= 90 else "🟡 Good" if success_rate >= 70 else "🔴 Poor"} delivery rate

**Thank you for using Enhanced MERGE-BOT! 🎉**"""
        
        # Add admin keyboard
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 Detailed Stats", callback_data="broadcast_stats"),
                InlineKeyboardButton("👨‍💼 Admin Panel", callback_data="admin_main")
            ]
        ])
        
        await message_handler.safe_edit_message(
            broadcast_state["progress_message"],
            completion_text,
            reply_markup=keyboard
        )
        
        # Log broadcast completion
        LOGGER.info(f"Broadcast completed: {sent}/{total} sent ({success_rate:.1f}% success)")
        
        # Save broadcast statistics to database
        if database.connected:
            stats = {
                "type": "broadcast",
                "total_users": total,
                "sent": sent,
                "failed": failed,
                "blocked": blocked,
                "success_rate": success_rate,
                "duration": elapsed,
                "timestamp": time.time()
            }
            await database.save_bot_stats(stats)
        
    except Exception as e:
        LOGGER.error(f"Broadcast completion display error: {e}")

@Client.on_callback_query(filters.regex(r"broadcast_stats"))
async def broadcast_stats_callback(c: Client, cb: CallbackQuery):
    """Show detailed broadcast statistics"""
    if cb.from_user.id != int(Config.OWNER):
        await cb.answer("🔒 Owner only!", show_alert=True)
        return
    
    if not database.connected:
        await cb.answer("📊 Database not connected for detailed stats", show_alert=True)
        return
    
    try:
        # Get recent broadcast stats
        recent_stats = await database.get_latest_stats()
        
        if not recent_stats or recent_stats.get("type") != "broadcast":
            await cb.answer("📊 No recent broadcast stats available", show_alert=True)
            return
        
        stats_text = f"""📊 **Detailed Broadcast Statistics**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📈 Performance Metrics:**
• **Total Recipients:** {recent_stats['total_users']}
• **Successful Deliveries:** {recent_stats['sent']}
• **Failed Deliveries:** {recent_stats['failed']}
• **Blocked/Inactive Users:** {recent_stats['blocked']}
• **Success Rate:** {recent_stats['success_rate']:.1f}%

**⏱️ Timing Information:**
• **Total Duration:** {get_readable_time(int(recent_stats['duration']))}
• **Average Speed:** {(recent_stats['sent'] / (recent_stats['duration'] / 60)):.1f} msg/min
• **Broadcast Time:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(recent_stats['timestamp']))}

**🔍 Analysis:**
• **Delivery Quality:** {"🟢 Excellent" if recent_stats['success_rate'] >= 90 else "🟡 Good" if recent_stats['success_rate'] >= 70 else "🔴 Needs Improvement"}
• **User Engagement:** {"🟢 High" if recent_stats['blocked'] < recent_stats['total_users'] * 0.1 else "🟡 Medium" if recent_stats['blocked'] < recent_stats['total_users'] * 0.2 else "🔴 Low"}
• **System Performance:** {"🟢 Optimal" if recent_stats['failed'] < recent_stats['total_users'] * 0.05 else "🟡 Good" if recent_stats['failed'] < recent_stats['total_users'] * 0.1 else "🔴 Poor"}

**💡 Recommendations:**
{"• Consider cleaning inactive users" if recent_stats['blocked'] > recent_stats['total_users'] * 0.15 else "• User base is healthy"}
{"• Check message content if high failure rate" if recent_stats['failed'] > recent_stats['total_users'] * 0.1 else "• System performance is good"}"""
        
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_main")]
        ])
        
        await cb.edit_message_text(stats_text, reply_markup=back_keyboard)
        
    except Exception as e:
        LOGGER.error(f"Broadcast stats error: {e}")
        await cb.answer("❌ Failed to load broadcast statistics", show_alert=True)

@Client.on_message(filters.command(["bstatus"]) & filters.private)
async def broadcast_status_command(c: Client, m: Message):
    """Check current broadcast status (owner only)"""
    if m.from_user.id != int(Config.OWNER):
        await m.reply_text(
            "🔒 **Owner Only Command!**\n"
            "This command is restricted to the bot owner.",
            quote=True
        )
        return
    
    if not broadcast_state["active"]:
        await m.reply_text(
            "📊 **No Active Broadcast**\n\n"
            "There is currently no broadcast operation running.\n"
            "Use `/broadcast <message>` to start a new broadcast.",
            quote=True
        )
        return
    
    # Show current broadcast status
    elapsed = time.time() - broadcast_state["start_time"]
    progress = broadcast_state["sent"] + broadcast_state["failed"] + broadcast_state["blocked"]
    total = broadcast_state["total_users"]
    progress_percent = (progress / total * 100) if total > 0 else 0
    
    status_text = f"""📊 **Current Broadcast Status**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 **Progress:** {progress} / {total} ({progress_percent:.1f}%)
✅ **Sent:** {broadcast_state['sent']}
❌ **Failed:** {broadcast_state['failed']}
🚫 **Blocked:** {broadcast_state['blocked']}
⏱️ **Running Time:** {get_readable_time(int(elapsed))}
📈 **Current Rate:** {(progress / (elapsed / 60)):.1f} msg/min

**Status:** Broadcasting in progress..."""
    
    await m.reply_text(status_text, quote=True)

@Client.on_message(filters.command(["bcancel"]) & filters.private)
async def broadcast_cancel_command(c: Client, m: Message):
    """Cancel active broadcast (owner only)"""
    if m.from_user.id != int(Config.OWNER):
        await m.reply_text(
            "🔒 **Owner Only Command!**\n"
            "This command is restricted to the bot owner.",
            quote=True
        )
        return
    
    if not broadcast_state["active"]:
        await m.reply_text(
            "📊 **No Active Broadcast**\n\n"
            "There is no active broadcast to cancel.",
            quote=True
        )
        return
    
    # Request confirmation
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, Cancel", callback_data="force_cancel_broadcast"),
            InlineKeyboardButton("❌ No, Continue", callback_data="continue_broadcast")
        ]
    ])
    
    await m.reply_text(
        "⚠️ **Cancel Broadcast Confirmation**\n\n"
        "Are you sure you want to cancel the active broadcast?\n"
        "This will stop the operation immediately.",
        reply_markup=keyboard,
        quote=True
    )

@Client.on_callback_query(filters.regex(r"force_cancel_broadcast"))
async def force_cancel_broadcast_callback(c: Client, cb: CallbackQuery):
    """Force cancel active broadcast"""
    if cb.from_user.id != int(Config.OWNER):
        await cb.answer("🔒 Owner only!", show_alert=True)
        return
    
    if broadcast_state["active"]:
        broadcast_state["active"] = False
        
        await cb.edit_message_text(
            "❌ **Broadcast Cancelled!**\n\n"
            "The broadcast operation has been cancelled by admin.\n"
            f"**Progress at cancellation:** {broadcast_state['sent']} messages sent"
        )
        
        LOGGER.info(f"Broadcast cancelled by admin. Progress: {broadcast_state['sent']} sent")
        await cb.answer("Broadcast cancelled successfully", show_alert=True)
    else:
        await cb.answer("No active broadcast to cancel", show_alert=True)

@Client.on_callback_query(filters.regex(r"continue_broadcast"))
async def continue_broadcast_callback(c: Client, cb: CallbackQuery):
    """Continue broadcast operation"""
    if cb.from_user.id != int(Config.OWNER):
        await cb.answer("🔒 Owner only!", show_alert=True)
        return
    
    await cb.edit_message_text(
        "✅ **Broadcast Continuing**\n\n"
        "The broadcast operation will continue running."
    )
    
    await cb.answer("Broadcast will continue", show_alert=True)

# Test broadcast functionality
@Client.on_message(filters.command(["btest"]) & filters.private)
async def test_broadcast_command(c: Client, m: Message):
    """Send test broadcast to owner only"""
    if m.from_user.id != int(Config.OWNER):
        await m.reply_text(
            "🔒 **Owner Only Command!**\n"
            "This command is restricted to the bot owner.",
            quote=True
        )
        return
    
    test_message = """🧪 **Test Broadcast Message**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is a test broadcast from Enhanced MERGE-BOT v6.0!

**Features tested:**
• ✅ Message formatting
• ✅ Delivery system
• ✅ Admin controls

If you receive this message, the broadcast system is working correctly! 🎉

**Enhanced MERGE-BOT v6.0** - @{owner_username}"""
    
    formatted_test = format_message_template(
        test_message,
        owner_username=Config.OWNER_USERNAME
    )
    
    try:
        await c.send_message(
            chat_id=m.from_user.id,
            text=formatted_test
        )
        
        await m.reply_text(
            "✅ **Test Broadcast Sent!**\n\n"
            "The test message has been sent successfully.\n"
            "Broadcast system is functioning correctly.",
            quote=True
        )
        
    except Exception as e:
        await m.reply_text(
            f"❌ **Test Broadcast Failed!**\n\n"
            f"**Error:** `{str(e)}`",
            quote=True
        )

# Export broadcast functions
__all__ = [
    'broadcast_command',
    'confirm_broadcast_callback',
    'cancel_broadcast_callback',
    'start_broadcast_process',
    'update_broadcast_progress',
    'show_broadcast_completion',
    'broadcast_stats_callback',
    'broadcast_status_command',
    'broadcast_cancel_command',
    'test_broadcast_command'
]
