#!/usr/bin/env python
"""
Script para trocar modelo do AI Service para Llama 3.2
Execução: python switch_to_llama32.py
"""

import os
import sys
import django
import requests
import json
import time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from cgbookstore.apps.chatbot_literario.services.ai_service import ai_service


def test_model(model_name):
    """Testa um modelo específico"""
    print(f"🔧 Testando modelo: {model_name}")

    try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "Você é um assistente literário da CG.BookStore."},
                {"role": "user", "content": "Quem escreveu Dom Casmurro? Responda em uma frase."}
            ],
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 100,
                "num_ctx": 2048
            }
        }

        start_time = time.time()
        response = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=60,
            headers={'Content-Type': 'application/json'}
        )
        duration = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            content = result.get('message', {}).get('content', '')
            print(f"   ✅ Sucesso em {duration:.1f}s: {len(content)} chars")
            print(f"   📝 Resposta: {content.strip()}")
            return True, content.strip()
        else:
            error_msg = response.text
            print(f"   ❌ Erro HTTP {response.status_code}: {error_msg}")
            return False, error_msg

    except Exception as e:
        print(f"   ❌ Exceção: {e}")
        return False, str(e)


def main():
    print("🚀 TROCA DE MODELO PARA LLAMA 3.2")
    print("=" * 50)

    # Verificar modelos disponíveis
    print("📋 Verificando modelos disponíveis...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("✅ Modelos encontrados:")
            for model in models:
                size_gb = model['size'] / 1e9
                print(f"   📦 {model['name']} ({size_gb:.1f}GB)")
        else:
            print("❌ Erro ao listar modelos")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

    # Testar modelos menores
    test_models = ["llama3.2:3b", "llama3.2:latest"]
    working_model = None

    for model in test_models:
        print(f"\n🧪 Testando {model}...")
        success, response = test_model(model)
        if success:
            working_model = model
            print(f"✅ {model} funcionando perfeitamente!")
            break
        else:
            print(f"❌ {model} falhou")

    if not working_model:
        print("\n❌ NENHUM MODELO FUNCIONOU!")
        print("💡 Solução: Aumentar RAM ou usar modelo ainda menor")
        return False

    # Atualizar AI Service
    print(f"\n🔄 Atualizando AI Service para usar {working_model}...")

    old_model = ai_service.model
    ai_service.model = working_model

    print(f"   📊 Modelo anterior: {old_model}")
    print(f"   📊 Novo modelo: {ai_service.model}")

    # Testar novo modelo no AI Service
    print(f"\n🧪 Testando AI Service com {working_model}...")

    try:
        messages = [
            {"role": "system", "content": "Você é um assistente literário da CG.BookStore."},
            {"role": "user", "content": "Quem escreveu Dom Casmurro?"}
        ]

        result = ai_service.generate_response(messages)

        if result.get('success'):
            response_text = result.get('response', '')
            print(f"   ✅ AI Service funcionando: {len(response_text)} chars")
            print(f"   📝 Resposta: {response_text[:150]}...")
            print(f"   ⚡ Estratégia: {result.get('response_strategy', 'N/A')}")

            # Verificar se não é fallback
            if result.get('response_strategy') != 'final_fallback':
                print("   🎉 PROBLEMA RESOLVIDO!")

                # Salvar configuração (informativo)
                print(f"\n💾 Para tornar permanente, atualize o settings.py:")
                print(f"   OLLAMA_MODEL = '{working_model}'")

                return True
            else:
                print("   ⚠️ Ainda caindo no fallback...")
                return False
        else:
            print(f"   ❌ Erro: {result.get('error', 'Desconhecido')}")
            return False

    except Exception as e:
        print(f"   ❌ Exceção: {e}")
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 SUCESSO! Sistema funcionando com novo modelo!")
        print("🚀 Execute: python manage.py test_system --test-chat")
    else:
        print("\n❌ FALHA! Problemas persistem.")

    sys.exit(0 if success else 1)