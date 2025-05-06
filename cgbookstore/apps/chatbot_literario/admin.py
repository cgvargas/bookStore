from django.contrib import admin
from django.urls import path, include
from .models import Conversation, Message
from .admin_views import get_admin_urls


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['timestamp']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'started_at', 'updated_at', 'message_count']
    list_filter = ['started_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'messages__content']
    inlines = [MessageInline]

    def message_count(self, obj):
        return obj.messages.count()

    message_count.short_description = 'Mensagens'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender_display', 'content_preview', 'conversation_user', 'timestamp']
    list_filter = ['sender', 'timestamp']
    search_fields = ['content', 'conversation__user__username']

    def sender_display(self, obj):
        return obj.get_sender_display()

    sender_display.short_description = 'Remetente'

    def content_preview(self, obj):
        max_length = 50
        if len(obj.content) > max_length:
            return obj.content[:max_length] + '...'
        return obj.content

    content_preview.short_description = 'Conteúdo'

    def conversation_user(self, obj):
        return obj.conversation.user.username

    conversation_user.short_description = 'Usuário'


# Adicionar URLs customizadas diretamente ao Django Admin
admin_urls = get_admin_urls()
admin.site.get_urls = (lambda original_get_urls=admin.site.get_urls:
                       lambda: admin_urls + original_get_urls())