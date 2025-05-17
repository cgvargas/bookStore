from django.db import models
from django.conf import settings


class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chatbot_conversations')
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conversa'
        verbose_name_plural = 'Conversas'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversa de {self.user.username} - {self.started_at.strftime('%d/%m/%Y %H:%M')}"


class Message(models.Model):
    SENDER_CHOICES = (
        ('user', 'Usuário'),
        ('bot', 'Chatbot'),
    )

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.get_sender_display()}: {self.content[:30]}..."


class KnowledgeItem(models.Model):
    """
    Modelo para armazenar itens da base de conhecimento do chatbot.
    Cada item contém uma pergunta, resposta e metadados associados.
    """
    question = models.TextField(verbose_name='Pergunta')
    answer = models.TextField(verbose_name='Resposta')
    category = models.CharField(max_length=100, verbose_name='Categoria', blank=True, default='geral')
    source = models.CharField(max_length=100, verbose_name='Fonte', blank=True, default='manual')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    embedding = models.JSONField(null=True, blank=True, verbose_name='Embedding')
    active = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Item de Conhecimento'
        verbose_name_plural = 'Itens de Conhecimento'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return f"{self.question[:50]}..."


class ConversationFeedback(models.Model):
    """
    Modelo para armazenar feedback sobre as respostas do chatbot.
    """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='feedback')
    helpful = models.BooleanField(default=False, verbose_name='Foi útil?')
    comment = models.TextField(blank=True, verbose_name='Comentário')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Data do feedback')

    class Meta:
        verbose_name = 'Feedback de Conversa'
        verbose_name_plural = 'Feedbacks de Conversas'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Feedback: {'Útil' if self.helpful else 'Não útil'} - {self.message}"