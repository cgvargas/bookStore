# cgbookstore/apps/chatbot_literario/services/external_ai_service.py

import requests
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class GroqService:
    """
    Serviço de IA externa usando Groq API - Solução rápida para chatbot literário
    ✅ VELOCIDADE: 2-5 segundos vs 50-120s local
    ✅ CONFIABILIDADE: 99.9% uptime
    ✅ GRATUITO: Para uso educacional/literário
    """

    def __init__(self):
        # Configurações da API Groq
        self.api_key = getattr(settings, 'GROQ_API_KEY', '')
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = getattr(settings, 'GROQ_MODEL', 'llama3-8b-8192')

        # Configurações otimizadas
        self.timeout = 10  # Groq é muito rápido
        self.max_tokens = getattr(settings, 'GROQ_MAX_TOKENS', 1024)
        self.temperature = 0.7

        # Rate limiting (Groq free tier)
        self.requests_per_minute = 100
        self.cache_timeout = 1800  # 30 min

        # Verificação de disponibilidade
        self.available = self._check_availability()

        if self.available:
            logger.info("✅ GroqService inicializado com sucesso!")
        else:
            logger.warning("⚠️ GroqService indisponível (API key ou conectividade)")

    def _check_availability(self) -> bool:
        """Verifica se o serviço Groq está disponível"""
        if not self.api_key:
            logger.warning("GROQ_API_KEY não configurada")
            return False

        try:
            # Teste simples de conectividade
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Teste com uma mensagem mínima
            test_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "teste"}],
                "max_tokens": 10
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=test_payload,
                headers=headers,
                timeout=5
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Erro ao verificar disponibilidade do Groq: {e}")
            return False

    def _build_literary_system_prompt(self) -> str:
        """
        System prompt super otimizado para literatura brasileira e mundial
        ✅ PRECISÃO: Evita erros como "Quarta Asa = Clarice Lispector"
        ✅ BRASILEIRO: Foco em literatura nacional
        """
        return """Você é o assistente literário especialista da CG.BookStore.Online.

EXPERTISE PRINCIPAL:
• Literatura Brasileira: Machado de Assis, Clarice Lispector, José de Alencar, Lima Barreto, Guimarães Rosa
• Literatura Mundial: Clássicos e contemporâneos  
• Movimentos: Romantismo, Realismo, Modernismo brasileiro
• Análises críticas e contexto histórico

REGRAS CRÍTICAS:
1. Se não souber sobre um livro/autor ESPECÍFICO, diga "Não tenho informações confiáveis sobre esta obra"
2. NUNCA invente informações sobre autores brasileiros
3. Priorize autores e obras do catálogo brasileiro
4. Para autores internacionais, seja preciso nas datas e obras
5. Use conhecimento da base quando fornecido

ESTILO: Culto mas acessível, educativo e envolvente.

Responda com precisão sobre literatura, admitindo quando não souber algo específico."""

    def _prepare_groq_payload(self, messages: List[Dict]) -> Dict:
        """
        Prepara payload otimizado para Groq API
        ✅ OTIMIZADO: Para velocidade e qualidade literária
        """

        # System prompt literário
        literary_messages = [
            {"role": "system", "content": self._build_literary_system_prompt()}
        ]

        # Adicionar mensagens (limitadas para velocidade)
        context_messages = messages[-6:]  # Últimas 6 mensagens para contexto
        literary_messages.extend(context_messages)

        payload = {
            "model": self.model,
            "messages": literary_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": 0.9,
            "stream": False
        }

        return payload

    def generate_response(self, messages: List[Dict]) -> Dict:
        """
        Gera resposta usando Groq API
        ✅ RÁPIDO: 2-5 segundos típico
        ✅ CONFIÁVEL: Com tratamento de erro
        """
        if not self.available:
            return {
                'success': False,
                'error': 'Groq service not available',
                'response': 'Serviço externo indisponível.'
            }

        start_time = time.time()

        try:
            # Cache key baseado nas mensagens
            cache_key = f"groq_response_{hash(str(messages))}"
            cached_response = cache.get(cache_key)

            if cached_response:
                logger.debug("Resposta Groq recuperada do cache")
                return cached_response

            # Preparar requisição
            payload = self._prepare_groq_payload(messages)
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            logger.info(f"🚀 Enviando requisição para Groq (modelo: {self.model})")

            # Fazer requisição
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            execution_time = time.time() - start_time

            if response.status_code == 200:
                response_data = response.json()

                # Extrair resposta
                bot_response = response_data['choices'][0]['message']['content']

                # Metadados
                usage = response_data.get('usage', {})

                result = {
                    'success': True,
                    'response': bot_response,
                    'execution_time': execution_time,
                    'service': 'groq',
                    'model': self.model,
                    'metadata': {
                        'tokens_used': usage.get('total_tokens', 0),
                        'prompt_tokens': usage.get('prompt_tokens', 0),
                        'completion_tokens': usage.get('completion_tokens', 0),
                        'response_length': len(bot_response)
                    }
                }

                # Cache da resposta
                cache.set(cache_key, result, timeout=self.cache_timeout)

                logger.info(f"✅ Resposta Groq gerada em {execution_time:.2f}s")
                return result

            else:
                error_msg = f"Groq API error: {response.status_code}"
                logger.error(f"{error_msg} - {response.text}")

                return {
                    'success': False,
                    'error': error_msg,
                    'response': 'Erro na API externa. Tente novamente.',
                    'execution_time': execution_time
                }

        except requests.Timeout:
            execution_time = time.time() - start_time
            logger.warning(f"⏰ Timeout na Groq API após {execution_time:.2f}s")

            return {
                'success': False,
                'error': 'timeout',
                'response': 'Timeout na resposta. Tente uma pergunta mais simples.',
                'execution_time': execution_time
            }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Erro na Groq API: {e}")

            return {
                'success': False,
                'error': str(e),
                'response': 'Erro técnico na IA externa.',
                'execution_time': execution_time
            }

    def health_check(self) -> Dict:
        """
        Health check do serviço Groq
        """
        if not self.available:
            return {
                'status': 'down',
                'service': 'groq',
                'error': 'API key not configured or service unavailable'
            }

        try:
            # Teste rápido
            test_messages = [{"role": "user", "content": "teste rápido"}]
            result = self.generate_response(test_messages)

            if result['success']:
                return {
                    'status': 'healthy',
                    'service': 'groq',
                    'model': self.model,
                    'response_time': result.get('execution_time', 0),
                    'available': True
                }
            else:
                return {
                    'status': 'degraded',
                    'service': 'groq',
                    'error': result.get('error', 'Unknown error'),
                    'available': False
                }

        except Exception as e:
            return {
                'status': 'down',
                'service': 'groq',
                'error': str(e),
                'available': False
            }

    def is_available(self) -> bool:
        """Verifica se o serviço está disponível"""
        return self.available and bool(self.api_key)


