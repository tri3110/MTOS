import json

from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.carts.serializers import CartItemSerializer
from apps.users.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated

from apps.carts.models import Cart, CartItem, CartItemOption, CartItemTopping
from common.redis_client import redis_client

def is_same_item(db_item, client_item):
    if db_item.product_id != client_item["product"]["id"]:
        return False

    db_options = set(
        db_item.options.values_list("option_id", flat=True)
    )
    client_options = set(client_item["options"].values())

    if db_options != client_options:
        return False

    db_toppings = set(
        (t.topping_id, t.quantity)
        for t in db_item.toppings.all()
    )
    client_toppings = set(
        (t["id"], t["quantity"])
        for t in client_item["toppings"]
    )

    return db_toppings == client_toppings

class CartView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            with transaction.atomic():
                cart, _ = Cart.objects.get_or_create(user=request.user)

                db_items = cart.items.prefetch_related("options", "toppings")

                for item in request.data['items']:
                    existing = None

                    for db_item in db_items:
                        if is_same_item(db_item, item):
                            existing = db_item
                            break

                    if existing:
                        existing.quantity += item["quantity"]
                        existing.save()
                    else:
                        new_item = CartItem.objects.create(
                            cart=cart,
                            product_id=item["product"]['id'],
                            quantity=item["quantity"],
                            price_snapshot=item["base_price"]
                        )

                        for option_id in item["options"].values():
                            CartItemOption.objects.create(
                                cart_item=new_item,
                                option_id=option_id
                            )

                        for topping in item["toppings"]:
                            CartItemTopping.objects.create(
                                cart_item=new_item,
                                topping_id=topping["id"],
                                price=topping["price"],
                                quantity=topping["quantity"]
                            )

                redis_client.delete(f"cart_{request.user.id}")

                return Response({
                    "items": CartItemSerializer(
                        cart.items.prefetch_related("options", "toppings", "product"),
                        many=True
                    ).data,
                    "message": "Sync success"
                }, status=200)

        except Exception as e:
            return Response({"message": str(e)}, status=400)

class CartAddView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user=request.user

            cache_key = f"cart_{user.id}"
            cached = redis_client.get(cache_key)
            if cached:
                return Response({"items": json.loads(cached)})

            cart = Cart.objects.get(user=user)
            data = CartItemSerializer(
                cart.items.prefetch_related("options", "toppings", "product"),
                many=True
            ).data

            redis_client.set(cache_key, json.dumps(data), ex=60)

            return Response({"items": data})

        except CartItem.DoesNotExist:
            return Response({"message": "Item not found"}, status=404)

        except Exception as e:
            return Response({"message": str(e)}, status=400)

    def post(self, request):
        try:
            with transaction.atomic():
                cart, _ = Cart.objects.get_or_create(user=request.user)

                item = request.data

                db_items = cart.items.prefetch_related("options", "toppings")

                existing = None
                for db_item in db_items:
                    if is_same_item(db_item, item):
                        existing = db_item
                        break

                if existing:
                    existing.quantity += item["quantity"]
                    existing.save()
                else:
                    new_item = CartItem.objects.create(
                        cart=cart,
                        product_id=item["product"]["id"],
                        quantity=item["quantity"],
                        price_snapshot=item["base_price"]
                    )

                    for option_id in item["options"].values():
                        CartItemOption.objects.create(
                            cart_item=new_item,
                            option_id=option_id
                        )

                    for topping in item["toppings"]:
                        CartItemTopping.objects.create(
                            cart_item=new_item,
                            topping_id=topping["id"],
                            price=topping["price"],
                            quantity=topping["quantity"]
                        )
                
                redis_client.delete(f"cart_{request.user.id}")

                return Response({
                    "items": CartItemSerializer(
                        cart.items.prefetch_related("options", "toppings", "product"),
                        many=True
                    ).data
                }, status=200)

        except Exception as e:
            return Response({"message": str(e)}, status=400)

    def patch(self, request, id):
        try:
            cart = Cart.objects.get(user=request.user)

            item = CartItem.objects.get(id=id, cart=cart)

            action = request.data.get("action")

            if action == "increase":
                item.quantity += 1
                item.save()

            elif action == "decrease":
                item.quantity -= 1

                if item.quantity <= 0:
                    item.delete()
                else:
                    item.save()
            else:
                return Response({"message": "Invalid action"}, status=400)
            
            redis_client.delete(f"cart_{request.user.id}")

            return Response({
                "items": CartItemSerializer(
                    cart.items.prefetch_related("options", "toppings", "product"),
                    many=True
                ).data
            })

        except CartItem.DoesNotExist:
            return Response({"message": "Item not found"}, status=404)

        except Exception as e:
            return Response({"message": str(e)}, status=400)

    def delete(self, request, id):
        try:
            cart = Cart.objects.get(user=request.user)

            item = CartItem.objects.get(id=id, cart=cart)
            item.delete()

            redis_client.delete(f"cart_{request.user.id}")

            return Response({
                "items": CartItemSerializer(
                    cart.items.prefetch_related("options", "toppings", "product"),
                    many=True
                ).data
            }, status=200)

        except CartItem.DoesNotExist:
            return Response({"message": "Item not found"}, status=404)

        except Exception as e:
            return Response({"message": str(e)}, status=400)

    # def patch(self, request, id):
    #     try:
    #         cart = Cart.objects.get(user=request.user)

    #         item = CartItem.objects.get(id=id, cart=cart)

    #         action = request.data.get("action")

    #         if action == "increase":
    #             item.quantity += 1
    #             item.save()

    #         elif action == "decrease":
    #             item.quantity -= 1

    #             if item.quantity <= 0:
    #                 item.delete()
    #             else:
    #                 item.save()
    #         else:
    #             return Response({"message": "Invalid action"}, status=400)

    #         return Response({
    #             "items": CartItemSerializer(
    #                 cart.items.prefetch_related("options", "toppings", "product"),
    #                 many=True
    #             ).data
    #         })

    #     except CartItem.DoesNotExist:
    #         return Response({"message": "Item not found"}, status=404)

    #     except Exception as e:
    #         return Response({"message": str(e)}, status=400)

    # def delete(self, request, id):
        try:
            cart = Cart.objects.get(user=request.user)

            item = CartItem.objects.get(id=id, cart=cart)
            item.delete()

            return Response({
                "items": CartItemSerializer(
                    cart.items.prefetch_related("options", "toppings", "product"),
                    many=True
                ).data
            }, status=200)

        except CartItem.DoesNotExist:
            return Response({"message": "Item not found"}, status=404)

        except Exception as e:
            return Response({"message": str(e)}, status=400)