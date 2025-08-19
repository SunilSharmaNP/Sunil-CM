# Enhanced FFmpeg Helper Module
# Advanced FFmpeg operations from original yashoswalyo/MERGE-BOT with enhancements

import os
import re
import json
import asyncio
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from config import Config
from __init__ import LOGGER

class FFmpegHelper:
    """Enhanced FFmpeg helper with advanced operations"""
    
    @staticmethod
    def check_ffmpeg() -> bool:
        """Check if FFmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    async def get_video_info(file_path: str) -> Dict[str, Any]:
        """Get comprehensive video information using ffprobe"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', '-show_chapters', file_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            if process.returncode == 0:
                probe_data = json.loads(stdout.decode('utf-8'))
                return FFmpegHelper._parse_probe_data(probe_data)
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                LOGGER.error(f"FFprobe failed: {error_msg}")
                return {}
                
        except asyncio.TimeoutError:
            LOGGER.error(f"FFprobe timeout for file: {file_path}")
            return {}
        except Exception as e:
            LOGGER.error(f"FFprobe error: {e}")
            return {}
    
    @staticmethod
    def _parse_probe_data(probe_data: Dict) -> Dict[str, Any]:
        """Parse ffprobe output into structured information"""
        info = {
            'duration': 0,
            'size': 0,
            'bitrate': 0,
            'format_name': 'unknown',
            'video_streams': [],
            'audio_streams': [],
            'subtitle_streams': [],
            'chapters': []
        }
        
        # Parse format information
        if 'format' in probe_data:
            format_info = probe_data['format']
            info['duration'] = float(format_info.get('duration', 0))
            info['size'] = int(format_info.get('size', 0))
            info['bitrate'] = int(format_info.get('bit_rate', 0))
            info['format_name'] = format_info.get('format_name', 'unknown')
        
        # Parse streams
        if 'streams' in probe_data:
            for stream in probe_data['streams']:
                stream_type = stream.get('codec_type', 'unknown')
                
                if stream_type == 'video':
                    video_info = {
                        'index': stream.get('index', 0),
                        'codec': stream.get('codec_name', 'unknown'),
                        'width': stream.get('width', 0),
                        'height': stream.get('height', 0),
                        'fps': FFmpegHelper._parse_fps(stream.get('r_frame_rate', '0/1')),
                        'bitrate': int(stream.get('bit_rate', 0)),
                        'pixel_format': stream.get('pix_fmt', 'unknown')
                    }
                    info['video_streams'].append(video_info)
                
                elif stream_type == 'audio':
                    audio_info = {
                        'index': stream.get('index', 0),
                        'codec': stream.get('codec_name', 'unknown'),
                        'channels': stream.get('channels', 0),
                        'sample_rate': stream.get('sample_rate', 0),
                        'bitrate': int(stream.get('bit_rate', 0)),
                        'language': stream.get('tags', {}).get('language', 'unknown')
                    }
                    info['audio_streams'].append(audio_info)
                
                elif stream_type == 'subtitle':
                    subtitle_info = {
                        'index': stream.get('index', 0),
                        'codec': stream.get('codec_name', 'unknown'),
                        'language': stream.get('tags', {}).get('language', 'unknown'),
                        'title': stream.get('tags', {}).get('title', '')
                    }
                    info['subtitle_streams'].append(subtitle_info)
        
        # Parse chapters
        if 'chapters' in probe_data:
            for chapter in probe_data['chapters']:
                chapter_info = {
                    'start': float(chapter.get('start_time', 0)),
                    'end': float(chapter.get('end_time', 0)),
                    'title': chapter.get('tags', {}).get('title', '')
                }
                info['chapters'].append(chapter_info)
        
        return info
    
    @staticmethod
    def _parse_fps(fps_string: str) -> float:
        """Parse frame rate string like '25/1' to float"""
        try:
            if '/' in fps_string:
                num, den = fps_string.split('/')
                return float(num) / float(den)
            return float(fps_string)
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    @staticmethod
    async def merge_videos_concat(
        input_files: List[str], 
        output_file: str,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """Merge videos using concat demuxer (fast, no re-encoding)"""
        try:
            # Create concat file
            concat_file = f"{output_file}.concat"
            
            with open(concat_file, 'w', encoding='utf-8') as f:
                for file_path in input_files:
                    # Use absolute path and escape single quotes
                    abs_path = os.path.abspath(file_path).replace("'", "'\\''")
                    f.write(f"file '{abs_path}'\n")
            
            # FFmpeg concat command
            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', concat_file, '-c', 'copy', output_file
            ]
            
            success = await FFmpegHelper._run_ffmpeg_with_progress(
                cmd, progress_callback, "Merging videos (fast mode)"
            )
            
            # Cleanup concat file
            try:
                os.remove(concat_file)
            except:
                pass
            
            return success
            
        except Exception as e:
            LOGGER.error(f"Video concat merge failed: {e}")
            return False
    
    @staticmethod
    async def merge_videos_complex(
        input_files: List[str],
        output_file: str,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """Merge videos using complex filter (robust, with re-encoding)"""
        try:
            cmd = ['ffmpeg', '-y']
            
            # Add input files
            for file_path in input_files:
                cmd.extend(['-i', file_path])
            
            # Complex filter for concatenation
            filter_complex = ''.join([f'[{i}:v][{i}:a]' for i in range(len(input_files))])
            filter_complex += f'concat=n={len(input_files)}:v=1:a=1[outv][outa]'
            
            cmd.extend([
                '-filter_complex', filter_complex,
                '-map', '[outv]', '-map', '[outa]',
                '-c:v', Config.VIDEO_CODEC,
                '-crf', str(Config.VIDEO_CRF),
                '-preset', Config.FFMPEG_PRESET,
                '-c:a', Config.AUDIO_CODEC,
                '-b:a', Config.AUDIO_BITRATE,
                output_file
            ])
            
            return await FFmpegHelper._run_ffmpeg_with_progress(
                cmd, progress_callback, "Merging videos (robust mode)"
            )
            
        except Exception as e:
            LOGGER.error(f"Video complex merge failed: {e}")
            return False
    
    @staticmethod
    async def add_audio_to_video(
        video_file: str,
        audio_files: List[str],
        output_file: str,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """Add multiple audio tracks to video"""
        try:
            cmd = ['ffmpeg', '-y', '-i', video_file]
            
            # Add audio inputs
            for audio_file in audio_files:
                cmd.extend(['-i', audio_file])
            
            # Map video stream
            cmd.extend(['-map', '0:v'])
            
            # Map original audio if exists
            cmd.extend(['-map', '0:a?'])
            
            # Map additional audio streams
            for i in range(len(audio_files)):
                cmd.extend(['-map', f'{i+1}:a'])
            
            # Output settings
            cmd.extend([
                '-c:v', 'copy',  # Copy video without re-encoding
                '-c:a', Config.AUDIO_CODEC,
                '-b:a', Config.AUDIO_BITRATE,
                output_file
            ])
            
            return await FFmpegHelper._run_ffmpeg_with_progress(
                cmd, progress_callback, "Adding audio tracks"
            )
            
        except Exception as e:
            LOGGER.error(f"Audio addition failed: {e}")
            return False
    
    @staticmethod
    async def add_subtitles_to_video(
        video_file: str,
        subtitle_files: List[str],
        output_file: str,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """Add subtitle tracks to video"""
        try:
            cmd = ['ffmpeg', '-y', '-i', video_file]
            
            # Add subtitle inputs
            for subtitle_file in subtitle_files:
                cmd.extend(['-i', subtitle_file])
            
            # Map video and audio streams
            cmd.extend(['-map', '0:v', '-map', '0:a'])
            
            # Map subtitle streams
            for i in range(len(subtitle_files)):
                cmd.extend(['-map', f'{i+1}:s'])
            
            # Output settings
            cmd.extend([
                '-c:v', 'copy',  # Copy video without re-encoding
                '-c:a', 'copy',  # Copy audio without re-encoding
                '-c:s', 'mov_text',  # Convert subtitles to MP4 compatible format
                output_file
            ])
            
            return await FFmpegHelper._run_ffmpeg_with_progress(
                cmd, progress_callback, "Adding subtitles"
            )
            
        except Exception as e:
            LOGGER.error(f"Subtitle addition failed: {e}")
            return False
    
    @staticmethod
    async def extract_audio(
        video_file: str,
        output_file: str,
        audio_codec: str = 'mp3',
        bitrate: str = '192k',
        progress_callback: Optional[callable] = None
    ) -> bool:
        """Extract audio from video"""
        try:
            cmd = [
                'ffmpeg', '-y', '-i', video_file,
                '-vn',  # No video
                '-c:a', audio_codec,
                '-b:a', bitrate,
                output_file
            ]
            
            return await FFmpegHelper._run_ffmpeg_with_progress(
                cmd, progress_callback, "Extracting audio"
            )
            
        except Exception as e:
            LOGGER.error(f"Audio extraction failed: {e}")
            return False
    
    @staticmethod
    async def extract_subtitles(
        video_file: str,
        output_dir: str,
        progress_callback: Optional[callable] = None
    ) -> List[str]:
        """Extract all subtitle streams from video"""
        try:
            # Get video info to find subtitle streams
            video_info = await FFmpegHelper.get_video_info(video_file)
            subtitle_streams = video_info.get('subtitle_streams', [])
            
            if not subtitle_streams:
                return []
            
            extracted_files = []
            base_name = os.path.splitext(os.path.basename(video_file))[0]
            
            for i, subtitle in enumerate(subtitle_streams):
                stream_index = subtitle['index']
                language = subtitle.get('language', 'unknown')
                
                output_file = os.path.join(
                    output_dir, 
                    f"{base_name}.{language}.{i}.srt"
                )
                
                cmd = [
                    'ffmpeg', '-y', '-i', video_file,
                    '-map', f'0:s:{i}',
                    '-c:s', 'srt',
                    output_file
                ]
                
                success = await FFmpegHelper._run_ffmpeg_with_progress(
                    cmd, progress_callback, f"Extracting subtitle {i+1}"
                )
                
                if success and os.path.exists(output_file):
                    extracted_files.append(output_file)
            
            return extracted_files
            
        except Exception as e:
            LOGGER.error(f"Subtitle extraction failed: {e}")
            return []
    
    @staticmethod
    async def generate_thumbnail(
        video_file: str,
        output_file: str,
        timestamp: Optional[float] = None,
        width: int = 320,
        height: int = 180
    ) -> bool:
        """Generate thumbnail from video"""
        try:
            if timestamp is None:
                # Get video duration and use middle frame
                video_info = await FFmpegHelper.get_video_info(video_file)
                duration = video_info.get('duration', 0)
                timestamp = duration / 2 if duration > 0 else 10
            
            cmd = [
                'ffmpeg', '-y', '-i', video_file,
                '-ss', str(timestamp),
                '-vframes', '1',
                '-filter:v', f'scale={width}:{height}',
                '-q:v', '2',
                output_file
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            return process.returncode == 0 and os.path.exists(output_file)
            
        except Exception as e:
            LOGGER.error(f"Thumbnail generation failed: {e}")
            return False
    
    @staticmethod
    async def _run_ffmpeg_with_progress(
        cmd: List[str],
        progress_callback: Optional[callable] = None,
        operation: str = "Processing"
    ) -> bool:
        """Run FFmpeg command with progress monitoring"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor progress
            start_time = time.time()
            last_update = 0
            
            while process.returncode is None:
                current_time = time.time()
                
                if progress_callback and (current_time - last_update) >= 3.0:
                    elapsed = current_time - start_time
                    if hasattr(progress_callback, '__call__'):
                        try:
                            await progress_callback(operation, elapsed)
                        except Exception as e:
                            LOGGER.warning(f"Progress callback error: {e}")
                    last_update = current_time
                
                await asyncio.sleep(1)
                
                try:
                    await asyncio.wait_for(process.wait(), timeout=0.1)
                    break
                except asyncio.TimeoutError:
                    continue
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_output = stderr.decode('utf-8', errors='ignore')[-500:]
                LOGGER.error(f"FFmpeg error: {error_output}")
                return False
            
            return True
            
        except Exception as e:
            LOGGER.error(f"FFmpeg execution error: {e}")
            return False

# Legacy functions for compatibility with old repo
def get_duration(file_path: str) -> int:
    """Legacy function to get video duration"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', file_path
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            duration = data.get('format', {}).get('duration', '0')
            return int(float(duration))
        return 0
    except Exception:
        return 0

def get_thumbnail(video_path: str, thumbnail_path: str, timestamp: str = "10") -> bool:
    """Legacy function to generate thumbnail"""
    try:
        cmd = [
            'ffmpeg', '-hide_banner', '-loglevel', 'error',
            '-i', video_path, '-ss', timestamp, '-vframes', '1',
            '-c:v', 'mjpeg', '-f', 'image2', '-y', thumbnail_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0 and os.path.exists(thumbnail_path)
    except Exception:
        return False

def get_video_resolution(file_path: str) -> Tuple[int, int]:
    """Legacy function to get video resolution"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', '-select_streams', 'v:0', file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            streams = data.get('streams', [])
            if streams:
                width = streams[0].get('width', 0)
                height = streams.get('height', 0)
                return width, height
        return 0, 0
    except Exception:
        return 0, 0

# Export FFmpeg helper functions
__all__ = [
    'FFmpegHelper',
    'get_duration',
    'get_thumbnail', 
    'get_video_resolution'
]
