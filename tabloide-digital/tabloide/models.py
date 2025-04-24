from django.db import models
from utils.rands import slygify_new
from utils.scraper import scrape_product
from utils.images import resize_image
from utils.rules import get_auto_pk
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable
from django.db.models import Sum
from django.db.models import Max


class PostManager(models.Manager):
    def get_published(self):
        return self\
            .filter(is_published=True)\
            .order_by('-pk')
            
class Tag(models.Model):
    class Meta:
        
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        
    name = models.CharField(max_length=50)
    slug = models.SlugField(
        max_length=50, 
        unique=True,
        default=None,
        blank=True,
        null=True,
    )
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slygify_new(self.name, 5)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Category(models.Model):
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        
    name = models.CharField(max_length=50)
    slug = models.SlugField(
        max_length=50, 
        unique=True,
        default=None,
        blank=True,
        null=True,
    )
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slygify_new(self.name, 5)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Promotion(models.Model):
    class Meta:
        verbose_name = 'Promoção'
        verbose_name_plural = 'Promoções'
        
        
    name = models.CharField(max_length=50, verbose_name='Nome da Promoção')
    slug = models.SlugField(
        max_length=50,
        unique=True,
        default=None,
        blank=True,
        null=True,
    )
    description = models.TextField(max_length=255, verbose_name='Descrição da Promoção')
    img_h = models.ImageField(upload_to='promotions/h/', verbose_name='Imagem Horizontal')
    start_date = models.DateField(verbose_name='Data de Início', auto_now_add=True, editable=True)
    end_date = models.DateField(verbose_name='Data de Término')
    order_promo = models.IntegerField(verbose_name='Ordem', blank=True, null=True)
    

    
    def save(self, *args, **kwargs):
        
        
        
        if not self.slug:
            self.slug = slygify_new(self.name, 5)
            
        actual_image = self.img_h.name 
          
        super().save(*args, **kwargs)
        
        if actual_image != self.img_h.name:
            resize_image(self.img_h, 400, True, 70)
        return super().save(*args, **kwargs)
        
    def __str__(self):
        return self.name
    
class Product(models.Model):
    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        
    objects = PostManager()
    codigo = models.IntegerField(
        verbose_name='Código',
        primary_key=True,
        unique=True,
        editable=True,
        serialize=False,
        blank=False,
        null=False,
        default=None,
    )
    combo = models.CharField(max_length=100, verbose_name='Combo', null=True, blank=True)
    related_products = models.ManyToManyField('self', blank=True, symmetrical=False, verbose_name='Produtos Relacionados',through='ProductCombo')
    name = models.CharField(max_length=50, verbose_name='Produto')
    slug = models.SlugField(
        max_length=50,
        unique=True,
        default=None,
        blank=False,
        null=False,
    )
    excerpt = models.CharField(max_length=150, verbose_name='Descrição curta')
    cover = models.URLField(max_length=255, blank=True, null=True, default='')
    vitrine_link = models.URLField(blank=True, default='', null=True, max_length=255)
    is_published = models.BooleanField(
        default=False,
        help_text='Esse campo deve ser marcado para tornar o post publico',
        verbose_name='Ativo'
    )
    old_price = models.DecimalField(max_digits=10, decimal_places=2, default=0,verbose_name='Preço de:')
    new_price = models.DecimalField(max_digits=10, decimal_places=2, default=0,verbose_name='Preço por:') 
    auto_new_price = models.BooleanField(
        default=True,
        help_text='Calcula o preço de acordo com o preço antigo',
        verbose_name='Preço automático')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='post_created_by',
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='post_updated_by',
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, default=None, verbose_name='Categoria'
    )
    tags = models.ManyToManyField(Tag, blank=True, default='')
    promotions = models.ManyToManyField(Promotion, blank=True, default='', editable=True, verbose_name='Promoções', through='ProductPromo')
    text_link = models.CharField(max_length=255, blank=True, null=True, default='', editable=False )
    
    @classmethod
    def create_auto_pk(cls, **kwargs):
        max_pk = cls.objects.aggregate(Max('pk'))['pk__max'] or 989999
        return cls.objects.create(pk=max_pk + 1, **kwargs)
    
    def format_to_link(self):
        return '%20' + self.name.replace(' ', '%20')
    
    def format_brazilian_decimal(self,value):
        """
        Formats decimal number to Brazilian standard
        Example: 1234.56 -> 1.234,56
        """
        if not value:
            return '0,00'
        
        # Convert to string with 2 decimal places
        formatted = '{:.2f}'.format(float(value))
        
        # Split integer and decimal parts
        integer_part, decimal_part = formatted.split('.')
        
        # Add thousand separators
        integer_part = '{:,}'.format(int(integer_part)).replace(',', '.')
        
        # Join with Brazilian decimal separator
        return f'{integer_part},{decimal_part}'
        
    def get_old_price(self):
        value = self.old_price
        return self.format_brazilian_decimal(value)
    
    def get_new_price(self):
        value = self.new_price
        return self.format_brazilian_decimal(value)
    
    def installment_price(self):
        value = round(self.new_price / 10, 2)
        return self.format_brazilian_decimal(value).split(',')
    
    def percentage_discount(self):
        value = round(100 - (self.new_price / self.old_price * 100), 2) 
        return self.format_brazilian_decimal(value) + '%'
    
    def fees(self):
        value =  round(self.new_price / 10 * 12, 2)
        return self.format_brazilian_decimal(value)

    def get_absolute_url(self):
        if not self.is_published:
            return reverse("tabloide:index")
        return reverse("tabloide:product", args=(self.slug,))
    
    def __str__(self):
        return self.name
    
    
    def clean(self):
        if not self._state.adding and self.pk != self.__original_pk:
            if not self.pk > 989999:
                raise ValidationError({'Código': 'O valor do Código não pode ser alterado após a criação.'})
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_pk = self.pk
        return super().__init__(*args, **kwargs)


    
    def save(self, *args, **kwargs):
        

        if not self.slug:
            self.slug = slygify_new(self.name, 5)


        if not self.pk or self.pk == 0:
            self.pk = get_auto_pk()

        self.clean()
        if not self.cover:
            self.cover = scrape_product(self.vitrine_link).get('img')
        
        self.text_link = self.format_to_link()


        if self.combo and self.combo.strip() and self.combo.lower()!= 'nan':
            product_ids = [pk.strip() for pk in self.combo.split(',')]
            product_ids = [int(pk) for pk in product_ids if pk.isdigit()]
            product_ids = list(set(product_ids))
            product_ids = [pk for pk in product_ids if pk != self.pk]

            # if not self._state.adding:

            if not self._state.adding:
                for f in product_ids:
                    try:
                        product = Product.objects.using(self._state.db).get(pk=int(f))
                        self.related_products.add(product,
                        through_defaults={'price': product.old_price,'total_price':product.old_price}
                        )
                    except Product.DoesNotExist:
                        continue

            combo_ativo = self.related_products.all().values_list('pk', flat=True)
            for i in combo_ativo:
                if i not in product_ids:
                    self.related_products.remove(i)
        else:
            self.related_products.clear()
            self.combo = None
        super_save = super().save(*args, **kwargs)
        return super_save
    
