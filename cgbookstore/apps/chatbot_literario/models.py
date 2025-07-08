from django.db import models
from django.conf import settings
from django.utils import timezone

from django.core.validators import MinValueValidator, MaxValueValidator

class KnowledgeItem(models.Model):
    """
    Armazena uma unidade de conhecimento para o chatbot (pergunta e resposta).
    """
    question = models.TextField(
        unique=True,
        help_text="A pergunta ou padrão de consulta do usuário."
    )
    answer = models.TextField(
        help_text="A resposta que o chatbot deve fornecer."
    )
    category = models.CharField(
        max_length=100,
        default='general',
        db_index=True,
        help_text="Categoria do conhecimento (ex: 'saudação', 'preços', 'autores')."
    )
    source = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Origem da informação (ex: 'manual', 'learned_from_chat')."
    )
    # ===== CAMPO ADICIONADO ABAIXO =====
    confidence = models.FloatField(
        default=0.8,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Nível de confiança na exatidão da resposta (0.0 a 1.0)."
    )
    # ===================================
    embedding = models.JSONField(
        null=True,
        blank=True,
        help_text="Vetor de embedding para a busca semântica."
    )
    active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indica se o item de conhecimento está ativo e pode ser usado."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item de Conhecimento"
        verbose_name_plural = "Itens de Conhecimento"
        ordering = ['-updated_at']

    def __str__(self):
        return self.question[:80]


class Conversation(models.Model):
    """
    Representa uma sessão de conversa entre um usuário e o chatbot.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chatbot_conversations'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    context_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Armazena o contexto da conversa, se necessário."
    )
    is_training_session = models.BooleanField(
        default=False,
        verbose_name='Sessão de Treinamento',
        help_text='Indica se esta conversa é do simulador de treinamento'
    )
    # REMOVIDO: Campo is_training_session duplicado

    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Título',
        help_text='Título descritivo da conversa'
    )

    class Meta:
        verbose_name = "Conversa do Chatbot"
        verbose_name_plural = "Conversas do Chatbot"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversa com {self.user.username} iniciada em {self.started_at.strftime('%Y-%m-%d %H:%M')}"

    def get_context(self):
        """
        Retorna o dicionário de dados de contexto da conversa.
        """
        return self.context_data

    def update_context(self, context_dict):
        """
        Atualiza o contexto da conversa.
        """
        self.context_data = context_dict
        self.save(update_fields=['context_data', 'updated_at'])


class Message(models.Model):
    """
    Armazena uma única mensagem dentro de uma conversa.
    """
    SENDER_CHOICES = [
        ('user', 'Usuário'),
        ('bot', 'Chatbot'),
    ]
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.CharField(
        max_length=10,
        choices=SENDER_CHOICES
    )
    was_corrected = models.BooleanField(
        default=False,
        verbose_name='Foi Corrigida',
        help_text='Indica se esta resposta foi corrigida via treinamento'
    )

    corrected_response = models.TextField(
        blank=True,
        verbose_name='Resposta Corrigida',
        help_text='A resposta correta fornecida durante o treinamento'
    )

    corrected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # CORRIGIDO: Era User, agora settings.AUTH_USER_MODEL
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrected_messages',
        verbose_name='Corrigida por',
        help_text='Admin que realizou a correção'
    )

    corrected_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Corrigida em',
        help_text='Data e hora da correção'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mensagem do Chatbot"
        verbose_name_plural = "Mensagens do Chatbot"
        ordering = ['timestamp']

    def __str__(self):
        return f"Mensagem de '{self.sender}' em {self.timestamp.strftime('%H:%M:%S')}"


class ConversationFeedback(models.Model):
    """
    Armazena o feedback do usuário para uma mensagem específica do chatbot.
    """
    RATING_CHOICES = [
        (1, '⭐'),
        (2, '⭐⭐'),
        (3, '⭐⭐⭐'),
        (4, '⭐⭐⭐⭐'),
        (5, '⭐⭐⭐⭐⭐'),
    ]

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='feedback',
        help_text="A mensagem do chatbot que está recebendo o feedback."
    )
    helpful = models.BooleanField(
        'Foi útil?',
        default=True,
        help_text="Indica se o usuário considerou a resposta útil."
    )
    comment = models.TextField(
        'Comentário',
        blank=True,
        null=True,
        help_text="Comentário opcional do usuário."
    )
    timestamp = models.DateTimeField(
        'Data do Feedback',
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Feedback de Conversa"
        verbose_name_plural = "Feedbacks de Conversas"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Feedback para a mensagem {self.message.id}"


class ChatAnalytics(models.Model):
    """
    Registra métricas e estatísticas de uso do chatbot para análise.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_analytics'
    )
    session_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="ID da sessão para agrupar interações de um mesmo usuário anônimo."
    )
    intent = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Intenção detectada pelo chatbot (ex: 'search', 'recommendation')."
    )
    response_time = models.FloatField(
        help_text="Tempo de resposta do chatbot em segundos."
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="Data e hora da interação."
    )

    class Meta:
        verbose_name = "Análise do Chat"
        verbose_name_plural = "Análises do Chat"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'intent']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        user_display = self.user.username if self.user else "Anônimo"
        return f"Interação de {user_display} em {self.timestamp.strftime('%Y-%m-%d %H:%M')} (Intenção: {self.intent})"


