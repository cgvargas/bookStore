# cgbookstore/apps/chatbot_literario/services/functional_chatbot.py

import logging
import re
from typing import List, Any, Dict, Optional
from django.db.models import Q

logger = logging.getLogger(__name__)


class FunctionalChatbot:
    """
    Chatbot "stateless" que usa o banco de dados para manter o contexto.
    ✅ CORRIGIDO: Compatível com sistema de inicialização atual
    """

    def __init__(self, training_service: Any = None):
        self.training_service = training_service
        self.max_history_pairs = 5

        # Log do status de inicialização
        if self.training_service:
            logger.info("✅ FunctionalChatbot inicializado com training_service ativo")
        else:
            logger.warning("⚠️ FunctionalChatbot inicializado sem training_service (modo limitado)")

    def get_response(self, user_message: str, conversation: 'Conversation') -> Dict[str, Any]:
        """
        ✅ CORRIGIDO: Melhor tratamento de erros e sistema híbrido
        """
        logger.info(f"📨 Processando mensagem para conversation_id '{conversation.id}': {user_message[:100]}...")

        try:
            # Carregar histórico da conversa
            history = self._load_history_from_db(conversation)
            logger.debug(f"📚 Histórico carregado: {len(history)} mensagens")

            # Buscar conhecimento relevante
            relevant_knowledge = self._get_relevant_knowledge(user_message)
            logger.debug(f"🧠 Conhecimento relevante: {len(relevant_knowledge)} itens")

            # Construir prompt para IA
            messages_for_ai = self._build_chat_prompt(user_message, history, relevant_knowledge)
            logger.debug(f"💬 Prompt construído: {len(messages_for_ai)} mensagens")

            # Gerar resposta com IA
            from .ai_service import ai_service
            ai_response = ai_service.generate_response(messages_for_ai)

            # Adicionar metadados sobre o sistema híbrido
            if relevant_knowledge:
                ai_response['source'] = 'hybrid'
                ai_response['knowledge_items_used'] = len(relevant_knowledge)
                logger.info(f"✅ Resposta híbrida gerada usando {len(relevant_knowledge)} itens de conhecimento")
            else:
                ai_response['source'] = 'ai'
                ai_response['knowledge_items_used'] = 0
                logger.info("✅ Resposta IA pura gerada (sem conhecimento local)")

            return ai_response

        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {e}", exc_info=True)
            return {
                'response': 'Desculpe, ocorreu um erro ao processar sua mensagem.',
                'success': False,
                'error': str(e),
                'source': 'error'
            }

    def _load_history_from_db(self, conversation: 'Conversation') -> List[Dict[str, str]]:
        """
        ✅ CORRIGIDO: Melhor tratamento do histórico
        """
        try:
            max_messages = self.max_history_pairs * 2
            messages = conversation.messages.order_by('-timestamp')[:max_messages]

            history = []
            for msg in reversed(messages):
                # ✅ CORREÇÃO: Usar propriedade 'sender' que foi adicionada ao modelo
                role = "user" if msg.sender == 'user' else "assistant"
                history.append({"role": role, "content": msg.content})

            logger.debug(f"📚 Histórico carregado: {len(history)} mensagens")
            return history

        except Exception as e:
            logger.error(f"❌ Erro ao carregar histórico: {e}")
            return []

    def _get_relevant_knowledge(self, message: str) -> List[Any]:
        """
        ✅ CORRIGIDO: Sistema de busca híbrido inteligente
        """
        try:
            # Importar o modelo DENTRO da função para evitar problemas de importação
            from ..models import KnowledgeItem

            # 1. BUSCA POR ENTIDADES NOMEADAS (Prioridade Alta)
            entities = re.findall(
                r'["\']([^"\']+)["\']|'  # Texto entre aspas
                r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\b|'  # Nomes compostos (ex: José de Alencar)
                r'\b([A-Z][a-z]{4,})\b',  # Palavras únicas com maiúscula (ex: Machado)
                message
            )
            extracted_terms = [term for group in entities for term in group if term]

            if extracted_terms:
                logger.debug(f"🎯 Entidades extraídas: {extracted_terms}")
                knowledge_items = set()

                for term in extracted_terms:
                    # Buscar por questão e resposta usando novos campos
                    items = KnowledgeItem.objects.filter(
                        Q(question__icontains=term) | Q(answer__icontains=term),
                        active=True
                    )[:3]  # Limitar para evitar sobrecarga
                    knowledge_items.update(items)

                if knowledge_items:
                    result = list(knowledge_items)
                    logger.info(f"✅ {len(result)} fatos encontrados para entidades: {extracted_terms}")
                    return result

            # 2. BUSCA POR PALAVRAS-CHAVE LITERÁRIAS (Prioridade Média)
            literary_keywords = self._extract_literary_keywords(message)
            if literary_keywords:
                logger.debug(f"📚 Palavras-chave literárias: {literary_keywords}")
                keyword_items = set()

                for keyword in literary_keywords:
                    items = KnowledgeItem.objects.filter(
                        Q(question__icontains=keyword) | Q(answer__icontains=keyword),
                        active=True
                    )[:2]  # Limitar resultados por palavra-chave
                    keyword_items.update(items)

                if keyword_items:
                    result = list(keyword_items)
                    logger.info(f"✅ {len(result)} fatos encontrados por palavras-chave literárias")
                    return result

            # 3. BUSCA SEMÂNTICA (Prioridade Média - Se training_service disponível)
            if self.training_service and hasattr(self.training_service, 'search_knowledge'):
                logger.debug("🔄 Tentando busca semântica...")
                try:
                    semantic_results = self.training_service.search_knowledge(
                        query=message,
                        limit=3,
                        threshold=0.5  # Threshold mais baixo para capturar mais resultados
                    )
                    if semantic_results:
                        logger.info(f"✅ {len(semantic_results)} resultados da busca semântica")
                        return semantic_results
                except Exception as e:
                    logger.warning(f"⚠️ Erro na busca semântica: {e}")
            else:
                logger.debug("⚠️ Busca semântica indisponível")

            # 4. BUSCA POR CATEGORIA (Prioridade Baixa)
            category_match = self._match_literary_category(message)
            if category_match:
                logger.debug(f"📂 Categoria identificada: {category_match}")
                category_items = KnowledgeItem.objects.filter(
                    category=category_match,
                    active=True
                )[:2]

                if category_items:
                    result = list(category_items)
                    logger.info(f"✅ {len(result)} fatos encontrados por categoria: {category_match}")
                    return result

            # 5. FALLBACK FINAL - Itens gerais mais recentes
            logger.debug("🔄 Usando fallback final...")
            general_items = KnowledgeItem.objects.filter(active=True).order_by('-updated_at')[:1]
            if general_items:
                result = list(general_items)
                logger.info(f"✅ {len(result)} fato(s) geral(is) como fallback")
                return result

            logger.info("ℹ️ Nenhum conhecimento relevante encontrado")
            return []

        except Exception as e:
            logger.error(f"❌ Erro na busca de conhecimento: {e}", exc_info=True)
            return []

    def _extract_literary_keywords(self, message: str) -> List[str]:
        """
        ✅ NOVO: Extração de palavras-chave específicas de literatura
        """
        # Palavras-chave literárias importantes
        literary_terms = {
            'romance', 'autor', 'livro', 'obra', 'poema', 'poesia', 'poeta',
            'literatura', 'literário', 'escritor', 'escreveu', 'publicou',
            'romantismo', 'realismo', 'modernismo', 'barroco', 'classicismo',
            'personagem', 'protagonista', 'enredo', 'narrativa', 'ficção',
            'análise', 'crítica', 'interpretação', 'tema', 'estilo',
            'brasil', 'brasileiro', 'portuguesa', 'português'
        }

        # Palavras para ignorar
        stopwords = {
            'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'da', 'do', 'para',
            'com', 'em', 'no', 'na', 'que', 'é', 'foi', 'tem', 'ter',
            'muito', 'mais', 'sobre', 'como', 'quando', 'onde', 'por'
        }

        # Extrair palavras, converter para minúsculas
        words = re.findall(r'\b[a-záàâãéêíóôõúç]{3,}\b', message.lower())

        # Filtrar por termos literários relevantes
        keywords = [word for word in words if word in literary_terms and word not in stopwords]

        return list(set(keywords))[:3]  # Máximo 3 palavras-chave únicas

    def _match_literary_category(self, message: str) -> Optional[str]:
        """
        ✅ NOVO: Identifica categoria literária pela mensagem
        """
        message_lower = message.lower()

        category_patterns = {
            'author': ['autor', 'escritor', 'poeta', 'quem escreveu', 'biografia'],
            'book': ['livro', 'obra', 'romance', 'novela', 'conto'],
            'movement': ['romantismo', 'realismo', 'modernismo', 'barroco', 'movimento'],
            'analysis': ['análise', 'interpretação', 'crítica', 'significado', 'tema'],
            'quote': ['citação', 'frase', 'verso', 'trecho'],
            'genre': ['gênero', 'épico', 'lírico', 'dramático', 'ficção']
        }

        for category, patterns in category_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return category

        return None

    def _build_chat_prompt(self, user_message: str, history: List[Dict], knowledge: List[Any]) -> List[Dict]:
        """
        ✅ CORRIGIDO: Construção otimizada do prompt com conhecimento
        """
        system_prompt = (
            "Você é o 'Chatbot Literário' da CG.BookStore.Online, um assistente especialista em literatura brasileira e internacional.\n\n"
            "SUAS ESPECIALIDADES:\n"
            "• Literatura brasileira e mundial\n"
            "• Análise de obras e autores\n"
            "• Recomendações personalizadas\n"
            "• História e movimentos literários\n\n"
            "DIRETRIZES DE RESPOSTA:\n"
            "1. Use SEMPRE as informações da 'Base de Fatos' quando disponíveis\n"
            "2. Combine TODOS os fatos relevantes para respostas completas\n"
            "3. Considere o histórico da conversa para continuidade\n"
            "4. Seja preciso e educativo\n"
            "5. Se não tiver informação específica, seja honesto sobre isso\n"
            "6. Mantenha o foco literário e cultural"
        )

        messages = [{"role": "system", "content": system_prompt}]

        # Adicionar conhecimento se disponível
        if knowledge:
            knowledge_text = "=== BASE DE FATOS LITERÁRIOS ===\n"
            for i, item in enumerate(knowledge, 1):
                # Compatibilidade com KnowledgeItem e SearchResult
                question_text = getattr(item, 'question', getattr(item, 'question_found', f'Fato {i}'))
                answer_text = getattr(item, 'answer', 'Informação não disponível.')

                knowledge_text += f"{i}. **{question_text}**\n   {answer_text}\n\n"

            knowledge_text += "=== FIM DA BASE DE FATOS ==="
            messages.append({"role": "system", "content": knowledge_text})

        # Adicionar histórico da conversa
        if history:
            messages.extend(history)

        # Adicionar pergunta atual
        messages.append({"role": "user", "content": user_message})

        return messages

    def get_status(self) -> Dict[str, Any]:
        """
        ✅ Status do chatbot e suas dependências
        """
        training_available = self.training_service is not None
        training_initialized = (
                training_available and
                hasattr(self.training_service, 'initialized') and
                self.training_service.initialized
        )

        return {
            'functional_chatbot': True,
            'training_service_available': training_available,
            'training_service_initialized': training_initialized,
            'max_history_pairs': self.max_history_pairs,
            'hybrid_mode': training_available
        }