
# apps\ai_service\views.py
import re
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from apps.ai_service.gemini_service import chat_with_gemini, get_products_by_keyword
from apps.carts.service import create_cart, serialize_cart

def detect_intent(message):
    message = message.lower()
    if any(w in message for w in ["mua", "lấy", "order", "đặt"]):
        return "order"

    return "chat"

UNITS = {
    "không": 0,
    "một": 1, "mot": 1,
    "hai": 2,
    "ba": 3,
    "bốn": 4, "bon": 4,
    "năm": 5, "nam": 5,
    "sáu": 6, "sau": 6,
    "bảy": 7, "bay": 7,
    "tám": 8, "tam": 8,
    "chín": 9, "chin": 9,
}

def parse_vietnamese_number(text):
    words = text.split()

    if not words:
        return None

    # mười (10–19)
    if words[0] in ["mười", "muoi"]:
        if len(words) == 1:
            return 10
        if words[1] in UNITS:
            return 10 + UNITS[words[1]]

    # số đơn
    if words[0] in UNITS:
        return UNITS[words[0]]

    return None


def extract_quantity(message):
    message = message.lower()

    # ✅ 1. Ưu tiên số digit
    match = re.search(r'\d+', message)
    if match:
        return int(match.group())

    words = message.split()

    # ✅ 2. parse 2 từ (mười một, mười hai...)
    for i in range(len(words)):
        phrase = " ".join(words[i:i+2])
        num = parse_vietnamese_number(phrase)
        if num:
            return num

    # ✅ 3. parse 1 từ (hai, ba...)
    for word in words:
        num = parse_vietnamese_number(word)
        if num:
            return num

    return 1

class ChatBotView(APIView):
    
    def post(self, request):
        user_message = request.data.get("message")

        if not user_message:
            return Response(
                {"error": "Message is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            intent = detect_intent(user_message)

            if intent == "order":
                if not request.user.id:
                    return Response({
                        "message": "Bạn cân đăng nhập để đặt hàng 🛒"
                    })

                products = get_products_by_keyword(user_message)
                quantity = extract_quantity(user_message)

                if products.exists():
                    product = products[0]

                    data = {
                        "product": {  
                            "id": product.id,
                            "name": product.name,
                            "price": product.price
                        },
                        "quantity": quantity,
                        "base_price": product.price,
                        "options": {},
                        "toppings": []
                    }

                    cart = create_cart(request.user, data)

                    return Response({
                        "message": f"Đã thêm {quantity} {product.name} vào giỏ hàng của bạn",
                        "items": serialize_cart(cart)
                    })

                return Response({
                    "message": "Không tìm thấy sản phẩm 😢"
                })
            
            reply = chat_with_gemini(user_message)
            
            return Response({"message": reply})

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )