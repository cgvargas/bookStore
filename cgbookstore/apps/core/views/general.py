# views/general.py
"""
Módulo de views gerais para o projeto CGBookStore.

Contém views para:
- Página inicial
- Registro de usuário
- Página sobre
- Contato
- Política de privacidade
- Termos de uso
"""

import logging
from typing import Dict, Any, List
from django.shortcuts import redirect, render
from django.contrib import messages
from django.views.generic import CreateView, TemplateView, FormView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.query import QuerySet
from django.core.mail import send_mail
from django.template.loader import render_to_string
from ..forms import ContatoForm

from cgbookstore.config import settings
from ..forms import UserRegistrationForm
from django.utils import timezone
from ..models.banner import Banner
from ..models.book import Book
from ..models.home_content import HomeSection, EventItem
from ..recommendations.engine import RecommendationEngine
from ..models.home_content import DefaultShelfType
from ..services.google_books_service import GoogleBooksClient


# Configuração de logger para rastreamento de eventos
logger = logging.getLogger(__name__)

User = get_user_model()


class IndexView(TemplateView):
    """
    View para página inicial da CGBookStore.

    Características:
    - Carrega seções dinâmicas definidas pelo admin
    - Suporta diferentes tipos de seções (prateleiras, vídeos, anúncios)
    - Mantém recomendações personalizadas para usuários logados
    - Tratamento de erros com logs detalhados
    - Suporte a seções personalizadas com layouts dinâmicos
    """
    template_name = 'core/home.html'

    # Função modificada dentro da classe IndexView no arquivo general.py

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            logger.info('[DIAGNÓSTICO INDEX] Iniciando carregamento da página inicial.')
            current_datetime = timezone.now()

            # 1. Banners
            context['banners'] = Banner.objects.filter(
                ativo=True, data_inicio__lte=current_datetime, data_fim__gte=current_datetime
            ).order_by('ordem')
            logger.info(f"[DIAGNÓSTICO INDEX] Banners carregados: {context['banners'].count()}")

            processed_sections = []

            # 2. Recomendações (se usuário logado)
            if self.request.user.is_authenticated:
                # O seu código de recomendações já funciona bem, então vamos mantê-lo
                # ... (código para gerar 'mixed_recommendations')
                # Apenas garantimos que o resultado seja adicionado corretamente
                engine = RecommendationEngine()
                mixed_recommendations = engine.get_mixed_recommendations(self.request.user, limit=12)
                context.update({
                    'external_recommendations': mixed_recommendations.get('external'),
                    'local_recommendations': mixed_recommendations.get('local'),
                    'has_mixed_recommendations': mixed_recommendations.get('has_external') or bool(
                        mixed_recommendations.get('local'))
                })
                logger.info(f"[DIAGNÓSTICO INDEX] Recomendações mistas processadas.")

            # 3. Processamento de todas as seções da Home
            logger.info('[DIAGNÓSTICO INDEX] Iniciando busca unificada de todas as seções.')
            admin_sections = HomeSection.objects.filter(ativo=True).prefetch_related(
                'book_shelf__shelf_type', 'book_shelf__livros__autores',
                'video_section__videos', 'custom_section__section_type',
                'author_section__autores', 'advertisement', 'link_items'
            ).order_by('ordem')

            logger.info(f'[DIAGNÓSTICO INDEX] Encontradas {admin_sections.count()} seções ativas para processar.')

            for section in admin_sections:
                try:
                    section_data = {'titulo': section.titulo, 'tipo': section.tipo, 'id': f'section-{section.id}',
                                    'css_class': section.css_class}

                    # TIPO: Prateleira de Livros
                    if section.tipo == 'shelf' and hasattr(section, 'book_shelf'):
                        book_shelf = section.book_shelf
                        livros = book_shelf.livros.all() if book_shelf.livros.exists() else book_shelf.get_filtered_books()
                        if livros.exists():
                            section_data['livros'] = livros[:book_shelf.max_livros]
                            if book_shelf.shelf_type: section_data['id'] = book_shelf.shelf_type.identificador
                            processed_sections.append(section_data)
                            logger.info(f'[DIAGNÓSTICO INDEX] ✅ Seção SHELF "{section.titulo}" adicionada.')
                        else:
                            logger.warning(f'[DIAGNÓSTICO INDEX] ❌ Seção SHELF "{section.titulo}" pulada (sem livros).')

                    # TIPO: Seção de Vídeos
                    elif section.tipo == 'video' and hasattr(section, 'video_section'):
                        video_section = section.video_section
                        if video_section.ativo:
                            videos = video_section.videos.filter(ativo=True, videosectionitem__ativo=True).order_by(
                                'videosectionitem__ordem')
                            if videos.exists():
                                section_data['videos'] = videos
                                processed_sections.append(section_data)
                                logger.info(f'[DIAGNÓSTICO INDEX] ✅ Seção VIDEO "{section.titulo}" adicionada.')
                            else:
                                logger.warning(
                                    f'[DIAGNÓSTICO INDEX] ❌ Seção VIDEO "{section.titulo}" pulada (sem vídeos ativos).')

                    # TIPO: Seção Customizada (Autores, Eventos, etc.)
                    elif section.tipo == 'custom':
                        logger.info(f'[DIAGNÓSTICO INDEX] Processando seção CUSTOM: "{section.titulo}"')
                        if hasattr(section, 'author_section') and section.author_section.ativo:
                            section_data['author_section'] = section.author_section
                            section_data['authors'] = section.author_section.get_autores()
                            processed_sections.append(section_data)
                            logger.info(f'[DIAGNÓSTICO INDEX] ✅ Seção de AUTORES "{section.titulo}" adicionada.')
                        # Adicione aqui 'elif' para outros tipos de 'custom_section' se necessário
                        else:
                            logger.warning(
                                f'[DIAGNÓSTICO INDEX] ⚠️ Seção CUSTOM "{section.titulo}" sem lógica de renderização definida.')

                    # Adicione outros elif para 'ad', 'link_grid', etc.

                except Exception as e:
                    logger.error(f'[DIAGNÓSTICO INDEX] ❌ ERRO ao processar seção "{section.titulo}": {e}',
                                 exc_info=True)

            # O nome da variável de contexto deve ser 'shelves' para corresponder ao template
            context['shelves'] = processed_sections

            # 4. Ranking de Leitores (Gamificação)
            context['ranking_usuarios'] = User.objects.annotate(
                livros_lidos=Count('bookshelves', filter=Q(bookshelves__shelf_type='lido'))
            ).filter(livros_lidos__gt=0).order_by('-livros_lidos')[:3]  # Apenas os 3 primeiros para a home
            logger.info(
                f"[DIAGNÓSTICO INDEX] Ranking de leitores carregado: {context['ranking_usuarios'].count()} usuários.")

            logger.info(
                f'[DIAGNÓSTICO INDEX] RESUMO: {len(processed_sections)} seções processadas. Página carregada com sucesso.')
            return context

        except Exception as e:
            logger.error(f'[DIAGNÓSTICO INDEX] ❌ ERRO FATAL ao carregar página: {e}', exc_info=True)
            messages.error(self.request, 'Ocorreu um erro ao carregar a página inicial.')
            context.update({'banners': [], 'shelves': [], 'ranking_usuarios': []})
            return context

    def _get_shelf_books(self, shelf_type, max_books):
        """Retorna livros baseado no tipo de prateleira."""
        filters = {
            'latest': Book.objects.all().order_by('-created_at'),
            'bestsellers': Book.objects.filter(quantidade_vendida__gt=0).order_by('-quantidade_vendida'),
            'most_viewed': Book.objects.filter(quantidade_acessos__gt=0).order_by('-quantidade_acessos'),
            'featured': Book.objects.filter(e_destaque=True).order_by('ordem_exibicao'),
            'movies': Book.objects.filter(adaptado_filme=True).order_by('ordem_exibicao'),
            'manga': Book.objects.filter(e_manga=True).order_by('ordem_exibicao'),
        }

        queryset = filters.get(shelf_type, Book.objects.none())
        return queryset[:max_books]


