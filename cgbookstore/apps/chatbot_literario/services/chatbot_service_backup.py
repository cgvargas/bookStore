import logging
import re
import random
import traceback
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

# Importar modelos necessários
from ..models import Conversation, Message

# Importar o serviço de treinamento
from .training_service import training_service

logger = logging.getLogger(__name__)


class ConversationContext:
    """
    Classe para gerenciar o contexto de uma conversa.
    """

    def __init__(self):
        self.entities = {}  # Entidades extraídas (livros, autores, etc.)
        self.last_topic = None  # Último tópico discutido
        self.last_question_type = None  # Tipo da última pergunta (autor, ano, etc.)
        self.conversation_history = []  # Histórico das últimas mensagens
        self.session_id = None  # ID da sessão/conversa

    def add_message(self, message, sender='user'):
        """Adiciona uma mensagem ao histórico do contexto."""
        self.conversation_history.append({
            'message': message,
            'sender': sender,
            'timestamp': timezone.now()
        })

        # Detectar tipo de pergunta se for do usuário
        if sender == 'user':
            self.last_question_type = self._detect_question_type(message)

        # Manter apenas as últimas 10 mensagens para não sobrecarregar
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

    def _detect_question_type(self, message):
        """Detecta o tipo de pergunta feita pelo usuário."""
        message_lower = message.lower()

        if re.search(r'\b(quem|autor|escreveu|criou)\b', message_lower):
            return 'autor'
        elif re.search(r'\b(quando|que ano|data|lançado|publicado)\b', message_lower):
            return 'ano'
        elif re.search(r'\b(onde|local|país|cidade)\b', message_lower):
            return 'local'
        elif re.search(r'\b(o que|sobre o que|tema|assunto)\b', message_lower):
            return 'tema'

        return None

    def extract_entities(self, message):
        """Extrai entidades da mensagem (livros, autores, anos, etc.) - VERSÃO CORRIGIDA."""
        message_lower = message.lower()

        # ✅ PADRÕES MELHORADOS para extrair entidades no contexto ativo
        patterns = {
            'book_title': [
                r'"([^"]+)"',  # Entre aspas duplas
                r'"([^"]+)"',  # Entre aspas curvadas
                r'\b(?:livro|obra|romance|novela)\s+([A-ZÀ-Ÿ][A-Za-zÀ-ÿ\s]+?)(?:\s*[\?\.]|$)',
                r'\b(O\s+[A-ZÀ-Ÿ][A-Za-zÀ-ÿ\s]+?)(?:\s*[\?\.]|$)',
                r'\b(Dom Casmurro|Senhor dos [Aa]n[eé]is|Silmarillion|Hobbit|Harry Potter|1984)\b',
            ],
            'author': [
                r'\b([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]*)*(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]+))\s+(?:é o autor|escreveu|criou)',
                r'(?:autor[a]?|escritor[a]?)\s+([A-ZÀ-Ÿ][A-Za-zÀ-ÿ\s\.]+?)(?:\s|$|\?|!)',
                r'\b(J\.?K\.?\s*Rowling|J\.?R\.?R\.?\s*Tolkien|Machado de Assis|George Orwell)\b',
                r'\b([A-ZÀ-Ÿ][a-zà-ÿ]+\s+de\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)\b',  # "Machado de Assis"
            ],
            'year': [r'\b(19\d{2}|20\d{2})\b'],
        }

        for entity_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, message, re.IGNORECASE)
                if matches:
                    if entity_type not in self.entities:
                        self.entities[entity_type] = []

                    for match in matches:
                        # Para tuplas (grupos de captura múltiplos), pegar o não-vazio
                        if isinstance(match, tuple):
                            match = next((m for m in match if m), '')

                        if match and match.strip():
                            entity_value = match.strip()
                            # Limpar entidade
                            entity_value = re.sub(r'[\.!\?]+$', '', entity_value)

                            if entity_value and len(entity_value) > 2 and entity_value not in self.entities[entity_type]:
                                self.entities[entity_type].append(entity_value)
                                logger.debug(f"Entidade extraída - {entity_type}: {entity_value}")

                                # ✅ CORREÇÃO: Atualizar last_topic quando nova entidade é encontrada
                                if entity_type in ['book_title', 'author']:
                                    self.last_topic = entity_value

    def get_context_string(self):
        """Retorna uma string com o contexto atual para ajudar na busca."""
        context_parts = []

        # Adicionar entidades ao contexto
        for entity_type, values in self.entities.items():
            if values:
                context_parts.append(f"{entity_type}: {', '.join(values)}")

        # Adicionar tipo da última pergunta
        if self.last_question_type:
            context_parts.append(f"pergunta_sobre: {self.last_question_type}")

        return " | ".join(context_parts)

    def find_referenced_entity(self, message, entity_type):
        """Encontra uma entidade referenciada no contexto atual."""
        if entity_type in self.entities and self.entities[entity_type]:
            # Retorna a entidade mais recente deste tipo
            return self.entities[entity_type][-1]
        return None

    def get_last_mentioned_book(self):
        """Retorna o último livro mencionado no contexto."""
        return self.find_referenced_entity("", 'book_title')

    def should_clear_context(self, message):
        """Verifica se deve limpar o contexto baseado na mensagem - VERSÃO CORRIGIDA."""
        message_lower = message.lower().strip()

        # ✅ CORREÇÃO 1: Identificar perguntas contextuais que NÃO devem limpar contexto
        contextual_questions = [
            r'^\s*(e\s+)?(quem|que|qual|quando|onde)\s+(escreveu|é|foi|escreveu\s+isso|criou)?\s*[\?\.]?$',
            r'^\s*quem\s+escreveu\s*[\?\.]?$',
            r'^\s*quando\s+(foi\s+)?(publicado|lançado)\s*[\?\.]?$',
            r'^\s*(e\s+)?o\s+autor\s*[\?\.]?$',
            r'^\s*autor\s*[\?\.]?$',
            r'^\s*(quais|que)\s+(livros|obras)\s+(ele|ela)\s+(escreveu|criou)\s*[\?\.]?$',
            r'^\s*outros\s+livros\s*[\?\.]?$',
        ]

        # Se é uma pergunta contextual curta, NÃO limpar contexto
        for pattern in contextual_questions:
            if re.match(pattern, message_lower):
                logger.debug(f"Pergunta contextual detectada: {message}")
                return False

        # ✅ CORREÇÃO 2: Palavras que indicam mudança EXPLÍCITA de assunto
        explicit_topic_change = [
            'agora fale sobre', 'me fale sobre', 'quero saber sobre', 'mude para',
            'agora me conte sobre', 'fale do livro', 'outro livro', 'diferente livro',
            'mudando de assunto', 'vamos falar de', 'e quanto ao', 'e sobre o livro',
            'agora sobre', 'conte sobre', 'fale sobre', 'vamos para o',
            'mudemos para', 'passemos para', 'agora quero saber sobre'
        ]

        # Verificar mudança explícita de assunto
        for indicator in explicit_topic_change:
            if indicator in message_lower:
                logger.debug(f"Mudança explícita de tópico detectada: {indicator}")
                return True

        # ✅ CORREÇÃO 3: Detectar padrões de introdução de novo tópico
        topic_introduction_patterns = [
            r'\b(agora|então|vamos)\s+(fal[ae]|cont[ae]|sobre)\s+',
            r'\b(me\s+)?(fal[ae]|cont[ae])\s+(sobre|do|da)\s+',
            r'\b(quero\s+saber|gostaria\s+de\s+saber)\s+sobre\s+',
            r'\b(e\s+)?(o|a)\s+(autor[a]?|escritor[a]?)\s+[A-ZÀ-Ÿ]',
        ]

        for pattern in topic_introduction_patterns:
            if re.search(pattern, message_lower):
                logger.debug(f"Padrão de introdução de tópico detectado: {pattern}")
                return True

        # ✅ CORREÇÃO 4: Detectar novo livro/autor apenas se for explícito
        new_entities = self._extract_entities_preview(message)

        # Se menciona um livro/autor diferente do contexto atual DE FORMA EXPLÍCITA
        if new_entities.get('book_title') or new_entities.get('author'):
            current_book = self.get_last_mentioned_book()
            current_author = self.find_referenced_entity("", 'author')

            new_book = new_entities.get('book_title', [''])[0] if new_entities.get('book_title') else None
            new_author = new_entities.get('author', [''])[0] if new_entities.get('author') else None

            # ✅ CORREÇÃO 5: Limpar contexto ao introduzir novo autor/livro explicitamente
            if new_book and current_book:
                if new_book.lower() != current_book.lower() and len(message.split()) >= 3:
                    logger.debug(f"Novo livro detectado: {new_book} (anterior: {current_book})")
                    return True

            if new_author and current_author:
                if new_author.lower() != current_author.lower() and len(message.split()) >= 3:
                    logger.debug(f"Novo autor detectado: {new_author} (anterior: {current_author})")
                    return True

            # ✅ CORREÇÃO 6: Limpar contexto ao mencionar novo autor quando contexto era sobre livro
            if new_author and current_book and not current_author:
                logger.debug(f"Mudança de livro para autor: {new_author}")
                return True

        return False

    def _extract_entities_preview(self, message):
        """Extrai entidades sem adicionar ao contexto (preview) - VERSÃO CORRIGIDA."""
        entities_preview = {}

        # ✅ PADRÕES MELHORADOS para detectar autores e livros
        patterns = {
            'book_title': [
                r'"([^"]+)"',  # Entre aspas duplas
                r'"([^"]+)"',  # Entre aspas curvadas
                r'\b(?:fale sobre|sobre o livro|livro)\s+([A-ZÀ-Ÿ][A-Za-zÀ-ÿ\s]+?)(?:\s*[\?\.]|$)',
                r'\b(Harry Potter|Senhor dos [Aa]n[eé]is|Silmarillion|Hobbit|Dom Casmurro|1984)\b',
                r'\b(O\s+[A-ZÀ-Ÿ][A-Za-zÀ-ÿ\s]+?)(?:\s*[\?\.]|$)',
            ],
            'author': [
                # ✅ PADRÕES ESPECÍFICOS para detectar menção de autores
                r'\b(?:fale sobre|sobre o? autor[a]?|autor[a]?)\s+([A-ZÀ-Ÿ][A-Za-zÀ-ÿ\s\.]+?)(?:\s|$|\?|!)',
                r'\b(J\.?K\.?\s*Rowling|J\.?R\.?R\.?\s*Tolkien|Machado de Assis|George Orwell)\b',
                r'\b([A-ZÀ-Ÿ][a-zà-ÿ]+\s+de\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)\b',  # Padrão "Machado de Assis"
                r'\b([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]+){1,2})\s*(?=\s|$|\?|!)',  # Nomes próprios compostos
            ],
        }

        for entity_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, message, re.IGNORECASE)
                if matches:
                    if entity_type not in entities_preview:
                        entities_preview[entity_type] = []
                    for match in matches:
                        if isinstance(match, tuple):
                            match = next((m for m in match if m), '')
                        if match and match.strip():
                            clean_match = re.sub(r'[\.!\?]+$', '', match.strip())
                            # ✅ FILTRAR nomes muito curtos ou genéricos
                            if len(clean_match) > 2 and not clean_match.lower() in ['ele', 'ela', 'autor', 'autora', 'livro']:
                                entities_preview[entity_type].append(clean_match)
                                logger.debug(f"Entidade detectada ({entity_type}): {clean_match}")

        return entities_preview


