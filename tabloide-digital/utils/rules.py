from django.db.models import Max          
            
def get_auto_pk():
    from tabloide.models import Product
    max_pk = Product.objects.aggregate(max_pk=Max('pk'))['max_pk'] or 989999
    if max_pk < 990000:
        pk = 990000
    else:
        pk = max_pk + 1
    return pk