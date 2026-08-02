import os
import sys
import django
from django.core.files import File
from django.conf import settings
from io import BytesIO
import urllib.request
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'm2shop.settings')
django.setup()

from catalog.models import Category, Product, Variant, FeaturedProduct, SiteConfig, TickerMessage
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q


def download_image(url):
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        img_file = BytesIO(resp.read())
        return img_file
    except Exception as e:
        print(f"  Erro ao baixar imagem {url}: {e}")
        return None


def create_superuser():
    if not User.objects.filter(username='admin').exists():
        password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        if password == 'admin123':
            print("  ⚠️  AVISO: Usando senha padrão 'admin123' para superusuário. Defina ADMIN_PASSWORD no .env")
        User.objects.create_superuser('admin', 'admin@m2moda.com.br', password)
        print("  Superusuário 'admin' criado")
    else:
        print("  Superusuário 'admin' já existe")


@transaction.atomic
def seed():
    print("Populando banco de dados...")

    create_superuser()

    categories_data = [
        {'name': 'Camisas Peruanas', 'slug': 'camisas-peruanas', 'description': 'Camisas peruanas bordadas, coloridas e estilosas.'},
        {'name': 'Camisetas Oversized', 'slug': 'camisetas-oversized', 'description': 'Camisetas oversized com estampas urbanas e básicas.'},
        {'name': 'Camisas de Time', 'slug': 'camisas-time', 'description': 'Camisas de futebol retrô e modernas.'},
        {'name': 'Joggers', 'slug': 'joggers', 'description': 'Calças joggers cargo, moletom e tactel.'},
        {'name': 'Cargo Pants', 'slug': 'cargo-pants', 'description': 'Calças cargo oversized e wide leg.'},
        {'name': 'Jaquetas', 'slug': 'jaquetas', 'description': 'Jaquetas, corta-vento e sobretudos urbanos.'},
        {'name': 'Calçados', 'slug': 'calcados', 'description': 'Tênis, sneakers e botas.'},
        {'name': 'Acessórios', 'slug': 'acessorios', 'description': 'Bonés, gorros, correntes, mochilas e cintos.'},
    ]

    categories = {}
    for cat_data in categories_data:
        cat, created = Category.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        categories[cat.slug] = cat
        if created:
            print(f"  Categoria '{cat.name}' criada")
        else:
            print(f"  Categoria '{cat.name}' já existe")

    products_data = [
        # Camisas Peruanas
        {
            'category_slug': 'camisas-peruanas',
            'name': 'Camisa Peruana Bordada Colorida',
            'slug': 'camisa-peruana-bordada-colorida',
            'description': 'Camisa peruana artesanal com bordados típicos coloridos. Algodão leve, modelagem reta, gola cubana. Peça única cheia de personalidade para looks estilosos.',
            'price': 179.90,
            'promotional_price': 149.90,
            'stock': 20,
            'featured': True,
            'image_url': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=600',
        },
        {
            'category_slug': 'camisas-peruanas',
            'name': 'Camisa Peruana Branca Detalhes Pretos',
            'slug': 'camisa-peruana-branca-detalhes-pretos',
            'description': 'Camisa peruana branca com bordados geométricos em preto. Tecido artesanal, botões de madrepérola. Estilo boho-chic com atitude urbana.',
            'price': 169.90,
            'promotional_price': None,
            'stock': 15,
            'featured': True,
            'image_url': 'https://images.unsplash.com/photo-1589310243389-96a5483213a8?w=600',
        },
        # Camisetas Oversized
        {
            'category_slug': 'camisetas-oversized',
            'name': 'Camiseta Oversized Preta Algodão 40',
            'slug': 'camiseta-oversized-preta-algodao-40',
            'description': 'Camiseta oversized em algodão penteado 40.1. Gola reforçada, modelagem ampla, caimento reto. A base do streetwear.',
            'price': 99.90,
            'promotional_price': 79.90,
            'stock': 80,
            'featured': True,
            'image_url': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600',
        },
        {
            'category_slug': 'camisetas-oversized',
            'name': 'Camiseta Oversized Branca Estampa Gráfica',
            'slug': 'camiseta-oversized-branca-estampa-grafica',
            'description': 'Camiseta oversized branca com estampa gráfica exclusiva. Algodão 30.1, gola redonda, modelagem larga. Estilo urbano autêntico.',
            'price': 109.90,
            'promotional_price': None,
            'stock': 60,
            'featured': True,
            'image_url': 'https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=600',
        },
        {
            'category_slug': 'camisetas-oversized',
            'name': 'Camiseta Oversized Cinza Mesch',
            'slug': 'camiseta-oversized-cinza-mesch',
            'description': 'Camiseta oversized em mescla de algodão. Modelagem ampla, gola redonda reforçada. Conforto extremo para o dia a dia.',
            'price': 89.90,
            'promotional_price': None,
            'stock': 70,
            'featured': False,
            'image_url': 'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=600',
        },
        # Camisas de Time
        {
            'category_slug': 'camisas-time',
            'name': 'Camisa Retrô Brasil 1994',
            'slug': 'camisa-retro-brasil-1994',
            'description': 'Camisa retrô da Seleção Brasileira 1994. Réplica fiel com tecido leve e tecnológico. Gola polo, listras tradicionais.',
            'price': 199.90,
            'promotional_price': 169.90,
            'stock': 30,
            'featured': True,
            'image_url': 'https://images.unsplash.com/photo-1577223625816-7546f13df25d?w=600',
        },
        {
            'category_slug': 'camisas-time',
            'name': 'Camisa Futebol Flamengo Torcedor',
            'slug': 'camisa-futebol-flamengo-torcedor',
            'description': 'Camisa de futebol estilo torcedor. Tecido poliéster respirável, escudo bordado, modelagem regular. Vista sua paixão.',
            'price': 179.90,
            'promotional_price': None,
            'stock': 40,
            'featured': False,
            'image_url': 'https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=600',
        },
        # Joggers
        {
            'category_slug': 'joggers',
            'name': 'Jogger Cargo Preta Elástico',
            'slug': 'jogger-cargo-preta-elastico',
            'description': 'Calça jogger cargo preta em sarja. Cós elástico com cordão, barra ajustada com elástico, bolsos laterais e cargo. Conforto e estilo.',
            'price': 149.90,
            'promotional_price': 129.90,
            'stock': 45,
            'featured': True,
            'image_url': 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=600',
        },
        {
            'category_slug': 'joggers',
            'name': 'Jogger Moletom Cinza Escuro',
            'slug': 'jogger-moletom-cinza-escuro',
            'description': 'Calça jogger em moletom 440g cinza escuro. Cós elástico, barra com ribana, bolsos laterais. Conforto térmico com estilo urbano.',
            'price': 129.90,
            'promotional_price': None,
            'stock': 55,
            'featured': False,
            'image_url': 'https://images.unsplash.com/photo-1552902865-b72c031ac5ea?w=600',
        },
        # Cargo Pants
        {
            'category_slug': 'cargo-pants',
            'name': 'Cargo Wide Leg Preta',
            'slug': 'cargo-wide-leg-preta',
            'description': 'Calça cargo wide leg preta em sarja resistente. Cintura regular, perna larga, 6 bolsos funcionais. A silhueta oversized que domina o streetwear.',
            'price': 189.90,
            'promotional_price': 159.90,
            'stock': 35,
            'featured': True,
            'image_url': 'https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=600',
        },
        {
            'category_slug': 'cargo-pants',
            'name': 'Cargo Cargo Bege Bolsos Laterais',
            'slug': 'cargo-cargo-bege-bolsos-laterais',
            'description': 'Calça cargo bege com modelagem reta. Bolsos laterais volumosos, cintura com presilhas para cinto. Peça chave do guarda-roupa urbano.',
            'price': 169.90,
            'promotional_price': None,
            'stock': 30,
            'featured': False,
            'image_url': 'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=600',
        },
        # Camisas de Time - França
        {
            'category_slug': 'camisas-time',
            'name': 'Camisa França Torcedor Azul',
            'slug': 'camisa-franca-torcedor-azul',
            'description': 'Camisa de futebol estilo torcedor da França. Tecido poliéster respirável, escudo bordado, modelagem regular. Azul clássico.',
            'price': 199.90,
            'promotional_price': 179.90,
            'stock': 30,
            'featured': True,
            'image_url': 'https://images.unsplash.com/photo-1562157873-818bc0726f68?w=600',
        },
        {
            'category_slug': 'camisas-time',
            'name': 'Camisa França Pré-Jogo Azul Escuro',
            'slug': 'camisa-franca-pre-jogo-azul-escuro',
            'description': 'Camisa pré-jogo da França azul escuro. Tecido leve e tecnológico, gola careca, escudo dourado. Elegância dentro e fora do campo.',
            'price': 219.90,
            'promotional_price': None,
            'stock': 20,
            'featured': True,
            'image_url': 'https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=600',
        },
        # Calçados
        {
            'category_slug': 'calcados',
            'name': 'Tênis Sneaker Branco Casual',
            'slug': 'tenis-sneaker-branco-casual',
            'description': 'Tênis sneaker branco em couro sintético. Solado tratorado, palmilha macia, cadarço grosso. O clássico do streetwear.',
            'price': 229.90,
            'promotional_price': 199.90,
            'stock': 35,
            'featured': True,
            'image_url': 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=600',
        },
        {
            'category_slug': 'calcados',
            'name': 'Tênis Cano Alto Preto',
            'slug': 'tenis-cano-alto-preto',
            'description': 'Tênis cano alto preto com solado robusto. Couro sintético, cadarço até o topo, forro interno macio. Estilo urbano e atitude.',
            'price': 259.90,
            'promotional_price': None,
            'stock': 25,
            'featured': True,
            'image_url': 'https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=600',
        },
        # Acessórios
        {
            'category_slug': 'acessorios',
            'name': 'Boné Street Preto Aba Curva',
            'slug': 'bone-street-preto-aba-curva',
            'description': 'Boné street preo com aba curva. Bordado frontal M2, fecho ajustável, algodão twill. O acessório essencial do visual urbano.',
            'price': 69.90,
            'promotional_price': 59.90,
            'stock': 60,
            'featured': True,
            'image_url': 'https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=600',
        },
        {
            'category_slug': 'acessorios',
            'name': 'Corrente Choker Prata Grosso',
            'slug': 'corrente-choker-prata-grosso',
            'description': 'Corrente choker em aço inoxidável prata. Elos grossos, fecho caranguejo, 45cm. O toque final para o look streetwear.',
            'price': 89.90,
            'promotional_price': None,
            'stock': 40,
            'featured': False,
            'image_url': 'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=600',
        },
    ]

    products_dir = Path(settings.MEDIA_ROOT) / 'products'
    products_dir.mkdir(parents=True, exist_ok=True)

    for prod_data in products_data:
        cat = categories[prod_data.pop('category_slug')]
        image_url = prod_data.pop('image_url')

        product, created = Product.objects.get_or_create(
            slug=prod_data['slug'],
            defaults={**prod_data, 'category': cat}
        )

        if created:
            print(f"  Produto '{product.name}' criado")
            img_data = download_image(image_url)
            if img_data:
                from datetime import datetime
                month_path = Path(str(datetime.now().year)) / f"{datetime.now().month:02d}"
                save_dir = products_dir / month_path
                save_dir.mkdir(parents=True, exist_ok=True)
                filename = f"{product.slug}.jpg"
                product.image.save(filename, File(img_data), save=True)
                print(f"    Imagem baixada para '{product.name}'")
        else:
            print(f"  Produto '{product.name}' já existe")

    # Criar variações (tamanhos) para cada produto
    sizes_map = {
        'Camisas Peruanas': ['P', 'M', 'G', 'GG'],
        'Camisetas Oversized': ['P', 'M', 'G', 'GG'],
        'Camisas de Time': ['P', 'M', 'G', 'GG'],
        'Joggers': ['P', 'M', 'G', 'GG'],
        'Cargo Pants': ['P', 'M', 'G', 'GG'],
        'Jaquetas': ['P', 'M', 'G', 'GG'],
        'Calçados': ['38', '39', '40', '41', '42'],
        'Acessórios': ['Único'],
    }
    for product in Product.objects.all():
        sizes = sizes_map.get(product.category.name, ['P', 'M', 'G'])
        for i, size in enumerate(sizes):
            stock = max(0, product.stock // len(sizes) + (i < product.stock % len(sizes)))
            Variant.objects.get_or_create(
                product=product,
                size=size,
                defaults={'stock': stock, 'order': i, 'sku': f'{product.code}-{size}'},
            )
        print(f'  Variantes criadas para {product.name}')

    # Criar Produtos em Destaque
    for i, product in enumerate(Product.objects.filter(featured=True)):
        FeaturedProduct.objects.get_or_create(
            product=product,
            defaults={'label': '', 'order': i, 'active': True},
        )
    print('  Produtos em destaque criados')

    # Criar Configuração do Site (padrão)
    if not SiteConfig.objects.exists():
        SiteConfig.objects.create(
            whatsapp_number='5511999999999',
            instagram='https://instagram.com/m.2modamasculina',
            facebook='https://facebook.com/m2modamasculina',
            email='contato@m2moda.com.br',
        )
        print('  SiteConfig criado')
    else:
        print('  SiteConfig já existe')

    # Frases do Ticker (barra de avisos do topo)
    if not TickerMessage.objects.exists():
        default_phrases = [
            '🔥 Moda masculina com estilo e atitude',
            '🚚 Frete grátis acima de R$ 199',
            '💳 Parcele em até 3x sem juros',
        ]
        for order, phrase in enumerate(default_phrases):
            TickerMessage.objects.create(text=phrase, order=order, active=True)
        print('  Frases do Ticker criadas')
    else:
        print('  Frases do Ticker já existem')

    # Gerar códigos e QR Codes para produtos existentes
    pending = Product.objects.filter(
        Q(code__isnull=True) | Q(code='') | Q(qrcode_image='')
    )
    count = pending.count()
    if count:
        for product in pending:
            product.save()
        print(f"  QR Codes e códigos gerados para {count} produto(s)")

    # Configuração padrão de frete (embalagem + região). Tarifas ficam no admin.
    from shipping.models import ShippingConfig, ShippingRegion
    config, created = ShippingConfig.objects.get_or_create(
        cep_origem='00000000',
        defaults={'cep_origem': '00000000', 'peso_padrao_kg': 1.0},
    )
    if created:
        print("  Configuração de frete criada (AJUSTE o CEP de origem e a embalagem no admin)")
    else:
        print("  Configuração de frete já existe")

    region, region_created = ShippingRegion.objects.get_or_create(
        nome='Todo Brasil',
        defaults={
            'nome': 'Todo Brasil',
            'cep_inicio': '00000000',
            'cep_fim': '99999999',
            'fator': 1.0,
        },
    )
    if region_created:
        print("  Região 'Todo Brasil' criada (ajuste faixas e fatores no admin)")
    else:
        print("  Região 'Todo Brasil' já existe")
    print("  IMPORTANTE: cadastre as TARIFAS (Sedex, PAC) em Admin > Frete > Tarifas de Envio")

    print("\nBanco populado com sucesso!")
    print("\nCredenciais de acesso:")
    print("  Admin:   usuario=admin (senha definida via ADMIN_PASSWORD ou 'admin123')")
    print("  URL Admin: http://localhost:8000/admin/")


if __name__ == '__main__':
    seed()
