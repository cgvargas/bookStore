# cgbookstore/apps/chatbot_literario/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone

User = get_user_model()


class Conversation(models.Model):
    """
    Modelo para armazenar conversas do chatbot literário.
    Mantém ID original para compatibilidade com dados existentes.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chatbot_conversations'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    title = models.CharField(max_length=200, blank=True, default="Nova Conversa")

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Conversa"
        verbose_name_plural = "Conversas"

    def __str__(self):
        return f"Conversa {self.id} - {self.user.username} ({self.started_at.strftime('%d/%m/%Y %H:%M')})"

    def deactivate(self):
        """Desativa a conversa"""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def activate(self):
        """Reativa a conversa"""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


class Message(models.Model):
    """
    Modelo para armazenar mensagens individuais de uma conversa.
    Mantém ID original para compatibilidade.
    """
    ROLE_CHOICES = [
        ('user', 'Usuário'),
        ('assistant', 'Assistente'),
        ('system', 'Sistema'),
    ]

    SOURCE_CHOICES = [
        ('ai', 'IA'),
        ('knowledge_base', 'Base de Conhecimento'),
        ('hybrid', 'Híbrido'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='ai')

    # Metadados de resposta (opcionais para compatibilidade)
    response_time = models.FloatField(null=True, blank=True, help_text="Tempo de resposta em segundos")
    model_used = models.CharField(max_length=50, blank=True, help_text="Modelo usado para gerar a resposta")
    token_count = models.IntegerField(null=True, blank=True, help_text="Número de tokens da resposta")

    class Meta:
        ordering = ['timestamp']
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..." if len(self.content) > 50 else f"{self.role}: {self.content}"

    # Compatibilidade com functional_chatbot.py
    @property
    def sender(self):
        """Propriedade para compatibilidade com código existente"""
        return self.role


class ConversationFeedback(models.Model):
    """
    Modelo para armazenar feedback das conversas.
    """
    RATING_CHOICES = [
        (1, '⭐'),
        (2, '⭐⭐'),
        (3, '⭐⭐⭐'),
        (4, '⭐⭐⭐⭐'),
        (5, '⭐⭐⭐⭐⭐'),
    ]

    conversation = models.OneToOneField(
        Conversation,
        on_delete=models.CASCADE,
        related_name='feedback',
        null=True, blank=True
    )
    rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"

    def __str__(self):
        rating_display = dict(self.RATING_CHOICES).get(self.rating, 'Sem nota')
        return f"Feedback - {rating_display} - {self.conversation.user.username if self.conversation else 'Sem conversa'}"


class KnowledgeItem(models.Model):
    """
    Modelo para item de conhecimento da base literária.
    ✅ CORRIGIDO: Compatível com training_service.py e embeddings_service.py
    """
    CONTENT_TYPE_CHOICES = [
        ('book', 'Livro'),
        ('author', 'Autor'),
        ('genre', 'Gênero'),
        ('movement', 'Movimento Literário'),
        ('analysis', 'Análise'),
        ('quote', 'Citação'),
        ('biography', 'Biografia'),
        ('context', 'Contexto Histórico'),
        ('geral', 'Geral'),  # Para compatibilidade com training_service
    ]

    # ✅ CAMPOS PARA TRAINING_SERVICE.PY (OBRIGATÓRIOS)
    question = models.CharField(
        max_length=500,
        help_text="Pergunta ou tópico principal",
        db_index=True,
        default="Tópico a ser definido"  # Valor padrão para migração
    )
    answer = models.TextField(
        help_text="Resposta ou conteúdo detalhado",
        default="Conteúdo a ser preenchido"  # Valor padrão para migração
    )
    category = models.CharField(
        max_length=50,
        choices=CONTENT_TYPE_CHOICES,
        default='geral',
        help_text="Categoria do conhecimento"
    )
    source = models.CharField(
        max_length=200,
        blank=True,
        default="knowledge_base",  # Valor padrão para migração
        help_text="Fonte da informação"
    )
    confidence = models.FloatField(
        default=1.0,
        help_text="Nível de confiança (0.0 a 1.0)"
    )
    active = models.BooleanField(
        default=True,
        help_text="Item ativo na base de conhecimento"
    )

    # ✅ CAMPOS PARA EMBEDDINGS_SERVICE.PY (OBRIGATÓRIOS)
    embedding = models.JSONField(
        null=True,
        blank=True,
        help_text="Vetor de embedding para busca semântica"
    )

    # ✅ CAMPOS EXISTENTES MANTIDOS (COMPATIBILIDADE)
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Título alternativo (compatibilidade)"
    )
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='book',
        help_text="Tipo de conteúdo (compatibilidade)"
    )
    content = models.TextField(
        blank=True,
        help_text="Conteúdo adicional (compatibilidade)"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados adicionais"
    )
    embedding_vector = models.JSONField(
        null=True,
        blank=True,
        help_text="Vetor de embedding alternativo (compatibilidade)"
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags para categorização"
    )

    # ✅ CAMPOS DE CONTROLE
    is_active = models.BooleanField(default=True)  # Compatibilidade
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Item de Conhecimento"
        verbose_name_plural = "Itens de Conhecimento"
        indexes = [
            models.Index(fields=['category', 'active']),
            models.Index(fields=['question']),
            models.Index(fields=['content_type', 'is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_category_display()}: {self.question[:50]}..."

    def save(self, *args, **kwargs):
        """
        ✅ SINCRONIZAÇÃO AUTOMÁTICA: Garante compatibilidade entre campos
        ✅ MIGRAÇÃO INTELIGENTE: Popula campos automaticamente
        """
        # Sincronizar campos para compatibilidade
        if not self.title and self.question:
            self.title = self.question[:200]
        elif not self.question and self.title:
            self.question = self.title[:500]

        if not self.content and self.answer:
            self.content = self.answer
        elif not self.answer and self.content:
            self.answer = self.content

        if not self.category and self.content_type:
            self.category = self.content_type
        elif not self.content_type and self.category:
            self.content_type = self.category

        # Garantir valores padrão para campos obrigatórios
        if not self.question:
            self.question = self.title or "Tópico a ser definido"

        if not self.answer:
            self.answer = self.content or "Conteúdo a ser preenchido"

        if not self.source:
            self.source = "knowledge_base"

        # Sincronizar campos active
        if self.active != self.is_active:
            self.is_active = self.active

        # Sincronizar embeddings
        if self.embedding and not self.embedding_vector:
            self.embedding_vector = self.embedding
        elif self.embedding_vector and not self.embedding:
            self.embedding = self.embedding_vector

        super().save(*args, **kwargs)

    # ✅ PROPRIEDADES PARA COMPATIBILIDADE COM TRAINING_SERVICE
    @property
    def confidence_base(self):
        """Alias para compatibilidade"""
        return self.confidence

    @confidence_base.setter
    def confidence_base(self, value):
        """Setter para compatibilidade"""
        self.confidence = value


class TrainingSession(models.Model):
    """
    Modelo para sessões de treinamento do chatbot.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('running', 'Executando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
        ('cancelled', 'Cancelado'),
    ]

    name = models.CharField(max_length=200, default="Sessão de Treinamento", help_text="Nome da sessão de treinamento")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Configurações do treinamento
    items_trained = models.IntegerField(default=0, help_text="Número de itens processados")
    items_total = models.IntegerField(default=0, help_text="Total de itens para processar")

    # Resultados e métricas (opcionais)
    accuracy_score = models.FloatField(null=True, blank=True, help_text="Score de acurácia")
    embeddings_generated = models.IntegerField(default=0, help_text="Embeddings gerados")
    processing_time = models.FloatField(null=True, blank=True, help_text="Tempo de processamento em segundos")

    # Logs e erros (opcionais)
    log_data = models.JSONField(default=dict, blank=True, help_text="Logs do treinamento")
    error_message = models.TextField(blank=True, default="", help_text="Mensagem de erro se houver")

    # Timestamps com valores padrão para migração
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Sessão de Treinamento"
        verbose_name_plural = "Sessões de Treinamento"

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"

    @property
    def progress_percentage(self):
        """Calcula a porcentagem de progresso"""
        if self.items_total == 0:
            return 0
        return (self.items_trained / self.items_total) * 100

    def mark_as_running(self):
        """Marca a sessão como executando"""
        self.status = 'running'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])

    def mark_as_completed(self, accuracy_score=None, embeddings_count=0):
        """Marca a sessão como concluída"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.accuracy_score = accuracy_score
        self.embeddings_generated = embeddings_count
        if self.started_at:
            processing_delta = self.completed_at - self.started_at
            self.processing_time = processing_delta.total_seconds()
        self.save(update_fields=['status', 'completed_at', 'accuracy_score', 'embeddings_generated', 'processing_time'])

    def mark_as_failed(self, error_message):
        """Marca a sessão como falhou"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'completed_at'])


class ChatbotConfiguration(models.Model):
    """
    Modelo para configurações do chatbot.
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(default="")
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração do Chatbot"
        verbose_name_plural = "Configurações do Chatbot"

    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."


class ConversationSummary(models.Model):
    """
    Modelo para resumos de conversas (para otimização de performance).
    """
    conversation = models.OneToOneField(
        Conversation,
        on_delete=models.CASCADE,
        related_name='summary'
    )
    summary_text = models.TextField(default="")
    key_topics = models.JSONField(default=list, blank=True)
    sentiment = models.CharField(max_length=20, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Resumo da Conversa"
        verbose_name_plural = "Resumos das Conversas"

    def __str__(self):
        return f"Resumo - {self.conversation.user.username} - {self.created_at.strftime('%d/%m/%Y')}"