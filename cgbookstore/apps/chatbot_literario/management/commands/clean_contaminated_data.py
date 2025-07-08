from django.core.management.base import BaseCommand
from cgbookstore.apps.chatbot_literario.models import KnowledgeItem
from cgbookstore.apps.chatbot_literario.services.training_service import training_service
from django.db import transaction
import re


class Command(BaseCommand):
    help = 'Remove dados contaminados específicos identificados na investigação SQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria removido, sem remover'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Remove sem confirmação'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        self.stdout.write("=" * 60)
        self.stdout.write("🧹 LIMPEZA DE DADOS CONTAMINADOS - BASEADA EM INVESTIGAÇÃO SQL")
        self.stdout.write("=" * 60)

        # DADOS REAIS DA INVESTIGAÇÃO (Query #7)
        contaminated_patterns = [
            {
                'name': 'Solo Leveling (22 registros identificados)',
                'question_patterns': [
                    r'.*Solo Leveling.*',
                    r'.*Jinwoo.*',
                    r'.*solo leveling.*'
                ],
                'answer_patterns': [
                    r'.*Solo Leveling.*',
                    r'.*Jinwoo Sung.*',
                    r'.*Shadow Monarch.*',
                    r'.*Weakest Hunter.*',
                    r'.*E-class hunter.*'
                ]
            },
            {
                'name': 'Christopher Paolini - Ciclo Herança (6 registros identificados)',
                'question_patterns': [
                    r'.*Christopher.*',
                    r'.*Paolini.*'
                ],
                'answer_patterns': [
                    r'.*Christopher Paolini.*',
                    r'.*Herança.*',
                    r'.*Eragon.*',
                    r'.*Brisingr.*',
                    r'.*Eldest.*',
                    r'.*Ciclo.*Herança.*',
                    r'.*Alagaësia.*',
                    r'.*Cavaleiro.*Dragão.*'
                ]
            },
            {
                'name': 'Percy Jackson (1 registro identificado)',
                'question_patterns': [
                    r'.*Percy Jackson.*',
                    r'.*mar de monstros.*'
                ],
                'answer_patterns': [
                    r'.*Percy Jackson.*',
                    r'.*olimpianos.*',
                    r'.*Meio-Sangue.*',
                    r'.*Poseidon.*'
                ]
            },
            {
                'name': 'Dragonlance (registros identificados)',
                'question_patterns': [
                    r'.*Dragonlance.*'
                ],
                'answer_patterns': [
                    r'.*Dragonlance.*',
                    r'.*Companheiros da Lança.*',
                    r'.*Guerra da Lança.*',
                    r'.*Krynn.*'
                ]
            }
        ]

        # IDs ESPECÍFICOS DA INVESTIGAÇÃO (Query #7)
        specific_contaminated_ids = [
            # Solo Leveling (22 registros)
            286, 284, 283, 281, 279, 278, 276, 275, 273, 272, 270, 269,
            267, 266, 264, 263, 261, 260, 258, 257, 251, 250,
            # Christopher Paolini (6 registros)
            320, 319, 147, 146, 144, 143, 79,
            # Percy Jackson (1 registro)
            191
        ]

        total_removed = 0
        items_to_remove = []

        # Análise da base atual
        self.stdout.write(f"\n📋 Analisando base de conhecimento...")
        all_items = KnowledgeItem.objects.filter(active=True)
        self.stdout.write(f"   📊 Total de itens ativos: {all_items.count()}")

        # MÉTODO 1: Verificar por IDs específicos (mais preciso)
        self.stdout.write(f"\n🎯 Verificando IDs específicos identificados na investigação...")
        specific_items = all_items.filter(id__in=specific_contaminated_ids)
        for item in specific_items:
            if item not in items_to_remove:
                items_to_remove.append(item)

        self.stdout.write(f"   ⚠️  Encontrados {len(specific_items)} itens por ID específico")

        # MÉTODO 2: Verificar por patterns (captura qualquer novo)
        for pattern_group in contaminated_patterns:
            self.stdout.write(f"\n🔍 Verificando: {pattern_group['name']}")
            group_items = []

            # Verificar padrões na pergunta
            for question_pattern in pattern_group['question_patterns']:
                items = all_items.filter(question__iregex=question_pattern)
                for item in items:
                    if item not in group_items:
                        group_items.append(item)

            # Verificar padrões na resposta
            for answer_pattern in pattern_group['answer_patterns']:
                items = all_items.filter(answer__iregex=answer_pattern)
                for item in items:
                    if item not in group_items:
                        group_items.append(item)

            if group_items:
                self.stdout.write(f"   ⚠️  Encontrados {len(group_items)} itens por pattern:")
                for item in group_items:
                    if item not in items_to_remove:
                        items_to_remove.append(item)
                        self.stdout.write(f"      - ID {item.id}: {item.question[:50]}...")
            else:
                self.stdout.write(f"   ✅ Nenhum item adicional encontrado por pattern")

        # MÉTODO 3: Verificação por conteúdo específico problemático
        self.stdout.write(f"\n🎯 Verificação adicional por conteúdo específico...")

        specific_bad_content = [
            # Solo Leveling específico
            "Shadow Monarch", "Jinwoo Sung", "E-class hunter", "Weakest Hunter",
            # Christopher Paolini específico
            "Christopher Paolini", "Ciclo da Herança", "Alagaësia", "Cavaleiro de Dragão",
            # Outros contaminados
            "Companheiros da Lança", "Guerra da Lança"
        ]

        for bad_content in specific_bad_content:
            items = all_items.filter(answer__icontains=bad_content)
            for item in items:
                if item not in items_to_remove:
                    items_to_remove.append(item)
                    self.stdout.write(f"   ⚠️  Conteúdo específico: ID {item.id} - {bad_content}")

        # Resumo da análise
        self.stdout.write(f"\n" + "=" * 60)
        self.stdout.write(f"📊 RESUMO DA ANÁLISE")
        self.stdout.write(f"=" * 60)
        self.stdout.write(f"   📋 Total de itens analisados: {all_items.count()}")
        self.stdout.write(f"   ⚠️  Itens contaminados encontrados: {len(items_to_remove)}")
        self.stdout.write(f"   ✅ Itens que permanecerão: {all_items.count() - len(items_to_remove)}")

        if not items_to_remove:
            self.stdout.write(f"\n🎉 Nenhum item contaminado encontrado! Base está limpa.")
            return

        # Mostrar detalhes dos primeiros itens contaminados
        self.stdout.write(f"\n📋 Primeiros 10 itens contaminados encontrados:")
        for item in items_to_remove[:10]:
            self.stdout.write(f"   🗑️  ID {item.id}:")
            self.stdout.write(f"      P: {item.question[:60]}")
            self.stdout.write(f"      R: {item.answer[:80]}...")

        if len(items_to_remove) > 10:
            self.stdout.write(f"   ... e mais {len(items_to_remove) - 10} itens")

        # Executar remoção
        if dry_run:
            self.stdout.write(f"\n🔍 DRY-RUN: Nenhum item foi removido.")
            self.stdout.write(f"   Para executar a limpeza: python manage.py clean_contaminated_data")
        else:
            # Confirmação de segurança
            if not force:
                self.stdout.write(
                    f"\n⚠️  ATENÇÃO: Esta operação irá remover {len(items_to_remove)} itens permanentemente!")
                self.stdout.write(f"   Itens identificados na investigação SQL como contaminados")
                response = input("Deseja continuar? (digite 'SIM' para confirmar): ")
                if response != 'SIM':
                    self.stdout.write("❌ Operação cancelada.")
                    return

            # Executar limpeza
            self.stdout.write(f"\n🧹 Iniciando limpeza de dados contaminados...")

            with transaction.atomic():
                removed_count = 0
                for item in items_to_remove:
                    try:
                        item_id = item.id
                        question = item.question[:50]
                        item.delete()
                        removed_count += 1
                        if removed_count <= 5:
                            self.stdout.write(f"   ✅ Removido: ID {item_id} - {question}...")
                    except Exception as e:
                        self.stdout.write(f"   ❌ Erro ao remover ID {item.id}: {e}")

                if removed_count > 5:
                    self.stdout.write(f"   ... e mais {removed_count - 5} itens removidos")

            self.stdout.write(f"\n🎉 Limpeza concluída!")
            self.stdout.write(f"   ✅ {removed_count} itens contaminados removidos")
            self.stdout.write(f"   📊 Base limpa com {all_items.count() - removed_count} itens de qualidade")

            # Atualizar embeddings após limpeza
            self.stdout.write(f"\n🔄 Atualizando embeddings...")
            try:
                training_service.initialized = False
                training_service.initialize()
                self.stdout.write(f"   ✅ Embeddings atualizados com sucesso")
            except Exception as e:
                self.stdout.write(f"   ⚠️  Erro ao atualizar embeddings: {e}")

        # Próximos passos
        self.stdout.write(f"\n" + "=" * 60)
        self.stdout.write(f"🎯 PRÓXIMOS PASSOS")
        self.stdout.write(f"=" * 60)

        if not dry_run and removed_count > 0:
            self.stdout.write(f"\n1. 🔄 Reinicie o servidor:")
            self.stdout.write(f"   python manage.py runserver")

            self.stdout.write(f"\n2. 📊 Execute normalização de categorias:")
            self.stdout.write(f"   python manage.py normalize_categories --dry-run")

            self.stdout.write(f"\n3. 🧪 Teste o chatbot:")
            self.stdout.write(f"   Teste: 'Quem escreveu O Hobbit?' (deve responder Tolkien)")
        else:
            self.stdout.write(f"\n🔍 Para executar a limpeza:")
            self.stdout.write(f"   python manage.py clean_contaminated_data")

        self.stdout.write(f"\n🏁 COMANDO CONCLUÍDO - BASE PRONTA PARA NORMALIZAÇÃO DE CATEGORIAS")