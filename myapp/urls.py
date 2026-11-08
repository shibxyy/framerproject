from django.urls import path
from . import views

urlpatterns = [
    # Landing & Auth
    path('', views.index, name='index'),
    path('register/farmer/', views.register_farmer, name='register_farmer'),
    path('register/consumer/', views.register_consumer, name='register_consumer'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Admin Module
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-farmers/', views.admin_farmers, name='admin_farmers'),
    path('admin-farmer-action/<int:farmer_id>/<str:action>/', views.admin_farmer_action, name='admin_farmer_action'),
    path('admin-consumers/', views.admin_consumers, name='admin_consumers'),
    path('admin-categories/', views.admin_categories, name='admin_categories'),
    path('admin-category-edit/<int:category_id>/', views.admin_category_edit, name='admin_category_edit'),
    path('admin-category-delete/<int:category_id>/', views.admin_category_delete, name='admin_category_delete'),
    path('admin-products/', views.admin_products, name='admin_products'),
    path('admin-product-action/<int:product_id>/<str:action>/', views.admin_product_action, name='admin_product_action'),
    path('admin-orders/', views.admin_orders, name='admin_orders'),
    path('admin-complaints/', views.admin_complaints, name='admin_complaints'),
    path('admin-reports/', views.admin_reports, name='admin_reports'),
    path('admin-reviews/', views.admin_reviews, name='admin_reviews'),
    path('admin-review-delete/<int:review_id>/', views.admin_delete_review, name='admin_delete_review'),

    # Farmer Module
    path('farmer-dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
    path('farmer-profile/', views.farmer_profile, name='farmer_profile'),
    path('farmer-products/', views.farmer_products, name='farmer_products'),
    path('farmer-product-add/', views.farmer_product_add, name='farmer_product_add'),
    path('farmer-product-edit/<int:product_id>/', views.farmer_product_edit, name='farmer_product_edit'),
    path('farmer-product-delete/<int:product_id>/', views.farmer_product_delete, name='farmer_product_delete'),
    path('farmer-orders/', views.farmer_orders, name='farmer_orders'),
    path('farmer-order-status/<int:item_id>/<str:status>/', views.farmer_update_order_status, name='farmer_update_order_status'),
    path('farmer-reports/', views.farmer_reports, name='farmer_reports'),
    path('farmer-reviews/', views.farmer_reviews, name='farmer_reviews'),


    # Consumer Module
    path('consumer-dashboard/', views.consumer_dashboard, name='consumer_dashboard'),
    path('consumer-profile/', views.consumer_profile, name='consumer_profile'),
    path('marketplace/', views.marketplace, name='marketplace'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:cart_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/remove/<int:cart_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('consumer-orders/', views.consumer_orders, name='consumer_orders'),
    path('consumer-order-track/<int:order_id>/', views.consumer_order_track, name='consumer_order_track'),
    path('consumer-order-cancel/<int:order_id>/', views.consumer_cancel_order, name='consumer_order_cancel'),
    path('consumer-complaints/', views.consumer_complaints, name='consumer_complaints'),
    path('consumer-notifications/', views.consumer_notifications, name='consumer_notifications'),
]
