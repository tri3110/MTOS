from django.db import models
from apps.users.models import User

from apps.products.models import Option, Product, Topping

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    session_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Dùng cho user chưa đăng nhập"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart of {self.user.username}"
        return f"Guest Cart ({self.session_id})"
    
class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)

    price_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    created_at = models.DateTimeField(auto_now_add=True)

class CartItemOption(models.Model):
    cart_item = models.ForeignKey(
        CartItem,
        on_delete=models.CASCADE,
        related_name="options"
    )
    option = models.ForeignKey(Option, on_delete=models.CASCADE)

class CartItemTopping(models.Model):
    cart_item = models.ForeignKey(
        CartItem,
        on_delete=models.CASCADE,
        related_name="toppings"
    )
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)