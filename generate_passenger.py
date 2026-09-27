import os
import base64
import requests
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("POLZA_API_KEY")
BASE_URL = "https://polza.ai/api/v1/media"

def get_base64_url(image_path):
    ext = image_path.split('.')[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    with open(image_path, "rb") as image_file:
        base64_image = base64.standard_b64encode(image_file.read()).decode("utf-8")
    return f"data:{mime};base64,{base64_image}"

def generate_image(prompt, reference_image_path, output_path):
    print(f"\n--- Starting Generation ---")
    print(f"Prompt: {prompt}")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    models = [
        "openai/gpt-image-2.5-sunburst",
        "openai/gpt-image-2.5-flare",
        "openai/gpt-5.4-image-2"
    ]
    
    for model in models:
        print(f"\nTrying model: {model}")
        payload = {
            "model": model,
            "input": {
                "prompt": prompt,
                "aspect_ratio": "16:9",
                "images": [
                    {
                        "type": "url",
                        "data": get_base64_url(reference_image_path)
                    }
                ],
                "image_resolution": "1K"
            },
            "async": True
        }
        
        response = requests.post(BASE_URL, headers=headers, json=payload)
        
        if not response.ok:
            print(f"Error starting job with {model}: {response.status_code}")
            print(response.text)
            continue  # Try next model
            
        data = response.json()
        task_id = data.get("id")
        
        if not task_id:
            if "url" in data:
                download_image(data["url"], output_path)
                return
            else:
                print("No task ID in response:", data)
                continue
                
        print(f"Task started. ID: {task_id}. Waiting for completion...")
        
        success = False
        while True:
            time.sleep(5)
            poll_resp = requests.get(f"{BASE_URL}/{task_id}", headers=headers)
            if not poll_resp.ok:
                print(f"Polling error: {poll_resp.status_code}")
                break
                
            poll_data = poll_resp.json()
            status = poll_data.get("status", "")
            
            if status in ["success", "completed"]:
                # The API returns URL in 'data' array for this model
                image_url = poll_data.get("url")
                if not image_url and "result" in poll_data:
                    image_url = poll_data["result"].get("url")
                if not image_url and "data" in poll_data and isinstance(poll_data["data"], list) and len(poll_data["data"]) > 0:
                    image_url = poll_data["data"][0].get("url")
                    
                if image_url:
                    download_image(image_url, output_path)
                    success = True
                else:
                    print("Completed but no URL found:", poll_data)
                break
            elif status in ["failed", "error"]:
                print("Generation failed:", poll_data)
                break
            else:
                print(f"Status: {status}... waiting")
                
        if success:
            return  # Done!
            
    print("All models failed for this prompt.")

def download_image(url, output_path):
    print(f"Downloading result from {url}...")
    img_resp = requests.get(url)
    if img_resp.ok:
        with open(output_path, 'wb') as f:
            f.write(img_resp.content)
        print(f"✅ Saved successfully to {output_path}")
    else:
        print("Failed to download image from result URL.")

if __name__ == "__main__":
    base_ref = "frontend/public/assets/male_young/neutral.png"
    
    if not os.path.exists(base_ref):
        print(f"Reference image not found: {base_ref}")
        exit(1)
        
    # 1. Сгенерировать нового пассажира (русский дедушка)
    prompt1 = "сгенерируй мне изображение с точно таким же видом вагона 1 в 1, но вместо пассажира сгенерируй русского дедушку. Придерживайся того же стиля комикса, что и в исходном изображении. У пассажира должно быть нейтральное выражение лица, смотрит на нас."
    generate_image(prompt1, base_ref, "frontend/public/assets/russian_grandpa_neutral.png")
    
    # 2. Сгенерировать новую эмоцию для текущего пассажира
    prompt2 = "сгенерируй мне изображение с точно таким же видом вагона 1 в 1, но у пассажира должна быть другая эмоция - он должен широко и искренне улыбаться. Придерживайся того же стиля комикса, что и в исходном изображении."
    generate_image(prompt2, base_ref, "frontend/public/assets/male_young/smiling_wide.png")
