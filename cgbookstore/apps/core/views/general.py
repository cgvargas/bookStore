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

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from ..models import EventItem, Advertisement
import logging
from django.shortcuts import redirect
from django.contrib import messages
from django.views.generic import CreateView, FormView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.middleware.csrf import get_token
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
from ..models.home_content import HomeSection, VideoItem
from ..recommendations.engine import RecommendationEngine
from ..services.google_books_service import GoogleBooksClient

logger = logging.getLogger(__name__)

User = get_user_model()


class IndexView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            print('=' * 80)
            print('[DIAGNÓSTICO INDEX] ==================== INÍCIO ====================')
            print('[DIAGNÓSTICO INDEX] IndexView.get_context_data() EXECUTADA!')
            print('[DIAGNÓSTICO INDEX] Iniciando carregamento da página inicial com estrutura final.')
            print('=' * 80)

            current_datetime = timezone.now()

            # Carregar banners
            context['banners'] = Banner.objects.filter(
                ativo=True, data_inicio__lte=current_datetime, data_fim__gte=current_datetime
            ).order_by('ordem')
            print(f'[DIAGNÓSTICO INDEX] Banners carregados: {context["banners"].count()}')

            # Recomendações para usuários autenticados
            if self.request.user.is_authenticated:
                print('[DIAGNÓSTICO INDEX] Carregando recomendações para usuário autenticado')
                engine = RecommendationEngine()
                mixed_recommendations = engine.get_mixed_recommendations(self.request.user, limit=12)
                context.update({
                    'external_recommendations': mixed_recommendations.get('external'),
                    'local_recommendations': mixed_recommendations.get('local'),
                    'has_mixed_recommendations': mixed_recommendations.get('has_external') or bool(
                        mixed_recommendations.get('local'))
                })

            processed_sections = []

            # *** INICIALIZAR background_settings FORA DO LOOP ***
            background_settings = None

            print('[DIAGNÓSTICO INDEX] Iniciando carregamento de seções...')

            all_sections = HomeSection.objects.filter(ativo=True).select_related(
                'advertisement', 'background_settings'  # *** IMPORTANTE: incluir background_settings ***
            ).prefetch_related(
                'manual_books',
                'video_section', 'video_section__videos',
                'author_section', 'author_section__autores',
                'link_items'
            ).order_by('ordem')

            print(f'[DIAGNÓSTICO INDEX] Encontradas {all_sections.count()} seções ativas para processar.')

            if all_sections.exists():
                sections_info = [f"{s.titulo} (tipo: {s.tipo}, id: {s.id})" for s in all_sections]
                print(f'[DIAGNÓSTICO INDEX] Lista completa de seções: {sections_info}')
            else:
                print('[DIAGNÓSTICO INDEX] ⚠️ NENHUMA seção ativa encontrada no banco de dados!')

            for index, section in enumerate(all_sections, 1):
                print(
                    f'[DIAGNÓSTICO INDEX] [{index}/{all_sections.count()}] Processando seção: "{section.titulo}" (tipo: {section.tipo}, id: {section.id})')

                section_data = {
                    'titulo': section.titulo,
                    'tipo': section.tipo,
                    'id': f'section-{section.id}',
                    'css_class': section.css_class,
                }

                # *** LÓGICA PARA BACKGROUND ***
                if section.tipo == 'background':
                    print(f'[DIAGNÓSTICO INDEX] └── Processando configuração de background: {section.titulo}')
                    print(
                        f'[DIAGNÓSTICO INDEX]     hasattr(section, "background_settings"): {hasattr(section, "background_settings")}')

                    if hasattr(section, 'background_settings'):
                        print(f'[DIAGNÓSTICO INDEX]     ✅ background_settings existe!')
                        bg_settings = section.background_settings
                        print(f'[DIAGNÓSTICO INDEX]     background_settings.habilitado: {bg_settings.habilitado}')
                        print(f'[DIAGNÓSTICO INDEX]     background_settings.imagem: {bg_settings.imagem}')
                        print(f'[DIAGNÓSTICO INDEX]     background_settings.opacidade: {bg_settings.opacidade}')
                        print(f'[DIAGNÓSTICO INDEX]     background_settings.aplicar_em: {bg_settings.aplicar_em}')
                        print(f'[DIAGNÓSTICO INDEX]     background_settings.posicao: {bg_settings.posicao}')

                        if bg_settings.habilitado:
                            print(f'[DIAGNÓSTICO INDEX]     ✅ Background habilitado e adicionado ao contexto')
                            # *** DEFINIR BACKGROUND_SETTINGS PARA USO NO CONTEXTO ***
                            background_settings = bg_settings
                            section_data['background_settings'] = bg_settings
                            processed_sections.append(section_data)
                        else:
                            print(f'[DIAGNÓSTICO INDEX]     ⚠️ Background existe mas está desabilitado')
                    else:
                        print(f'[DIAGNÓSTICO INDEX]     ❌ background_settings não existe para: {section.titulo}')
                        # Debug adicional
                        attrs = [attr for attr in dir(section) if
                                 not attr.startswith("_") and not callable(getattr(section, attr))]
                        print(
                            f'[DIAGNÓSTICO INDEX]     Atributos disponíveis: {attrs[:10]}...')  # Mostrar só os primeiros 10

                elif section.tipo == 'shelf':
                    print(f'[DIAGNÓSTICO INDEX] └── Processando prateleira de livros: {section.titulo}')
                    livros = section.get_books()
                    if livros and livros.exists():
                        print(f'[DIAGNÓSTICO INDEX]     ✅ Prateleira com {livros.count()} livros adicionada')
                        section_data['livros'] = livros
                        processed_sections.append(section_data)
                    else:
                        print(f'[DIAGNÓSTICO INDEX]     ⚠️ Prateleira sem livros: {section.titulo}')

                elif section.tipo == 'video':
                    print(f'[DIAGNÓSTICO INDEX] └── Processando seção de vídeo: {section.titulo}')
                    print(
                        f'[DIAGNÓSTICO INDEX]     Verificando se tem video_section... {hasattr(section, "video_section")}')
                    if hasattr(section, 'video_section'):
                        print(f'[DIAGNÓSTICO INDEX]     ✅ video_section existe! Buscando vídeos associados...')
                        videos = VideoItem.objects.filter(
                            videosectionitem__video_section=section.video_section,
                            videosectionitem__ativo=True
                        ).order_by('videosectionitem__ordem')
                        print(f'[DIAGNÓSTICO INDEX]     Vídeos encontrados após filtro e ordenação: {videos.count()}')
                        if videos.exists():
                            print(
                                f'[DIAGNÓSTICO INDEX]     ✅ Seção de vídeo com {videos.count()} vídeos adicionada ao contexto.')
                            section_data['videos'] = videos
                            processed_sections.append(section_data)
                        else:
                            print(
                                f'[DIAGNÓSTICO INDEX]     ⚠️ Seção de vídeo encontrada, mas sem vídeos ativos associados: {section.titulo}')
                    else:
                        print(
                            f'[DIAGNÓSTICO INDEX]     ❌ Atributo video_section não foi encontrado para: {section.titulo}. Verifique se a seção foi salva corretamente no admin.')

                elif section.tipo == 'author':
                    print('=' * 50)
                    print(f'[DIAGNÓSTICO INDEX] └── 🎯 PROCESSANDO SEÇÃO DE AUTOR: {section.titulo}')
                    print(f'[DIAGNÓSTICO INDEX]     Verificando se tem author_section...')
                    print(
                        f'[DIAGNÓSTICO INDEX]     hasattr(section, "author_section"): {hasattr(section, "author_section")}')
                    if hasattr(section, 'author_section'):
                        print(f'[DIAGNÓSTICO INDEX]     ✅ author_section existe!')
                        print(f'[DIAGNÓSTICO INDEX]     author_section.ativo: {section.author_section.ativo}')
                        print(f'[DIAGNÓSTICO INDEX]     Chamando get_autores()...')
                        try:
                            autores = section.author_section.get_autores()
                            print(f'[DIAGNÓSTICO INDEX]     get_autores() executado com sucesso')
                            print(f'[DIAGNÓSTICO INDEX]     Tipo do retorno: {type(autores)}')
                            if autores:
                                if hasattr(autores, 'count'):
                                    autores_count = autores.count()
                                else:
                                    autores_count = len(autores)
                                print(f'[DIAGNÓSTICO INDEX]     Autores encontrados: {autores_count}')
                                if autores_count > 0:
                                    try:
                                        autores_list = list(autores.values_list('nome', 'sobrenome', 'ativo'))
                                        print(f'[DIAGNÓSTICO INDEX]     Lista de autores: {autores_list}')
                                    except Exception as e:
                                        print(f'[DIAGNÓSTICO INDEX]     Erro ao listar autores: {e}')

                                    print(
                                        f'[DIAGNÓSTICO INDEX]     ✅ SEÇÃO DE AUTOR ADICIONADA COM {autores_count} AUTORES!')
                                    section_data['authors'] = autores
                                    section_data['author_section'] = section.author_section
                                    processed_sections.append(section_data)
                                else:
                                    print(f'[DIAGNÓSTICO INDEX]     ⚠️ get_autores() retornou lista vazia')
                            else:
                                print(f'[DIAGNÓSTICO INDEX]     ⚠️ get_autores() retornou None')
                        except Exception as autor_error:
                            print(f'[DIAGNÓSTICO INDEX]     ❌ ERRO em get_autores(): {autor_error}')
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f'[DIAGNÓSTICO INDEX]     ❌ author_section NÃO EXISTE para seção: {section.titulo}')
                    print('=' * 50)

                # Outros tipos de seção...
                elif section.tipo == 'ad':
                    print(f'[DIAGNÓSTICO INDEX] └── Processando propaganda: {section.titulo}')
                    if hasattr(section, 'advertisement'):
                        print(f'[DIAGNÓSTICO INDEX]     ✅ Propaganda adicionada')
                        section_data['advertisement'] = section.advertisement
                        processed_sections.append(section_data)
                    else:
                        print(f'[DIAGNÓSTICO INDEX]     ❌ advertisement não existe para: {section.titulo}')

                elif section.tipo == 'link_grid':
                    print(f'[DIAGNÓSTICO INDEX] └── Processando grade de links: {section.titulo}')
                    if hasattr(section, 'link_items'):
                        links = section.link_items.filter(ativo=True)
                        if links.exists():
                            print(f'[DIAGNÓSTICO INDEX]     ✅ Grade de links com {links.count()} itens adicionada')
                            section_data['links'] = links
                            processed_sections.append(section_data)
                        else:
                            print(f'[DIAGNÓSTICO INDEX]     ⚠️ Grade de links sem itens: {section.titulo}')
                    else:
                        print(f'[DIAGNÓSTICO INDEX]     ❌ link_items não existe para: {section.titulo}')

                else:
                    print(f'[DIAGNÓSTICO INDEX] └── Tipo de seção não reconhecido: {section.tipo}')

            # *** ADICIONAR BACKGROUND_SETTINGS AO CONTEXTO FORA DO LOOP ***
            context['background_settings'] = background_settings
            context['shelves'] = processed_sections

            # *** DEBUG FINAL DO BACKGROUND ***
            print('=' * 80)
            print(f'[DIAGNÓSTICO INDEX] ==================== DEBUG BACKGROUND ====================')
            if background_settings:
                print(f'[DIAGNÓSTICO INDEX] ✅ BACKGROUND SETTINGS FINAL DEFINIDO:')
                print(f'[DIAGNÓSTICO INDEX]     - Objeto: {background_settings}')
                print(f'[DIAGNÓSTICO INDEX]     - Imagem: {background_settings.imagem}')
                print(f'[DIAGNÓSTICO INDEX]     - URL: {background_settings.imagem.url}')
                print(f'[DIAGNÓSTICO INDEX]     - Habilitado: {background_settings.habilitado}')
                print(f'[DIAGNÓSTICO INDEX]     - Opacidade: {background_settings.opacidade}')
                print(f'[DIAGNÓSTICO INDEX]     - Posição: {background_settings.posicao}')
                print(f'[DIAGNÓSTICO INDEX]     - Aplicar em: {background_settings.aplicar_em}')
            else:
                print(f'[DIAGNÓSTICO INDEX] ❌ BACKGROUND_SETTINGS É NONE - NÃO SERÁ RENDERIZADO')
            print('=' * 80)

            # Resto do código (eventos, ranking, etc...)
            featured_events = EventItem.objects.filter(
                ativo=True,
                em_destaque=True
            ).order_by('-data_evento')[:6]
            context['featured_events'] = featured_events
            if featured_events:
                print(
                    f'[DIAGNÓSTICO INDEX] ✅ {len(featured_events)} evento(s) em destaque encontrados para o carrossel.')
            else:
                print('[DIAGNÓSTICO INDEX] ⚠️ Nenhum evento em destaque ativo foi encontrado.')

            context['ranking_usuarios'] = User.objects.select_related('profile').annotate(
                livros_lidos=Count('bookshelves', filter=Q(bookshelves__shelf_type='lido'))
            ).filter(livros_lidos__gt=0).order_by('-livros_lidos')[:3]

            print(f'[DIAGNÓSTICO INDEX] Ranking de leitores: {context["ranking_usuarios"].count()} usuários')

            # >>> INÍCIO DA CORREÇÃO <<<
            # Busca as opções de prateleiras para serem usadas nos dropdowns da página.
            try:
                opcoes_prateleiras = Book.get_shelf_special_choices()
                # Filtra a opção "Nenhum" (''), que não é útil em um dropdown de adição.
                opcoes_prateleiras_filtradas = [choice for choice in opcoes_prateleiras if choice[0]]
                context['opcoes_prateleiras'] = opcoes_prateleiras_filtradas
                print(
                    f'[DIAGNÓSTICO INDEX] ✅ Opções de prateleiras carregadas para dropdowns: {len(opcoes_prateleiras_filtradas)} opções')
            except Exception as e:
                # Em caso de erro, define uma lista vazia para não quebrar a página.
                context['opcoes_prateleiras'] = []
                print(f'[DIAGNÓSTICO INDEX] ❌ Erro ao buscar opções de prateleiras para a home: {e}')
            # >>> FIM DA CORREÇÃO <<<

            print('[DIAGNÓSTICO INDEX] ==================== FIM ====================')
            print('=' * 80)
            return context

        except Exception as e:
            print(f'[DIAGNÓSTICO INDEX] ❌ ERRO FATAL ao carregar página: {e}')
            import traceback
            traceback.print_exc()
            messages.error(self.request, 'Ocorreu um erro ao carregar a página inicial.')
            context.update({'banners': [], 'shelves': [], 'ranking_usuarios': [], 'background_settings': None,
                            'opcoes_prateleiras': []})
            return context


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


class EventosView(ListView):
    model = EventItem
    template_name = 'core/eventos.html'
    context_object_name = 'event_list'
    paginate_by = 10

    def get_queryset(self):
        # Retorna todos os eventos ativos, ordenados pelos mais recentes primeiro
        return EventItem.objects.filter(ativo=True).order_by('-data_evento')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Adiciona propagandas ativas ao contexto para exibir na página
        context['advertisements'] = Advertisement.objects.filter(
            section__ativo=True
        ).select_related('section')
        context['title'] = 'Eventos Literários'
        return context

@require_http_methods(["GET"])
def get_csrf_token(request):
    """
    View para obter/renovar o CSRF token.
    Útil quando o token expira ou há problemas de sincronização.
    """
    try:
        # Obter novo token
        token = get_token(request)

        logger.info(
            f'CSRF token gerado para usuário: {request.user.username if request.user.is_authenticated else "Anônimo"}')

        return JsonResponse({
            'csrf_token': token,
            'status': 'success',
            'message': 'Token CSRF obtido com sucesso'
        })

    except Exception as e:
        logger.error(f'Erro ao gerar CSRF token: {str(e)}')
        return JsonResponse({
            'error': 'Erro ao obter token CSRF',
            'status': 'error'
        }, status=500)