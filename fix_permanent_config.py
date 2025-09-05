#!/usr/bin/env python
"""
Script para correção permanente de configuração do AI Service
Execução: python fix_permanent_config.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from cgbookstore.apps.chatbot_literario.services.ai_service import ai_service


def patch_ai_service():
    """Aplica correções permanentes no AI Service"""
    print("🔧 APLICANDO CORREÇÕES PERMANENTES")
    print("=" * 50)

    # 1. Configurar modelo
    print("1. Configurando modelo...")
    ai_service.model = "llama3.2:3b"
    print(f"   ✅ Modelo: {ai_service.model}")

    # 2. Configurar timeouts adequados para Llama 3.2
    print("2. Configurando timeouts...")
    ai_service.timeout_quick = 30  # Era 15s → 30s (Llama precisa de ~25s)
    ai_service.timeout_normal = 60  # Era 45s → 60s
    ai_service.timeout_max = 90  # Era 90s → mantém
    ai_service.timeout = 60  # Timeout padrão

    print(f"   ✅ Quick: {ai_service.timeout_quick}s")
    print(f"   ✅ Normal: {ai_service.timeout_normal}s")
    print(f"   ✅ Max: {ai_service.timeout_max}s")

    # 3. Teste integrado
    print("\n3. Testando configuração...")

    try:
        messages = [
            {"role": "system", "content": "Você é um assistente literário."},
            {"role": "user", "content": "Quem escreveu Dom Casmurro? Responda em uma frase."}
        ]

        print("   ⏳ Executando teste...")
        result = ai_service._get_smart_response(messages)

        print(f"   📊 Sucesso: {result.get('success')}")
        print(f"   ⚡ Estratégia: {result.get('response_strategy')}")
        print(f"   ⏱️ Tempo: {result.get('execution_time', 0):.1f}s")

        if result.get('success') and result.get('response_strategy') != 'final_fallback':
            response_text = result.get('response', '')
            print(f"   📝 Resposta: {response_text[:100]}...")
            print("   🎉 CONFIGURAÇÃO FUNCIONANDO!")
            return True
        else:
            print(f"   ❌ Ainda em fallback: {result.get('error', 'N/A')}")
            return False

    except Exception as e:
        print(f"   ❌ Erro no teste: {e}")
        return False


def test_functional_chatbot():
    """Testa o FunctionalChatbot diretamente"""
    print("\n🧪 TESTANDO FUNCTIONAL CHATBOT")
    print("-" * 40)

    try:
        from cgbookstore.apps.chatbot_literario.services import functional_chatbot
        from cgbookstore.apps.chatbot_literario.models import Conversation

        # Criar conversa mock para teste
        class MockConversation:
            def __init__(self):
                self.id = 999
                self.messages = type('MockManager', (), {
                    'order_by': lambda self, field: []
                })()

        test_conversation = MockConversation()
        test_message = "Quem escreveu Dom Casmurro?"

        print(f"   📨 Pergunta: {test_message}")
        print("   ⏳ Processando...")

        response = functional_chatbot.get_response(test_message, test_conversation)

        print(f"   📊 Sucesso: {response.get('success', False)}")
        print(f"   📡 Fonte: {response.get('source', 'N/A')}")
        print(f"   🧠 Conhecimento usado: {response.get('knowledge_items_used', 0)} itens")

        resp_text = response.get('response', '')
        if resp_text:
            print(f"   📝 Resposta ({len(resp_text)} chars): {resp_text[:120]}...")

            # Verificar se não é fallback
            if "dificuldades técnicas" not in resp_text:
                print("   🎉 FUNCTIONAL CHATBOT FUNCIONANDO!")
                return True
            else:
                print("   ⚠️ Ainda usando fallback...")
                return False
        else:
            print("   ❌ Resposta vazia")
            return False

    except Exception as e:
        print(f"   ❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("🚀 CORREÇÃO PERMANENTE DO SISTEMA")
    print("=" * 60)

    # Aplicar patches
    ai_success = patch_ai_service()

    # Testar functional chatbot
    chatbot_success = test_functional_chatbot()

    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESULTADO DA CORREÇÃO")
    print("-" * 30)
    print(f"🔧 AI Service: {'✅ OK' if ai_success else '❌ FALHA'}")
    print(f"🤖 Functional Chatbot: {'✅ OK' if chatbot_success else '❌ FALHA'}")

    if ai_success and chatbot_success:
        print("\n🎉 SISTEMA TOTALMENTE FUNCIONAL!")
        print("🚀 Execute: python manage.py test_system --test-chat")
        print("📚 Pronto para continuar expansão!")
        return True
    else:
        print("\n⚠️ AINDA HÁ PROBLEMAS...")
        if not ai_success:
            print("❌ AI Service precisa de mais ajustes")
        if not chatbot_success:
            print("❌ Functional Chatbot com problemas")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)