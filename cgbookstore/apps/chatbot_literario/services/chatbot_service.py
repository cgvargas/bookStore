import logging
import re
import random
from django.conf import settings
from django.utils import timezone

# Importar o serviço de treinamento
from .training_service import training_service

logger = logging.getLogger(__name__)


class ChatbotService:
    """
    Serviço principal do chatbot. Responsável por processar mensagens
    e gerar respostas adequadas utilizando a base de conhecimento.
    """

    def __init__(self):
        self.initialized = False
        self.intent_patterns = self._load_intent_patterns()

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
            'ajuda': r'\b(ajuda|socorro|help|como funciona|o que você faz)\b',
            'navegacao': r'(como|onde|posso).{1,30}(encontr[ao]|v[eê]r|ir|acesso)',
        }

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

    def get_response(self, message, user=None):
        """
        Processa a mensagem do usuário e retorna uma resposta.

        Args:
            message (str): Mensagem do usuário
            user (User, opcional): Usuário que enviou a mensagem

        Returns:
            tuple: (resposta, fonte)
        """
        if not self.initialized:
            self.initialize()

        try:
            # Detectar intenção
            intent = self.detect_intent(message)

            # Tratar intenções específicas
            if intent:
                intent_response = self._handle_intent(intent, message, user)
                if intent_response:
                    return intent_response, "intent"

            # Buscar na base de conhecimento
            knowledge_results = training_service.search_knowledge_base(message)

            if knowledge_results and len(knowledge_results) > 0:
                # CORREÇÃO: Acessar o objeto KnowledgeItem corretamente
                # Cada resultado é uma tupla (item, score)
                best_match = knowledge_results[0]
                knowledge_item = best_match[0]  # Primeiro elemento é o objeto KnowledgeItem
                similarity = best_match[1]  # Segundo elemento é o score de similaridade

                logger.debug(f"Melhor correspondência: {knowledge_item.question} (score: {similarity})")

                # Verificar se a similaridade está acima do threshold
                if similarity >= 0.7:
                    # Acessar o atributo 'answer' do objeto
                    return knowledge_item.answer, "knowledge_base"

            # Resposta padrão se não encontrar nada na base de conhecimento
            return self._get_fallback_response(intent), "fallback"

        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            return "Desculpe, estou enfrentando algumas dificuldades no momento. Poderia tentar novamente mais tarde?", "error"

    def _handle_intent(self, intent, message, user):
        """
        Trata intenções específicas com respostas predefinidas.

        Args:
            intent (str): Intenção detectada
            message (str): Mensagem do usuário
            user (User): Usuário que enviou a mensagem

        Returns:
            str: Resposta para a intenção específica ou None
        """
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

        Args:
            intent (str): Intenção detectada (se houver)

        Returns:
            str: Resposta genérica
        """
        fallbacks = [
            "Não tenho certeza sobre isso. Poderia reformular sua pergunta?",
            "Hmm, ainda estou aprendendo sobre esse assunto. Poderia perguntar de outra forma?",
            "Não encontrei uma resposta específica para isso. Posso ajudar com informações sobre livros, autores ou navegação no site.",
            "Não tenho essa informação no momento. Posso ajudar com algo mais relacionado à literatura ou ao uso do site?"
        ]

        return random.choice(fallbacks)


# Instância singleton do serviço
chatbot = ChatbotService()