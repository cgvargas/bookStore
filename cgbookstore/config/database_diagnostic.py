#!/usr/bin/env python3
"""
Script de Diagnóstico para Problemas de Conectividade com Supabase
Arquivo: cgbookstore/config/database_diagnostic.py

Este script identifica e diagnostica problemas de conectividade com o banco Supabase.
"""

import os
import sys
import socket
import subprocess
import psycopg2
from urllib.parse import urlparse
import time
import json
from datetime import datetime


class SupabaseDiagnostic:
    def __init__(self):
        self.host = "db.amytpwmgpkizuwkwvpzm.supabase.co"
        self.port = 5432
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'recommendations': []
        }

    def print_header(self, title):
        """Imprime cabeçalho formatado"""
        print(f"\n{'=' * 60}")
        print(f"🔍 {title}")
        print(f"{'=' * 60}")

    def print_test(self, test_name, status, details=""):
        """Imprime resultado de teste"""
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   └─ {details}")

        self.results['tests'][test_name] = {
            'status': status,
            'details': details
        }

    def test_dns_resolution(self):
        """Testa resolução DNS do host Supabase"""
        self.print_header("TESTE 1: Resolução DNS")

        try:
            # Teste de resolução DNS
            ip = socket.gethostbyname(self.host)
            self.print_test("Resolução DNS", "PASS", f"Host resolvido para IP: {ip}")
            return True
        except socket.gaierror as e:
            self.print_test("Resolução DNS", "FAIL", f"Erro: {str(e)}")
            self.results['recommendations'].append(
                "❌ CRÍTICO: Problema de DNS. Verifique conexão com internet e configurações de DNS."
            )
            return False

    def test_network_connectivity(self):
        """Testa conectividade de rede"""
        self.print_header("TESTE 2: Conectividade de Rede")

        try:
            # Teste de ping
            if os.name == 'nt':  # Windows
                result = subprocess.run(['ping', '-n', '4', self.host],
                                        capture_output=True, text=True, timeout=10)
            else:  # Linux/Mac
                result = subprocess.run(['ping', '-c', '4', self.host],
                                        capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                self.print_test("Ping Test", "PASS", "Host responde ao ping")
                return True
            else:
                self.print_test("Ping Test", "FAIL", "Host não responde ao ping")
                return False

        except subprocess.TimeoutExpired:
            self.print_test("Ping Test", "FAIL", "Timeout no ping")
            return False
        except Exception as e:
            self.print_test("Ping Test", "FAIL", f"Erro: {str(e)}")
            return False

    def test_port_connectivity(self):
        """Testa conectividade na porta PostgreSQL"""
        self.print_header("TESTE 3: Conectividade na Porta 5432")

        try:
            # Teste de conexão na porta 5432
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((self.host, self.port))
            sock.close()

            if result == 0:
                self.print_test("Porta 5432", "PASS", "Porta PostgreSQL acessível")
                return True
            else:
                self.print_test("Porta 5432", "FAIL", "Porta PostgreSQL não acessível")
                self.results['recommendations'].append(
                    "❌ Porta 5432 bloqueada. Verifique firewall/proxy corporativo."
                )
                return False

        except Exception as e:
            self.print_test("Porta 5432", "FAIL", f"Erro: {str(e)}")
            return False

    def test_database_credentials(self):
        """Testa credenciais do banco de dados"""
        self.print_header("TESTE 4: Credenciais do Banco")

        # Busca credenciais em variáveis de ambiente
        database_configs = [
            {
                'name': 'Variáveis de Ambiente',
                'host': os.getenv('SUPABASE_DB_HOST', self.host),
                'database': os.getenv('SUPABASE_DB_NAME', 'postgres'),
                'user': os.getenv('SUPABASE_DB_USER', ''),
                'password': os.getenv('SUPABASE_DB_PASSWORD', ''),
                'port': os.getenv('SUPABASE_DB_PORT', '5432')
            },
            {
                'name': 'DATABASE_URL',
                'url': os.getenv('DATABASE_URL', '')
            }
        ]

        # Testa cada configuração
        for config in database_configs:
            if 'url' in config and config['url']:
                self.test_database_url(config['url'])
            elif all([config.get('host'), config.get('database'),
                      config.get('user'), config.get('password')]):
                self.test_database_connection(config)
            else:
                self.print_test(f"Config {config['name']}", "WARN",
                                "Credenciais incompletas ou não encontradas")

    def test_database_url(self, database_url):
        """Testa conexão usando DATABASE_URL"""
        try:
            parsed = urlparse(database_url)
            if not parsed.hostname:
                self.print_test("DATABASE_URL", "FAIL", "URL inválida")
                return False

            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            self.print_test("DATABASE_URL", "PASS", f"Conectado: {version[:50]}...")
            return True

        except psycopg2.OperationalError as e:
            self.print_test("DATABASE_URL", "FAIL", str(e))
            self.analyze_psycopg2_error(str(e))
            return False
        except Exception as e:
            self.print_test("DATABASE_URL", "FAIL", f"Erro: {str(e)}")
            return False

    def test_database_connection(self, config):
        """Testa conexão usando parâmetros individuais"""
        try:
            conn = psycopg2.connect(
                host=config['host'],
                database=config['database'],
                user=config['user'],
                password=config['password'],
                port=config['port'],
                connect_timeout=10
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            self.print_test(f"Config {config['name']}", "PASS",
                            f"Conectado: {version[:50]}...")
            return True

        except psycopg2.OperationalError as e:
            self.print_test(f"Config {config['name']}", "FAIL", str(e))
            self.analyze_psycopg2_error(str(e))
            return False
        except Exception as e:
            self.print_test(f"Config {config['name']}", "FAIL", f"Erro: {str(e)}")
            return False

    def analyze_psycopg2_error(self, error_msg):
        """Analisa erros específicos do psycopg2"""
        if "could not translate host name" in error_msg:
            self.results['recommendations'].append(
                "🔧 DNS: Problema de resolução de nome. Tente usar IP direto ou verificar DNS."
            )
        elif "Connection refused" in error_msg:
            self.results['recommendations'].append(
                "🔧 REDE: Conexão recusada. Verifique firewall e configurações de rede."
            )
        elif "authentication failed" in error_msg:
            self.results['recommendations'].append(
                "🔧 AUTH: Credenciais inválidas. Verifique usuário e senha do Supabase."
            )
        elif "timeout" in error_msg.lower():
            self.results['recommendations'].append(
                "🔧 TIMEOUT: Conexão lenta. Verifique estabilidade da internet."
            )

    def check_environment_variables(self):
        """Verifica variáveis de ambiente relevantes"""
        self.print_header("TESTE 5: Variáveis de Ambiente")

        env_vars = [
            'DATABASE_URL',
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY',
            'SUPABASE_DB_HOST',
            'SUPABASE_DB_NAME',
            'SUPABASE_DB_USER',
            'SUPABASE_DB_PASSWORD',
            'SUPABASE_DB_PORT'
        ]

        found_vars = []
        for var in env_vars:
            value = os.getenv(var)
            if value:
                # Mascarar senhas e chaves
                if 'password' in var.lower() or 'key' in var.lower():
                    display_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                else:
                    display_value = value

                self.print_test(f"Env {var}", "PASS", f"Definida: {display_value}")
                found_vars.append(var)
            else:
                self.print_test(f"Env {var}", "WARN", "Não definida")

        if not found_vars:
            self.results['recommendations'].append(
                "⚠️  CONFIGURAÇÃO: Nenhuma variável de ambiente Supabase encontrada."
            )

    def test_alternative_hosts(self):
        """Testa hosts alternativos do Supabase"""
        self.print_header("TESTE 6: Hosts Alternativos")

        # Diferentes variações do host Supabase
        alternative_hosts = [
            "db.amytpwmgpkizuwkwvpzm.supabase.co",  # Host original
            "aws-0-us-east-1.pooler.supabase.com",  # Pooler alternativo
        ]

        for host in alternative_hosts:
            try:
                ip = socket.gethostbyname(host)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, 5432))
                sock.close()

                if result == 0:
                    self.print_test(f"Host {host}", "PASS", f"IP: {ip}")
                else:
                    self.print_test(f"Host {host}", "FAIL", f"IP: {ip}, Porta inacessível")

            except Exception as e:
                self.print_test(f"Host {host}", "FAIL", str(e))

    def generate_recommendations(self):
        """Gera recomendações baseadas nos testes"""
        self.print_header("RECOMENDAÇÕES")

        # Adiciona recomendações gerais
        if not any(test['status'] == 'PASS' for test in self.results['tests'].values()
                   if 'DNS' in test or 'Conectividade' in test):
            self.results['recommendations'].append(
                "🌐 INTERNET: Verifique sua conexão com a internet."
            )

        if not any(test['status'] == 'PASS' for test in self.results['tests'].values()
                   if 'Porta' in test):
            self.results['recommendations'].append(
                "🔥 FIREWALL: Porta 5432 pode estar bloqueada por firewall corporativo."
            )

        # Recomendações específicas para Windows
        if os.name == 'nt':
            self.results['recommendations'].append(
                "🖥️  WINDOWS: Tente executar como administrador se houver problemas de rede."
            )

        # Imprime todas as recomendações
        if self.results['recommendations']:
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"{i}. {rec}")
        else:
            print("✅ Nenhum problema detectado!")

    def save_report(self):
        """Salva relatório em arquivo JSON"""
        report_file = "database_diagnostic_report.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Relatório salvo em: {report_file}")
        except Exception as e:
            print(f"\n❌ Erro ao salvar relatório: {e}")

    def run_full_diagnostic(self):
        """Executa diagnóstico completo"""
        print("🚀 Iniciando Diagnóstico de Conectividade Supabase")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Executa todos os testes
        self.test_dns_resolution()
        self.test_network_connectivity()
        self.test_port_connectivity()
        self.check_environment_variables()
        self.test_database_credentials()
        self.test_alternative_hosts()

        # Gera recomendações e salva relatório
        self.generate_recommendations()
        self.save_report()

        print(f"\n{'=' * 60}")
        print("✅ Diagnóstico concluído!")
        print(f"{'=' * 60}")


def main():
    """Função principal"""
    try:
        diagnostic = SupabaseDiagnostic()
        diagnostic.run_full_diagnostic()
    except KeyboardInterrupt:
        print("\n\n⚡ Diagnóstico interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())