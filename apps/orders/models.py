from django.db import models
from apps.products.models import Product, Topping
from apps.stores.models import StoreModel
from apps.users.models import User
from apps.vouchers.models import Voucher

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('waiting_payment', 'Waiting Payment'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('delivering', 'Delivering'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ("cod", "Cash on Delivery"),
        ("momo", "MoMo"),
        ("vnpay", "VNPay"),
        ("zalopay", "ZaloPay"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    store = models.ForeignKey(StoreModel, on_delete=models.SET_NULL, null=True)
    voucher = models.ForeignKey(Voucher, on_delete=models.SET_NULL, null=True, blank=True)

    customer_name = models.CharField(max_length=100)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    earned_points = models.IntegerField(default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    idempotency_key = models.CharField(max_length=100, unique=True)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default="momo")
    payment_url = models.TextField(null=True, blank=True)
    qr_code = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    def calculate_total(self):
        total = 0

        for item in self.items.all():
            item_total = item.price * item.quantity

            topping_total = sum(
                t.price * t.quantity for t in item.toppings.all()
            )

            total += item_total + topping_total

        self.total_price = total
        return total
    
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
class OrderItemTopping(models.Model):
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='toppings'
    )
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)

    class Meta:
        unique_together = ('order_item', 'topping')

    def __str__(self):
        return f"{self.topping.name} x {self.quantity}"
    
class OrderLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='logs')
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
class Delivery(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    shipper_name = models.CharField(max_length=100)
    delivered_at = models.DateTimeField(null=True, blank=True)
 