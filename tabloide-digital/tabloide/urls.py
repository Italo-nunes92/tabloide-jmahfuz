
from django.urls import path
from tabloide.views import ProductListView, TagListView,\
    SearchListView, ProductView, CategoryPostView, SelecionarCidadeView,\
    NearestCityView, PromotionView, SetCidadeSessionView, WhatsAppClickView, CampaignClickListView, LoginView, \
    CustomPasswordChangeView, update_or_create_products
from django.contrib.auth.views import LogoutView

app_name = 'tabloide'

urlpatterns = [
    path('', SelecionarCidadeView.as_view(), name='index'),
    path('loja/<slug:slug>', SelecionarCidadeView.as_view(), name='index'),
    path('product/<slug:slug>/', ProductView.as_view(), name='product'),
    path('<int:pk>/tag/<slug:slug>/', TagListView.as_view(), name='tag'),
    path('<int:pk>/search/:', SearchListView.as_view(), name='search'),
    path('<int:pk>/category/<slug:slug>/', CategoryPostView.as_view(), name='category'),
    path('tabloide/<int:pk>/', ProductListView.as_view() , name='tabloide'),
    path('nearest-city/', NearestCityView.as_view(), name='nearest-city'),
    path('promotions/', PromotionView.as_view(), name='promotions'),
    path('set-cidade-session/', SetCidadeSessionView.as_view(), name='set-cidade-session'),
    path('click-whatsapp/<slug:slug>/', WhatsAppClickView.as_view(), name='click-whatsapp'),
    path('campaign-clicks/', CampaignClickListView.as_view(), name='campaign_clicks'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),
    path('change-password/', CustomPasswordChangeView.as_view(), name='change_password'),
    path('api/products/', update_or_create_products, name='update_or_create_products'),

]