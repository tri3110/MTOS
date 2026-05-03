import json
import random
from apps.ai_service.models import ChatMessage, MessageCache
from apps.products.models import Category, Product, ProductOption, ProductTopping
from django.contrib.postgres.search import TrigramSimilarity
import re
from common.redis_client import redis_client
from common.constants import Constant, UserCache
from common.utils import hash_text, normalize_text

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

def detect_intent(message):
    message = message.lower()
    if any(w in message for w in Constant.ORDER_KEYWORDS):
        return "order"

    return "chat"

def parse_vietnamese_number(text):
    words = text.split()

    if not words:
        return None

    # mười (10–19)
    if words[0] in ["mười", "muoi"]:
        if len(words) == 1:
            return 10
        if words[1] in Constant.UNITS_NUMBER:
            return 10 + Constant.UNITS_NUMBER[words[1]]

    # số đơn
    if words[0] in Constant.UNITS_NUMBER:
        return Constant.UNITS_NUMBER[words[0]]

    return None

def extract_options(message, product):
    message = message.lower()

    pos = ProductOption.objects.filter(product=product)\
        .select_related("option__group")

    result = {}

    for po in pos:
        opt = po.option
        group = opt.group

        opt_name = opt.name.lower()

        # Check keyword of group
        group_keywords = [k.lower() for k in group.keywords or []]

        has_group = any(k in message for k in group_keywords)
        has_option = opt_name in message

        if has_group and has_option:
            result[group.name] = opt

    return result

def apply_default_options(product, options_dict):
    pos = ProductOption.objects.filter(product=product)\
        .select_related("option__group")

    grouped = {}

    # Gom theo group_id
    for po in pos:
        group = po.option.group
        grouped.setdefault(group.id, []).append(po.option)

    result = []

    for group_id, opts in grouped.items():
        selected_opt = None

        # Nếu user đã chọn (từ extract_options)
        for opt in opts:
            if opt.group.name in options_dict and options_dict[opt.group.name].id == opt.id:
                selected_opt = opt
                break

        # Nếu chưa chọn → lấy default
        if not selected_opt:
            selected_opt = next(
                (o for o in opts if o.name.lower() == "bình thường"),
                None
            )

        if selected_opt:
            result.append({
                "group_id": group_id,
                "option_id": selected_opt.id
            })

    return result

def get_or_create_state(user):
    state, created = ChatMessage.objects.get_or_create(
        user=user,
        defaults={
            "status": "idle",
            "draft_order": None
        }
    )
    return state

def get_cached_parse(user, message):
    msg = normalize_text(message)

    return ChatMessage.objects.filter(
        user=user,
        content=msg,
        parsed_data__isnull=False
    ).order_by("-created_at").first()

def get_cached_or_ai(message):
    from apps.ai_service.services.gemini_service import get_json_from_gemini

    norm = normalize_text(message)
    h = hash_text(norm)

    cache_key = f"{UserCache.CHAT.key}:{h}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    data = MessageCache.objects.filter(
        message_hash=h,
        is_context_dependent=False
    ).first()

    if data:
        data.usage_count += 1
        data.save()

        result = {
            "parsed": data.parsed_data,
            "response": data.response_text
        }
    else:
        parsed = get_json_from_gemini(message)

        data = MessageCache.objects.create(
            message_hash=h,
            normalized_text=norm,
            parsed_data=parsed,
            parsed_intent=parsed.get("intent"),
        )

        result = {
            "parsed": parsed,
            "response": None
        }

    redis_client.set(cache_key, json.dumps(result), ex=UserCache.CHAT.ttl)

    return result

def handle_message(user, message):
    from apps.ai_service.services.gemini_service import chat_with_gemini

    try:
        if message.lower().strip() in Constant.GREETING_WORDS:
            return handle_greeting()
        

        simple_intent = detect_simple_intent(message)
        if simple_intent:
            parsed = {"intent": simple_intent, "items": []}
            cached_response = None
        else:
            data = get_cached_or_ai(message)
            parsed = data["parsed"]
            cached_response = data.get("response")

        intent = parsed.get("intent")

        if user.id:
            state = get_or_create_state(user)
            if intent == "order":
                return handle_order(state, parsed)

            elif intent == "confirm_order":
                return handle_confirm(state)

            elif intent == "modify_order":
                return handle_modify(state, parsed)
            
            elif intent == "cancel_order":
                return handle_cancel(state)
        
        if intent == "chat":
            if cached_response:
                return {"message": cached_response}

            reply = chat_with_gemini(message)

            if not simple_intent:
                norm = normalize_text(message)
                h = hash_text(norm)

                MessageCache.objects.filter(message_hash=h).update(response_text=reply)

                redis_client.set(
                    f"{UserCache.CHAT.key}:{h}",
                    json.dumps({
                        "parsed": parsed,
                        "response": reply
                    }),
                    ex=UserCache.CHAT.ttl
                )

            return {"message": reply}

        else:
            return chat_with_gemini(message)
        
    except Exception as e:
        print("Error handling message:", e)
        return "Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau."

