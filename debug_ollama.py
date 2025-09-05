#!/usr/bin/env python
"""
Script de diagnóstico detalhado Ollama + Django
Execução: python debug_ollama.py
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


def test_direct_ollama():
    """Teste direto com Ollama sem Django"""
    print("🔧 TESTE DIRETO COM OLLAMA")
    print("-" * 40)

    try:
        # Teste 1: Verificar modelos
        print("1. Verificando modelos...")
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"   ✅ {len(models)} modelo(s) encontrado(s)")
            for model in models:
                print(f"   📦 {model['name']} ({model['size'] / 1e9:.1f}GB)")
        else:
            print(f"   ❌ Erro: {response.status_code}")
            return False

        # Teste 2: Geração simples
        print("\n2. Teste de geração simples...")
        payload = {
            "model": "gpt-oss:20b",
            "prompt": "Quem escreveu Dom Casmurro?",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 50
            }
        }

        start_time = time.time()
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60
        )
        duration = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            print(f"   ✅ Resposta em {duration:.2f}s: {len(response_text)} chars")
            print(f"   📝 Texto: {response_text[:100]}...")
            return True
        else:
            print(f"   ❌ Erro: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Exceção: {e}")
        return False


def test_django_ai_service():
    """Teste do AI Service do Django"""
    print("\n🔧 TESTE DJANGO AI SERVICE")
    print("-" * 40)

    try:
        # Verificar configurações
        print("1. Configurações:")
        print(f"   📡 Base URL: {ai_service.base_url}")
        print(f"   🤖 Modelo: {ai_service.model}")
        print(f"   ⏱️ Timeouts: {ai_service.timeout_quick}s/{ai_service.timeout_normal}s/{ai_service.timeout_max}s")

        # Teste de payload
        print("\n2. Testando payload...")
        messages = [
            {"role": "system", "content": "Você é um assistente literário."},
            {"role": "user", "content": "Quem escreveu Dom Casmurro?"}
        ]

        payload = ai_service._prepare_gpt_oss_payload(messages, 60)
        print(f"   📦 Payload: {len(json.dumps(payload))} bytes")
        print(f"   🔧 Opções: {payload.get('options', {})}")

        # Teste manual da requisição
        print("\n3. Requisição manual...")
        start_time = time.time()

        response = requests.post(
            f"{ai_service.base_url}/api/chat",
            json=payload,
            timeout=60,
            headers={'Content-Type': 'application/json'}
        )

        duration = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            content = result.get('message', {}).get('content', '')
            print(f"   ✅ Sucesso em {duration:.2f}s: {len(content)} chars")
            print(f"   📝 Resposta: {content[:150]}...")
            return True
        else:
            print(f"   ❌ Erro HTTP {response.status_code}")
            print(f"   📝 Resposta: {response.text[:200]}...")
            return False

    except Exception as e:
        print(f"   ❌ Exceção: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_service_method():
    """Teste do método do AI Service"""
    print("\n🔧 TESTE MÉTODO AI SERVICE")
    print("-" * 40)

    try:
        messages = [
            {"role": "system", "content": "Você é um assistente literário."},
            {"role": "user", "content": "Quem escreveu Dom Casmurro? Responda em uma frase curta."}
        ]

        print("1. Executando _get_smart_response...")
        result = ai_service._get_smart_response(messages)

        print(f"   📊 Sucesso: {result.get('success')}")
        print(f"   ⚡ Estratégia: {result.get('response_strategy')}")
        print(f"   ⏱️ Tempo: {result.get('execution_time', 0):.2f}s")
        print(f"   📝 Resposta: {result.get('response', '')[:100]}...")

        if result.get('error'):
            print(f"   ❌ Erro: {result.get('error')}")

        return result.get('success', False)

    except Exception as e:
        print(f"   ❌ Exceção: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("🚀 DIAGNÓSTICO COMPLETO OLLAMA + DJANGO")
    print("=" * 60)

    results = []

    # Teste 1: Ollama direto
    results.append(test_direct_ollama())

    # Teste 2: Django AI Service
    results.append(test_django_ai_service())

    # Teste 3: Método AI Service
    results.append(test_ai_service_method())

    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("-" * 30)
    print(f"🔧 Ollama direto: {'✅ OK' if results[0] else '❌ FALHA'}")
    print(f"🔧 Django AI Service: {'✅ OK' if results[1] else '❌ FALHA'}")
    print(f"🔧 Método AI Service: {'✅ OK' if results[2] else '❌ FALHA'}")

    if all(results):
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("🔧 Problema deve estar em outro lugar...")
    else:
        print("\n⚠️ PROBLEMA IDENTIFICADO!")
        failed_tests = []
        if not results[0]: failed_tests.append("Ollama direto")
        if not results[1]: failed_tests.append("Django AI Service")
        if not results[2]: failed_tests.append("Método AI Service")
        print(f"❌ Falhas: {', '.join(failed_tests)}")

    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)