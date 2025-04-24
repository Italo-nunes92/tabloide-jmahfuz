from django.contrib import admin
from tabloide.models import Tag, Category, Page, Product, Store, Promotion, CampaignClick, ProductPromo, ProductCombo
from tabloide.modelss.profile import Profile
from django_summernote.admin import SummernoteModelAdmin
from django.urls import reverse
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# Register your models here.




@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = 'id', 'name', 'slug',
    list_display_links = 'name',
    search_fields = 'id', 'name', 'slug',
    list_per_page = 10
    ordering = '-id',
    prepopulated_fields = {
        'slug': ('name',)
    }
    
class ProductComboInline(admin.TabularInline):
    model = ProductCombo
    fk_name = 'product'  # Define o campo de relacionamento
    extra = 0  # Número de combos vazios exibidos por padrão
    readonly_fields =  'related_product','price', 'total_price' ,
    search_fields = 'product', 'product__pk',
    
    def has_add_permission(self, request, obj =...):
        return False
    def has_delete_permission(self, request, obj =...):
        return False
    

    
    

class ProductPromoAdmin(admin.TabularInline):
    model = ProductPromo
    extra = 1
    readonly_fields = 'end_date', 'price',
    autocomplete_fields = ['product']
    

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = 'id', 'name', 'slug',
    list_display_links = 'name',
    search_fields = 'id', 'name', 'slug',
    list_per_page = 10
    ordering = '-id',
    prepopulated_fields = {
        'slug': ('name',)
    }
    actions = 'link'
    

@admin.register(Page)
class PageAdmin(SummernoteModelAdmin):
    summernote_fields = 'content',
    list_display = 'id', 'title', 'slug', 'is_published',
    list_display_links = 'title',
    search_fields = 'id', 'title', 'slug', 'content',
    list_per_page = 50
    list_filter = 'is_published',
    list_editable = 'is_published',
    ordering = '-id',
    prepopulated_fields = {
        'slug': ('title',)
    }
    

@admin.register(Product)
class ProductAdmin(SummernoteModelAdmin):
    summernote_fields = 'content',
    list_display = 'pk', 'name', 'new_price', 'is_published', 'display_promotions',
    list_display_links = 'pk','name',
    search_fields = 'pk', 'name',
    list_per_page = 50
    list_filter = 'is_published', 'category', 'promotions',
    list_editable = 'is_published', 
    prepopulated_fields = {
        'slug': ('name',)
    }
    readonly_fields = 'created_at', 'updated_at','updated_by','created_by','link', 
    autocomplete_fields = 'tags', 'category', 'promotions', 'related_products',
    
    hidden_fields = 'text_link',
    
    inlines = ProductPromoAdmin, ProductComboInline

    actions = ['clear_promotions'] + [
        f'add_promotion_{promotion.pk}' for promotion in Promotion.objects.all()
    ]

    def clear_promotions(self, request, queryset):
        """Remove todas as promoções dos produtos selecionados."""
        ProductPromo.objects.filter(product__in=queryset).delete()
        self.message_user(request, _("Promoções removidas dos produtos selecionados."))
    clear_promotions.short_description = _("Remover todas as promoções dos produtos selecionados")

    # Gerar dinamicamente ações para cada promoção existente
    def get_actions(self, request):
        actions = super().get_actions(request)
        for promotion in Promotion.objects.all():
            action_name = f'add_promotion_{promotion.pk}'

            def make_action(promotion):
                def action(self, request, queryset):
                    for product in queryset:
                        ProductPromo.objects.get_or_create(product=product, promotion=promotion)
                    self.message_user(
                        request,
                        _("Promoção '%s' adicionada aos produtos selecionados.") % promotion.name
                    )
                action.short_description = _("Adicionar promoção: %s") % promotion.name
                return action

            actions[action_name] = (make_action(promotion), action_name, make_action(promotion).short_description)
        return actions
    
    def get_search_results(self, request, queryset, search_term):
        if search_term:
            pks = search_term.split()  # Split by whitespace
            if all(pk.isdigit() for pk in pks):
                return queryset.filter(pk__in=pks), True
        return super().get_search_results(request, queryset, search_term)

    def display_promotions(self, obj):
        return ", ".join([promotion.name for promotion in obj.promotions.all()])
    display_promotions.short_description = "Promoções"
    
    
    def link(self, obj):
        if not obj.pk:
            return '-'
        

        url_do_post = obj.get_absolute_url()
        link = mark_safe(f'<a href="{url_do_post}" target="_blank">{obj.title}</a>')
        return link
 
    def save_model(self, request, obj, form, change):

        if not obj.codigo and request.POST.get('codigo') != '':
            obj.codigo = request.POST.get('codigo')
        
        if change:
            obj.updated_by = request.user
        else:
            obj.created_by = request.user
        


        obj.save()
        
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = 'number_store', 'city', 'phone_number','store_manager', 'latitude', 'longitude', 'adress',
    fields = ('number_store', 'city','city_slug', 'phone_number','store_manager','latitude', 'longitude', 'adress')
    list_display_links = 'city',
    search_fields = 'number_store', 'city', 'phone_number','store_manager',
    list_per_page = 40
    ordering = 'pk',
    readonly_fields = 'text_link',
    
@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = 'pk','name', 'start_date', 'end_date', 'order_promo', 
    list_editable = 'end_date', 'order_promo',
    list_display_links = 'name',
    search_fields = 'name', 'pk',
    list_per_page = 40
    ordering = 'pk',
    readonly_fields = 'pk',
    prepopulated_fields = {
        'slug': ('name',)
        }
    inlines = ProductPromoAdmin,
    

    
@admin.register(CampaignClick)
class CLickAdmin(admin.ModelAdmin):
    list_display = 'ip','city', 'promotion', 'product', 'click_at_date', 'price_at_click',
    list_display_links = 'city',
    list_per_page = 40
    ordering = 'click_at_date',
    list_filter = 'promotion', 'product', 'click_at_date', 'city', 
    readonly_fields = 'ip','city', 'promotion', 'product', 'click_at_date', 'price_at_click',
    search_fields = 'city__city', 'promotion__name', 'product__name', 
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj = ...):
        return False
    



@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = 'user',
    autocomplete_fields = 'allowed_cities',
    
