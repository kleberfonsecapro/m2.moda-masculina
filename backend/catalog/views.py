import json

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from .models import Category, Product, FeaturedProduct, CarouselSlide, CarouselSettings


def home(request):
    featured_items = FeaturedProduct.objects.filter(active=True).select_related('product')
    featured_products = [item.product for item in featured_items if item.product.available]
    categories = Category.objects.all().order_by('-featured', 'name')
    featured_categories = Category.objects.filter(featured=True)
    slides = CarouselSlide.objects.filter(active=True).order_by('order')
    carousel_settings = CarouselSettings.objects.first()
    return render(request, 'catalog/home.html', {
        'featured_items': featured_items,
        'categories': categories,
        'featured_categories': featured_categories,
        'slides': slides,
        'carousel_settings': carousel_settings,
    })


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return render(request, 'catalog/product_list.html', {
        'category': category,
        'categories': categories,
        'products': products,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(
        category=product.category, available=True
    ).exclude(id=product.id)[:4]

    return render(request, 'catalog/product_detail.html', {
        'product': product,
        'related_products': related_products,
    })


@login_required(login_url='/vendas/entrar/')
def sales_page(request):
    try:
        cart_obj = Cart.objects.prefetch_related('items__product__category').get(user=request.user)
    except Cart.DoesNotExist:
        cart_obj = None

    return render(request, 'catalog/sales.html', {
        'cart': cart_obj,
    })


@login_required(login_url='/vendas/entrar/')
@require_POST
def sales_add_item(request):
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip()
        quantity = int(data.get('quantity', 1))
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Dados inválidos'}, status=400)

    if not code:
        return JsonResponse({'error': 'Código do produto é obrigatório'}, status=400)

    product = get_object_or_404(Product, code=code, available=True)

    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart_obj, product=product,
        defaults={'quantity': 0}
    )

    new_qty = cart_item.quantity + quantity
    if new_qty > product.stock:
        return JsonResponse({
            'error': f'Estoque insuficiente. Disponível: {product.stock}',
        }, status=400)

    cart_item.quantity = new_qty
    cart_item.save()

    return JsonResponse({
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
            'code': product.code,
            'price': str(product.effective_price),
            'image': product.image.url,
        },
        'cart_total': str(cart_obj.total),
        'cart_items': cart_obj.total_items,
    })


@login_required(login_url='/vendas/entrar/')
@require_POST
def sales_checkout(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    try:
        cart = Cart.objects.prefetch_related('items__product').get(user=request.user)
    except Cart.DoesNotExist:
        return JsonResponse({'error': 'Carrinho vazio'}, status=400)

    if not cart.items.exists():
        return JsonResponse({'error': 'Carrinho vazio'}, status=400)

    payment_method = data.get('payment_method', 'cash')
    if payment_method not in dict(Order.PAYMENT_CHOICES):
        return JsonResponse({'error': 'Forma de pagamento inválida'}, status=400)

    customer_name = data.get('customer_name', '').strip() or request.user.get_full_name() or request.user.username
    customer_phone = data.get('customer_phone', '').strip()

    order = Order.objects.create(
        user=request.user,
        full_name=customer_name,
        email=request.user.email,
        phone=customer_phone,
        address='Venda presencial',
        city='',
        state='',
        zip_code='',
        payment_method=payment_method,
    )

    for cart_item in cart.items.all():
        product = cart_item.product
        if cart_item.quantity > product.stock:
            return JsonResponse({
                'error': f'Estoque insuficiente para {product.name}. Disponível: {product.stock}',
            }, status=400)

        OrderItem.objects.create(
            order=order,
            product=product,
            price=product.effective_price,
            quantity=cart_item.quantity,
        )
        product.stock -= cart_item.quantity
        product.save(update_fields=['stock'])

    cart.items.all().delete()

    return JsonResponse({
        'success': True,
        'order_id': order.id,
        'payment_method': order.get_payment_method_display(),
        'total': str(order.total),
        'items': [
            {'name': item.product.name, 'qty': item.quantity, 'total': str(item.total)}
            for item in order.items.all()
        ],
        'redirect': reverse('orders:order_detail', args=[order.id]),
    })


@login_required(login_url='/vendas/entrar/')
def sales_product_lookup(request):
    code = request.GET.get('code', '').strip()
    if not code:
        return JsonResponse({'error': 'Código obrigatório'}, status=400)

    product = get_object_or_404(Product, code=code, available=True)

    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'code': product.code,
        'price': str(product.effective_price),
        'image': product.image.url,
        'stock': product.stock,
    })


@login_required(login_url='/vendas/entrar/')
def stock_page(request):
    products = Product.objects.all().order_by('code')
    total_stock_value = sum(p.stock_value for p in products)
    total_items = sum(p.stock for p in products)

    return render(request, 'catalog/stock.html', {
        'products': products,
        'total_stock_value': total_stock_value,
        'total_items': total_items,
    })
