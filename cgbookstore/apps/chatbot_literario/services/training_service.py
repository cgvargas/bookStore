import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class ChatbotTrainingService:
    """
    Serviço para treinamento e melhoria contínua do chatbot literário.
    Versão simplificada sem embeddings.
    """
    # Definir initialized como atributo de classe para garantir que sempre existe
    initialized = False

    def __init__(self):
        # Definição de atributos
        self.conversation_data = []
        self.knowledge_base = []
        self.data_folder = os.path.join('cgbookstore', 'apps', 'chatbot_literario', 'data')

        # Garantir que a pasta de dados existe
        os.makedirs(self.data_folder, exist_ok=True)

        # Carregar dados no início
        try:
            self._load_data()
            # Definir como inicializado após carregar com sucesso
            self.__class__.initialized = True
            logger.info("Serviço de treinamento inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar serviço de treinamento: {str(e)}")
            # Garantir que initialized seja False em caso de erro
            self.__class__.initialized = False

    def _load_data(self):
        """Carrega dados de treinamento e base de conhecimento."""
        try:
            # Carregar conversas salvas
            conversation_path = os.path.join(self.data_folder, 'conversations.json')
            if os.path.exists(conversation_path):
                with open(conversation_path, 'r', encoding='utf-8') as f:
                    self.conversation_data = json.load(f)
                logger.info(f"Carregadas {len(self.conversation_data)} conversas")
            else:
                self.conversation_data = []
                logger.info("Arquivo de conversas não encontrado. Iniciando com lista vazia.")

            # Carregar base de conhecimento
            knowledge_path = os.path.join(self.data_folder, 'knowledge_base.json')
            if os.path.exists(knowledge_path):
                with open(knowledge_path, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
                logger.info(f"Carregados {len(self.knowledge_base)} itens na base de conhecimento")
            else:
                self.knowledge_base = []
                logger.info("Arquivo de base de conhecimento não encontrado. Iniciando com lista vazia.")
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {str(e)}")
            self.conversation_data = []
            self.knowledge_base = []
            raise

    def save_data(self):
        """Salva dados de treinamento em disco."""
        try:
            # Salvar conversas
            conversation_path = os.path.join(self.data_folder, 'conversations.json')
            with open(conversation_path, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_data, f, ensure_ascii=False, indent=2)

            # Salvar base de conhecimento
            knowledge_path = os.path.join(self.data_folder, 'knowledge_base.json')
            with open(knowledge_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)

            logger.info("Dados salvos com sucesso")
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {str(e)}")

    def add_conversation(self, user_input, bot_response, feedback=None):
        """Adiciona uma conversa ao conjunto de dados de treinamento."""
        try:
            conversation = {
                'user_input': user_input,
                'bot_response': bot_response,
                'timestamp': datetime.now().isoformat(),
                'feedback': feedback
            }

            self.conversation_data.append(conversation)

            # Salvar a cada 10 novas conversas
            if len(self.conversation_data) % 10 == 0:
                self.save_data()

            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar conversa: {str(e)}")
            return False

    def add_knowledge_item(self, question, answer, category=None, source=None):
        """Adiciona um item à base de conhecimento."""
        try:
            knowledge_item = {
                'question': question,
                'answer': answer,
                'category': category,
                'source': source,
                'timestamp': datetime.now().isoformat()
            }

            self.knowledge_base.append(knowledge_item)
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar item à base de conhecimento: {str(e)}")
            return False

    def search_knowledge_base(self, query, top_k=3):
        """
        Busca itens relevantes na base de conhecimento.
        Implementação simplificada usando correspondência de palavras-chave.
        """
        if not self.knowledge_base:
            return []

        try:
            # Busca simples por palavras-chave
            query_words = set(query.lower().split())
            results = []

            for idx, item in enumerate(self.knowledge_base):
                question_words = set(item['question'].lower().split())
                # Calcular uma pontuação simples baseada na interseção de palavras
                common_words = question_words.intersection(query_words)
                if common_words:
                    score = len(common_words) / max(len(question_words), len(query_words))
                    results.append((item, score))

            # Ordenar por relevância
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.error(f"Erro ao buscar na base de conhecimento: {str(e)}")
            return []

    def add_feedback(self, conversation_index, feedback):
        """Adiciona feedback do usuário a uma conversa existente."""
        try:
            if 0 <= conversation_index < len(self.conversation_data):
                self.conversation_data[conversation_index]['feedback'] = feedback
                self.save_data()
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao adicionar feedback: {str(e)}")
            return False

    def generate_training_statistics(self):
        """Gera estatísticas sobre os dados de treinamento."""
        try:
            stats = {
                'total_conversations': len(self.conversation_data),
                'total_knowledge_items': len(self.knowledge_base),
                'conversations_with_feedback': sum(1 for c in self.conversation_data if c.get('feedback')),
                'positive_feedback': sum(1 for c in self.conversation_data
                                         if c.get('feedback') and c['feedback'].get('helpful') == True),
                'negative_feedback': sum(1 for c in self.conversation_data
                                         if c.get('feedback') and c['feedback'].get('helpful') == False),
                'knowledge_categories': {}
            }

            # Contagem por categoria
            for item in self.knowledge_base:
                category = item.get('category', 'uncategorized')
                if category in stats['knowledge_categories']:
                    stats['knowledge_categories'][category] += 1
                else:
                    stats['knowledge_categories'][category] = 1

            return stats
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas: {str(e)}")
            return {}


# Instância global para uso no aplicativo
training_service = ChatbotTrainingService()