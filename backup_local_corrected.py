#!/usr/bin/env python
"""
SCRIPT DE BACKUP CORRIGIDO - BANCO LOCAL cgbookstore_db
======================================================
Este script extrai todos os dados do PostgreSQL local (cgbookstore_db)
usando as credenciais corretas para migração ao Supabase.

Uso: python backup_local_corrected.py
"""

import os
import json
import django
from datetime import datetime
from django.conf import settings
from django.core import serializers
from django.apps import apps

# Configurar Django para usar .env.local
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')

# Forçar uso do arquivo .env.local
import environ

env = environ.Env()

# Ler arquivo .env.local
env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
if os.path.exists(env_file):
    env.read_env(env_file)
    print(f"✅ Usando configurações de: {env_file}")
else:
    print(f"❌ Arquivo {env_file} não encontrado!")

django.setup()

# Imports dos models após setup do Django
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType


class DatabaseBackup:
    def __init__(self):
        self.backup_data = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_file = f"backup_cgbookstore_local_{self.timestamp}.json"

    def log(self, message):
        """Log com timestamp"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def test_connection(self):
        """Testar conexão com banco local"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database(), version();")
                db_info = cursor.fetchone()
                self.log(f"✅ Conectado ao banco: {db_info[0]}")
                self.log(f"✅ Versão PostgreSQL: {db_info[1][:30]}...")
                return True
        except Exception as e:
            self.log(f"❌ Erro de conexão: {str(e)}")
            return False

    def get_table_counts(self):
        """Obter contagem de todas as tabelas"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                # Query para contar registros das tabelas principais
                tables_to_check = [
                    'user', 'core_book', 'core_author', 'core_profile',
                    'core_userbookshelf', 'chatbot_literario_conversation',
                    'chatbot_literario_message', 'chatbot_literario_knowledgeitem'
                ]

                self.log("\n📊 CONTAGEM DE REGISTROS POR TABELA:")
                self.log("=" * 50)

                total_records = 0
                for table in tables_to_check:
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
                        count = cursor.fetchone()[0]
                        total_records += count
                        self.log(f"  {table}: {count} registros")
                    except Exception as e:
                        self.log(f"  {table}: Erro - {str(e)}")

                self.log(f"\n📊 TOTAL ESTIMADO: {total_records} registros")
                return total_records

        except Exception as e:
            self.log(f"❌ Erro ao contar tabelas: {str(e)}")
            return 0

    def get_model_data_by_table(self, table_name, model_name=None):
        """Extrair dados diretamente da tabela"""
        try:
            from django.db import connection

            # Usar nome da tabela como modelo se não fornecido
            if not model_name:
                model_name = table_name

            with connection.cursor() as cursor:
                # Contar registros
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                count = cursor.fetchone()[0]

                if count > 0:
                    # Buscar todos os dados
                    cursor.execute(f'SELECT * FROM "{table_name}";')
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()

                    # Converter para formato serializável
                    data = []
                    for row in rows:
                        row_dict = {}
                        for i, value in enumerate(row):
                            # Converter tipos não serializáveis
                            if hasattr(value, 'isoformat'):  # datetime
                                row_dict[columns[i]] = value.isoformat()
                            elif isinstance(value, (int, float, str, bool)) or value is None:
                                row_dict[columns[i]] = value
                            else:
                                row_dict[columns[i]] = str(value)
                        data.append(row_dict)

                    self.backup_data[model_name] = {
                        'count': count,
                        'columns': columns,
                        'data': data
                    }
                    self.log(f"✅ {table_name}: {count} registros extraídos")
                else:
                    self.log(f"⚠️  {table_name}: Tabela vazia")

        except Exception as e:
            self.log(f"❌ Erro ao extrair {table_name}: {str(e)}")

    def backup_main_tables(self):
        """Backup das tabelas principais identificadas"""
        self.log("\n🔍 EXTRAINDO DADOS - TABELAS PRINCIPAIS")
        self.log("=" * 50)

        # Tabelas principais com dados importantes
        main_tables = {
            'user': 'users',
            'core_book': 'books',
            'core_author': 'authors',
            'core_profile': 'profiles',
            'core_userbookshelf': 'user_bookshelves',
            'chatbot_literario_conversation': 'chatbot_conversations',
            'chatbot_literario_message': 'chatbot_messages',
            'chatbot_literario_knowledgeitem': 'chatbot_knowledge',
            'core_bookauthor': 'book_authors',
            'core_readingprogress': 'reading_progress',
            'core_readingstats': 'reading_stats'
        }

        for table_name, model_name in main_tables.items():
            self.get_model_data_by_table(table_name, model_name)

    def backup_django_system(self):
        """Backup das tabelas do sistema Django"""
        self.log("\n⚙️  EXTRAINDO DADOS - SISTEMA DJANGO")
        self.log("=" * 50)

        django_tables = {
            'django_content_type': 'content_types',
            'auth_permission': 'permissions',
            'auth_group': 'groups',
            'django_migrations': 'migrations'
        }

        for table_name, model_name in django_tables.items():
            self.get_model_data_by_table(table_name, model_name)

    def create_migration_info(self):
        """Criar informações da migração"""
        total_records = sum(
            data.get('count', 0)
            for data in self.backup_data.values()
            if isinstance(data, dict) and 'count' in data
        )

        self.backup_data['_migration_info'] = {
            'timestamp': self.timestamp,
            'source_database': 'PostgreSQL Local (cgbookstore_db)',
            'target_database': 'Supabase PostgreSQL',
            'django_version': django.get_version(),
            'total_models': len(self.backup_data) - 1,
            'total_records': total_records,
            'source_credentials': {
                'host': 'localhost',
                'port': 5432,
                'database': 'cgbookstore_db',
                'user': 'cgbookstore_user'
            },
            'created_at': datetime.now().isoformat()
        }

    def save_backup(self):
        """Salvar backup em arquivo JSON"""
        try:
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.backup_data, f, indent=2, ensure_ascii=False, default=str)

            file_size = os.path.getsize(self.backup_file) / (1024 * 1024)  # MB
            self.log(f"\n💾 BACKUP SALVO: {self.backup_file}")
            self.log(f"📊 Tamanho: {file_size:.2f} MB")

        except Exception as e:
            self.log(f"❌ Erro ao salvar backup: {str(e)}")

    def print_summary(self):
        """Imprimir resumo do backup"""
        self.log("\n" + "=" * 60)
        self.log("📋 RESUMO DO BACKUP - cgbookstore_db")
        self.log("=" * 60)

        total_records = 0
        for model_name, data in self.backup_data.items():
            if model_name != '_migration_info' and isinstance(data, dict):
                count = data.get('count', 0)
                total_records += count
                self.log(f"  {model_name}: {count} registros")

        self.log(f"\n📊 TOTAL DE REGISTROS: {total_records}")
        self.log(f"🕒 HORÁRIO: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        self.log(f"💾 ARQUIVO: {self.backup_file}")

    def run_backup(self):
        """Executar backup completo"""
        self.log("🚀 INICIANDO BACKUP DO BANCO LOCAL - cgbookstore_db")
        self.log("=" * 60)

        # Testar conexão
        if not self.test_connection():
            self.log("❌ Falha na conexão. Verifique as credenciais.")
            return None

        # Contar registros
        expected_records = self.get_table_counts()

        # Executar backups
        self.backup_django_system()
        self.backup_main_tables()

        # Adicionar informações da migração
        self.create_migration_info()

        # Salvar arquivo
        self.save_backup()

        # Mostrar resumo
        self.print_summary()

        return self.backup_file


def main():
    """Função principal"""
    print("=" * 60)
    print("🔄 BACKUP CORRETO - cgbookstore_db → SUPABASE")
    print("=" * 60)

    # Criar instância do backup
    backup = DatabaseBackup()

    # Executar backup
    backup_file = backup.run_backup()

    if backup_file:
        print("\n" + "=" * 60)
        print("✅ BACKUP CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print(f"📁 Arquivo gerado: {backup_file}")
        print("🔄 Próximo passo: executar migrate_to_supabase.py")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ BACKUP FALHADO - Verificar credenciais")
        print("=" * 60)


if __name__ == "__main__":
    main()