"""
Serviço principal do chatbot literário.
Coordena todas as funcionalidades: processamento de mensagens, busca de conhecimento,
geração de respostas e analytics.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from cgbookstore.apps.chatbot_literario.models import (
    Conversation, Message, KnowledgeItem, ChatAnalytics, ConversationFeedback
)
from cgbookstore.apps.chatbot_literario.services.embeddings import embeddings_service
from cgbookstore.apps.chatbot_literario.services.ai_service import ollama_service

logger = logging.getLogger(__name__)


class FunctionalChatbotService:
    """
    Serviço principal do chatbot literário.
    Orquestra todos os componentes para gerar respostas inteligentes.
    """

    def __init__(self):
        self.max_context_messages = 5
        self.similarity_threshold = 0.7
        self.max_knowledge_items = 3

    def get_response(self, message: str, user: User = None, conversation_id: str = None) -> Dict[str, Any]:
        """
        Método wrapper para compatibilidade com views existentes.
        Chama process_message() internamente.

        Args:
            message: Texto da mensagem
            user: Usuário (pode ser None)
            conversation_id: ID da conversa (opcional)

        Returns:
            Dict com a resposta formatada
        """
        try:
            # Se não há usuário, criar um usuário temporário ou usar sistema
            if not user:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user, created = User.objects.get_or_create(
                    username='guest_user',
                    defaults={
                        'email': 'guest@cgbookstore.com',
                        'first_name': 'Usuário',
                        'last_name': 'Convidado'
                    }
                )

            # Chamar process_message com session_id baseado no conversation_id
            session_id = conversation_id if conversation_id else None

            result = self.process_message(
                user=user,
                message_text=message,
                session_id=session_id
            )

            # Formatar resposta para compatibilidade com view
            if result.get('success'):
                return {
                    'success': True,
                    'response': result['response'],
                    'conversation_id': result.get('conversation_id'),  # Usar conversation_id do process_message
                    'message_id': result.get('message_id'),
                    'knowledge_sources': [],  # Para compatibilidade
                    'response_metadata': {
                        'intent': result.get('intent'),
                        'confidence': result.get('confidence'),
                        'response_time': result.get('response_time'),
                        'knowledge_used': result.get('knowledge_used', 0)
                    }
                }
            else:
                return {
                    'success': False,
                    'response': result.get('error', 'Erro desconhecido'),
                    'error': result.get('details')
                }

        except Exception as e:
            logger.error(f"Erro no wrapper get_response: {str(e)}")
            return {
                'success': False,
                'response': 'Desculpe, ocorreu um erro interno.',
                'error': str(e)
            }

    def get_user_personalization_data(self, user: User) -> Dict[str, Any]:
        """
        Obtém dados de personalização do usuário.
        Método para compatibilidade com views existentes.

        Args:
            user: Usuário

        Returns:
            Dict com dados de personalização
        """
        try:
            if not user or not user.is_authenticated:
                return {
                    'user_name': 'Visitante',
                    'total_conversations': 0,
                    'favorite_topics': [],
                    'is_guest': True
                }

            # Contar conversas do usuário
            total_conversations = Conversation.objects.filter(user=user).count()

            # Buscar tópicos mais frequentes (baseado em analytics)
            from django.db.models import Count
            top_intents = ChatAnalytics.objects.filter(
                user=user
            ).values('intent').annotate(
                count=Count('intent')
            ).order_by('-count')[:3]

            favorite_topics = [item['intent'] for item in top_intents if item['intent'] != 'unknown']

            return {
                'user_name': user.get_full_name() or user.username,
                'total_conversations': total_conversations,
                'favorite_topics': favorite_topics,
                'is_guest': False,
                'user_id': user.id
            }

        except Exception as e:
            logger.error(f"Erro ao obter dados de personalização: {str(e)}")
            return {
                'user_name': user.username if user else 'Visitante',
                'total_conversations': 0,
                'favorite_topics': [],
                'is_guest': not user or not user.is_authenticated,
                'error': str(e)
            }

    def submit_feedback_wrapper(self, message_id: int, rating: int, comment: str = None, user: User = None) -> bool:
        """
        Método wrapper para compatibilidade com views existentes.

        Args:
            message_id: ID da mensagem
            rating: Avaliação (1-5)
            comment: Comentário opcional
            user: Usuário que está dando feedback

        Returns:
            True se feedback foi salvo com sucesso
        """
        return self.submit_feedback(
            user=user,
            message_id=message_id,
            rating=rating,
            feedback_text=comment
        )

    def process_message(self, user: User, message_text: str, session_id: str = None) -> Dict[str, Any]:
        """
        Processa uma mensagem do usuário e retorna a resposta do chatbot.

        Args:
            user: Usuário que enviou a mensagem
            message_text: Texto da mensagem
            session_id: ID da sessão (opcional)

        Returns:
            Dict com a resposta e metadados
        """
        start_time = time.time()

        try:
            # 1. Criar ou recuperar conversa
            conversation = self._get_or_create_conversation(user, session_id)

            # 2. Salvar mensagem do usuário
            user_message = self._save_user_message(conversation, message_text)

            # 3. Classificar intenção (simplificado)
            intent_data = self._classify_simple_intent(message_text)

            # 4. Buscar conhecimento relevante
            knowledge_items = self._search_knowledge(message_text)

            # 5. Construir contexto da conversa
            context = self._build_conversation_context(conversation)

            # 6. Gerar resposta via IA
            response_text = self._generate_ai_response(
                user_message=message_text,
                context=context,
                knowledge_items=knowledge_items,
                intent_data=intent_data
            )

            # 7. Validar resposta (simplificado)
            validation_result = self._validate_simple_response(response_text)

            # 8. Salvar resposta do bot
            bot_message = self._save_bot_message(conversation, response_text)

            # 9. Calcular tempo de resposta
            response_time = time.time() - start_time

            # 10. Atualizar analytics
            self._update_analytics(
                user=user,
                session_id=session_id,
                intent=intent_data.get('intent', 'unknown'),
                response_time=response_time
            )

            # 11. Preparar resposta
            return {
                'success': True,
                'response': response_text,
                'conversation_id': conversation.id,
                'message_id': bot_message.id,
                'intent': intent_data.get('intent'),
                'confidence': intent_data.get('confidence', 0.0),
                'knowledge_used': len(knowledge_items),
                'response_time': round(response_time, 3),
                'validation': validation_result
            }

        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}", exc_info=True)

            # Analytics para erro
            self._update_analytics(
                user=user,
                session_id=session_id,
                intent='error',
                response_time=time.time() - start_time
            )

            return {
                'success': False,
                'error': 'Desculpe, ocorreu um erro interno. Tente novamente.',
                'details': str(e) if logger.isEnabledFor(logging.DEBUG) else None
            }

    def _get_or_create_conversation(self, user: User, session_id: str = None) -> Conversation:
        """Obtém conversa existente ou cria nova."""
        # Como não temos session_id no model, vamos usar a conversa mais recente
        # ou criar uma nova se necessário
        try:
            # Buscar conversa mais recente do usuário (últimas 24 horas)
            from datetime import timedelta
            recent_time = timezone.now() - timedelta(hours=24)

            conversation = Conversation.objects.filter(
                user=user,
                created_at__gte=recent_time
            ).order_by('-created_at').first()

            if conversation:
                return conversation
        except Exception:
            pass

        # Criar nova conversa usando apenas campos que existem
        conversation = Conversation.objects.create(
            user=user
        )

        logger.info(f"Nova conversa criada: {conversation.id} para usuário {user.id}")
        return conversation

    def _save_user_message(self, conversation: Conversation, text: str) -> Message:
        """Salva mensagem do usuário."""
        return Message.objects.create(
            conversation=conversation,
            sender='user',
            content=text,
            timestamp=timezone.now()
        )

    def _save_bot_message(self, conversation: Conversation, text: str) -> Message:
        """Salva mensagem do bot."""
        return Message.objects.create(
            conversation=conversation,
            sender='bot',
            content=text,
            timestamp=timezone.now()
        )

    def _search_knowledge(self, query: str) -> List[KnowledgeItem]:
        """
        Busca itens de conhecimento relevantes usando embeddings.

        Args:
            query: Texto da consulta

        Returns:
            Lista de itens de conhecimento ordenados por relevância
        """
        try:
            # Criar embedding da consulta
            query_embedding = embeddings_service.create_embedding(query)

            # Buscar todos os itens com embeddings
            all_items = KnowledgeItem.objects.filter(embedding__isnull=False)

            # Calcular similaridades manualmente
            similarities = []
            for item in all_items:
                try:
                    # Calcular similaridade usando o método do service
                    similarity = embeddings_service.calculate_similarity(
                        query_embedding,
                        item.embedding
                    )

                    # Apenas itens acima do threshold
                    if similarity >= self.similarity_threshold:
                        similarities.append((item, similarity))

                except Exception as e:
                    logger.debug(f"Erro ao calcular similaridade para item {item.id}: {str(e)}")
                    continue

            # Ordenar por similaridade (maior primeiro) e limitar resultados
            similarities.sort(key=lambda x: x[1], reverse=True)
            similar_items = [item for item, _ in similarities[:self.max_knowledge_items]]

            logger.info(f"Encontrados {len(similar_items)} itens de conhecimento para: {query[:50]}...")
            return similar_items

        except Exception as e:
            logger.error(f"Erro na busca de conhecimento: {str(e)}")
            return []

    def _build_conversation_context(self, conversation: Conversation) -> str:
        """
        Constrói contexto da conversa com mensagens recentes.

        Args:
            conversation: Objeto da conversa

        Returns:
            String com o contexto formatado
        """
        try:
            recent_messages = Message.objects.filter(
                conversation=conversation
            ).order_by('-timestamp')[:self.max_context_messages]

            context_parts = []
            for message in reversed(recent_messages):
                role = "Usuário" if message.sender == 'user' else "Assistente"
                context_parts.append(f"{role}: {message.content}")

            context = "\n".join(context_parts) if context_parts else ""

            logger.debug(f"Contexto construído com {len(recent_messages)} mensagens")
            return context

        except Exception as e:
            logger.error(f"Erro ao construir contexto: {str(e)}")
            return ""

    def _generate_ai_response(
            self,
            user_message: str,
            context: str,
            knowledge_items: List[KnowledgeItem],
            intent_data: Dict
    ) -> str:
        """
        Gera resposta usando lógica interna com contexto melhorado.

        Args:
            user_message: Mensagem do usuário
            context: Contexto da conversa
            knowledge_items: Itens de conhecimento relevantes
            intent_data: Dados da classificação de intenção

        Returns:
            Texto da resposta gerada
        """
        try:
            intent = intent_data.get('intent', 'general')

            # CORREÇÃO 1: Analisar contexto para perguntas sequenciais
            contextual_topic = self._extract_topic_from_context(context, user_message)

            # CORREÇÃO 2: Validar relevância dos resultados
            relevant_items = self._filter_relevant_knowledge(knowledge_items, user_message, contextual_topic)

            # Resposta baseada na intenção e conhecimento validado
            if intent == 'greeting':
                response = "Olá! Sou seu assistente literário especializado. Posso ajudá-lo com informações sobre livros, autores, resenhas e recomendações literárias. Como posso ajudá-lo hoje?"

            elif intent == 'question':
                if relevant_items:
                    # Usar o melhor item de conhecimento RELEVANTE
                    best_item = relevant_items[0]
                    response = f"Com base no meu conhecimento literário:\n\n📚 {best_item.question}\n\n{best_item.answer}"

                    if len(relevant_items) > 1:
                        response += f"\n\n💡 Encontrei {len(relevant_items)} informações relacionadas. Quer que eu detalhe mais algum aspecto específico?"

                elif contextual_topic:
                    # CORREÇÃO 3: Resposta honesta sobre o tópico do contexto
                    response = f"Você está perguntando sobre **{contextual_topic}**, mas infelizmente não encontrei essa informação específica em meu conhecimento atual. Posso tentar ajudar de outra forma ou você pode reformular a pergunta com mais detalhes?"

                else:
                    # Análise da pergunta para resposta mais inteligente
                    message_lower = user_message.lower()
                    if any(word in message_lower for word in ['data', 'quando', 'ano', 'lançamento', 'publicação']):
                        response = f"Você está perguntando sobre datas, mas preciso saber sobre qual livro ou autor específico. Pode me dar mais contexto sobre o que está procurando?"
                    elif any(word in message_lower for word in ['quem', 'autor', 'escritor']):
                        response = f"Para responder sobre '{user_message}', preciso de mais contexto. Você está perguntando sobre um autor específico, uma obra, ou características de algum período literário?"
                    elif any(word in message_lower for word in ['livro', 'obra', 'romance', 'poesia']):
                        response = f"Sua pergunta sobre '{user_message}' é interessante! Para dar uma resposta mais precisa, pode especificar o gênero, período ou autor que tem em mente?"
                    else:
                        response = f"Entendo que você está perguntando sobre '{user_message}'. Como assistente literário, posso ajudá-lo melhor se você especificar sobre livros, autores, períodos literários ou análises específicas."

            elif intent == 'recommendation':
                if relevant_items:
                    response = "Com base no seu interesse, posso sugerir:\n\n"
                    for i, item in enumerate(relevant_items[:2], 1):
                        response += f"📖 {i}. {item.question}\n{item.answer[:200]}...\n\n"
                    response += "Quer que eu detalhe alguma dessas sugestões?"
                else:
                    response = "Adoraria recomendar livros para você! Para dar sugestões mais personalizadas, me conte:\n\n• Que gêneros prefere? (ficção, romance, suspense, clássicos...)\n• Há algum autor que já admira?\n• Prefere leituras mais leves ou densas?\n• Algum tema específico de interesse?"

            elif intent == 'search':
                if relevant_items:
                    response = f"Encontrei {len(relevant_items)} informações relevantes:\n\n"
                    for i, item in enumerate(relevant_items, 1):
                        response += f"📚 {i}. **{item.question}**\n{item.answer[:300]}...\n\n"
                    response += "Quer que eu aprofunde algum desses tópicos?"
                else:
                    response = "Vou ajudá-lo a encontrar informações literárias! Pode ser mais específico sobre o que busca? Por exemplo:\n\n• 'livros de Machado de Assis'\n• 'características do Romantismo'\n• 'análise de Dom Casmurro'\n• 'autores contemporâneos brasileiros'"

            elif intent == 'thanks':
                response = "Fico muito feliz em ajudar com questões literárias! Se tiver mais dúvidas sobre livros, autores, análises ou qualquer tópico relacionado à literatura, estarei sempre aqui. Boa leitura! 📖✨"

            elif intent == 'goodbye':
                response = "Foi um prazer conversar sobre literatura com você! Até a próxima conversa literária. Que seus próximos livros sejam inesquecíveis! 📚✨"

            else:
                # Resposta geral inteligente baseada no conteúdo
                if relevant_items:
                    best_item = relevant_items[0]
                    response = f"Baseado na sua mensagem, encontrei isso:\n\n📚 **{best_item.question}**\n\n{best_item.answer}\n\nIsso responde sua questão ou você gostaria de saber mais sobre algum aspecto específico?"
                else:
                    # Análise básica da mensagem para resposta contextual
                    message_lower = user_message.lower()
                    if any(word in message_lower for word in ['ajuda', 'help', 'como']):
                        response = "Estou aqui para ajudá-lo com questões literárias! Posso:\n\n📖 Fornecer informações sobre autores e obras\n📚 Fazer recomendações de leitura\n✍️ Explicar movimentos e períodos literários\n🔍 Ajudar com análises de textos\n\nO que você gostaria de explorar?"
                    else:
                        response = f"Sua mensagem sobre '{user_message[:100]}...' é interessante! Como assistente literário especializado, posso ajudá-lo com informações sobre livros, autores, análises literárias e recomendações. Como posso ser mais útil especificamente?"

            # CORREÇÃO 4: Remover contexto redundante se a resposta já for completa
            final_response = response.strip()

            logger.info(f"Resposta contextual gerada com {len(final_response)} caracteres")
            return final_response

        except Exception as e:
            logger.error(f"Erro na geração de resposta: {str(e)}")
            return "Desculpe, ocorreu um erro interno. Como assistente literário, estarei aqui quando quiser tentar novamente! 📚"

    def _build_enhanced_prompt(
            self,
            user_message: str,
            knowledge_items: List[KnowledgeItem],
            intent_data: Dict
    ) -> str:
        """
        Constrói prompt enriquecido para a IA.

        Args:
            user_message: Mensagem do usuário
            knowledge_items: Itens de conhecimento relevantes
            intent_data: Dados da intenção classificada

        Returns:
            Prompt formatado
        """
        prompt_parts = [
            "Você é um assistente literário especializado. Responda de forma útil e precisa.",
            f"\nPergunta do usuário: {user_message}"
        ]

        # Adicionar intenção se disponível
        if intent_data.get('intent'):
            prompt_parts.append(f"\nIntenção detectada: {intent_data['intent']}")

        # Adicionar conhecimento relevante
        if knowledge_items:
            prompt_parts.append("\nInformações relevantes:")
            for idx, item in enumerate(knowledge_items, 1):
                prompt_parts.append(f"{idx}. P: {item.question}")
                prompt_parts.append(f"   R: {item.answer}")

        prompt_parts.append("\nResposta:")

        return "\n".join(prompt_parts)

    def _update_analytics(
            self,
            user: User,
            session_id: str,
            intent: str,
            response_time: float
    ) -> None:
        """
        Atualiza analytics da conversa.

        Args:
            user: Usuário
            session_id: ID da sessão
            intent: Intenção classificada
            response_time: Tempo de resposta em segundos
        """
        try:
            # CORREÇÃO: Usar apenas campos que existem no model ChatAnalytics
            ChatAnalytics.objects.create(
                user=user,
                session_id=session_id or f"session_{int(time.time())}",
                intent=intent,
                response_time=response_time,
                timestamp=timezone.now()
            )

            logger.debug(f"Analytics atualizado para usuário {user.id}")

        except Exception as e:
            logger.error(f"Erro ao atualizar analytics: {str(e)}")

    def _extract_topic_from_context(self, context: str, current_message: str) -> Optional[str]:
        """
        Extrai o tópico principal do contexto da conversa.

        Args:
            context: Contexto da conversa
            current_message: Mensagem atual do usuário

        Returns:
            Tópico principal ou None
        """
        try:
            if not context:
                return None

            # Procurar por tópicos literários mencionados recentemente
            context_lower = context.lower()
            current_lower = current_message.lower()

            # Palavras-chave que indicam referência temporal
            temporal_keywords = ['data', 'quando', 'ano', 'lançamento', 'publicação', 'escreveu', 'criou']
            is_temporal_question = any(keyword in current_lower for keyword in temporal_keywords)

            if is_temporal_question:
                # Buscar nomes de livros, autores ou obras no contexto recente
                import re

                # Padrões para identificar títulos e autores
                book_patterns = [
                    r'(?:livro|obra|romance)\s+([A-Z][^.!?]*)',
                    r'([A-Z][a-zA-Z\s]+(?:Assis|Tolkien|Shakespeare|Austen|Joyce|Hemingway))',  # Autores famosos
                    r'(?:O|A|Os|As)\s+([A-Z][a-zA-Z\s]+)',  # Títulos que começam com artigo
                    r'([A-Z][a-zA-Z\s]*(?:Hobbit|Casmurro|Sertão|Potter|Senhor))',  # Livros famosos
                ]

                for pattern in book_patterns:
                    matches = re.findall(pattern, context)
                    if matches:
                        # Retorna o match mais recente (último)
                        topic = matches[-1].strip()
                        if len(topic) > 2:  # Evitar matches muito curtos
                            logger.info(f"Tópico extraído do contexto: {topic}")
                            return topic

                # Buscar palavras capitalizadas (possíveis nomes próprios)
                words = context.split()
                capitalized_words = []
                for word in words[-20:]:  # Últimas 20 palavras
                    clean_word = re.sub(r'[^\w\s]', '', word)
                    if clean_word and clean_word[0].isupper() and len(clean_word) > 2:
                        capitalized_words.append(clean_word)

                if capitalized_words:
                    # Retorna a última palavra capitalizada encontrada
                    topic = capitalized_words[-1]
                    logger.info(f"Tópico extraído (palavra capitalizada): {topic}")
                    return topic

            return None

        except Exception as e:
            logger.error(f"Erro ao extrair tópico do contexto: {str(e)}")
            return None

    def _filter_relevant_knowledge(
            self,
            knowledge_items: List[KnowledgeItem],
            user_message: str,
            contextual_topic: str = None
    ) -> List[KnowledgeItem]:
        """
        Filtra itens de conhecimento por relevância real.

        Args:
            knowledge_items: Lista de itens encontrados
            user_message: Mensagem do usuário
            contextual_topic: Tópico do contexto (opcional)

        Returns:
            Lista filtrada de itens relevantes
        """
        try:
            if not knowledge_items:
                return []

            relevant_items = []
            message_lower = user_message.lower()

            # Palavras-chave da mensagem
            message_keywords = set(message_lower.split())

            # Adicionar tópico contextual às palavras-chave
            if contextual_topic:
                contextual_keywords = set(contextual_topic.lower().split())
                message_keywords.update(contextual_keywords)

            for item in knowledge_items:
                # Verificar relevância baseada em palavras-chave
                item_text = f"{item.question} {item.answer}".lower()
                item_keywords = set(item_text.split())

                # Calcular interseção de palavras-chave
                common_keywords = message_keywords.intersection(item_keywords)

                # Filtros de relevância
                relevance_score = 0

                # Pontuação por palavras-chave comuns
                relevance_score += len(common_keywords) * 1

                # Bonus para correspondências exatas de tópico contextual
                if contextual_topic and contextual_topic.lower() in item_text:
                    relevance_score += 10

                # Bonus para correspondências de nomes próprios
                import re
                proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', user_message)
                for noun in proper_nouns:
                    if noun.lower() in item_text:
                        relevance_score += 5

                # Penalização para respostas muito genéricas
                generic_phrases = ['posso ajudar', 'mais informações', 'entre em contato']
                if any(phrase in item_text for phrase in generic_phrases):
                    relevance_score -= 2

                # Filtro mínimo de relevância
                if relevance_score >= 2:
                    relevant_items.append((item, relevance_score))

            # Ordenar por relevância
            relevant_items.sort(key=lambda x: x[1], reverse=True)

            # Retornar apenas os itens (sem score)
            filtered_items = [item for item, score in relevant_items]

            logger.info(f"Filtrados {len(filtered_items)} itens relevantes de {len(knowledge_items)} originais")
            return filtered_items

        except Exception as e:
            logger.error(f"Erro ao filtrar conhecimento relevante: {str(e)}")
            return knowledge_items  # Retorna lista original em caso de erro

    def _classify_simple_intent(self, message_text: str) -> Dict[str, Any]:
        """
        Classificação simples de intenção baseada em palavras-chave.

        Args:
            message_text: Texto da mensagem

        Returns:
            Dict com intent e confidence
        """
        message_lower = message_text.lower()

        # Palavras-chave para diferentes intenções
        intent_keywords = {
            'question': ['o que', 'como', 'quando', 'onde', 'por que', 'qual', '?'],
            'recommendation': ['recomende', 'sugira', 'indique', 'recomendação'],
            'search': ['buscar', 'procurar', 'encontrar', 'achar'],
            'greeting': ['olá', 'oi', 'bom dia', 'boa tarde', 'boa noite'],
            'thanks': ['obrigado', 'obrigada', 'valeu', 'muito obrigado'],
            'goodbye': ['tchau', 'até logo', 'adeus', 'despedida']
        }

        # Verificar cada intenção
        for intent, keywords in intent_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return {
                        'intent': intent,
                        'confidence': 0.8
                    }

        # Intenção padrão
        return {
            'intent': 'general',
            'confidence': 0.5
        }

    def _validate_simple_response(self, response_text: str) -> Dict[str, Any]:
        """
        Validação simples da resposta gerada.

        Args:
            response_text: Texto da resposta

        Returns:
            Dict com resultado da validação
        """
        # Verificações básicas
        is_valid = True
        issues = []

        # Verificar se resposta não está vazia
        if not response_text or len(response_text.strip()) < 5:
            is_valid = False
            issues.append("Resposta muito curta")

        # Verificar se não é muito longa
        if len(response_text) > 2000:
            issues.append("Resposta muito longa")

        # Verificar se contém caracteres especiais problemáticos
        problematic_chars = ['<script', '<?php', 'javascript:']
        for char in problematic_chars:
            if char in response_text.lower():
                is_valid = False
                issues.append("Conteúdo suspeito detectado")
                break

        return {
            'is_valid': is_valid,
            'issues': issues,
            'score': 1.0 if is_valid else 0.5
        }

    def get_conversation_history(
            self,
            user: User,
            conversation_id: int = None,
            session_id: str = None,
            limit: int = 50
    ) -> List[Dict]:
        """
        Recupera histórico de conversa.

        Args:
            user: Usuário
            conversation_id: ID da conversa específica (opcional)
            session_id: ID da sessão (opcional)
            limit: Limite de mensagens

        Returns:
            Lista de mensagens formatadas
        """
        try:
            filters = {'conversation__user': user}

            if conversation_id:
                filters['conversation_id'] = conversation_id
            elif session_id:
                filters['conversation__session_id'] = session_id

            messages = Message.objects.filter(**filters).order_by('-timestamp')[:limit]

            return [
                {
                    'id': msg.id,
                    'sender': msg.sender,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'conversation_id': msg.conversation.id
                }
                for msg in reversed(messages)
            ]

        except Exception as e:
            logger.error(f"Erro ao recuperar histórico: {str(e)}")
            return []

    def submit_feedback(
            self,
            user: User,
            message_id: int,
            rating: int,
            feedback_text: str = None
    ) -> bool:
        """
        Submete feedback sobre uma resposta.

        Args:
            user: Usuário que está dando feedback
            message_id: ID da mensagem avaliada
            rating: Avaliação (1-5)
            feedback_text: Comentário opcional

        Returns:
            True se feedback foi salvo com sucesso
        """
        try:
            # Verificar se mensagem existe e pertence ao usuário
            message = Message.objects.get(
                id=message_id,
                conversation__user=user,
                sender='bot'
            )

            # CORREÇÃO: Usar campos corretos do ConversationFeedback
            feedback, created = ConversationFeedback.objects.get_or_create(
                conversation=message.conversation,
                user=user,
                defaults={
                    'rating': rating,
                    'feedback_text': feedback_text or '',
                    'created_at': timezone.now()
                }
            )

            if not created:
                # Atualizar feedback existente
                feedback.rating = rating
                feedback.feedback_text = feedback_text or ''
                feedback.save()

            logger.info(f"Feedback salvo para mensagem {message_id} por usuário {user.id}")
            return True

        except Message.DoesNotExist:
            logger.warning(f"Mensagem {message_id} não encontrada para usuário {user.id}")
            return False
        except Exception as e:
            logger.error(f"Erro ao salvar feedback: {str(e)}")
            return False

    def get_user_analytics(self, user: User, days: int = 30) -> Dict[str, Any]:
        """
        Recupera analytics do usuário.

        Args:
            user: Usuário
            days: Número de dias para análise

        Returns:
            Dicionário com estatísticas
        """
        try:
            from datetime import timedelta

            start_date = timezone.now() - timedelta(days=days)

            # Buscar analytics do período
            analytics = ChatAnalytics.objects.filter(
                user=user,
                timestamp__gte=start_date
            )

            total_interactions = analytics.count()

            if total_interactions == 0:
                return {
                    'total_interactions': 0,
                    'average_response_time': 0,
                    'top_intents': [],
                    'daily_usage': []
                }

            # Calcular métricas
            avg_response_time = analytics.aggregate(
                avg_time=models.Avg('response_time')
            )['avg_time'] or 0

            # Top intenções
            from django.db.models import Count
            top_intents = list(analytics.values('intent').annotate(
                count=Count('intent')
            ).order_by('-count')[:5])

            return {
                'total_interactions': total_interactions,
                'average_response_time': round(avg_response_time, 3),
                'top_intents': top_intents,
                'period_days': days
            }

        except Exception as e:
            logger.error(f"Erro ao recuperar analytics: {str(e)}")
            return {'error': str(e)}

    def end_conversation(self, user: User, conversation_id: int = None, session_id: str = None) -> bool:
        """
        Finaliza uma conversa.
        Como o model não tem campos de controle de estado, apenas retorna True.

        Args:
            user: Usuário
            conversation_id: ID da conversa (opcional)
            session_id: ID da sessão (opcional)

        Returns:
            True sempre (compatibilidade)
        """
        try:
            # Como não temos campos de controle de estado no model,
            # apenas log da ação
            logger.info(f"Conversa finalizada para usuário {user.id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao finalizar conversa: {str(e)}")
            return False


# Instância global do serviço
functional_chatbot = FunctionalChatbotService()