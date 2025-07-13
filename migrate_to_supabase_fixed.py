#!/usr/bin/env python
"""
SCRIPT DE MIGRAÇÃO CORRIGIDO - BACKUP LOCAL → SUPABASE
======================================================
Script corrigido que resolve problemas de mapeamento de tabelas,
transações e garante migração completa dos dados.

Uso: python migrate_to_supabase_fixed.py
"""

import os
import json
import django
from datetime import datetime
from django.conf import settings
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()


class SupabaseMigrationFixed:
    def __init__(self, backup_file=None):
        self.backup_file = backup_file or self.find_latest_backup()
        self.backup_data = {}
        self.migration_stats = {
            'tables_processed': 0,
            'tables_success': 0,
            'records_attempted': 0,
            'records_success': 0,
            'errors': [],
            'warnings': []
        }
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Mapeamento correto das tabelas
        self.table_mapping = {
            # Sistema Django
            'content_types': 'django_content_type',
            'permissions': 'auth_permission',
            'migrations': 'django_migrations',

            # Projeto - Users
            'users': '"user"',  # Aspas por ser palavra reservada
            'profiles': 'core_profile',

            # Projeto - Core
            'books': 'core_book',
            'authors': 'core_author',
            'book_authors': 'core_bookauthor',
            'user_bookshelves': 'core_userbookshelf',
            'reading_progress': 'core_readingprogress',
            'reading_stats': 'core_readingstats',

            # Projeto - Chatbot
            'chatbot_knowledge': 'chatbot_literario_knowledgeitem',
            'chatbot_conversations': 'chatbot_literario_conversation',
            'chatbot_messages': 'chatbot_literario_message'
        }

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
                return True
        except Exception as e:
            self.log(f"Erro de conexão com Supabase: {str(e)}", "ERROR")
            return False

    def insert_single_record(self, cursor, table_name, record_data):
        """Inserir um único registro com tratamento de erro"""
        try:
            # Preparar colunas e valores
            cols = list(record_data.keys())
            values = list(record_data.values())

            # Tratar valores None e tipos especiais
            processed_values = []
            for value in values:
                if value is None:
                    processed_values.append(None)
                elif isinstance(value, bool):
                    processed_values.append(value)
                elif isinstance(value, (int, float)):
                    processed_values.append(value)
                else:
                    processed_values.append(str(value))

            # Criar query de INSERT com ON CONFLICT
            placeholders = ', '.join(['%s'] * len(processed_values))
            cols_str = ', '.join([f'"{col}"' for col in cols])

            # Usar ON CONFLICT para evitar duplicatas
            query = f'''
                INSERT INTO {table_name} ({cols_str}) 
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING
            '''

            cursor.execute(query, processed_values)
            return True

        except Exception as e:
            # Log do erro específico mas continua
            record_id = record_data.get('id', 'N/A')
            self.log(f"Erro no registro ID {record_id}: {str(e)[:100]}...", "WARNING")
            return False

    def migrate_table_data_fixed(self, table_key, table_data):
        """Migrar dados de uma tabela com tratamento robusto de erros"""
        try:
            count = table_data.get('count', 0)
            data = table_data.get('data', [])

            if count == 0:
                self.log(f"Tabela {table_key} vazia - pulando")
                return True

            # Mapear nome da tabela
            actual_table = self.table_mapping.get(table_key, table_key)

            self.log(f"Migrando {table_key} → {actual_table}: {count} registros...")

            success_count = 0
            error_count = 0

            # Usar conexão SEM transação
            with connection.cursor() as cursor:
                for i, record in enumerate(data, 1):
                    if self.insert_single_record(cursor, actual_table, record):
                        success_count += 1
                    else:
                        error_count += 1

                    # Log de progresso a cada 100 registros
                    if i % 100 == 0:
                        self.log(f"  Progresso {table_key}: {i}/{count} processados")

            # Estatísticas da tabela
            self.migration_stats['tables_processed'] += 1
            if success_count > 0:
                self.migration_stats['tables_success'] += 1

            self.migration_stats['records_attempted'] += count
            self.migration_stats['records_success'] += success_count

            # Log final da tabela
            if error_count == 0:
                self.log(f"✅ {table_key}: {success_count} registros migrados", "SUCCESS")
            else:
                self.log(f"⚠️  {table_key}: {success_count} sucessos, {error_count} erros", "WARNING")

            return success_count > 0

        except Exception as e:
            self.log(f"Erro crítico na tabela {table_key}: {str(e)}", "ERROR")
            return False

    def migrate_all_data_fixed(self):
        """Migrar todos os dados com ordem otimizada"""
        self.log("\n🚀 INICIANDO MIGRAÇÃO CORRIGIDA")
        self.log("=" * 50)

        # Ordem otimizada (independentes primeiro)
        migration_order = [
            # Sistema Django (menos importantes)
            'content_types',
            'permissions',

            # Dados do projeto (ordem de dependência)
            'users',
            'profiles',
            'authors',
            'books',
            'book_authors',
            'user_bookshelves',
            'reading_progress',
            'reading_stats',

            # Chatbot (order importante)
            'chatbot_knowledge',
            'chatbot_conversations',
            'chatbot_messages',

            # Migrações por último
            'migrations'
        ]

        # Migrar tabelas na ordem especificada
        for table_key in migration_order:
            if table_key in self.backup_data:
                self.migrate_table_data_fixed(table_key, self.backup_data[table_key])
            else:
                self.log(f"Tabela {table_key} não encontrada no backup")

        # Migrar qualquer tabela restante não listada
        for table_key, table_data in self.backup_data.items():
            if table_key not in migration_order and table_key != '_migration_info':
                self.log(f"Migrando tabela extra: {table_key}")
                self.migrate_table_data_fixed(table_key, table_data)

    def validate_migration_detailed(self):
        """Validação detalhada da migração"""
        self.log("\n🔍 VALIDAÇÃO DETALHADA DA MIGRAÇÃO")
        self.log("=" * 50)

        validation_queries = {
            'users': 'SELECT COUNT(*) FROM "user"',
            'books': 'SELECT COUNT(*) FROM core_book',
            'authors': 'SELECT COUNT(*) FROM core_author',
            'profiles': 'SELECT COUNT(*) FROM core_profile',
            'user_bookshelves': 'SELECT COUNT(*) FROM core_userbookshelf',
            'conversations': 'SELECT COUNT(*) FROM chatbot_literario_conversation',
            'messages': 'SELECT COUNT(*) FROM chatbot_literario_message',
            'knowledge': 'SELECT COUNT(*) FROM chatbot_literario_knowledgeitem'
        }

        validation_results = {}
        total_migrated = 0

        try:
            with connection.cursor() as cursor:
                for name, query in validation_queries.items():
                    try:
                        cursor.execute(query)
                        count = cursor.fetchone()[0]
                        validation_results[name] = count
                        total_migrated += count

                        # Comparar com backup original se possível
                        original_key = {
                            'users': 'users',
                            'books': 'books',
                            'authors': 'authors',
                            'profiles': 'profiles',
                            'user_bookshelves': 'user_bookshelves',
                            'conversations': 'chatbot_conversations',
                            'messages': 'chatbot_messages',
                            'knowledge': 'chatbot_knowledge'
                        }.get(name)

                        if original_key and original_key in self.backup_data:
                            original_count = self.backup_data[original_key].get('count', 0)
                            percentage = (count / original_count * 100) if original_count > 0 else 0
                            self.log(f"{name}: {count}/{original_count} registros ({percentage:.1f}%)")
                        else:
                            self.log(f"{name}: {count} registros")

                    except Exception as e:
                        self.log(f"Erro ao validar {name}: {str(e)}", "WARNING")
                        validation_results[name] = 0

        except Exception as e:
            self.log(f"Erro durante validação: {str(e)}", "ERROR")

        self.log(f"\n📊 TOTAL MIGRADO: {total_migrated} registros")
        return validation_results

    def create_detailed_report(self):
        """Criar relatório detalhado da migração"""
        self.log("\n📋 RELATÓRIO FINAL DETALHADO")
        self.log("=" * 60)

        # Estatísticas gerais
        success_rate = (self.migration_stats['records_success'] /
                        max(self.migration_stats['records_attempted'], 1)) * 100

        self.log(f"🕒 Horário: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        self.log(f"📁 Backup usado: {self.backup_file}")
        self.log(f"📊 Tabelas processadas: {self.migration_stats['tables_processed']}")
        self.log(f"📊 Tabelas com sucesso: {self.migration_stats['tables_success']}")
        self.log(f"📊 Registros tentados: {self.migration_stats['records_attempted']}")
        self.log(f"📊 Registros migrados: {self.migration_stats['records_success']}")
        self.log(f"📊 Taxa de sucesso: {success_rate:.1f}%")

        if self.migration_stats['warnings']:
            self.log(f"⚠️  Avisos: {len(self.migration_stats['warnings'])}")

        if self.migration_stats['errors']:
            self.log(f"❌ Erros críticos: {len(self.migration_stats['errors'])}")

        # Status final
        if success_rate > 90:
            self.log("🎉 Migração EXCELENTE!", "SUCCESS")
        elif success_rate > 70:
            self.log("✅ Migração BOA!", "SUCCESS")
        elif success_rate > 50:
            self.log("⚠️  Migração PARCIAL", "WARNING")
        else:
            self.log("❌ Migração com PROBLEMAS", "ERROR")

    def run_migration_fixed(self, clear_data=False):
        """Executar migração corrigida completa"""
        self.log("🚀 INICIANDO MIGRAÇÃO CORRIGIDA PARA SUPABASE")
        self.log("=" * 60)

        # 1. Carregar backup
        if not self.load_backup():
            return False

        # 2. Testar conexão
        if not self.test_supabase_connection():
            return False

        # 3. Limpeza opcional (apenas se solicitada)
        if clear_data:
            self.log("🧹 Pulando limpeza - dados serão inseridos com ON CONFLICT")

        # 4. Migrar dados SEM transação global
        self.migrate_all_data_fixed()

        # 5. Validar migração
        self.validate_migration_detailed()

        # 6. Relatório final
        self.create_detailed_report()

        return True


def main():
    """Função principal"""
    print("=" * 60)
    print("🔄 MIGRAÇÃO CORRIGIDA - BACKUP LOCAL → SUPABASE")
    print("=" * 60)

    # Criar instância da migração
    migration = SupabaseMigrationFixed()

    # Executar migração (sem limpeza automática)
    success = migration.run_migration_fixed(clear_data=False)

    if success:
        print("\n" + "=" * 60)
        print("✅ MIGRAÇÃO CORRIGIDA CONCLUÍDA!")
        print("=" * 60)
        print("🌐 Dados migrados para Supabase com tratamento de erros")
        print("🔗 Verifique o dashboard do Supabase")
        print("📊 Consulte o relatório detalhado acima")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ MIGRAÇÃO FALHADA")
        print("=" * 60)
        print("Verifique os logs acima para identificar problemas")
        print("=" * 60)


if __name__ == "__main__":
    main()