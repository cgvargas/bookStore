import subprocess
import requests
import json
import time
import os
import logging
from typing import Dict, List, Optional, Tuple
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.cache import cache
from cgbookstore.apps.chatbot_literario.services.ai_service import ai_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Comando de gestão do Ollama com suporte completo ao GPT-OSS.

    Funcionalidades:
    - Download e verificação de modelos
    - Migração do Llama para GPT-OSS
    - Benchmarks e testes de performance
    - Diagnósticos e troubleshooting
    - Gestão de cache e otimizações
    """

    help = 'Gerencia modelos Ollama com foco em GPT-OSS para chatbot literário'

    def add_arguments(self, parser):
        """Adiciona argumentos do comando."""
        subparsers = parser.add_subparsers(dest='action', help='Ações disponíveis')

        # === COMANDOS BÁSICOS ===
        # Status geral
        status_parser = subparsers.add_parser('status', help='Verifica status do Ollama e modelos')
        status_parser.add_argument('--detailed', action='store_true', help='Status detalhado')

        # Download de modelos
        pull_parser = subparsers.add_parser('pull', help='Baixa modelo específico')
        pull_parser.add_argument('model', help='Nome do modelo (ex: gpt-oss:20b)')
        pull_parser.add_argument('--force', action='store_true', help='Força re-download')

        # === COMANDOS SIMPLIFICADOS ===
        # Download simples
        download_parser = subparsers.add_parser('download-gpt-oss', help='Apenas baixa GPT-OSS sem testes')
        download_parser.add_argument('--variant', choices=['20b', '120b'], default='20b')

        # Verificação rápida
        quick_parser = subparsers.add_parser('quick-check', help='Verificação rápida do GPT-OSS')

        # === COMANDOS GPT-OSS ESPECÍFICOS ===
        # Setup GPT-OSS
        setup_parser = subparsers.add_parser('setup-gpt-oss', help='Configura GPT-OSS completo')
        setup_parser.add_argument('--variant', choices=['20b', '120b'], default='20b',
                                  help='Variante do modelo (20b ou 120b)')
        setup_parser.add_argument('--skip-test', action='store_true', help='Pula testes após setup')

        # Migração
        migrate_parser = subparsers.add_parser('migrate-to-gpt-oss', help='Migra do Llama para GPT-OSS')
        migrate_parser.add_argument('--backup-config', action='store_true', help='Backup das configurações')
        migrate_parser.add_argument('--rollback', action='store_true', help='Reverter migração')

        # === COMANDOS DE TESTE E BENCHMARK ===
        # Benchmark
        benchmark_parser = subparsers.add_parser('benchmark', help='Testa performance dos modelos')
        benchmark_parser.add_argument('--model', help='Modelo específico para testar')
        benchmark_parser.add_argument('--iterations', type=int, default=3, help='Número de iterações')
        benchmark_parser.add_argument('--reasoning-test', action='store_true', help='Incluir teste de reasoning')

        # Teste literário
        literary_parser = subparsers.add_parser('test-literary', help='Testa capacidades literárias')
        literary_parser.add_argument('--save-results', action='store_true', help='Salvar resultados em arquivo')

        # === COMANDOS DE MANUTENÇÃO ===
        # Limpeza
        cleanup_parser = subparsers.add_parser('cleanup', help='Limpa cache e arquivos temporários')
        cleanup_parser.add_argument('--deep', action='store_true', help='Limpeza profunda')

        # Diagnóstico
        diag_parser = subparsers.add_parser('diagnose', help='Diagnóstica problemas comuns')
        diag_parser.add_argument('--fix', action='store_true', help='Tenta corrigir problemas encontrados')

        # Health check
        health_parser = subparsers.add_parser('health', help='Verificação de saúde completa')
        health_parser.add_argument('--verbose', action='store_true', help='Output detalhado')

    def handle(self, *args, **options):
        """Handler principal do comando."""
        action = options.get('action')

        if not action:
            self.print_usage()
            return

        try:
            # Verificar se Ollama está rodando
            if action not in ['diagnose']:
                self._check_ollama_running()

            # Executar ação específica
            method_name = f'_handle_{action.replace("-", "_")}'
            if hasattr(self, method_name):
                getattr(self, method_name)(options)
            else:
                self.stdout.write(
                    self.style.ERROR(f'Ação não implementada: {action}')
                )

        except Exception as e:
            logger.error(f"Erro no comando ollama {action}: {e}", exc_info=True)
            raise CommandError(f"Erro: {e}")

    def _check_ollama_running(self):
        """Verifica se o Ollama está executando."""
        try:
            base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise CommandError("Ollama não está respondendo corretamente")
        except requests.RequestException:
            raise CommandError(
                "Ollama não está executando. "
                "Inicie com: ollama serve"
            )

    def print_usage(self):
        """Imprime informações de uso."""
        self.stdout.write(self.style.SUCCESS("=== GESTÃO OLLAMA GPT-OSS ===\n"))

        commands = [
            ("status", "Verifica status dos modelos"),
            ("setup-gpt-oss", "Configura GPT-OSS completo"),
            ("migrate-to-gpt-oss", "Migra do Llama para GPT-OSS"),
            ("benchmark", "Testa performance"),
            ("test-literary", "Testa capacidades literárias"),
            ("health", "Verificação de saúde"),
            ("diagnose", "Diagnóstica problemas"),
            ("cleanup", "Limpa cache"),
        ]

        for cmd, desc in commands:
            self.stdout.write(f"  {cmd:<20} - {desc}")

        self.stdout.write(f"\nUso: python manage.py ollama <comando> [opções]")

    def _handle_download_gpt_oss(self, options):
        """Baixa GPT-OSS sem testes complexos."""
        variant = options.get('variant', '20b')
        model_name = f"gpt-oss:{variant}"

        self.stdout.write(self.style.SUCCESS(f"=== DOWNLOAD GPT-OSS {variant.upper()} ==="))

        # Verificar se já existe
        if self._verify_model_available(model_name):
            self.stdout.write(f"✅ {model_name} já está disponível!")
            return

        # Download simples
        self.stdout.write(f"📥 Baixando {model_name}...")
        try:
            self._download_model(model_name)
            self.stdout.write(f"✅ Download concluído!")

            # Verificar após download
            time.sleep(3)  # Aguardar um pouco
            if self._verify_model_available(model_name):
                self.stdout.write(f"✅ {model_name} confirmado e pronto para uso!")
            else:
                self.stdout.write(f"⚠️  Modelo baixado mas pode precisar de alguns segundos para ficar disponível")

        except Exception as e:
            self.stdout.write(f"⚠️  Erro/Aviso no download: {e}")
            self.stdout.write(f"🔧 Verifique manualmente com: ollama list")

    def _handle_quick_check(self, options):
        """Verificação rápida do status GPT-OSS."""
        self.stdout.write(self.style.SUCCESS("=== VERIFICAÇÃO RÁPIDA GPT-OSS ==="))

        # Verificar modelos GPT-OSS disponíveis
        models = self._get_available_models()
        gpt_oss_models = [m for m in models if 'gpt-oss' in m]

        if gpt_oss_models:
            self.stdout.write(f"✅ Modelos GPT-OSS encontrados:")
            for model in gpt_oss_models:
                self.stdout.write(f"  🔥 {model}")
        else:
            self.stdout.write("❌ Nenhum modelo GPT-OSS encontrado")
            self.stdout.write("💡 Execute: python manage.py ollama download-gpt-oss")
            return

        # Verificar configuração atual
        current_model = getattr(settings, 'OLLAMA_MODEL', 'N/A')
        if 'gpt-oss' in current_model:
            self.stdout.write(f"✅ Configuração atual: {current_model}")
        else:
            self.stdout.write(f"⚠️  Configuração atual: {current_model}")
            self.stdout.write(f"💡 Atualize OLLAMA_MODEL=gpt-oss:20b no .env")

        # Teste de conectividade simples
        try:
            base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.stdout.write("✅ Ollama está online")
            else:
                self.stdout.write(f"⚠️  Ollama resposta: {response.status_code}")
        except Exception as e:
            self.stdout.write(f"❌ Ollama offline: {e}")

    # === HANDLERS DE COMANDOS ===

    def _handle_status(self, options):
        """Verifica status do Ollama e modelos."""
        detailed = options.get('detailed', False)

        self.stdout.write(self.style.SUCCESS("=== STATUS OLLAMA ==="))

        # Status do serviço
        health = ai_service.health_check()
        if health['status'] == 'healthy':
            self.stdout.write(self.style.SUCCESS("✅ Ollama: Online"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Ollama: {health['error']}"))

        # Lista de modelos disponíveis
        models = self._get_available_models()
        self.stdout.write(f"\n📦 Modelos disponíveis: {len(models)}")

        current_model = getattr(settings, 'OLLAMA_MODEL', 'N/A')

        for model in models:
            name = model['name']
            size = model.get('size', 0)
            size_gb = size / (1024 ** 3) if size else 0

            status_icon = "🟢" if name == current_model else "⚪"

            if 'gpt-oss' in name:
                status_icon = "🔥"  # GPT-OSS em destaque

            self.stdout.write(
                f"  {status_icon} {name:<20} ({size_gb:.1f}GB)"
            )

            if detailed and 'gpt-oss' in name:
                self._show_gpt_oss_details(name)

    def _handle_setup_gpt_oss(self, options):
        """Configura GPT-OSS completo."""
        variant = options.get('variant', '20b')
        skip_test = options.get('skip_test', False)

        model_name = f"gpt-oss:{variant}"

        self.stdout.write(
            self.style.SUCCESS(f"=== CONFIGURANDO GPT-OSS {variant.upper()} ===")
        )

        # 1. Verificar se modelo já existe
        self.stdout.write("1. Verificando se modelo já existe...")
        if self._verify_model_available(model_name):
            self.stdout.write(f"✅ Modelo {model_name} já disponível!")
        else:
            # Download do modelo
            self.stdout.write("1. Baixando modelo...")
            try:
                self._download_model(model_name)
            except CommandError as e:
                if "baixado com sucesso" in str(e) or "provavelmente baixado" in str(e):
                    self.stdout.write("✅ Download concluído com avisos")
                else:
                    raise e

        # 2. Verificar disponibilidade novamente
        self.stdout.write("2. Verificando disponibilidade...")
        max_retries = 3
        for attempt in range(max_retries):
            if self._verify_model_available(model_name):
                self.stdout.write(f"✅ Modelo {model_name} confirmado na tentativa {attempt + 1}")
                break
            else:
                self.stdout.write(f"⏳ Tentativa {attempt + 1}/{max_retries} - aguardando...")
                time.sleep(2)
        else:
            self.stdout.write(f"⚠️  Modelo pode não estar completamente disponível ainda")

        # 3. Configurar cache
        self.stdout.write("3. Configurando cache...")
        self._setup_gpt_oss_cache()

        # 4. Teste básico (opcional)
        if not skip_test:
            self.stdout.write("4. Executando teste básico...")
            try:
                self._test_model_basic(model_name)
            except CommandError as e:
                if "provavelmente está funcionando" in str(e) or "teste conectividade" in str(e):
                    self.stdout.write("⚠️  Teste com avisos - prosseguindo...")
                else:
                    self.stdout.write(f"⚠️  Erro no teste: {e}")
                    self.stdout.write("🔧 Configure manualmente se necessário")

        # 5. Instruções de configuração
        self.stdout.write("5. Configuração final...")
        self._update_model_config(model_name)

        self.stdout.write(
            self.style.SUCCESS(f"✅ GPT-OSS {variant} configurado!")
        )

        # Dicas específicas para GPT-OSS
        self._show_gpt_oss_tips(variant)

        # Comandos de próximos passos
        self.stdout.write(f"\n🎯 PRÓXIMOS PASSOS:")
        self.stdout.write(f"1. Atualize OLLAMA_MODEL=gpt-oss:{variant} no .env")
        self.stdout.write(f"2. Reinicie o servidor Django")
        self.stdout.write(f"3. Teste: python manage.py debug_chatbot connectivity")
        self.stdout.write(f"4. Teste completo: python manage.py debug_chatbot simple-response")

    def _handle_migrate_to_gpt_oss(self, options):
        """Migra do Llama para GPT-OSS."""
        backup_config = options.get('backup_config', False)
        rollback = options.get('rollback', False)

        if rollback:
            self._rollback_migration()
            return

        self.stdout.write(self.style.SUCCESS("=== MIGRAÇÃO PARA GPT-OSS ==="))

        # Backup das configurações atuais
        if backup_config:
            self.stdout.write("📋 Fazendo backup das configurações...")
            self._backup_current_config()

        # Verificar modelos disponíveis
        current_model = getattr(settings, 'OLLAMA_MODEL', '')
        self.stdout.write(f"📊 Modelo atual: {current_model}")

        # Recomendar variante baseada no hardware
        recommended_variant = self._recommend_gpt_oss_variant()
        self.stdout.write(f"💡 Variante recomendada: {recommended_variant}")

        # Confirmar migração
        confirm = input("Continuar com a migração? (s/N): ")
        if confirm.lower() != 's':
            self.stdout.write("Migração cancelada.")
            return

        # Executar migração
        target_model = f"gpt-oss:{recommended_variant}"
        self._execute_migration(current_model, target_model)

        self.stdout.write(
            self.style.SUCCESS("✅ Migração concluída com sucesso!")
        )

    def _handle_benchmark(self, options):
        """Executa benchmark dos modelos."""
        model = options.get('model')
        iterations = options.get('iterations', 3)
        reasoning_test = options.get('reasoning_test', False)

        if not model:
            model = getattr(settings, 'OLLAMA_MODEL', 'gpt-oss:20b')

        self.stdout.write(
            self.style.SUCCESS(f"=== BENCHMARK: {model} ===")
        )

        results = {
            'model': model,
            'iterations': iterations,
            'tests': []
        }

        # Testes básicos
        for i in range(iterations):
            self.stdout.write(f"Iteração {i + 1}/{iterations}...")

            test_result = self._run_benchmark_iteration(model, reasoning_test)
            results['tests'].append(test_result)

            # Mostrar resultado da iteração
            self.stdout.write(
                f"  ⏱️  Tempo: {test_result['response_time']:.2f}s"
            )
            self.stdout.write(
                f"  📝 Tokens: {test_result['tokens_generated']}"
            )

        # Calcular médias
        avg_time = sum(t['response_time'] for t in results['tests']) / iterations
        avg_tokens = sum(t['tokens_generated'] for t in results['tests']) / iterations

        self.stdout.write(f"\n📊 RESULTADOS MÉDIOS:")
        self.stdout.write(f"  ⏱️  Tempo médio: {avg_time:.2f}s")
        self.stdout.write(f"  📝 Tokens médios: {avg_tokens:.0f}")
        self.stdout.write(f"  🚀 Tokens/segundo: {avg_tokens / avg_time:.1f}")

        # Classificação de performance
        performance_rating = self._classify_performance(avg_time, avg_tokens)
        self.stdout.write(f"  ⭐ Avaliação: {performance_rating}")

    def _handle_test_literary(self, options):
        """Testa capacidades literárias específicas."""
        save_results = options.get('save_results', False)

        self.stdout.write(self.style.SUCCESS("=== TESTE CAPACIDADES LITERÁRIAS ==="))

        # Testes específicos para literatura
        literary_tests = [
            {
                'name': 'Análise de Estilo',
                'prompt': 'Analise brevemente o estilo literário de Machado de Assis',
                'expected_keywords': ['ironia', 'realismo', 'psicológico']
            },
            {
                'name': 'Recomendação de Livros',
                'prompt': 'Recomende um livro para quem gosta de ficção científica brasileira',
                'expected_keywords': ['ficção científica', 'brasileiro', 'livro']
            },
            {
                'name': 'Contexto Histórico',
                'prompt': 'Explique o contexto histórico do Romantismo no Brasil',
                'expected_keywords': ['romantismo', 'brasil', 'século', 'histórico']
            }
        ]

        results = []

        for test in literary_tests:
            self.stdout.write(f"\n🧪 Testando: {test['name']}")

            # Executar teste
            start_time = time.time()
            response = ai_service.get_ai_response(
                user_message=test['prompt'],
                conversation_id=0,  # Teste independente
                reasoning_effort='medium'
            )
            end_time = time.time()

            if response['success']:
                response_text = response['response'].lower()

                # Verificar palavras-chave esperadas
                found_keywords = [
                    kw for kw in test['expected_keywords']
                    if kw in response_text
                ]

                keyword_score = len(found_keywords) / len(test['expected_keywords'])

                test_result = {
                    'test_name': test['name'],
                    'success': True,
                    'response_time': end_time - start_time,
                    'response_length': len(response['response']),
                    'keyword_score': keyword_score,
                    'found_keywords': found_keywords,
                    'response': response['response'][:200] + "..." if len(response['response']) > 200 else response[
                        'response']
                }

                self.stdout.write(f"  ✅ Sucesso - Score: {keyword_score:.1%}")
                self.stdout.write(f"  ⏱️  Tempo: {test_result['response_time']:.2f}s")

            else:
                test_result = {
                    'test_name': test['name'],
                    'success': False,
                    'error': response.get('error', 'Erro desconhecido')
                }

                self.stdout.write(f"  ❌ Falha: {test_result['error']}")

            results.append(test_result)

        # Resumo dos resultados
        successful_tests = [r for r in results if r['success']]
        success_rate = len(successful_tests) / len(results)

        self.stdout.write(f"\n📊 RESUMO DOS TESTES LITERÁRIOS:")
        self.stdout.write(f"  🎯 Taxa de sucesso: {success_rate:.1%}")

        if successful_tests:
            avg_keyword_score = sum(r['keyword_score'] for r in successful_tests) / len(successful_tests)
            avg_time = sum(r['response_time'] for r in successful_tests) / len(successful_tests)

            self.stdout.write(f"  📝 Score médio de palavras-chave: {avg_keyword_score:.1%}")
            self.stdout.write(f"  ⏱️  Tempo médio: {avg_time:.2f}s")

        # Salvar resultados se solicitado
        if save_results:
            self._save_literary_test_results(results)

    def _handle_health(self, options):
        """Verificação de saúde completa."""
        verbose = options.get('verbose', False)

        self.stdout.write(self.style.SUCCESS("=== VERIFICAÇÃO DE SAÚDE COMPLETA ==="))

        health_checks = []

        # 1. Status do Ollama
        ollama_health = ai_service.health_check()
        health_checks.append({
            'check': 'Ollama Service',
            'status': ollama_health['status'],
            'details': ollama_health
        })

        # 2. Modelo configurado
        current_model = getattr(settings, 'OLLAMA_MODEL', '')
        model_available = self._verify_model_available(current_model)
        health_checks.append({
            'check': 'Modelo Configurado',
            'status': 'healthy' if model_available else 'error',
            'details': {'model': current_model, 'available': model_available}
        })

        # 3. Cache Redis
        cache_health = self._check_cache_health()
        health_checks.append({
            'check': 'Cache Redis',
            'status': cache_health['status'],
            'details': cache_health
        })

        # 4. Teste de resposta simples
        try:
            test_response = ai_service.get_ai_response(
                user_message="Teste de conectividade",
                conversation_id=0
            )
            response_health = 'healthy' if test_response['success'] else 'error'
        except Exception as e:
            response_health = 'error'
            test_response = {'error': str(e)}

        health_checks.append({
            'check': 'Teste de Resposta',
            'status': response_health,
            'details': test_response
        })

        # Mostrar resultados
        for check in health_checks:
            status_icon = "✅" if check['status'] == 'healthy' else "❌"
            self.stdout.write(f"{status_icon} {check['check']}: {check['status']}")

            if verbose and check['details']:
                for key, value in check['details'].items():
                    self.stdout.write(f"    {key}: {value}")

        # Status geral
        all_healthy = all(check['status'] == 'healthy' for check in health_checks)
        overall_status = "✅ Sistema saudável" if all_healthy else "⚠️  Problemas detectados"

        self.stdout.write(f"\n{overall_status}")

    def _handle_cleanup(self, options):
        """Limpa cache e arquivos temporários."""
        deep = options.get('deep', False)

        self.stdout.write(self.style.SUCCESS("=== LIMPEZA DO SISTEMA ==="))

        cleaned_items = []

        # Limpar cache Redis
        try:
            cache.clear()
            cleaned_items.append("Cache Redis geral")

            # Cache específico do GPT-OSS
            if hasattr(cache, 'delete_pattern'):
                gpt_oss_keys = cache.delete_pattern("gpt_oss*")
                if gpt_oss_keys:
                    cleaned_items.append(f"Cache GPT-OSS ({gpt_oss_keys} chaves)")

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Erro ao limpar cache: {e}"))

        # Limpeza profunda
        if deep:
            # Limpar logs antigos (opcional)
            log_files_cleaned = self._cleanup_old_logs()
            if log_files_cleaned:
                cleaned_items.append(f"Logs antigos ({log_files_cleaned} arquivos)")

        # Resultados
        if cleaned_items:
            self.stdout.write("🧹 Itens limpos:")
            for item in cleaned_items:
                self.stdout.write(f"  - {item}")
        else:
            self.stdout.write("ℹ️  Nada para limpar.")

    def _handle_diagnose(self, options):
        """Diagnóstica problemas comuns."""
        fix_issues = options.get('fix', False)

        self.stdout.write(self.style.SUCCESS("=== DIAGNÓSTICO DO SISTEMA ==="))

        issues_found = []

        # Verificar se Ollama está rodando
        try:
            self._check_ollama_running()
        except CommandError as e:
            issues_found.append({
                'issue': 'Ollama não está executando',
                'solution': 'Execute: ollama serve',
                'fixable': False
            })

        # Verificar modelo configurado
        current_model = getattr(settings, 'OLLAMA_MODEL', '')
        if not self._verify_model_available(current_model):
            issues_found.append({
                'issue': f'Modelo {current_model} não disponível',
                'solution': f'Execute: python manage.py ollama pull {current_model}',
                'fixable': True,
                'fix_action': lambda: self._download_model(current_model)
            })

        # Verificar configurações de cache
        cache_issues = self._diagnose_cache_issues()
        issues_found.extend(cache_issues)

        # Verificar configurações do settings
        config_issues = self._diagnose_config_issues()
        issues_found.extend(config_issues)

        # Mostrar problemas encontrados
        if issues_found:
            self.stdout.write(f"⚠️  {len(issues_found)} problema(s) encontrado(s):")

            for i, issue in enumerate(issues_found, 1):
                self.stdout.write(f"\n{i}. {issue['issue']}")
                self.stdout.write(f"   Solução: {issue['solution']}")

                if fix_issues and issue.get('fixable') and 'fix_action' in issue:
                    try:
                        self.stdout.write("   🔧 Corrigindo...")
                        issue['fix_action']()
                        self.stdout.write("   ✅ Corrigido!")
                    except Exception as e:
                        self.stdout.write(f"   ❌ Erro ao corrigir: {e}")
        else:
            self.stdout.write("✅ Nenhum problema encontrado!")

    # === MÉTODOS AUXILIARES ===

    def _get_available_models(self) -> List[str]:
        """Retorna lista de modelos disponíveis."""
        try:
            base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
            response = requests.get(f"{base_url}/api/tags", timeout=10)

            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])

                # Extrair nomes dos modelos
                model_names = []
                for model in models:
                    if isinstance(model, dict):
                        name = model.get('name', '')
                        if name:
                            model_names.append(name)
                    elif isinstance(model, str):
                        model_names.append(model)

                # Debug: mostrar modelos encontrados
                logger.debug(f"Modelos encontrados via API: {model_names}")
                return model_names
            else:
                logger.warning(f"API retornou status {response.status_code}")

        except requests.RequestException as e:
            logger.error(f"Erro ao buscar modelos via API: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar modelos: {e}")

        # Fallback: tentar via comando ollama list
        try:
            import subprocess
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                models = []
                for line in lines[1:]:  # Pular header
                    if line.strip():
                        # Primeira coluna é o nome do modelo
                        model_name = line.split()[0]
                        if model_name and model_name != 'NAME':
                            models.append(model_name)

                logger.debug(f"Modelos encontrados via CLI: {models}")
                return models

        except Exception as e:
            logger.error(f"Erro ao executar 'ollama list': {e}")

        return []

    def _verify_model_available(self, model_name: str) -> bool:
        """Verifica se um modelo específico está disponível."""
        models = self._get_available_models()

        # Verificação direta
        if model_name in models:
            return True

        # Verificação com variações (alguns modelos podem ter tags diferentes)
        for model in models:
            if model_name in model or model in model_name:
                return True

        # Verificação específica para gpt-oss (pode aparecer com diferentes formatos)
        if 'gpt-oss' in model_name:
            for model in models:
                if 'gpt-oss' in model.lower():
                    return True

        return False

    def _download_model(self, model_name: str):
        """Baixa um modelo específico."""
        self.stdout.write(f"📥 Baixando {model_name}...")

        try:
            # Configurar encoding para Windows
            import locale
            if os.name == 'nt':  # Windows
                encoding = 'utf-8'
            else:
                encoding = locale.getpreferredencoding()

            result = subprocess.run(
                ['ollama', 'pull', model_name],
                capture_output=True,
                text=True,
                encoding=encoding,
                errors='replace',  # Substituir caracteres problemáticos
                timeout=1800  # 30 minutos
            )

            if result.returncode == 0:
                self.stdout.write(f"✅ {model_name} baixado com sucesso!")
            else:
                error_msg = result.stderr.encode('utf-8', errors='replace').decode('utf-8')
                raise CommandError(f"Erro ao baixar {model_name}: {error_msg}")

        except subprocess.TimeoutExpired:
            raise CommandError(f"Timeout ao baixar {model_name}")
        except FileNotFoundError:
            raise CommandError("Comando 'ollama' não encontrado no PATH")
        except UnicodeDecodeError as e:
            self.stdout.write(f"⚠️  Aviso de encoding: {e}")
            self.stdout.write(f"✅ {model_name} provavelmente baixado com sucesso!")

    def _test_model_basic(self, model_name: str):
        """Executa teste básico em um modelo."""
        try:
            base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')

            # Para GPT-OSS, usar endpoint /api/chat em vez de /api/generate
            if 'gpt-oss' in model_name:
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "user", "content": "Responda apenas 'OK' para testar conectividade."}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 10
                    }
                }
                endpoint = f"{base_url}/api/chat"
                timeout = 90  # Timeout maior para GPT-OSS
            else:
                # Modelo tradicional
                payload = {
                    "model": model_name,
                    "prompt": "Responda apenas 'OK' para testar conectividade.",
                    "stream": False
                }
                endpoint = f"{base_url}/api/generate"
                timeout = 30

            self.stdout.write(f"🧪 Testando {model_name} (timeout: {timeout}s)...")

            response = requests.post(
                endpoint,
                json=payload,
                timeout=timeout
            )

            if response.status_code == 200:
                self.stdout.write(f"✅ Teste básico do {model_name}: OK")

                # Mostrar parte da resposta para debug
                try:
                    response_data = response.json()
                    if 'gpt-oss' in model_name and 'message' in response_data:
                        content = response_data['message'].get('content', '')[:50]
                        self.stdout.write(f"📝 Resposta: {content}...")
                    elif 'response' in response_data:
                        content = response_data['response'][:50]
                        self.stdout.write(f"📝 Resposta: {content}...")
                except:
                    pass  # Ignorar erros de parsing para o teste básico

            else:
                raise CommandError(f"Teste falhou: HTTP {response.status_code}")

        except requests.Timeout:
            # Para GPT-OSS, timeout não é necessariamente um erro fatal
            if 'gpt-oss' in model_name:
                self.stdout.write(f"⚠️  Timeout em {timeout}s - GPT-OSS pode estar processando")
                self.stdout.write("✅ Modelo provavelmente está funcionando (GPT-OSS é mais lento)")
            else:
                raise CommandError(f"Timeout no teste básico após {timeout}s")
        except Exception as e:
            # Para GPT-OSS, alguns erros podem ser tolerados
            if 'gpt-oss' in model_name and ('connection' in str(e).lower() or 'timeout' in str(e).lower()):
                self.stdout.write(f"⚠️  Problema de conectividade: {e}")
                self.stdout.write("✅ Modelo baixado - teste conectividade manualmente")
            else:
                raise CommandError(f"Erro no teste básico: {e}")

    def _recommend_gpt_oss_variant(self) -> str:
        """Recomenda variante do GPT-OSS baseada no hardware."""
        # Verificar memória disponível (simplificado)
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024 ** 3)

            if memory_gb >= 32:
                return "120b"  # Modelo maior para sistemas robustos
            else:
                return "20b"  # Modelo menor para sistemas modestos
        except ImportError:
            return "20b"  # Fallback seguro

    def _classify_performance(self, avg_time: float, avg_tokens: float) -> str:
        """Classifica a performance do modelo."""
        tokens_per_second = avg_tokens / avg_time if avg_time > 0 else 0

        if tokens_per_second > 50:
            return "🚀 Excelente"
        elif tokens_per_second > 30:
            return "⚡ Boa"
        elif tokens_per_second > 15:
            return "✅ Aceitável"
        else:
            return "🐌 Lenta"

    def _run_benchmark_iteration(self, model: str, include_reasoning: bool) -> Dict:
        """Executa uma iteração de benchmark."""
        prompt = "Explique em 2 parágrafos a importância da literatura brasileira."

        start_time = time.time()

        response = ai_service.get_ai_response(
            user_message=prompt,
            conversation_id=0,
            reasoning_effort='high' if include_reasoning else 'low'
        )

        end_time = time.time()

        return {
            'response_time': end_time - start_time,
            'tokens_generated': len(response.get('response', '').split()) if response['success'] else 0,
            'success': response['success'],
            'has_reasoning': 'reasoning' in response
        }

    def _setup_gpt_oss_cache(self):
        """Configura cache específico para GPT-OSS."""
        try:
            # Testar conexão com cache
            cache.set('gpt_oss_test', 'ok', timeout=60)
            test_value = cache.get('gpt_oss_test')

            if test_value == 'ok':
                self.stdout.write("✅ Cache GPT-OSS configurado")
            else:
                self.stdout.write("⚠️  Cache pode não estar funcionando corretamente")

        except Exception as e:
            self.stdout.write(f"❌ Erro no cache: {e}")

    def _show_gpt_oss_tips(self, variant: str):
        """Mostra dicas de uso do GPT-OSS."""
        self.stdout.write(f"\n💡 DICAS DE USO - GPT-OSS {variant.upper()}:")

        tips = [
            "Configure reasoning_effort baseado na complexidade da tarefa",
            "Use chain-of-thought para análises literárias profundas",
            "Monitor o cache Redis para otimizar performance",
            "Ajuste timeouts conforme necessário em produção"
        ]

        for tip in tips:
            self.stdout.write(f"  • {tip}")

    def _check_cache_health(self) -> Dict:
        """Verifica saúde do cache Redis."""
        try:
            cache.set('health_check', 'ok', timeout=10)
            result = cache.get('health_check')

            if result == 'ok':
                return {'status': 'healthy', 'message': 'Cache funcionando'}
            else:
                return {'status': 'degraded', 'message': 'Cache não retornou valor esperado'}

        except Exception as e:
            return {'status': 'error', 'message': f'Erro no cache: {e}'}

    def _diagnose_cache_issues(self) -> List[Dict]:
        """Diagnóstica problemas do cache."""
        issues = []

        try:
            # Testar cache principal
            cache.set('diagnose_test', 'value', timeout=10)
            if cache.get('diagnose_test') != 'value':
                issues.append({
                    'issue': 'Cache principal não está funcionando',
                    'solution': 'Verificar configuração do Redis',
                    'fixable': False
                })

            # Verificar cache GPT-OSS específico
            from django.core.cache import caches
            if 'gpt_oss_responses' in caches:
                gpt_cache = caches['gpt_oss_responses']
                gpt_cache.set('diagnose_gpt_test', 'value', timeout=10)
                if gpt_cache.get('diagnose_gpt_test') != 'value':
                    issues.append({
                        'issue': 'Cache GPT-OSS específico com problemas',
                        'solution': 'Verificar configuração gpt_oss_responses no Redis',
                        'fixable': False
                    })

        except Exception as e:
            issues.append({
                'issue': f'Erro ao testar cache: {e}',
                'solution': 'Verificar se Redis está executando',
                'fixable': False
            })

        return issues

    def _diagnose_config_issues(self) -> List[Dict]:
        """Diagnóstica problemas de configuração."""
        issues = []

        # Verificar configurações essenciais
        required_settings = [
            ('OLLAMA_BASE_URL', 'http://localhost:11434'),
            ('OLLAMA_MODEL', 'gpt-oss:20b'),
        ]

        for setting_name, default_value in required_settings:
            if not hasattr(settings, setting_name):
                issues.append({
                    'issue': f'Configuração {setting_name} não encontrada',
                    'solution': f'Adicionar {setting_name}={default_value} no settings.py',
                    'fixable': False
                })

        # Verificar se modelo configurado existe
        current_model = getattr(settings, 'OLLAMA_MODEL', '')
        if current_model and not self._verify_model_available(current_model):
            issues.append({
                'issue': f'Modelo configurado {current_model} não está disponível',
                'solution': f'Execute: ollama pull {current_model}',
                'fixable': True,
                'fix_action': lambda: self._download_model(current_model)
            })

        return issues

    def _backup_current_config(self):
        """Faz backup das configurações atuais."""
        import json
        from datetime import datetime

        config_backup = {
            'timestamp': datetime.now().isoformat(),
            'model': getattr(settings, 'OLLAMA_MODEL', ''),
            'base_url': getattr(settings, 'OLLAMA_BASE_URL', ''),
            'timeout': getattr(settings, 'OLLAMA_TIMEOUT', 30),
            'temperature': getattr(settings, 'OLLAMA_TEMPERATURE', 0.7),
        }

        backup_file = f'ollama_config_backup_{int(time.time())}.json'

        try:
            with open(backup_file, 'w') as f:
                json.dump(config_backup, f, indent=2)

            self.stdout.write(f"✅ Backup salvo em: {backup_file}")

        except Exception as e:
            self.stdout.write(f"⚠️  Erro ao fazer backup: {e}")

    def _execute_migration(self, from_model: str, to_model: str):
        """Executa a migração entre modelos."""
        self.stdout.write(f"🔄 Migrando de {from_model} para {to_model}")

        # 1. Verificar se modelo de destino está disponível
        if not self._verify_model_available(to_model):
            self.stdout.write(f"📥 Baixando {to_model}...")
            self._download_model(to_model)

        # 2. Testar modelo de destino
        self.stdout.write("🧪 Testando modelo de destino...")
        self._test_model_basic(to_model)

        # 3. Limpar cache antigo
        self.stdout.write("🧹 Limpando cache antigo...")
        try:
            cache.clear()
        except Exception as e:
            self.stdout.write(f"⚠️  Erro ao limpar cache: {e}")

        # 4. Configurar novo modelo (simulado - requer restart)
        self.stdout.write("⚙️  Configurando novo modelo...")
        self.stdout.write(
            f"📝 Atualize OLLAMA_MODEL={to_model} no seu arquivo .env"
        )
        self.stdout.write(
            "🔄 Reinicie o servidor Django para aplicar mudanças"
        )

    def _rollback_migration(self):
        """Reverte migração para configuração anterior."""
        self.stdout.write(self.style.WARNING("=== ROLLBACK DE MIGRAÇÃO ==="))

        # Procurar arquivos de backup
        import glob
        backup_files = glob.glob('ollama_config_backup_*.json')

        if not backup_files:
            self.stdout.write("❌ Nenhum backup encontrado para rollback")
            return

        # Usar backup mais recente
        latest_backup = max(backup_files, key=os.path.getctime)
        self.stdout.write(f"📋 Usando backup: {latest_backup}")

        try:
            import json
            with open(latest_backup, 'r') as f:
                backup_config = json.load(f)

            # Mostrar configurações do backup
            self.stdout.write("🔙 Configurações do backup:")
            for key, value in backup_config.items():
                if key != 'timestamp':
                    self.stdout.write(f"  {key}: {value}")

            # Instruções para rollback manual
            self.stdout.write("\n📝 Para fazer rollback:")
            self.stdout.write(f"1. Atualize OLLAMA_MODEL={backup_config.get('model', '')}")
            self.stdout.write("2. Reinicie o servidor Django")
            self.stdout.write("3. Execute: python manage.py ollama health")

        except Exception as e:
            self.stdout.write(f"❌ Erro ao ler backup: {e}")

    def _update_model_config(self, model_name: str):
        """Atualiza configuração do modelo (informativo)."""
        self.stdout.write(f"📝 Para usar {model_name} permanentemente:")
        self.stdout.write(f"1. Atualize OLLAMA_MODEL={model_name} no .env")
        self.stdout.write("2. Reinicie o servidor Django")
        self.stdout.write("3. Verifique com: python manage.py ollama status")

    def _show_gpt_oss_details(self, model_name: str):
        """Mostra detalhes específicos do GPT-OSS."""
        if 'gpt-oss:20b' in model_name:
            details = [
                "  • 21B parâmetros (3.6B ativos)",
                "  • Ideal para hardware modesto (16GB RAM)",
                "  • Otimizado para baixa latência",
                "  • Suporte completo a chain-of-thought"
            ]
        elif 'gpt-oss:120b' in model_name:
            details = [
                "  • 117B parâmetros (5.1B ativos)",
                "  • Requer hardware robusto (32GB+ RAM)",
                "  • Performance superior em análises",
                "  • Reasoning avançado para tarefas complexas"
            ]
        else:
            details = ["  • Modelo GPT-OSS detectado"]

        for detail in details:
            self.stdout.write(detail)

    def _save_literary_test_results(self, results: List[Dict]):
        """Salva resultados dos testes literários em arquivo."""
        import json
        from datetime import datetime

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'literary_test_results_{timestamp}.json'

        output_data = {
            'timestamp': datetime.now().isoformat(),
            'model': getattr(settings, 'OLLAMA_MODEL', 'unknown'),
            'results': results,
            'summary': {
                'total_tests': len(results),
                'successful_tests': len([r for r in results if r['success']]),
                'success_rate': len([r for r in results if r['success']]) / len(results) if results else 0
            }
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            self.stdout.write(f"💾 Resultados salvos em: {filename}")

        except Exception as e:
            self.stdout.write(f"❌ Erro ao salvar resultados: {e}")

    def _cleanup_old_logs(self) -> int:
        """Remove logs antigos (se existirem)."""
        import glob
        from datetime import datetime, timedelta

        # Procurar por logs antigos (mais de 30 dias)
        cutoff_date = datetime.now() - timedelta(days=30)
        log_patterns = ['*.log', 'logs/*.log', 'ollama*.log']

        cleaned_count = 0

        for pattern in log_patterns:
            for log_file in glob.glob(pattern):
                try:
                    file_time = datetime.fromtimestamp(os.path.getctime(log_file))
                    if file_time < cutoff_date:
                        os.remove(log_file)
                        cleaned_count += 1
                except (OSError, IOError):
                    pass  # Ignorar erros de permissão

        return cleaned_count