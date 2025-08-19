# Enhanced Video Compression Module
# Advanced video compression from SunilSharmaNP/Sunil-CM with enhancements

import os
import asyncio
import time
from typing import Optional, Dict, Any, Callable
from config import Config
from helpers.utils import get_readable_file_size, get_video_info
from __init__ import LOGGER

class VideoCompressor:
    """Enhanced video compressor with multiple quality presets"""
    
    def __init__(self):
        self.presets = {
            'best': {
                'crf': 18,
                'preset': 'slow',
                'audio_bitrate': '256k',
                'description': 'Best quality, larger file size'
            },
            'balanced': {
                'crf': 23,
                'preset': 'medium',
                'audio_bitrate': '192k', 
                'description': 'Balanced quality and size'
            },
            'compressed': {
                'crf': 28,
                'preset': 'fast',
                'audio_bitrate': '128k',
                'description': 'Smaller size, lower quality'
            },
            'ultra_compressed': {
                'crf': 32,
                'preset': 'veryfast',
                'audio_bitrate': '96k',
                'description': 'Minimum size, basic quality'
            }
        }
    
    async def compress_video(
        self,
        input_path: str,
        output_path: str,
        quality: str = 'balanced',
        target_size_mb: Optional[int] = None,
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """Compress video with specified quality preset"""
        if not os.path.exists(input_path):
            LOGGER.error(f"Input file not found: {input_path}")
            return False
        
        try:
            # Get video info
            video_info = get_video_info(input_path)
            duration = video_info.get('duration', 0)
            
            if duration <= 0:
                LOGGER.error("Could not determine video duration")
                return False
            
            # Choose compression settings
            if target_size_mb:
                settings = await self._calculate_bitrate_for_size(
                    input_path, target_size_mb, duration
                )
            else:
                settings = self.presets.get(quality, self.presets['balanced'])
            
            # Build FFmpeg command
            cmd = self._build_compression_command(input_path, output_path, settings)
            
            LOGGER.info(f"Starting compression: {quality} preset")
            LOGGER.info(f"Command: {' '.join(cmd)}")
            
            # Run compression with progress monitoring
            success = await self._run_compression(cmd, duration, progress_callback)
            
            if success and os.path.exists(output_path):
                # Verify output file
                original_size = os.path.getsize(input_path)
                compressed_size = os.path.getsize(output_path)
                compression_ratio = (1 - compressed_size / original_size) * 100
                
                LOGGER.info(f"✅ Compression completed!")
                LOGGER.info(f"   Original: {get_readable_file_size(original_size)}")
                LOGGER.info(f"   Compressed: {get_readable_file_size(compressed_size)}")
                LOGGER.info(f"   Saved: {compression_ratio:.1f}%")
                
                return True
            else:
                LOGGER.error("❌ Compression failed")
                return False
                
        except Exception as e:
            LOGGER.error(f"Compression error: {e}")
            return False
    
    def _build_compression_command(
        self, 
        input_path: str, 
        output_path: str, 
        settings: Dict[str, Any]
    ) -> list:
        """Build FFmpeg command for compression"""
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-c:v', Config.VIDEO_CODEC,
            '-crf', str(settings.get('crf', 23)),
            '-preset', settings.get('preset', 'medium'),
            '-c:a', Config.AUDIO_CODEC,
            '-b:a', settings.get('audio_bitrate', '192k'),
            '-movflags', '+faststart',  # Optimize for streaming
            '-pix_fmt', 'yuv420p',  # Ensure compatibility
        ]
        
        # Add custom video bitrate if specified
        if 'video_bitrate' in settings:
            cmd.extend(['-b:v', settings['video_bitrate']])
        
        # Add resolution scaling if specified
        if 'scale' in settings:
            cmd.extend(['-vf', f"scale={settings['scale']}"])
        
        # Add frame rate limit if specified
        if 'fps' in settings:
            cmd.extend(['-r', str(settings['fps'])])
        
        cmd.append(output_path)
        return cmd
    
    async def _calculate_bitrate_for_size(
        self, 
        input_path: str, 
        target_mb: int, 
        duration: float
    ) -> Dict[str, Any]:
        """Calculate bitrate to achieve target file size"""
        target_bits = target_mb * 8 * 1024 * 1024  # Convert MB to bits
        duration_seconds = duration
        
        # Reserve 20% for audio
        audio_bitrate_kbps = 128  # Default audio bitrate
        audio_bits = audio_bitrate_kbps * 1000 * duration_seconds
        
        # Calculate video bitrate
        video_bits = target_bits - audio_bits
        video_bitrate_bps = video_bits / duration_seconds
        video_bitrate_kbps = int(video_bitrate_bps / 1000)
        
        # Ensure minimum quality
        video_bitrate_kbps = max(video_bitrate_kbps, 500)  # Minimum 500 kbps
        
        LOGGER.info(f"Target size: {target_mb}MB")
        LOGGER.info(f"Calculated video bitrate: {video_bitrate_kbps}k")
        
        return {
            'video_bitrate': f'{video_bitrate_kbps}k',
            'audio_bitrate': f'{audio_bitrate_kbps}k',
            'crf': None,  # Don't use CRF when targeting specific bitrate
            'preset': 'medium',
            'description': f'Optimized for {target_mb}MB target size'
        }
    
    async def _run_compression(
        self, 
        cmd: list, 
        duration: float,
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """Run FFmpeg compression with progress monitoring"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            start_time = time.time()
            last_update = 0
            
            # Monitor process
            while process.returncode is None:
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Update progress every 3 seconds
                if progress_callback and (current_time - last_update) >= 3.0:
                    # Estimate progress based on time (rough approximation)
                    estimated_progress = min(elapsed / (duration * 0.5), 1.0)  # Assume compression takes 50% of video duration
                    
                    try:
                        await progress_callback(
                            int(estimated_progress * 100), 
                            100, 
                            f"Compressing... ({elapsed:.0f}s elapsed)"
                        )
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
            
            if process.returncode == 0:
                return True
            else:
                error_output = stderr.decode('utf-8', errors='ignore')[-500:]
                LOGGER.error(f"FFmpeg compression error: {error_output}")
                return False
                
        except Exception as e:
            LOGGER.error(f"Compression process error: {e}")
            return False
    
    async def get_compression_estimate(
        self, 
        input_path: str, 
        quality: str = 'balanced'
    ) -> Dict[str, Any]:
        """Get estimated compression results without actually compressing"""
        try:
            video_info = get_video_info(input_path)
            original_size = os.path.getsize(input_path)
            
            # Rough estimates based on quality preset
            compression_ratios = {
                'best': 0.85,       # 15% reduction
                'balanced': 0.65,   # 35% reduction  
                'compressed': 0.45, # 55% reduction
                'ultra_compressed': 0.30  # 70% reduction
            }
            
            ratio = compression_ratios.get(quality, 0.65)
            estimated_size = int(original_size * ratio)
            
            preset_info = self.presets.get(quality, self.presets['balanced'])
            
            return {
                'original_size': original_size,
                'original_size_str': get_readable_file_size(original_size),
                'estimated_size': estimated_size,
                'estimated_size_str': get_readable_file_size(estimated_size),
                'reduction_percent': int((1 - ratio) * 100),
                'quality_preset': quality,
                'description': preset_info['description'],
                'estimated_time_minutes': int(video_info.get('duration', 0) / 60 * 0.5)  # Rough estimate
            }
            
        except Exception as e:
            LOGGER.error(f"Compression estimate error: {e}")
            return {}
    
    def get_available_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get all available compression presets"""
        return self.presets.copy()
    
    async def create_custom_preset(
        self, 
        name: str, 
        crf: int, 
        preset: str, 
        audio_bitrate: str,
        description: str = ""
    ) -> bool:
        """Create custom compression preset"""
        try:
            if not (15 <= crf <= 35):
                LOGGER.error("CRF must be between 15 and 35")
                return False
            
            valid_presets = ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow']
            if preset not in valid_presets:
                LOGGER.error(f"Invalid preset. Must be one of: {valid_presets}")
                return False
            
            self.presets[name] = {
                'crf': crf,
                'preset': preset,
                'audio_bitrate': audio_bitrate,
                'description': description or f"Custom preset: CRF {crf}, {preset}"
            }
            
            LOGGER.info(f"✅ Created custom preset: {name}")
            return True
            
        except Exception as e:
            LOGGER.error(f"Failed to create custom preset: {e}")
            return False

# Global compressor instance
video_compressor = VideoCompressor()

# Legacy functions for compatibility
async def compress_video(
    input_path: str, 
    output_path: str, 
    quality: str = 'balanced',
    progress_callback: Optional[Callable] = None
) -> bool:
    """Legacy compression function"""
    return await video_compressor.compress_video(input_path, output_path, quality, progress_callback=progress_callback)

def get_compression_presets() -> Dict[str, str]:
    """Get available compression presets (legacy)"""
    presets = video_compressor.get_available_presets()
    return {name: info['description'] for name, info in presets.items()}

# Export compression functions
__all__ = [
    'VideoCompressor',
    'video_compressor',
    'compress_video', 
    'get_compression_presets'
]
