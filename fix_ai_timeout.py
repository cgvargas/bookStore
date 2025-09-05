#!/usr/bin/env python
"""
Script para corrigir timeouts do AI Service
Execução: python fix_ai_timeout.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from cgbookstore.apps.chatbot_literario.services.ai_service import ai_service


def main():
    print("🔧 CORREÇÃO DE TIMEOUT DO AI SERVICE")
    print("=" * 50)

    try:
        # Verificar configuração atual
        print(f"📊 Timeout atual - Quick: {ai_service.timeout_quick}s")
        print(f"📊 Timeout atual - Normal: {ai_service.timeout_normal}s")
        print(f"📊 Timeout atual - Max: {ai_service.timeout_max}s")

        # Ajustar timeouts para GPT-OSS
        print("\n🔄 Ajustando timeouts...")

        ai_service.timeout_quick = 30  # Era 15s → 30s
        ai_service.timeout_normal = 90  # Era 45s → 90s
        ai_service.timeout_max = 150  # Era 90s → 150s

        print(f"✅ Timeout ajustado - Quick: {ai_service.timeout_quick}s")
        print(f"✅ Timeout ajustado - Normal: {ai_service.timeout_normal}s")
        print(f"✅ Timeout ajustado - Max: {ai_service.timeout_max}s")

        # Testar conectividade
        print("\n🧪 TESTANDO CONECTIVIDADE...")
        health = ai_service.health_check()

        print(f"📡 Status: {health.get('status', 'unknown')}")
        print(f"🤖 Modelo disponível: {health.get('model_available', False)}")
        print(f"⏱️ Tempo de resposta: {health.get('response_time', 0):.2f}s")

        if health.get('status') == 'healthy':
            print("✅ AI SERVICE FUNCIONANDO!")

            # Teste simples de geração
            print("\n🎯 TESTE RÁPIDO DE GERAÇÃO...")
            test_messages = [
                {"role": "system", "content": "Você é um assistente literário da CG.BookStore."},
                {"role": "user", "content": "Quem escreveu Dom Casmurro? Responda em uma frase."}
            ]

            print("⏳ Gerando resposta...")
            result = ai_service.generate_response(test_messages)

            if result.get('success'):
                response_text = result.get('response', '')
                print(f"✅ Resposta gerada: {len(response_text)} caracteres")
                print(f"📝 Resposta: {response_text}")
                print(f"⚡ Estratégia: {result.get('response_strategy', 'N/A')}")
                print(f"⏱️ Metadata: {result.get('metadata', {})}")
            else:
                print(f"❌ Erro na geração: {result.get('error', 'Desconhecido')}")
                return False

        else:
            print("❌ AI SERVICE COM PROBLEMAS")
            print(f"Erro: {health.get('error', 'Desconhecido')}")
            return False

        print("\n" + "=" * 50)
        print("🎯 CORREÇÃO CONCLUÍDA COM SUCESSO!")
        print("🚀 Execute agora: python manage.py test_system --test-chat")
        return True

    except Exception as e:
        print(f"❌ ERRO NO SCRIPT: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)