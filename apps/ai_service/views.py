
# import os
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework import status
# from openai import OpenAI

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# class ChatBotView(APIView):
    
#     def post(self, request):
#         user_message = request.data.get("message")

#         if not user_message:
#             return Response(
#                 {"error": "Message is required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         system_prompt = """
#         Bạn là nhân viên bán trà sữa và cà phê chuyên nghiệp.

#         Phong cách:
#         - Thân thiện, tự nhiên như người thật
#         - Trả lời ngắn gọn, dễ hiểu
#         - Luôn gợi ý thêm đồ uống nếu phù hợp

#         Menu:
#         - Trà sữa trân châu
#         - Trà sữa matcha
#         - Trà đào
#         - Cà phê đen
#         - Cà phê sữa
#         - Bạc xỉu

#         Nếu khách phân vân → hãy recommend 1-2 món phù hợp nhất.
#         """

#         try:
#             response = client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[
#                     {"role": "system", "content": system_prompt},
#                     {"role": "user", "content": user_message}
#                 ],
#                 temperature=0.7  # ✅ thêm để trả lời tự nhiên hơn
#             )

#             reply = response.choices[0].message.content

#             return Response({"message": reply})

#         except Exception as e:
#             return Response(
#                 {"error": str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )