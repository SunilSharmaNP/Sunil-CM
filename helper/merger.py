# Enhanced Merger Module
# Combines robust merging from SunilSharmaNP/Sunil-CM with old repo structure

import os
import time
import asyncio
import subprocess
from typing import List, Optional, Dict, Any
from config import Config
from helpers.utils import get_readable_file_size, format_progress_time
from __init__ import LOGGER, performance_monitor

class EnhancedMerger:
    """
    Enhanced merger combining old repo's features with new repo's robustness
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.output_dir = f"{Config.DOWNLOAD_DIR}/{user_id}"
        self.temp_dir = f"temp/{user_id}"
        self.merged_files = []
        self._ensure_directories()
        
        # Performance tracking
        performance_monitor.start_operation(f"merger_init_{user_id}")
    
    def _ensure_directories(self):
        """Ensure output directories exist"""
        for directory in [self.output_dir, self.temp_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory, mode=0o755, exist_ok=True)
    
    async def merge_videos(self, video_paths: List[str], status_message, output_filename: str = None) -> Optional[str]:
        """
        Enhanced video merging with fallback modes
        """
        if len(video_paths) < 2:
            await status_message.edit_text("❌ **Need at least 2 videos to merge!**")
            return None
        
        if not output_filename:
            timestamp = int(time.time())
            output_filename = f"merged_video_{timestamp}.mp4"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        try:
            performance_monitor.start_operation(f"video_merge_{self.user_id}")
            LOGGER.info(f"Starting video merge for user {self.user_id}: {len(video_paths)} files")
            
            # Try fast mode first (stream copy)
            await status_message.edit_text(
                f"🔧 **Enhanced Merge Process**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 **Files:** {len(video_paths)} videos\n"
                f"⚡ **Mode:** Fast merge (stream copy)\n"
                f"🔄 **Status:** Analyzing compatibility..."
            )
            
            # Check if all videos have compatible formats
            if await self._check_compatibility(video_paths):
                # Try fast merge
                result = await self._fast_merge(video_paths, output_path, status_message)
                if result:
                    performance_monitor.end_operation(f"video_merge_{self.user_id}", success=True)
                    self.merged_files.append(result)
                    return result
            
            # Fallback to robust merge (re-encoding)
            await status_message.edit_text(
                f"🔧 **Enhanced Merge Process**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 **Files:** {len(video_paths)} videos\n"
                f"🛡️ **Mode:** Robust merge (re-encoding)\n"
                f"🔄 **Status:** Processing with quality preservation..."
            )
            
            result = await self._robust_merge(video_paths, output_path, status_message)
            if result:
                performance_monitor.end_operation(f"video_merge_{self.user_id}", success=True)
                self.merged_files.append(result)
                return result
            
            performance_monitor.end_operation(f"video_merge_{self.user_id}", success=False)
            return None
            
        except Exception as e:
            LOGGER.error(f"Video merge error for user {self.user_id}: {e}")
            await status_message.edit_text(
                f"❌ **Merge Failed!**\n"
                f"**Error:** `{str(e)}`\n"
                f"**Suggestion:** Check video formats and try again"
            )
            performance_monitor.end_operation(f"video_merge_{self.user_id}", success=False)
            return None
    
    async def _check_compatibility(self, video_paths: List[str]) -> bool:
        """Check if videos can be merged using fast mode"""
        try:
            # Get info about first video as reference
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', '-show_format', video_paths[0]
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                import json
                info = json.loads(stdout.decode())
                ref_video_codec = None
                ref_audio_codec = None
                
                for stream in info.get('streams', []):
                    if stream['codec_type'] == 'video' and not ref_video_codec:
                        ref_video_codec = stream['codec_name']
                    elif stream['codec_type'] == 'audio' and not ref_audio_codec:
                        ref_audio_codec = stream['codec_name']
                
                # Check if all other videos have same codecs
                for video_path in video_paths[1:]:
                    if not await self._has_compatible_codecs(video_path, ref_video_codec, ref_audio_codec):
                        return False
                
                return True
            
            return False
            
        except Exception as e:
            LOGGER.error(f"Compatibility check error: {e}")
            return False
    
    async def _has_compatible_codecs(self, video_path: str, ref_video_codec: str, ref_audio_codec: str) -> bool:
        """Check if video has compatible codecs with reference"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', video_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                import json
                info = json.loads(stdout.decode())
                
                for stream in info.get('streams', []):
                    if stream['codec_type'] == 'video':
                        if stream['codec_name'] != ref_video_codec:
                            return False
                    elif stream['codec_type'] == 'audio':
                        if stream['codec_name'] != ref_audio_codec:
                            return False
                
                return True
            
            return False
            
        except Exception as e:
            LOGGER.error(f"Codec check error for {video_path}: {e}")
            return False
    
    async def _fast_merge(self, video_paths: List[str], output_path: str, status_message) -> Optional[str]:
        """Fast merge using stream copy (no re-encoding)"""
        try:
            # Create concat file
            concat_file = os.path.join(self.temp_dir, f"concat_{int(time.time())}.txt")
            
            with open(concat_file, 'w', encoding='utf-8') as f:
                for video_path in video_paths:
                    # Use absolute path and escape single quotes
                    abs_path = os.path.abspath(video_path).replace("'", "'\\''")
                    f.write(f"file '{abs_path}'\n")
            
            # FFmpeg command for fast concat
            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', concat_file, '-c', 'copy', output_path
            ]
            
            start_time = time.time()
            
            # Run with progress monitoring
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor progress (simplified for fast mode)
            while process.returncode is None:
                await asyncio.sleep(1)
                elapsed = time.time() - start_time
                await status_message.edit_text(
                    f"⚡ **Fast Merge in Progress...**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔄 **Mode:** Stream copy (no re-encoding)\n"
                    f"⏱️ **Elapsed:** `{format_progress_time(int(elapsed))}`\n"
                    f"📊 **Quality:** Original preserved"
                )
                
                try:
                    await asyncio.wait_for(process.wait(), timeout=0.1)
                    break
                except asyncio.TimeoutError:
                    continue
            
            stdout, stderr = await process.communicate()
            
            # Clean up concat file
            try:
                os.remove(concat_file)
            except:
                pass
            
            if process.returncode == 0 and os.path.exists(output_path):
                # Verify output file
                if os.path.getsize(output_path) > 0:
                    merge_time = time.time() - start_time
                    file_size = get_readable_file_size(os.path.getsize(output_path))
                    
                    await status_message.edit_text(
                        f"✅ **Fast Merge Completed!**\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📁 **Output:** `{os.path.basename(output_path)}`\n"
                        f"📊 **Size:** `{file_size}`\n"
                        f"⏱️ **Time:** `{format_progress_time(int(merge_time))}`\n"
                        f"⚡ **Mode:** Fast (stream copy)\n"
                        f"🎯 **Quality:** Original preserved"
                    )
                    
                    LOGGER.info(f"Fast merge successful: {output_path}")
                    return output_path
            
            # Fast merge failed, will try robust merge
            if os.path.exists(output_path):
                os.remove(output_path)
            
            LOGGER.warning("Fast merge failed, will try robust merge")
            return None
            
        except Exception as e:
            LOGGER.error(f"Fast merge error: {e}")
            return None
    
    async def _robust_merge(self, video_paths: List[str], output_path: str, status_message) -> Optional[str]:
        """Robust merge with re-encoding and progress tracking"""
        try:
            # Create input list
            inputs = []
            for i, video_path in enumerate(video_paths):
                inputs.extend(['-i', video_path])
            
            # Build FFmpeg command with quality settings
            cmd = [
                'ffmpeg', '-y'
            ] + inputs + [
                '-filter_complex',
                f'{"".join([f"[{i}:v][{i}:a]" for i in range(len(video_paths))])}concat=n={len(video_paths)}:v=1:a=1[outv][outa]',
                '-map', '[outv]', '-map', '[outa]',
                '-c:v', Config.VIDEO_CODEC,
                '-crf', str(Config.VIDEO_CRF),
                '-preset', Config.FFMPEG_PRESET,
                '-c:a', Config.AUDIO_CODEC,
                '-b:a', Config.AUDIO_BITRATE,
                output_path
            ]
            
            start_time = time.time()
            last_update = 0
            
            # Get total duration for progress calculation
            total_duration = await self._get_total_duration(video_paths)
            
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor progress
            while process.returncode is None:
                current_time = time.time()
                
                if current_time - last_update >= 3.0:  # Update every 3 seconds
                    elapsed = current_time - start_time
                    
                    # Try to get current progress from output file size (rough estimate)
                    if os.path.exists(output_path):
                        current_size = os.path.getsize(output_path)
                        progress_text = (
                            f"🛡️ **Robust Merge in Progress...**\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"🔄 **Mode:** Re-encoding with quality preservation\n"
                            f"📊 **Current Size:** `{get_readable_file_size(current_size)}`\n"
                            f"⏱️ **Elapsed:** `{format_progress_time(int(elapsed))}`\n"
                            f"🎯 **Quality:** CRF {Config.VIDEO_CRF} ({Config.FFMPEG_PRESET})\n"
                            f"🔧 **Codec:** {Config.VIDEO_CODEC}/{Config.AUDIO_CODEC}"
                        )
                        await status_message.edit_text(progress_text)
                    
                    last_update = current_time
                
                await asyncio.sleep(1)
                
                try:
                    await asyncio.wait_for(process.wait(), timeout=0.1)
                    break
                except asyncio.TimeoutError:
                    continue
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and os.path.exists(output_path):
                # Verify output file
                if os.path.getsize(output_path) > 0:
                    merge_time = time.time() - start_time
                    file_size = get_readable_file_size(os.path.getsize(output_path))
                    
                    await status_message.edit_text(
                        f"✅ **Robust Merge Completed!**\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📁 **Output:** `{os.path.basename(output_path)}`\n"
                        f"📊 **Size:** `{file_size}`\n"
                        f"⏱️ **Time:** `{format_progress_time(int(merge_time))}`\n"
                        f"🛡️ **Mode:** Robust (re-encoded)\n"
                        f"🎯 **Quality:** CRF {Config.VIDEO_CRF}"
                    )
                    
                    LOGGER.info(f"Robust merge successful: {output_path}")
                    return output_path
            
            # Log error details
            if stderr:
                error_output = stderr.decode('utf-8', errors='ignore')[-500:]  # Last 500 chars
                LOGGER.error(f"FFmpeg error output: {error_output}")
            
            await status_message.edit_text(
                f"❌ **Robust Merge Failed!**\n"
                f"FFmpeg process returned error code: {process.returncode}\n"
                f"Check video formats and try again."
            )
            
            return None
            
        except Exception as e:
            LOGGER.error(f"Robust merge error: {e}")
            await status_message.edit_text(f"❌ **Merge Error:** `{str(e)}`")
            return None
    
    async def _get_total_duration(self, video_paths: List[str]) -> float:
        """Get total duration of all videos"""
        total_duration = 0.0
        
        for video_path in video_paths:
            try:
                cmd = [
                    'ffprobe', '-v', 'quiet', '-print_format', 'json',
                    '-show_format', video_path
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    import json
                    info = json.loads(stdout.decode())
                    duration = float(info.get('format', {}).get('duration', 0))
                    total_duration += duration
                    
            except Exception as e:
                LOGGER.error(f"Duration check error for {video_path}: {e}")
                continue
        
        return total_duration
    
    async def cleanup(self):
        """Clean up temporary files and resources"""
        try:
            # Clean temp directory
            if os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                LOGGER.debug(f"Cleaned up temp directory for user {self.user_id}")
            
            # Optional: Clean up merged files if auto-cleanup is enabled
            if Config.AUTO_DELETE_FILES and hasattr(self, 'merged_files'):
                for file_path in self.merged_files:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except:
                        pass
                
                if self.merged_files:
                    LOGGER.info(f"Cleaned up {len(self.merged_files)} merged files for user {self.user_id}")
            
        except Exception as e:
            LOGGER.error(f"Error during merger cleanup: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get merger statistics"""
        return {
            'user_id': self.user_id,
            'output_dir': self.output_dir,
            'temp_dir': self.temp_dir,
            'files_merged': len(self.merged_files) if hasattr(self, 'merged_files') else 0
        }

# Legacy functions for compatibility
async def merge_videos(video_paths: List[str], user_id: int, status_message, output_filename: str = None) -> Optional[str]:
    """Legacy wrapper function for compatibility"""
    merger = EnhancedMerger(user_id)
    try:
        result = await merger.merge_videos(video_paths, status_message, output_filename)
        return result
    finally:
        await merger.cleanup()

# Export main class and functions
__all__ = [
    'EnhancedMerger',
    'merge_videos'
]
