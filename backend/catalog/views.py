from django.shortcuts import render, get_object_or_404
from .models import Category, Product, CarouselSlide, CarouselSettings


def home(request):
    featured_products = Product.objects.filter(available=True, featured=True)[:8]
    categories = Category.objects.all().order_by('-featured', 'name')
    featured_categories = Category.objects.filter(featured=True)
    slides = CarouselSlide.objects.filter(active=True).order_by('order')
    carousel_settings = CarouselSettings.objects.first()
    return render(request, 'catalog/home.html', {
        'featured_products': featured_products,
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
