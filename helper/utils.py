# Enhanced Utilities Module
# Combines utility functions from both repositories with enhancements

import os
import re
import time
import math
import asyncio
from typing import Optional, Dict, Any, Union
from urllib.parse import urlparse
from config import Config
from __init__ import LOGGER

class UserSettings:
    """
    Enhanced user settings class from old repo with new features
    """
    
    def __init__(self, user_id: int, name: str):
        self.user_id = user_id
        self.name = name
        self.allowed = False
        self.banned = False
        self.merge_mode = 1  # 1=video, 2=audio, 3=subtitle, 4=extract
        self.upload_as_doc = False
        self.upload_to_drive = False
        self.custom_thumbnail = None
        self.language = "en"
        self.compression_enabled = False
        self.auto_delete = True
        
        # Load existing settings
        self._load_settings()
    
    def _load_settings(self):
        """Load user settings from database or file"""
        try:
            # Try to load from database first
            if hasattr(self, '_load_from_database'):
                self._load_from_database()
            else:
                # Fallback to in-memory storage
                self._load_from_memory()
        except Exception as e:
            LOGGER.error(f"Failed to load settings for user {self.user_id}: {e}")
    
    def _load_from_memory(self):
        """Load settings from in-memory storage (fallback)"""
        from __init__ import MERGE_MODE, UPLOAD_AS_DOC, UPLOAD_TO_DRIVE
        
        # Load from global dictionaries
        if self.user_id in MERGE_MODE:
            self.merge_mode = MERGE_MODE[self.user_id]
        if self.user_id in UPLOAD_AS_DOC:
            self.upload_as_doc = UPLOAD_AS_DOC[self.user_id]
        if self.user_id in UPLOAD_TO_DRIVE:
            self.upload_to_drive = UPLOAD_TO_DRIVE[self.user_id]
    
    def set(self):
        """Save user settings"""
        try:
            if hasattr(self, '_save_to_database'):
                self._save_to_database()
            else:
                self._save_to_memory()
        except Exception as e:
            LOGGER.error(f"Failed to save settings for user {self.user_id}: {e}")
    
    def _save_to_memory(self):
        """Save settings to in-memory storage (fallback)"""
        from __init__ import MERGE_MODE, UPLOAD_AS_DOC, UPLOAD_TO_DRIVE
        
        # Save to global dictionaries
        MERGE_MODE[self.user_id] = self.merge_mode
        UPLOAD_AS_DOC[self.user_id] = self.upload_as_doc
        UPLOAD_TO_DRIVE[self.user_id] = self.upload_to_drive
    
    def reset(self):
        """Reset user settings to defaults"""
        self.merge_mode = 1
        self.upload_as_doc = False
        self.upload_to_drive = False
        self.custom_thumbnail = None
        self.compression_enabled = False
        self.auto_delete = True
        self.set()
    
    def get_merge_mode_text(self) -> str:
        """Get human-readable merge mode"""
        modes = {
            1: "📹 Video Merge",
            2: "🎵 Audio Merge", 
            3: "📄 Subtitle Merge",
            4: "🔍 Extract Streams"
        }
        return modes.get(self.merge_mode, "📹 Video Merge")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'allowed': self.allowed,
            'banned': self.banned,
            'merge_mode': self.merge_mode,
            'upload_as_doc': self.upload_as_doc,
            'upload_to_drive': self.upload_to_drive,
            'custom_thumbnail': self.custom_thumbnail,
            'language': self.language,
            'compression_enabled': self.compression_enabled,
            'auto_delete': self.auto_delete
        }

def get_readable_file_size(size_bytes: int) -> str:
    """
    Convert bytes to human readable file size
    Enhanced version with more precision
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def get_readable_time(seconds: int) -> str:
    """
    Convert seconds to human readable time
    Enhanced version with better formatting
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"

