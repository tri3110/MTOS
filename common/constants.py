from enum import Enum

class ProductCache(Enum):
    FULL_DATA = ("product:full_data", 300)
    BASIC_DATA = ("product:basic_data", 60)

    def __init__(self, key, ttl):
        self.key = key
        self.ttl = ttl

class CategoryCache(Enum):
    FULL_DATA = ("category:full_data", 300)
    BASIC_DATA = ("category:basic_data", 60)

    def __init__(self, key, ttl):
        self.key = key
        self.ttl = ttl

class ToppingCache(Enum):
    ACTIVE = ("topping:active", 300)

    def __init__(self, key, ttl):
        self.key = key
        self.ttl = ttl

class OptionGroupCache(Enum):
    ACTIVE = ("optiongroup:active", 300)

    def __init__(self, key, ttl):
        self.key = key
        self.ttl = ttl

class StoreCache(Enum):
    ACTIVE = ("stores:active", 300)

    def __init__(self, key, ttl):
        self.key = key
        self.ttl = ttl

class SliderCache(Enum):
    ACTIVE = ("sliders:active", 300)

    def __init__(self, key, ttl):
        self.key = key
        self.ttl = ttl

class UserCache(Enum):
    ACTIVE = ("users:active", 300)
    CHAT = ("users:chat", 86400) # 86400s = 1 day

    def __init__(self, key, ttl):
        self.key = key
        self.ttl = ttl

class HomeCache(Enum):
    ACTIVE = ("home:data", 100)

    def __init__(self, key, ttl):
        self.key = key
        self.ttl = ttl

class Constant():
    SHIPPING_FEE = 15000
    UNITS_NUMBER = {
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

    ORDER_KEYWORDS = ["cho", "mua", "lấy", "order", "đặt"]

    GREETING_WORDS = [
        "hi", "hello", "xin chào", "chào", "hey", "helo"
    ]

    RESPONSES_GREETING = [
        "Xin chào. Bạn muốn uống gì hôm nay?",
        "Hello! Mình là Diệu Diệu. Bạn gọi món nhé!",
        "Chào bạn. Hôm nay uống gì nào?"
    ]

    CONFIRM_WORDS = [
        "ok", "oke", "ok rồi", "đúng rồi", "chuẩn", "confirm", "đặt đi", "ừ", "uh", 
        "đồng ý", "xác nhận", "yes", "đúng", "chốt đơn", "chốt", "đặt", "đặt hàng", "uk"
    ]

    CANCEL_WORDS = [
        "hủy", "thôi", "không mua nữa", "bỏ đi", "cancel", "hủy đơn", "hủy đi", "hủy order", "hủy bỏ"
    ]
   