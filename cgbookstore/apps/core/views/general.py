# views/general.py
from django.shortcuts import render
from django.contrib import messages

def index(request):
    """
    View para a página inicial
    """
    try:
        context = {
            'livros_destaque': [],
            'livros_mais_vendidos': [],
        }
        return render(request, 'core/home.html', context)
    except Exception as e:
        messages.error(request, 'Ocorreu um erro ao carregar a página inicial.')
        return render(request, 'core/home.html', {
            'livros_destaque': [],
            'livros_mais_vendidos': [],
        })

def register(request):
    return render(request, 'core/register.html')

def sobre(request):
    return render(request, 'core/sobre.html')

def contato(request):
    return render(request, 'core/contato.html')

def politica_privacidade(request):
    return render(request, 'core/politica_privacidade.html')

def termos_uso(request):
    return render(request, 'core/termos_uso.html')