class TrainingSession(models.Model):
    """
    Model para rastrear sessões de treinamento e correções do chatbot.
    Registra todas as intervenções manuais para analytics e auditoria.
    """

    TRAINING_TYPES = [
        ('manual_correction', 'Correção Manual via Simulador'),
        ('manual_addition', 'Adição Manual de Conhecimento'),
        ('bulk_training', 'Treinamento em Lote'),
        ('auto_learning', 'Aprendizado Automático'),
        ('embedding_update', 'Atualização de Embeddings'),
        ('knowledge_cleanup', 'Limpeza da Base de Conhecimento'),
    ]

    # Informações da sessão
    trainer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuário Treinador',
        help_text='Admin que realizou o treinamento'
    )

    session_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='ID da Sessão',
        help_text='Identificador único da sessão de treinamento'
    )

    training_type = models.CharField(
        max_length=20,
        choices=TRAINING_TYPES,
        default='manual_correction',
        verbose_name='Tipo de Treinamento'
    )

    # Conteúdo do treinamento
    original_question = models.TextField(
        verbose_name='Pergunta Original',
        help_text='Pergunta que gerou a necessidade de treinamento'
    )

    original_answer = models.TextField(
        blank=True,
        verbose_name='Resposta Original',
        help_text='Resposta incorreta que foi dada pelo sistema'
    )

    corrected_answer = models.TextField(
        verbose_name='Resposta Corrigida',
        help_text='Resposta correta fornecida durante o treinamento'
    )

    # Relacionamentos
    knowledge_item = models.ForeignKey(
        'KnowledgeItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Item de Conhecimento',
        help_text='Item da KB criado/modificado durante esta sessão'
    )

    conversation = models.ForeignKey(
        'Conversation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Conversa Relacionada',
        help_text='Conversa onde ocorreu o erro (se aplicável)'
    )

    # Metadados
    notes = models.TextField(
        blank=True,
        verbose_name='Observações',
        help_text='Notas adicionais sobre a sessão de treinamento'
    )

    success = models.BooleanField(
        default=True,
        verbose_name='Sucesso',
        help_text='Indica se o treinamento foi aplicado com sucesso'
    )

    error_message = models.TextField(
        blank=True,
        verbose_name='Mensagem de Erro',
        help_text='Detalhes do erro caso o treinamento tenha falhado'
    )

    # Métricas de performance
    response_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Tempo de Resposta (ms)',
        help_text='Tempo que levou para processar o treinamento'
    )

    confidence_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Score de Confiança',
        help_text='Score de confiança na correção aplicada (0.0 a 1.0)'
    )

    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Criado em'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    class Meta:
        verbose_name = 'Sessão de Treinamento'
        verbose_name_plural = 'Sessões de Treinamento'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['trainer_user', '-created_at']),
            models.Index(fields=['training_type', '-created_at']),
            models.Index(fields=['success', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'Treinamento #{self.id} - {self.get_training_type_display()}'

    def save(self, *args, **kwargs):
        # Gera session_id automático se não fornecido
        if not self.session_id:
            timestamp = self.created_at.strftime('%Y%m%d_%H%M%S')
            user_id = self.trainer_user.id if self.trainer_user else 'system'
            self.session_id = f'train_{user_id}_{timestamp}'

        super().save(*args, **kwargs)

    @property
    def duration_display(self):
        """Retorna o tempo de resposta em formato legível."""
        if self.response_time:
            if self.response_time < 1000:
                return f'{self.response_time:.2f}ms'
            else:
                return f'{self.response_time / 1000:.2f}s'
        return 'N/A'

    @property
    def was_successful(self):
        """Indica se a sessão foi bem-sucedida."""
        return self.success and not self.error_message