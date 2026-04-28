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
   