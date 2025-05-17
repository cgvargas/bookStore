import json
import os
import logging
import datetime
import traceback

from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone

# Importar o modelo SentenceTransformer se estiver disponível
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Importar métricas de similaridade
try:
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Importar os modelos
from ..models import KnowledgeItem, Message, ConversationFeedback

logger = logging.getLogger(__name__)


class TrainingService:
    """
    Serviço responsável pelo gerenciamento da base de conhecimento do chatbot
    e pelo treinamento contínuo com base no feedback dos usuários.
    """

    def __init__(self):
        self.initialized = False
        self.embedding_model = None
        self.embedding_dim = 384  # Dimensão padrão para o modelo all-MiniLM-L6-v2

        # Caminho para arquivos legados (para migração)
        self.data_dir = os.path.join(settings.BASE_DIR, 'cgbookstore', 'apps', 'chatbot_literario', 'data')
        self.knowledge_file = os.path.join(self.data_dir, 'knowledge_base.json')
        self.conversations_file = os.path.join(self.data_dir, 'conversations.json')

    def initialize(self):
        """Inicializa o serviço de treinamento e carrega o modelo de embeddings."""
        if self.initialized:
            return

        # Verificar se o diretório de dados existe (para migração)
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Inicializar modelo de embeddings se disponível
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info("Inicializando modelo de embeddings...")
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Modelo de embeddings inicializado com sucesso.")
            except Exception as e:
                logger.error(f"Erro ao inicializar modelo de embeddings: {str(e)}")
                self.embedding_model = None
        else:
            logger.warning("Biblioteca sentence-transformers não encontrada. Embeddings não estarão disponíveis.")
            self.embedding_model = None

        # Migrar dados legados, se existirem
        self._migrate_legacy_data()

        self.initialized = True
        logger.info("Serviço de treinamento inicializado com sucesso.")

    def _migrate_legacy_data(self):
        """Migra dados de arquivos JSON para o banco de dados, se necessário."""
        # Verificar se existem itens no banco de dados
        if KnowledgeItem.objects.exists():
            return

        # Verificar se o arquivo de conhecimento existe
        if os.path.exists(self.knowledge_file):
            try:
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    knowledge_base = json.load(f)

                # Importar itens para o banco de dados
                count = 0
                for item in knowledge_base:
                    # Verificar se o item já existe
                    existing = KnowledgeItem.objects.filter(
                        question=item['question'],
                        answer=item.answer
                    ).first()

                    if not existing:
                        # Converter embedding se existir
                        embedding = item.get('embedding')

                        # Criar novo item
                        KnowledgeItem.objects.create(
                            question=item['question'],
                            answer=item.answer,
                            category=item.get('category', 'geral'),
                            source=item.get('source', 'migração'),
                            embedding=embedding
                        )
                        count += 1

                logger.info(f"Migrados {count} itens de conhecimento para o banco de dados.")
            except Exception as e:
                logger.error(f"Erro ao migrar base de conhecimento: {str(e)}")

    def add_knowledge_item(self, question, answer, category='geral', source='manual'):
        """
        Adiciona um novo item à base de conhecimento.

        Args:
            question (str): A pergunta do usuário
            answer (str): A resposta do chatbot
            category (str): Categoria do conhecimento (ex: livros, autores, navegação)
            source (str): Fonte do conhecimento (ex: manual, conversa, importação)

        Returns:
            bool: True se o item foi adicionado com sucesso, False caso contrário
        """
        if not self.initialized:
            self.initialize()

        try:
            # Verificar se já existe item similar
            existing = KnowledgeItem.objects.filter(
                question=question,
                answer=answer
            ).first()

            if existing:
                # Atualizar item existente
                existing.category = category
                existing.source = source
                existing.updated_at = timezone.now()
                existing.save()
                logger.info(f"Item de conhecimento atualizado: {question[:30]}...")
                return True

            # Gerar embedding se o modelo estiver disponível
            embedding = None
            if self.embedding_model:
                try:
                    embedding = self.embedding_model.encode(question).tolist()
                except Exception as e:
                    logger.error(f"Erro ao gerar embedding: {str(e)}")

            # Criar novo item
            KnowledgeItem.objects.create(
                question=question,
                answer=answer,
                category=category,
                source=source,
                embedding=embedding
            )

            logger.info(f"Novo item de conhecimento adicionado: {question[:30]}...")
            return True

        except Exception as e:
            logger.error(f"Erro ao adicionar item de conhecimento: {str(e)}")
            return False

    def add_conversation(self, user_input, bot_response):
        """
        Registra uma conversa entre usuário e chatbot para fins de treinamento.

        Args:
            user_input (str): Mensagem do usuário
            bot_response (str): Resposta do chatbot
        """
        if not self.initialized:
            self.initialize()

        # Este método não precisa mais salvar em arquivo, pois as conversas
        # já são salvas no banco de dados pelos controladores/views
        pass

    def add_feedback(self, message_id, feedback_data):
        """
        Adiciona feedback a uma mensagem específica do chatbot.

        Args:
            message_id (int): ID da mensagem
            feedback_data (dict): Dados do feedback (helpful, comment)
        """
        try:
            message = Message.objects.filter(id=message_id, sender='bot').first()
            if not message:
                logger.warning(f"Mensagem não encontrada para feedback: {message_id}")
                return False

            # Verificar se já existe feedback para esta mensagem
            existing = ConversationFeedback.objects.filter(message=message).first()
            if existing:
                # Atualizar feedback existente
                existing.helpful = feedback_data.get('helpful', False)
                existing.comment = feedback_data.get('comment', '')
                existing.save()
            else:
                # Criar novo feedback
                ConversationFeedback.objects.create(
                    message=message,
                    helpful=feedback_data.get('helpful', False),
                    comment=feedback_data.get('comment', '')
                )

            return True

        except Exception as e:
            logger.error(f"Erro ao adicionar feedback: {str(e)}")
            return False

    def search_knowledge_base(self, query, threshold=0.7, max_results=5):
        """
        Busca na base de conhecimento por itens relevantes para a consulta.

        Args:
            query (str): A pergunta do usuário
            threshold (float): Limiar mínimo de similaridade (0-1)
            max_results (int): Número máximo de resultados

        Returns:
            list: Lista de tuplas (item, score) ordenadas por relevância
        """
        if not self.initialized:
            self.initialize()

        # Buscar apenas itens ativos
        knowledge_items = KnowledgeItem.objects.filter(active=True)

        if not knowledge_items:
            logger.warning("Base de conhecimento vazia.")
            return []

        # Debug: Verificar quantos itens estão sendo considerados
        logger.debug(f"Buscando em {knowledge_items.count()} itens de conhecimento ativos")

        # Se temos o modelo de embeddings e suporte a sklearn
        if self.embedding_model and SKLEARN_AVAILABLE:
            try:
                # Gerar embedding para a consulta
                query_embedding = self.embedding_model.encode(query)

                # Obter itens com embeddings
                items_with_embeddings = []
                items_embeddings = []

                for item in knowledge_items:
                    # Verificar se o embedding é válido
                    if item.embedding and isinstance(item.embedding, (list, tuple)) and len(item.embedding) > 0:
                        try:
                            # Verificar se é possível converter para numpy array
                            embedding_array = np.array(item.embedding)
                            if embedding_array.shape[0] == self.embedding_dim:
                                items_with_embeddings.append(item)
                                items_embeddings.append(embedding_array)
                        except Exception as e:
                            logger.warning(f"Erro ao processar embedding do item {item.id}: {str(e)}")

                # Debug: Verificar quantos itens têm embeddings válidos
                logger.debug(f"Encontrados {len(items_with_embeddings)} itens com embeddings válidos")

                if not items_with_embeddings:
                    logger.warning("Nenhum item com embedding válido encontrado.")
                    # Fallback para busca simples
                else:
                    # Calcular similaridades
                    similarities = cosine_similarity([query_embedding], items_embeddings)[0]

                    # Combinar itens com suas similaridades
                    results = list(zip(items_with_embeddings, similarities))

                    # Filtrar por threshold e ordenar por similaridade
                    filtered_results = [(item, score) for item, score in results if score >= threshold]
                    filtered_results.sort(key=lambda x: x[1], reverse=True)

                    # Limitar número de resultados
                    limited_results = filtered_results[:max_results]

                    # Debug: Mostrar os resultados
                    for item, score in limited_results:
                        logger.debug(f"Match: {item.question[:30]}... (Score: {score:.4f})")

                    if limited_results:
                        return limited_results

            except Exception as e:
                logger.error(f"Erro ao buscar com embeddings: {str(e)}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
                # Fallback para busca simples

        # Busca simples por palavras-chave (fallback)
        logger.info("Realizando busca simples por palavras-chave.")
        words = query.lower().split()
        results = []

        for item in knowledge_items:
            # Calcular pontuação simples baseada em palavras correspondentes
            question_lower = item.question.lower()
            score = sum(1 for word in words if word in question_lower) / len(words)

            if score >= threshold:
                results.append((item, score))

        # Ordenar resultados por pontuação
        results.sort(key=lambda x: x[1], reverse=True)

        # Debug: Mostrar os resultados da busca simples
        for item, score in results[:max_results]:
            logger.debug(f"Match (simples): {item.question[:30]}... (Score: {score:.4f})")

        return results[:max_results]

    def generate_training_statistics(self):
        """
        Gera estatísticas sobre a base de conhecimento e treinamento.

        Returns:
            dict: Estatísticas sobre o treinamento
        """
        if not self.initialized:
            self.initialize()

        try:
            # Estatísticas da base de conhecimento
            total_knowledge = KnowledgeItem.objects.count()
            active_knowledge = KnowledgeItem.objects.filter(active=True).count()

            # Distribuição por categoria
            category_counts = KnowledgeItem.objects.values('category') \
                .annotate(count=Count('id')) \
                .order_by('-count')

            # Distribuição por fonte
            source_counts = KnowledgeItem.objects.values('source') \
                .annotate(count=Count('id')) \
                .order_by('-count')

            # Estatísticas de conversas
            total_conversations = Message.objects.filter(sender='user').count()

            # Estatísticas de feedback
            total_feedback = ConversationFeedback.objects.count()
            positive_feedback = ConversationFeedback.objects.filter(helpful=True).count()
            negative_feedback = total_feedback - positive_feedback

            # Taxa de satisfação (se houver feedback)
            satisfaction_rate = 0
            if total_feedback > 0:
                satisfaction_rate = (positive_feedback / total_feedback) * 100

            # Conhecimento adicionado recentemente
            recent_knowledge = KnowledgeItem.objects.filter(
                created_at__gte=timezone.now() - datetime.timedelta(days=30)
            ).count()

            # Conhecimento com embeddings vs. sem embeddings
            with_embeddings = KnowledgeItem.objects.filter(embedding__isnull=False).count()
            without_embeddings = total_knowledge - with_embeddings

            return {
                'total_knowledge': total_knowledge,
                'active_knowledge': active_knowledge,
                'categories': list(category_counts),
                'sources': list(source_counts),
                'total_conversations': total_conversations,
                'total_feedback': total_feedback,
                'positive_feedback': positive_feedback,
                'negative_feedback': negative_feedback,
                'satisfaction_rate': satisfaction_rate,
                'recent_knowledge': recent_knowledge,
                'with_embeddings': with_embeddings,
                'without_embeddings': without_embeddings,
                'embeddings_available': SENTENCE_TRANSFORMERS_AVAILABLE,
                'sklearn_available': SKLEARN_AVAILABLE
            }

        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas: {str(e)}")
            return {
                'error': str(e)
            }

    def update_embeddings(self, batch_size=100):
        """
        Atualiza os embeddings para itens da base de conhecimento que não os possuem.

        Args:
            batch_size (int): Tamanho do lote para processamento

        Returns:
            int: Número de itens atualizados
        """
        if not self.initialized:
            self.initialize()

        if not self.embedding_model:
            logger.warning("Modelo de embeddings não disponível.")
            return 0

        try:
            # Obter itens sem embeddings
            items_without_embeddings = KnowledgeItem.objects.filter(
                Q(embedding__isnull=True) | Q(embedding={})
            ).order_by('id')[:batch_size]

            updated_count = 0

            for item in items_without_embeddings:
                try:
                    # Gerar embedding
                    embedding = self.embedding_model.encode(item.question).tolist()

                    # Atualizar item
                    item.embedding = embedding
                    item.save(update_fields=['embedding'])

                    updated_count += 1

                except Exception as e:
                    logger.error(f"Erro ao gerar embedding para item {item.id}: {str(e)}")
                    continue

            logger.info(f"Atualizados {updated_count} embeddings.")
            return updated_count

        except Exception as e:
            logger.error(f"Erro ao atualizar embeddings: {str(e)}")
            return 0

    def get_conversations_with_metadata(self, limit=50):
        """
        Obtém conversas recentes com metadados adicionais.

        Args:
            limit (int): Número máximo de conversas a retornar

        Returns:
            list: Lista de conversas com metadados
        """
        # Esta função é útil para o painel de treinamento
        conversations = []

        # Obter mensagens de usuário mais recentes
        user_messages = Message.objects.filter(sender='user').order_by('-timestamp')[:limit]

        for user_msg in user_messages:
            try:
                # Obter resposta do bot (se existir)
                bot_response = Message.objects.filter(
                    conversation=user_msg.conversation,
                    sender='bot',
                    timestamp__gt=user_msg.timestamp
                ).order_by('timestamp').first()

                if bot_response:
                    # Verificar se há feedback
                    feedback = ConversationFeedback.objects.filter(message=bot_response).first()

                    conversations.append({
                        'user_input': user_msg.content,
                        'bot_response': bot_response.content,
                        'timestamp': user_msg.timestamp,
                        'user': {'username': user_msg.conversation.user.username},
                        'feedback': {
                            'helpful': feedback.helpful if feedback else None,
                            'comment': feedback.comment if feedback else None
                        } if feedback else None
                    })
            except Exception as e:
                logger.error(f"Erro ao processar conversa: {str(e)}")
                continue

        return conversations


# Instância singleton do serviço
training_service = TrainingService()