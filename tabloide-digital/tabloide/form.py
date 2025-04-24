from django import forms
from .models import Store, Promotion, Product, User

class StoreForm(forms.Form):
    

    city = forms.ModelChoiceField(
        queryset=Store.objects.all().values_list('city', flat=True).distinct().order_by('city'),
        empty_label="Selecione sua cidade",
        label="Cidade",
        required=True
    )
    

class CampaignClickFilterForm(forms.Form):

    
    promotion = forms.ModelChoiceField(
        queryset=Promotion.objects.all(), required=False, label="Promoção",
        empty_label="Todas as promoções"
    )
    city = forms.ModelChoiceField(
        queryset=Store.objects.all().order_by('city'), required=False, label="Cidade",
        empty_label="Todas as cidades"
    )
    
    codigo = forms.CharField(
        required=False,
        label="Codigo do Produto",
        widget=forms.TextInput(attrs={'placeholder': 'Ex: 000000'})
    )

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Data início"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Data término"
    )
    
    options = forms.ChoiceField(
        choices=[('1', 'Simples'), ('2', 'Detalhado')],
        widget=forms.RadioSelect,
        label='Opções',
        initial='1',
    )
    ordem = forms.ChoiceField(
        choices=[('1', 'Por Nº'), ('2', 'Por Nome')],
        widget=forms.RadioSelect,
        label='Ordem de apresentação',
        initial='1',
    )
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and not user.has_perm('tabloide.can_view_all_cities'):
            allowed_cities = user.profile.allowed_cities.all()
            self.fields['city'].queryset = allowed_cities
            if len(user.profile.allowed_cities.all()) == 1: self.fields['ordem'].widget = forms.HiddenInput()
                
            
    
class LoginForm(forms.Form):
    
    object = User.objects.all()

    
    username = forms.CharField(label='Usuário')
    password = forms.CharField(label='Senha', widget=forms.PasswordInput)   
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)