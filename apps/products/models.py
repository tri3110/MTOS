from django.db import models
from apps.users.models import User
from django.contrib.postgres.indexes import GinIndex


class Category(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    slug = models.SlugField(unique=True, null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="category_created")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="category_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('out_of_stock', 'Out of Stock'),
    ]

    name = models.CharField(max_length=150, db_index=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    purchase_count = models.IntegerField(default=0)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="product_created")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="product_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        indexes = [
            GinIndex(
                fields=['name'],
                name='product_name_trgm',
                opclasses=['gin_trgm_ops']
            ),
        ]
    
class Topping(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='toppings/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="topping_created")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="topping_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class ProductTopping(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_toppings'
    )

    topping = models.ForeignKey(
        Topping,
        on_delete=models.CASCADE
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)
    max_quantity = models.IntegerField(default=3)
    is_required = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} - {self.topping.name}"

class OptionGroup(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=100)  # Ngọt, Đá
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="option_group_created")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="option_group_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Option(models.Model):
    group = models.ForeignKey(
        OptionGroup,
        on_delete=models.CASCADE,
        related_name='options',
        null=True,
    )

    name = models.CharField(max_length=100)  # ít, bình thường, nhiều
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
class ProductOption(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_options'
    )

    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE
    )

    is_required = models.BooleanField(default=True)

    class Meta:
        unique_together = ('product', 'option')