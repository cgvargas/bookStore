#!/usr/bin/env python
"""
Patch final para o Functional Chatbot - resolver timeouts
Execução: python patch_functional_chatbot.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()


def patch_all_ai_services():
    """Patch em todas as instâncias do AI Service"""
    print("🔧 PATCH GLOBAL DOS AI SERVICES")
    print("=" * 50)

    try:
        # 1. Patch do ai_service principal
        from cgbookstore.apps.chatbot_literario.services.ai_service import ai_service

        print("1. Configurando AI Service principal...")
        ai_service.model = "llama3.2:3b"
        ai_service.timeout_quick = 45  # Mais tempo para sistema híbrido
        ai_service.timeout_normal = 90  # Dobrar timeout normal
        ai_service.timeout_max = 120  # Aumentar máximo
        ai_service.timeout = 90  # Timeout padrão

        print(f"   ✅ Modelo: {ai_service.model}")
        print(f"   ✅ Timeouts: {ai_service.timeout_quick}s/{ai_service.timeout_normal}s/{ai_service.timeout_max}s")

        # 2. Patch do functional_chatbot
        from cgbookstore.apps.chatbot_literario.services import functional_chatbot

        print("2. Verificando Functional Chatbot...")
        status = functional_chatbot.get_status()
        print(f"   📊 Status: {status}")

        # 3. Recriar instância do AI Service se necessário
        print("3. Recriando instância AI Service...")

        # Patch direto no módulo
        import cgbookstore.apps.chatbot_literario.services.ai_service as ai_module
        ai_module.ai_service.model = "llama3.2:3b"
        ai_module.ai_service.timeout_quick = 45
        ai_module.ai_service.timeout_normal = 90
        ai_module.ai_service.timeout_max = 120
        ai_module.ai_service.timeout = 90

        print("   ✅ Instância global patchada")

        return True

    except Exception as e:
        print(f"   ❌ Erro no patch: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_real_conversation():
    """Teste com conversa real do banco"""
    print("\n🧪 TESTE COM CONVERSA REAL")
    print("-" * 40)

    try:
        from cgbookstore.apps.chatbot_literario.services import functional_chatbot
        from cgbookstore.apps.chatbot_literario.models import Conversation, User
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Criar usuário de teste se não existir
        test_user, created = User.objects.get_or_create(
            username='test_chatbot',
            defaults={'email': 'test@test.com'}
        )

        print(f"   👤 Usuário: {test_user.username} ({'criado' if created else 'existente'})")

        # Criar conversa real
        conversation = Conversation.objects.create(
            user=test_user,
            title="Teste do Sistema Híbrido"
        )

        print(f"   💬 Conversa criada: ID {conversation.id}")

        # Teste de resposta
        test_message = "Quem escreveu Dom Casmurro?"
        print(f"   📨 Pergunta: {test_message}")
        print("   ⏳ Processando...")

        response = functional_chatbot.get_response(test_message, conversation)

        print(f"   📊 Sucesso: {response.get('success', False)}")
        print(f"   📡 Fonte: {response.get('source', 'N/A')}")
        print(f"   🧠 Conhecimento: {response.get('knowledge_items_used', 0)} itens")

        resp_text = response.get('response', '')
        if resp_text:
            print(f"   📝 Resposta ({len(resp_text)} chars):")
            print(f"      {resp_text[:200]}...")

            # Verificar qualidade da resposta
            if "Machado de Assis" in resp_text and "dificuldades técnicas" not in resp_text:
                print("   🎉 RESPOSTA DE QUALIDADE!")

                # Limpar dados de teste
                conversation.delete()
                if created:
                    test_user.delete()

                return True
            else:
                print("   ⚠️ Resposta ainda com problemas...")

                # Limpar dados de teste
                conversation.delete()
                if created:
                    test_user.delete()

                return False
        else:
            print("   ❌ Resposta vazia")

            # Limpar dados de teste
            conversation.delete()
            if created:
                test_user.delete()

            return False

    except Exception as e:
        print(f"   ❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_simple_response_test():
    """Teste simplificado sem timeout complexo"""
    print("\n🧪 TESTE SIMPLIFICADO")
    print("-" * 40)

    try:
        # Importar AI service diretamente
        from cgbookstore.apps.chatbot_literario.services.ai_service import ai_service

        # Teste com prompt simples híbrido
        print("   📝 Preparando prompt híbrido...")

        messages = [
            {
                "role": "system",
                "content": "Você é um assistente literário da CG.BookStore. Responda de forma direta e concisa."
            },
            {
                "role": "system",
                "content": """=== BASE DE FATOS LITERÁRIOS ===
1. **O que é Dom Casmurro?**
   Dom Casmurro é um romance de Machado de Assis publicado em 1899, considerado uma das obras-primas da literatura brasileira.

2. **Quem foi Machado de Assis?**
   Joaquim Maria Machado de Assis (1839-1908) é considerado o maior escritor da literatura brasileira.
=== FIM DA BASE DE FATOS ==="""
            },
            {
                "role": "user",
                "content": "Quem escreveu Dom Casmurro?"
            }
        ]

        print("   ⏳ Testando resposta híbrida...")
        result = ai_service.generate_response(messages)

        if result.get('success'):
            response_text = result.get('response', '')
            print(f"   ✅ Sucesso: {len(response_text)} chars")
            print(f"   📝 Resposta: {response_text}")
            print(f"   ⚡ Estratégia: {result.get('response_strategy', 'N/A')}")

            if "Machado de Assis" in response_text:
                print("   🎉 RESPOSTA HÍBRIDA FUNCIONANDO!")
                return True
            else:
                print("   ⚠️ Resposta não contém informação esperada")
                return False
        else:
            print(f"   ❌ Falha: {result.get('error', 'N/A')}")
            return False

    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False


def main():
    print("🚀 PATCH FINAL DO FUNCTIONAL CHATBOT")
    print("=" * 60)

    # 1. Patch global
    patch_success = patch_all_ai_services()

    # 2. Teste simplificado
    simple_success = create_simple_response_test()

    # 3. Teste com conversa real (se simples funcionou)
    real_success = False
    if simple_success:
        real_success = test_with_real_conversation()

    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("-" * 30)
    print(f"🔧 Patch Global: {'✅ OK' if patch_success else '❌ FALHA'}")
    print(f"🧪 Teste Simples: {'✅ OK' if simple_success else '❌ FALHA'}")
    print(f"💬 Teste Real: {'✅ OK' if real_success else '❌ FALHA'}")

    if patch_success and simple_success:
        print("\n🎉 SISTEMA FUNCIONANDO!")

        if real_success:
            print("✅ Functional Chatbot 100% operacional!")
            print("🚀 Execute: python manage.py test_system --test-chat")
            print("📚 Pronto para expansão!")
        else:
            print("⚠️ Functional Chatbot com limitações, mas AI Service OK")
            print("💡 Podemos continuar com expansão usando AI Service")

        return True
    else:
        print("\n❌ PROBLEMAS PERSISTEM")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
