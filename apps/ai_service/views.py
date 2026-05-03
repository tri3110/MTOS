
# apps\ai_service\views.py
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.ai_service.services.service import handle_message

class ChatBotView(APIView):
    
    def post(self, request):
        user_message = request.data.get("message")

        reply = handle_message(request.user, user_message)

        return Response(reply)

        # if not user_message:
        #     return Response(
        #         {"error": "Message is required"},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )

        # try:
        #     intent = detect_intent(user_message)

        #     if intent == "order":
        #         if not request.user.id:
        #             return Response({
        #                 "message": "Bạn cân đăng nhập để đặt hàng 🛒"
        #             })

        #         products = get_products_by_keyword(user_message)
        #         quantity = extract_quantity(user_message)

        #         if products.exists():
        #             product = products[0]

        #             new_message = user_message.replace(product.name, "")

        #             options = extract_options(new_message, product)
        #             options = apply_default_options(product, options)
        #             toppings = extract_toppings(user_message, product)

        #             data = {
        #                 "product": {  
        #                     "id": product.id,
        #                     "name": product.name,
        #                     "price": product.price
        #                 },
        #                 "quantity": quantity,
        #                 "base_price": product.price,
        #                 "options": options,
        #                 "toppings": toppings
        #             }

        #             cart = create_cart(request.user, data)

        #             return Response({
        #                 "message": f"Đã thêm {quantity} {product.name} vào giỏ hàng của bạn",
        #                 "items": serialize_cart(cart)
        #             })

        #         return Response({
        #             "message": "Không tìm thấy sản phẩm 😢"
        #         })
            
        #     reply = chat_with_gemini(user_message)
            
        #     return Response({"message": reply})

        # except Exception as e:
        #     return Response(
        #         {"error": str(e)},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
        #     )