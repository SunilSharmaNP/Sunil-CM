# Enhanced Database Module
# MongoDB operations from original yashoswalyo/MERGE-BOT with enhancements

import asyncio
import logging
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
from config import Config
from __init__ import LOGGER

class DatabaseManager:
    """Enhanced Database Manager for MongoDB operations"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.users_collection = None
        self.settings_collection = None
        self.stats_collection = None
        self.logs_collection = None
        self.connected = False
    
    async def initialize(self):
        """Initialize database connection"""
        if not Config.DATABASE_URL:
            LOGGER.warning("No database URL provided, using in-memory storage")
            return False
        
        try:
            self.client = AsyncIOMotorClient(Config.DATABASE_URL)
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Initialize database and collections
            self.database = self.client.enhanced_merge_bot
            self.users_collection = self.database.users
            self.settings_collection = self.database.user_settings
            self.stats_collection = self.database.bot_stats
            self.logs_collection = self.database.activity_logs
            
            # Create indexes for better performance
            await self.users_collection.create_index("user_id", unique=True)
            await self.settings_collection.create_index("user_id", unique=True)
            await self.logs_collection.create_index([("timestamp", -1)])
            
            self.connected = True
            LOGGER.info("✅ Database connected successfully")
            return True
            
        except Exception as e:
            LOGGER.error(f"❌ Database connection failed: {e}")
            self.connected = False
            return False
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.connected = False
            LOGGER.info("Database connection closed")
    
    # ===== USER MANAGEMENT =====
    
    async def add_user(self, user_data: Dict[str, Any]) -> bool:
        """Add new user to database"""
        if not self.connected:
            return False
        
        try:
            # Check if user already exists
            existing = await self.users_collection.find_one({"user_id": user_data["user_id"]})
            if existing:
                return await self.update_user(user_data["user_id"], user_data)
            
            # Add timestamp
            import time
            user_data["created_at"] = time.time()
            user_data["last_active"] = time.time()
            
            await self.users_collection.insert_one(user_data)
            LOGGER.info(f"Added new user: {user_data['user_id']}")
            return True
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to add user: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data from database"""
        if not self.connected:
            return None
        
        try:
            user = await self.users_collection.find_one({"user_id": user_id})
            if user:
                # Update last active time
                import time
                await self.users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"last_active": time.time()}}
                )
            return user
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to get user {user_id}: {e}")
            return None
    
    async def update_user(self, user_id: int, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        if not self.connected:
            return False
        
        try:
            import time
            update_data["last_active"] = time.time()
            
            result = await self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": update_data},
                upsert=True
            )
            return result.acknowledged
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to update user {user_id}: {e}")
            return False
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user from database"""
        if not self.connected:
            return False
        
        try:
            # Delete user and settings
            await self.users_collection.delete_one({"user_id": user_id})
            await self.settings_collection.delete_one({"user_id": user_id})
            LOGGER.info(f"Deleted user: {user_id}")
            return True
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to delete user {user_id}: {e}")
            return False
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users from database"""
        if not self.connected:
            return []
        
        try:
            cursor = self.users_collection.find({})
            users = await cursor.to_list(length=None)
            return users
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to get all users: {e}")
            return []
    
    async def get_user_count(self) -> int:
        """Get total user count"""
        if not self.connected:
            return 0
        
        try:
            count = await self.users_collection.count_documents({})
            return count
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to get user count: {e}")
            return 0
    
    async def ban_user(self, user_id: int, reason: str = "Violation of terms") -> bool:
        """Ban a user"""
        if not self.connected:
            return False
        
        try:
            import time
            ban_data = {
                "banned": True,
                "ban_reason": reason,
                "ban_time": time.time(),
                "allowed": False
            }
            
            result = await self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": ban_data}
            )
            
            if result.modified_count > 0:
                LOGGER.info(f"Banned user {user_id}: {reason}")
                return True
            return False
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to ban user {user_id}: {e}")
            return False
    
    async def unban_user(self, user_id: int) -> bool:
        """Unban a user"""
        if not self.connected:
            return False
        
        try:
            unban_data = {
                "banned": False,
                "ban_reason": None,
                "ban_time": None
            }
            
            result = await self.users_collection.update_one(
                {"user_id": user_id},
                {"$unset": {"ban_reason": "", "ban_time": ""}, "$set": {"banned": False}}
            )
            
            if result.modified_count > 0:
                LOGGER.info(f"Unbanned user {user_id}")
                return True
            return False
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to unban user {user_id}: {e}")
            return False
    
    # ===== USER SETTINGS =====
    
    async def save_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Save user settings to database"""
        if not self.connected:
            return False
        
        try:
            import time
            settings["user_id"] = user_id
            settings["updated_at"] = time.time()
            
            result = await self.settings_collection.update_one(
                {"user_id": user_id},
                {"$set": settings},
                upsert=True
            )
            return result.acknowledged
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to save settings for user {user_id}: {e}")
            return False
    
    async def get_user_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user settings from database"""
        if not self.connected:
            return None
        
        try:
            settings = await self.settings_collection.find_one({"user_id": user_id})
            return settings
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to get settings for user {user_id}: {e}")
            return None
    
    async def delete_user_settings(self, user_id: int) -> bool:
        """Delete user settings"""
        if not self.connected:
            return False
        
        try:
            result = await self.settings_collection.delete_one({"user_id": user_id})
            return result.deleted_count > 0
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to delete settings for user {user_id}: {e}")
            return False
    
    # ===== ACTIVITY LOGGING =====
    
    async def log_activity(self, user_id: int, activity: str, details: Dict[str, Any] = None):
        """Log user activity"""
        if not self.connected:
            return
        
        try:
            import time
            log_entry = {
                "user_id": user_id,
                "activity": activity,
                "details": details or {},
                "timestamp": time.time()
            }
            
            await self.logs_collection.insert_one(log_entry)
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to log activity: {e}")
    
    async def get_user_activity(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user activity logs"""
        if not self.connected:
            return []
        
        try:
            cursor = self.logs_collection.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit)
            
            activities = await cursor.to_list(length=None)
            return activities
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to get activity for user {user_id}: {e}")
            return []
    
    # ===== STATISTICS =====
    
    async def save_bot_stats(self, stats: Dict[str, Any]) -> bool:
        """Save bot statistics"""
        if not self.connected:
            return False
        
        try:
            import time
            stats["timestamp"] = time.time()
            
            await self.stats_collection.insert_one(stats)
            return True
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to save bot stats: {e}")
            return False
    
    async def get_latest_stats(self) -> Optional[Dict[str, Any]]:
        """Get latest bot statistics"""
        if not self.connected:
            return None
        
        try:
            stats = await self.stats_collection.find_one(
                {},
                sort=[("timestamp", -1)]
            )
            return stats
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to get latest stats: {e}")
            return None
    
    # ===== DATABASE MAINTENANCE =====
    
    async def cleanup_old_logs(self, days: int = 30):
        """Clean up old activity logs"""
        if not self.connected:
            return
        
        try:
            import time
            cutoff_time = time.time() - (days * 24 * 3600)
            
            result = await self.logs_collection.delete_many(
                {"timestamp": {"$lt": cutoff_time}}
            )
            
            if result.deleted_count > 0:
                LOGGER.info(f"Cleaned up {result.deleted_count} old log entries")
            
        except PyMongoError as e:
            LOGGER.error(f"Failed to cleanup old logs: {e}")
    
    async def backup_database(self) -> bool:
        """Create database backup"""
        if not self.connected:
            return False
        
        try:
            import time
            import json
            
            # Export all collections
            backup_data = {
                "timestamp": time.time(),
                "users": [],
                "settings": [],
                "stats": []
            }
            
            # Backup users
            async for user in self.users_collection.find({}):
                user["_id"] = str(user["_id"])  # Convert ObjectId to string
                backup_data["users"].append(user)
            
            # Backup settings
            async for setting in self.settings_collection.find({}):
                setting["_id"] = str(setting["_id"])
                backup_data["settings"].append(setting)
            
            # Save backup to file
            backup_filename = f"backup_{int(time.time())}.json"
            with open(f"backups/{backup_filename}", "w") as f:
                json.dump(backup_data, f, indent=2)
            
            LOGGER.info(f"Database backup created: {backup_filename}")
            return True
            
        except Exception as e:
            LOGGER.error(f"Failed to create database backup: {e}")
            return False

# Initialize global database manager
database = DatabaseManager()

# Legacy functions for compatibility with old repo
async def add_user(user_id: int, name: str):
    """Legacy function - add user"""
    user_data = {
        "user_id": user_id,
        "name": name,
        "allowed": False,
        "banned": False
    }
    return await database.add_user(user_data)

async def get_user_count():
    """Legacy function - get user count"""
    return await database.get_user_count()

async def is_user_allowed(user_id: int) -> bool:
    """Legacy function - check if user is allowed"""
    user = await database.get_user(user_id)
    if user:
        return user.get("allowed", False)
    return False

async def allow_user(user_id: int):
    """Legacy function - allow user"""
    return await database.update_user(user_id, {"allowed": True})

async def ban_user_db(user_id: int, reason: str = "Violation"):
    """Legacy function - ban user"""
    return await database.ban_user(user_id, reason)

async def unban_user_db(user_id: int):
    """Legacy function - unban user"""
    return await database.unban_user(user_id)

# Auto-initialize database connection
async def init_database():
    """Initialize database connection on import"""
    if Config.DATABASE_URL:
        await database.initialize()

# Export database functions
__all__ = [
    'DatabaseManager', 'database',
    'add_user', 'get_user_count', 'is_user_allowed', 
    'allow_user', 'ban_user_db', 'unban_user_db',
    'init_database'
]
