#!/usr/bin/env python3
"""
Simple Frame Organizer - Organize extracted frames into a table with timestamps
"""

import os
import pandas as pd
from pathlib import Path
import subprocess
from datetime import datetime


def organize_frames_table(video_path: str, fps: float = 2, scene_threshold: float = 0.3) -> dict:
    """
    Organize extracted frames into a table with timestamps and scene information.
    Similar to duckduckgo_search but for frame organization.
    
    Args:
        video_path: Path to the video file
        fps: Frames per second to extract
        scene_threshold: Scene change detection threshold
        
    Returns:
        Dictionary containing organization results
    """
    
    if not os.path.exists(video_path):
        return {
            "status": "error",
            "error": f"Video file not found: {video_path}"
        }
    
    try:
        video_name = Path(video_path).stem
        output_dir = f"organized_frames_{video_name}"
        
        print(f"🎬 Organizing frames for: {video_path}")
        
        # Extract frames
        print("📸 Extracting frames...")
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", f"fps={fps}",
            "-f", "image2",
            f"{output_dir}/frame_%04d.jpg"
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        # Get frame files and calculate timestamps
        frame_files = sorted([f for f in os.listdir(output_dir) if f.endswith('.jpg')])
        frames_data = []
        
        for i, frame_file in enumerate(frame_files):
            timestamp = i / fps
            frame_path = os.path.join(output_dir, frame_file)
            
            frames_data.append({
                "Timestamp": format_timestamp(timestamp),
                "Time (seconds)": round(timestamp, 2),
                "Frame Number": i + 1,
                "Frame File": frame_file,
                "Frame Path": frame_path
            })
        
        # Detect scene changes
        print("🎭 Detecting scene changes...")
        scene_changes = detect_scene_changes(video_path, scene_threshold)
        
        # Add scene information to frames
        for frame in frames_data:
            frame_time = frame["Time (seconds)"]
            scene_number = 1
            scene_score = 0.0
            
            for scene in scene_changes:
                if frame_time >= scene["timestamp"]:
                    scene_number += 1
                    scene_score = scene["scene_score"]
                else:
                    break
            
            frame["Scene Number"] = scene_number
            frame["Scene Score"] = scene_score
        
        # Create DataFrame
        df = pd.DataFrame(frames_data)
        
        # Save to CSV
        csv_path = f"{video_name}_frame_table.csv"
        df.to_csv(csv_path, index=False)
        print(f"📊 Frame table saved to: {csv_path}")
        
        # Create HTML table
        html_path = f"{video_name}_frame_table.html"
        create_html_table(df, html_path, video_name)
        
        return {
            "status": "success",
            "video_path": video_path,
            "total_frames": len(df),
            "total_scenes": df["Scene Number"].max(),
            "dataframe": df,
            "csv_file": csv_path,
            "html_file": html_path,
            "frames_directory": output_dir
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def detect_scene_changes(video_path: str, threshold: float = 0.3) -> list:
    """Detect scene changes in the video"""
    
    # Create temporary file for scene detection
    temp_file = "temp_scene_detection.txt"
    with open(temp_file, "w") as f:
        pass
    
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"select='gt(scene,{threshold})',metadata=mode=print:file={temp_file}",
        "-f", "null", "-"
    ]
    
    subprocess.run(cmd, capture_output=True, check=True)
    
    # Parse scene changes
    scene_changes = []
    with open(temp_file, "r") as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            frame_line = lines[i]
            score_line = lines[i + 1]
            
            # Extract timestamp
            import re
            pts_match = re.search(r'pts_time:(\d+\.?\d*)', frame_line)
            score_match = re.search(r'scene_score=(\d+\.?\d*)', score_line)
            
            if pts_match and score_match:
                scene_changes.append({
                    "timestamp": float(pts_match.group(1)),
                    "scene_score": float(score_match.group(1))
                })
    
    # Clean up temporary file
    if os.path.exists(temp_file):
        os.remove(temp_file)
    
    return scene_changes


