# ADScriptGen 🎬

**AI-Powered Video Script Generation for Accessibility**

ADScriptGen is an intelligent video processing and script generation tool that creates descriptive audio scripts for videos, making them accessible to visually impaired audiences. The system uses AI to analyze video frames and generate contextual, emotionally engaging descriptions.

## 🌟 Features

- **Video Frame Extraction**: Extract frames from videos at configurable FPS rates
- **Scene Change Detection**: Automatically detect scene transitions using FFmpeg
- **AI-Powered Analysis**: Use OpenAI's GPT-4 Vision to analyze video frames
- **Customizable Script Styles**: Generate scripts in different tones (serious, funny, dramatic, educational)
- **Audience Targeting**: Tailor content for different audiences (children, adults, elderly)
- **Multi-language Support**: Generate scripts in Chinese with timestamp formatting
- **Interactive Frame Selection**: Web-based interface for manual frame selection
- **Comprehensive Metadata**: Extract detailed video information and statistics

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- FFmpeg installed on your system
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/liyamacode/ADScriptGen.git
   cd ADScriptGen
   ```

2. **Install dependencies**
   ```bash
   pip install openai python-dotenv pandas pathlib
   ```

3. **Install FFmpeg**
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`
   - **Windows**: Download from [FFmpeg official website](https://ffmpeg.org/download.html)

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your OpenAI API key
   ```

## 📖 Usage

### 1. Video Processing

Extract frames and analyze video content:

```python
from video_processor import FFmpegVideoProcessor

# Initialize processor
processor = FFmpegVideoProcessor()

# Extract frames from video
frames_dir = processor.extract_frames("your_video.mp4", fps=2)

# Detect scene changes
scene_changes = processor.detect_scene_changes("your_video.mp4")

# Get video metadata
metadata = processor.get_video_metadata("your_video.mp4")
```

### 2. Frame Organization

Organize extracted frames into a searchable table:

```python
from scene_selection import organize_frames_table

# Organize frames with timestamps and scene information
result = organize_frames_table("your_video.mp4", fps=2, scene_threshold=0.3)

if result["status"] == "success":
    print(f"Generated {result['total_frames']} frames across {result['total_scenes']} scenes")
    print(f"CSV file: {result['csv_file']}")
    print(f"HTML interface: {result['html_file']}")
```

### 3. Script Generation

Generate AI-powered descriptive scripts:

```python
from script_generator import analyze_all_frames_together

# Prepare frame data
frames_data = [
    {"timestamp": "00:00:15", "image_path": "frame_0001.jpg"},
    {"timestamp": "00:00:30", "image_path": "frame_0002.jpg"},
    # ... more frames
]

# Generate script with custom style and audience
script = analyze_all_frames_together(
    frames_data=frames_data,
    movie_style="dramatic",  # Options: serious, funny, dramatic, educational, neutral
    target_audience="adults"  # Options: children, adults, elderly, general
)

print(script)
```

### 4. Interactive Frame Selection

1. Run the frame organization script to generate an HTML interface
2. Open the generated HTML file in your browser
3. Select frames you want to include in the script
4. Download the selection as JSON
5. Use the JSON file with the script generator

## 🎨 Script Styles

- **Serious**: Professional, factual descriptions
- **Funny**: Light-hearted, humorous tone
- **Dramatic**: Emotional, atmospheric descriptions
- **Educational**: Informative, explanatory style
- **Neutral**: Balanced, objective tone

## 👥 Target Audiences

- **Children**: Simple vocabulary, positive tone, warm descriptions
- **Adults**: Rich vocabulary, complex concepts
- **Elderly**: Clear, slow-paced descriptions
- **General**: Balanced approach for wide audiences

## 📁 Project Structure

```
ADScriptGen/
├── video_processor.py      # Core video processing functionality
├── scene_selection.py      # Frame organization and selection
├── script_generator.py     # AI-powered script generation
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional: for custom endpoints
```

### FFmpeg Settings

- **FPS**: Control frame extraction rate (default: 2 fps)
- **Scene Threshold**: Adjust scene change sensitivity (0.0-1.0, default: 0.3)
- **Output Quality**: Configure image quality and format

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for providing the GPT-4 Vision API
- FFmpeg for video processing capabilities
- The accessibility community for inspiration and feedback

## 📞 Support

For questions, issues, or contributions, please:

1. Check the [Issues](https://github.com/liyamacode/ADScriptGen/issues) page
2. Create a new issue with detailed information
3. Contact the maintainers

---

**Made with ❤️ for accessibility and inclusive content creation** 