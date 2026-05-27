from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from catalog.models import Product
from .models import Cart, CartItem


@login_required
def cart_detail(request):
    try:
        cart_obj = Cart.objects.prefetch_related('items__product').get(user=request.user)
    except Cart.DoesNotExist:
        cart_obj = None

    return render(request, 'cart/cart_detail.html', {'cart': cart_obj})


@login_required
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart_obj, product=product,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f'{product.name} adicionado ao carrinho.')
    return redirect('cart:cart_detail')


@login_required
def cart_remove(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.info(request, 'Item removido do carrinho.')
    return redirect('cart:cart_detail')


@login_required
def cart_update(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = request.POST.get('quantity', 1)
    try:
        quantity = int(quantity)
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    except ValueError:
        pass
    return redirect('cart:cart_detail')
