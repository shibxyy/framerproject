from django.contrib import admin
from .models import Farmer, Consumer, Category, Product, Cart, Order, OrderItem, Feedback, Complaint, Notification

@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'phone_number', 'farm_location', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('full_name', 'user__username', 'phone_number', 'farm_location')

@admin.register(Consumer)
class ConsumerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'phone_number', 'created_at')
    search_fields = ('full_name', 'user__username', 'phone_number', 'delivery_address')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'created_at')
    search_fields = ('category_name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'farmer', 'category', 'price_per_kg', 'stock_quantity', 'status', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('product_name', 'farmer__full_name', 'description')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('consumer', 'product', 'quantity', 'created_at')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'consumer', 'total_amount', 'order_status', 'payment_status', 'order_date')
    list_filter = ('order_status', 'payment_status', 'order_date')
    search_fields = ('id', 'consumer__full_name', 'transaction_id')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'farmer', 'quantity', 'price', 'item_status')
    list_filter = ('item_status',)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('consumer', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'subject', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('subject', 'description', 'user__username')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('consumer', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
