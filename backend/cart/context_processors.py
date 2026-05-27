from .models import Cart


def cart(request):
    cart_items_count = 0
    cart_items = []

    if request.user.is_authenticated:
        try:
            cart_obj = Cart.objects.get(user=request.user)
            cart_items = cart_obj.items.select_related('product').all()
            cart_items_count = cart_obj.total_items
        except Cart.DoesNotExist:
            pass

    return {
        'cart_items_count': cart_items_count,
        'cart_items': cart_items,
    }
