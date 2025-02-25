import gradio as gr
import requests
import json
import os
import hashlib
import time
from PIL import Image
from pathlib import Path
from io import BytesIO
from groq import Groq
from dotenv import load_dotenv

if os.path.exists('.env'):
    load_dotenv()
else:
    print("Warning: .env file not found. Using default environment variables.")

# Get environment variables with fallback
api_key_token = os.getenv('api_key_token', '')
groq_api_key = os.getenv('groq_api_key', '')

if not api_key_token or not groq_api_key:
    raise ValueError("Please configure your API keys in .env file")

# Ghi log khởi động
print("Version 2.19 - Fixed RGBA to RGB conversion for JPEG")
print("Running grok_app.py with workflow processing and .env configuration")

# URL và thông tin cá nhân từ API
url_pre = "https://ap-east-1.tensorart.cloud/v1"
SAVE_DIR = "generated_images"
Path(SAVE_DIR).mkdir(exist_ok=True)

# Danh sách mã sản phẩm
PRODUCT_GROUPS = {
    "Standard": {
        "C1012 Glacier White": "817687427545199895",
        "C1026 Polar": "819910519797326073",
        "C3269 Ash Grey": "821839484099264081",
        "C3168 Silver Wave": "821849044696643212",
        "C1005 Milky White": "821948258441171133",
    },
    "Deluxe": {
        "C2103 Onyx Carrara": "827090618489513527",
        "C2104 Massa": "822075428127644644",
        "C3105 Casla Cloudy": "828912225788997963",
        "C3146 Casla Nova": "828013009961087650",
        "C2240 Marquin": "828085015087780649",
        "C2262 Concrete (Honed)": "822211862058871636",
        "C3311 Calacatta Sky": "829984593223502930",
        "C3346 Massimo": "827938741386607132",
    },
    "Luxury": {
        "C4143 Mario": "829984593223502930",
        "C4145 Marina": "828132560375742058",
        "C4202 Calacatta Gold": "828167757632695310",
        "C1205 Casla Everest": "828296778450463190",
        "C4211 Calacatta Supreme": "828436321937882328",
        "C4204 Calacatta Classic": "828422973179466146",
        "C5240 Spring": "is coming",
        "C1102 Super White": "828545723344775887",
        "C4246 Casla Mystery": "828544778451950698",
        "C4345 Oro": "828891068780182635",
        "C4346 Luxe": "829436426547535131",
        "C4342 Casla Eternal": "829190256201829181",
        "C4221 Athena": "829644354504131520",
        "C4222 Lagoon": "is coming",
        "C5225 Amber": "is coming",
    },
    "Super Luxury": {
        "C4255 Calacatta Extra": "829659013227537217",
    },
}

# Danh sách ảnh sản phẩm tương ứng với mã sản phẩm
PRODUCT_IMAGE_MAP = {
    "C1012 Glacier White": "product_images/C1012.jpg",
    "C1026 Polar": "product_images/C1026.jpg",
    "C3269 Ash Grey": "product_images/C3269.jpg",
    "C3168 Silver Wave": "product_images/C3168.jpg",
    "C1005 Milky White": "product_images/C1005.jpg",
    "C2103 Onyx Carrara": "product_images/C2103.jpg",
    "C2104 Massa": "product_images/C2104.jpg",
    "C3105 Casla Cloudy": "product_images/C3105.jpg",
    "C3146 Casla Nova": "product_images/C3146.jpg",
    "C2240 Marquin": "product_images/C2240.jpg",
    "C2262 Concrete (Honed)": "product_images/C2262.jpg",
    "C3311 Calacatta Sky": "product_images/C3311.jpg",
    "C3346 Massimo": "product_images/C3346.jpg",
    "C4143 Mario": "product_images/C4143.jpg",
    "C4145 Marina": "product_images/C4145.jpg",
    "C4202 Calacatta Gold": "product_images/C4202.jpg",
    "C1205 Casla Everest": "product_images/C1205.jpg",
    "C4211 Calacatta Supreme": "product_images/C4211.jpg",
    "C4204 Calacatta Classic": "product_images/C4204.jpg",
    "C1102 Super White": "product_images/C1102.jpg",
    "C4246 Casla Mystery": "product_images/C4246.jpg",
    "C4345 Oro": "product_images/C4345.jpg",
    "C4346 Luxe": "product_images/C4346.jpg",
    "C4342 Casla Eternal": "product_images/C4342.jpg",
    "C4221 Athena": "product_images/C4221.jpg",
    "C4255 Calacatta Extra": "product_images/C4255.jpg",
}

