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
                    # Obter recomendações mistas (locais + externas)
                    engine = RecommendationEngine()
                    mixed_recommendations = engine.get_mixed_recommendations(self.request.user, limit=12)

                    # Adiciona recomendações ao contexto
                    context['external_recommendations'] = mixed_recommendations['external']
                    context['local_recommendations'] = mixed_recommendations['local']
                    context['has_mixed_recommendations'] = mixed_recommendations['has_external'] or bool(
                        mixed_recommendations['local'])

                    logger.info(f'Recomendações mistas geradas para usuário {self.request.user.username}')

                    # Adiciona recomendações locais às seções tradicionais
                    if mixed_recommendations['local']:
                        processed_sections.append({
                            'titulo': 'Recomendados para Você',
                            'tipo': 'shelf',
                            'id': 'recomendados',
                            'livros': mixed_recommendations['local']
                        })

                except Exception as e:
                    logger.error(f'Erro ao gerar recomendações mistas: {str(e)}')
                    # Fallback para recomendações tradicionais
                    try:
                        recommended_books = engine.get_recommendations(self.request.user)[:12]
                        if recommended_books:
                            processed_sections.append({
                                'titulo': 'Recomendados para Você',
                                'tipo': 'shelf',
                                'id': 'recomendados',
                                'livros': recommended_books
                            })
                            logger.info(f'Recomendações tradicionais geradas para usuário {self.request.user.username}')
                    except Exception as e2:
                        logger.error(f'Erro ao gerar recomendações tradicionais: {str(e2)}')

            # Busca tipos de prateleiras padrão
            default_shelf_types = DefaultShelfType.objects.filter(ativo=True).order_by('ordem')

            for shelf_type in default_shelf_types:
                try:
                    # Método 1: Tenta usar o método get_livros
                    livros = shelf_type.get_livros()

                    # Se não encontrou livros, tenta método alternativo
                    if not livros.exists():
                        # Método 2: Tenta filtro direto por tipo_shelf_especial
                        livros = Book.objects.filter(tipo_shelf_especial=shelf_type.identificador).order_by(
                            'ordem_exibicao')
                        logger.info(
                            f"Tentativa direta por tipo_shelf_especial={shelf_type.identificador}: {livros.count()} livros")

                        # Se ainda não encontrou, tenta outros campos
                        if not livros.exists():
                            # Método 3: Tenta campos booleanos para tipos especiais
                            if shelf_type.identificador == 'ebooks':
                                # Adiciona 'ebooks' como fallback final
                                livros = Book.objects.filter(e_lancamento=True)[
                                         :5]  # Usa alguns livros para mostrar algo
                                logger.info("Usando livros de lançamento como fallback para ebooks")

                            elif shelf_type.identificador == 'mais_vendidos':
                                livros = Book.objects.all().order_by('-quantidade_vendida')[:12]
                                logger.info("Usando livros ordenados por vendas para mais_vendidos")

                            elif shelf_type.identificador == 'destaques':
                                livros = Book.objects.filter(e_destaque=True)
                                logger.info("Usando livros de destaque")

                            # Adicione outros tipos específicos aqui se necessário

                    # Limita a quantidade de livros
                    livros = livros[:shelf_type.max_livros if hasattr(shelf_type, 'max_livros') else 12]

                    # Se encontrou livros, adiciona à lista de seções
                    if livros.exists():
                        processed_sections.append({
                            'id': shelf_type.identificador,
                            'titulo': shelf_type.nome,
                            'tipo': 'shelf',
                            'livros': livros
                        })
                        logger.info(f'Prateleira padrão adicionada: {shelf_type.nome} com {livros.count()} livros')
                    else:
                        logger.warning(f'Nenhum livro encontrado para prateleira: {shelf_type.nome}')

                except Exception as e:
                    logger.error(f'Erro ao processar prateleira {shelf_type.nome}: {str(e)}')
                    continue

            # Busca seções customizadas do admin
            admin_sections = HomeSection.objects.filter(ativo=True).prefetch_related(
                'book_shelf', 'book_shelf__shelf_type', 'book_shelf__livros',
                'video_section', 'video_section__videos',
                'custom_section',  # Adiciona prefetch para custom_section
                'author_section'  # Adiciona prefetch para author_section
            ).order_by('ordem')

            for section in admin_sections:
                try:
                    section_data = {
                        'titulo': section.titulo,
                        'subtitulo': getattr(section, 'subtitulo', None),
                        # Usa getattr para verificar se o atributo existe
                        'tipo': section.tipo,
                        'css_class': section.css_class,
                        'id': f'section-{section.id}',
                        'botao_texto': getattr(section, 'botao_texto', None),  # Também verificando botao_texto
                        'botao_url': getattr(section, 'botao_url', None)  # Também verificando botao_url
                    }

                    # Processa seção baseado no tipo
                    if section.tipo == 'shelf':
                        try:
                            # Verifica se a seção tem uma prateleira associada
                            if hasattr(section, 'book_shelf'):
                                book_shelf = section.book_shelf

                                # Verifica se existe tipo personalizado
                                if book_shelf.shelf_type:
                                    # Usa o identificador do tipo personalizado
                                    section_data['id'] = book_shelf.shelf_type.identificador

                                # Obtém livros conforme configuração
                                if book_shelf.livros.exists():
                                    # Se já tem livros adicionados manualmente
                                    livros = book_shelf.livros.all().order_by('bookshelfitem__ordem')[
                                             :book_shelf.max_livros]
                                    section_data['livros'] = livros
                                    processed_sections.append(section_data)
                                    logger.info(f'Prateleira adicionada (livros manuais): {section.titulo}')
                                else:
                                    # Se não, busca livros filtrados
                                    livros = book_shelf.get_filtered_books()[:book_shelf.max_livros]
                                    if livros.exists():
                                        section_data['livros'] = livros
                                        processed_sections.append(section_data)
                                        logger.info(f'Prateleira adicionada (filtro): {section.titulo}')
                                    else:
                                        logger.warning(f'Nenhum livro encontrado para prateleira: {section.titulo}')
                        except Exception as e:
                            logger.error(f'Erro ao processar prateleira {section.titulo}: {str(e)}')

                    elif section.tipo == 'video':
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
                        except Exception as e:
                            logger.error(f'Erro ao processar seção de vídeo {section.titulo}: {str(e)}')

                    elif section.tipo == 'ad' and hasattr(section, 'advertisement'):
                        try:
                            ad = section.advertisement
                            if ad and ad.data_inicio <= current_datetime <= ad.data_fim:
                                section_data['advertisement'] = ad
                                processed_sections.append(section_data)
                                logger.info(f'Propaganda adicionada: {section.titulo}')
                            else:
                                logger.warning(f'Propaganda fora do período de exibição: {section.titulo}')
                        except Exception as e:
                            logger.error(f'Erro ao processar propaganda {section.titulo}: {str(e)}')

                    elif section.tipo == 'link_grid':
                        try:
                            links = section.link_items.filter(ativo=True).order_by('ordem')
                            if links.exists():
                                section_data['links'] = links
                                processed_sections.append(section_data)
                                logger.info(f'Grade de links adicionada: {section.titulo} com {links.count()} links')
                            else:
                                logger.warning(f'Nenhum link ativo encontrado para seção {section.titulo}')
                        except Exception as e:
                            logger.error(f'Erro ao processar grade de links {section.titulo}: {str(e)}')

                    elif section.tipo == 'custom':
                        try:
                            # Verifica se existe uma configuração de seção personalizada
                            if hasattr(section, 'custom_section'):
                                custom_section = section.custom_section

                                if custom_section and custom_section.ativo:
                                    section_data['custom_type'] = custom_section.section_type.identificador

                                    # Definir o template com base no layout selecionado
                                    if custom_section.layout:
                                        section_data['template'] = custom_section.layout.template_path

                                    # Processar seção de eventos
                                    if custom_section.section_type.identificador == 'events':
                                        # Carregar eventos ativos ordenados
                                        events = EventItem.objects.filter(
                                            custom_section=custom_section,
                                            ativo=True
                                        ).order_by('ordem', 'data_evento')

                                        # Processamento específico para layout de destaque
                                        if custom_section.layout and custom_section.layout.identificador == 'eventos-destaque':
                                            # Separar eventos em destaque e secundários
                                            eventos_destaque = events.filter(em_destaque=True)[:1]
                                            if eventos_destaque:
                                                # Se houver evento em destaque, os secundários são os demais
                                                eventos_secundarios = events.exclude(id=eventos_destaque[0].id)[:6]
                                            else:
                                                # Se não houver evento em destaque, usar o primeiro como destaque
                                                # e os demais como secundários
                                                eventos_destaque = events[:1]
                                                eventos_secundarios = events[1:7]
                                            # Variável intermediária com tipo explícito
                                            data_dict: Dict[str, Any] = {
                                                'events': events,
                                                'eventos_destaque': eventos_destaque,
                                                'eventos_secundarios': eventos_secundarios
                                            }
                                            section_data['data'] = data_dict
                                        else:
                                            # Para os demais layouts, apenas passar os eventos
                                            section_data['data'] = {
                                                'events': events
                                            }

                                        # Só adiciona a seção se tiver eventos para mostrar
                                        if events.exists():
                                            processed_sections.append(section_data)
                                            logger.info(
                                                f'Seção de eventos adicionada: {section.titulo} com {events.count()} eventos')
                                        else:
                                            logger.warning(
                                                f'Nenhum evento ativo encontrado para seção {section.titulo}')

                                    # Adicionar processamento para outros tipos de seção personalizada no futuro
                                    # Exemplo:
                                    # elif custom_section.section_type.identificador == 'testimonials':
                                    #     ...
                                else:
                                    logger.warning(f'Seção personalizada inativa: {section.titulo}')

                            # NOVO: Verifica se existe uma seção de autores associada
                            elif hasattr(section, 'author_section'):
                                author_section = section.author_section
                                if author_section and author_section.ativo:
                                    # Obtém autores desta seção usando o método definido no modelo
                                    authors = author_section.get_autores()

                                    # Adiciona ao contexto da seção
                                    section_data['authors'] = authors
                                    section_data['author_section'] = author_section
                                    section_data['custom_type'] = 'authors'  # Identifica o tipo para template

                                    processed_sections.append(section_data)
                                    logger.info(
                                        f'Seção de autores adicionada: {section.titulo} com {len(authors)} autores')
                                else:
                                    logger.warning(f'Seção de autores inativa: {section.titulo}')
                            else:
                                # Se for tipo custom mas não tiver configuração, adiciona como genérica
                                processed_sections.append(section_data)
                                logger.warning(f'Seção do tipo "custom" sem configuração: {section.titulo}')
                        except Exception as e:
                            logger.error(f'Erro ao processar seção personalizada {section.titulo}: {str(e)}')
                            # Adiciona como seção genérica em caso de erro
                            processed_sections.append(section_data)
                    else:
                        # Para outros tipos de seção
                        processed_sections.append(section_data)
                        logger.info(f'Seção genérica adicionada: {section.titulo} (tipo: {section.tipo})')
                except Exception as e:
                    logger.error(f'Erro ao processar seção {section.titulo}: {str(e)}')
                    continue

            # NOVA IMPLEMENTAÇÃO: Ranking de Leitores
            try:
                logger.info('Iniciando cálculo do ranking de leitores')

                # Obtém usuários ativos com prateleiras
                from django.db.models import Count, Q
                from ..models.user import User

                # Obtém métricas de interação dos usuários (livros lidos)
                # Usando o modelo UserBookShelf ao invés de BookshelfItem
                from ..models.book import UserBookShelf

                # Agrega métricas por usuário
                ranking_usuarios = User.objects.filter(
                    bookshelves__shelf_type='lido'  # Filtra apenas livros marcados como lidos
                ).annotate(
                    livros_lidos=Count('bookshelves', filter=Q(bookshelves__shelf_type='lido')),
                    interacoes=Count('bookshelves')  # Total de interações (todos os tipos de prateleira)
                ).order_by('-livros_lidos', '-interacoes')[:3]  # Limita aos 3 melhores

                # Prepara dados para o template
                ranking_data = []
                for user in ranking_usuarios:
                    # Obtém avatar do perfil ou usa imagem padrão
                    try:
                        avatar_url = user.foto.url if user.foto else None
                    except:
                        avatar_url = None

                    ranking_data.append({
                        'nome': user.get_full_name() or user.username,
                        'livros_lidos': user.livros_lidos,
                        'avatar_url': avatar_url,
                        # Identifica usuários premium (para uso futuro)
                        'premium': False  # Implementar lógica futura de premium aqui
                    })

                # Adiciona ao contexto se existir ao menos um usuário no ranking
                if ranking_data:
                    context['ranking_usuarios'] = ranking_data
                    logger.info(f'Ranking de leitores calculado com sucesso: {len(ranking_data)} usuários')
                else:
                    logger.warning('Nenhum usuário encontrado para o ranking de leitores')

            except Exception as e:
                logger.error(f'Erro ao calcular ranking de leitores: {str(e)}')
                # Não adiciona o ranking ao contexto em caso de erro

            # NOVA IMPLEMENTAÇÃO: Background Personalizado
            try:
                # Buscar configurações de background
                background_section = HomeSection.objects.filter(
                    tipo='background',
                    ativo=True
                ).first()

                if background_section and hasattr(background_section, 'background_settings'):
                    background_settings = background_section.background_settings
                    if not background_settings.habilitado:
                        background_settings = None
                else:
                    background_settings = None

                # Adicionar ao contexto
                context['background_settings'] = background_settings
                logger.info('Configurações de background carregadas')
            except Exception as e:
                logger.error(f'Erro ao carregar configurações de background: {str(e)}')
                context['background_settings'] = None

            # Mantenha a atualização do contexto com o nome 'shelves' para compatibilidade
            context.update({
                'banners': banners,
                'shelves': processed_sections  # Mantém o nome 'shelves' usado no template
            })

            logger.info('Página inicial carregada com sucesso')
            return context

        except Exception as e:
            logger.error(f'Erro ao carregar página inicial: {str(e)}')
            messages.error(self.request, 'Ocorreu um erro ao carregar a página inicial.')
            context.update({
                'banners': [],
                'sections': []  # Alterado de 'shelves' para 'sections'
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
            return redirect('checkout_premium')
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