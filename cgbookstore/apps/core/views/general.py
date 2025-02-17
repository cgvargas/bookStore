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
from ..models.home_content import HomeSection, VideoSection
from ..recommendations.engine import RecommendationEngine
from ..models.home_content import DefaultShelfType

# Configuração de logger para rastreamento de eventos
logger = logging.getLogger(__name__)


class IndexView(TemplateView):
    """
    View para página inicial da CGBookStore.

    Características:
    - Carrega seções dinâmicas definidas pelo admin
    - Suporta diferentes tipos de seções (prateleiras, vídeos, anúncios)
    - Mantém recomendações personalizadas para usuários logados
    - Tratamento de erros com logs detalhados
    """
    template_name = 'core/home.html'

    # views/general.py

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            logger.info('Iniciando carregamento da página inicial')
            current_datetime = timezone.now()

            # Busca banners ativos
            banners = Banner.objects.filter(
                ativo=True,
                data_inicio__lte=current_datetime,
                data_fim__gte=current_datetime
            ).order_by('ordem')

            # Inicializa lista de seções
            processed_sections = []

            # Adiciona recomendações personalizadas se usuário estiver logado
            if self.request.user.is_authenticated:
                try:
                    engine = RecommendationEngine()
                    recommended_books = engine.get_recommendations(self.request.user)[:12]
                    if recommended_books:
                        processed_sections.append({
                            'titulo': 'Recomendados para Você',
                            'tipo': 'shelf',
                            'id': 'recomendados',
                            'livros': recommended_books
                        })
                        logger.info(f'Recomendações geradas para usuário {self.request.user.username}')
                except Exception as e:
                    logger.error(f'Erro ao gerar recomendações: {str(e)}')

            default_shelf_types = DefaultShelfType.objects.filter(ativo=True).order_by('ordem')

            for shelf_type in default_shelf_types:
                livros = shelf_type.get_livros()[:12]  # Limita a 12 livros

                if livros.exists():
                    processed_sections.append({
                        'id': shelf_type.identificador,
                        'titulo': shelf_type.nome,
                        'tipo': 'shelf',
                        'livros': livros
                    })
                    logger.info(f'Prateleira padrão adicionada: {shelf_type.nome}')

            # Busca seções customizadas do admin
            admin_sections = HomeSection.objects.filter(ativo=True).select_related('video_section').order_by('ordem')

            for section in admin_sections:
                try:
                    section_data = {
                        'titulo': section.titulo,
                        'tipo': section.tipo,
                        'css_class': section.css_class,
                        'id': f'section-{section.id}'
                    }

                    # Processa seção baseado no tipo
                    if section.tipo == 'video':
                        try:
                            video_section = section.video_section
                            if video_section and video_section.ativo:
                                videos = video_section.videos.filter(
                                    videosectionitem__ativo=True,
                                    ativo=True
                                ).order_by('videosectionitem__ordem')

                                if videos.exists():
                                    section_data['video_section'] = video_section
                                    section_data['videos'] = videos
                                    processed_sections.append(section_data)
                                    logger.info(
                                        f'Seção de vídeos adicionada: {section.titulo} com {videos.count()} vídeos')
                                else:
                                    logger.warning(f'Nenhum vídeo ativo encontrado para seção {section.titulo}')
                            else:
                                logger.warning(f'Seção de vídeo inativa: {section.titulo}')
                        except VideoSection.DoesNotExist:
                            logger.warning(f'Nenhuma seção de vídeo associada à seção {section.titulo}')
                    else:
                        # Para outros tipos de seção
                        processed_sections.append(section_data)

                except Exception as e:
                    logger.error(f'Erro ao processar seção {section.titulo}: {str(e)}')
                    continue

            context.update({
                'banners': banners,
                'shelves': processed_sections
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
    success_url = reverse_lazy('contato')

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