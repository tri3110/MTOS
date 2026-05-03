#E:\MTOS\MTOS\backend\apps\ai_service\gemini_service.py

import json
import os
import re
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def parse_gemini_json(raw_text: str):
    try:
        cleaned = re.sub(r"```json|```", "", raw_text).strip()

        return json.loads(cleaned)

    except json.JSONDecodeError:
        print("JSON parse error:", raw_text)
        return None

def get_json_from_gemini(message):
    prompt = f"""
        Bạn là một AI chuyên nhận đơn đồ uống.

        Nhiệm vụ: trích xuất dữ liệu đơn hàng từ câu của khách.

        =====================
        INPUT:
        Khách: "{message}"
        =====================

        YÊU CẦU:

        1. Chỉ trả về JSON hợp lệ (valid JSON)
        2. KHÔNG thêm text, KHÔNG giải thích
        3. Dùng dấu " cho JSON (KHÔNG dùng ')
        4. Nếu có nhiều món → trả về nhiều items
        5. Nếu thiếu thông tin → để null (KHÔNG đoán)
        6. KHÔNG tự tạo option không có trong câu
        7. quantity mặc định = 1 nếu không nói

        =====================
        SCHEMA:

        {{
            "intent": "order | confirm_order | modify_order | chat",
            "items": [
                {{
                    "product_name": string,
                    "quantity": number,
                    "options": {{
                        "size": string | null,
                        "sugar": string | null,
                        "ice": string | null
                    }},
                    "toppings": [
                        {{
                            "name": string,
                            "quantity": number
                        }}
                    ]
                }}
            ]
        }}
    """
    
    res = model.generate_content(prompt)
    data = parse_gemini_json(res.text)

    return data

def chat_with_gemini(message: str) -> str:
    from apps.ai_service.services.service import get_products_by_keyword

    products = get_products_by_keyword(message)
    context = "\n".join([
        f"{p.name} - {p.price}k"
        for p in products
    ])

    prompt = f"""
        Bạn là nhân viên bán đồ uống.

        Menu liên quan:
        {context}

        Khách: {message}
        Trả lời ngắn gọn, gợi ý 1-2 món.
    """

    res = model.generate_content(prompt)

    return res.text

