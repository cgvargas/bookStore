# views/general.py
import logging
from django.shortcuts import redirect
from django.contrib import messages
from django.views.generic import CreateView, TemplateView, FormView
from django.urls import reverse_lazy

from django.core.mail import send_mail
from django.template.loader import render_to_string
from ..forms import ContatoForm

from cgbookstore.config import settings
from ..forms import UserRegistrationForm
from django.utils import timezone
from ..models.banner import Banner
from ..models.book import Book
from ..recommendations.engine import RecommendationEngine

logger = logging.getLogger(__name__)


class IndexView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            logger.info('Iniciando carregamento da página inicial')

            # Busca banners ativos
            current_datetime = timezone.now()
            banners = Banner.objects.filter(
                ativo=True,
                data_inicio__lte=current_datetime,
                data_fim__gte=current_datetime
            ).order_by('ordem')

            # Busca livros para cada seção
            lancamentos = Book.objects.filter(e_lancamento=True).order_by('ordem_exibicao')[:12]
            mais_vendidos = Book.objects.filter(quantidade_vendida__gt=0).order_by('-quantidade_vendida')[:12]
            mais_acessados = Book.objects.filter(quantidade_acessos__gt=0).order_by('-quantidade_acessos')[:12]
            destaques = Book.objects.filter(e_destaque=True).order_by('ordem_exibicao')[:12]
            adaptados_filme = Book.objects.filter(adaptado_filme=True).order_by('ordem_exibicao')[:12]
            mangas = Book.objects.filter(e_manga=True).order_by('ordem_exibicao')[:12]

            # Adicionar recomendações personalizadas se usuário estiver logado
            recommended_books = []
            if self.request.user.is_authenticated:
                try:
                    engine = RecommendationEngine()
                    recommended_books = engine.get_recommendations(self.request.user)[:12]
                    logger.info(f'Recomendações geradas para usuário {self.request.user.username}')
                except Exception as e:
                    logger.error(f'Erro ao gerar recomendações: {str(e)}')

            # Organiza as prateleiras em uma estrutura
            shelves = [
                {'id': 'recomendados', 'titulo': 'Recomendados para Você', 'livros': recommended_books},
                {'id': 'lancamentos', 'titulo': 'Lançamentos', 'livros': lancamentos},
                {'id': 'mais-vendidos', 'titulo': 'Mais Vendidos', 'livros': mais_vendidos},
                {'id': 'mais-acessados', 'titulo': 'Mais Acessados Online', 'livros': mais_acessados},
                {'id': 'destaques', 'titulo': 'Livros em Destaque', 'livros': destaques},
                {'id': 'adaptados', 'titulo': 'Adaptados para Filme/Série', 'livros': adaptados_filme},
                {'id': 'mangas', 'titulo': 'Mangás', 'livros': mangas},
            ]

            context.update({
                'banners': banners,
                'shelves': shelves
            })

            logger.info('Página inicial carregada com sucesso')
            return context

        except Exception as e:
            logger.error(f'Erro ao carregar página inicial: {str(e)}')
            messages.error(self.request, 'Ocorreu um erro ao carregar a página inicial.')
            context.update({
                'banners': [],
                'shelves': []
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


class ContatoView(FormView):
    template_name = 'core/contato.html'
    form_class = ContatoForm
    success_url = reverse_lazy('contato')

    def enviar_email_admin(self, dados):
        """Envia email para administração"""
        logger.info(f'Enviando email admin - Assunto: {dados["assunto"]}')
        try:
            mensagem = render_to_string('core/email/contato_email.html', dados)
            send_mail(
                f'Contato do Site: {dados["assunto"]}',
                mensagem,
                settings.EMAIL_HOST_USER,
                ['cg.bookstore.online@gmail.com'],
                fail_silently=False
            )
            logger.info('Email admin enviado com sucesso')
            return True
        except Exception as e:
            logger.error(f'Erro ao enviar email admin: {str(e)}')
            return False

    def enviar_email_confirmacao(self, dados):
        """Envia email de confirmação para usuário"""
        logger.info(f'Enviando confirmação para: {dados["email"]}')
        try:
            mensagem = render_to_string('core/email/contato_confirmacao.html', dados)
            send_mail(
                'Confirmação de Contato - CGBookStore',
                mensagem,
                settings.EMAIL_HOST_USER,
                [dados['email']],
                fail_silently=False
            )
            logger.info('Email de confirmação enviado com sucesso')
            return True
        except Exception as e:
            logger.error(f'Erro ao enviar confirmação: {str(e)}')
            return False

    def form_valid(self, form):
        dados = form.cleaned_data
        logger.info(f'Processando contato de: {dados["email"]}')

        # Tenta enviar ambos os emails
        admin_enviado = self.enviar_email_admin(dados)
        confirma_enviado = self.enviar_email_confirmacao(dados)

        if admin_enviado and confirma_enviado:
            messages.success(self.request, 'Mensagem enviada com sucesso! Em breve retornaremos seu contato.')
            logger.info('Processo de contato concluído com sucesso')
        else:
            if not admin_enviado:
                logger.error('Falha ao enviar para administração')
            if not confirma_enviado:
                logger.error('Falha ao enviar confirmação')
            messages.error(self.request, 'Erro ao enviar mensagem. Por favor, tente novamente.')

        return super().form_valid(form)

class PoliticaPrivacidadeView(TemplateView):
    template_name = 'core/politica_privacidade.html'

class TermosUsoView(TemplateView):
    template_name = 'core/termos_uso.html'