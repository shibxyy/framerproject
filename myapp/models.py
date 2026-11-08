from django.db import models
from django.contrib.auth.models import User

class Farmer(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Blocked', 'Blocked'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farmer_profile')
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    farm_location = models.CharField(max_length=255)
    profile_image = models.ImageField(upload_to='farmers/', default='farmers/default.jpg', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"

class Consumer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='consumer_profile')
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    delivery_address = models.TextField()
    profile_image = models.ImageField(upload_to='consumers/', default='consumers/default.jpg', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"

class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    category_image = models.ImageField(upload_to='categories/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.category_name

class Product(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Out Of Stock', 'Out Of Stock'),
    )
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    product_name = models.CharField(max_length=200)
    description = models.TextField()
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    product_image = models.ImageField(upload_to='products/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product_name} - {self.farmer.full_name}"

class Cart(models.Model):
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.quantity * self.product.price_per_kg

    def __str__(self):
        return f"{self.consumer.full_name} - {self.product.product_name} ({self.quantity}kg)"

class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Packed', 'Packed'),
        ('Out For Delivery', 'Out For Delivery'),
        ('Delivered', 'Delivered'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    )
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_address = models.TextField()
    payment_status = models.CharField(max_length=20, default='Paid')
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    order_status = models.CharField(max_length=30, choices=ORDER_STATUS_CHOICES, default='Pending')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.consumer.full_name}"

class OrderItem(models.Model):
    ITEM_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Packed', 'Packed'),
        ('Out For Delivery', 'Out For Delivery'),
        ('Delivered', 'Delivered'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    item_status = models.CharField(max_length=30, choices=ITEM_STATUS_CHOICES, default='Pending')

    def subtotal(self):
        return self.quantity * self.price

    def __str__(self):
        return f"Order #{self.order.id} Item: {self.product.product_name}"

class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='feedbacks')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField(choices=RATING_CHOICES, default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.consumer.full_name} rating {self.rating} on {self.product.product_name}"

class Complaint(models.Model):
    COMPLAINT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Rejected', 'Rejected'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=COMPLAINT_STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Complaint #{self.id} by {self.user.username} - {self.subject}"

class Notification(models.Model):
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification to {self.consumer.full_name}: {self.title}"
