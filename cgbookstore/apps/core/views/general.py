# views/general.py
import logging
from django.shortcuts import redirect
from django.contrib import messages
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from ..forms import UserRegistrationForm

logger = logging.getLogger(__name__)

class IndexView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            logger.info('Iniciando carregamento da página inicial')
            context.update({
                'livros_destaque': [],
                'livros_mais_vendidos': [],
            })
            logger.info('Página inicial carregada com sucesso')
            return context
        except (ValueError, AttributeError, TypeError) as e:
            logger.error(f'Erro ao carregar página inicial: {str(e)}')
            messages.error(self.request, 'Ocorreu um erro ao carregar a página inicial.')
            context.update({
                'livros_destaque': [],
                'livros_mais_vendidos': [],
            })
            return context


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'core/register.html'
    success_url = reverse_lazy('index')

    def get(self, request, *args, **kwargs):
        logger.info('Acessando página de registro')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            logger.info('Iniciando registro de novo usuário')
            user = form.save(commit=False)
            user.is_active = False  # Usuário inativo até verificar email
            user.save()

            from .auth import send_verification_email
            if send_verification_email(self.request, user):
                messages.success(
                    self.request,
                    'Registro realizado com sucesso! Por favor, verifique seu email para ativar sua conta.'
                )
                logger.info(f'Usuário {user.username} registrado. Email de verificação enviado.')
            else:
                messages.warning(
                    self.request,
                    'Conta criada, mas houve um erro ao enviar o email de verificação. Entre em contato com o suporte.'
                )
                logger.error(f'Erro ao enviar email de verificação para {user.username}')

            return redirect('index')
        except Exception as e:
            logger.error(f'Erro no registro do usuário: {str(e)}')
            messages.error(self.request, 'Erro ao realizar registro.')
            return self.form_invalid(form)

class SobreView(TemplateView):
    template_name = 'core/sobre.html'

class ContatoView(TemplateView):
    template_name = 'core/contato.html'

class PoliticaPrivacidadeView(TemplateView):
    template_name = 'core/politica_privacidade.html'

class TermosUsoView(TemplateView):
    template_name = 'core/termos_uso.html'