import os
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def analyze_all_frames_together(frames_data, movie_style, target_audience):
    """
    Send all selected frames to the LLM in a single API call for comprehensive analysis
    """
    try:
        # Create personalized prompt based on style and audience
        style_instructions = ""
        if movie_style == "serious":
            style_instructions = "保持严肃、专业的语调，避免幽默或轻松的表达。"
        elif movie_style == "funny":
            style_instructions = "使用轻松、幽默的语调，可以适当添加有趣的描述。"
        elif movie_style == "dramatic":
            style_instructions = "使用戏剧性的语调，强调情感和氛围。"
        elif movie_style == "educational":
            style_instructions = "使用教育性的语调，注重解释和说明。"
        else:
            style_instructions = "使用中性、平衡的语调。"

        audience_instructions = ""
        if target_audience == "children":
            audience_instructions = "使用简单易懂的词汇，避免复杂概念，保持积极、快乐的氛围，使用温暖的语调。"
        elif target_audience == "adults":
            audience_instructions = "可以使用更丰富的词汇和概念，适合成年人的理解水平。"
        elif target_audience == "elderly":
            audience_instructions = "使用清晰、缓慢的描述，避免快速变化的场景描述，保持温和的语调。"
        else:
            audience_instructions = "使用适合一般观众的平衡语调。"

        # Prepare all images for the API call
        content = [
            {
                "type": "text",
                "text": f"""你正在分析一系列讲述故事的视频帧。

请检查所有帧并创建一系列简洁但富有情感和全面的描述，这些描述可以在特定的时间间隔内进行语音播报。

电影风格：{movie_style}
目标观众：{target_audience}

要求：
1. 为每一帧创建简洁但富有情感和全面的描述，可以在几秒钟内说完
2. 在每个描述的开头包含时间戳（例如："00:00:15: 显示了一张海报..."）
3. 专注于事实观察 - 描述你看到的内容（物体、颜色、位置、动作）
4. 保持每个描述简短明了 - 适合音频叙述
5. 以清晰、按时间顺序的方式编写，适合视障观众
6. 每个描述应该足够短，可以在其代表的时间间隔内说完
7. 所有的描述连在一起应该是具有一定的故事性
8. 请用中文回答

风格要求：
- {style_instructions}
- {audience_instructions}

请将你的回答格式化为一系列时间戳描述，每个帧一个描述。"""
            }
        ]
        
        # Add each image with its timestamp
        for frame_info in frames_data:
            timestamp = frame_info["timestamp"]
            image_path = frame_info["image_path"]
            
            # Encode the image
            base64_image = encode_image_to_base64(image_path)
            if not base64_image:
                print(f"Warning: Could not encode image {image_path}")
                continue
                
            # Add image to content
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })
            
            # Add timestamp label
            content.append({
                "type": "text",
                "text": f"\n[Frame at {timestamp}]"
            })
        
        print(f"Sending {len(frames_data)} frames to OpenAI API for comprehensive analysis...")
        print(f"Style: {movie_style}, Target Audience: {target_audience}")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ],
            max_tokens=16000
        )
        
        print("Received comprehensive analysis from OpenAI API")
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error analyzing frames together: {e}")
        return f"Error: {e}"

def main():
    # Ask user for prefix
    prefix = input("Enter the file name prefix (e.g., 'Bun'): ").strip()
    if not prefix:
        print("No prefix provided. Exiting.")
        return
    
    # Ask user for movie style
    print("\n请选择电影风格：")
    print("1. serious - 严肃")
    print("2. funny - 幽默")
    print("3. dramatic - 戏剧性")
    print("4. educational - 教育性")
    print("5. neutral - 中性")
    
    style_choice = input("请输入选择 (1-5): ").strip()
    style_map = {
        "1": "serious",
        "2": "funny", 
        "3": "dramatic",
        "4": "educational",
        "5": "neutral"
    }
    movie_style = style_map.get(style_choice, "neutral")
    
    # Ask user for target audience
    print("\n请选择目标观众：")
    print("1. children - 儿童")
    print("2. adults - 成年人")
    print("3. elderly - 老年人")
    print("4. general - 一般观众")
    
    audience_choice = input("请输入选择 (1-4): ").strip()
    audience_map = {
        "1": "children",
        "2": "adults",
        "3": "elderly", 
        "4": "general"
    }
    target_audience = audience_map.get(audience_choice, "general")
    
    selected_json_file = f"../{prefix}_selected_frames.json"
    frames_dir = f"{prefix}_extracted_frames"
    output_story_file = f"{prefix}_storyscript.txt"

    # Load selected frames JSON
    if not os.path.exists(selected_json_file):
        print(f"Selected frames file '{selected_json_file}' not found. Exiting.")
        return
    if not os.path.isdir(frames_dir):
        print(f"Frames directory '{frames_dir}' not found. Exiting.")
        return
        
    with open(selected_json_file, "r", encoding="utf-8") as f:
        selected_frames = json.load(f)
    if not selected_frames:
        print(f"No frames found in {selected_json_file}. Exiting.")
        return
        
    print(f"Loaded {len(selected_frames)} selected frames from {selected_json_file}.")
    
    # Prepare frames data for analysis
    frames_data = []
    for entry in selected_frames:
        frame_file = entry.get("frame_file")
        timestamp = entry.get("timestamp")
        if not frame_file or not timestamp:
            print(f"Skipping entry with missing frame_file or timestamp: {entry}")
            continue
            
        frame_path = os.path.join(frames_dir, frame_file)
        if not os.path.exists(frame_path):
            print(f"Frame file '{frame_path}' not found. Skipping.")
            continue
            
        frames_data.append({
            "timestamp": timestamp,
            "image_path": frame_path,
            "frame_file": frame_file
        })
    
    if not frames_data:
        print("No valid frames found to analyze. Exiting.")
        return
    
    print(f"Prepared {len(frames_data)} frames for analysis...")
    
    # Analyze all frames together
    storyline = analyze_all_frames_together(frames_data, movie_style, target_audience)

    # Save to text file
    try:
        with open(output_story_file, "w", encoding="utf-8") as f:
            f.write(f"视频故事分析: {prefix}\n")
            f.write(f"电影风格: {movie_style}\n")
            f.write(f"目标观众: {target_audience}\n")
            f.write("=" * 80 + "\n\n")
            f.write("个性化时间戳描述\n")
            f.write("-" * 40 + "\n")
            f.write(storyline)
            f.write("\n")
        print(f"个性化故事脚本已保存到 {output_story_file}")
    except Exception as e:
        print(f"Error saving output file: {e}")

if __name__ == "__main__":
    main()