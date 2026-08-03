from catalog.models import Product, Variant


def cart_item_key(product_id, variant_id=None):
    return f'{product_id}-{variant_id or ""}'


def get_cart_items(request):
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
            'key': cart_item_key(item['product_id'], item.get('variant_id')),
            'product': product,
            'variant': variant,
            'quantity': item['quantity'],
            'total': product.effective_price * item['quantity'],
        })
    return items


def get_cart_total(request):
    return sum(i['total'] for i in get_cart_items(request))


def clear_shipping(request):
    request.session.pop('shipping', None)
    request.session.modified = True
