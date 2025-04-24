from django.urls import reverse, reverse_lazy
from django.conf import settings
from django.shortcuts import redirect, render
from django.db.models import Q, Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse, HttpResponseBadRequest, Http404 , HttpResponse
from django.views.generic import ListView, DetailView, FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth import authenticate, login
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from utils.scraper import scrape_product
from utils.export_excel import export_as_excel
from utils.log_erros import erro_log
from utils.rules import get_auto_pk
from tabloide.models import Product, Store, CampaignClick, Promotion
from tabloide.form import StoreForm, CampaignClickFilterForm, LoginForm
from datetime import datetime , timedelta
from geopy.distance import geodesic

from .serializers import ProductSerializer
import pytz

SAO_PAULO_TZ = pytz.timezone('America/Sao_Paulo')

PER_PAGE = 12


def my_view(request):
    context = {
        'version': settings.STATIC_VERSION,  # Defina STATIC_VERSION no settings.py
    }
    return render(request, 'tabloide/pages/index.html', context)


class SelecionarCidadeView(FormView):
    template_name = 'tabloide/pages/index.html'
    form_class = StoreForm
    
    def dispatch(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        print(slug)
        
        if slug:
            try:
                city = Store.objects.get(city_slug=slug)
                self.request.session['cidade_selecionada'] = city.pk
                self.request.session['number'] = city.text_link
                self.request.session['city'] = city.pk
                self.initial = {'city': city.city}
            except Store.DoesNotExist:
                return redirect(reverse('tabloide:index'))
        else:
            self.request.session['city'] = None
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug')
        city = Store.objects.filter(city_slug=slug).first() if slug else ''
        
            
        context.update(
            {
                'page_title': 'Home | ',
                'city_slug': city
            }
        )

        if city:
            context['promocoes'] = Promotion.objects.filter(
                start_date__lte=datetime.now(SAO_PAULO_TZ),
                end_date__gte=datetime.now(SAO_PAULO_TZ)
            ).order_by('order_promo')
            for prom in context['promocoes']:
                prom.detalhe_url = reverse('tabloide:tabloide', kwargs={'pk': prom.id})
        return context
        
    def get_success_url(self):
        return reverse('tabloide:promotions')

class SetCidadeSessionView(View):

    def post(self, request):
        cidade_id = request.POST.get('cidade_id')
        if cidade_id:
            request.session['cidade_selecionada'] = cidade_id
            city = Store.objects.get(city=cidade_id)
            self.request.session['number'] = city.text_link
            self.request.session['city'] = city.pk
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error'}, status=400)
    
class PromotionView(ListView):
    model = Promotion
    template_name = 'tabloide/partials/_promo-card.html'
    context_object_name = 'promocoes'
    
    def get(self, request,  *args, **kwargs):
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponseBadRequest('Requisição inválida')
        

        supers = super().get(request, *args, **kwargs)

        return supers
    
    def get_queryset(self):
        qs = super().get_queryset()
        now = datetime.now(SAO_PAULO_TZ)
        qs = qs.filter(
            Q(start_date__lte=now) &
            Q(end_date__gte=now)
        ).order_by('order_promo')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        for prom in context['promocoes']:
            prom.detalhe_url = reverse('tabloide:tabloide', kwargs={'pk': prom.id})
        context.update(
            {  
                'page_title': 'Promoções | ',
            }
        )
        return context
    
class ProductListView(ListView):
    template_name = 'tabloide/pages/tabloide.html'
    paginate_by = PER_PAGE
    model = Product
    
    def get(self, request, *args, **kwargs):
        
        self.request.session['promo'] = self.kwargs.get('pk')
        return super().get(request, *args, **kwargs)
    
  
    
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(
            promotions__id=self.kwargs.get('pk'),
            is_published=True)
        validade = Promotion.objects.get(id=self.kwargs.get('pk')).end_date
        now = datetime.now(SAO_PAULO_TZ).date()
        if now > validade :
            return qs.none()
        return qs    
    
    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        number = self.request.session.get('number', 0)
        promo = Promotion.objects.get(id=self.request.session.get('promo',0))
   
        context.update(
            {
                'page_title': 'Tabloide | ',
                'whatsapp': number,
                'promo': promo,
                
            }
        )
        return context    

class TagListView(ProductListView):
    allow_empty = False
    queryset = Product.objects.filter(is_published=True)
    
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(tags__slug=self.kwargs.get('slug'))
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_title = f'{self.object_list[0].tags.first().name} | '
        context.update(
            {
                'page_title': page_title,
            }
        )        
        return context

class SearchListView(ProductListView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._search_value = ''

        
    def setup(self, request, *args, **kwargs):
        self._search_value = request.GET.get('search','').strip() 
        return super().setup(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(
            Q(name__icontains=self._search_value) |
            Q(excerpt__icontains=self._search_value)
        )[0:PER_PAGE]
        
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        page_title = f'{self._search_value[:30]} - Search | '
        context.update(
            {
                'page_title': page_title,
                'search_value': self._search_value,
            }
        )        
        return context

    def get(self, request, *args, **kwargs):
        if self._search_value == '':
            return redirect(f'/tabloide/{self.request.session["promo"]}')
        
        return super().get(request, *args, **kwargs)
    
class CategoryPostView(ProductListView):
    allow_empty = False
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(category__slug=self.kwargs.get('slug'))
                
        return qs
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_title = f'{self.object_list[0].category.name} | '
        context.update(
            {
                'page_title': page_title,
            }
        )        
        return context

class ProductView(DetailView):
    model = Product
    template_name = 'tabloide/pages/product.html'
    context_object_name = 'product'
    
    def get_context_data(self, **kwargs):
        promo = self.request.session.get('promo')
        ctx = super().get_context_data(**kwargs)
        product = self.get_object()
        page_title = f'{product.name} | '
        number = self.request.session.get('number', 0)
        city = self.request.session.get('city', 0)
        promo = Promotion.objects.get(id=self.request.session.get('promo'))
        
        ctx.update(
            {
                'page_title': page_title,
                'product_values': scrape_product(product.vitrine_link),
                'whatsapp': number,
                'city': city,
                'codigo': product.pk,
                'back_url': reverse('tabloide:tabloide',kwargs={'pk': promo.pk}),
                'promo': promo,
            }
        )
        return ctx
    
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)
    
class NearestCityView(View):
    def post(self, request, *args, **kwargs):
        try:
            lat = float(request.POST.get('latitude'))
            lon = float(request.POST.get('longitude'))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Coordenadas inválidas'}, status=400)
        
        stores = Store.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        center = Store.objects.get(pk=3)
        
        if not stores.exists():
            return JsonResponse({'error': 'Nenhuma loja cadastrada'}, status=404)

        nearest_store = min(
            stores,
            key=lambda store: geodesic((lat, lon), (store.latitude, store.longitude)).km
        )

        if self.request.session.get('city') != None:
            nearest_store = None
        

        return JsonResponse({'cidade_id': nearest_store.city})

class WhatsAppClickView(ProductView):
    
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            context = self.get_context_data(object=self.object)
            ip = self.get_client_ip(self.request)
            erro_log(str(ip))
            city = self.request.session.get('city', '')
            promo = self.request.session.get('promo', '')
            product_pk = self.object.pk
            
            # Verificar se os valores necessários existem
            if not city or not promo:
                # Redirecionar para uma página segura ou mostrar mensagem de erro
                return redirect('tabloide:index')
                
            date = datetime.now(SAO_PAULO_TZ) - timedelta(days=1)
            value = CampaignClick.objects.filter(
                ip=ip, city=city, product=product_pk, 
                click_at_date__gte=date, promotion=promo
            ).exists()
    
            if not value:
                try:
                    store = Store.objects.get(pk=city)
                    promotion = self.object.promotions.get(pk=promo)
                    
                    CampaignClick.objects.create(
                        ip=ip,
                        city=store,
                        product=self.object,
                        price_at_click=self.object.new_price,
                        promotion=promotion,
                    )
                    erro_log(f"Deu certo")
                except (Store.DoesNotExist, Promotion.DoesNotExist) as e:
                    # Log do erro
                    erro_log(f"Erro ao criar CampaignClick: {e}")
                    # Continuar sem criar o registro
                    pass
                   
            erro_log(f"Deu certo")
            return self.render_to_response(context)
        except Exception as e:
            # Log do erro para depuração
            erro_log(f"Erro na WhatsAppClickView: {e}")
            # Redirecionar para uma página segura
            return redirect('tabloide:index')

    def render_to_response(self, context, **response_kwargs):
        whatsapp = context['whatsapp']
        text_link = self.object.text_link
        if self.object.combo:
            text_link += f'%20({self.object.combo.replace(",", "-")})'
        else:
            text_link += f'%20({self.object.pk})'
        return redirect(whatsapp+text_link)
  
class LoginView(LoginView):
    template_name = 'tabloide/login.html'
    form_class = LoginForm
    success_url = 'tabloide:campaign_clicks'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)
  
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(self.success_url)
            
        return redirect('tabloide:login')
 
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'tabloide/change_password.html'
    success_url = reverse_lazy('tabloide:campaign_clicks')
    
class CampaignClickListView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'tabloide/campaignclick_list.html'
    permission_required = 'tabloide.view_campaignclick'  # defina a permissão criada
    form_class = CampaignClickFilterForm
    login_url = 'tabloide:login'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['data'] = self.request.GET
        kwargs['user'] = self.request.user
        return kwargs
    


    def get(self, request, *args, **kwargs):
        # Se houver query params, fazemos o filtro
        if request.GET:
            form = self.get_form_class()(request.GET, user=request.user)
        else:
            form = self.get_form_class()(user=request.user)
        
        qs = CampaignClick.objects.all()
        if form.is_valid():
            promotion = form.cleaned_data.get('promotion')
            codigo = form.cleaned_data.get('codigo').strip()
            city = form.cleaned_data.get('city')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            options = form.cleaned_data.get('options')
            ordem = form.cleaned_data.get('ordem')
            
            
            if start_date:
                qs = qs.filter(click_at_date__date__gte=start_date)
            if end_date:
                end_date = end_date + timedelta(days=1)
                qs = qs.filter(click_at_date__date__lte=end_date)
            if promotion:
                qs = qs.filter(promotion=promotion)
            if codigo:
                qs = qs.filter(product_id=codigo)
            if city:
                qs = qs.filter(city=city).order_by('city')
            if not city and not request.user.has_perm('tabloide.can_view_all_cities'):
                qs = qs.filter(city__in=request.user.profile.allowed_cities.all())
                
            stats = {}
            
            
            if options == '1':
                colunas = ['Cidade','Nº Loja','Código', 'Produto', 'Promoção','Clicks']
                product_detail = qs.annotate(
                    ).values(
                        'promotion', 
                        'city', 
                        'product',
                    ).annotate(
                        click_count=Count('id')
                    ).order_by('city','promotion')
                    
                for entry in product_detail:
                    city = Store.objects.get(pk=entry['city']).city
                    number = Store.objects.get(pk=entry['city']).number_store

                    if city not in stats:
                        stats[city] = []
                    
                    stats[city].append({
                        'number': f'{number:02}',
                        'cod': entry['product'],
                        'product': Product.objects.get(pk=entry['product']).name,
                        'promotion': Promotion.objects.get(pk=entry['promotion']).name,
                        'count': entry['click_count'],
                    })
                    
                    
                    
            if options == '2':
                colunas = ['Cidade','Nº Loja','Código', 'Produto','Clicks', 'Data', 'Promoção', 'Preço']
                product_detail = qs.annotate(
                        date=TruncDate('click_at_date')
                    ).values(
                        'click_at_date', 
                        'promotion', 
                        'city', 
                        'product',
                        'price_at_click'
                    ).annotate(
                        click_count=Count('id')
                    ).order_by('city','click_at_date', 'promotion')
                    
                for entry in product_detail:
                    city = Store.objects.get(pk=entry['city']).city
                    number = Store.objects.get(pk=entry['city']).number_store

                    if city not in stats:
                        stats[city] = []
                    
                    stats[city].append({
                        'number': f'{number:02}',
                        'cod': entry['product'],
                        'product': Product.objects.get(pk=entry['product']).name,
                        'count': entry['click_count'],
                        'date': (entry['click_at_date'] - timedelta(hours=3)).strftime('%d/%m/%Y %H:%M:%S'),
                        'promotion': Promotion.objects.get(pk=entry['promotion']).name,
                        'price':entry['price_at_click']
                    })
                    
            if ordem == '1':
                data = stats
            elif ordem == '2':
                data = {}
                for key, value in sorted(stats.items()):
                    data[key] = value

        
            

        # Se houver ação de exportação, processa a exportação
        export = request.GET.get('export')
        if export == 'excel':
            if not self.request.user.has_perm('tabloide.can_view_all_cities'):
                qs = qs.filter(city__in=request.user.profile.allowed_cities.all())
            return export_as_excel(data, colunas)
        elif export == 'pdf':
            return self.export_as_pdf(product_detail)
        
        if len(self.request.get_full_path().split('?')) == 1:
            return render(request, self.template_name, {'form': form, 'object_list': ''})
        
        
        
        
        

            
        return render(request, self.template_name, {'form': form, 'object_list': data})
    
   
        
    def export_as_pdf(self, qs):
        # Implementação exemplo para PDF. Aqui é recomendado renderizar um template HTML e converter para PDF.
        # Para isso, bibliotecas como xhtml2pdf podem ser utilizadas.
        response = HttpResponse("PDF export not implemented", content_type='text/plain')
        return response
    
    
    
#API REST para atualizar os preços:

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_or_create_products(request):
    data = request.data
    results = []
    tags = []

    if isinstance(data, list):
        for product_data in data:
            tags_bool = False
            tags = []
            print(product_data)
            if 'tags' in product_data.keys():
                tags_bool = True
                tags = product_data.pop('tags')
            if not 'pk' in product_data.keys() or product_data['pk'] == '':
                try:
                    product = Product.objects.get(name=product_data['name'])
                    product_data['pk'] = product.pk
                    products_related = product.related_products.all()
                    for i in products_related:
                        tags.append(i.tags.all().first().pk)
                        product_data['category'] = i.category_id
                    tags_bool = True
                except Product.DoesNotExist:
                    combo = product_data['combo'].strip(',').strip().split(',')
                    for i in combo:
                        product_combo = Product.objects.get(pk=i)
                        tags.append(product_combo.tags.all().first().pk)
                        product_data['category'] = product_combo.category_id
                    product_data['pk'] = get_auto_pk()
                    tags_bool = True
                
                serializer = ProductSerializer(data=product_data)
            else:
                serializer = ProductSerializer(data=product_data)

            if serializer.is_valid():
                product, created = Product.objects.update_or_create(
                    pk=product_data.get('pk'),
                    defaults=serializer.validated_data
                )
                if tags_bool: product.tags.set(tags)
                results.append({
                    'pk': product.pk,
                    'created': created,
                    'status': 'success'
                })
                
            else:
                # Capturar todas as exceções e registrar detalhes
                results.append({
                    'pk': product_data.get('pk'),
                    'created': False,
                    'status': 'error',
                })

        return Response(results, status=status.HTTP_200_OK)
    
    else:
        tags_bool = False
        tags = []
        if 'tags' in data.keys():
            tags = data.pop('tags')
            tags_bool = True
        if not data.get('pk') or data.get('pk') == 0:
            try:
                product = Product.objects.get(name=data['name'])
                data['pk'] = product.pk
                products_related = product.related_products.all()
                for i in products_related:
                    tags.append(i.tags.all().first().pk)
                    data['category'] = i.category_id
                tags_bool = True
            except Product.DoesNotExist:
                combo = data['combo'].strip(',').strip().split(',')
                for i in combo:
                    product_combo = Product.objects.get(pk=i)
                    tags.append(product_combo.tags.all().first().pk)
                    data['category'] = product_combo.category_id
                data['pk'] = get_auto_pk()
                tags_bool = True
            
            serializer = ProductSerializer(data=data)
        else:
            serializer = ProductSerializer(data=data)
        # Handle single product
        if serializer.is_valid():
            product, created = Product.objects.update_or_create(
                pk=data.get('pk'),
                defaults=serializer.validated_data
            )
            if tags_bool: product.tags.set(tags)
            
            return Response({
                'pk': product.pk,
                'created': created,
                'status': 'success'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'pk': data.get('pk'),
                'created': False,
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

  
   
