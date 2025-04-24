from django.shortcuts import redirect
from django.urls import reverse, resolve, Resolver404
from tabloide.models import Store


class CidadeSelectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.session.get('cidade_selecionada') and request.path != reverse('tabloide:index'):
            return redirect('tabloide:index')
        return self.get_response(request)


class SlugCorrectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.strip("/")  # Remove as barras no início e no final do path

        # Verifica se o path não começa com "loja/" e não está vazio
        if path and not path.startswith("loja/"):
            try:
                # Tenta resolver a URL para verificar se é um path válido registrado no urls.py
                resolve(path)
            except Resolver404:
                # Se não for um path registrado, verifica se é uma slug válida no modelo Store
                store = Store.objects.filter(city_slug=path).first()
                if store:
                    # Redireciona para a URL correta com "loja/"
                    return redirect(f"/loja/{path}")

        # Continua o processamento normal se não for necessário corrigir
        return self.get_response(request)