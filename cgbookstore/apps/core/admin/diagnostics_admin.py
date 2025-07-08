# cgbookstore/apps/core/admin/diagnostics_admin.py
"""
Módulo administrativo para ferramentas de diagnóstico do sistema.
Integração com os comandos de performance e manutenção.
"""

import json
import threading
from datetime import datetime
from io import StringIO
import sys

from django.contrib import admin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import path, reverse
from django.core.management import call_command
from django.core.cache import caches
from django.utils.decorators import method_decorator

from .mixins import LoggingAdminMixin


class DiagnosticsAdmin:
    """
    Classe para gerenciar ferramentas de diagnóstico no admin
    """

    def __init__(self, admin_site):
        self.admin_site = admin_site
        self.running_tasks = {}  # Para tracking de tarefas em execução

    def get_urls(self):
        """URLs para as ferramentas de diagnóstico"""
        urls = [
            path('diagnostics/', self.diagnostics_dashboard, name='diagnostics_dashboard'),
            path('diagnostics/performance/', self.performance_diagnostics, name='performance_diagnostics'),
            path('diagnostics/redis-info/', self.redis_info, name='redis_info'),
            path('diagnostics/fix-covers/', self.fix_corrupted_covers, name='fix_corrupted_covers'),
            path('diagnostics/debug-books/', self.debug_book_images, name='debug_book_images'),
            path('diagnostics/debug-recommendations/', self.debug_recommendations, name='debug_recommendations'),
            path('diagnostics/system-health/', self.system_health_check, name='system_health_check'),
            path('diagnostics/clear-cache/', self.clear_cache, name='clear_cache'),
            path('diagnostics/task-status/<str:task_id>/', self.task_status, name='task_status'),
        ]
        return urls

    @method_decorator(staff_member_required, name='dispatch')
    def diagnostics_dashboard(self, request):
        """Dashboard principal de diagnósticos"""
        context = {
            'title': 'Ferramentas de Diagnóstico',
            'site_title': 'CG BookStore Admin',
            'site_header': 'Administração CG BookStore',
            'tools': [
                {
                    'name': 'Diagnóstico de Performance',
                    'description': 'Análise completa de performance do sistema',
                    'url': reverse('admin:performance_diagnostics'),
                    'icon': '🚀',
                    'category': 'performance'
                },
                {
                    'name': 'Informações do Redis',
                    'description': 'Status e estatísticas do cache Redis',
                    'url': reverse('admin:redis_info'),
                    'icon': '💾',
                    'category': 'cache'
                },
                {
                    'name': 'Corrigir Capas Corrompidas',
                    'description': 'Detecta e corrige imagens de capas corrompidas',
                    'url': reverse('admin:fix_corrupted_covers'),
                    'icon': '🖼️',
                    'category': 'maintenance'
                },
                {
                    'name': 'Debug de Imagens',
                    'description': 'Diagnóstico de problemas com imagens de livros',
                    'url': reverse('admin:debug_book_images'),
                    'icon': '🔍',
                    'category': 'debug'
                },
                {
                    'name': 'Debug de Recomendações',
                    'description': 'Análise do sistema de recomendações',
                    'url': reverse('admin:debug_recommendations'),
                    'icon': '🎯',
                    'category': 'debug'
                },
                {
                    'name': 'Health Check do Sistema',
                    'description': 'Verificação geral da saúde do sistema',
                    'url': reverse('admin:system_health_check'),
                    'icon': '💚',
                    'category': 'monitoring'
                },
                {
                    'name': 'Limpar Cache',
                    'description': 'Limpeza seletiva dos caches do sistema',
                    'url': reverse('admin:clear_cache'),
                    'icon': '🧹',
                    'category': 'cache'
                }
            ],
            'running_tasks': self.running_tasks
        }

        return render(request, 'admin/diagnostics/dashboard.html', context)

    def performance_diagnostics(self, request):
        """Executa diagnóstico de performance"""
        if request.method == 'POST':
            # Parâmetros do formulário
            test_type = request.POST.get('test_type', 'quick')
            output_format = request.POST.get('output_format', 'console')
            save_report = request.POST.get('save_report', False)

            try:
                # Executar comando em thread separada para não bloquear
                task_id = f"perf_diag_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                def run_diagnostics():
                    try:
                        args = []
                        if test_type == 'quick':
                            args.append('--quick')
                        elif test_type == 'deep':
                            args.append('--deep')

                        if output_format != 'console':
                            args.extend(['--output', output_format])

                        if save_report:
                            filename = f'performance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                            args.extend(['--save-report', filename])

                        # Capturar output
                        old_stdout = sys.stdout
                        sys.stdout = mystdout = StringIO()

                        try:
                            call_command('performance_diagnostics', *args)
                            output = mystdout.getvalue()
                        finally:
                            sys.stdout = old_stdout

                        self.running_tasks[task_id] = {
                            'status': 'completed',
                            'output': output,
                            'completed_at': datetime.now()
                        }

                    except Exception as e:
                        self.running_tasks[task_id] = {
                            'status': 'error',
                            'error': str(e),
                            'completed_at': datetime.now()
                        }

                # Iniciar tarefa
                self.running_tasks[task_id] = {
                    'status': 'running',
                    'started_at': datetime.now()
                }

                thread = threading.Thread(target=run_diagnostics)
                thread.daemon = True
                thread.start()

                messages.success(request, f'Diagnóstico iniciado! ID da tarefa: {task_id}')
                return redirect('admin:diagnostics_dashboard')

            except Exception as e:
                messages.error(request, f'Erro ao iniciar diagnóstico: {e}')

        context = {
            'title': 'Diagnóstico de Performance',
            'site_title': 'CG BookStore Admin',
            'site_header': 'Administração CG BookStore',
            'form_action': reverse('admin:performance_diagnostics')
        }

        return render(request, 'admin/diagnostics/performance_form.html', context)

    def redis_info(self, request):
        """Exibe informações do Redis"""
        try:
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()

            try:
                call_command('redis_info')
                output = mystdout.getvalue()
            finally:
                sys.stdout = old_stdout

            context = {
                'title': 'Informações do Redis',
                'site_title': 'CG BookStore Admin',
                'site_header': 'Administração CG BookStore',
                'output': output,
                'success': True
            }

        except Exception as e:
            context = {
                'title': 'Informações do Redis',
                'site_title': 'CG BookStore Admin',
                'site_header': 'Administração CG BookStore',
                'error': str(e),
                'success': False
            }

        return render(request, 'admin/diagnostics/command_output.html', context)

    def fix_corrupted_covers(self, request):
        """Executa correção de capas corrompidas"""
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

                context = {
                    'title': 'Correção de Capas Corrompidas',
                    'site_title': 'CG BookStore Admin',
                    'site_header': 'Administração CG BookStore',
                    'output': output,
                    'success': True
                }

            except Exception as e:
                messages.error(request, f'Erro ao executar correção: {e}')
                context = {
                    'title': 'Correção de Capas Corrompidas',
                    'site_title': 'CG BookStore Admin',
                    'site_header': 'Administração CG BookStore',
                    'error': str(e),
                    'success': False
                }

            return render(request, 'admin/diagnostics/command_output.html', context)

        # GET - Exibe formulário de confirmação
        context = {
            'title': 'Correção de Capas Corrompidas',
            'site_title': 'CG BookStore Admin',
            'site_header': 'Administração CG BookStore',
            'action_url': reverse('admin:fix_corrupted_covers'),
            'description': 'Esta ferramenta irá verificar e corrigir capas de livros corrompidas.',
            'warning': 'Esta operação pode demorar alguns minutos dependendo do número de livros.'
        }

        return render(request, 'admin/diagnostics/confirm_action.html', context)

    def debug_book_images(self, request):
        """Debug de imagens de livros"""
        try:
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()

            try:
                call_command('debug_book_images')
                output = mystdout.getvalue()
            finally:
                sys.stdout = old_stdout

            context = {
                'title': 'Debug de Imagens de Livros',
                'site_title': 'CG BookStore Admin',
                'site_header': 'Administração CG BookStore',
                'output': output,
                'success': True
            }

        except Exception as e:
            context = {
                'title': 'Debug de Imagens de Livros',
                'site_title': 'CG BookStore Admin',
                'site_header': 'Administração CG BookStore',
                'error': str(e),
                'success': False
            }

        return render(request, 'admin/diagnostics/command_output.html', context)

    def debug_recommendations(self, request):
        """Debug do sistema de recomendações"""
        try:
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()

            try:
                call_command('debug_recommendations')
                output = mystdout.getvalue()
            finally:
                sys.stdout = old_stdout

            context = {
                'title': 'Debug de Recomendações',
                'site_title': 'CG BookStore Admin',
                'site_header': 'Administração CG BookStore',
                'output': output,
                'success': True
            }

        except Exception as e:
            context = {
                'title': 'Debug de Recomendações',
                'site_title': 'CG BookStore Admin',
                'site_header': 'Administração CG BookStore',
                'error': str(e),
                'success': False
            }

        return render(request, 'admin/diagnostics/command_output.html', context)

    def system_health_check(self, request):
        """Health check geral do sistema"""
        try:
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()

            try:
                call_command('system_health_check')
                output = mystdout.getvalue()
            finally:
                sys.stdout = old_stdout

            context = {
                'title': 'Health Check do Sistema',
                'site_title': 'CG BookStore Admin',
                'site_header': 'Administração CG BookStore',
                'output': output,
                'success': True
            }

        except Exception as e:
            context = {
                'title': 'Health Check do Sistema',
                'site_title': 'CG BookStore Admin',
                'site_header': 'Administração CG BookStore',
                'error': str(e),
                'success': False
            }

        return render(request, 'admin/diagnostics/command_output.html', context)

    def clear_cache(self, request):
        """Limpa caches do sistema"""
        if request.method == 'POST':
            cache_type = request.POST.get('cache_type', 'all')

            try:
                if cache_type == 'all':
                    # Limpa todos os caches EXCETO o cache de sessão
                    for cache_name in ['recommendations', 'google_books', 'image_proxy']:
                        try:
                            cache = caches[cache_name]
                            cache.clear()
                        except Exception:
                            pass

                    # Limpa o cache padrão de forma seletiva para preservar sessões
                    try:
                        from django.core.cache import cache as default_cache
                        # Lista de chaves conhecidas para limpar (evita limpar sessões)
                        known_cache_keys = [
                            'book_category_config',
                            'homepage_shelves',
                            'recommended_books',
                            'user_activity_stats',
                            'book_statistics'
                        ]
                        for key in known_cache_keys:
                            default_cache.delete(key)
                    except Exception:
                        pass

                    messages.success(request, 'Todos os caches foram limpos com sucesso!')
                else:
                    # Limpa cache específico (apenas se não for o padrão)
                    if cache_type != 'default':
                        cache = caches[cache_type]
                        cache.clear()
                        messages.success(request, f'Cache "{cache_type}" limpo com sucesso!')
                    else:
                        messages.warning(request,
                                         'Cache padrão não pode ser limpo completamente para preservar sessões.')

            except Exception as e:
                messages.error(request, f'Erro ao limpar cache: {e}')

            # CORREÇÃO: Usar HttpResponseRedirect com URL absoluta para evitar problemas de sessão
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            return HttpResponseRedirect(reverse('admin:diagnostics_dashboard'))

        # GET - Exibe formulário
        context = {
            'title': 'Limpar Cache',
            'site_title': 'CG BookStore Admin',
            'site_header': 'Administração CG BookStore',
            'cache_options': [
                {'value': 'all', 'label': 'Todos os Caches (Exceto Sessões)'},
                {'value': 'recommendations', 'label': 'Cache de Recomendações'},
                {'value': 'google_books', 'label': 'Cache Google Books'},
                {'value': 'image_proxy', 'label': 'Cache de Imagens'},
            ]
        }

        return render(request, 'admin/diagnostics/clear_cache_form.html', context)

    def task_status(self, request, task_id):
        """Retorna status de uma tarefa em execução"""
        task = self.running_tasks.get(task_id)

        if not task:
            return JsonResponse({'error': 'Tarefa não encontrada'}, status=404)

        return JsonResponse(task, default=str)


# Instância global para uso nas URLs
diagnostics_admin = DiagnosticsAdmin(None)