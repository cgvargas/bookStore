# cgbookstore/apps/chatbot_literario/admin.py

from django.contrib import admin, messages  # ✅ Importar 'messages' para feedback ao usuário
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.core.exceptions import FieldError

from cgbookstore.apps.core.admin import admin_site
from .models import Conversation, Message, KnowledgeItem, ConversationFeedback
from django.db import connection

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'content', 'timestamp')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class ConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'started_at', 'updated_at', 'message_count')
    list_filter = ('started_at', 'updated_at', 'user')
    search_fields = ('user__username', 'messages__content')
    date_hierarchy = 'started_at'
    inlines = [MessageInline]

    def message_count(self, obj):
        return obj.messages.count()

    message_count.short_description = 'Mensagens'


class FeedbackInline(admin.TabularInline):
    model = ConversationFeedback
    extra = 0
    readonly_fields = ('helpful', 'comment', 'timestamp')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender_display', 'short_content', 'timestamp', 'conversation_user')
    list_filter = ('sender', 'timestamp')
    search_fields = ('content', 'conversation__user__username')
    readonly_fields = ('conversation', 'sender', 'content', 'timestamp')
    inlines = [FeedbackInline]

    def sender_display(self, obj):
        return obj.get_sender_display()

    sender_display.short_description = 'Remetente'

    def short_content(self, obj):
        return obj.content[:40] + ('...' if len(obj.content) > 40 else '')

    short_content.short_description = 'Conteúdo'

    def conversation_user(self, obj):
        return obj.conversation.user.username

    conversation_user.short_description = 'Usuário'


class KnowledgeItemAdmin(admin.ModelAdmin):
    # ... (toda a sua configuração, list_display, actions, etc. permanece aqui) ...
    list_display = ('short_question', 'category', 'active', 'updated_at')
    list_filter = ('category', 'active', 'source', 'created_at')
    search_fields = ('question', 'answer', 'category')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('active',)
    list_per_page = 50
    # ...

    def short_question(self, obj):
        return obj.question[:70] + ('...' if len(obj.question) > 70 else '')
    short_question.short_description = 'Pergunta'

    def short_answer(self, obj):
        return obj.answer[:70] + ('...' if len(obj.answer) > 70 else '')
    short_answer.short_description = 'Resposta'

    # --- Suas ações ... ---
    actions = ['make_literatura', 'make_general'] # etc...

    @admin.action(description='Mover para categoria: Literatura')
    def make_literatura(self, request, queryset):
        # ...
        updated_count = queryset.update(category='literatura')
        self.message_user(request, f'{updated_count} itens foram movidos para a categoria "Literatura".', messages.SUCCESS)

    @admin.action(description='Mover para categoria: Geral')
    def make_general(self, request, queryset):
        # ...
        updated_count = queryset.update(category='general')
        self.message_user(request, f'{updated_count} itens foram movidos para a categoria "Geral".', messages.SUCCESS)

    # ✅ SUBSTITUA O MÉTODO get_search_results POR ESTA VERSÃO FINAL
    def get_search_results(self, request, queryset, search_term):
        # A busca padrão do Django sempre será nosso fallback
        queryset_standard, use_distinct_standard = super().get_search_results(request, queryset, search_term)

        if not search_term.strip():
            return queryset_standard, use_distinct_standard

        # Se for PostgreSQL, tentamos a busca inteligente
        if connection.vendor == 'postgresql':
            search_config = 'portuguese' # Tenta a melhor configuração primeiro
            try:
                # Tenta a busca com a configuração de idioma
                vector = SearchVector('question', 'answer', config=search_config)
                query = SearchQuery(search_term, config=search_config, search_type='websearch')
                queryset_vector = queryset.annotate(search=vector).filter(search=query)
            except FieldError:
                # Se 'portuguese' não estiver configurado no PG, ele lança um FieldError.
                # Nós o capturamos e tentamos novamente com a configuração 'simple'.
                print("AVISO: Config de busca 'portuguese' não encontrada. Usando fallback 'simple'.")
                search_config = 'simple'
                vector = SearchVector('question', 'answer', config=search_config)
                query = SearchQuery(search_term, config=search_config, search_type='websearch')
                queryset_vector = queryset.annotate(search=vector).filter(search=query)

            # Combina os resultados da busca padrão (que usa LIKE) com a busca por vetor
            combined_queryset = (queryset_standard | queryset_vector).distinct()
            return combined_queryset, True

        # Para outros bancos, retorna apenas a busca padrão
        return queryset_standard, use_distinct_standard


class ConversationFeedbackAdmin(admin.ModelAdmin):
    list_display = ('message_content', 'helpful', 'comment_preview', 'timestamp')
    list_filter = ('helpful', 'timestamp')
    search_fields = ('comment', 'message__content')
    readonly_fields = ('message', 'helpful', 'comment', 'timestamp')

    def message_content(self, obj):
        return obj.message.content[:40] + ('...' if len(obj.message.content) > 40 else '')

    message_content.short_description = 'Mensagem'

    def comment_preview(self, obj):
        if not obj.comment:
            return '-'
        return obj.comment[:40] + ('...' if len(obj.comment) > 40 else '')

    comment_preview.short_description = 'Comentário'


# Registrar todos os modelos no admin_site personalizado (mantendo sua estrutura)
admin_site.register(Conversation, ConversationAdmin)
admin_site.register(Message, MessageAdmin)
admin_site.register(KnowledgeItem, KnowledgeItemAdmin)
admin_site.register(ConversationFeedback, ConversationFeedbackAdmin)