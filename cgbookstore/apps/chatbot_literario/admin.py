# cgbookstore/apps/chatbot_literario/admin.py
from django.contrib import admin
from django.utils.html import format_html
# Remova a importação de reverse e mark_safe se não forem usadas em outro lugar
# from django.urls import reverse
# from django.utils.safestring import mark_safe
from .models import (
    Conversation,
    Message,
    ConversationFeedback,
    KnowledgeItem,
    ChatbotConfiguration,
    TrainingSession,
    ConversationSummary
)

# 1. IMPORTAR A SUA INSTÂNCIA DE ADMIN PERSONALIZADA
from cgbookstore.apps.core.admin import admin_site


class MessageInline(admin.TabularInline):
    """Inline para mensagens dentro de uma conversa"""
    model = Message
    extra = 0
    # Campos readonly podem ser simplificados se não houver lógica complexa
    readonly_fields = ('role', 'content', 'source', 'timestamp', 'response_time', 'model_used', 'token_count')

    # O campo 'fields' pode ser omitido se todos os campos do modelo estiverem em readonly_fields

    def has_add_permission(self, request, obj=None):
        return False


class ConversationFeedbackInline(admin.StackedInline):
    """Inline para feedback de conversa"""
    model = ConversationFeedback
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('rating', 'comment', 'created_at')


class ConversationAdmin(admin.ModelAdmin):
    """Admin para conversas"""
    list_display = ('id', 'user', 'title', 'is_active', 'started_at', 'message_count', 'has_feedback')
    list_filter = ('is_active', 'started_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'title')
    readonly_fields = ('id', 'started_at', 'updated_at')
    list_editable = ('is_active',)
    date_hierarchy = 'started_at'

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'user', 'title', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [MessageInline, ConversationFeedbackInline]

    def message_count(self, obj):
        """Conta mensagens na conversa"""
        return obj.messages.count()

    message_count.short_description = 'Mensagens'

    def has_feedback(self, obj):
        """Verifica se tem feedback"""
        # A verificação de hasattr(obj, 'feedback') pode falhar se não houver feedback.
        # É mais seguro usar um try-except ou verificar se o campo é None.
        try:
            if obj.feedback:
                return format_html('<span style="color: green;">✓</span>')
        except ConversationFeedback.DoesNotExist:
            pass
        return format_html('<span style="color: red;">✗</span>')

    has_feedback.short_description = 'Feedback'
    has_feedback.allow_tags = True  # Para versões mais antigas do Django

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('messages').select_related('feedback')


# ... (As definições das outras classes Admin como MessageAdmin, KnowledgeItemAdmin, etc. permanecem as mesmas)
class MessageAdmin(admin.ModelAdmin):
    """Admin para mensagens"""
    list_display = ('conversation', 'role', 'content_preview', 'source', 'timestamp', 'response_time')
    list_filter = ('role', 'source', 'timestamp')
    search_fields = ('content', 'conversation__user__username')
    readonly_fields = ('id', 'timestamp', 'response_time', 'model_used', 'token_count')
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'conversation', 'role', 'content', 'source')
        }),
        ('Metadados', {
            'fields': ('timestamp', 'response_time', 'model_used', 'token_count'),
            'classes': ('collapse',)
        }),
    )

    def content_preview(self, obj):
        """Preview do conteúdo da mensagem"""
        if len(obj.content) > 50:
            return f"{obj.content[:50]}..."
        return obj.content

    content_preview.short_description = 'Conteúdo'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conversation__user')