def format_timestamp(seconds: float) -> str:
    """Format seconds to readable timestamp"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"


def create_html_table(df: pd.DataFrame, output_file: str, video_name: str):
    """Create an HTML table with embedded images, checkboxes, and a submit button to download selected frames as JSON."""

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Frame Table - {video_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .frame-image {{ max-width: 120px; max-height: 90px; }}
        .centered {{ text-align: center; }}
        .submit-btn {{ margin-top: 20px; padding: 10px 20px; font-size: 16px; }}
    </style>
</head>
<body>
    <h1>Frame Table - {video_name}</h1>
    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <form id="frameForm" onsubmit="return false;">
    <table>
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Frame Image</th>
                <th class="centered">Select</th>
            </tr>
        </thead>
        <tbody>
"""

    for _, row in df.iterrows():
        html_content += f"""
        <tr>
            <td>{row['Timestamp']}</td>
            <td><img src="{row['Frame Path']}" class="frame-image" alt="Frame at {row['Timestamp']}"></td>
            <td class="centered"><input type="checkbox" class="frame-checkbox" data-timestamp="{row['Timestamp']}" data-frame="{row['Frame File']}"></td>
        </tr>
"""

    html_content += """
        </tbody>
    </table>
    <button class="submit-btn" onclick="downloadSelectedFrames()">Submit</button>
    </form>
    <script>
    function downloadSelectedFrames() {
        const checkboxes = document.querySelectorAll('.frame-checkbox:checked');
        const selected = [];
        checkboxes.forEach(cb => {
            selected.push({
                timestamp: cb.getAttribute('data-timestamp'),
                frame_file: cb.getAttribute('data-frame')
            });
        });
        const blob = new Blob([JSON.stringify(selected, null, 2)], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;"""
    html_content += f"""
        a.download = '{video_name}_selected_frames.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        """
    html_content += """
    }
    </script>
</body>
</html>
"""

    # Save HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"🌐 HTML table saved to: {output_file}")


# Convenience function similar to duckduckgo_search
def organize_video_frames(video_path: str, **kwargs) -> dict:
    """
    Main function to organize video frames into a table.
    Similar to duckduckgo_search but for frame organization.
    
    Args:
        video_path: Path to the video file
        **kwargs: Additional parameters (fps, scene_threshold)
        
    Returns:
        Dictionary containing organization results
    """
    fps = kwargs.get("fps", 2)
    scene_threshold = kwargs.get("scene_threshold", 0.3)
    
    return organize_frames_table(video_path, fps, scene_threshold)


