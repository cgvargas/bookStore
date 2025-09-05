# Arquivo: cgbookstore/apps/core/admin/diagnostics_admin.py

import threading
from io import StringIO
import sys
import time
from datetime import datetime

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.core.management import call_command
from django.core.cache import caches, cache
from django.contrib.admin.views.decorators import staff_member_required

from ..models import Author, Book


@staff_member_required
def diagnostics_dashboard(request):
    running_tasks = request.session.get('running_tasks', {})
    context = {
        'title': 'Ferramentas de Diagnóstico',
        'tools': [
            {
                'name': 'Diagnóstico de Performance',
                'url_name': 'admin:performance_diagnostics',
                'description': 'Analisa e reporta métricas de performance da aplicação.',
                'category': 'performance',
                'icon': '⚡'
            },
            {
                'name': 'Informações do Redis',
                'url_name': 'admin:redis_info',
                'description': 'Exibe estatísticas e informações detalhadas do servidor Redis.',
                'category': 'cache',
                'icon': '💾'
            },
            {
                'name': 'Limpar Cache',
                'url_name': 'admin:clear_cache',
                'description': 'Abre o formulário para limpar caches específicos ou todos.',
                'category': 'cache',
                'icon': '🧹'
            },
            {
                'name': 'Corrigir Capas Corrompidas',
                'url_name': 'admin:fix_corrupted_covers',
                'description': 'Verifica e tenta reparar arquivos de imagem de capas de livros.',
                'category': 'maintenance',
                'icon': '🖼️'
            },
            {
                'name': 'Debug de Imagens',
                'url_name': 'admin:debug_book_images',
                'description': 'Executa um diagnóstico em todas as imagens de livros para encontrar problemas.',
                'category': 'debug',
                'icon': '🔍'
            },
            {
                'name': 'Debug de Recomendações',
                'url_name': 'admin:debug_recommendations',
                'description': 'Verifica a integridade e a lógica do sistema de recomendações.',
                'category': 'debug',
                'icon': '🎯'
            },
            {
                'name': 'Health Check do Sistema',
                'url_name': 'admin:system_health_check',
                'description': 'Realiza uma verificação completa da saúde dos componentes do sistema.',
                'category': 'monitoring',
                'icon': '💚'
            },
        ],
        'running_tasks': running_tasks
    }
    return render(request, 'admin/diagnostics/dashboard.html', context)


@staff_member_required
def performance_diagnostics(request):
    # Se a requisição for POST, executa o diagnóstico
    if request.method == 'POST':
        test_type = request.POST.get('test_type', 'quick')
        output_format = request.POST.get('output_format', 'console')
        save_report = request.POST.get('save_report')

        results = []
        start_time = time.time()

        results.append(f"Iniciando Diagnóstico de Performance ({test_type.capitalize()})")
        results.append("=" * 40)

        # 1. Teste de Conexão com o Banco de Dados
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                results.append("[OK] Conexão com o banco de dados bem-sucedida.")
        except Exception as e:
            results.append(f"[ERRO] Falha ao conectar ao banco de dados: {e}")
            output = "\n".join(results)
            context = {'title': 'Resultado do Diagnóstico de Performance', 'output': output, 'success': False}
            return render(request, 'admin/diagnostics/command_output.html', context)

        # 2. Teste de Query Simples
        t0 = time.time()
        book_count = Book.objects.count()
        t1 = time.time()
        results.append(f"[INFO] Contagem de livros ({book_count} registros) levou: {t1 - t0:.4f} segundos.")

        # 3. Teste de Query Complexa (apenas em Análise Profunda)
        if test_type == 'deep':
            t0 = time.time()
            authors_with_books = Author.objects.prefetch_related('books').all()[:20]
            for author in authors_with_books:
                _ = len(author.books.all())  # Usar 'books' como definido no related_name
            t1 = time.time()
            results.append(f"[INFO] Query complexa (autor com livros) levou: {t1 - t0:.4f} segundos.")

        # 4. Teste de Performance do Cache
        try:
            cache_key = 'performance_test_key'
            cache_value = 'ok'

            t0 = time.time()
            cache.set(cache_key, cache_value, timeout=5)
            t1 = time.time()

            t2 = time.time()
            value_from_cache = cache.get(cache_key)
            t3 = time.time()

            if value_from_cache == cache_value:
                results.append(f"[OK] Cache funcional. Escrita: {t1 - t0:.6f}s | Leitura: {t3 - t2:.6f}s.")
            else:
                results.append("[AVISO] O valor lido do cache é diferente do escrito.")
            cache.delete(cache_key)
        except Exception as e:
            results.append(f"[ERRO] Falha ao testar o cache: {e}")

        total_time = time.time() - start_time
        results.append("=" * 40)
        results.append(f"Diagnóstico concluído em {total_time:.2f} segundos.")

        output = "\n".join(results)
        context = {
            'title': 'Resultado do Diagnóstico de Performance',
            'output': output,
            'success': True
        }
        return render(request, 'admin/diagnostics/command_output.html', context)

    # Se a requisição for GET, apenas exibe o formulário
    context = {
        'title': 'Diagnóstico de Performance',
        'form_action': reverse('admin:performance_diagnostics')
    }
    return render(request, 'admin/diagnostics/performance_form.html', context)


