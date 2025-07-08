# cgbookstore/apps/chatbot_literario/services/ai_service.py
import requests
import json
import logging
from django.conf import settings
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class AIService:
    """
    Serviço de IA otimizado para integração com Ollama usando a API de Chat.
    """

    def __init__(self):
        self.config = settings.OLLAMA_CONFIG
        # ✅ CORREÇÃO: Usando as chaves corretas do dicionário
        self.ollama_url = self.config.get('base_url', 'http://localhost:11434')
        self.ollama_model = self.config.get('model', 'llama3.2:3b')
        self.timeout = self.config.get('timeout', 60)

    def generate_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Gera resposta usando a API de Chat do Ollama.

        Args:
            messages: Uma lista de mensagens no formato [{'role': 'system'|'user'|'assistant', 'content': '...'}].

        Returns:
            Dicionário com a resposta da IA.
        """
        if not self.is_available():
            logger.warning("Ollama não está disponível. Retornando resposta de fallback.")
            return self._fallback_response()

        try:
            # ✅ Usa o endpoint /api/chat, que é o correto para conversas
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.6}
                },
                headers={'Content-Type': 'application/json'},
                timeout=self.timeout
            )
            response.raise_for_status()  # Lança exceção para status 4xx/5xx

            result = response.json()
            content = result.get('message', {}).get('content', '').strip()

            logger.info(f"Resposta recebida do Ollama: {content[:100]}...")

            return {
                'success': True,
                'response': content,
                'model_used': result.get('model', self.ollama_model),
                'confidence': 0.85,  # Confiança alta pois veio da IA
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na chamada ao Ollama (/api/chat): {e}")
            return self._fallback_response(error_message=str(e))
        except Exception as e:
            logger.error(f"Erro inesperado no AIService: {e}", exc_info=True)
            return self._fallback_response(error_message=str(e))

    def _fallback_response(self, error_message: str = None) -> Dict[str, Any]:
        """Resposta de fallback aprimorada quando Ollama falha."""
        user_friendly_message = (
            "Peço desculpas, estou enfrentando uma instabilidade na minha conexão com o sistema de inteligência artificial no momento. 😔\n\n"
            "Por favor, tente sua pergunta novamente em alguns instantes. Se o problema persistir, nossa equipe já foi notificada."
        )
        return {
            'success': False,
            'response': user_friendly_message,
            'source': 'fallback_error',
            'error': error_message or "Falha na comunicação com o serviço de IA."
        }

    def is_available(self) -> bool:
        """Verifica se o serviço Ollama está ativo e acessível."""
        try:
            # O endpoint raiz é suficiente para um health check rápido.
            response = requests.get(self.ollama_url, timeout=5)
            return response.status_code == 200 and "Ollama is running" in response.text
        except requests.exceptions.RequestException:
            return False


# Instância global
ai_service = AIService()


# Função global para compatibilidade
def is_ai_available() -> bool:
    return ai_service.is_available()