from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .forms import UserRegistrationForm, ContactForm
from .models import Profile, Product, Logo, Slider, Order, OrderItem
from django.http import HttpResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
import random
import string

def generate_verification_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def home(request):
    product = Product.objects.all()
    logo = Logo.objects.all()
    slider = Slider.objects.all()
    return render(request, "home.html", {
        'slider': slider,
        'product': product,
        'logo': logo,
    })

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})

def success(request):
    return render(request, 'success.html')

def product(request, post_id):
    product = get_object_or_404(Product, id=post_id)
    return render(request, 'product.html', {'product': product})

@login_required
def cart(request):
    cart = request.session.get('cart', {})
    product_ids = cart.keys()
    products = {product.id: product for product in Product.objects.filter(id__in=product_ids)}
    cart_items = [(products.get(int(product_id)), quantity) for product_id, quantity in cart.items()]
    total_price = sum(product.price * quantity for product, quantity in cart_items if product)
    
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    product = get_object_or_404(Product, id=product_id)
    cart[product_id] = cart.get(product_id, 0) + 1
    request.session['cart'] = cart
    return redirect('/')

@login_required
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    if product_id_str in cart:
        if cart[product_id_str] > 1:
            cart[product_id_str] -= 1
        else:
            del cart[product_id_str]
        request.session['cart'] = cart
    return redirect('cart')

@login_required
def cod(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('cart')
    
    products = {product_id: Product.objects.get(id=int(product_id)) for product_id in cart.keys()}
    cart_items = [(products.get(product_id), quantity) for product_id, quantity in cart.items()]
    total_price = sum(product.price * quantity for product, quantity in cart_items if product)
    
    return render(request, 'cod.html', {'cart_items': cart_items, 'total_price': total_price})

@require_POST
@login_required
def confirm_order(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('cart')

    full_name = request.POST.get('full_name')
    phone_number = request.POST.get('phone_number')
    address = request.POST.get('address')

    order = Order.objects.create(
        user=request.user,
        full_name=full_name,
        phone_number=phone_number,
        address=address,
    )

    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
        )

    request.session['cart'] = {}
    return render(request, 'order_confirmed.html', {'order': order})

def search_view(request):
    query = request.GET.get('q')
    results = []
    if query:
        results = Product.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))
        if not results:
            messages.info(request, 'No products found.')
    return render(request, 'search_results.html', {'query': query, 'results': results})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Store user data temporarily in session
            request.session['temp_user_data'] = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password'],
                'phone_number': form.cleaned_data['phone_number'],
                'address': form.cleaned_data['address']
            }

            # Generate verification code and send email
            verification_code = generate_verification_code()
            try:
                send_mail(
                    'Verify your email',
                    f'Your verification code is {verification_code}',
                    'your_email@example.com',  # Replace with your email
                    [form.cleaned_data['email']],
                    fail_silently=False,
                )
                # Save verification code in session
                request.session['verification_code'] = verification_code
                messages.success(request, 'Check your email for the verification code.')
                return redirect('verify_email')
            except BadHeaderError:
                messages.error(request, 'Invalid header found.')
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
                
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})

def verify_email(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        if code == request.session.get('verification_code'):
            # Retrieve temporary user data from the session
            temp_user_data = request.session.get('temp_user_data')
            if temp_user_data:
                # Create the user
                user = User.objects.create_user(
                    username=temp_user_data['username'],
                    email=temp_user_data['email'],
                    password=temp_user_data['password']
                )
                
                # Check if the profile already exists
                profile, created = Profile.objects.get_or_create(user=user)
                
                # If profile was newly created, set additional fields
                if created:
                    profile.phone_number = temp_user_data['phone_number']
                    profile.address = temp_user_data['address']
                    profile.email_verified = True  # Set to True upon verification
                    profile.save()

                # Log the user in
                login(request, user)
                messages.success(request, 'Email verified successfully! You are now logged in.')
                # Clear session data
                del request.session['temp_user_data']
                del request.session['verification_code']
                return redirect('home')
            else:
                messages.error(request, 'Temporary user data not found.')
        else:
            messages.error(request, 'Invalid verification code.')

    return render(request, 'verify_email.html')


@login_required
def user_orders(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'user_orders.html', {'orders': orders})

class CustomLoginView(LoginView):
    template_name = 'login.html'