# Định nghĩa màu sắc cho từng nhóm sản phẩm
GROUP_COLORS = {
    "Standard": "#FFCCCC",
    "Deluxe": "#CCFFCC",
    "Luxury": "#CCCCFF",
    "Super Luxury": "#CCFCFF",
}

# Khởi tạo client Groq
client = Groq(api_key=groq_api_key)

def rewrite_prompt_with_groq(vietnamese_prompt, product_codes):
    prompt = f"{vietnamese_prompt}, featuring {' and '.join(product_codes)} quartz marble"
    return prompt

# Hàm upload ảnh lên TensorArt
def upload_image_to_tensorart(image_path):
    try:
        url = f"{url_pre}/resource/image"
        payload = json.dumps({"expireSec": "7200"})
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key_token}'
        }
        print(f"Starting upload for: {image_path}")
        if not os.path.exists(image_path):
            print(f"File does not exist: {image_path}")
            return None
        response = requests.post(url, headers=headers, data=payload, timeout=30)
        print(f"POST response: {response.status_code} - {response.text}")
        response.raise_for_status()
        resource_response = response.json()
        
        put_url = resource_response.get('putUrl')
        headers_put = resource_response.get('headers', {'Content-Type': 'image/jpeg'})
        if not put_url:
            print(f"Upload failed - No 'putUrl' in response: {resource_response}")
            return None
        
        print(f"Got putUrl: {put_url}")
        with open(image_path, 'rb') as img_file:
            upload_response = requests.put(put_url, data=img_file, headers=headers_put)
            print(f"PUT response: {upload_response.status_code} - {upload_response.text}")
            if upload_response.status_code not in [200, 203]:
                raise Exception(f"PUT failed with status {upload_response.status_code}: {upload_response.text}")
            if upload_response.status_code == 203:
                print("Warning: PUT returned 203 - CallbackFailed, but proceeding with resourceId")
        
        resource_id = resource_response.get('resourceId')
        if not resource_id:
            print(f"Upload failed - No 'resourceId' in response: {resource_response}")
            return None
        print(f"Upload successful - resourceId: {resource_id}")
        time.sleep(10)  # Đợi đồng bộ tài nguyên
        print(f"Waited 10s for resource sync: {resource_id}")
        return resource_id
    except Exception as e:
        print(f"Upload error for {image_path}: {str(e)}")
        return None

# Hàm kiểm tra params
def check_workflow_params(params):
    url = f"{url_pre}/jobs/workflow/params/check"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key_token}'
    }
    payload = json.dumps({"params": params})
    print(f"Checking workflow params: {json.dumps(payload, indent=2)}")
    response = requests.post(url, headers=headers, data=payload, timeout=30)
    print(f"Params check response: {response.status_code} - {response.text}")
    if response.status_code != 200:
        raise Exception(f"Params check failed: {response.text}")
    return response.json()

