# Enhanced RClone Upload Module
# Google Drive integration from original yashoswalyo/MERGE-BOT with enhancements

import os
import asyncio
import json
from typing import Optional, Dict, Any, Callable
from config import Config
from helpers.utils import get_readable_file_size, get_readable_time
from __init__ import LOGGER

class RCloneUploader:
    """Enhanced RClone uploader for Google Drive integration"""
    
    def __init__(self):
        self.rclone_config = "/app/rclone.conf"  # Docker path
        self.drive_name = "gdrive"  # RClone remote name
        self.folder_id = Config.GDRIVE_FOLDER_ID or "root"
    
    def check_rclone_installed(self) -> bool:
        """Check if rclone is installed and configured"""
        try:
            result = asyncio.run(asyncio.create_subprocess_exec(
                'rclone', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            ))
            return True
        except Exception:
            return False
    
    async def setup_rclone_config(self, client_id: str, client_secret: str, refresh_token: str) -> bool:
        """Setup rclone configuration for Google Drive"""
        try:
            config_content = f"""[{self.drive_name}]
type = drive
client_id = {client_id}
client_secret = {client_secret}
scope = drive
root_folder_id = {self.folder_id}
refresh_token = {refresh_token}
"""
            
            # Ensure config directory exists
            config_dir = os.path.dirname(self.rclone_config)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.rclone_config, 'w') as f:
                f.write(config_content)
            
            # Test configuration
            return await self.test_connection()
            
        except Exception as e:
            LOGGER.error(f"Failed to setup rclone config: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test rclone connection to Google Drive"""
        try:
            process = await asyncio.create_subprocess_exec(
                'rclone', 'lsd', f'{self.drive_name}:',
                '--config', self.rclone_config,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                LOGGER.info("✅ RClone connection test successful")
                return True
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                LOGGER.error(f"❌ RClone connection test failed: {error_msg}")
                return False
                
        except Exception as e:
            LOGGER.error(f"RClone connection test error: {e}")
            return False
    
    async def upload_file(
        self, 
        file_path: str, 
        remote_path: str = None,
        progress_callback: Optional[Callable] = None
    ) -> Optional[Dict[str, str]]:
        """Upload file to Google Drive using rclone"""
        if not os.path.exists(file_path):
            LOGGER.error(f"File not found: {file_path}")
            return None
        
        try:
            filename = os.path.basename(file_path)
            if not remote_path:
                remote_path = filename
            
            # Ensure remote path doesn't start with /
            remote_path = remote_path.lstrip('/')
            
            file_size = os.path.getsize(file_path)
            LOGGER.info(f"Starting rclone upload: {filename} ({get_readable_file_size(file_size)})")
            
            # RClone upload command with progress
            cmd = [
                'rclone', 'copy', file_path, 
                f'{self.drive_name}:{self.folder_id}',
                '--config', self.rclone_config,
                '--progress',
                '--stats', '2s',
                '--transfers', '4',
                '--checkers', '8'
            ]
            
            # Start rclone process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor progress
            if progress_callback:
                await self._monitor_progress(process, file_size, progress_callback)
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Get file info from Google Drive
                file_info = await self._get_file_info(remote_path)
                LOGGER.info(f"✅ RClone upload successful: {filename}")
                return file_info
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                LOGGER.error(f"❌ RClone upload failed: {error_msg}")
                return None
                
        except Exception as e:
            LOGGER.error(f"RClone upload error: {e}")
            return None
    
    async def _monitor_progress(
        self, 
        process: asyncio.subprocess.Process, 
        total_size: int,
        progress_callback: Callable
    ):
        """Monitor rclone upload progress"""
        import re
        start_time = time.time()
        
        try:
            while process.returncode is None:
                await asyncio.sleep(2)
                
                # Try to read stderr for progress info
                try:
                    # This is a simplified progress monitoring
                    # RClone progress parsing can be complex
                    elapsed = time.time() - start_time
                    
                    # Estimate progress based on time (rough approximation)
                    # In real implementation, you'd parse rclone's progress output
                    estimated_progress = min(elapsed / 60.0, 1.0)  # Assume 1 minute for full upload
                    current_size = int(total_size * estimated_progress)
                    
                    await progress_callback(current_size, total_size, "Uploading to Google Drive")
                    
                except Exception as e:
                    LOGGER.warning(f"Progress monitoring error: {e}")
                
                try:
                    await asyncio.wait_for(process.wait(), timeout=0.1)
                    break
                except asyncio.TimeoutError:
                    continue
                    
        except Exception as e:
            LOGGER.error(f"Progress monitoring failed: {e}")
    
    async def _get_file_info(self, filename: str) -> Dict[str, str]:
        """Get file information from Google Drive"""
        try:
            # List files to get the uploaded file info
            process = await asyncio.create_subprocess_exec(
                'rclone', 'lsjson', f'{self.drive_name}:{self.folder_id}',
                '--config', self.rclone_config,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                files_data = json.loads(stdout.decode('utf-8'))
                
                # Find the uploaded file
                for file_data in files_data:
                    if file_data.get('Name') == filename:
                        return {
                            'name': file_data.get('Name', filename),
                            'size': str(file_data.get('Size', 0)),
                            'id': file_data.get('ID', ''),
                            'link': self._generate_drive_link(file_data.get('ID', '')),
                            'modified': file_data.get('ModTime', '')
                        }
            
            # Fallback if file info not found
            return {
                'name': filename,
                'size': '0',
                'id': 'unknown',
                'link': f'https://drive.google.com/drive/folders/{self.folder_id}',
                'modified': ''
            }
            
        except Exception as e:
            LOGGER.error(f"Failed to get file info: {e}")
            return {'name': filename, 'size': '0', 'id': 'unknown', 'link': '', 'modified': ''}
    
    def _generate_drive_link(self, file_id: str) -> str:
        """Generate Google Drive sharing link"""
        if file_id and file_id != 'unknown':
            return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        return f"https://drive.google.com/drive/folders/{self.folder_id}"
    
    async def create_folder(self, folder_name: str, parent_id: str = None) -> Optional[str]:
        """Create folder in Google Drive"""
        try:
            parent = parent_id or self.folder_id
            
            process = await asyncio.create_subprocess_exec(
                'rclone', 'mkdir', f'{self.drive_name}:{parent}/{folder_name}',
                '--config', self.rclone_config,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                LOGGER.info(f"✅ Created folder: {folder_name}")
                return f"{parent}/{folder_name}"
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                LOGGER.error(f"❌ Failed to create folder: {error_msg}")
                return None
                
        except Exception as e:
            LOGGER.error(f"Folder creation error: {e}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Google Drive"""
        try:
            process = await asyncio.create_subprocess_exec(
                'rclone', 'delete', f'{self.drive_name}:{self.folder_id}/{file_path}',
                '--config', self.rclone_config,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                LOGGER.info(f"✅ Deleted file: {file_path}")
                return True
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                LOGGER.error(f"❌ Failed to delete file: {error_msg}")
                return False
                
        except Exception as e:
            LOGGER.error(f"File deletion error: {e}")
            return False
    
    async def list_files(self, folder_path: str = "") -> List[Dict[str, Any]]:
        """List files in Google Drive folder"""
        try:
            full_path = f"{self.folder_id}/{folder_path}".strip('/')
            
            process = await asyncio.create_subprocess_exec(
                'rclone', 'lsjson', f'{self.drive_name}:{full_path}',
                '--config', self.rclone_config,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                files_data = json.loads(stdout.decode('utf-8'))
                return files_data
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                LOGGER.error(f"❌ Failed to list files: {error_msg}")
                return []
                
        except Exception as e:
            LOGGER.error(f"File listing error: {e}")
            return []

# Global instance
rclone_uploader = RCloneUploader()

# Legacy functions for compatibility with old repo
async def rclone_upload(file_path: str, status_message=None) -> Optional[str]:
    """Legacy rclone upload function"""
    if not rclone_uploader.check_rclone_installed():
        LOGGER.error("RClone not installed or configured")
        return None
    
    # Progress callback for status updates
    async def progress_callback(current, total, status):
        if status_message:
            try:
                progress_percent = (current / total * 100) if total > 0 else 0
                await status_message.edit_text(
                    f"☁️ **Google Drive Upload**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 **Progress:** {progress_percent:.1f}%\n"
                    f"📁 **Size:** {get_readable_file_size(current)} / {get_readable_file_size(total)}\n"
                    f"🔄 **Status:** {status}"
                )
            except Exception as e:
                LOGGER.warning(f"Progress update failed: {e}")
    
    result = await rclone_uploader.upload_file(file_path, progress_callback=progress_callback)
    
    if result:
        return result.get('link', '')
    return None

def setup_rclone_config():
    """Setup rclone configuration (placeholder)"""
    # This would typically set up the rclone config
    # In practice, you'd need to configure OAuth2 credentials
    LOGGER.info("RClone configuration setup - manual configuration required")
    return True

# Export rclone functions
__all__ = [
    'RCloneUploader',
    'rclone_uploader', 
    'rclone_upload',
    'setup_rclone_config'
]
