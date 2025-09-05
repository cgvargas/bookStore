#!/usr/bin/env python3
"""
Script Final para Corrigir Configuração Supabase
Arquivo: cgbookstore/config/supabase_final_fix.py

Este script testa as configurações corretas do Supabase baseado nos resultados anteriores.
"""

import os
import sys
import psycopg2
import json
from datetime import datetime


class SupabaseFinalFix:
    def __init__(self):
        self.project_ref = "amytpwmgpkizuwkwvpzm"
        self.password = "Oa023568910@"
        self.working_config = None

    def print_header(self, title):
        """Imprime cabeçalho formatado"""
        print(f"\n{'=' * 60}")
        print(f"🔧 {title}")
        print(f"{'=' * 60}")

    def test_connection_config(self, config_name, host, port, database, user, password):
        """Testa uma configuração específica de conexão"""
        print(f"\n🔗 Testando: {config_name}")
        print(f"   Host: {host}:{port}")
        print(f"   Database: {database}")
        print(f"   User: {user}")

        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                connect_timeout=15
            )

            # Testa uma query simples
            cursor = conn.cursor()
            cursor.execute("SELECT current_database(), current_user, version();")
            result = cursor.fetchone()

            print(f"✅ SUCESSO!")
            print(f"   Database: {result[0]}")
            print(f"   User: {result[1]}")
            print(f"   PostgreSQL: {result[2][:50]}...")

            cursor.close()
            conn.close()

            return {
                'success': True,
                'config': {
                    'name': config_name,
                    'host': host,
                    'port': port,
                    'database': database,
                    'user': user,
                    'password': password
                },
                'db_info': {
                    'database': result[0],
                    'user': result[1],
                    'version': result[2]
                }
            }

        except psycopg2.OperationalError as e:
            error_msg = str(e)
            print(f"❌ FALHA: {error_msg}")

            # Analisa o tipo de erro
            if "Tenant or user not found" in error_msg:
                print("   💡 Dica: Formato de usuário ou projeto incorreto")
            elif "authentication failed" in error_msg:
                print("   💡 Dica: Senha incorreta")
            elif "timeout" in error_msg.lower():
                print("   💡 Dica: Conexão muito lenta")
            elif "connection refused" in error_msg.lower():
                print("   💡 Dica: Porta ou host incorreto")

            return {'success': False, 'error': error_msg}

        except Exception as e:
            print(f"❌ ERRO: {str(e)}")
            return {'success': False, 'error': str(e)}

    def test_all_configurations(self):
        """Testa todas as configurações possíveis"""
        self.print_header("TESTANDO CONFIGURAÇÕES SUPABASE")

        # Configurações para testar baseadas no diagnóstico anterior
        test_configs = [
            # Configuração 1: Host direto com porta pooler
            {
                'name': 'Host Direto - Porta Pooler (6543)',
                'host': f'{self.project_ref}.supabase.co',
                'port': 6543,
                'database': 'postgres',
                'user': f'postgres.{self.project_ref}',
                'password': self.password
            },

            # Configuração 2: Host direto com porta padrão
            {
                'name': 'Host Direto - Porta Padrão (5432)',
                'host': f'{self.project_ref}.supabase.co',
                'port': 5432,
                'database': 'postgres',
                'user': 'postgres',
                'password': self.password
            },

            # Configuração 3: Pooler US East com projeto específico
            {
                'name': 'Pooler US East - Com Projeto',
                'host': 'aws-0-us-east-1.pooler.supabase.com',
                'port': 5432,
                'database': 'postgres',
                'user': f'postgres.{self.project_ref}',
                'password': self.password
            },

            # Configuração 4: Pooler US East com modo transaction
            {
                'name': 'Pooler US East - Transaction Mode',
                'host': 'aws-0-us-east-1.pooler.supabase.com',
                'port': 6543,
                'database': 'postgres',
                'user': f'postgres.{self.project_ref}',
                'password': self.password
            },

            # Configuração 5: Host com db prefix
            {
                'name': 'Host com DB Prefix',
                'host': f'db.{self.project_ref}.supabase.co',
                'port': 5432,
                'database': 'postgres',
                'user': 'postgres',
                'password': self.password
            },
        ]

        successful_configs = []

        for config in test_configs:
            result = self.test_connection_config(
                config['name'],
                config['host'],
                config['port'],
                config['database'],
                config['user'],
                config['password']
            )

            if result['success']:
                successful_configs.append(result)
                if not self.working_config:  # Pega a primeira que funcionar
                    self.working_config = result

        return successful_configs

    def create_env_file(self, config):
        """Cria arquivo .env com configuração funcional"""
        self.print_header("CRIANDO ARQUIVO .ENV")

        # Gera DATABASE_URL
        database_url = (f"postgresql://{config['config']['user']}:{config['config']['password']}"
                        f"@{config['config']['host']}:{config['config']['port']}/{config['config']['database']}")

        # Conteúdo do arquivo .env
        env_content = f"""# Configuracao Supabase - Gerado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Configuracao funcional encontrada: {config['config']['name']}

# Database Configuration
DATABASE_URL={database_url}
SUPABASE_DB_HOST={config['config']['host']}
SUPABASE_DB_NAME={config['config']['database']}
SUPABASE_DB_USER={config['config']['user']}
SUPABASE_DB_PASSWORD={config['config']['password']}
SUPABASE_DB_PORT={config['config']['port']}

# Supabase Project Settings
SUPABASE_URL=https://{self.project_ref}.supabase.co
SUPABASE_ANON_KEY=SEU_ANON_KEY_AQUI
SUPABASE_SERVICE_ROLE_KEY=SEU_SERVICE_KEY_AQUI

# Django Settings
DEBUG=True
SECRET_KEY=django-insecure-CHANGE-THIS-IN-PRODUCTION
ALLOWED_HOSTS=localhost,127.0.0.1,{self.project_ref}.supabase.co

# Environment
ENVIRONMENT=development
"""

        # Escreve arquivo .env
        env_file = ".env"
        backup_file = f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Faz backup se arquivo já existir
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as original:
                    with open(backup_file, 'w') as backup:
                        backup.write(original.read())
                print(f"📋 Backup criado: {backup_file}")
            except Exception as e:
                print(f"⚠️  Erro ao criar backup: {e}")

        try:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            print(f"✅ Arquivo {env_file} criado com sucesso!")
            print(f"📁 Localizacao: {os.path.abspath(env_file)}")
            return env_file
        except Exception as e:
            print(f"❌ Erro ao criar arquivo .env: {e}")
            return None

    def create_settings_snippet(self, config):
        """Cria snippet para settings.py"""
        self.print_header("CONFIGURACAO PARA SETTINGS.PY")

        settings_code = f'''# Configuracao de Banco de Dados Supabase
# Configuracao funcional: {config['config']['name']}
# Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

import os
from decouple import config

# Database Configuration
DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': config('SUPABASE_DB_HOST', default='{config['config']['host']}'),
        'NAME': config('SUPABASE_DB_NAME', default='{config['config']['database']}'),
        'USER': config('SUPABASE_DB_USER', default='{config['config']['user']}'),
        'PASSWORD': config('SUPABASE_DB_PASSWORD', default=''),
        'PORT': config('SUPABASE_DB_PORT', default='{config['config']['port']}', cast=int),
        'OPTIONS': {{
            'connect_timeout': 30,
            'options': '-c statement_timeout=30000',
            'sslmode': 'require',
        }},
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }}
}}

# Alternativa usando DATABASE_URL (mais simples)
# import dj_database_url
# DATABASES = {{
#     'default': dj_database_url.config(
#         default=config('DATABASE_URL', default=''),
#         conn_max_age=600,
#         conn_health_checks=True,
#     )
# }}'''

        print("📝 Adicione ao seu settings.py:")
        print("=" * 60)
        print(settings_code)
        print("=" * 60)

        # Salva em arquivo
        settings_file = "settings_supabase_config.py"
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(settings_code)
            print(f"\n💾 Configuracao salva em: {settings_file}")
        except Exception as e:
            print(f"\n❌ Erro ao salvar configuracao: {e}")

        return settings_code

    def test_final_connection(self, config):
        """Testa conexão final usando DATABASE_URL"""
        self.print_header("TESTE FINAL COM DATABASE_URL")

        database_url = (f"postgresql://{config['config']['user']}:{config['config']['password']}"
                        f"@{config['config']['host']}:{config['config']['port']}/{config['config']['database']}")

        print(f"🔗 Testando DATABASE_URL completa...")

        try:
            # Simula como o Django faria
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()

            # Testa queries comuns do Django
            cursor.execute("SELECT 1;")
            cursor.execute("SELECT current_database(), current_user;")
            result = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
            table_count = cursor.fetchone()[0]

            print(f"✅ DATABASE_URL funcional!")
            print(f"   Database: {result[0]}")
            print(f"   User: {result[1]}")
            print(f"   Tabelas publicas: {table_count}")

            cursor.close()
            conn.close()
            return True

        except Exception as e:
            print(f"❌ Erro com DATABASE_URL: {e}")
            return False

    def run_complete_fix(self):
        """Executa correção completa"""
        print("🚀 CORRECAO FINAL DO SUPABASE")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Projeto: {self.project_ref}")

        try:
            # Testa todas as configurações
            successful_configs = self.test_all_configurations()

            if not successful_configs:
                print(f"\n❌ NENHUMA CONFIGURACAO FUNCIONAL ENCONTRADA!")
                print("💡 Possíveis soluções:")
                print("   1. Verifique se o projeto Supabase está ativo")
                print("   2. Confirme a senha no painel do Supabase")
                print("   3. Verifique se há restrições de IP")
                print("   4. Tente pausar e despausar o projeto")
                return False

            print(f"\n🎉 SUCESSO! {len(successful_configs)} configuração(ões) funcional(is) encontrada(s):")
            for i, config in enumerate(successful_configs, 1):
                print(f"   {i}. {config['config']['name']}")

            # Usa a primeira configuração funcional
            best_config = successful_configs[0]
            print(f"\n🏆 Usando configuração: {best_config['config']['name']}")

            # Cria arquivo .env
            env_file = self.create_env_file(best_config)

            # Cria configuração para settings.py
            settings_code = self.create_settings_snippet(best_config)

            # Teste final
            if self.test_final_connection(best_config):
                print(f"\n{'=' * 60}")
                print("✅ CONFIGURACAO SUPABASE CORRIGIDA COM SUCESSO!")
                print(f"{'=' * 60}")
                print("\n📋 PROXIMOS PASSOS:")
                print("1. Instale python-decouple:")
                print("   pip install python-decouple")
                print("\n2. Instale dj-database-url (opcional):")
                print("   pip install dj-database-url")
                print("\n3. Atualize seu cgbookstore/config/settings.py com a configuracao mostrada")
                print("\n4. Reinicie o servidor Django:")
                print("   python manage.py runserver")
                print("\n5. Teste o acesso ao profile e outras funcionalidades")

                return True
            else:
                print(f"\n⚠️  Configuracao encontrada mas teste final falhou")
                return False

        except KeyboardInterrupt:
            print("\n\n⚡ Processo interrompido pelo usuario.")
            return False
        except Exception as e:
            print(f"\n❌ Erro inesperado: {e}")
            return False


def main():
    """Função principal"""
    try:
        fixer = SupabaseFinalFix()
        success = fixer.run_complete_fix()

        if success:
            print(f"\n🎯 Processo concluído com sucesso!")
            return 0
        else:
            print(f"\n❌ Processo falhou. Verifique os erros acima.")
            return 1

    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())