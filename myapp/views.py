from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg, F
from django.http import JsonResponse
from django.utils import timezone
import uuid

from .models import (
    Farmer, Consumer, Category, Product, Cart, Order, OrderItem,
    Feedback, Complaint, Notification
)
from .forms import (
    FarmerRegistrationForm, ConsumerRegistrationForm, CategoryForm,
    ProductForm, FarmerProfileForm, ConsumerProfileForm, ComplaintForm, FeedbackForm
)

# ----------------------------------------------------
# HELPER DECORATORS & FUNCTIONS
# ----------------------------------------------------
def get_user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser or user.groups.filter(name='admin').exists():
        return 'admin'
    if user.groups.filter(name='farmer').exists():
        return 'farmer'
    if user.groups.filter(name='consumer').exists():
        return 'consumer'
    return None

def admin_required(view_func):
    @never_cache
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to access this page.")
            return redirect('login')
        role = get_user_role(request.user)
        if role != 'admin':
            messages.error(request, "Access Denied: You do not have permission to access the Admin Portal.")
            return redirect_dashboard(request.user)
        response = view_func(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    return _wrapped_view

def farmer_required(view_func):
    @never_cache
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to access this page.")
            return redirect('login')
        role = get_user_role(request.user)
        if role != 'farmer':
            messages.error(request, "Access Denied: You do not have permission to access the Farmer Portal.")
            return redirect_dashboard(request.user)
        try:
            farmer = request.user.farmer_profile
            if farmer.status != 'Approved':
                messages.warning(request, f"Your farmer account status is currently '{farmer.status}'. Access restricted until approved by Admin.")
                return redirect('index')
        except Farmer.DoesNotExist:
            messages.error(request, "Farmer profile not found.")
            return redirect('index')
            
        response = view_func(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    return _wrapped_view

def consumer_required(view_func):
    @never_cache
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to access this page.")
            return redirect('login')
        role = get_user_role(request.user)
        if role != 'consumer':
            messages.error(request, "Access Denied: You do not have permission to access the Consumer Dashboard.")
            return redirect_dashboard(request.user)
        response = view_func(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    return _wrapped_view


def create_notification(consumer, title, message):
    Notification.objects.create(
        consumer=consumer,
        title=title,
        message=message,
        is_read=False
    )

# ----------------------------------------------------
# LANDING & AUTHENTICATION VIEWS
# ----------------------------------------------------
@never_cache
def index(request):
    categories = Category.objects.all()[:6]
    featured_products = Product.objects.filter(status='Approved', stock_quantity__gt=0)[:8]
    popular_farmers = Farmer.objects.filter(status='Approved')[:4]
    recent_reviews = Feedback.objects.select_related('consumer', 'product').order_by('-created_at')[:4]
    
    role = get_user_role(request.user)
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'popular_farmers': popular_farmers,
        'recent_reviews': recent_reviews,
        'user_role': role,
    }
    return render(request, 'landing.html', context)

@never_cache
def register_farmer(request):
    if request.user.is_authenticated:
        return redirect_dashboard(request.user)

    if request.method == 'POST':
        form = FarmerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            farmer_group, _ = Group.objects.get_or_create(name='farmer')
            user.groups.add(farmer_group)

            farmer = form.save(commit=False)
            farmer.user = user
            farmer.status = 'Pending'
            farmer.save()

            messages.success(request, "Farmer registration submitted successfully! Please wait for Admin approval before logging in.")
            return redirect('login')
    else:
        form = FarmerRegistrationForm()
    
    return render(request, 'auth/register_farmer.html', {'form': form})

@never_cache
def register_consumer(request):
    if request.user.is_authenticated:
        return redirect_dashboard(request.user)

    if request.method == 'POST':
        form = ConsumerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            consumer_group, _ = Group.objects.get_or_create(name='consumer')
            user.groups.add(consumer_group)

            consumer = form.save(commit=False)
            consumer.user = user
            consumer.save()

            messages.success(request, "Consumer account created successfully! You can now log in.")
            return redirect('login')
    else:
        form = ConsumerRegistrationForm()
    
    return render(request, 'auth/register_consumer.html', {'form': form})

@never_cache
def user_login(request):
    if request.user.is_authenticated:
        return redirect_dashboard(request.user)

    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')

        # Allow username or email login
        user = authenticate(request, username=username_or_email, password=password)
        if not user:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            # Check farmer status if user is farmer
            if user.groups.filter(name='farmer').exists() and not user.is_superuser:
                try:
                    farmer = user.farmer_profile
                    if farmer.status == 'Pending':
                        messages.warning(request, "Your farmer account is pending approval by the Admin.")
                        return render(request, 'auth/login.html')
                    elif farmer.status == 'Rejected':
                        messages.error(request, "Your farmer application was rejected by the Admin.")
                        return render(request, 'auth/login.html')
                    elif farmer.status == 'Blocked':
                        messages.error(request, "Your farmer account has been blocked by the Admin.")
                        return render(request, 'auth/login.html')
                except Farmer.DoesNotExist:
                    messages.error(request, "Farmer profile does not exist.")
                    return render(request, 'auth/login.html')

            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect_dashboard(user)
        else:
            messages.error(request, "Invalid username/email or password.")

    return render(request, 'auth/login.html')

def redirect_dashboard(user):
    role = get_user_role(user)
    if role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'farmer':
        return redirect('farmer_dashboard')
    elif role == 'consumer':
        return redirect('consumer_dashboard')
    else:
        return redirect('index')

@never_cache
def user_logout(request):
    request.session.flush()
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    response = redirect('login')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


# ----------------------------------------------------
# ADMIN MODULE
# ----------------------------------------------------
@admin_required
def admin_dashboard(request):
    total_farmers = Farmer.objects.count()
    pending_farmers = Farmer.objects.filter(status='Pending').count()
    total_consumers = Consumer.objects.count()
    total_categories = Category.objects.count()
    total_products = Product.objects.count()
    pending_products = Product.objects.filter(status='Pending').count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(order_status='Pending').count()
    delivered_orders = Order.objects.filter(order_status='Delivered').count()
    total_revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0.00
    pending_complaints = Complaint.objects.filter(status='Pending').count()

    recent_activities = Order.objects.select_related('consumer').order_by('-order_date')[:5]
    top_farmers = Farmer.objects.annotate(order_count=Count('order_items')).order_by('-order_count')[:5]
    top_products = Product.objects.annotate(sales_count=Count('order_items')).order_by('-sales_count')[:5]

    context = {
        'total_farmers': total_farmers,
        'pending_farmers': pending_farmers,
        'total_consumers': total_consumers,
        'total_categories': total_categories,
        'total_products': total_products,
        'pending_products': pending_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'total_revenue': total_revenue,
        'pending_complaints': pending_complaints,
        'recent_activities': recent_activities,
        'top_farmers': top_farmers,
        'top_products': top_products,
    }
    return render(request, 'admin/dashboard.html', context)

@admin_required
def admin_farmers(request):
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')

    farmers = Farmer.objects.all().order_by('-created_at')
    if status_filter:
        farmers = farmers.filter(status=status_filter)
    if search_query:
        farmers = farmers.filter(Q(full_name__icontains=search_query) | Q(user__username__icontains=search_query) | Q(phone_number__icontains=search_query))

    return render(request, 'admin/farmers.html', {'farmers': farmers, 'status_filter': status_filter, 'search_query': search_query})

@admin_required
def admin_farmer_action(request, farmer_id, action):
    farmer = get_object_or_404(Farmer, id=farmer_id)
    if action == 'approve':
        farmer.status = 'Approved'
        messages.success(request, f"Farmer {farmer.full_name} has been approved.")
    elif action == 'reject':
        farmer.status = 'Rejected'
        messages.warning(request, f"Farmer {farmer.full_name} has been rejected.")
    elif action == 'block':
        farmer.status = 'Blocked'
        messages.error(request, f"Farmer {farmer.full_name} has been blocked.")
    farmer.save()
    return redirect('admin_farmers')

@admin_required
def admin_consumers(request):
    search_query = request.GET.get('q', '')
    consumers = Consumer.objects.all().order_by('-created_at')
    if search_query:
        consumers = consumers.filter(Q(full_name__icontains=search_query) | Q(user__username__icontains=search_query) | Q(phone_number__icontains=search_query))
    return render(request, 'admin/consumers.html', {'consumers': consumers, 'search_query': search_query})

@admin_required
def admin_categories(request):
    categories = Category.objects.annotate(product_count=Count('products')).order_by('category_name')
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "New category added successfully.")
            return redirect('admin_categories')
    else:
        form = CategoryForm()

    return render(request, 'admin/categories.html', {'categories': categories, 'form': form})

@admin_required
def admin_category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully.")
            return redirect('admin_categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'admin/category_form.html', {'form': form, 'category': category})

@admin_required
def admin_category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if category.products.exists():
        messages.error(request, f"Cannot delete category '{category.category_name}' because it contains products. Remove or reassign products first.")
    else:
        category.delete()
        messages.success(request, f"Category '{category.category_name}' deleted successfully.")
    return redirect('admin_categories')

@admin_required
def admin_products(request):
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')

    products = Product.objects.select_related('farmer', 'category').order_by('-created_at')
    if status_filter:
        products = products.filter(status=status_filter)
    if search_query:
        products = products.filter(Q(product_name__icontains=search_query) | Q(farmer__full_name__icontains=search_query) | Q(category__category_name__icontains=search_query))

    return render(request, 'admin/products.html', {'products': products, 'status_filter': status_filter, 'search_query': search_query})

@admin_required
def admin_product_action(request, product_id, action):
    product = get_object_or_404(Product, id=product_id)
    if action == 'approve':
        product.status = 'Approved' if product.stock_quantity > 0 else 'Out Of Stock'
        messages.success(request, f"Product '{product.product_name}' approved.")
    elif action == 'reject':
        product.status = 'Rejected'
        messages.warning(request, f"Product '{product.product_name}' rejected.")
    product.save()
    return redirect('admin_products')

@admin_required
def admin_orders(request):
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')

    orders = Order.objects.select_related('consumer').prefetch_related('items__product').order_by('-order_date')
    if status_filter:
        orders = orders.filter(order_status=status_filter)
    if search_query:
        orders = orders.filter(Q(id__icontains=search_query) | Q(consumer__full_name__icontains=search_query) | Q(transaction_id__icontains=search_query))

    return render(request, 'admin/orders.html', {'orders': orders, 'status_filter': status_filter, 'search_query': search_query})

@admin_required
def admin_complaints(request):
    status_filter = request.GET.get('status', '')
    complaints = Complaint.objects.select_related('user').order_by('-created_at')
    if status_filter:
        complaints = complaints.filter(status=status_filter)

    if request.method == 'POST':
        complaint_id = request.POST.get('complaint_id')
        new_status = request.POST.get('status')
        complaint = get_object_or_404(Complaint, id=complaint_id)
        complaint.status = new_status
        complaint.save()

        # Notify consumer if user has consumer profile
        try:
            consumer = complaint.user.consumer_profile
            create_notification(consumer, "Complaint Status Updated", f"Your complaint #{complaint.id} ('{complaint.subject}') status is now: {new_status}")
        except Consumer.DoesNotExist:
            pass

        messages.success(request, f"Complaint #{complaint.id} status updated to {new_status}.")
        return redirect('admin_complaints')

    return render(request, 'admin/complaints.html', {'complaints': complaints, 'status_filter': status_filter})

@admin_required
def admin_reports(request):
    sales_report = Order.objects.values('order_status').annotate(count=Count('id'), total_revenue=Sum('total_amount'))
    top_farmers = Farmer.objects.annotate(total_sales=Sum('order_items__quantity'), revenue=Sum(F('order_items__quantity') * F('order_items__price'))).order_by('-revenue')[:10]
    top_products = Product.objects.annotate(total_qty=Sum('order_items__quantity'), total_revenue=Sum(F('order_items__quantity') * F('order_items__price'))).order_by('-total_revenue')[:10]
    complaint_stats = Complaint.objects.values('status').annotate(count=Count('id'))

    context = {
        'sales_report': sales_report,
        'top_farmers': top_farmers,
        'top_products': top_products,
        'complaint_stats': complaint_stats,
    }
    return render(request, 'admin/reports.html', context)

# ----------------------------------------------------
# FARMER MODULE
# ----------------------------------------------------
@farmer_required
def farmer_dashboard(request):
    farmer = request.user.farmer_profile
    my_products = Product.objects.filter(farmer=farmer)
    total_products = my_products.count()
    approved_products = my_products.filter(status='Approved').count()
    low_stock_products = my_products.filter(stock_quantity__lte=5).count()

    order_items = OrderItem.objects.filter(farmer=farmer).select_related('order', 'product')
    total_orders = order_items.values('order').distinct().count()
    pending_orders = order_items.filter(item_status='Pending').values('order').distinct().count()
    completed_orders = order_items.filter(item_status='Delivered').values('order').distinct().count()

    total_earnings = order_items.filter(item_status='Delivered').aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0.00

    recent_orders = order_items.order_by('-order__order_date')[:6]

    context = {
        'farmer': farmer,
        'total_products': total_products,
        'approved_products': approved_products,
        'low_stock_products': low_stock_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_earnings': total_earnings,
        'recent_orders': recent_orders,
    }
    return render(request, 'farmer/dashboard.html', context)

@farmer_required
def farmer_profile(request):
    farmer = request.user.farmer_profile
    if request.method == 'POST':
        form = FarmerProfileForm(request.POST, request.FILES, instance=farmer)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('farmer_profile')
    else:
        form = FarmerProfileForm(instance=farmer)
    return render(request, 'farmer/profile.html', {'form': form, 'farmer': farmer})

@farmer_required
def farmer_products(request):
    farmer = request.user.farmer_profile
    products = Product.objects.filter(farmer=farmer).order_by('-created_at')
    return render(request, 'farmer/products.html', {'products': products})

@farmer_required
def farmer_product_add(request):
    farmer = request.user.farmer_profile
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.farmer = farmer
            product.status = 'Pending' # Pending Admin approval
            product.save()
            messages.success(request, f"Vegetable '{product.product_name}' submitted! Awaiting Admin approval.")
            return redirect('farmer_products')
    else:
        form = ProductForm()
    return render(request, 'farmer/product_form.html', {'form': form, 'action': 'Add'})

@farmer_required
def farmer_product_edit(request, product_id):
    farmer = request.user.farmer_profile
    product = get_object_or_404(Product, id=product_id, farmer=farmer)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            updated_product = form.save(commit=False)
            if updated_product.stock_quantity > 0 and updated_product.status == 'Out Of Stock':
                updated_product.status = 'Approved'
            elif updated_product.stock_quantity <= 0:
                updated_product.status = 'Out Of Stock'
            updated_product.save()
            messages.success(request, f"Product '{product.product_name}' updated successfully.")
            return redirect('farmer_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'farmer/product_form.html', {'form': form, 'action': 'Edit', 'product': product})

@farmer_required
def farmer_product_delete(request, product_id):
    farmer = request.user.farmer_profile
    product = get_object_or_404(Product, id=product_id, farmer=farmer)
    
    if OrderItem.objects.filter(product=product).exists():
        messages.error(request, f"Cannot delete '{product.product_name}' as it is linked to existing order history.")
    else:
        product.delete()
        messages.success(request, f"Product '{product.product_name}' deleted successfully.")
    return redirect('farmer_products')

@farmer_required
def farmer_orders(request):
    farmer = request.user.farmer_profile
    status_filter = request.GET.get('status', '')

    items = OrderItem.objects.filter(farmer=farmer).select_related('order__consumer', 'product').order_by('-order__order_date')
    if status_filter:
        items = items.filter(item_status=status_filter)

    return render(request, 'farmer/orders.html', {'order_items': items, 'status_filter': status_filter})

@farmer_required
def farmer_update_order_status(request, item_id, status):
    farmer = request.user.farmer_profile
    item = get_object_or_404(OrderItem, id=item_id, farmer=farmer)
    old_status = item.item_status
    item.item_status = status
    item.save()

    # Sync main order status based on all items
    order = item.order
    all_items = order.items.all()
    statuses = set(i.item_status for i in all_items)
    if statuses == {'Delivered'}:
        order.order_status = 'Delivered'
    elif 'Out For Delivery' in statuses:
        order.order_status = 'Out For Delivery'
    elif 'Packed' in statuses:
        order.order_status = 'Packed'
    elif 'Accepted' in statuses:
        order.order_status = 'Accepted'
    elif statuses == {'Rejected'}:
        order.order_status = 'Rejected'
    order.save()

    # Generate Notification for Consumer
    title = f"Order #{order.id} Update: {status}"
    message = f"Farmer {farmer.full_name} updated your item '{item.product.product_name}' status from '{old_status}' to '{status}'."
    create_notification(order.consumer, title, message)

    messages.success(request, f"Order Item #{item.id} status updated to {status}.")
    return redirect('farmer_orders')

@farmer_required
def farmer_reports(request):
    farmer = request.user.farmer_profile
    order_items = OrderItem.objects.filter(farmer=farmer)

    stock_report = Product.objects.filter(farmer=farmer).order_by('stock_quantity')
    daily_sales = order_items.filter(item_status='Delivered').values('order__order_date__date').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price'))
    ).order_by('-order__order_date__date')[:15]

    monthly_sales = order_items.filter(item_status='Delivered').values('order__order_date__month', 'order__order_date__year').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price'))
    ).order_by('-order__order_date__year', '-order__order_date__month')

    context = {
        'stock_report': stock_report,
        'daily_sales': daily_sales,
        'monthly_sales': monthly_sales,
    }
    return render(request, 'farmer/reports.html', context)

# ----------------------------------------------------
# CONSUMER MODULE
# ----------------------------------------------------
@consumer_required
def consumer_dashboard(request):
    consumer = request.user.consumer_profile
    orders = Order.objects.filter(consumer=consumer).order_by('-order_date')
    recent_orders = orders[:5]
    total_orders = orders.count()
    pending_orders = orders.filter(order_status__in=['Pending', 'Accepted', 'Packed', 'Out For Delivery']).count()

    unread_notifications_count = Notification.objects.filter(consumer=consumer, is_read=False).count()
    recent_notifications = Notification.objects.filter(consumer=consumer).order_by('-created_at')[:5]

    context = {
        'consumer': consumer,
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'unread_notifications_count': unread_notifications_count,
        'recent_notifications': recent_notifications,
    }
    return render(request, 'consumer/dashboard.html', context)

@consumer_required
def marketplace(request):
    consumer = request.user.consumer_profile
    products = Product.objects.filter(status='Approved', stock_quantity__gt=0).select_related('farmer', 'category').annotate(
        avg_rating=Avg('feedbacks__rating'),
        review_count=Count('feedbacks', distinct=True),
        sales_count=Count('order_items', filter=Q(order_items__item_status='Delivered'), distinct=True)
    )
    categories = Category.objects.all()
    farmers = Farmer.objects.filter(status='Approved')

    # Search and Filtering Parameters
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    farmer_id = request.GET.get('farmer', '')
    max_price = request.GET.get('price', '')
    min_rating = request.GET.get('rating', '')
    availability = request.GET.get('availability', '')
    sort_by = request.GET.get('sort', 'newest')

    # Search Filter (Product Name, Category Name, Farmer Name)
    if query:
        products = products.filter(
            Q(product_name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__category_name__icontains=query) |
            Q(farmer__full_name__icontains=query)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if farmer_id:
        products = products.filter(farmer_id=farmer_id)

    if max_price:
        try:
            products = products.filter(price_per_kg__lte=float(max_price))
        except ValueError:
            pass

    if min_rating:
        try:
            products = products.filter(avg_rating__gte=float(min_rating))
        except ValueError:
            pass

    if availability == 'in_stock':
        products = products.filter(stock_quantity__gt=0)

    # Sorting Logic
    if sort_by == 'highest_rated':
        products = products.order_by('-avg_rating', '-review_count')
    elif sort_by == 'most_reviewed':
        products = products.order_by('-review_count', '-avg_rating')
    elif sort_by == 'best_selling':
        products = products.order_by('-sales_count')
    elif sort_by == 'price_low':
        products = products.order_by('price_per_kg')
    elif sort_by == 'price_high':
        products = products.order_by('-price_per_kg')
    else: # newest
        products = products.order_by('-created_at')

    # Recommended Products Queries
    base_approved = Product.objects.filter(status='Approved', stock_quantity__gt=0).select_related('farmer', 'category').annotate(
        avg_rating=Avg('feedbacks__rating'),
        review_count=Count('feedbacks', distinct=True),
        sales_count=Count('order_items', filter=Q(order_items__item_status='Delivered'), distinct=True)
    )
    top_rated_products = base_approved.order_by('-avg_rating', '-review_count')[:4]
    most_reviewed_products = base_approved.order_by('-review_count', '-avg_rating')[:4]
    best_selling_products = base_approved.order_by('-sales_count')[:4]
    newly_added_products = base_approved.order_by('-created_at')[:4]

    # AJAX Response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = []
        for p in products:
            data.append({
                'id': p.id,
                'name': p.product_name,
                'category': p.category.category_name,
                'farmer': p.farmer.full_name,
                'price': float(p.price_per_kg),
                'stock': float(p.stock_quantity),
                'image': p.product_image.url if p.product_image else '/static/images/placeholder.jpg',
                'rating': round(float(p.avg_rating or 0.0), 1),
                'review_count': p.review_count,
            })
        return JsonResponse({'products': data})

    context = {
        'products': products,
        'categories': categories,
        'farmers': farmers,
        'query': query,
        'selected_category': category_id,
        'selected_farmer': farmer_id,
        'max_price': max_price,
        'min_rating': min_rating,
        'availability': availability,
        'sort_by': sort_by,
        'top_rated_products': top_rated_products,
        'most_reviewed_products': most_reviewed_products,
        'best_selling_products': best_selling_products,
        'newly_added_products': newly_added_products,
    }
    return render(request, 'consumer/marketplace.html', context)

@consumer_required
def product_detail(request, product_id):
    consumer = request.user.consumer_profile
    product = get_object_or_404(Product.objects.select_related('farmer', 'category'), id=product_id)
    feedbacks = Feedback.objects.filter(product=product).select_related('consumer').order_by('-created_at')
    
    total_ratings = feedbacks.count()
    avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0.0
    avg_rating_rounded = round(avg_rating, 1)

    # Calculate Star Breakdown
    star_counts = {
        5: feedbacks.filter(rating=5).count(),
        4: feedbacks.filter(rating=4).count(),
        3: feedbacks.filter(rating=3).count(),
        2: feedbacks.filter(rating=2).count(),
        1: feedbacks.filter(rating=1).count(),
    }
    star_pcts = {
        star: round((count / total_ratings * 100), 1) if total_ratings > 0 else 0
        for star, count in star_counts.items()
    }

    # Strict Review Eligibility Rule:
    # Review is ONLY allowed if consumer has purchased this product AND order item status is 'Delivered'
    user_has_ordered = OrderItem.objects.filter(
        order__consumer=consumer,
        product=product,
        item_status='Delivered'
    ).exists()

    user_feedback = Feedback.objects.filter(consumer=consumer, product=product).first()

    if request.method == 'POST':
        if not user_has_ordered:
            messages.error(request, "Review submission is not allowed. You can only review products that have been delivered to you.")
            return redirect('product_detail', product_id=product.id)

        form = FeedbackForm(request.POST, instance=user_feedback) if user_feedback else FeedbackForm(request.POST)
        if form.is_valid():
            if user_feedback:
                user_feedback.rating = form.cleaned_data['rating']
                user_feedback.comment = form.cleaned_data['comment']
                user_feedback.save()
                messages.success(request, "Your review and star rating have been updated successfully!")
                create_notification(consumer, "Review Updated", f"Your review for '{product.product_name}' was updated successfully.")
            else:
                feedback = form.save(commit=False)
                feedback.consumer = consumer
                feedback.product = product
                feedback.save()
                messages.success(request, "Thank you! Product review and 5-star rating submitted successfully.")
                create_notification(consumer, "Review Submitted", f"Your review for '{product.product_name}' was submitted successfully.")
            return redirect('product_detail', product_id=product.id)
    else:
        form = FeedbackForm(instance=user_feedback) if user_feedback else FeedbackForm()

    # Related Products (Same category, excluding current product)
    related_products = Product.objects.filter(
        category=product.category,
        status='Approved',
        stock_quantity__gt=0
    ).exclude(id=product.id).select_related('farmer', 'category').annotate(
        avg_rating=Avg('feedbacks__rating'),
        review_count=Count('feedbacks')
    )[:4]

    context = {
        'product': product,
        'feedbacks': feedbacks,
        'avg_rating': avg_rating_rounded,
        'total_ratings': total_ratings,
        'star_counts': star_counts,
        'star_pcts': star_pcts,
        'user_has_ordered': user_has_ordered,
        'user_feedback': user_feedback,
        'form': form,
        'related_products': related_products,
    }
    return render(request, 'consumer/product_detail.html', context)


@consumer_required
def add_to_cart(request, product_id):
    consumer = request.user.consumer_profile
    product = get_object_or_404(Product, id=product_id)

    if product.status != 'Approved' or product.stock_quantity <= 0:
        messages.error(request, "This vegetable is currently unavailable.")
        return redirect('marketplace')

    try:
        qty = float(request.POST.get('quantity', 1.0))
        if qty <= 0:
            qty = 1.0
    except ValueError:
        qty = 1.0

    if qty > float(product.stock_quantity):
        messages.error(request, f"Requested quantity ({qty}kg) exceeds available stock ({product.stock_quantity}kg).")
        return redirect('product_detail', product_id=product.id)

    cart_item, created = Cart.objects.get_or_create(consumer=consumer, product=product)
    if not created:
        new_qty = float(cart_item.quantity) + qty
        if new_qty > float(product.stock_quantity):
            messages.warning(request, f"Cannot add more. Combined cart quantity ({new_qty}kg) exceeds available stock.")
            return redirect('cart_view')
        cart_item.quantity = new_qty
        cart_item.save()
        messages.success(request, f"Updated quantity of '{product.product_name}' in cart ({new_qty}kg).")
    else:
        cart_item.quantity = qty
        cart_item.save()
        messages.success(request, f"Added {qty}kg of '{product.product_name}' to cart.")

    return redirect('cart_view')

@consumer_required
def cart_view(request):
    consumer = request.user.consumer_profile
    cart_items = Cart.objects.filter(consumer=consumer).select_related('product__farmer')
    
    total_amount = sum(item.total_price() for item in cart_items)
    
    return render(request, 'consumer/cart.html', {'cart_items': cart_items, 'total_amount': total_amount})

@consumer_required
def update_cart_quantity(request, cart_id):
    consumer = request.user.consumer_profile
    cart_item = get_object_or_404(Cart, id=cart_id, consumer=consumer)
    
    if request.method == 'POST':
        try:
            qty = float(request.POST.get('quantity', 1))
            if qty <= 0:
                cart_item.delete()
                messages.info(request, "Item removed from cart.")
            elif qty > float(cart_item.product.stock_quantity):
                messages.error(request, f"Stock limit reached. Max available: {cart_item.product.stock_quantity}kg.")
            else:
                cart_item.quantity = qty
                cart_item.save()
                messages.success(request, "Cart quantity updated.")
        except ValueError:
            messages.error(request, "Invalid quantity.")

    return redirect('cart_view')

@consumer_required
def remove_from_cart(request, cart_id):
    consumer = request.user.consumer_profile
    cart_item = get_object_or_404(Cart, id=cart_id, consumer=consumer)
    cart_item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect('cart_view')

@consumer_required
def checkout(request):
    consumer = request.user.consumer_profile
    cart_items = Cart.objects.filter(consumer=consumer).select_related('product__farmer')

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('marketplace')

    total_amount = sum(item.total_price() for item in cart_items)

    if request.method == 'POST':
        delivery_address = request.POST.get('delivery_address', consumer.delivery_address)
        
        # Verify stock for all items before placing order
        for item in cart_items:
            if item.quantity > item.product.stock_quantity:
                messages.error(request, f"Insufficient stock for '{item.product.product_name}'. Available: {item.product.stock_quantity}kg.")
                return redirect('cart_view')

        # Create Order
        transaction_id = "TXN-" + uuid.uuid4().hex[:10].upper()
        order = Order.objects.create(
            consumer=consumer,
            total_amount=total_amount,
            delivery_address=delivery_address,
            payment_status='Paid',
            transaction_id=transaction_id,
            order_status='Pending'
        )

        # Create Order Items and decrease stock
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                farmer=item.product.farmer,
                quantity=item.quantity,
                price=item.product.price_per_kg,
                item_status='Pending'
            )
            # Automatic Stock Reduction
            item.product.stock_quantity -= item.quantity
            if item.product.stock_quantity <= 0:
                item.product.stock_quantity = 0
                item.product.status = 'Out Of Stock'
            item.product.save()

        # Clear Cart
        cart_items.delete()

        # In-app Notification for Consumer
        create_notification(consumer, "Order Placed Successfully", f"Your order #{order.id} for ₹{total_amount} has been placed successfully! Transaction ID: {transaction_id}")

        messages.success(request, f"Order #{order.id} placed successfully! Thank you for supporting local farmers.")
        return redirect('consumer_order_track', order_id=order.id)

    return render(request, 'consumer/checkout.html', {'cart_items': cart_items, 'total_amount': total_amount, 'consumer': consumer})

@consumer_required
def consumer_orders(request):
    consumer = request.user.consumer_profile
    orders = Order.objects.filter(consumer=consumer).prefetch_related('items__product').order_by('-order_date')
    return render(request, 'consumer/orders.html', {'orders': orders})

@consumer_required
def consumer_order_track(request, order_id):
    consumer = request.user.consumer_profile
    order = get_object_or_404(Order.objects.prefetch_related('items__product', 'items__farmer'), id=order_id, consumer=consumer)
    return render(request, 'consumer/order_track.html', {'order': order})

@consumer_required
def consumer_cancel_order(request, order_id):
    consumer = request.user.consumer_profile
    order = get_object_or_404(Order, id=order_id, consumer=consumer)

    if order.order_status not in ['Pending', 'Accepted']:
        messages.error(request, f"Order #{order.id} cannot be cancelled as it is already '{order.order_status}'.")
        return redirect('consumer_orders')

    order.order_status = 'Cancelled'
    order.save()

    # Restore stock for products
    for item in order.items.all():
        item.item_status = 'Cancelled'
        item.save()
        item.product.stock_quantity += item.quantity
        if item.product.status == 'Out Of Stock' and item.product.stock_quantity > 0:
            item.product.status = 'Approved'
        item.product.save()

    create_notification(consumer, "Order Cancelled", f"Order #{order.id} was cancelled and stock has been updated.")
    messages.info(request, f"Order #{order.id} cancelled successfully.")
    return redirect('consumer_orders')

@consumer_required
def consumer_complaints(request):
    user = request.user
    consumer = user.consumer_profile
    complaints = Complaint.objects.filter(user=user).order_by('-created_at')

    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = user
            complaint.save()

            create_notification(consumer, "Complaint Submitted", f"Your complaint #{complaint.id} ('{complaint.subject}') was submitted successfully.")
            messages.success(request, "Complaint submitted successfully! Our Admin team will review it shortly.")
            return redirect('consumer_complaints')
    else:
        form = ComplaintForm()

    return render(request, 'consumer/complaints.html', {'complaints': complaints, 'form': form})

@consumer_required
def consumer_notifications(request):
    consumer = request.user.consumer_profile
    notifications = Notification.objects.filter(consumer=consumer).order_by('-created_at')

    # AJAX Mark Read action
    if request.method == 'POST':
        notif_id = request.POST.get('notif_id')
        action = request.POST.get('action')
        
        if action == 'mark_all_read':
            notifications.update(is_read=True)
            messages.success(request, "All notifications marked as read.")
        elif notif_id:
            notif = get_object_or_404(Notification, id=notif_id, consumer=consumer)
            notif.is_read = True
            notif.save()
        return redirect('consumer_notifications')

    return render(request, 'consumer/notifications.html', {'notifications': notifications})

@consumer_required
def consumer_profile(request):
    consumer = request.user.consumer_profile
    if request.method == 'POST':
        form = ConsumerProfileForm(request.POST, request.FILES, instance=consumer)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('consumer_profile')
    else:
        form = ConsumerProfileForm(instance=consumer)
    return render(request, 'consumer/profile.html', {'form': form, 'consumer': consumer})

# ----------------------------------------------------
# FARMER & ADMIN REVIEW ANALYTICS MODULES
# ----------------------------------------------------
@farmer_required
def farmer_reviews(request):
    farmer = request.user.farmer_profile
    products = Product.objects.filter(farmer=farmer).annotate(
        avg_rating=Avg('feedbacks__rating'),
        review_count=Count('feedbacks')
    )
    feedbacks = Feedback.objects.filter(product__farmer=farmer).select_related('consumer', 'product').order_by('-created_at')
    
    total_reviews = feedbacks.count()
    overall_avg = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0.0
    best_rated_product = products.order_by('-avg_rating', '-review_count').first()
    lowest_rated_product = products.exclude(avg_rating__isnull=True).order_by('avg_rating').first()

    context = {
        'farmer': farmer,
        'products': products,
        'feedbacks': feedbacks,
        'total_reviews': total_reviews,
        'overall_avg': round(overall_avg, 1),
        'best_rated_product': best_rated_product,
        'lowest_rated_product': lowest_rated_product,
    }
    return render(request, 'farmer/reviews.html', context)

@admin_required
def admin_reviews(request):
    search_query = request.GET.get('q', '')
    rating_filter = request.GET.get('rating', '')
    
    feedbacks = Feedback.objects.select_related('consumer', 'product__farmer').order_by('-created_at')
    if search_query:
        feedbacks = feedbacks.filter(
            Q(product__product_name__icontains=search_query) |
            Q(consumer__full_name__icontains=search_query) |
            Q(comment__icontains=search_query)
        )
    if rating_filter:
        try:
            feedbacks = feedbacks.filter(rating=int(rating_filter))
        except ValueError:
            pass

    total_reviews = Feedback.objects.count()
    platform_avg_rating = Feedback.objects.aggregate(Avg('rating'))['rating__avg'] or 0.0
    top_rated_products = Product.objects.annotate(avg_rating=Avg('feedbacks__rating'), rev_cnt=Count('feedbacks')).filter(rev_cnt__gt=0).order_by('-avg_rating', '-rev_cnt')[:5]

    context = {
        'feedbacks': feedbacks,
        'total_reviews': total_reviews,
        'platform_avg_rating': round(platform_avg_rating, 1),
        'top_rated_products': top_rated_products,
        'search_query': search_query,
        'rating_filter': rating_filter,
    }
    return render(request, 'admin/reviews.html', context)

@admin_required
def admin_delete_review(request, review_id):
    feedback = get_object_or_404(Feedback, id=review_id)
    product_name = feedback.product.product_name
    feedback.delete()
    messages.success(request, f"Review for '{product_name}' has been deleted.")
    return redirect('admin_reviews')

