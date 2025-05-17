from django.contrib import admin
from cgbookstore.apps.core.admin import admin_site  # Importar o admin_site personalizado
from .models import Conversation, Message, KnowledgeItem, ConversationFeedback


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'content', 'timestamp')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# Remover o decorador @admin.register e usar admin_site.register
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


# Remover o decorador @admin.register e usar admin_site.register
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
        return obj.content[:50] + ('...' if len(obj.content) > 50 else '')

    short_content.short_description = 'Conteúdo'

    def conversation_user(self, obj):
        return obj.conversation.user.username

    conversation_user.short_description = 'Usuário'


# Remover o decorador @admin.register e usar admin_site.register
class KnowledgeItemAdmin(admin.ModelAdmin):
    list_display = ('short_question', 'short_answer', 'category', 'source', 'created_at', 'active')
    list_filter = ('category', 'source', 'active', 'created_at')
    search_fields = ('question', 'answer', 'category')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('active',)
    fieldsets = (
        (None, {
            'fields': ('question', 'answer'),
        }),
        ('Classificação', {
            'fields': ('category', 'source'),
        }),
        ('Controle', {
            'fields': ('active', 'created_at', 'updated_at'),
        }),
    )

    def short_question(self, obj):
        return obj.question[:50] + ('...' if len(obj.question) > 50 else '')

    short_question.short_description = 'Pergunta'

    def short_answer(self, obj):
        return obj.answer[:50] + ('...' if len(obj.answer) > 50 else '')

    short_answer.short_description = 'Resposta'


# Remover o decorador @admin.register e usar admin_site.register
class ConversationFeedbackAdmin(admin.ModelAdmin):
    list_display = ('message_content', 'helpful', 'comment_preview', 'timestamp')
    list_filter = ('helpful', 'timestamp')
    search_fields = ('comment', 'message__content')
    readonly_fields = ('message', 'helpful', 'comment', 'timestamp')

    def message_content(self, obj):
        return obj.message.content[:50] + ('...' if len(obj.message.content) > 50 else '')

    message_content.short_description = 'Mensagem'

    def comment_preview(self, obj):
        if not obj.comment:
            return '-'
        return obj.comment[:50] + ('...' if len(obj.comment) > 50 else '')

    comment_preview.short_description = 'Comentário'


# Registrar todos os modelos no admin_site personalizado
admin_site.register(Conversation, ConversationAdmin)
admin_site.register(Message, MessageAdmin)
admin_site.register(KnowledgeItem, KnowledgeItemAdmin)
admin_site.register(ConversationFeedback, ConversationFeedbackAdmin)