def cart(request):
    session_cart = request.session.get('cart', [])
    count = sum(i['quantity'] for i in session_cart)
    return {'cart_count': count}