class ChatbotService:
    """
    Serviço principal do chatbot. Responsável por processar mensagens
    e gerar respostas adequadas utilizando a base de conhecimento e contexto.
    """

    def __init__(self):
        self.initialized = False
        self.intent_patterns = self._load_intent_patterns()
        self.user_contexts = {}  # Contextos por usuário

    def initialize(self):
        """Inicializa o serviço do chatbot."""
        if self.initialized:
            return

        # Inicializar serviço de treinamento
        if not training_service.initialized:
            training_service.initialize()

        self.initialized = True
        logger.info("Serviço do chatbot inicializado com sucesso.")

    def _load_intent_patterns(self):
        """Carrega padrões de reconhecimento de intenções (intents)."""
        return {
            'saudacao': r'\b(olá|oi|e aí|hey|bom dia|boa tarde|boa noite|hello)\b',
            'despedida': r'\b(tchau|adeus|até logo|até mais|até a próxima|até breve)\b',
            'agradecimento': r'\b(obrigad[oa]|valeu|thanks|grat[oa]|agradeç[oa])\b',
            'livro_busca': r'(encontr[ea]|busc[ae]|procur[ae]|quero).{1,30}livro',
            'autor_info': r'(quem|informaç[õo]es|sobre).{1,30}autor[a]?',
            'recomendacao': r'(recomend[ae]|suger[ei]|indic[ae]).{1,30}(livro|leitura)',
            'ajuda': r'\b(ajuda|socorro|help|como funciona|o que você (faz|pode fazer))\b',
            'navegacao': r'(como|onde|posso).{1,30}(encontr[ao]|v[eê]r|ir|acesso)',
            'autor_pergunta': r'\b(quem|autor|escreveu|criou)\b',
            'ano_pergunta': r'\b(quando|que ano|data|lançado|publicado)\b',
            'contexto_pergunta': r'\b(e\s+)?(quem|que|qual|quando|onde)\b',
        }

    def get_user_context(self, user):
        """Obtém ou cria o contexto de conversa para um usuário."""
        user_id = user.id if user else 'anonymous'

        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = ConversationContext()

            # Se for um usuário autenticado, carregar histórico recente
            if user:
                self._load_recent_conversation_history(user, self.user_contexts[user_id])

        return self.user_contexts[user_id]

    def _load_recent_conversation_history(self, user, context):
        """Carrega o histórico recente de conversas do usuário."""
        try:
            # Buscar conversas recentes (últimas 24 horas)
            recent_time = timezone.now() - timezone.timedelta(hours=24)
            recent_conversations = Conversation.objects.filter(
                user=user,
                updated_at__gte=recent_time
            ).order_by('-updated_at')[:3]  # Últimas 3 conversas

            for conversation in recent_conversations:
                # Buscar mensagens da conversa
                messages = Message.objects.filter(
                    conversation=conversation
                ).order_by('timestamp')[:10]  # Últimas 10 mensagens

                for message in messages:
                    # Verificar se o campo existe antes de usar
                    if hasattr(message, 'is_user'):
                        sender = 'user' if message.is_user else 'bot'
                    elif hasattr(message, 'sender'):
                        sender = message.sender
                    else:
                        # Assumir baseado em padrões do conteúdo ou alternar
                        sender = 'user'  # Padrão para compatibilidade

                    context.add_message(message.content, sender)
                    if sender == 'user':
                        context.extract_entities(message.content)

        except Exception as e:
            logger.warning(f"Erro ao carregar histórico de conversa: {e}")

    def detect_intent(self, message):
        """
        Detecta a intenção do usuário com base em padrões regex.

        Args:
            message (str): Mensagem do usuário

        Returns:
            str: Nome da intenção detectada ou None
        """
        message = message.lower()

        for intent, pattern in self.intent_patterns.items():
            if re.search(pattern, message, re.IGNORECASE):
                return intent

        return None

    def _is_contextual_question(self, message, context):
        """Verifica se a pergunta se refere ao contexto atual."""
        contextual_patterns = [
            r'^e\s+(quem|que|qual|quando|onde|o\s+autor)',  # "E quem", "E o autor"
            r'^\s*(quem|que|qual|quando|onde)\s+(escreveu|foi|é)?\s*$',  # Perguntas muito curtas
            r'^(e\s+)?o\s+autor\s*[\?\.]?$',  # "O autor?" ou "E o autor?"
            r'^autor\s*[\?\.]?$',  # Apenas "autor?"
            r'^\s*(quais|que)\s+(livros|obras)\s+(ele|ela)\s+(escreveu|criou)\s*[\?\.]?$',  # "Quais livros ela escreveu?"
        ]

        message_lower = message.lower().strip()

        # Verificar se a mensagem é muito curta e parece contextual
        if len(message_lower.split()) <= 5:
            for pattern in contextual_patterns:
                if re.search(pattern, message_lower):
                    # Verificar se há contexto relevante
                    if context.entities.get('book_title') or context.entities.get('author'):
                        logger.debug(f"Pergunta contextual detectada: {message}")
                        return True

        return False

    def _answer_contextual_question(self, message, context):
        """Responde a perguntas contextuais usando o contexto atual - VERSÃO CORRIGIDA."""
        message_lower = message.lower()

        # Identificar sobre qual livro/autor está perguntando
        current_book = context.get_last_mentioned_book()
        current_author = context.find_referenced_entity("", 'author')

        logger.debug(f"Contexto atual - Livro: {current_book}, Autor: {current_author}")

        search_query = None

        # ✅ CORREÇÃO: Perguntas sobre autor - queries mais específicas
        if re.search(r'\b(quem|autor|escreveu|criou)\b', message_lower):
            if current_book:
                search_query = f"Quem escreveu {current_book}"
                logger.debug(f"Busca contextual por autor: {search_query}")
            elif current_author:
                search_query = f"autor {current_author}"
                logger.debug(f"Busca contextual sobre autor: {search_query}")
            else:
                return None

        # ✅ CORREÇÃO: Perguntas sobre livros do autor
        elif re.search(r'\b(quais|que)\s+(livros|obras)\s+(ele|ela)\s+(escreveu|criou)\b', message_lower):
            if current_author:
                search_query = f"livros {current_author} obras"
                logger.debug(f"Busca contextual por obras do autor: {search_query}")
            elif current_book:
                search_query = f"outros livros autor {current_book}"
                logger.debug(f"Busca contextual por obras do mesmo autor: {search_query}")
            else:
                return None

        # ✅ CORREÇÃO: Perguntas sobre data/ano
        elif re.search(r'\b(quando|que ano|data|lançado|publicado)\b', message_lower):
            if current_book:
                search_query = f"quando {current_book} publicado"
                logger.debug(f"Busca contextual por data: {search_query}")
            elif current_author:
                search_query = f"quando {current_author} nasceu"
                logger.debug(f"Busca contextual por data do autor: {search_query}")
            else:
                return None

        else:
            return None

        # ✅ FAZER BUSCA sem filtros problemáticos
        if search_query:
            knowledge_results = training_service.search_knowledge_base(
                search_query,
                threshold=0.4,  # Threshold mais baixo para busca contextual
                max_results=5,
                context_filter=None  # Sem filtros restritivos
            )

            if knowledge_results and len(knowledge_results) > 0:
                # ✅ VALIDAÇÃO CONTEXTUAL melhorada
                for i, (knowledge_item, similarity) in enumerate(knowledge_results):
                    logger.debug(f"Resultado {i + 1}: {knowledge_item.question} (score: {similarity})")

                    answer_lower = knowledge_item.answer.lower()
                    question_lower = knowledge_item.question.lower()

                    is_contextually_relevant = False

                    # ✅ VALIDAÇÃO mais flexível do contexto
                    if current_book:
                        book_words = current_book.lower().split()
                        main_words = [word for word in book_words if len(word) > 2]

                        for word in main_words:
                            if word in question_lower or word in answer_lower:
                                is_contextually_relevant = True
                                break

                        if current_book.lower() in question_lower or current_book.lower() in answer_lower:
                            is_contextually_relevant = True

                    if current_author and not is_contextually_relevant:
                        author_words = current_author.lower().split()
                        main_author_words = [word for word in author_words if len(word) > 2]

                        for word in main_author_words:
                            if word in question_lower or word in answer_lower:
                                is_contextually_relevant = True
                                break

                        if current_author.lower() in question_lower or current_author.lower() in answer_lower:
                            is_contextually_relevant = True

                    # ✅ ACEITAR resultados com boa similaridade OU contexto relevante
                    if (is_contextually_relevant and similarity >= 0.4) or similarity >= 0.7:
                        logger.debug(f"Resposta contextual selecionada: {knowledge_item.answer[:100]}...")
                        return knowledge_item.answer

                # ✅ USAR melhor resultado geral se não encontrou contextual
                if knowledge_results:
                    best_result = knowledge_results[0]
                    best_item, best_similarity = best_result

                    if best_similarity >= 0.6:
                        logger.debug(f"Usando melhor resultado geral: {best_item.answer[:100]}... (score: {best_similarity})")
                        return best_item.answer

        return None

    def get_response(self, message, user=None):
        """
        Processa a mensagem do usuário e retorna uma resposta considerando o contexto.
        """
        if not self.initialized:
            self.initialize()

        try:
            # Obter contexto do usuário
            context = self.get_user_context(user)

            # ✅ VERIFICAR se deve limpar o contexto ANTES de qualquer processamento
            if context.should_clear_context(message):
                logger.debug("🧹 Limpando contexto devido a mudança de tópico")
                # Preservar histórico mas limpar entidades
                context.entities = {}
                context.last_topic = None
                context.last_question_type = None

            # Adicionar mensagem ao contexto
            context.add_message(message, 'user')
            context.extract_entities(message)

            # ✅ VERIFICAR se é uma pergunta contextual ANTES de detectar intent
            if self._is_contextual_question(message, context):
                logger.debug("🎯 Processando pergunta contextual")
                contextual_answer = self._answer_contextual_question(message, context)
                if contextual_answer:
                    context.add_message(contextual_answer, 'bot')
                    return contextual_answer, "contextual"

            # Detectar intenção
            intent = self.detect_intent(message)

            # Tratar intenções específicas
            if intent:
                intent_response = self._handle_intent(intent, message, user)
                if intent_response:
                    context.add_message(intent_response, 'bot')
                    return intent_response, "intent"

            # Buscar na base de conhecimento (busca geral)
            knowledge_results = training_service.search_knowledge_base(
                message,
                threshold=0.5,
                max_results=5,
                context_filter=None
            )

            if knowledge_results and len(knowledge_results) > 0:
                best_match = knowledge_results[0]
                knowledge_item = best_match[0]
                similarity = best_match[1]

                logger.debug(f"Melhor correspondência: {knowledge_item.question} (score: {similarity})")

                if similarity >= 0.5:
                    response = knowledge_item.answer
                    context.add_message(response, 'bot')
                    return response, "knowledge_base"

            # Resposta de fallback
            fallback_response = self._get_fallback_response(intent)
            context.add_message(fallback_response, 'bot')
            return fallback_response, "fallback"

        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            error_response = "Desculpe, estou enfrentando algumas dificuldades no momento. Poderia tentar novamente mais tarde?"
            return error_response, "error"

    def _handle_intent(self, intent, message, user):
        """Trata intenções específicas com respostas predefinidas."""
        responses = {
            'saudacao': [
                f"Olá! Em que posso ajudar hoje?",
                f"Oi! Como posso ser útil para você?",
                f"Olá! Estou aqui para ajudar com suas dúvidas sobre livros e navegação no site."
            ],
            'despedida': [
                "Até mais! Foi um prazer ajudar.",
                "Tchau! Volte sempre que precisar.",
                "Até a próxima! Boa leitura!"
            ],
            'agradecimento': [
                "De nada! Estou sempre à disposição.",
                "Por nada! É um prazer ajudar.",
                "Disponha! Estou aqui para isso."
            ],
            'ajuda': [
                "Estou aqui para ajudar com suas dúvidas sobre livros, autores e como navegar no site. Você pode me perguntar sobre recomendações de leitura, informações sobre obras ou autores, ou como encontrar funcionalidades específicas no site.",
                "Posso ajudar com informações sobre livros, autores e navegação no site. Experimente perguntar sobre um livro específico, solicitar recomendações ou pedir ajuda para encontrar algo no site."
            ]
        }

        if intent in responses:
            return random.choice(responses[intent])

        return None

    def _get_fallback_response(self, intent):
        """
        Retorna uma resposta genérica quando não há correspondência na base de conhecimento.
        """
        fallbacks = [
            "Não tenho certeza sobre isso. Poderia reformular sua pergunta?",
            "Hmm, ainda estou aprendendo sobre esse assunto. Poderia perguntar de outra forma?",
            "Não encontrei uma resposta específica para isso. Posso ajudar com informações sobre livros, autores ou navegação no site.",
            "Não tenho essa informação no momento. Posso ajudar com algo mais relacionado à literatura ou ao uso do site?"
        ]

        return random.choice(fallbacks)

    def clear_user_context(self, user):
        """Limpa o contexto de um usuário específico."""
        user_id = user.id if user else 'anonymous'
        if user_id in self.user_contexts:
            del self.user_contexts[user_id]


# Instância singleton do serviço
chatbot = ChatbotService()