def handle_greeting():
    return {
        "intent": "chat",
        "message": random.choice(Constant.RESPONSES_GREETING)
    }

def detect_simple_intent(message):
    msg = normalize_text(message)

    # confirm
    if msg in Constant.CONFIRM_WORDS:
        return "confirm_order"

    # cancel
    if msg in Constant.CANCEL_WORDS:
        return "cancel_order"

    return None

def handle_confirm(state):
    if state.status != "confirming" or not state.draft_order:
        return {"message": "Không có đơn nào để xác nhận."}

    items = ""
    for item in state.draft_order:
        items = process_add_to_cart(item, state.user)

    reset_state(state)

    return {
        "intent": "confirm_order",
        "message": "✅ Đã thêm vào giỏ hàng!",
        "items": items
    }

def handle_order(state, parsed):
    items = parsed.get("items", [])

    state.draft_order = items
    state.status = "confirming"
    state.save()

    return build_confirm_message(items)

def handle_modify(state, parsed):
    if state.status != "confirming":
        return {"message": "Không có đơn để chỉnh sửa."}

    state.draft_order = parsed.get("items", [])
    state.save()

    return build_confirm_message(state.draft_order)

def build_confirm_message(items):
    lines = []

    for item in items:
        name = item["product_name"]
        qty = item.get("quantity", 1)

        options = item.get("options", {})
        opt_text = ", ".join(
            [v for v in options.values() if v]
        )

        line = f"- {qty} {name}"
        if opt_text:
            line += f" ({opt_text})"

        lines.append(line)

    return {
        "intent": "confirm",
        "message": "Bạn muốn đặt:\n\n" + "\n".join(lines) + "\nXác nhận không?",
        "data": items
    }

def handle_cancel(state):
    reset_state(state)
    return {"message": "Đã hủy đơn của bạn"}

def reset_state(state):
    state.status = "idle"
    state.draft_order = None
    state.save()

def process_add_to_cart(item, user):
    from apps.carts.service import create_cart, serialize_cart

    product = Product.objects.filter(
        name__icontains=item["product_name"]
    ).first()

    toppings = build_toppings(item, product)
    options = build_options(item, item["product_name"], product)

    data = {
        "product": {  
            "id": product.id,
            "name": product.name,
            "price": product.price
        },
        "quantity": item.get("quantity", 1),
        "base_price": product.price,
        "options": options,
        "toppings": toppings
    }

    cart = create_cart(user, data)
    return serialize_cart(cart)

def build_toppings(item, product):
    toppings = []

    for t in item.get("toppings", []):
        name = t.get("name")

        pt = ProductTopping.objects.filter(
            product=product,
            topping__name__iexact=name
        ).select_related("topping").first()

        if not pt:
            continue

        qty = min(t.get("quantity", 1), pt.max_quantity)

        toppings.append({
            "id": pt.topping.id,
            "price": pt.price,
            "quantity": qty
        })

    return toppings

def build_options(item, message, product):

    ai_options = item.get("options", {}) or {}

    # Map AI → options_dict
    options_dict = map_ai_options(ai_options, product)

    # Fallback nếu AI thiếu
    if not options_dict:
        extracted = extract_options(message, product)
        options_dict.update(extracted)

    # Luôn luôn apply default
    return apply_default_options(product, options_dict)

def map_ai_options(ai_options, product):
    from collections import defaultdict

    options_dict = {}

    if not ai_options:
        return options_dict

    # 🔥 lấy option theo product
    pos = ProductOption.objects.filter(product=product)\
        .select_related("option__group")

    # group theo group
    grouped = defaultdict(list)
    group_map = {}

    for po in pos:
        group = po.option.group
        grouped[group.id].append(po.option)
        group_map[group.id] = group

    # normalize key AI
    ai_options_norm = {
        k.lower(): (v.lower() if isinstance(v, str) else v)
        for k, v in ai_options.items() if v
    }

    # 🔥 mapping
    for group_id, options in grouped.items():
        group = group_map[group_id]
        group_keywords = [k.lower() for k in (group.keywords or [])]

        matched_value = None

        # 1. match theo key (size, ice, sugar)
        for key, value in ai_options_norm.items():
            if key in group_keywords:
                matched_value = value
                break

        # 2. fallback: match theo value ("ít đá" chứa "đá")
        if not matched_value:
            for value in ai_options_norm.values():
                if any(k in value for k in group_keywords):
                    matched_value = value
                    break

        if not matched_value:
            continue

        # 🔥 tìm option phù hợp trong group
        selected_option = None

        for opt in options:
            opt_name = opt.name.lower()

            # match trực tiếp
            if opt_name in matched_value:
                selected_option = opt
                break

            # match keyword (nếu bạn thêm keywords cho Option)
            if hasattr(opt, "keywords") and opt.keywords:
                if any(k in matched_value for k in opt.keywords):
                    selected_option = opt
                    break

        if selected_option:
            options_dict[group.name] = selected_option

    return options_dict