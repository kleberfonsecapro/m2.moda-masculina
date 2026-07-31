from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from cart.models import Cart, CartItem
from catalog.models import Product, Variant


@receiver(user_logged_in)
def migrate_session_cart(sender, request, user, **kwargs):
    session_cart = request.session.get('cart', [])
    if not session_cart:
        return

    cart_obj, _ = Cart.objects.get_or_create(user=user)

    for item in session_cart:
        product_id = item.get('product_id')
        variant_id = item.get('variant_id')
        quantity = item.get('quantity', 1)

        try:
            product = Product.objects.get(id=product_id, available=True)
        except Product.DoesNotExist:
            continue

        variant = None
        if variant_id:
            try:
                variant = Variant.objects.get(id=variant_id, product=product)
            except Variant.DoesNotExist:
                continue

        stock_source = variant if variant else product
        existing = CartItem.objects.filter(
            cart=cart_obj, product=product, variant=variant
        ).first()

        if existing:
            new_qty = min(existing.quantity + quantity, stock_source.stock)
            existing.quantity = new_qty
            existing.save()
        else:
            qty = min(quantity, stock_source.stock)
            if qty > 0:
                CartItem.objects.create(
                    cart=cart_obj,
                    product=product,
                    variant=variant,
                    quantity=qty,
                )

    request.session['cart'] = []
    request.session.modified = True
