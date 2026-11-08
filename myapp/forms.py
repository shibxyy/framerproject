import re
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Farmer, Consumer, Category, Product, Complaint, Feedback

# Custom Validators
def validate_phone_number(value):
    if not value:
        raise ValidationError("Phone number is required.")
    cleaned = re.sub(r'[\s\-\+\(\)]', '', value)
    if not cleaned.isdigit():
        raise ValidationError("Phone number must contain only numeric digits.")
    if len(cleaned) < 10 or len(cleaned) > 15:
        raise ValidationError("Phone number must be between 10 and 15 digits.")

def validate_image_file(file):
    if file:
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        import os
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in valid_extensions:
            raise ValidationError(f"Unsupported file format '{ext}'. Allowed formats: JPG, JPEG, PNG, WEBP.")
        max_size = 5 * 1024 * 1024 # 5 MB
        if file.size > max_size:
            raise ValidationError(f"Image file size ({round(file.size/(1024*1024), 2)}MB) exceeds maximum allowed limit of 5MB.")

class FarmerRegistrationForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        min_length=3,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Username'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password (min 6 characters)'})
    )
    confirm_password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    full_name = forms.CharField(
        max_length=200,
        min_length=3,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'})
    )
    phone_number = forms.CharField(
        validators=[validate_phone_number],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit Phone Number'})
    )
    address = forms.CharField(
        min_length=5,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Address'})
    )
    farm_location = forms.CharField(
        max_length=255,
        min_length=3,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Farm Location / District'})
    )
    profile_image = forms.ImageField(
        required=False,
        validators=[validate_image_file],
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Farmer
        fields = ['full_name', 'phone_number', 'address', 'farm_location', 'profile_image']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match. Please enter matching passwords.")

        username = cleaned_data.get("username")
        if username and User.objects.filter(username=username).exists():
            self.add_error('username', f"Username '{username}' is already taken. Please choose a different username.")

        email = cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            self.add_error('email', f"Email address '{email}' is already registered.")

        return cleaned_data

class ConsumerRegistrationForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        min_length=3,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Username'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password (min 6 characters)'})
    )
    confirm_password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    full_name = forms.CharField(
        max_length=200,
        min_length=3,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'})
    )
    phone_number = forms.CharField(
        validators=[validate_phone_number],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit Phone Number'})
    )
    delivery_address = forms.CharField(
        min_length=5,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Default Delivery Address'})
    )
    profile_image = forms.ImageField(
        required=False,
        validators=[validate_image_file],
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Consumer
        fields = ['full_name', 'phone_number', 'delivery_address', 'profile_image']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match. Please enter matching passwords.")

        username = cleaned_data.get("username")
        if username and User.objects.filter(username=username).exists():
            self.add_error('username', f"Username '{username}' is already taken.")

        email = cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            self.add_error('email', f"Email address '{email}' is already registered.")

        return cleaned_data

class CategoryForm(forms.ModelForm):
    category_name = forms.CharField(
        max_length=100,
        min_length=2,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category Name'})
    )
    category_image = forms.ImageField(
        validators=[validate_image_file],
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Category
        fields = ['category_name', 'category_image']

    def clean_category_name(self):
        name = self.cleaned_data.get('category_name')
        if name:
            qs = Category.objects.filter(category_name__iexact=name)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f"Category '{name}' already exists.")
        return name

class ProductForm(forms.ModelForm):
    product_name = forms.CharField(
        max_length=200,
        min_length=2,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vegetable Name'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    description = forms.CharField(
        min_length=10,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Produce description & organic notes...'})
    )
    price_per_kg = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price per kg (₹)'})
    )
    stock_quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Available Stock (kg)'})
    )
    product_image = forms.ImageField(
        validators=[validate_image_file],
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Product
        fields = ['category', 'product_name', 'description', 'price_per_kg', 'stock_quantity', 'product_image']

class FarmerProfileForm(forms.ModelForm):
    full_name = forms.CharField(max_length=200, min_length=3, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(validators=[validate_phone_number], widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(min_length=5, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    farm_location = forms.CharField(max_length=255, min_length=3, widget=forms.TextInput(attrs={'class': 'form-control'}))
    profile_image = forms.ImageField(required=False, validators=[validate_image_file], widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Farmer
        fields = ['full_name', 'phone_number', 'address', 'farm_location', 'profile_image']

class ConsumerProfileForm(forms.ModelForm):
    full_name = forms.CharField(max_length=200, min_length=3, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(validators=[validate_phone_number], widget=forms.TextInput(attrs={'class': 'form-control'}))
    delivery_address = forms.CharField(min_length=5, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    profile_image = forms.ImageField(required=False, validators=[validate_image_file], widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Consumer
        fields = ['full_name', 'phone_number', 'delivery_address', 'profile_image']

class ComplaintForm(forms.ModelForm):
    subject = forms.CharField(max_length=255, min_length=5, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject of complaint'}))
    description = forms.CharField(min_length=10, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your complaint in detail...'}))

    class Meta:
        model = Complaint
        fields = ['subject', 'description']

class FeedbackForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[(i, f"{i} Stars") for i in range(5, 0, -1)],
        coerce=int,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'ratingSelect'}),
        required=True,
        error_messages={'required': 'Please select a star rating between 1 and 5.'}
    )
    comment = forms.CharField(
        min_length=10,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Share your experience with this vegetable produce... (10 to 500 characters)',
            'maxlength': '500'
        }),
        required=True,
        error_messages={
            'required': 'Review comment is required.',
            'min_length': 'Review comment must be at least 10 characters long.',
            'max_length': 'Review comment cannot exceed 500 characters.'
        }
    )

    class Meta:
        model = Feedback
        fields = ['rating', 'comment']