class ConversationFeedbackAdmin(admin.ModelAdmin):
    """Admin para feedback de conversas"""
    list_display = ('conversation', 'rating_display', 'comment_preview', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('conversation__user__username', 'comment')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'conversation', 'rating', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def rating_display(self, obj):
        """Exibe o rating com estrelas"""
        if obj.rating:
            return dict(obj.RATING_CHOICES).get(obj.rating, 'Sem nota')
        return 'Sem nota'

    rating_display.short_description = 'Avaliação'

    def comment_preview(self, obj):
        """Preview do comentário"""
        if obj.comment and len(obj.comment) > 50:
            return f"{obj.comment[:50]}..."
        return obj.comment or "Sem comentário"

    comment_preview.short_description = 'Comentário'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conversation__user')


class KnowledgeItemAdmin(admin.ModelAdmin):
    """Admin para itens de conhecimento"""
    list_display = ('title', 'content_type', 'is_active', 'created_at', 'has_embedding')
    list_filter = ('content_type', 'is_active', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('id', 'created_at', 'updated_at', 'embedding_status')
    list_editable = ('is_active',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'title', 'content_type', 'content', 'is_active')
        }),
        ('Metadados', {
            'fields': ('metadata', 'tags'),
            'classes': ('collapse',)
        }),
        ('Embedding', {
            'fields': ('embedding_status', 'embedding_vector'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_embedding(self, obj):
        """Verifica se tem embedding"""
        if obj.embedding_vector:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')

    has_embedding.short_description = 'Embedding'

    def embedding_status(self, obj):
        """Status do embedding"""
        if obj.embedding_vector:
            return format_html('<span style="color: green;">Embedding disponível</span>')
        return format_html('<span style="color: orange;">Embedding pendente</span>')

    embedding_status.short_description = 'Status do Embedding'

    actions = ['generate_embeddings', 'activate_items', 'deactivate_items']

    def generate_embeddings(self, request, queryset):
        """Ação para gerar embeddings"""
        count = queryset.filter(embedding_vector__isnull=True).count()
        self.message_user(request, f"Solicitação para gerar embeddings de {count} itens enviada.")

    generate_embeddings.short_description = "Gerar embeddings dos itens selecionados"

    def activate_items(self, request, queryset):
        """Ação para ativar itens"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} itens ativados com sucesso.")

    activate_items.short_description = "Ativar itens selecionados"

    def deactivate_items(self, request, queryset):
        """Ação para desativar itens"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} itens desativados com sucesso.")

    deactivate_items.short_description = "Desativar itens selecionados"


class TrainingSessionAdmin(admin.ModelAdmin):
    """Admin para sessões de treinamento"""
    list_display = ('name', 'status', 'progress_bar', 'accuracy_score', 'embeddings_generated', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('id', 'progress_percentage', 'created_at', 'started_at', 'completed_at', 'processing_time')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'name', 'status')
        }),
        ('Progresso', {
            'fields': ('items_trained', 'items_total', 'progress_percentage')
        }),
        ('Resultados', {
            'fields': ('accuracy_score', 'embeddings_generated', 'processing_time'),
            'classes': ('collapse',)
        }),
        ('Logs e Erros', {
            'fields': ('log_data', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def progress_bar(self, obj):
        """Barra de progresso visual"""
        percentage = obj.progress_percentage
        color = 'green' if percentage == 100 else 'blue' if percentage > 0 else 'gray'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}%</div></div>',
            percentage, color, int(percentage)
        )

    progress_bar.short_description = 'Progresso'

    def has_add_permission(self, request):
        return False  # Sessões são criadas programaticamente

    def has_delete_permission(self, request, obj=None):
        return obj and obj.status in ['completed', 'failed', 'cancelled'] if obj else True


class ChatbotConfigurationAdmin(admin.ModelAdmin):
    """Admin para configurações do chatbot"""
    list_display = ('key', 'value_preview', 'is_active', 'updated_at')
    list_filter = ('is_active', 'updated_at')
    search_fields = ('key', 'value', 'description')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active',)

    fieldsets = (
        ('Configuração', {
            'fields': ('key', 'value', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def value_preview(self, obj):
        """Preview do valor da configuração"""
        if len(obj.value) > 50:
            return f"{obj.value[:50]}..."
        return obj.value

    value_preview.short_description = 'Valor'


class ConversationSummaryAdmin(admin.ModelAdmin):
    """Admin para resumos de conversas"""
    list_display = ('conversation', 'sentiment', 'key_topics_preview', 'created_at')
    list_filter = ('sentiment', 'created_at')
    search_fields = ('conversation__user__username', 'summary_text')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Resumo', {
            'fields': ('conversation', 'summary_text', 'sentiment')
        }),
        ('Análise', {
            'fields': ('key_topics',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def key_topics_preview(self, obj):
        """Preview dos tópicos principais"""
        if obj.key_topics:
            topics = obj.key_topics[:3]  # Primeiros 3 tópicos
            return ", ".join(topics) + ("..." if len(obj.key_topics) > 3 else "")
        return "Nenhum tópico"

    key_topics_preview.short_description = 'Tópicos'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conversation__user')


# REGISTRE OS MODELOS COM A SUA INSTÂNCIA PERSONALIZADA
admin_site.register(Conversation, ConversationAdmin)
admin_site.register(Message, MessageAdmin)
admin_site.register(ConversationFeedback, ConversationFeedbackAdmin)
admin_site.register(KnowledgeItem, KnowledgeItemAdmin)
admin_site.register(ChatbotConfiguration, ChatbotConfigurationAdmin)
admin_site.register(TrainingSession, TrainingSessionAdmin)
admin_site.register(ConversationSummary, ConversationSummaryAdmin)

