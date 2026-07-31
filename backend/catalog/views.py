import json

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models, transaction
from django.urls import reverse
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from orders.forms import OrderCreateForm
from orders.models import Order, OrderItem
from cart.models import Cart, CartItem
from .models import Category, Product, Variant, FeaturedProduct, CarouselSlide, CarouselSettings, Newsletter


def home(request):
    featured_items = FeaturedProduct.objects.filter(
        active=True
    ).select_related('product__category').prefetch_related('product__variants')
    categories = Category.objects.all().order_by('-featured', 'name')
    recent_products = Product.objects.filter(
        available=True
    ).prefetch_related('variants').order_by('-created_at')[:8]
    slides = CarouselSlide.objects.filter(active=True).order_by('order')
    carousel_settings = CarouselSettings.objects.first()
    return render(request, 'catalog/home.html', {
        'featured_items': featured_items,
        'categories': categories,
        'recent_products': recent_products,
        'slides': slides,
        'carousel_settings': carousel_settings,
    })


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True).prefetch_related('variants')

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

    if quantity < 1:
        return JsonResponse({'error': 'Quantidade deve ser maior que zero'}, status=400)

    product = get_object_or_404(Product, code=code, available=True)

    cart_obj, _ = Cart.objects.get_or_create(user=request.user)

    try:
        cart_item = CartItem.objects.get(cart=cart_obj, product=product, variant__isnull=True)
        created = False
    except CartItem.DoesNotExist:
        cart_item = CartItem(cart=cart_obj, product=product, variant=None, quantity=0)
        created = True

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

    with transaction.atomic():
        product_ids = [item.product_id for item in cart.items.all()]
        locked_products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)}

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
            product = locked_products[cart_item.product_id]
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


def product_search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})

    products = Product.objects.filter(
        models.Q(name__icontains=q) | models.Q(code__icontains=q),
        available=True
    ).select_related('category').prefetch_related('variants')[:8]

    results = []
    for p in products:
        variant_data = []
        for v in p.variants.all():
            variant_data.append({
                'id': v.id,
                'size': v.size,
                'color': v.color,
                'stock': v.stock,
                'sku': v.sku,
            })
        results.append({
            'id': p.id,
            'code': p.code,
            'name': p.name,
            'slug': p.slug,
            'price': str(p.effective_price),
            'promotional_price': str(p.promotional_price) if p.promotional_price else None,
            'discount_percentage': p.discount_percentage,
            'image': p.image.url,
            'has_variants': p.has_variants,
            'variants': variant_data,
            'category': p.category.name,
            'category_slug': p.category.slug,
            'url': p.get_absolute_url(),
        })

    return JsonResponse({'results': results})


def _cart_item_key(product_id, variant_id=None):
    return f'{product_id}-{variant_id or ""}'


@require_POST
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity', 1))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Dados inválidos'}, status=400)

    if not product_id or quantity < 1:
        return JsonResponse({'error': 'Produto e quantidade obrigatórios'}, status=400)

    product = get_object_or_404(Product, id=product_id, available=True)

    variant = None
    if variant_id:
        variant = get_object_or_404(Variant, id=variant_id, product=product)

    stock_source = variant if variant else product

    session = request.session
    cart = session.get('cart', [])
    cart_key = _cart_item_key(product_id, variant_id)

    existing_qty = next(
        (
            i['quantity']
            for i in cart
            if _cart_item_key(i['product_id'], i.get('variant_id')) == cart_key
        ),
        0,
    )

    new_total = existing_qty + quantity
    if new_total > stock_source.stock:
        return JsonResponse({
            'error': f'Estoque insuficiente. Disponível: {stock_source.stock}, já no carrinho: {existing_qty}',
        }, status=400)

    for item in cart:
        if _cart_item_key(item['product_id'], item.get('variant_id')) == cart_key:
            item['quantity'] = new_total
            break
    else:
        cart.append({
            'product_id': product_id,
            'variant_id': variant_id,
            'quantity': quantity,
        })

    session['cart'] = cart
    session.modified = True

    return JsonResponse({
        'success': True,
        'cart_count': sum(i['quantity'] for i in cart),
    })


