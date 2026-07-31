from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from cart.models import Cart
from catalog.models import Product
from .models import Order, OrderItem
from .forms import OrderCreateForm


@login_required
def order_create(request):
    try:
        cart = Cart.objects.prefetch_related('items__product').get(user=request.user)
    except Cart.DoesNotExist:
        messages.info(request, 'Seu carrinho está vazio.')
        return redirect('catalog:product_list')

    if not cart.items.exists():
        messages.info(request, 'Seu carrinho está vazio.')
        return redirect('catalog:product_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                product_ids = [item.product_id for item in cart.items.all()]
                locked_products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)}

                order = form.save(commit=False)
                order.user = request.user
                order.save()

                for cart_item in cart.items.all():
                    product = locked_products[cart_item.product_id]
                    if cart_item.quantity > product.stock:
                        messages.error(
                            request,
                            f'Estoque insuficiente para {product.name}. Disponível: {product.stock}',
                        )
                        return redirect('cart:cart_detail')

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        price=product.effective_price,
                        quantity=cart_item.quantity,
                    )
                    product.stock -= cart_item.quantity
                    product.save(update_fields=['stock'])

                cart.items.all().delete()
            messages.success(request, 'Pedido realizado com sucesso!')
            return redirect('orders:order_detail', order_id=order.id)
    else:
        form = OrderCreateForm(
            initial={
                'full_name': f'{request.user.first_name} {request.user.last_name}',
                'email': request.user.email,
            }
        )

    return render(request, 'orders/order_create.html', {
        'form': form,
        'cart': cart,
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/order_list.html', {'orders': orders})
