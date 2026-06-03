import io

from django.db import models
from django.urls import reverse
from django.core.files.base import ContentFile


class Category(models.Model):
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField('Descrição', blank=True)
    featured = models.BooleanField('Destaque', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:product_list_by_category', args=[self.slug])


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='products',
        verbose_name='Categoria'
    )
    code = models.CharField('Código', max_length=20, unique=True, blank=True)
    name = models.CharField('Nome', max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField('Descrição')
    purchase_price = models.DecimalField(
        'Preço de Compra', max_digits=10, decimal_places=2,
        default=0
    )
    price = models.DecimalField('Preço de Venda', max_digits=10, decimal_places=2)
    promotional_price = models.DecimalField(
        'Preço Promocional', max_digits=10, decimal_places=2,
        blank=True, null=True
    )
    image = models.ImageField('Imagem', upload_to='products/%Y/%m/')
    qrcode_image = models.ImageField('QR Code', upload_to='qrcodes/', blank=True)
    stock = models.PositiveIntegerField('Estoque', default=0)
    available = models.BooleanField('Disponível', default=True)
    featured = models.BooleanField('Destaque', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'{self.code} - {self.name}' if self.code else self.name

    def get_absolute_url(self):
        return reverse('catalog:product_detail', args=[self.slug])

    @property
    def effective_price(self):
        return self.promotional_price if self.promotional_price else self.price

    @property
    def stock_value(self):
        return (self.purchase_price or 0) * self.stock

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        skip_qrcode = kwargs.pop('_skip_qrcode', False)

        super().save(*args, **kwargs)

        if is_new and not self.code:
            self.code = f'M2-{self.pk:05d}'
            self.save(update_fields=['code'], _skip_qrcode=True)
            self._generate_qrcode()
            return

        if not skip_qrcode:
            self._generate_qrcode()

    def _generate_qrcode(self):
        if not self.code:
            return

        text = (
            f'M2 Moda Masculina\n'
            f'Produto: {self.name}\n'
            f'Código: {self.code}\n'
            f'Preço: R$ {self.effective_price}'
        )

        try:
            import qrcode as qrcode_lib
            img = qrcode_lib.make(text)
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            filename = f'qrcode_{self.code}.png'
            self.qrcode_image.save(
                filename, ContentFile(buffer.getvalue()), save=False
            )
            super().save(update_fields=['qrcode_image'])
        except ImportError:
            pass


class FeaturedProduct(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='featured_items',
        verbose_name='Produto'
    )
    label = models.CharField('Rótulo', max_length=100, blank=True,
        help_text='Ex: "Lançamento", "Mais Vendido"')
    image = models.ImageField('Imagem', upload_to='featured/', blank=True,
        help_text='Deixe vazio para usar a imagem do produto')
    order = models.PositiveIntegerField('Ordem', default=0)
    active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Produto em Destaque'
        verbose_name_plural = 'Produtos em Destaque'

    def __str__(self):
        return f'{self.product.name} (ordem {self.order})'


class CarouselSlide(models.Model):
    label = models.CharField('Rótulo', max_length=100, blank=True,
        help_text='Ex: "Nova Coleção", "Ofertas"')
    title = models.CharField('Título', max_length=200, blank=True,
        help_text='Ex: "Camisas de Time"')
    title_highlight = models.CharField('Título em destaque', max_length=200, blank=True,
        help_text='Parte do título com cor de destaque. Ex: "Brasil"')
    description = models.TextField('Descrição', blank=True)
    image = models.ImageField('Imagem', upload_to='carousel/', blank=True)
    image_url = models.URLField('URL da Imagem', max_length=500, blank=True,
        help_text='Usado somente se nenhuma imagem for enviada acima')
    link_url = models.CharField('URL do Link', max_length=200, blank=True,
        help_text='Ex: /catalog/camisas-time/ ou deixe vazio para /')
    link_text = models.CharField('Texto do Botão', max_length=100, default='Ver Agora')
    order = models.PositiveIntegerField('Ordem', default=0)
    active = models.BooleanField('Ativo', default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Slide do Carrossel'
        verbose_name_plural = 'Slides do Carrossel'

    def __str__(self):
        return self.title or self.label or f'Slide #{self.order}'


class SiteConfig(models.Model):
    whatsapp_number = models.CharField(
        'WhatsApp', max_length=20,
        help_text='Número com DDI e DDD. Ex: 5511999999999'
    )
    instagram = models.URLField(
        'Instagram', max_length=255, blank=True,
        help_text='URL completa do perfil. Ex: https://instagram.com/m.2modamasculina'
    )
    facebook = models.URLField(
        'Facebook', max_length=255, blank=True,
        help_text='URL completa da página'
    )
    youtube = models.URLField(
        'YouTube', max_length=255, blank=True,
        help_text='URL completa do canal'
    )
    tiktok = models.URLField(
        'TikTok', max_length=255, blank=True,
        help_text='URL completa do perfil'
    )
    twitter = models.URLField(
        'Twitter / X', max_length=255, blank=True,
        help_text='URL completa do perfil'
    )
    email = models.EmailField(
        'E-mail', max_length=255, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração do Site'
        verbose_name_plural = 'Configurações do Site'

    def __str__(self):
        return 'Configurações do Site'

    def save(self, *args, **kwargs):
        if not self.pk and SiteConfig.objects.exists():
            return
        super().save(*args, **kwargs)


class CarouselSettings(models.Model):
    autoplay_interval = models.PositiveIntegerField(
        'Intervalo automático (ms)', default=5000,
        help_text='Tempo entre cada slide em milissegundos (5000 = 5s)'
    )
    transition_speed = models.PositiveIntegerField(
        'Velocidade da transição (ms)', default=800,
        help_text='Duração da animação entre slides'
    )

    class Meta:
        verbose_name = 'Configuração do Carrossel'
        verbose_name_plural = 'Configurações do Carrossel'

    def __str__(self):
        return 'Configurações do Carrossel'

    def save(self, *args, **kwargs):
        if not self.pk and CarouselSettings.objects.exists():
            return
        super().save(*args, **kwargs)