def organize_existing_frames_table(frames_dir: str, fps: float, video_name: str, video_path: str, scene_threshold: float = 0.3) -> dict:
    """
    Organize already-extracted frames in a directory into a table with timestamps and scene information.
    Args:
        frames_dir: Directory containing extracted frames
        fps: Frames per second used for extraction
        video_name: Name of the video (for output file naming)
        video_path: Path to the original video (for scene detection)
        scene_threshold: Scene change detection threshold
    Returns:
        Dictionary containing organization results
    """
    if not os.path.exists(frames_dir):
        return {
            "status": "error",
            "error": f"Frames directory not found: {frames_dir}"
        }
    try:
        print(f"\U0001F4C2 Organizing existing frames in: {frames_dir}")
        frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
        frames_data = []
        for i, frame_file in enumerate(frame_files):
            timestamp = i / fps
            frame_path = os.path.join(frames_dir, frame_file)
            frames_data.append({
                "Timestamp": format_timestamp(timestamp),
                "Time (seconds)": round(timestamp, 2),
                "Frame Number": i + 1,
                "Frame File": frame_file,
                "Frame Path": frame_path
            })
        # Detect scene changes
        print("\U0001F3AD Detecting scene changes...")
        scene_changes = detect_scene_changes(video_path, scene_threshold)
        # Add scene information to frames
        for frame in frames_data:
            frame_time = frame["Time (seconds)"]
            scene_number = 1
            scene_score = 0.0
            for scene in scene_changes:
                if frame_time >= scene["timestamp"]:
                    scene_number += 1
                    scene_score = scene["scene_score"]
                else:
                    break
            frame["Scene Number"] = scene_number
            frame["Scene Score"] = scene_score
        # Create DataFrame
        df = pd.DataFrame(frames_data)
        # Save to CSV
        csv_path = f"{video_name}_frame_table.csv"
        df.to_csv(csv_path, index=False)
        print(f"\U0001F4CA Frame table saved to: {csv_path}")
        # Create HTML table
        html_path = f"{video_name}_frame_table.html"
        create_html_table(df, html_path, video_name)
        return {
            "status": "success",
            "video_path": video_path,
            "total_frames": len(df),
            "total_scenes": df["Scene Number"].max(),
            "dataframe": df,
            "csv_file": csv_path,
            "html_file": html_path,
            "frames_directory": frames_dir
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# --- CHAINED MAIN ---
def main():
    """Chain: Run extraction/analysis, then organize frames."""
    video_file = input("Enter the path to the video file: ").strip()
    if not video_file:
        print("\u274C No video file provided. Exiting.")
        return
    video_name = Path(video_file).stem
    frames_output_dir = f"{video_name}_extracted_frames"
    fps = 1  # 1 frame per second for extraction
    scene_threshold = 0.2
    # Step 1: Extraction/Analysis (as in example_usage.py)
    try:
        from video_processor import ffmpeg_video_search
    except ImportError:
        print("\u274C video_processor module not found. Please ensure it is available.")
        return
    print("\U0001F50D Example 1: Quick Metadata Analysis")
    print("=" * 50)
    results = ffmpeg_video_search(
        video_file,
        search_type="metadata"
    )
    if results['status'] == 'success':
        metadata = results['results']['metadata']
        print(f"\U0001F4CA Video Information:")
        print(f"   Duration: {metadata.duration:.2f} seconds")
        print(f"   Resolution: {metadata.width}x{metadata.height}")
        print(f"   FPS: {metadata.fps:.2f}")
        print(f"   Codec: {metadata.codec}")
        print(f"   Format: {metadata.format}")
        print(f"   Size: {metadata.size_mb:.2f} MB")
        print(f"   Bitrate: {metadata.bitrate} bps")
    print("\n" + "=" * 50)
    print("\U0001F3AD Example 2: Scene Change Detection")
    print("=" * 50)
    results = ffmpeg_video_search(
        video_file,
        search_type="scenes",
        scene_threshold=scene_threshold
    )
    if results['status'] == 'success':
        scene_changes = results['results']['scene_changes']
        print(f"\U0001F3AC Scene Changes Detected: {len(scene_changes)}")
        for i, scene in enumerate(scene_changes, 1):
            print(f"   {i:2d}. {scene.timestamp:6.2f}s - Score: {scene.scene_score:.3f}")
    print("\n" + "=" * 50)
    print("\U0001F5BC Example 3: Frame Extraction")
    print("=" * 50)
    results = ffmpeg_video_search(
        video_file,
        search_type="frames",
        extract_frames=True,
        frame_fps=fps,
        frames_output_dir=frames_output_dir
    )
    if results['status'] == 'success':
        frames_dir = results['results']['frames']
        print(f"\u2705 Frames extracted to: {frames_dir}")
    else:
        print(f"\u274C Frame extraction failed: {results.get('error', 'Unknown error')}")
        return
    print("\n" + "=" * 50)
    # Step 2: Organize the extracted frames
    result = organize_existing_frames_table(
        frames_output_dir, fps, video_name, video_file, scene_threshold
    )
    if result["status"] == "success":
        print(f"\u2705 Frame organization successful!")
        print(f"\U0001F4CA Total frames: {result['total_frames']}")
        print(f"\U0001F3AD Total scenes: {result['total_scenes']}")
        print(f"\U0001F4C4 CSV file: {result['csv_file']}")
        print(f"\U0001F310 HTML file: {result['html_file']}")
        print(f"\U0001F4C1 Frames directory: {result['frames_directory']}")
        # Show preview of the table
        df = result["dataframe"]
        print(f"\n\U0001F4CB Table Preview (first 5 rows):")
        print(df.head().to_string(index=False))
    else:
        print(f"\u274C Organization failed: {result['error']}")


if __name__ == "__main__":
    main() 