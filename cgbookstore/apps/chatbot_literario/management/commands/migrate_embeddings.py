"""
Comando para migrar embeddings do chatbot para o novo formato.
Corrige incompatibilidades de dimensões entre modelos.
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction

from cgbookstore.apps.chatbot_literario.models import KnowledgeItem
from cgbookstore.apps.chatbot_literario.services.embeddings import embeddings_service
from cgbookstore.apps.chatbot_literario.services.functional_chatbot import chatbot_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migra embeddings do chatbot para corrigir incompatibilidades de dimensões'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força regeneração de todos os embeddings, mesmo os válidos'
        )

        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Número de items para processar por vez (padrão: 50)'
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a migração sem fazer alterações'
        )

        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Apenas verifica embeddings sem migrar'
        )

    def handle(self, *args, **options):
        force = options['force']
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        check_only = options['check_only']

        self.stdout.write(self.style.NOTICE('=== Migração de Embeddings do Chatbot ===\n'))

        # Informações do modelo
        model_info = embeddings_service.get_model_info()
        self.stdout.write(f"Modelo: {model_info['model_name']}")
        self.stdout.write(f"Dimensão esperada: {model_info['expected_dimension']}")
        self.stdout.write(f"Batch size: {batch_size}\n")

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Modo DRY RUN - Nenhuma alteração será feita\n'))

        if check_only:
            self._check_embeddings()
            return

        # Busca todos os items
        all_items = KnowledgeItem.objects.all()
        total_items = all_items.count()

        if total_items == 0:
            self.stdout.write(self.style.WARNING('Nenhum item de conhecimento encontrado.'))
            return

        self.stdout.write(f"Total de items: {total_items}")

        # Estatísticas
        stats = {
            'total': total_items,
            'valid': 0,
            'invalid': 0,
            'missing': 0,
            'migrated': 0,
            'failed': 0,
            'errors': []
        }

        # Primeira passagem: análise
        self.stdout.write(self.style.NOTICE('\n📊 Analisando embeddings...'))

        for item in all_items:
            if not item.embedding:
                stats['missing'] += 1
            else:
                is_valid, error = embeddings_service.validate_embedding(item.embedding)
                if is_valid:
                    stats['valid'] += 1
                else:
                    stats['invalid'] += 1
                    if len(stats['errors']) < 5:  # Mostra apenas primeiros 5 erros
                        stats['errors'].append(f"Item {item.id}: {error}")

        # Mostra análise
        self.stdout.write(f"\n✅ Válidos: {stats['valid']}")
        self.stdout.write(f"❌ Inválidos: {stats['invalid']}")
        self.stdout.write(f"❓ Sem embeddings: {stats['missing']}")

        if stats['errors']:
            self.stdout.write(self.style.ERROR('\nPrimeiros erros encontrados:'))
            for error in stats['errors']:
                self.stdout.write(f"  - {error}")

        # Verifica se precisa migrar
        items_to_migrate = stats['invalid'] + stats['missing']
        if not force and items_to_migrate == 0:
            self.stdout.write(self.style.SUCCESS('\n✨ Todos os embeddings estão válidos! Nada a fazer.'))
            return

        if force:
            items_to_migrate = total_items
            self.stdout.write(self.style.WARNING(f'\n⚠️  Modo FORCE: Todos os {total_items} items serão regenerados'))
        else:
            self.stdout.write(f'\n📝 {items_to_migrate} items precisam ser migrados')

        # Confirmação
        if not dry_run:
            confirm = input('\nDeseja continuar com a migração? (s/N): ')
            if confirm.lower() != 's':
                self.stdout.write(self.style.ERROR('Migração cancelada.'))
                return

        # Segunda passagem: migração
        self.stdout.write(self.style.NOTICE('\n🔄 Iniciando migração...'))

        processed = 0

        try:
            with transaction.atomic():
                for i in range(0, total_items, batch_size):
                    batch = all_items[i:i + batch_size]

                    for item in batch:
                        processed += 1

                        # Verifica se precisa migrar
                        if not force:
                            if item.embedding:
                                is_valid, _ = embeddings_service.validate_embedding(item.embedding)
                                if is_valid:
                                    continue

                        # Migra o item
                        if not dry_run:
                            try:
                                text_to_embed = f"{item.question} {item.answer}"
                                new_embedding = embeddings_service.create_embedding(text_to_embed)
                                item.embedding = new_embedding.tolist()
                                item.save(update_fields=['embedding', 'updated_at'])
                                stats['migrated'] += 1
                            except Exception as e:
                                stats['failed'] += 1
                                logger.error(f"Erro ao migrar item {item.id}: {str(e)}")
                        else:
                            stats['migrated'] += 1

                        # Mostra progresso
                        if processed % 10 == 0:
                            progress = (processed / total_items) * 100
                            self.stdout.write(
                                f"\rProgresso: {processed}/{total_items} ({progress:.1f}%)",
                                ending=''
                            )

                    # Pequena pausa entre batches para não sobrecarregar
                    if not dry_run and i + batch_size < total_items:
                        import time
                        time.sleep(0.5)

                # Se chegou aqui e não é dry-run, commit será feito automaticamente

        except KeyboardInterrupt:
            self.stdout.write(self.style.ERROR('\n\n⚠️  Migração interrompida pelo usuário!'))
            raise CommandError('Migração cancelada')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n\n❌ Erro durante migração: {str(e)}'))
            raise CommandError(f'Erro na migração: {str(e)}')

        # Resultado final
        self.stdout.write(self.style.SUCCESS('\n\n✅ Migração concluída!'))
        self.stdout.write(f"\n📊 Resumo:")
        self.stdout.write(f"  Total processado: {processed}")
        self.stdout.write(f"  Migrados: {stats['migrated']}")
        self.stdout.write(f"  Falhas: {stats['failed']}")

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\n🎉 Embeddings atualizados com sucesso!'))
            self.stdout.write('\n💡 Dica: Execute com --check-only para verificar o resultado')

    def _check_embeddings(self):
        """Verifica o estado atual dos embeddings."""
        self.stdout.write(self.style.NOTICE('🔍 Verificando embeddings...\n'))

        all_items = KnowledgeItem.objects.all()
        total = all_items.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('Nenhum item encontrado.'))
            return

        # Análise detalhada
        dimensions = {}
        valid_count = 0
        invalid_count = 0
        missing_count = 0

        for item in all_items:
            if not item.embedding:
                missing_count += 1
                continue

            is_valid, error = embeddings_service.validate_embedding(item.embedding)

            if is_valid:
                valid_count += 1
                # Conta dimensões
                dim = len(item.embedding) if isinstance(item.embedding, list) else item.embedding.shape[0]
                dimensions[dim] = dimensions.get(dim, 0) + 1
            else:
                invalid_count += 1
                self.stdout.write(f"Item {item.id}: {error}")

        # Mostra resultados
        self.stdout.write(f"\n📊 Análise de {total} items:")
        self.stdout.write(f"  ✅ Válidos: {valid_count} ({valid_count / total * 100:.1f}%)")
        self.stdout.write(f"  ❌ Inválidos: {invalid_count} ({invalid_count / total * 100:.1f}%)")
        self.stdout.write(f"  ❓ Sem embeddings: {missing_count} ({missing_count / total * 100:.1f}%)")

        if dimensions:
            self.stdout.write(f"\n📏 Distribuição de dimensões:")
            for dim, count in sorted(dimensions.items()):
                marker = "✅" if dim == embeddings_service.EXPECTED_DIMENSION else "⚠️"
                self.stdout.write(f"  {marker} {dim}D: {count} items")

        # Recomendações
        if invalid_count > 0 or missing_count > 0:
            self.stdout.write(self.style.WARNING(
                f'\n⚠️  Recomendação: Execute o comando sem --check-only para corrigir {invalid_count + missing_count} items'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('\n✨ Todos os embeddings estão válidos!'))