def format_progress_time(seconds: int) -> str:
    """
    Format time for progress displays
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds//60}:{seconds%60:02d}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}:{minutes:02d}:{seconds%60:02d}"

def is_valid_url(url: str) -> bool:
    """
    Enhanced URL validation
    """
    try:
        parsed = urlparse(url)
        
        # Check basic URL structure
        if not all([parsed.scheme, parsed.netloc]):
            return False
        
        # Check for supported schemes
        if parsed.scheme not in ['http', 'https', 'ftp']:
            return False
        
        # Check for common video/media file extensions in URL
        valid_extensions = Config.VIDEO_EXTENSIONS + Config.AUDIO_EXTENSIONS + Config.SUBTITLE_EXTENSIONS
        path_lower = parsed.path.lower()
        
        # Allow if path ends with valid extension or if it's a streaming URL
        if any(path_lower.endswith(f'.{ext}') for ext in valid_extensions):
            return True
        
        # Allow common streaming/download domains
        streaming_domains = [
            'youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com',
            'drive.google.com', 'dropbox.com', 'mega.nz', 'mediafire.com',
            'gofile.io', 'file.io', 'transfersh.com'
        ]
        
        if any(domain in parsed.netloc.lower() for domain in streaming_domains):
            return True
        
        # Allow if URL path suggests it's a direct file
        if '/file/' in parsed.path or '/download/' in parsed.path or '/video/' in parsed.path:
            return True
        
        return True  # Allow other URLs for broader compatibility
        
    except Exception as e:
        LOGGER.error(f"URL validation error: {e}")
        return False

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system usage
    """
    # Remove or replace invalid characters
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove extra spaces and dots
    filename = re.sub(r'\s+', ' ', filename).strip()
    filename = re.sub(r'\.+', '.', filename)
    
    # Ensure reasonable length
    if len(filename) > 250:
        name, ext = os.path.splitext(filename)
        filename = name[:240] + ext
    
    return filename

def get_video_info(file_path: str) -> Dict[str, Any]:
    """
    Get video information using ffprobe
    Enhanced version with error handling
    """
    try:
        import subprocess
        import json
        
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            info = json.loads(result.stdout)
            
            # Extract relevant information
            video_info = {
                'duration': 0,
                'width': 0,
                'height': 0,
                'video_codec': 'unknown',
                'audio_codec': 'unknown',
                'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                'bitrate': 0
            }
            
            # Get format information
            if 'format' in info:
                format_info = info['format']
                video_info['duration'] = int(float(format_info.get('duration', 0)))
                video_info['bitrate'] = int(format_info.get('bit_rate', 0))
            
            # Get stream information
            for stream in info.get('streams', []):
                if stream['codec_type'] == 'video':
                    video_info['width'] = stream.get('width', 0)
                    video_info['height'] = stream.get('height', 0)
                    video_info['video_codec'] = stream.get('codec_name', 'unknown')
                elif stream['codec_type'] == 'audio':
                    video_info['audio_codec'] = stream.get('codec_name', 'unknown')
            
            return video_info
    
    except Exception as e:
        LOGGER.error(f"Failed to get video info for {file_path}: {e}")
    
    # Return default info on error
    return {
        'duration': 0,
        'width': 0,
        'height': 0,
        'video_codec': 'unknown',
        'audio_codec': 'unknown',
        'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        'bitrate': 0
    }

def get_progress_bar(progress: float, length: int = 20, filled_char: str = None, empty_char: str = None) -> str:
    """
    Generate progress bar with customizable characters
    """
    filled_char = filled_char or Config.FINISHED_PROGRESS_STR
    empty_char = empty_char or Config.UN_FINISHED_PROGRESS_STR
    
    filled_len = int(length * progress)
    empty_len = length - filled_len
    
    return filled_char * filled_len + empty_char * empty_len