@require_POST
def update_cart(request):
    try:
        data = json.loads(request.body)
        item_key = data.get('key')
        action = data.get('action')
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Dados inválidos'}, status=400)

    if action not in ('remove', 'increase', 'decrease'):
        return JsonResponse({'error': 'Ação inválida'}, status=400)

    session = request.session
    cart = session.get('cart', [])

    if action == 'remove':
        cart = [
            i for i in cart
            if _cart_item_key(i['product_id'], i.get('variant_id')) != item_key
        ]
    else:
        for i in cart:
            if _cart_item_key(i['product_id'], i.get('variant_id')) == item_key:
                if action == 'increase':
                    i['quantity'] += 1
                elif action == 'decrease':
                    i['quantity'] = max(1, i['quantity'] - 1)
                break

    session['cart'] = cart
    session.modified = True

    return JsonResponse({
        'success': True,
        'cart_count': sum(i['quantity'] for i in cart),
    })


def cart_page(request):
    items = _get_cart_items(request)
    total = _get_cart_total(request)
    return render(request, 'catalog/cart.html', {
        'cart_items': items,
        'cart_total': total,
    })


def store_checkout(request):
    if not request.user.is_authenticated:
        messages.info(request, 'Faça login para finalizar seu pedido.')
        return redirect(f"{reverse('accounts:login')}?next={reverse('catalog:store_checkout')}")

    items = _get_cart_items(request)
    total = _get_cart_total(request)

    if not items:
        messages.info(request, 'Seu carrinho está vazio.')
        return redirect('catalog:cart_page')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                product_ids = [item['product'].id for item in items]
                locked_products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)}

                order = form.save(commit=False)
                order.user = request.user
                order.save()

                for item_data in items:
                    product_id = item_data['product'].id
                    product = locked_products[product_id]
                    variant = item_data['variant']
                    quantity = item_data['quantity']

                    stock_source = variant if variant else product
                    if quantity > stock_source.stock:
                        messages.error(
                            request,
                            f'Estoque insuficiente para {product.name}. Disponível: {stock_source.stock}',
                        )
                        return redirect('catalog:cart_page')

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        variant=variant,
                        price=product.effective_price,
                        quantity=quantity,
                    )

                    stock_source.stock -= quantity
                    stock_source.save(update_fields=['stock'])

            request.session['cart'] = []
            request.session.modified = True
            messages.success(request, 'Pedido realizado com sucesso!')
            return redirect('orders:order_detail', order_id=order.id)
    else:
        initial = {
            'full_name': f'{request.user.first_name} {request.user.last_name}',
            'email': request.user.email,
        }
        form = OrderCreateForm(initial=initial)

    return render(request, 'catalog/checkout.html', {
        'form': form,
        'cart_items': items,
        'cart_total': total,
    })


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
@require_POST
def newsletter_signup(request):
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados inválidos'}, status=400)

    if not email:
        return JsonResponse({'error': 'E-mail obrigatório'}, status=400)

    if len(email) > 254:
        return JsonResponse({'error': 'E-mail muito longo'}, status=400)

    import re
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return JsonResponse({'error': 'E-mail inválido'}, status=400)

    Newsletter.objects.get_or_create(email=email)

    return JsonResponse({
        'success': True,
    })


def _get_cart_items(request):
    cart = request.session.get('cart', [])
    items = []
    for item in cart:
        try:
            product = Product.objects.get(id=item['product_id'], available=True)
        except Product.DoesNotExist:
            continue
        variant = None
        if item.get('variant_id'):
            try:
                variant = Variant.objects.get(id=item['variant_id'], product=product)
            except Variant.DoesNotExist:
                pass
        items.append({
            'key': _cart_item_key(item['product_id'], item.get('variant_id')),
            'product': product,
            'variant': variant,
            'quantity': item['quantity'],
            'total': product.effective_price * item['quantity'],
        })
    return items


def _get_cart_total(request):
    return sum(i['total'] for i in _get_cart_items(request))



