from django.core.management.base import BaseCommand
from cgbookstore.apps.chatbot_literario.models import KnowledgeItem
from cgbookstore.apps.chatbot_literario.services import training_service
from django.db import transaction
from collections import defaultdict


class Command(BaseCommand):
    help = 'Normaliza categorias inconsistentes baseado na investigação SQL (22→6 categorias)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria normalizado, sem alterar'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Normaliza sem confirmação'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        self.stdout.write("=" * 60)
        self.stdout.write("🔧 NORMALIZAÇÃO DE CATEGORIAS - BASEADA EM INVESTIGAÇÃO SQL")
        self.stdout.write("=" * 60)

        # MAPEAMENTO BASEADO NA INVESTIGAÇÃO (Query #6 e #10)
        # Padrão original de maio 2025 (antes da degradação)
        CATEGORY_MAPPING = {
            # LIVROS (consolidar em 'livros' - padrão maio 2025)
            'livros': 'livros',  # 192 registros (mantém)
            'Livros': 'livros',  # 10 registros
            'Literatura': 'livros',  # 6 registros
            'Literatura Brasileira': 'livros',  # 2 registros
            'faq_literatura': 'livros',  # 5 registros
            'Datas': 'livros',  # 2 registros
            'conversas': 'livros',  # 1 registro
            '': 'livros',  # 1 registro vazio

            # AUTORES (consolidar em 'autores' - padrão maio 2025)
            'autores': 'autores',  # 13 registros (mantém)
            'Autores': 'autores',  # 2 registros
            'Autores Brasileiros': 'autores',  # 1 registro

            # AJUDA (consolidar em 'ajuda' - padrão maio 2025)
            'ajuda': 'ajuda',  # 5 registros (mantém)
            'Ajuda': 'ajuda',  # 2 registros
            'generos_literarios': 'ajuda',  # 5 registros
            'Suporte': 'ajuda',  # 2 registros

            # NAVEGAÇÃO (consolidar em 'navegacao' - padrão maio 2025)
            'navegacao': 'navegacao',  # 9 registros (mantém)
            'Navegação': 'navegacao',  # 2 registros
            'Perfil': 'navegacao',  # 3 registros
            'Conta': 'navegacao',  # 2 registros
            'Busca': 'navegacao',  # 1 registro

            # RECOMENDAÇÕES (consolidar em 'recomendacao' - padrão maio 2025)
            'recomendacao': 'recomendacao',  # 3 registros (mantém)
            'Recomendações': 'recomendacao',  # 6 registros
        }

        # Análise da base atual
        self.stdout.write(f"\n📋 Analisando categorias atuais...")
        all_items = KnowledgeItem.objects.filter(active=True)
        self.stdout.write(f"   📊 Total de itens ativos: {all_items.count()}")

        # Contar categorias atuais
        current_categories = defaultdict(int)
        for item in all_items:
            current_categories[item.category or ''] += 1

        self.stdout.write(f"\n📊 Categorias atuais encontradas ({len(current_categories)}):")
        for category, count in sorted(current_categories.items(), key=lambda x: x[1], reverse=True):
            display_cat = f"'{category}'" if category else "'(vazio)'"
            self.stdout.write(f"   📚 {display_cat}: {count} itens")

        # Planejar normalizações
        normalization_plan = {}
        items_to_update = []

        for old_category, new_category in CATEGORY_MAPPING.items():
            if old_category != new_category:  # Só se houver mudança
                items = all_items.filter(category=old_category)
                if items.exists():
                    normalization_plan[old_category] = {
                        'new_category': new_category,
                        'count': items.count(),
                        'items': list(items)
                    }
                    items_to_update.extend(items)

        # Mostrar plano de normalização
        self.stdout.write(f"\n🔧 PLANO DE NORMALIZAÇÃO:")
        self.stdout.write("-" * 40)

        if not normalization_plan:
            self.stdout.write(f"   ✅ Todas as categorias já estão normalizadas!")
            return

        total_to_update = len(items_to_update)
        for old_cat, plan in normalization_plan.items():
            display_old = f"'{old_cat}'" if old_cat else "'(vazio)'"
            self.stdout.write(f"   {display_old} → '{plan['new_category']}' ({plan['count']} itens)")

        # Mostrar resultado final esperado
        self.stdout.write(f"\n📊 RESULTADO FINAL ESPERADO:")
        final_categories = defaultdict(int)

        # Contar categorias que não mudam
        for item in all_items:
            current_cat = item.category or ''
            if current_cat in CATEGORY_MAPPING:
                final_cat = CATEGORY_MAPPING[current_cat]
            else:
                final_cat = current_cat  # Mantém se não está no mapeamento
            final_categories[final_cat] += 1

        for category, count in sorted(final_categories.items(), key=lambda x: x[1], reverse=True):
            self.stdout.write(f"   📚 '{category}': {count} itens")

        # Mostrar exemplos de itens que serão alterados
        self.stdout.write(f"\n📋 Exemplos de itens que serão normalizados:")
        examples_shown = 0
        for old_cat, plan in list(normalization_plan.items())[:3]:  # Primeiras 3 categorias
            self.stdout.write(f"\n   🔧 {old_cat} → {plan['new_category']}:")
            for item in plan['items'][:2]:  # 2 exemplos por categoria
                self.stdout.write(f"      - ID {item.id}: {item.question[:50]}...")
                examples_shown += 1
                if examples_shown >= 6:  # Limite de exemplos
                    break
            if examples_shown >= 6:
                break

        # Executar normalização
        if dry_run:
            self.stdout.write(f"\n🔍 DRY-RUN: {total_to_update} itens seriam normalizados")
            self.stdout.write(f"   Para executar: python manage.py normalize_categories")
        else:
            # Confirmação de segurança
            if not force:
                self.stdout.write(f"\n⚠️  ATENÇÃO: Esta operação irá alterar {total_to_update} itens!")
                self.stdout.write(f"   Normalizando 22 categorias → 6 categorias padronizadas")
                response = input("Deseja continuar? (digite 'SIM' para confirmar): ")
                if response != 'SIM':
                    self.stdout.write("❌ Operação cancelada.")
                    return

            # Executar normalização
            self.stdout.write(f"\n🔧 Iniciando normalização de categorias...")

            with transaction.atomic():
                updated_count = 0
                for old_cat, plan in normalization_plan.items():
                    try:
                        # Atualizar todos os itens desta categoria
                        items_updated = KnowledgeItem.objects.filter(
                            category=old_cat,
                            active=True
                        ).update(category=plan['new_category'])

                        updated_count += items_updated
                        self.stdout.write(f"   ✅ {old_cat} → {plan['new_category']}: {items_updated} itens")

                    except Exception as e:
                        self.stdout.write(f"   ❌ Erro ao normalizar '{old_cat}': {e}")

            self.stdout.write(f"\n🎉 Normalização concluída!")
            self.stdout.write(f"   ✅ {updated_count} itens normalizados")
            self.stdout.write(f"   📊 Base com categorias padronizadas (6 categorias)")

            # Verificar resultado final
            final_categories_actual = defaultdict(int)
            for item in KnowledgeItem.objects.filter(active=True):
                final_categories_actual[item.category or ''] += 1

            self.stdout.write(f"\n📊 Verificação - Categorias finais:")
            for category, count in sorted(final_categories_actual.items(), key=lambda x: x[1], reverse=True):
                self.stdout.write(f"   📚 '{category}': {count} itens")

            # Atualizar embeddings
            self.stdout.write(f"\n🔄 Atualizando embeddings...")
            try:
                # Reinicializar serviço
                training_service.initialized = False
                if hasattr(training_service, 'initialize'):
                    training_service.initialize()
                    self.stdout.write(f"   ✅ Embeddings atualizados")
                else:
                    self.stdout.write(f"   ⚠️  Reinicie o servidor para atualizar embeddings")
            except Exception as e:
                self.stdout.write(f"   ⚠️  Erro embeddings: {e}")

        # Próximos passos
        self.stdout.write(f"\n" + "=" * 60)
        self.stdout.write(f"🎯 PRÓXIMOS PASSOS")
        self.stdout.write(f"=" * 60)

        if not dry_run and total_to_update > 0:
            self.stdout.write(f"\n1. 🔄 Reinicie o servidor:")
            self.stdout.write(f"   python manage.py runserver")

            self.stdout.write(f"\n2. 🧪 Teste o chatbot:")
            self.stdout.write(f"   'Quem escreveu O Hobbit?' → deve responder Tolkien")
            self.stdout.write(f"   'Quais outros livros da autora?' → manter contexto")

            self.stdout.write(f"\n3. 📊 Otimizar functional_chatbot.py:")
            self.stdout.write(f"   Próxima fase: melhorar algoritmo de contexto")
        else:
            self.stdout.write(f"\n🔍 Para executar a normalização:")
            self.stdout.write(f"   python manage.py normalize_categories")

        self.stdout.write(f"\n🏁 NORMALIZAÇÃO DE CATEGORIAS CONCLUÍDA")
        self.stdout.write(f"   ✅ Base pronta para otimização do functional_chatbot.py")