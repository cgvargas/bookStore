#!/usr/bin/env python
"""
SCRIPT DE MIGRAÇÃO - BACKUP LOCAL → SUPABASE
============================================
Este script importa os dados do backup local para o Supabase,
preservando relacionamentos e validando a migração completa.

Uso: python migrate_to_supabase.py
"""

import os
import json
import django
from datetime import datetime
from django.conf import settings
from django.db import transaction, connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()


class SupabaseMigration:
    def __init__(self, backup_file=None):
        self.backup_file = backup_file or self.find_latest_backup()
        self.backup_data = {}
        self.migration_stats = {
            'tables_migrated': 0,
            'records_migrated': 0,
            'errors': [],
            'warnings': []
        }
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def log(self, message, level="INFO"):
        """Log com timestamp e nível"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "WARNING": "⚠️ ",
            "ERROR": "❌"
        }.get(level, "📝")

        print(f"[{timestamp}] {prefix} {message}")

        if level in ["WARNING", "ERROR"]:
            self.migration_stats[level.lower() + 's'].append(message)

    def find_latest_backup(self):
        """Encontrar o backup mais recente"""
        backup_files = [f for f in os.listdir('.') if f.startswith('backup_cgbookstore_local_') and f.endswith('.json')]
        if not backup_files:
            self.log("Nenhum arquivo de backup encontrado!", "ERROR")
            return None

        latest_backup = sorted(backup_files)[-1]
        self.log(f"Backup encontrado: {latest_backup}")
        return latest_backup

    def load_backup(self):
        """Carregar dados do backup"""
        try:
            if not self.backup_file or not os.path.exists(self.backup_file):
                self.log(f"Arquivo de backup não encontrado: {self.backup_file}", "ERROR")
                return False

            with open(self.backup_file, 'r', encoding='utf-8') as f:
                self.backup_data = json.load(f)

            total_records = sum(
                data.get('count', 0)
                for data in self.backup_data.values()
                if isinstance(data, dict) and 'count' in data
            )

            self.log(f"Backup carregado: {total_records} registros")

            # Mostrar informações do backup
            if '_migration_info' in self.backup_data:
                info = self.backup_data['_migration_info']
                self.log(f"Origem: {info.get('source_database', 'N/A')}")
                self.log(f"Criado em: {info.get('created_at', 'N/A')}")

            return True

        except Exception as e:
            self.log(f"Erro ao carregar backup: {str(e)}", "ERROR")
            return False

    def test_supabase_connection(self):
        """Testar conexão com Supabase"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database(), version();")
                db_info = cursor.fetchone()
                self.log(f"Conectado ao Supabase: {db_info[0]}")
                self.log(f"Versão PostgreSQL: {db_info[1][:50]}...")
                return True
        except Exception as e:
            self.log(f"Erro de conexão com Supabase: {str(e)}", "ERROR")
            return False

    def clear_existing_data(self):
        """Limpar dados existentes (opcional)"""
        self.log("\n🧹 LIMPANDO DADOS EXISTENTES NO SUPABASE")
        self.log("=" * 50)

        # Tabelas na ordem correta para evitar conflitos de FK
        tables_to_clear = [
            'chatbot_literario_message',
            'chatbot_literario_conversation',
            'chatbot_literario_conversationfeedback',
            'chatbot_literario_chatanalytics',
            'chatbot_literario_trainingsession',
            'chatbot_literario_knowledgeitem',
            'core_readingprogress',
            'core_readingstats',
            'core_userbookshelf',
            'core_bookauthor',
            'core_book',
            'core_author',
            'core_profile',
            'user_user_permissions',
            'user_groups',
            '"user"'  # Usar aspas por ser palavra reservada
        ]

        try:
            with connection.cursor() as cursor:
                for table in tables_to_clear:
                    try:
                        cursor.execute(f'DELETE FROM {table};')
                        self.log(f"Tabela {table} limpa")
                    except Exception as e:
                        self.log(f"Aviso ao limpar {table}: {str(e)}", "WARNING")

            self.log("Limpeza concluída", "SUCCESS")

        except Exception as e:
            self.log(f"Erro durante limpeza: {str(e)}", "ERROR")

    def migrate_table_data(self, table_key, table_data):
        """Migrar dados de uma tabela específica"""
        try:
            table_name = table_key
            count = table_data.get('count', 0)
            data = table_data.get('data', [])
            columns = table_data.get('columns', [])

            if count == 0:
                self.log(f"Tabela {table_name} vazia - pulando")
                return True

            self.log(f"Migrando {table_name}: {count} registros...")

            # Mapear nomes das tabelas
            table_mapping = {
                'users': '"user"',
                'books': 'core_book',
                'authors': 'core_author',
                'profiles': 'core_profile',
                'user_bookshelves': 'core_userbookshelf',
                'chatbot_conversations': 'chatbot_literario_conversation',
                'chatbot_messages': 'chatbot_literario_message',
                'chatbot_knowledge': 'chatbot_literario_knowledgeitem',
                'book_authors': 'core_bookauthor',
                'reading_progress': 'core_readingprogress',
                'reading_stats': 'core_readingstats'
            }

            actual_table = table_mapping.get(table_name, table_name)

            with connection.cursor() as cursor:
                for row in data:
                    try:
                        # Preparar colunas e valores
                        cols = list(row.keys())
                        values = list(row.values())

                        # Criar query de INSERT
                        placeholders = ', '.join(['%s'] * len(values))
                        cols_str = ', '.join([f'"{col}"' for col in cols])  # Usar aspas para colunas

                        query = f'INSERT INTO {actual_table} ({cols_str}) VALUES ({placeholders})'

                        cursor.execute(query, values)

                    except Exception as row_error:
                        self.log(f"Erro na linha {row.get('id', '?')} de {table_name}: {str(row_error)}", "WARNING")
                        continue

            self.migration_stats['tables_migrated'] += 1
            self.migration_stats['records_migrated'] += count
            self.log(f"✅ {table_name}: {count} registros migrados", "SUCCESS")

            return True

        except Exception as e:
            self.log(f"Erro ao migrar {table_key}: {str(e)}", "ERROR")
            return False

    def migrate_all_data(self):
        """Migrar todos os dados na ordem correta"""
        self.log("\n🚀 INICIANDO MIGRAÇÃO DE DADOS")
        self.log("=" * 50)

        # Ordem de migração para respeitar dependências
        migration_order = [
            'content_types',
            'permissions',
            'users',
            'profiles',
            'authors',
            'books',
            'book_authors',
            'user_bookshelves',
            'reading_progress',
            'reading_stats',
            'chatbot_knowledge',
            'chatbot_conversations',
            'chatbot_messages',
            'migrations'  # Por último
        ]

        # Migrar tabelas na ordem especificada
        for table_key in migration_order:
            if table_key in self.backup_data:
                self.migrate_table_data(table_key, self.backup_data[table_key])

        # Migrar qualquer tabela restante
        for table_key, table_data in self.backup_data.items():
            if table_key not in migration_order and table_key != '_migration_info':
                self.migrate_table_data(table_key, table_data)

    def validate_migration(self):
        """Validar se a migração foi bem-sucedida"""
        self.log("\n🔍 VALIDANDO MIGRAÇÃO")
        self.log("=" * 50)

        validation_queries = {
            'users': 'SELECT COUNT(*) FROM "user"',
            'books': 'SELECT COUNT(*) FROM core_book',
            'authors': 'SELECT COUNT(*) FROM core_author',
            'conversations': 'SELECT COUNT(*) FROM chatbot_literario_conversation',
            'messages': 'SELECT COUNT(*) FROM chatbot_literario_message'
        }

        validation_results = {}

        try:
            with connection.cursor() as cursor:
                for name, query in validation_queries.items():
                    cursor.execute(query)
                    count = cursor.fetchone()[0]
                    validation_results[name] = count
                    self.log(f"{name}: {count} registros no Supabase")

        except Exception as e:
            self.log(f"Erro durante validação: {str(e)}", "ERROR")

        return validation_results

    def create_migration_report(self):
        """Criar relatório final da migração"""
        self.log("\n📋 RELATÓRIO FINAL DA MIGRAÇÃO")
        self.log("=" * 60)

        self.log(f"🕒 Horário: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        self.log(f"📁 Backup usado: {self.backup_file}")
        self.log(f"📊 Tabelas migradas: {self.migration_stats['tables_migrated']}")
        self.log(f"📊 Registros migrados: {self.migration_stats['records_migrated']}")

        if self.migration_stats['warnings']:
            self.log(f"⚠️  Avisos: {len(self.migration_stats['warnings'])}")

        if self.migration_stats['errors']:
            self.log(f"❌ Erros: {len(self.migration_stats['errors'])}")

        self.log("🎯 Migração concluída!")

    def run_migration(self, clear_data=False):
        """Executar migração completa"""
        self.log("🚀 INICIANDO MIGRAÇÃO PARA SUPABASE")
        self.log("=" * 60)

        # 1. Carregar backup
        if not self.load_backup():
            return False

        # 2. Testar conexão
        if not self.test_supabase_connection():
            return False

        # 3. Limpar dados existentes (opcional)
        if clear_data:
            self.clear_existing_data()

        # 4. Migrar dados com transação
        try:
            with transaction.atomic():
                self.migrate_all_data()

        except Exception as e:
            self.log(f"Erro durante migração (rollback executado): {str(e)}", "ERROR")
            return False

        # 5. Validar migração
        self.validate_migration()

        # 6. Relatório final
        self.create_migration_report()

        return True


def main():
    """Função principal"""
    print("=" * 60)
    print("🔄 MIGRAÇÃO BACKUP LOCAL → SUPABASE")
    print("=" * 60)

    # Criar instância da migração
    migration = SupabaseMigration()

    # Perguntar se deve limpar dados existentes
    print("\n❓ Limpar dados existentes no Supabase antes da migração?")
    print("   [s] Sim - Limpar tudo e migrar dados limpos")
    print("   [n] Não - Adicionar aos dados existentes")

    choice = input("\nEscolha (s/n): ").lower().strip()
    clear_data = choice in ['s', 'sim', 'y', 'yes']

    # Executar migração
    success = migration.run_migration(clear_data=clear_data)

    if success:
        print("\n" + "=" * 60)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        print("🌐 Dados migrados para Supabase")
        print("🔗 Acesse o dashboard do Supabase para verificar")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ MIGRAÇÃO FALHADA")
        print("=" * 60)
        print("Verifique os logs acima para identificar problemas")
        print("=" * 60)


if __name__ == "__main__":
    main()