class HuggingFaceService:
    """
    Serviço de backup usando Hugging Face Inference API
    ✅ GRATUITO: Completamente free
    ✅ BACKUP: Quando Groq falhar
    """

    def __init__(self):
        self.api_key = getattr(settings, 'HF_API_KEY', '')
        self.model = getattr(settings, 'HF_MODEL', 'microsoft/DialoGPT-large')
        self.base_url = "https://api-inference.huggingface.co/models"
        self.timeout = 15  # HF pode ser mais lenta
        self.available = bool(self.api_key)

        if self.available:
            logger.info("✅ HuggingFaceService disponível como backup")

    def generate_response(self, messages: List[Dict]) -> Dict:
        """Gera resposta usando HF Inference API"""
        if not self.available:
            return {
                'success': False,
                'error': 'HuggingFace service not available',
                'response': 'Serviço de backup indisponível.'
            }

        start_time = time.time()

        try:
            # Extrair última mensagem do usuário
            user_message = ""
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_message = msg.get('content', '')
                    break

            if not user_message:
                return {
                    'success': False,
                    'error': 'No user message found',
                    'response': 'Mensagem inválida.'
                }

            # Preparar payload HF
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "inputs": f"Literatura: {user_message}",
                "parameters": {
                    "max_length": 500,
                    "temperature": 0.7,
                    "do_sample": True
                }
            }

            response = requests.post(
                f"{self.base_url}/{self.model}",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            execution_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                if isinstance(data, list) and len(data) > 0:
                    bot_response = data[0].get('generated_text', 'Resposta indisponível.')

                    return {
                        'success': True,
                        'response': bot_response,
                        'service': 'huggingface',
                        'execution_time': execution_time
                    }

            return {
                'success': False,
                'error': f'HF API error: {response.status_code}',
                'response': 'Erro no serviço de backup.',
                'execution_time': execution_time
            }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Erro HuggingFace: {e}")

            return {
                'success': False,
                'error': str(e),
                'response': 'Erro técnico no backup.',
                'execution_time': execution_time
            }

    def is_available(self) -> bool:
        return self.available


class ExternalAIManager:
    """
    Gerenciador de múltiplos serviços de IA externa
    ✅ FALLBACK: Groq → HuggingFace → Error
    ✅ INTELIGENTE: Escolha automática do melhor serviço
    """

    def __init__(self):
        self.groq = GroqService()
        self.hf = HuggingFaceService()

        # Prioridade dos serviços
        self.services = [
            ('groq', self.groq),
            ('huggingface', self.hf)
        ]

        # Log dos serviços disponíveis
        available_services = [name for name, service in self.services if service.is_available()]
        logger.info(f"🌐 External AI Services disponíveis: {available_services}")

    def generate_response(self, messages: List[Dict]) -> Dict:
        """
        Gera resposta usando o melhor serviço disponível
        ✅ FALLBACK: Automático entre serviços
        ✅ RÁPIDO: Prioriza velocidade
        """
        last_error = None

        for service_name, service in self.services:
            if not service.is_available():
                logger.debug(f"Serviço {service_name} indisponível, tentando próximo...")
                continue

            try:
                logger.info(f"🔄 Tentando {service_name}...")
                result = service.generate_response(messages)

                if result['success']:
                    logger.info(f"✅ Resposta gerada por {service_name} em {result.get('execution_time', 0):.2f}s")
                    result['fallback_service'] = service_name
                    return result
                else:
                    last_error = result.get('error', 'Unknown error')
                    logger.warning(f"⚠️ {service_name} falhou: {last_error}")

            except Exception as e:
                last_error = str(e)
                logger.error(f"❌ Erro em {service_name}: {e}")
                continue

        # Todos os serviços falharam
        logger.error("❌ Todos os serviços externos falharam")

        return {
            'success': False,
            'error': f'All external services failed. Last error: {last_error}',
            'response': self._get_fallback_response(),
            'fallback_service': 'none'
        }

    def _get_fallback_response(self) -> str:
        """Resposta de fallback quando tudo falha"""
        return (
            "Nossos serviços de IA estão temporariamente indisponíveis. "
            "Aqui estão algumas alternativas:\n\n"
            "🔍 **Busque diretamente**: Use a busca principal do site\n"
            "📚 **Explore categorias**: Visite literatura brasileira, clássicos mundiais\n"
            "💬 **Reformule**: Tente uma pergunta mais específica em alguns minutos\n\n"
            "⚡ *Nossos sistemas estão sendo otimizados para melhor performance.*"
        )

    def health_check(self) -> Dict:
        """Health check de todos os serviços"""
        services_status = {}

        for service_name, service in self.services:
            try:
                if hasattr(service, 'health_check'):
                    services_status[service_name] = service.health_check()
                else:
                    services_status[service_name] = {
                        'status': 'healthy' if service.is_available() else 'down',
                        'available': service.is_available()
                    }
            except Exception as e:
                services_status[service_name] = {
                    'status': 'error',
                    'error': str(e),
                    'available': False
                }

        # Status geral
        available_count = sum(1 for status in services_status.values()
                              if status.get('available', False))

        overall_status = 'healthy' if available_count > 0 else 'down'

        return {
            'overall_status': overall_status,
            'available_services': available_count,
            'total_services': len(self.services),
            'services': services_status
        }

    def is_available(self) -> bool:
        """Verifica se pelo menos um serviço está disponível"""
        return any(service.is_available() for _, service in self.services)


# ✅ INSTÂNCIAS GLOBAIS
groq_service = GroqService()
external_ai_manager = ExternalAIManager()


# ✅ FUNÇÃO DE CONVENIÊNCIA
def get_external_response(messages: List[Dict]) -> Dict:
    """Função standalone para obter resposta de IA externa"""
    return external_ai_manager.generate_response(messages)


def is_external_ai_available() -> bool:
    """Verifica se IA externa está disponível"""
    return external_ai_manager.is_available()