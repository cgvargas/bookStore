import torch
import logging
import re
from transformers import AutoModelForCausalLM, AutoTokenizer

# Importar o serviço de recomendação
from .recommendation_service import recommendation_service
from . import training_service

logger = logging.getLogger(__name__)


class ChatbotService:
    def __init__(self):
        self.model_name = "microsoft/DialoGPT-medium"
        self.tokenizer = None
        self.model = None
        self.max_length = 1000
        self.initialized = False

        # Padrões de reconhecimento de intents
        self.patterns = {
            'recomendacao_genero': r'recomend[ae][rção]?\s+(?:um[as]?\s+)?(?:livros?|obras?)\s+(?:de|sobre)?\s+([a-záàâãéèêíìóòôõúùüç\s]+)',
            'sinopse': r'sinopse\s+d[eo]\s+(?:livro\s+)?["\']?([^"\']+)["\']?',
            'autor': r'(?:quem\s+(?:é|foi)|informações\s+sobre)\s+(?:o\s+autor\s+)?["\']?([^"\']+)["\']?',
            'navegacao': r'onde\s+(?:eu\s+)?(?:posso\s+)?(?:encontr[oa]r?|v[êe]r?|est[áa]o?|fic[ao]m?)\s+(?:os\s+)?([a-záàâãéèêíìóòôõúùüç\s]+)',
            'saudacao': r'(?:olá|oi|e aí|boa tarde|bom dia|boa noite|hello|hi)',
            'agradecimento': r'(?:obrigad[oa]|valeu|agradeç[oa]|thanks)',
            'ajuda': r'(?:ajud[ae]|help|socorro|auxílio|me ajude|pode me ajudar|preciso de ajuda)'
        }

    def initialize(self):
        """Carrega o modelo e o tokenizer."""
        try:
            logger.info(f"Inicializando chatbot com modelo {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            self.initialized = True
            logger.info("Chatbot inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar chatbot: {str(e)}")
            raise

    def get_response(self, input_text, user=None, conversation_history=None):
        """Gera uma resposta para o texto de entrada com base no histórico de conversa."""
        # Verificar se há correspondência na base de conhecimento
        knowledge_response = self._check_knowledge_base(input_text)
        if knowledge_response:
            return knowledge_response, conversation_history

        # Processar o texto para identificar intents
        intent, entities = self._identify_intent(input_text.lower())

        # Se identificamos uma intent específica, gerar resposta apropriada
        if intent and hasattr(self, f"_handle_{intent}"):
            try:
                handler = getattr(self, f"_handle_{intent}")
                response = handler(entities, user)
                if response:
                    return response, conversation_history
            except Exception as e:
                logger.error(f"Erro ao processar intent {intent}: {str(e)}")

        # Se não tiver intent específica ou falhar, usar o modelo DialoGPT
        if not self.initialized:
            self.initialize()

        # Preparar histórico de conversa se existir
        chat_history_ids = conversation_history if conversation_history is not None else []

        try:
            # Codificar a entrada do usuário
            new_input_ids = self.tokenizer.encode(input_text + self.tokenizer.eos_token,
                                                  return_tensors='pt')

            # Concatenar histórico (se existir) com nova entrada
            if len(chat_history_ids) > 0:
                bot_input_ids = torch.cat([chat_history_ids, new_input_ids], dim=-1)
            else:
                bot_input_ids = new_input_ids

            # Gerar resposta
            chat_history_ids = self.model.generate(
                bot_input_ids,
                max_length=self.max_length,
                pad_token_id=self.tokenizer.eos_token_id,
                no_repeat_ngram_size=3,
                do_sample=True,
                top_k=50,
                top_p=0.95,
                temperature=0.7
            )

            # Decodificar resposta
            response = self.tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0],
                                             skip_special_tokens=True)

            # Adicionar contexto de livros e adaptações para tornar as respostas mais relacionadas a literatura
            if not response or response.isspace():
                response = "Desculpe, não consegui formular uma resposta adequada. Posso ajudar com recomendações de livros ou informações sobre autores?"

            # Adaptar respostas para o contexto literário
            response = self._adapt_response_to_literary_context(input_text, response)

            return response, chat_history_ids

        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {str(e)}")
            return "Desculpe, ocorreu um erro ao processar sua mensagem. Poderia tentar novamente?", None

    def _check_knowledge_base(self, input_text):
        """Verifica se há uma resposta adequada na base de conhecimento."""
        if not training_service.initialized:
            training_service.initialize()

        knowledge_results = training_service.search_knowledge_base(input_text)

        # Se encontrou resultados com alta relevância, usar a resposta da base de conhecimento
        if knowledge_results and knowledge_results[0][1] > 0.75:  # Threshold de similaridade
            return knowledge_results[0][0]['answer']

        return None

    def _identify_intent(self, text):
        """Identifica a intenção do usuário baseado em padrões."""
        for intent, pattern in self.patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extrai as entidades encontradas (grupos capturados)
                entities = match.groups() if match.groups() else []
                return intent, entities

        return None, []

    def _handle_recomendacao_genero(self, entities, user):
        """Manipula pedidos de recomendação por gênero."""
        if not entities:
            return "Que tipo de livro você gostaria que eu recomendasse?"

        genero = entities[0].strip()
        books = recommendation_service.get_recommendations_by_genre(genero, limit=3)

        if not books or len(books) == 0:
            return f"Não encontrei livros de {genero} para recomendar. Que tal tentar outro gênero?"

        response = f"Para quem gosta de {genero}, recomendo:\n\n"
        for i, book in enumerate(books, 1):
            response += f"{i}. {book.titulo} - {book.autor}\n"
            if hasattr(book, 'descricao') and book.descricao:
                desc = book.descricao[:100] + "..." if len(book.descricao) > 100 else book.descricao
                response += f"   {desc}\n"
            response += "\n"

        response += "Gostaria de mais informações sobre algum desses livros?"
        return response

    def _handle_sinopse(self, entities, user):
        """Manipula pedidos de sinopse de livros."""
        if not entities:
            return "Qual livro você gostaria de saber a sinopse?"

        titulo = entities[0].strip()
        # Aqui você implementaria a lógica para buscar a sinopse no banco de dados
        # Por enquanto, retornamos uma resposta genérica
        return f"A sinopse de '{titulo}' não está disponível no momento. Estou em fase de treinamento para fornecer informações mais detalhadas sobre livros específicos."

    def _handle_autor(self, entities, user):
        """Manipula pedidos de informações sobre autores."""
        if not entities:
            return "Sobre qual autor você gostaria de saber mais?"

        autor = entities[0].strip()
        # Aqui você implementaria a lógica para buscar informações do autor
        return f"Ainda estou aprendendo sobre {autor}. Em breve poderei fornecer informações mais detalhadas sobre autores."

    def _handle_navegacao(self, entities, user):
        """Manipula perguntas sobre navegação no site."""
        if not entities:
            return "O que você está procurando no site?"

        busca = entities[0].strip().lower()

        # Mapeamento de termos comuns para páginas no site
        navegacao = {
            'favoritos': "Seus livros favoritos podem ser encontrados na sua página de perfil. Basta acessar 'Perfil' no menu superior.",
            'prateleira': "Suas prateleiras de livros estão na página de perfil, organizadas em 'Favoritos', 'Lendo', 'Quero Ler' e 'Lidos'.",
            'lendo': "Os livros que você está lendo atualmente estão na prateleira 'Lendo' em seu perfil.",
            'perfil': "Você pode acessar seu perfil clicando em seu nome/avatar no canto superior direito do site.",
            'busca': "Para buscar livros, use a barra de pesquisa no topo do site ou acesse 'Livros > Buscar' no menu principal.",
            'recomendações': "Você pode ver recomendações personalizadas na página inicial ou em 'Livros > Recomendados' no menu principal.",
            'configurações': "As configurações da sua conta podem ser acessadas através do menu no seu perfil, clicando em 'Editar Perfil'."
        }

        # Verificar correspondências parciais
        for termo, resposta in navegacao.items():
            if termo in busca or busca in termo:
                return resposta

        return f"Não tenho certeza sobre onde encontrar '{busca}'. Você pode tentar usar a barra de pesquisa no topo do site ou navegar pelo menu principal."

    def _handle_saudacao(self, entities, user):
        """Manipula saudações."""
        if user and hasattr(user, 'first_name') and user.first_name:
            return f"Olá, {user.first_name}! Sou o assistente literário da CG.BookStore. Como posso ajudar você hoje? Posso recomendar livros, falar sobre autores ou ajudar a navegar no site."
        else:
            return "Olá! Sou o assistente literário da CG.BookStore. Como posso ajudar você hoje? Posso recomendar livros, falar sobre autores ou ajudar a navegar no site."

    def _handle_agradecimento(self, entities, user):
        """Manipula agradecimentos."""
        return "De nada! Estou sempre à disposição para ajudar com suas necessidades literárias. Mais alguma coisa em que eu possa ajudar?"

    def _handle_ajuda(self, entities, user):
        """Manipula pedidos de ajuda."""
        return """Posso ajudar você de várias formas:

1. Recomendar livros por gênero (ex: "recomende livros de fantasia")
2. Informar sobre funcionalidades do site (ex: "onde encontro meus favoritos?")
3. Em breve poderei fornecer sinopses e informações sobre autores

Como posso ajudar você hoje?"""

    def _adapt_response_to_literary_context(self, input_text, response):
        """Adapta a resposta do modelo para o contexto literário."""
        # Palavras-chave relacionadas a literatura
        book_keywords = ['livro', 'autor', 'literatura', 'ler', 'leitura', 'história', 'romance', 'poesia']

        # Verificar se a resposta já está no contexto literário
        is_already_literary = any(keyword in response.lower() for keyword in book_keywords)

        if not is_already_literary and any(keyword in input_text.lower() for keyword in book_keywords):
            literary_phrases = [
                "Como amante de literatura, ",
                "Falando de livros, ",
                "No mundo da literatura, ",
                "Como seu assistente literário, ",
                "Para quem aprecia bons livros, "
            ]

            import random
            prefix = random.choice(literary_phrases)
            first_letter = response[0].lower()
            rest = response[1:] if len(response) > 1 else ""

            return prefix + first_letter + rest

        return response


# Instância singleton para uso no aplicativo
chatbot = ChatbotService()