class RegisterView(CreateView):
    """
    View para registro de novos usuários.

    Características:
    - Utiliza formulário personalizado de registro
    - Desativa usuário até verificação de email
    - Envia email de verificação
    - Tratamento de erros de registro
    """
    form_class = UserRegistrationForm
    template_name = 'core/register.html'
    success_url = reverse_lazy('index')

    def get(self, request, *args, **kwargs):
        """
        Log de acesso à página de registro.

        Args:
            request: Requisição HTTP
        """
        logger.info('Acessando página de registro')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Processa registro de novo usuário.

        Etapas:
        1. Salva usuário como inativo
        2. Envia email de verificação
        3. Adiciona mensagens de status

        Args:
            form: Formulário de registro validado

        Returns:
            HttpResponseRedirect: Redireciona para página inicial
        """
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
    """
    View para página institucional 'Sobre'.

    Renderiza template estático com informações sobre a empresa.
    """
    template_name = 'core/sobre.html'


class PlanosView(TemplateView):
    """
    View para página de planos da plataforma.

    Renderiza template estático com as opções de planos
    Freemium e Premium disponíveis.
    """
    template_name = 'core/planos.html'


class PremiumSignupView(TemplateView):
    """
    Gerencia o registro de novos usuários premium.
    Redireciona para o formulário de pagamento após o registro.
    """
    template_name = 'core/register.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['premium'] = True
        context['next'] = reverse_lazy('checkout_premium')
        return context

    def get(self, request, *args, **kwargs):
        # Se o usuário já estiver logado, redirecione direto para o checkout
        if request.user.is_authenticated:
            return redirect('core:checkout_premium')
        return super().get(request, *args, **kwargs)


class ContatoView(FormView):
    """
    View para formulário de contato.

    Características:
    - Processa formulário de contato
    - Envia emails para administração e usuário
    - Tratamento de erros de envio de email
    """
    template_name = 'core/contato.html'
    form_class = ContatoForm
    success_url = reverse_lazy('core:contato')

    def enviar_email_admin(self, dados):
        """
        Envia email para administração com detalhes do contato.

        Args:
            dados (dict): Dados do formulário de contato

        Returns:
            bool: Indica sucesso no envio de email
        """
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
        """
        Envia email de confirmação para o usuário.

        Args:
            dados (dict): Dados do formulário de contato

        Returns:
            bool: Indica sucesso no envio de email
        """
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
        """
        Processa formulário de contato válido.

        Etapas:
        1. Envia email para administração
        2. Envia email de confirmação para usuário
        3. Adiciona mensagens de status

        Args:
            form: Formulário de contato validado

        Returns:
            HttpResponse: Resposta após processamento do formulário
        """
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
    """
    View para página de Política de Privacidade.

    Renderiza template estático com política de privacidade.
    """
    template_name = 'core/politica_privacidade.html'


class TermosUsoView(TemplateView):
    """
    View para página de Termos de Uso.

    Renderiza template estático com termos de uso.
    """
    template_name = 'core/termos_uso.html'


def get_external_book_details(request, external_id):
    """
    View para buscar detalhes de um livro externo específico
    """
    try:
        # Trata IDs negativos (que são IDs temporários internos)
        if external_id.startswith('-'):
            # Tenta buscar nas recomendações armazenadas em cache
            from ..recommendations.engine import RecommendationEngine
            engine = RecommendationEngine()

            # Obtém recomendações para o usuário atual
            recommendations = engine.get_mixed_recommendations(request.user)

            # Procura o livro com o ID específico
            for book in recommendations.get('external', []):
                if book.get('id') == external_id:
                    return JsonResponse(book)

            return JsonResponse({'error': 'Livro temporário não encontrado'}, status=404)

        # Para outros IDs, usa a API do Google Books
        client = GoogleBooksClient()
        book_data = client.get_book_by_id(external_id)

        if not book_data:
            return JsonResponse({'error': 'Livro não encontrado'}, status=404)

        # Retorna os dados do livro como JSON
        return JsonResponse(book_data, encoder=DjangoJSONEncoder)

    except Exception as e:
        logger.error(f"Erro ao buscar detalhes do livro externo: {str(e)}")
        return JsonResponse({'error': 'Erro ao buscar detalhes do livro'}, status=500)


class ReaderRankingView(TemplateView):
    template_name = "core/ranking_leitores.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        leitores = User.objects.annotate(
            livros_lidos=Count('bookshelves', filter=Q(bookshelves__shelf_type='lido'))
        ).filter(livros_lidos__gt=0).order_by('-livros_lidos')[:80]

        context['leitores'] = leitores
        return context


# Salva Cookies na sessão do Django
def aceitar_cookies(request):
    request.session['cookie_consent'] = True
    return JsonResponse({'cookie_consent': True})