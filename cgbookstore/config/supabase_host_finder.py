#!/usr/bin/env python3
"""
Script para Encontrar e Configurar Host Correto do Supabase
Arquivo: cgbookstore/config/supabase_host_finder.py

Este script ajuda a encontrar o host correto do seu projeto Supabase e
configura automaticamente as credenciais.
"""

import os
import sys
import json
import socket
import psycopg2
import re
from datetime import datetime
from urllib.parse import urlparse
import subprocess


class SupabaseHostFinder:
    def __init__(self):
        self.project_ref = None
        self.region = None
        self.working_hosts = []
        self.test_results = {}

    def print_header(self, title):
        """Imprime cabeçalho formatado"""
        print(f"\n{'=' * 70}")
        print(f"🔍 {title}")
        print(f"{'=' * 70}")

    def print_step(self, step, description):
        """Imprime etapa atual"""
        print(f"\n🔧 ETAPA {step}: {description}")
        print("-" * 50)

    def extract_project_ref_from_old_host(self):
        """Extrai referência do projeto do host antigo"""
        old_host = "db.amytpwmgpkizuwkwvpzm.supabase.co"
        if "." in old_host:
            potential_ref = old_host.split(".")[1]  # amytpwmgpkizuwkwvpzm
            self.project_ref = potential_ref
            print(f"📋 Referência extraída do host antigo: {self.project_ref}")
            return True
        return False

    def generate_possible_hosts(self):
        """Gera lista de possíveis hosts baseado na referência do projeto"""
        possible_hosts = []

        if self.project_ref:
            # Formatos comuns do Supabase
            host_patterns = [
                f"db.{self.project_ref}.supabase.co",  # Formato antigo
                f"{self.project_ref}.supabase.co",  # Formato direto
                f"aws-0-us-east-1.pooler.supabase.com",  # Pooler genérico
                f"aws-0-us-west-1.pooler.supabase.com",  # Pooler west
                f"aws-0-eu-west-1.pooler.supabase.com",  # Pooler europa
                f"db.{self.project_ref}.pooler.supabase.com",  # Pooler específico
                f"{self.project_ref}.db.supabase.co",  # Variação
                f"postgresql.{self.project_ref}.supabase.co",  # Com protocolo
            ]

            # Adiciona variações regionais
            regions = ['us-east-1', 'us-west-1', 'eu-west-1', 'ap-southeast-1']
            for region in regions:
                host_patterns.extend([
                    f"aws-0-{region}.pooler.supabase.com",
                    f"db.{self.project_ref}.{region}.supabase.co",
                ])

            possible_hosts = host_patterns

        # Adiciona hosts genéricos conhecidos
        generic_hosts = [
            "aws-0-us-east-1.pooler.supabase.com",
            "aws-0-us-west-1.pooler.supabase.com",
            "aws-0-eu-west-1.pooler.supabase.com",
        ]

        possible_hosts.extend(generic_hosts)

        # Remove duplicatas mantendo ordem
        seen = set()
        unique_hosts = []
        for host in possible_hosts:
            if host not in seen:
                seen.add(host)
                unique_hosts.append(host)

        return unique_hosts

    def test_host_connectivity(self, host, port=5432, timeout=5):
        """Testa conectividade com um host específico"""
        try:
            # Teste DNS
            ip = socket.gethostbyname(host)

            # Teste de porta
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return {
                    'status': 'SUCCESS',
                    'ip': ip,
                    'message': f'Host acessível na porta {port}'
                }
            else:
                return {
                    'status': 'PORT_CLOSED',
                    'ip': ip,
                    'message': f'Host resolve DNS mas porta {port} inacessível'
                }

        except socket.gaierror:
            return {
                'status': 'DNS_FAIL',
                'ip': None,
                'message': 'Host não resolve DNS'
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'ip': None,
                'message': f'Erro: {str(e)}'
            }

    def scan_for_working_hosts(self):
        """Escaneia lista de hosts possíveis"""
        self.print_step(1, "Escaneando Hosts Possíveis")

        # Extrai referência do projeto
        self.extract_project_ref_from_old_host()

        # Gera lista de hosts possíveis
        possible_hosts = self.generate_possible_hosts()

        print(f"🔍 Testando {len(possible_hosts)} hosts possíveis...")

        working_hosts = []

        for i, host in enumerate(possible_hosts, 1):
            print(f"[{i:2d}/{len(possible_hosts)}] Testando: {host:<50}", end=" ")

            result = self.test_host_connectivity(host)
            self.test_results[host] = result

            if result['status'] == 'SUCCESS':
                print(f"✅ {result['message']} (IP: {result['ip']})")
                working_hosts.append({
                    'host': host,
                    'ip': result['ip'],
                    'type': self.categorize_host(host)
                })
            elif result['status'] == 'PORT_CLOSED':
                print(f"⚠️  {result['message']} (IP: {result['ip']})")
            else:
                print(f"❌ {result['message']}")

        self.working_hosts = working_hosts
        return working_hosts

    def categorize_host(self, host):
        """Categoriza tipo do host"""
        if 'pooler' in host:
            return 'connection_pooler'
        elif self.project_ref and self.project_ref in host:
            return 'direct_project'
        else:
            return 'generic'

    def test_database_connection(self, host, user='postgres', password='', database='postgres', port=5432):
        """Testa conexão real com banco de dados"""
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                connect_timeout=10
            )

            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            return {
                'status': 'SUCCESS',
                'message': f'Conexão realizada com sucesso',
                'version': version
            }

        except psycopg2.OperationalError as e:
            error_msg = str(e)
            if 'authentication failed' in error_msg:
                return {
                    'status': 'AUTH_FAILED',
                    'message': 'Host funciona mas credenciais inválidas',
                    'error': error_msg
                }
            else:
                return {
                    'status': 'CONNECTION_FAILED',
                    'message': 'Falha na conexão',
                    'error': error_msg
                }
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Erro inesperado: {str(e)}'
            }

    def prompt_for_credentials(self):
        """Solicita credenciais do usuário"""
        self.print_step(2, "Configuração de Credenciais")

        print("Para testar a conexão com banco, precisamos das credenciais do Supabase.")
        print("Você pode encontrá-las em: https://supabase.com/dashboard/project/[SEU_PROJETO]/settings/database")
        print()

        credentials = {}

        # User (padrão postgres)
        user = input("👤 Database User [postgres]: ").strip()
        credentials['user'] = user if user else 'postgres'

        # Password
        password = input("🔑 Database Password: ").strip()
        credentials['password'] = password

        # Database (padrão postgres)
        database = input("🗄️  Database Name [postgres]: ").strip()
        credentials['database'] = database if database else 'postgres'

        # Port (padrão 5432)
        port = input("🔌 Port [5432]: ").strip()
        credentials['port'] = int(port) if port.isdigit() else 5432

        return credentials

    def test_working_hosts_with_credentials(self, credentials):
        """Testa hosts funcionais com credenciais"""
        self.print_step(3, "Testando Conexões com Credenciais")

        if not self.working_hosts:
            print("❌ Nenhum host funcional encontrado para testar.")
            return []

        successful_connections = []

        for host_info in self.working_hosts:
            host = host_info['host']
            print(f"\n🔗 Testando conexão com: {host}")

            result = self.test_database_connection(
                host=host,
                user=credentials['user'],
                password=credentials['password'],
                database=credentials['database'],
                port=credentials['port']
            )

            if result['status'] == 'SUCCESS':
                print(f"✅ Sucesso! {result['message']}")
                print(f"   PostgreSQL: {result['version'][:60]}...")
                successful_connections.append({
                    **host_info,
                    'credentials_valid': True,
                    'db_version': result['version']
                })
            elif result['status'] == 'AUTH_FAILED':
                print(f"🔐 {result['message']}")
                successful_connections.append({
                    **host_info,
                    'credentials_valid': False,
                    'auth_error': result['error']
                })
            else:
                print(f"❌ {result['message']}")
                if 'error' in result:
                    print(f"   Erro: {result['error']}")

        return successful_connections

    def generate_env_file(self, host_info, credentials):
        """Gera arquivo .env com configurações"""
        self.print_step(4, "Gerando Arquivo de Configuração")

        host = host_info['host']

        # Gera DATABASE_URL
        database_url = (f"postgresql://{credentials['user']}:{credentials['password']}"
                        f"@{host}:{credentials['port']}/{credentials['database']}")

        # Conteúdo do arquivo .env
        env_content = f"""# Configurações do Supabase - Gerado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Host funcional encontrado: {host} (IP: {host_info['ip']})
# Tipo: {host_info['type']}

# Database Configuration
DATABASE_URL={database_url}
SUPABASE_DB_HOST={host}
SUPABASE_DB_NAME={credentials['database']}
SUPABASE_DB_USER={credentials['user']}
SUPABASE_DB_PASSWORD={credentials['password']}
SUPABASE_DB_PORT={credentials['port']}

# Supabase Project Settings (ajuste conforme necessário)
SUPABASE_URL=https://{self.project_ref or 'SEU_PROJETO'}.supabase.co
SUPABASE_ANON_KEY=SUA_ANON_KEY_AQUI
SUPABASE_SERVICE_ROLE_KEY=SUA_SERVICE_KEY_AQUI

# Django Settings
DEBUG=True
SECRET_KEY=django-insecure-CHANGE-ME
ALLOWED_HOSTS=localhost,127.0.0.1

# Environment
ENVIRONMENT=development
"""

        # Escreve arquivo .env
        env_file = ".env"
        try:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            print(f"✅ Arquivo {env_file} criado com sucesso!")
            print(f"📁 Localização: {os.path.abspath(env_file)}")
            return env_file
        except Exception as e:
            print(f"❌ Erro ao criar arquivo .env: {e}")
            return None

    def generate_settings_update(self, host_info, credentials):
        """Gera código para atualizar settings.py"""
        host = host_info['host']

        settings_code = f"""# Configuração de Banco de Dados Supabase - Atualizada em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Host funcional: {host} (IP: {host_info['ip']})

import os
from decouple import config

# Database Configuration
DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': config('SUPABASE_DB_HOST', default='{host}'),
        'NAME': config('SUPABASE_DB_NAME', default='{credentials['database']}'),
        'USER': config('SUPABASE_DB_USER', default='{credentials['user']}'),
        'PASSWORD': config('SUPABASE_DB_PASSWORD', default=''),
        'PORT': config('SUPABASE_DB_PORT', default='{credentials['port']}'),
        'OPTIONS': {{
            'connect_timeout': 30,
            'options': '-c statement_timeout=30000'
        }},
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }}
}}

# Configuração alternativa usando DATABASE_URL
# import dj_database_url
# DATABASES = {{
#     'default': dj_database_url.config(
#         default=config('DATABASE_URL', default=''),
#         conn_max_age=600,
#         conn_health_checks=True,
#     )
# }}
"""

        print("📝 Configuração sugerida para settings.py:")
        print("=" * 60)
        print(settings_code)
        print("=" * 60)

        return settings_code

    def save_results_report(self, successful_connections):
        """Salva relatório completo dos resultados"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'project_ref': self.project_ref,
            'total_hosts_tested': len(self.test_results),
            'working_hosts_found': len(self.working_hosts),
            'successful_connections': len(successful_connections),
            'test_results': self.test_results,
            'working_hosts': self.working_hosts,
            'successful_connections': successful_connections
        }

        report_file = "supabase_host_finder_report.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"📄 Relatório completo salvo em: {report_file}")
        except Exception as e:
            print(f"❌ Erro ao salvar relatório: {e}")

    def run_complete_scan(self):
        """Executa escaneamento completo"""
        print("🚀 Iniciando Busca por Host Correto do Supabase")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Etapa 1: Escanear hosts
            working_hosts = self.scan_for_working_hosts()

            if not working_hosts:
                print("\n❌ Nenhum host funcional encontrado!")
                print("💡 Verifique se:")
                print("   1. Projeto Supabase está ativo")
                print("   2. Conexão com internet está estável")
                print("   3. Firewall não está bloqueando porta 5432")
                return

            print(f"\n✅ Encontrados {len(working_hosts)} hosts funcionais:")
            for i, host_info in enumerate(working_hosts, 1):
                print(f"   {i}. {host_info['host']} (IP: {host_info['ip']}, Tipo: {host_info['type']})")

            # Etapa 2: Solicitar credenciais
            print(f"\n{'=' * 70}")
            try_credentials = input("🔑 Deseja testar conexões com credenciais? (s/N): ").strip().lower()

            if try_credentials in ['s', 'sim', 'y', 'yes']:
                credentials = self.prompt_for_credentials()

                # Etapa 3: Testar conexões
                successful_connections = self.test_working_hosts_with_credentials(credentials)

                if successful_connections:
                    # Escolher melhor conexão
                    best_connection = None
                    for conn in successful_connections:
                        if conn.get('credentials_valid'):
                            best_connection = conn
                            break

                    if not best_connection:
                        best_connection = successful_connections[0]  # Pega primeiro disponível

                    print(f"\n🎯 Melhor conexão encontrada: {best_connection['host']}")

                    # Etapa 4: Gerar configurações
                    env_file = self.generate_env_file(best_connection, credentials)
                    settings_code = self.generate_settings_update(best_connection, credentials)

                    print(f"\n{'=' * 70}")
                    print("✅ PRÓXIMOS PASSOS:")
                    print("1. Instale python-decouple: pip install python-decouple")
                    print("2. Atualize seu settings.py com a configuração mostrada acima")
                    print("3. Reinicie o servidor Django")
                    print("4. Teste a conexão")

                # Salvar relatório
                self.save_results_report(successful_connections)
            else:
                print("\n📋 Hosts funcionais encontrados (sem teste de credenciais):")
                for host_info in working_hosts:
                    print(f"   • {host_info['host']} (IP: {host_info['ip']})")

                self.save_results_report([])

        except KeyboardInterrupt:
            print("\n\n⚡ Processo interrompido pelo usuário.")
        except Exception as e:
            print(f"\n❌ Erro inesperado: {e}")


def main():
    """Função principal"""
    try:
        finder = SupabaseHostFinder()
        finder.run_complete_scan()

        print(f"\n{'=' * 70}")
        print("✅ Busca concluída!")
        print(f"{'=' * 70}")

    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())