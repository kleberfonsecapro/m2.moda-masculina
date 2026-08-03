from decimal import Decimal

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from catalog import views as catalog_views
from catalog.models import Category, FeaturedProduct, Product
from cart.models import Cart
from cart.services import get_cart_items, get_cart_total
from shipping.models import ShippingConfig


def home(request):
    featured_items = FeaturedProduct.objects.filter(
        active=True
    ).select_related('product__category').prefetch_related('product__variants')
    categories = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__available=True))
    ).order_by('-featured', 'name')
    recent_products = Product.objects.filter(
        available=True
    ).prefetch_related('variants').order_by('-created_at')[:8]
    return render(request, 'mobile/catalog/home.html', {
        'featured_items': featured_items,
        'categories': categories,
        'recent_products': recent_products,
    })


def categories(request):
    categories = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__available=True))
    ).order_by('-featured', 'name')
    return render(request, 'mobile/catalog/categories.html', {
        'categories': categories,
    })


def product_list(request, category_slug=None):
    category = None
    products = Product.objects.filter(available=True).prefetch_related('variants')

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(code__icontains=query)
        )

    return render(request, 'mobile/catalog/product_list.html', {
        'category': category,
        'products': products,
        'query': query,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    return render(request, 'mobile/catalog/product_detail.html', {
        'product': product,
        'shipping_config': ShippingConfig.objects.first(),
    })


def cart(request):
    items = get_cart_items(request)
    total = get_cart_total(request)
    shipping = request.session.get('shipping')
    context = {
        'cart_items': items,
        'cart_total': total,
        'cart_count': sum(i['quantity'] for i in items),
        'shipping': shipping,
    }
    if shipping:
        context['shipping_total'] = total + Decimal(shipping.get('value', '0'))
    return render(request, 'mobile/catalog/cart.html', context)


def checkout(request):
    return catalog_views.store_checkout(
        request,
        template_name='mobile/catalog/checkout.html',
        empty_cart_view_name='mobile:cart',
        success_view_name='mobile:order_success',
    )


def order_success(request, order_id):
    return catalog_views.order_success(
        request,
        order_id,
        template_name='mobile/catalog/order_success.html',
    )


class SalesLoginView(LoginView):
    template_name = 'mobile/sales/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return reverse('mobile:sales_page')


@login_required(login_url='/m/vendas/entrar/')
def sales_page(request):
    cart_obj = Cart.objects.prefetch_related('items__product__category').filter(
        user=request.user
    ).first()
    return render(request, 'mobile/sales/sales_page.html', {'cart': cart_obj})


def profile(request):
    return render(request, 'mobile/account/profile.html')


def view_mobile(request):
    response = redirect('mobile:home')
    response.set_cookie(
        'view_mode',
        'mobile',
        max_age=31536000,
        samesite='Lax',
        secure=settings.SESSION_COOKIE_SECURE,
    )
    return response


def view_desktop(request):
    response = redirect('catalog:home')
    response.set_cookie(
        'view_mode',
        'desktop',
        max_age=31536000,
        samesite='Lax',
        secure=settings.SESSION_COOKIE_SECURE,
    )
    return response