class ProductPromo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    promotion = models.ForeignKey(Promotion,on_delete=models.CASCADE)
    end_date = models.DateField(blank=True, null=True)
    price = models.FloatField(blank=True, null=True)   
    
    def save(self, *args, **kwargs):
        if self.promotion:
            self.end_date = self.promotion.end_date
            self.price = self.product.new_price
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.product} - {self.promotion}'

class Page(models.Model):
    class Meta:
        verbose_name = 'Page'
        verbose_name_plural = 'Pages'

    title = models.CharField(max_length=50)
    slug = models.SlugField(
        max_length=50,
        unique=True,
        default="",
        blank=True,
        null=False,
    )
    is_published = models.BooleanField(
        default=True,
        help_text='Esse campo deve ser marcado para tornar a página publica',
        
    )
    content = models.TextField()
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slygify_new(self.title, 5)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
class Store(models.Model):
    class Meta:
        verbose_name = 'Loja'
        verbose_name_plural = 'Lojas'

    number_store = models.IntegerField(verbose_name='Numero da Loja', primary_key=True, unique=True, editable=True)
    city = models.CharField(max_length=50, verbose_name='Nome da Loja')
    city_slug = models.SlugField(
        max_length=50,
        default="",
        blank=True,
        null=False,
    )
    adress = models.CharField(max_length=150, verbose_name='Endereço')
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    phone_number = models.CharField(verbose_name='WhatsApp', max_length=20, blank=True, null=True, default='')
    text = models.TextField(max_length=255, verbose_name='Mensagem WhatsApp', blank=True, null=True, default='Estou interessado no produto: ')
    store_manager = models.CharField(max_length=100, verbose_name='Gerente')
    text_link = models.TextField(max_length=255, default='', null=True, blank=True)
    
    def geocode_city(self):
        try:
            geolocator = Nominatim(user_agent="store_locator")
            location = geolocator.geocode(self.adress)
            if location:
                self.latitude = location.latitude
                self.longitude = location.longitude
        except GeocoderUnavailable:
            print("Geocoder service is unavailable.")
            pass
    
    def whatsapp(self):
        number = f'55{str(self.phone_number)}'
        text = self.text
        
        link = f"https://wa.me/{number}?text={text.replace(' ', '%20')}"
        return link
    
    def save(self, *args, **kwargs):
        
        if not self.latitude or not self.longitude:
            self.geocode_city()
        
        self.text_link = self.whatsapp()
        
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.city
    
class CampaignClick(models.Model):
    class Meta:
        verbose_name = 'Contador de Acessos'
        verbose_name_plural = 'Contadores de Acessos'
        indexes = [
            models.Index(fields=['promotion', 'click_at_date']),
            models.Index(fields=['city']),
            models.Index(fields=['product']),
        ]
        permissions = [
            ("can_view_all_cities", "Can view campaign clicks for all cities"),
        ]
        
    ip = models.GenericIPAddressField()
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    city = models.ForeignKey(Store, on_delete=models.CASCADE)    
    click_at_date = models.DateTimeField(auto_now_add=True)
    price_at_click = models.DecimalField(max_digits=10, decimal_places=2, default=0)
        
    def __str__(self):
        return f'{self.product.name}'
    
class ProductCombo(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='combos_as_main',  # Relacionamento onde este produto é o principal
        verbose_name='Produto Principal'
    )
    related_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='combos_as_related',  # Relacionamento onde este produto é o relacionado
        verbose_name='Produto Relacionado'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    multi = models.IntegerField(default=1, verbose_name='Quantidade')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0) 

    class Meta:
        verbose_name = 'Combo de Produto'
        verbose_name_plural = 'Combos de Produtos'
        unique_together = ('product', 'related_product')  # Evita duplicação de combos
        
    def save(self, *args, **kwargs):

        self.total_price = self.price * self.multi
   
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.product} - {self.price}'
    
    
    
    
    

