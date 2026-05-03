
from apps.carts.models import Cart, CartItem, CartItemOption, CartItemTopping
from apps.carts.serializers import CartItemSerializer
from common.redis_client import redis_client
from django.db.models import F

def get_cart_items(cart):
    return cart.items.select_related("product").prefetch_related(
        "options",
        "toppings__topping"
    )

def build_item_key(product_id, options, toppings):
    return (
        product_id,
        tuple(sorted(opt["option_id"] for opt in options)),
        tuple(sorted((t["id"], t["quantity"]) for t in toppings))
    )

def serialize_cart(cart):
    items = get_cart_items(cart)
    return CartItemSerializer(items, many=True).data


def build_db_map(db_items):
    db_map = {}

    for db_item in db_items:
        key = (
            db_item.product_id,
            tuple(sorted(db_item.options.values_list("option_id", flat=True))),
            tuple(sorted((t.topping_id, t.quantity) for t in db_item.toppings.all()))
        )
        db_map[key] = db_item

    return db_map

def create_cart(user, data):
    cart, _ = Cart.objects.get_or_create(user=user)

    db_items = get_cart_items(cart)
    db_map = build_db_map(db_items)

    key = build_item_key(
        data["product"]["id"],
        data.get("options", []),
        data.get("toppings", [])
    )

    existing = db_map.get(key)

    if existing:
        CartItem.objects.filter(id=existing.id).update(
            quantity=F("quantity") + data["quantity"]
        )
    else:
        new_item = CartItem.objects.create(
            cart=cart,
            product_id=data["product"]["id"],
            quantity=data["quantity"],
            price_snapshot=data["base_price"]
        )

        CartItemOption.objects.bulk_create([
            CartItemOption(
                cart_item=new_item,
                option_id=opt["option_id"]
            )
            for opt in data.get("options", [])
        ])

        CartItemTopping.objects.bulk_create([
            CartItemTopping(
                cart_item=new_item,
                topping_id=t["id"],
                price=t["price"],
                quantity=t["quantity"]
            )
            for t in data.get("toppings", [])
        ])

    redis_client.delete(f"cart:{user.id}")

    return cart