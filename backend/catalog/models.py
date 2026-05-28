from django.db import models
from django.urls import reverse


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
    name = models.CharField('Nome', max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField('Descrição')
    price = models.DecimalField('Preço', max_digits=10, decimal_places=2)
    promotional_price = models.DecimalField(
        'Preço Promocional', max_digits=10, decimal_places=2,
        blank=True, null=True
    )
    image = models.ImageField('Imagem', upload_to='products/%Y/%m/')
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
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:product_detail', args=[self.slug])

    @property
    def effective_price(self):
        return self.promotional_price if self.promotional_price else self.price


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
