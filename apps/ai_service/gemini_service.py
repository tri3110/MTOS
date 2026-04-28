#E:\MTOS\MTOS\backend\apps\ai_service\gemini_service.py

import os
import google.generativeai as genai
from apps.products.models import Category, Product
from django.contrib.postgres.search import TrigramSimilarity

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def get_products_by_keyword(message):
    message = message.lower()

    categories = Category.objects.filter(status="active")

    for cat in categories:
        if any(kw in message for kw in cat.keywords):
            products = Product.objects.filter(
                category=cat,
                status="active"
            ).annotate(
                similarity=TrigramSimilarity('name', message)
            ).order_by('-similarity')

            return products[:5]

    products = Product.objects.annotate(
        similarity=TrigramSimilarity('name', message)
    ).filter(
        similarity__gt=0.2,
        status="active"
    ).order_by('-similarity')[:5]

    return products

def chat_with_gemini(message: str) -> str:
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

