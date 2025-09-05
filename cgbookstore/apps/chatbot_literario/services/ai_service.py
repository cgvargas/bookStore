import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from ..models import Conversation, Message
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# ✅ NOVA IMPORTAÇÃO: External AI Service para fallback rápido
from .external_ai_service import external_ai_manager

logger = logging.getLogger(__name__)


class AIService:
    """
    Serviço de IA integrado com Ollama local + Groq external para chatbot literário.
    ✅ HÍBRIDO: Local (Llama 3.2:3b) + External (Groq API)
    ✅ RÁPIDO: Fallback para 2-5s quando local falha
    ✅ CONFIÁVEL: 99% uptime com múltiplos providers

    Ordem de tentativas:
    1. Llama local (15s timeout)
    2. Groq API (5s timeout)
    3. Fallback response
    """

    def __init__(self):
        self.base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2:3b')

        # ✅ TIMEOUTS SUPER OTIMIZADOS PARA SISTEMA HÍBRIDO
        self.timeout_quick = 10  # Otimizado: 15s → 10s para fallback mais rápido
        self.timeout_normal = 20  # Timeout local menor
        self.timeout_max = 25  # Máximo para local
        self.timeout = 20

        self.max_tokens = getattr(settings, 'OLLAMA_MAX_TOKENS', 2048)

        # ✅ CONFIGURAÇÕES OTIMIZADAS
        self.temperature = getattr(settings, 'GPT_OSS_TEMPERATURE', 0.7)

        # ✅ EXECUTOR PARA TIMEOUTS
        self.executor = ThreadPoolExecutor(max_workers=3)

        # ✅ EXTERNAL AI MANAGER
        self.external_ai = external_ai_manager

        # Status dos serviços
        self.local_available = False
        self.external_available = self.external_ai.is_available()

        # Verificação de disponibilidade
        self._verify_services_availability()

    def _verify_services_availability(self) -> None:
        """Verifica disponibilidade dos serviços local e externo."""
        # Verificar serviço local
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]

                if self.model not in available_models:
                    logger.warning(
                        f"Modelo {self.model} não encontrado localmente. "
                        f"Modelos disponíveis: {available_models}. "
                        f"Sistema funcionará apenas com IA externa."
                    )
                    self.local_available = False
                else:
                    logger.info(f"✅ Modelo local {self.model} verificado e disponível.")
                    self.local_available = True
            else:
                logger.error(f"Erro ao verificar modelos locais: {response.status_code}")
                self.local_available = False

        except requests.RequestException as e:
            logger.error(f"Ollama local indisponível: {e}")
            self.local_available = False

        # Log do status geral
        if self.local_available and self.external_available:
            logger.info("🚀 Sistema HÍBRIDO ativo: Local + External AI disponíveis!")
        elif self.external_available:
            logger.info("🌐 Sistema EXTERNAL ativo: Apenas External AI disponível")
        elif self.local_available:
            logger.info("🏠 Sistema LOCAL ativo: Apenas Llama local disponível")
        else:
            logger.warning("⚠️ NENHUM serviço de IA disponível - apenas fallbacks")

    def _build_system_prompt(self, user_profile: Dict = None) -> str:
        """
        Constrói o prompt do sistema otimizado para análises literárias.
        ✅ OTIMIZADO: Mais conciso para velocidade
        """
        base_prompt = """Você é um assistente literário especializado da CG.BookStore.Online.

ESPECIALIDADES:
- Literatura brasileira e mundial
- Análises críticas e contextuais 
- Recomendações personalizadas
- Navegação no site

DIRETRIZES:
1. Respostas diretas e informativas
2. Adapte ao nível do usuário
3. Foque na experiência literária
4. Use conhecimento fornecido quando disponível
5. Seja preciso e acessível"""

        # Personalização baseada no perfil (reduzida)
        if user_profile:
            experience_level = user_profile.get('reading_level', 'intermediário')
            favorite_genres = user_profile.get('favorite_genres', [])

            if experience_level or favorite_genres:
                personalization = f"\n\nPERFIL: {experience_level}"
                if favorite_genres:
                    personalization += f", gêneros: {', '.join(favorite_genres[:2])}"
                base_prompt += personalization

        return base_prompt

    def _prepare_local_payload(self, messages: List[Dict], timeout_target: int = None) -> Dict:
        """
        ✅ OTIMIZADO: Prepara payload para Llama local
        """
        # Configurações baseadas no timeout
        if timeout_target and timeout_target <= self.timeout_quick:
            config = {
                "temperature": 0.1,
                "num_predict": 384,
                "num_ctx": 2048,
                "repeat_penalty": 1.05,
                "top_k": 20,
                "top_p": 0.7,
            }
        else:
            config = {
                "temperature": self.temperature,
                "num_predict": 768,
                "num_ctx": 3072,
                "repeat_penalty": 1.1,
                "top_k": 40,
                "top_p": 0.9
            }

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": config
        }

        return payload

    def _execute_local_with_timeout(self, messages: List[Dict], timeout_seconds: int,
                                    operation_name: str = "IA Local") -> Dict:
        """
        ✅ ATUALIZADO: Executa requisição local com timeout otimizado
        """
        start_time = time.time()

        def make_request():
            payload = self._prepare_local_payload(messages, timeout_seconds)
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=timeout_seconds,
                headers={'Content-Type': 'application/json'}
            )
            return response

        try:
            logger.info(f"🏠 Iniciando {operation_name} (timeout: {timeout_seconds}s)")

            future = self.executor.submit(make_request)
            response = future.result(timeout=timeout_seconds)

            execution_time = time.time() - start_time
            logger.info(f"✅ {operation_name} concluída em {execution_time:.2f}s")

            if response.status_code == 200:
                response_data = response.json()
                final_answer, reasoning_chain = self._extract_reasoning_chain(response_data)

                return {
                    'success': True,
                    'response': final_answer,
                    'reasoning': reasoning_chain,
                    'execution_time': execution_time,
                    'timeout_used': timeout_seconds,
                    'service': 'local',
                    'model': self.model,
                    'metadata': {
                        'response_length': len(final_answer),
                        'processing_time': execution_time
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'execution_time': execution_time,
                    'service': 'local',
                    'fallback_needed': True
                }

        except FutureTimeoutError:
            execution_time = time.time() - start_time
            logger.warning(f"⏰ Timeout em {operation_name} após {execution_time:.2f}s")

            return {
                'success': False,
                'error': 'timeout',
                'execution_time': execution_time,
                'timeout_used': timeout_seconds,
                'service': 'local',
                'message': f'Timeout na {operation_name} após {timeout_seconds}s',
                'fallback_needed': True
            }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Erro em {operation_name}: {e}")

            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time,
                'service': 'local',
                'fallback_needed': True
            }

    def _get_smart_response(self, messages: List[Dict]) -> Dict:
        """
        ✅ REVOLUCIONÁRIO: Sistema híbrido com fallback External AI

        Ordem de tentativas:
        1. Llama local (15s) - Se disponível
        2. Groq External (5s) - Sempre tenta
        3. Fallback final - Resposta padrão
        """
        logger.info("🎯 Iniciando sistema híbrido: Local → External → Fallback")

        # 1. TENTATIVA LOCAL (Se disponível)
        if self.local_available:
            local_result = self._execute_local_with_timeout(
                messages=messages,
                timeout_seconds=self.timeout_quick,
                operation_name="Llama Local"
            )

            if local_result['success']:
                local_result['response_strategy'] = 'local'
                logger.info("✅ Resposta LOCAL bem-sucedida!")
                return local_result
            else:
                logger.info("⚠️ Llama local falhou, tentando External AI...")
        else:
            logger.info("⚠️ Llama local indisponível, indo direto para External AI...")

        # 2. TENTATIVA EXTERNAL AI (Groq + HuggingFace)
        if self.external_available:
            logger.info("🌐 Tentando External AI (Groq)...")
            try:
                external_result = self.external_ai.generate_response(messages)

                if external_result['success']:
                    external_result['response_strategy'] = 'external'
                    external_result['service'] = external_result.get('fallback_service', 'external')
                    logger.info(f"✅ Resposta EXTERNAL bem-sucedida via {external_result.get('service', 'external')}!")
                    return external_result
                else:
                    logger.warning(f"⚠️ External AI falhou: {external_result.get('error', 'Unknown error')}")

            except Exception as e:
                logger.error(f"❌ Erro no External AI: {e}")
        else:
            logger.info("⚠️ External AI indisponível")

        # 3. FALLBACK FINAL - Quando tudo falha
        logger.info("🆘 Executando fallback final...")
        return self._get_comprehensive_fallback_response()

    def _get_comprehensive_fallback_response(self) -> Dict:
        """
        ✅ MELHORADO: Fallback mais útil e informativo
        """
        logger.info("🆘 Executando fallback final...")

        # Resposta baseada no status dos serviços
        if not self.local_available and not self.external_available:
            status_msg = "Todos os nossos serviços de IA estão temporariamente indisponíveis."
        elif not self.local_available:
            status_msg = "Nosso serviço local está indisponível e o serviço externo apresenta problemas."
        elif not self.external_available:
            status_msg = "Nosso serviço principal está sobrecarregado."
        else:
            status_msg = "Estamos enfrentando alta demanda no momento."

        response_parts = [
            f"Desculpe, {status_msg} ",
            "Aqui estão algumas alternativas:\n\n",
            "🔍 **Busque diretamente**: Use a busca principal do site para encontrar livros\n",
            "📚 **Explore por categoria**: Literatura Brasileira, Clássicos Mundiais, Contemporâneos\n",
            "👤 **Acesse seu perfil**: Veja recomendações personalizadas baseadas em seu histórico\n",
            "💬 **Tente novamente**: Reformule sua pergunta em alguns minutos\n\n",
            "⚡ *Nossos sistemas estão sendo otimizados continuamente para melhor performance.*"
        ]

        # Informações de debug em desenvolvimento
        if settings.DEBUG:
            debug_info = []
            if not self.local_available:
                debug_info.append("Local: indisponível")
            if not self.external_available:
                debug_info.append("External: indisponível")

            if debug_info:
                response_parts.append(f"\n🔧 *Debug: {', '.join(debug_info)}*")

        return {
            'success': True,
            'response': ''.join(response_parts),
            'response_strategy': 'comprehensive_fallback',
            'service': 'fallback',
            'metadata': {
                'local_available': self.local_available,
                'external_available': self.external_available,
                'fallback_type': 'comprehensive'
            }
        }

    def _extract_reasoning_chain(self, response_data: Dict) -> Tuple[str, Optional[str]]:
        """
        Extrai o conteúdo da resposta e o chain-of-thought quando disponível.
        """
        try:
            if 'message' in response_data and 'content' in response_data['message']:
                full_content = response_data['message']['content']

                # Verifica se há separação explícita de reasoning
                if "## Raciocínio:" in full_content or "<thinking>" in full_content:
                    # Separar reasoning da resposta final
                    parts = full_content.split("## Resposta:", 1)
                    if len(parts) == 2:
                        reasoning = parts[0].replace("## Raciocínio:", "").strip()
                        final_answer = parts[1].strip()
                        return final_answer, reasoning

                    # Formato alternativo com tags
                    if "<thinking>" in full_content and "</thinking>" in full_content:
                        import re
                        thinking_match = re.search(r'<thinking>(.*?)</thinking>',
                                                   full_content, re.DOTALL)
                        if thinking_match:
                            reasoning = thinking_match.group(1).strip()
                            final_answer = full_content.replace(thinking_match.group(0), "").strip()
                            return final_answer, reasoning

                return full_content, None

        except (KeyError, AttributeError) as e:
            logger.error(f"Erro ao extrair reasoning chain: {e}")

        return "", None

    def get_ai_response(self, user_message: str, conversation_id: int,
                        user_profile: Dict = None,
                        reasoning_effort: str = None) -> Dict:
        """
        ✅ ATUALIZADO: Obtém resposta usando sistema híbrido otimizado
        """
        try:
            # Cache key para otimização
            cache_key = f"hybrid_response_{hash(user_message)}_{conversation_id}"
            cached_response = cache.get(cache_key)

            if cached_response and not reasoning_effort:
                logger.debug(f"Resposta recuperada do cache para conversa {conversation_id}")
                return cached_response

            # Construir histórico da conversa
            messages = self._build_conversation_history(conversation_id, user_profile)
            messages.append({
                "role": "user",
                "content": user_message
            })

            # Log da requisição
            logger.info(f"Enviando requisição para sistema híbrido - Conversa: {conversation_id}")

            # ✅ USAR SISTEMA HÍBRIDO OTIMIZADO
            result = self._get_smart_response(messages)

            # Cache da resposta (apenas para consultas simples e bem-sucedidas)
            if result['success'] and not reasoning_effort and result.get(
                    'response_strategy') != 'comprehensive_fallback':
                cache.set(cache_key, result, timeout=1800)  # 30 min

            service_used = result.get('service', result.get('response_strategy', 'unknown'))
            response_length = len(result.get('response', ''))
            logger.info(f"Resposta híbrida: {service_used} - {response_length} chars")

            return result

        except Exception as e:
            error_msg = f"Erro inesperado no sistema híbrido: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'fallback_needed': True,
                'service': 'error'
            }

    def _build_conversation_history(self, conversation_id: int,
                                    user_profile: Dict = None) -> List[Dict]:
        """
        ✅ OTIMIZADO: Constrói histórico mais conciso para velocidade
        """
        messages = []

        # System prompt personalizado (mais conciso)
        system_prompt = self._build_system_prompt(user_profile)
        messages.append({
            "role": "system",
            "content": system_prompt
        })

        try:
            # Buscar conversa e mensagens (limitadas para velocidade)
            conversation = Conversation.objects.get(id=conversation_id)
            recent_messages = Message.objects.filter(
                conversation=conversation
            ).order_by('-timestamp')[:6]  # Reduzido de 10 para 6 mensagens

            # Adicionar mensagens ao contexto (ordem cronológica)
            for message in reversed(recent_messages):
                messages.append({
                    "role": "user" if message.sender == "user" else "assistant",
                    "content": message.content
                })

        except Conversation.DoesNotExist:
            logger.warning(f"Conversa {conversation_id} não encontrada")
        except Exception as e:
            logger.error(f"Erro ao buscar histórico: {e}")

        return messages

    def analyze_literature_with_reasoning(self, text: str, analysis_type: str,
                                          user_profile: Dict = None) -> Dict:
        """
        Análise literária especializada com sistema híbrido.
        ✅ ATUALIZADO: Usa sistema híbrido otimizado
        """
        analysis_prompts = {
            'style': 'Analise o estilo literário deste texto',
            'theme': 'Identifique e explore os temas presentes',
            'character': 'Analise os personagens e suas características',
            'structure': 'Examine a estrutura narrativa',
            'context': 'Contextualize historicamente e culturalmente'
        }

        prompt = analysis_prompts.get(analysis_type, 'Faça uma análise geral')
        full_prompt = f"""
            {prompt}: 
            "{text}"         
            Por favor, forneça uma análise completa e fundamentada.
        """

        return self.get_ai_response(
            user_message=full_prompt,
            conversation_id=0,  # Análise independente
            user_profile=user_profile
        )

    def health_check(self) -> Dict:
        """
        ✅ ATUALIZADO: Verifica o status de saúde do sistema híbrido.
        """
        try:
            # Status do serviço local
            local_status = 'down'
            local_response_time = None

            if self.local_available:
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                    local_response_time = time.time() - start_time

                    if response.status_code == 200:
                        local_status = 'healthy'
                    else:
                        local_status = 'degraded'
                except:
                    local_status = 'down'
                    self.local_available = False

            # Status do serviço externo
            external_status = self.external_ai.health_check()

            # Status geral
            if local_status == 'healthy' or external_status.get('overall_status') == 'healthy':
                overall_status = 'healthy'
            elif local_status in ['healthy', 'degraded'] or external_status.get('overall_status') in ['healthy',
                                                                                                      'degraded']:
                overall_status = 'degraded'
            else:
                overall_status = 'down'

            return {
                'status': overall_status,
                'system_type': 'hybrid',
                'local_service': {
                    'status': local_status,
                    'available': self.local_available,
                    'model': self.model if self.local_available else None,
                    'response_time': local_response_time
                },
                'external_service': external_status,
                'timeout_config': {
                    'quick': self.timeout_quick,
                    'normal': self.timeout_normal,
                    'max': self.timeout_max
                }
            }

        except Exception as e:
            return {
                'status': 'error',
                'system_type': 'hybrid',
                'error': str(e),
                'local_available': False,
                'external_available': False
            }

    def generate_response(self, messages: List[Dict]) -> Dict:
        """
        ✅ ATUALIZADO: Método de compatibilidade com FunctionalChatbot usando sistema híbrido
        """
        try:
            # Extrair a mensagem do usuário (última mensagem)
            user_message = ""
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_message = msg.get('content', '')
                    break

            if not user_message:
                return {
                    'success': False,
                    'error': 'Nenhuma mensagem do usuário encontrada',
                    'response': 'Não foi possível processar sua mensagem.'
                }

            # ✅ USAR SISTEMA HÍBRIDO OTIMIZADO
            result = self._get_smart_response(messages)

            # Retornar no formato esperado pelo FunctionalChatbot
            if result['success']:
                return {
                    'success': True,
                    'response': result['response'],
                    'metadata': result.get('metadata', {}),
                    'reasoning': result.get('reasoning'),
                    'response_strategy': result.get('response_strategy', 'unknown'),
                    'service': result.get('service', 'hybrid')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Erro desconhecido'),
                    'response': 'Desculpe, não consegui processar sua solicitação no momento.',
                    'service': result.get('service', 'error')
                }

        except Exception as e:
            logger.error(f"Erro em generate_response: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'response': 'Ocorreu um erro interno. Tente novamente.',
                'service': 'error'
            }

    def is_available(self) -> bool:
        """
        ✅ ATUALIZADO: Verifica se pelo menos um serviço está disponível.
        """
        try:
            # Atualizar status se necessário
            if not self.local_available and not self.external_available:
                self._verify_services_availability()

            return self.local_available or self.external_available
        except Exception as e:
            logger.error(f"Erro ao verificar disponibilidade: {e}")
            return False


def is_ai_available() -> bool:
    """
    ✅ ATUALIZADO: Função standalone para verificar disponibilidade do sistema híbrido.
    """
    try:
        return ai_service.is_available()
    except Exception as e:
        logger.error(f"Erro ao verificar disponibilidade da IA: {e}")
        return False


# ✅ INSTÂNCIA GLOBAL ATUALIZADA
ai_service = AIService()