def format_duration(seconds: int) -> str:
    """
    Format duration in HH:MM:SS format
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def estimate_merge_time(file_sizes: list, mode: str = "fast") -> int:
    """
    Estimate merge time based on file sizes and mode
    """
    total_size = sum(file_sizes)
    
    # Rough estimates based on empirical data
    if mode == "fast":
        # Stream copy mode - very fast
        return max(10, total_size // (100 * 1024 * 1024))  # ~100MB/s
    else:
        # Re-encoding mode - slower
        return max(30, total_size // (10 * 1024 * 1024))   # ~10MB/s

def clean_temp_files(directory: str, max_age: int = 3600):
    """
    Clean temporary files older than max_age seconds
    """
    try:
        if not os.path.exists(directory):
            return
        
        current_time = time.time()
        cleaned_files = 0
        
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            try:
                if os.path.isfile(filepath):
                    # Check file age
                    if current_time - os.path.getctime(filepath) > max_age:
                        os.remove(filepath)
                        cleaned_files += 1
                elif os.path.isdir(filepath):
                    # Recursively clean subdirectories
                    clean_temp_files(filepath, max_age)
                    # Remove empty directories
                    if not os.listdir(filepath):
                        os.rmdir(filepath)
                        cleaned_files += 1
            except Exception as e:
                LOGGER.warning(f"Failed to clean {filepath}: {e}")
        
        if cleaned_files > 0:
            LOGGER.info(f"Cleaned {cleaned_files} files from {directory}")
            
    except Exception as e:
        LOGGER.error(f"Error cleaning directory {directory}: {e}")

def validate_video_file(file_path: str) -> bool:
    """
    Validate if file is a valid video file
    """
    try:
        # Check file exists and has size
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return False
        
        # Check file extension
        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        if ext not in Config.VIDEO_EXTENSIONS:
            return False
        
        # Try to get video info
        info = get_video_info(file_path)
        if info['duration'] > 0 and info['width'] > 0 and info['height'] > 0:
            return True
        
        return False
        
    except Exception as e:
        LOGGER.error(f"Video validation error for {file_path}: {e}")
        return False

def create_safe_filename(base_name: str, extension: str = None, max_length: int = 200) -> str:
    """
    Create a safe filename with optional extension
    """
    # Sanitize base name
    safe_name = sanitize_filename(base_name)
    
    # Add extension if provided
    if extension:
        if not extension.startswith('.'):
            extension = '.' + extension
        safe_name += extension
    
    # Ensure length limit
    if len(safe_name) > max_length:
        if extension:
            name_part = safe_name[:-len(extension)]
            safe_name = name_part[:max_length-len(extension)] + extension
        else:
            safe_name = safe_name[:max_length]
    
    return safe_name

async def run_command_async(cmd: list, timeout: int = 300) -> tuple:
    """
    Run command asynchronously with timeout
    Returns (returncode, stdout, stderr)
    """
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return process.returncode, stdout.decode(), stderr.decode()
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise TimeoutError(f"Command timed out after {timeout} seconds")
            
    except Exception as e:
        LOGGER.error(f"Command execution error: {e}")
        return -1, "", str(e)

def get_system_info() -> Dict[str, Any]:
    """
    Get system information for stats
    """
    try:
        import psutil
        import platform
        
        return {
            'platform': platform.system(),
            'platform_version': platform.release(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_total': psutil.disk_usage('/').total,
            'disk_free': psutil.disk_usage('/').free,
            'uptime': time.time() - psutil.boot_time()
        }
    except Exception as e:
        LOGGER.error(f"Failed to get system info: {e}")
        return {}

# Export all utility functions
__all__ = [
    'UserSettings',
    'get_readable_file_size',
    'get_readable_time', 
    'format_progress_time',
    'is_valid_url',
    'sanitize_filename',
    'get_video_info',
    'get_progress_bar',
    'format_duration',
    'estimate_merge_time',
    'clean_temp_files',
    'validate_video_file',
    'create_safe_filename',
    'run_command_async',
    'get_system_info'
]
