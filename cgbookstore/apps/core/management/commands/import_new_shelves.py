# Arquivo: cgbookstore/apps/core/management/commands/import_new_shelves.py

import json
from django.core.management.base import BaseCommand
from cgbookstore.apps.core.models import HomeSection, HomeSectionBookItem, Book


class Command(BaseCommand):
    help = 'Importa os dados das prateleiras antigas do arquivo de backup para a nova estrutura unificada.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=================================================="))
        self.stdout.write(self.style.SUCCESS("🚀 Iniciando importação para a nova estrutura..."))
        self.stdout.write(self.style.SUCCESS("=================================================="))

        backup_file = 'old_shelves_backup.json'

        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.stdout.write(f"✅ Arquivo '{backup_file}' lido com sucesso. {len(data)} prateleiras para importar.")
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f"ERRO: Arquivo '{backup_file}' não encontrado! Execute a exportação primeiro."))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f"ERRO: Arquivo '{backup_file}' contém um JSON inválido."))
            return

        imported_count = 0
        skipped_count = 0

        for shelf_data in data:
            section_id = shelf_data.get('section_id')
            if not section_id:
                self.stdout.write(self.style.WARNING("  - Registro no backup sem 'section_id'. Pulando."))
                skipped_count += 1
                continue

            try:
                # Encontra a HomeSection correspondente
                section = HomeSection.objects.get(id=section_id)
                self.stdout.write(f"\nProcessing prateleira: '{section.titulo}' (ID: {section.id})")

                section.max_books = shelf_data.get('max_books', 12)

                # Configura prateleiras automáticas
                if shelf_data.get('automatic_filter_field'):
                    section.shelf_behavior = 'automatic'
                    section.shelf_filter_field = shelf_data['automatic_filter_field']
                    section.shelf_filter_value = shelf_data.get('automatic_filter_value', '')
                    self.stdout.write(
                        f"  -> Definida como AUTOMÁTICA. Filtro: {section.shelf_filter_field} = '{section.shelf_filter_value}'")

                # Configura prateleiras manuais
                elif shelf_data.get('manual_books'):
                    section.shelf_behavior = 'manual'
                    manual_books_ids = shelf_data['manual_books']
                    self.stdout.write(f"  -> Definida como MANUAL. Adicionando {len(manual_books_ids)} livros...")

                    # Limpa quaisquer itens antigos para garantir uma importação limpa
                    section.manual_books.clear()

                    # Adiciona os livros manuais com a ordem correta
                    for index, book_id in enumerate(manual_books_ids):
                        try:
                            HomeSectionBookItem.objects.create(
                                section=section,
                                book_id=book_id,
                                ordem=index
                            )
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(
                                f"    - AVISO: Não foi possível adicionar o livro com ID {book_id}. Erro: {e}"))
                    self.stdout.write("    -> Livros manuais adicionados.")

                else:
                    self.stdout.write("  -> Nenhuma configuração de livros encontrada (nem automática, nem manual).")

                section.save()
                imported_count += 1

            except HomeSection.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"  - AVISO: Seção com ID {section_id} não encontrada na nova base de dados. Pulando."))
                skipped_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  - ERRO CRÍTICO ao processar seção ID {section_id}: {e}"))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS("\n=================================================="))
        self.stdout.write(self.style.SUCCESS("✅ Importação concluída!"))
        self.stdout.write(f"   - {imported_count} prateleiras processadas com sucesso.")
        self.stdout.write(f"   - {skipped_count} prateleiras puladas devido a avisos ou erros.")
        self.stdout.write(self.style.SUCCESS("=================================================="))