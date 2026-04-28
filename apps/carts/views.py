import json
from django.db import transaction
from django.db.models import F
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.carts.service import build_db_map, build_item_key, create_cart, get_cart_items, serialize_cart
from apps.users.authentication import CookieJWTAuthentication
from apps.carts.models import Cart, CartItem, CartItemOption, CartItemTopping
from common.redis_client import redis_client
from rest_framework.permissions import IsAuthenticated

def get_cart_cache_key(user_id):
    return f"cart:{user_id}"

class CartView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            with transaction.atomic():
                cart, _ = Cart.objects.get_or_create(user=request.user)

                db_items = get_cart_items(cart)
                db_map = build_db_map(db_items)

                for item in request.data["items"]:
                    key = build_item_key(
                        item["product"]["id"],
                        item["options"].values(),
                        item["toppings"]
                    )

                    existing = db_map.get(key)

                    if existing:
                        CartItem.objects.filter(id=existing.id).update(
                            quantity=F("quantity") + item["quantity"]
                        )
                    else:
                        new_item = CartItem.objects.create(
                            cart=cart,
                            product_id=item["product"]["id"],
                            quantity=item["quantity"],
                            price_snapshot=item["base_price"]
                        )

                        CartItemOption.objects.bulk_create([
                            CartItemOption(
                                cart_item=new_item,
                                option_id=opt_id
                            )
                            for opt_id in item["options"].values()
                        ])

                        CartItemTopping.objects.bulk_create([
                            CartItemTopping(
                                cart_item=new_item,
                                topping_id=t["id"],
                                price=t["price"],
                                quantity=t["quantity"]
                            )
                            for t in item["toppings"]
                        ])

                redis_client.delete(get_cart_cache_key(request.user.id))

                return Response({
                    "items": serialize_cart(cart),
                    "message": "Sync success"
                })

        except Exception as e:
            return Response({"message": str(e)}, status=400)


class CartAddView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            cache_key = get_cart_cache_key(user.id)

            cached = redis_client.get(cache_key)
            if cached:
                return Response({"items": json.loads(cached)})

            cart = Cart.objects.filter(user=user).first()
            if not cart:
                return Response({"items": []})

            data = serialize_cart(cart)

            redis_client.set(cache_key, json.dumps(data), ex=60)

            return Response({"items": data})

        except Exception as e:
            return Response({"message": str(e)}, status=400)

    def post(self, request):
        try:
            with transaction.atomic():
                cart = create_cart(request.user, request.data)
                return Response({
                    "items": serialize_cart(cart)
                })

        except Exception as e:
            return Response({"message": str(e)}, status=400)

    def patch(self, request, id):
        try:
            action = request.data.get("action")

            if action == "increase":
                CartItem.objects.filter(id=id).update(quantity=F("quantity") + 1)

            elif action == "decrease":
                item = CartItem.objects.filter(id=id).first()
                if not item:
                    return Response({"message": "Item not found"}, status=404)

                if item.quantity <= 1:
                    item.delete()
                else:
                    CartItem.objects.filter(id=id).update(quantity=F("quantity") - 1)

            else:
                return Response({"message": "Invalid action"}, status=400)

            redis_client.delete(get_cart_cache_key(request.user.id))

            cart = Cart.objects.filter(user=request.user).first()
            return Response({"items": serialize_cart(cart)})

        except Exception as e:
            return Response({"message": str(e)}, status=400)

    def delete(self, request, id):
        try:
            CartItem.objects.filter(id=id).delete()

            redis_client.delete(get_cart_cache_key(request.user.id))

            cart = Cart.objects.filter(user=request.user).first()
            return Response({
                "items": serialize_cart(cart)
            })

        except Exception as e:
            return Response({"message": str(e)}, status=400)