import subprocess
import json
import os
import re
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from pathlib import Path
import tempfile
import shutil


@dataclass
class VideoMetadata:
    """Data class to store video metadata"""
    duration: float
    width: int
    height: int
    fps: float
    bitrate: int
    codec: str
    format: str
    size_mb: float


@dataclass
class SceneChange:
    """Data class to store scene change information"""
    timestamp: float
    frame_number: int
    scene_score: float


@dataclass
class VideoAnalysis:
    """Data class to store comprehensive video analysis results"""
    metadata: VideoMetadata
    scene_changes: List[SceneChange]
    frame_count: int
    audio_duration: float
    transcription: Optional[str] = None
    transcription_timestamps: Optional[List[Dict]] = None


class FFmpegVideoProcessor:
    """
    A comprehensive video processing class similar to duckduckgo_search
    but using FFmpeg for video analysis and processing.
    """
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        Initialize the video processor.
        
        Args:
            ffmpeg_path: Path to FFmpeg executable
        """
        self.ffmpeg_path = ffmpeg_path
        self._check_ffmpeg_availability()
    
    def _check_ffmpeg_availability(self) -> None:
        """Check if FFmpeg is available in the system."""
        try:
            result = subprocess.run([self.ffmpeg_path, "-version"], 
                                  capture_output=True, text=True, check=True)
            print(f"✓ FFmpeg available: {result.stdout.split()[2]}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("FFmpeg not found. Please install FFmpeg first.")
    
    def get_video_metadata(self, video_path: str) -> VideoMetadata:
        """
        Extract comprehensive metadata from a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            VideoMetadata object containing video information
        """
        # Get file size
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
        
        # Get detailed metadata using ffprobe
        probe_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", video_path
        ]
        
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
            audio_stream = next((s for s in data['streams'] if s['codec_type'] == 'audio'), None)
            
            if not video_stream:
                raise ValueError("No video stream found in the file")
            
            return VideoMetadata(
                duration=float(data['format']['duration']),
                width=int(video_stream['width']),
                height=int(video_stream['height']),
                fps=eval(video_stream['r_frame_rate']),  # Convert fraction to float
                bitrate=int(data['format']['bit_rate']),
                codec=video_stream['codec_name'],
                format=data['format']['format_name'],
                size_mb=file_size
            )
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to extract metadata: {e}")
    
    def detect_scene_changes(self, video_path: str, threshold: float = 0.3) -> List[SceneChange]:
        """
        Detect scene changes in a video using FFmpeg.
        
        Args:
            video_path: Path to the video file
            threshold: Scene change detection threshold (0.0 to 1.0)
            
        Returns:
            List of SceneChange objects
        """
        # Create temporary file for scene detection output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_output = tmp_file.name
        
        try:
            cmd = [
                self.ffmpeg_path, "-i", video_path,
                "-vf", f"select='gt(scene,{threshold})',metadata=mode=print:file={tmp_output}",
                "-f", "null", "-"
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            # Parse the output file
            scene_changes = []
            with open(tmp_output, 'r') as f:
                content = f.read()
            
            # Parse scene change data
            lines = content.strip().split('\n')
            for i in range(0, len(lines), 2):
                if i + 1 < len(lines):
                    frame_line = lines[i]
                    score_line = lines[i + 1]
                    
                    # Extract timestamp
                    pts_match = re.search(r'pts_time:(\d+\.?\d*)', frame_line)
                    frame_match = re.search(r'frame:(\d+)', frame_line)
                    score_match = re.search(r'scene_score=(\d+\.?\d*)', score_line)
                    
                    if pts_match and frame_match and score_match:
                        scene_changes.append(SceneChange(
                            timestamp=float(pts_match.group(1)),
                            frame_number=int(frame_match.group(1)),
                            scene_score=float(score_match.group(1))
                        ))
            
            return scene_changes
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_output):
                os.unlink(tmp_output)
    
    def extract_frames(self, video_path: str, fps: float = 2, output_dir: str = "frames") -> str:
        """
        Extract frames from video at specified FPS.
        
        Args:
            video_path: Path to the video file
            fps: Frames per second to extract
            output_dir: Directory to save extracted frames
            
        Returns:
            Path to the output directory
        """
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = [
            self.ffmpeg_path, "-i", video_path,
            "-vf", f"fps={fps}",
            f"{output_dir}/frame_%04d.jpg"
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        return output_dir
    
    def transcribe_audio(self, video_path: str, language: str = None, 
                        output_dir: str = "transcriptions") -> Tuple[str, List[Dict]]:
        """
        Transcribe audio from video using Whisper (if available).
        
        Args:
            video_path: Path to the video file
            language: Language code for transcription
            output_dir: Directory to save transcription files
            
        Returns:
            Tuple of (transcription_text, timestamped_segments)
        """
        try:
            import whisper
        except ImportError:
            raise ImportError("Whisper not installed. Install with: pip install openai-whisper")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Load Whisper model
        model = whisper.load_model("base")
        
        # Transcribe with timestamps
        result = model.transcribe(video_path, language=language, word_timestamps=True)
        
        # Save transcription files
        base_name = Path(video_path).stem
        transcription_path = os.path.join(output_dir, f"{base_name}.txt")
        
        with open(transcription_path, 'w', encoding='utf-8') as f:
            f.write(result["text"])
        
        # Save timestamped segments
        segments_path = os.path.join(output_dir, f"{base_name}_segments.json")
        with open(segments_path, 'w', encoding='utf-8') as f:
            json.dump(result["segments"], f, indent=2, ensure_ascii=False)
        
        return result["text"], result["segments"]
    
    def search_video_content(self, video_path: str, 
                           search_type: str = "all",
                           **kwargs) -> Dict:
        """
        Search and analyze video content - main function similar to duckduckgo_search.
        
        Args:
            video_path: Path to the video file
            search_type: Type of analysis ("metadata", "scenes", "frames", "transcription", "all")
            **kwargs: Additional parameters for specific analysis types
            
        Returns:
            Dictionary containing analysis results
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        results = {
            "video_path": video_path,
            "analysis_type": search_type,
            "results": {}
        }
        
        try:
            if search_type in ["metadata", "all"]:
                results["results"]["metadata"] = self.get_video_metadata(video_path)
            
            if search_type in ["scenes", "all"]:
                threshold = kwargs.get("scene_threshold", 0.3)
                results["results"]["scene_changes"] = self.detect_scene_changes(video_path, threshold)
            
            if search_type in ["frames", "all"]:
                if kwargs.get("extract_frames", False):
                    fps = kwargs.get("frame_fps", 2)
                    output_dir = kwargs.get("frames_output_dir", "frames")
                    results["results"]["frames"] = self.extract_frames(video_path, fps, output_dir)
            
            if search_type in ["transcription", "all"]:
                if kwargs.get("transcribe", False):
                    language = kwargs.get("language", None)
                    text, segments = self.transcribe_audio(video_path, language)
                    results["results"]["transcription"] = {
                        "text": text,
                        "segments": segments
                    }
            
            results["status"] = "success"
            
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
        
        return results


# Convenience function similar to duckduckgo_search
def ffmpeg_video_search(video_path: str, 
                       search_type: str = "all",
                       **kwargs) -> Dict:
    """
    Convenience function for video analysis, similar to duckduckgo_search.
    
    Args:
        video_path: Path to the video file
        search_type: Type of analysis ("metadata", "scenes", "frames", "transcription", "all")
        **kwargs: Additional parameters
        
    Returns:
        Dictionary containing analysis results
    """
    processor = FFmpegVideoProcessor()
    return processor.search_video_content(video_path, search_type, **kwargs)


# Example usage and demonstration
if __name__ == "__main__":
    # Example usage
    processor = FFmpegVideoProcessor()
    
    # Analyze a video file
    video_file = "Movie 1.MP4"
    
    if os.path.exists(video_file):
        print("🎬 FFmpeg Video Processor Demo")
        print("=" * 50)
        
        # Quick search
        results = ffmpeg_video_search(
            video_file,
            search_type="all",
            scene_threshold=0.2,
            extract_frames=True,
            frame_fps=2,
            transcribe=True
        )
        
        print(f"✅ Analysis completed: {results['status']}")
        
        if results['status'] == 'success':
            metadata = results['results']['metadata']
            print(f"\n📊 Video Info:")
            print(f"   Duration: {metadata.duration:.2f} seconds")
            print(f"   Resolution: {metadata.width}x{metadata.height}")
            print(f"   FPS: {metadata.fps:.2f}")
            print(f"   Size: {metadata.size_mb:.2f} MB")
            
            scene_changes = results['results']['scene_changes']
            print(f"\n🎭 Scene Changes: {len(scene_changes)} detected")
            for i, scene in enumerate(scene_changes[:5]):  # Show first 5
                print(f"   {i+1}. {scene.timestamp:.2f}s (score: {scene.scene_score:.3f})")
            
            if 'transcription' in results['results']:
                transcription = results['results']['transcription']['text']
                print(f"\n🎤 Transcription Preview:")
                print(f"   {transcription[:200]}...")
    else:
        print(f"❌ Video file not found: {video_file}")
        print("Please ensure the video file exists in the current directory.") 