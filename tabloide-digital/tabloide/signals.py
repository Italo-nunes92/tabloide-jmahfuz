from django.db.models.signals import m2m_changed, post_save, pre_save, post_init
from django.dispatch import receiver
from .models import Product, ProductCombo
from django.db.models import Sum

@receiver(post_save, sender=Product)
def check_related_products(sender, instance, **kwargs):
    from django.db import transaction
    with transaction.atomic():
        products_combo = ProductCombo.objects.filter(related_product=instance)
        for i in products_combo:
            i.price = instance.old_price
            i.product.related_products.add(i.related_product)
            i.save()
        if instance.combo and not instance.related_products.all().exists():
            instance.save()
            
        if not instance.old_price:
            products_combo.first().save()
        
    

@receiver(pre_save, sender=Product)
def update_related_total(sender, instance, **kwargs):
    if instance.combo:
        price = ProductCombo.objects.filter(product=instance).aggregate(total=Sum('total_price'))['total'] or 0
        instance.old_price = price
        if instance.auto_new_price and price != 0:
            instance.new_price = rounding(price)
    



@receiver(post_save, sender=ProductCombo)
def update_related_total(sender, instance, **kwargs):
    
    pro = Product.objects.get(pk=instance.product.pk)
    prod_combo = pro.related_products.all()
    soma = 0
    for i in prod_combo:
        teste = ProductCombo.objects.filter(product=instance.product, related_product=i)
        soma = soma + teste.first().total_price
    
    instance.product.old_price = soma
    if instance.product.auto_new_price:
        instance.product.new_price = rounding(soma)
    instance.product.save(update_fields=['old_price', 'new_price'])

def rounding(value):
    value_f = float(value) /1.206
    number_s = str(value_f)
    number_s = number_s.split('.')
    if int(number_s[1]) > 94:
        number_f = float(number_s[0]) + 1
        price = number_f
        return price
    return float(value_f)