# Hàm chạy workflow và chờ kết quả
def run_workflow(payload, step_name):
    try:
        check_workflow_params(payload["params"])
    except Exception as e:
        print(f"Workflow params check failed for {step_name}: {str(e)}")
        raise
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key_token}'
    }
    print(f"Sending {step_name} workflow request to {url_pre}/jobs/workflow with data: {json.dumps(payload, indent=2)}")
    response = requests.post(f"{url_pre}/jobs/workflow", json=payload, headers=headers, timeout=300)
    print(f"{step_name} workflow response: {response.status_code} - {response.text}")
    if response.status_code != 200:
        raise Exception(f"Error {response.status_code}: {response.text}")
    
    response_data = response.json()
    job_id = response_data['job'].get('id')
    if not job_id:
        raise Exception("Không tìm thấy job_id trong response")
    
    print(f"Starting {step_name} job status check for job_id: {job_id}")
    max_attempts = 36
    for attempt in range(max_attempts):
        response = requests.get(f"{url_pre}/jobs/{job_id}", headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        print(f"{step_name} job status (attempt {attempt + 1}/{max_attempts}): {json.dumps(result, indent=2)}")
        status = result['job'].get('status')
        if status == 'SUCCESS':
            success_info = result['job'].get('successInfo', {})
            if not success_info.get('images'):
                raise Exception(f"Không tìm thấy hình ảnh trong successInfo cho {step_name}")
            image_url = success_info['images'][0]['url']
            image_response = requests.get(image_url)
            image = Image.open(BytesIO(image_response.content))
            # Chuyển từ RGBA sang RGB nếu cần
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            output_path = Path(SAVE_DIR) / f"{step_name}_{int(time.time())}.jpg"
            image.save(output_path)
            print(f"{step_name} image saved to: {output_path}")
            return str(output_path)
        elif status in ['FAILED', 'ERROR']:
            failed_info = result['job'].get('failedInfo', {})
            error_reason = failed_info.get('reason', 'Không có chi tiết')
            error_code = failed_info.get('code', 'Không xác định')
            raise Exception(f"{step_name} job thất bại: {error_reason} (code: {error_code})")
        time.sleep(5)
    raise Exception(f"Hết thời gian chờ {step_name} job sau 3 phút")

# Hàm tạo mask và áp texture
def generate_mask(image_resource_id, position, selected_product_code):
    try:
        if not image_resource_id:
            raise Exception("Không có image_resource_id hợp lệ - ảnh gốc chưa được upload")
        print(f"Using image_resource_id: {image_resource_id}")
        time.sleep(10)  # Đợi đồng bộ tài nguyên
        
        short_code = selected_product_code.split()[0]
        texture_filepath = PRODUCT_IMAGE_MAP.get(selected_product_code)
        print(f"Texture file: {texture_filepath}, exists: {os.path.exists(texture_filepath)}")
        if not texture_filepath or not os.path.exists(texture_filepath):
            raise Exception(f"Không tìm thấy ảnh sản phẩm cho mã {short_code}")
        
        texture_resource_id = upload_image_to_tensorart(texture_filepath)
        print(f"Texture resource_id: {texture_resource_id}")
        if not texture_resource_id:
            raise Exception(f"Không thể upload ảnh sản phẩm {short_code}")
        time.sleep(10)  # Đợi đồng bộ tài nguyên

        if isinstance(position, (set, list)):
            position = position[0] if position else "default"
        print(f"Position: {position}, type: {type(position)}")

        # Dùng params đúng như mẫu TensorArt
        workflow_params = {
            "1": {
                "classType": "LayerMask: SegmentAnythingUltra V3",
                "inputs": {
                    "black_point": 0.3,
                    "detail_dilate": 6,
                    "detail_erode": 65,
                    "detail_method": "GuidedFilter",
                    "device": "cuda",
                    "image": ["2", 0],
                    "max_megapixels": 2,
                    "process_detail": True,
                    "prompt": ["4", 0],
                    "sam_models": ["3", 0],
                    "threshold": 0.3,
                    "white_point": 0.99
                },
                "properties": {"Node name for S&R": "LayerMask: SegmentAnythingUltra V3"}
            },
            "10": {
                "classType": "Image Seamless Texture",
                "inputs": {
                    "blending": 0.37,
                    "images": ["17", 0],
                    "tiled": "true",
                    "tiles": 2
                },
                "properties": {"Node name for S&R": "Image Seamless Texture"}
            },
            "13": {
                "classType": "Paste By Mask",
                "inputs": {
                    "image_base": ["2", 0],
                    "image_to_paste": ["10", 0],
                    "mask": ["8", 0],
                    "resize_behavior": "resize"
                },
                "properties": {"Node name for S&R": "Paste By Mask"}
            },
            "17": {
                "classType": "TensorArt_LoadImage",
                "inputs": {
                    "_height": 768,
                    "_width": 512,
                    "image": texture_resource_id,
                    "upload": "image"
                },
                "properties": {"Node name for S&R": "TensorArt_LoadImage"}
            },
            "2": {
                "classType": "TensorArt_LoadImage",
                "inputs": {
                    "_height": 1024,
                    "_width": 768,
                    "image": image_resource_id,
                    "upload": "image"
                },
                "properties": {"Node name for S&R": "TensorArt_LoadImage"}
            },
            "3": {
                "classType": "LayerMask: LoadSegmentAnythingModels",
                "inputs": {
                    "grounding_dino_model": "GroundingDINO_SwinB (938MB)",
                    "sam_model": "sam_vit_h (2.56GB)"
                },
                "properties": {"Node name for S&R": "LayerMask: LoadSegmentAnythingModels"}
            },
            "4": {
                "classType": "TensorArt_PromptText",
                "inputs": {"Text": position.lower()},
                "properties": {"Node name for S&R": "TensorArt_PromptText"}
            },
            "7": {
                "classType": "PreviewImage",
                "inputs": {"images": ["13", 0]},
                "properties": {"Node name for S&R": "PreviewImage"}
            },
            "8": {
                "classType": "MaskToImage",
                "inputs": {"mask": ["1", 1]},
                "properties": {"Node name for S&R": "MaskToImage"}
            }
        }

        payload = {
            "requestId": f"workflow_{int(time.time())}",
            "params": workflow_params,
            "runningNotifyUrl": ""
        }
        
        output_path = run_workflow(payload, "full_workflow")
        return output_path

    except Exception as e:
        print(f"Mask generation error: {str(e)}")
        return None

# Hàm xử lý img2img với spinner và progress bar
def generate_img2img(image, position, size_choice, custom_size, *product_choices):
    yield None, gr.update(visible=True), gr.update(visible=True, value='<div class="progress-container"><div class="progress-bar" style="width: 0%"></div></div>'), None
    
    if size_choice == "Custom size":
        if not custom_size.strip():
            yield "Vui lòng nhập kích thước tùy chỉnh.", gr.update(visible=False), gr.update(visible=False), None
            return
        width, height = map(int, custom_size.split("x"))
    else:
        width, height = map(int, size_choice.split("x"))

    yield "Đang upload ảnh gốc...", gr.update(visible=True), gr.update(visible=True, value='<div class="progress-container"><div class="progress-bar" style="width: 20%"></div></div>'), None
    image_path = Path(SAVE_DIR) / f"input_{int(time.time())}.jpg"
    image.save(image_path)
    image_resource_id = upload_image_to_tensorart(str(image_path))
    print(f"Generated image_resource_id: {image_resource_id}")
    if not image_resource_id:
        yield "Lỗi: Không thể upload ảnh gốc", gr.update(visible=False), gr.update(visible=False), None
        return

    yield "Đang chuẩn bị ảnh sản phẩm...", gr.update(visible=True), gr.update(visible=True, value='<div class="progress-container"><div class="progress-bar" style="width: 40%"></div></div>'), None
    selected_products = []
    for group, choices in zip(PRODUCT_GROUPS.keys(), product_choices):
        selected_products.extend(choices)
    if not selected_products:
        yield "Vui lòng chọn ít nhất một mã sản phẩm.", gr.update(visible=False), gr.update(visible=False), None
        return
    selected_product_code = selected_products[0]

    yield "Đang tạo mask và áp texture...", gr.update(visible=True), gr.update(visible=True, value='<div class="progress-container"><div class="progress-bar" style="width: 60%"></div></div>'), None
    output_path = generate_mask(image_resource_id, position, selected_product_code)
    if not output_path:
        yield "Lỗi: Không thể tạo ảnh", gr.update(visible=False), gr.update(visible=False), None
        return
    
    yield "Hoàn tất!", gr.update(visible=False), gr.update(visible=True, value='<div class="progress-container"><div class="progress-bar" style="width: 100%"></div></div>'), Image.open(output_path)

# Hàm generate_with_loading (text2img)
def generate_with_loading(prompt, size_choice, custom_size, *product_choices):
    yield None, gr.update(visible=True), gr.update(visible=True, value='<div class="progress-container"><div class="progress-bar" style="width: 0%"></div></div>'), None
    try:
        if size_choice == "Custom size":
            if not custom_size.strip():
                yield "Vui lòng nhập kích thước tùy chỉnh.", gr.update(visible=False), gr.update(visible=False), None
                return
            width, height = map(int, custom_size.split("x"))
        else:
            width, height = map(int, size_choice.split("x"))

        selected_products = []
        for group, choices in zip(PRODUCT_GROUPS.keys(), product_choices):
            selected_products.extend(choices)
        if not selected_products:
            yield "Vui lòng chọn ít nhất một mã sản phẩm.", gr.update(visible=False), gr.update(visible=False), None
            return

        short_codes = [code.split()[0] for code in selected_products]
        rewritten_prompt = rewrite_prompt_with_groq(prompt, short_codes)
        print(f"Rewritten Prompt: {rewritten_prompt}")

        progress = 0
        while progress < 100:
            time.sleep(0.5)
            progress += 10
            yield None, gr.update(visible=True), gr.update(value=f'<div class="progress-container"><div class="progress-bar" style="width: {progress}%"></div></div>'), None

        result = txt2img(rewritten_prompt, width, height, short_codes)
        if isinstance(result, str):
            yield result, gr.update(visible=False), gr.update(visible=False), None
        else:
            yield None, gr.update(visible=False), gr.update(visible=False), result
    except Exception as e:
        yield f"Lỗi khi xử lý: {e}", gr.update(visible=False), gr.update(visible=False), None

# Hàm text2img
def txt2img(prompt, width, height, product_codes):
    model_id = "779398605850080514"
    vae_id = "ae.sft"

    txt2img_data = {
        "request_id": hashlib.md5(str(int(time.time())).encode()).hexdigest(),
        "stages": [
            {"type": "INPUT_INITIALIZE", "inputInitialize": {"seed": -1, "count": 1}},
            {
                "type": "DIFFUSION",
                "diffusion": {
                    "width": width,
                    "height": height,
                    "prompts": [{"text": prompt}],
                    "negativePrompts": [{"text": " "}],
                    "sdModel": model_id,
                    "sdVae": vae_id,
                    "sampler": "Euler a",
                    "steps": 30,
                    "cfgScale": 8,
                    "clipSkip": 1,
                    "etaNoiseSeedDelta": 31337,
                }
            }
        ]
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key_token}'
    }
    response = requests.post(f"{url_pre}/jobs", json=txt2img_data, headers=headers)
    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"
    response_data = response.json()
    job_id = response_data['job']['id']
    print(f"Job created. ID: {job_id}")
    start_time = time.time()
    timeout = 300
    while True:
        time.sleep(10)
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            return f"Error: Job timed out after {timeout} seconds."
        response = requests.get(f"{url_pre}/jobs/{job_id}", headers=headers)
        if response.status_code != 200:
            return f"Error: {response.status_code} - {response.text}"
        get_job_response_data = response.json()
        job_status = get_job_response_data['job']['status']
        if job_status == 'SUCCESS':
            image_url = get_job_response_data['job']['successInfo']['images'][0]['url']
            response_image = requests.get(image_url)
            img = Image.open(BytesIO(response_image.content))
            save_path = Path(SAVE_DIR) / f"{hashlib.md5(prompt.encode()).hexdigest()}.png"
            img.save(save_path)
            print(f"Image saved to: {save_path}")
            return img
        elif job_status == 'FAILED':
            return "Error: Job failed."