@staff_member_required
def redis_info(request):
    try:
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        try:
            call_command('redis_info')
            output = mystdout.getvalue()
        finally:
            sys.stdout = old_stdout
        context = {'title': 'Informações do Redis', 'output': output, 'success': True}
    except Exception as e:
        context = {'title': 'Informações do Redis', 'error': str(e), 'success': False}
    return render(request, 'admin/diagnostics/command_output.html', context)


@staff_member_required
def fix_corrupted_covers(request):
    if request.method == 'POST':
        try:
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            try:
                call_command('fix_corrupted_covers')
                output = mystdout.getvalue()
                messages.success(request, 'Correção de capas executada com sucesso!')
            finally:
                sys.stdout = old_stdout
            context = {'title': 'Resultado da Correção de Capas', 'output': output, 'success': True}
        except Exception as e:
            messages.error(request, f'Erro ao executar correção: {e}')
            context = {'title': 'Erro na Correção de Capas', 'error': str(e), 'success': False}
        return render(request, 'admin/diagnostics/command_output.html', context)

    context = {
        'title': 'Confirmar Correção de Capas',
        'action_url': reverse('admin:fix_corrupted_covers'),
        'description': 'Esta ferramenta irá verificar e tentar corrigir capas de livros corrompidas.',
        'warning': 'Esta operação pode ser demorada.'
    }
    return render(request, 'admin/diagnostics/confirm_action.html', context)


@staff_member_required
def debug_book_images(request):
    try:
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        try:
            call_command('debug_book_images')
            output = mystdout.getvalue()
        finally:
            sys.stdout = old_stdout
        context = {'title': 'Debug de Imagens de Livros', 'output': output, 'success': True}
    except Exception as e:
        context = {'title': 'Debug de Imagens de Livros', 'error': str(e), 'success': False}
    return render(request, 'admin/diagnostics/command_output.html', context)


@staff_member_required
def debug_recommendations(request):
    try:
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        try:
            call_command('debug_recommendations')
            output = mystdout.getvalue()
        finally:
            sys.stdout = old_stdout
        context = {'title': 'Debug de Recomendações', 'output': output, 'success': True}
    except Exception as e:
        context = {'title': 'Debug de Recomendações', 'error': str(e), 'success': False}
    return render(request, 'admin/diagnostics/command_output.html', context)


@staff_member_required
def system_health_check(request):
    try:
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        try:
            call_command('system_health_check')
            output = mystdout.getvalue()
        finally:
            sys.stdout = old_stdout
        context = {'title': 'Health Check do Sistema', 'output': output, 'success': True}
    except Exception as e:
        context = {'title': 'Health Check do Sistema', 'error': str(e), 'success': False}
    return render(request, 'admin/diagnostics/command_output.html', context)


@staff_member_required
def clear_cache(request):
    if request.method == 'POST':
        cache_type = request.POST.get('cache_type', 'all')
        try:
            if cache_type == 'all':
                for cache_name in caches:
                    caches[cache_name].clear()
                messages.success(request, 'Todos os caches foram limpos com sucesso!')
            else:
                caches[cache_type].clear()
                messages.success(request, f'Cache "{cache_type}" limpo com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao limpar cache: {e}')
        return redirect('admin:diagnostics_dashboard')

    context = {
        'title': 'Limpar Cache',
        'cache_options': [{'value': name, 'label': name} for name in caches]
    }
    return render(request, 'admin/diagnostics/clear_cache_form.html', context)


@staff_member_required
def task_status(request, task_id):
    task = request.session.get('running_tasks', {}).get(task_id)
    if not task:
        return JsonResponse({'error': 'Tarefa não encontrada'}, status=404)
    return JsonResponse(task, default=str)