# CSS
css = """
.loading-spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: auto; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.progress-container { width: 100%; max-width: 400px; margin: 20px auto; background-color: #f3f3f3; border-radius: 20px; overflow: hidden; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); }
.progress-bar { width: 0%; height: 10px; background: linear-gradient(90deg, #3498db, #e74c3c); border-radius: 20px; transition: width 0.3s ease-in-out; }
"""

# Giao diện Gradio
with gr.Blocks(css=css) as demo:
    gr.Markdown("## Ứng dụng Tạo Ảnh CaslaQuartz với Ảnh Sản Phẩm")
    with gr.Tabs():
        with gr.Tab("Text2Img"):
            with gr.Row():
                with gr.Column():
                    prompt_input = gr.Textbox(label="Mô tả ảnh cần tạo", placeholder="Một nhà bếp hiện đại với mặt bàn bằng đá thạch anh.")
                    size_radio = gr.Radio(choices=["1152x768", "1024x1024", "768x1152", "Custom size"], label="Chọn kích thước ảnh", value="1024x1024")
                    custom_size_input = gr.Textbox(label="Nhập kích thước tùy chỉnh (VD: 1280x720)", placeholder="Chiều rộng x Chiều cao", visible=False)
                    size_radio.change(fn=lambda x: gr.update(visible=x == "Custom size"), inputs=size_radio, outputs=custom_size_input)
                    product_checkbox_group = []
                    for group, color in GROUP_COLORS.items():
                        with gr.Accordion(f"Sản phẩm - {group}", open=False):
                            checkboxes = gr.CheckboxGroup(
                                choices=[(code, code) for code in PRODUCT_GROUPS[group] if PRODUCT_GROUPS[group][code] not in ["is coming", "is loading"]],
                                label=f"Chọn sản phẩm ({group})",
                                value=[]
                            )
                            product_checkbox_group.append((group, checkboxes))
                    generate_button = gr.Button("Generate")
                with gr.Column():
                    output_image = gr.Image(label="Ảnh đã tạo")
                    error_message = gr.Textbox(label="Thông báo", visible=False)
                    loading_spinner = gr.HTML('<div class="loading-spinner"></div>', visible=False)
                    progress_bar = gr.HTML('', visible=False)
            inputs = [prompt_input, size_radio, custom_size_input] + [checkboxes for _, checkboxes in product_checkbox_group]
            generate_button.click(fn=generate_with_loading, inputs=inputs, outputs=[error_message, loading_spinner, progress_bar, output_image])

        with gr.Tab("Img2Img"):
            with gr.Row():
                with gr.Column():
                    image_upload = gr.Image(label="Tải lên ảnh", type="pil")
                    position_input = gr.Dropdown(label="Chọn vật muốn thử nghiệm", choices=["Wall", "Countertop", "Floor", "Backsplash"], value="Wall")
                    size_radio_img2img = gr.Radio(choices=["1152x768", "1024x1024", "768x1152", "Custom size"], label="Chọn kích thước ảnh", value="1024x1024")
                    custom_size_input_img2img = gr.Textbox(label="Nhập kích thước tùy chỉnh (VD: 1280x720)", placeholder="Chiều rộng x Chiều cao", visible=False)
                    size_radio_img2img.change(fn=lambda x: gr.update(visible=x == "Custom size"), inputs=size_radio_img2img, outputs=custom_size_input_img2img)
                    product_checkbox_group_img2img = []
                    for group, color in GROUP_COLORS.items():
                        with gr.Accordion(f"Sản phẩm - {group}", open=False):
                            checkboxes = gr.CheckboxGroup(
                                choices=[(code, code) for code in PRODUCT_GROUPS[group] if PRODUCT_GROUPS[group][code] not in ["is coming", "is loading"]],
                                label=f"Chọn sản phẩm ({group})",
                                value=[]
                            )
                            product_checkbox_group_img2img.append((group, checkboxes))
                    inpaint_button = gr.Button("Inpaint")
                with gr.Column():
                    output_image_img2img = gr.Image(label="Ảnh đã tạo")
                    error_message_img2img = gr.Textbox(label="Thông báo", visible=False)
                    loading_spinner_img2img = gr.HTML('<div class="loading-spinner"></div>', visible=False)
                    progress_bar_img2img = gr.HTML('', visible=False)
            inputs_img2img = [image_upload, position_input, size_radio_img2img, custom_size_input_img2img] + [checkboxes for _, checkboxes in product_checkbox_group_img2img]
            inpaint_button.click(fn=generate_img2img, inputs=inputs_img2img, outputs=[error_message_img2img, loading_spinner_img2img, progress_bar_img2img, output_image_img2img])

demo.launch(share=True)