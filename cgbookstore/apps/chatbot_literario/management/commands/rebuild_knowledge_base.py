from django.core.management.base import BaseCommand
from cgbookstore.apps.chatbot_literario.models import KnowledgeItem
from cgbookstore.apps.chatbot_literario.services.training_service import training_service
from django.db import transaction
import json


class Command(BaseCommand):
    help = 'Reconstrói a base de conhecimento com dados limpos e organizados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria adicionado, sem adicionar'
        )
        parser.add_argument(
            '--clear-first',
            action='store_true',
            help='Limpa a base antes de adicionar novos dados'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clear_first = options['clear_first']

        self.stdout.write("=" * 60)
        self.stdout.write("🏗️ RECONSTRUÇÃO DA BASE DE CONHECIMENTO")
        self.stdout.write("=" * 60)

        # Verificar estado atual
        current_count = KnowledgeItem.objects.filter(active=True).count()
        self.stdout.write(f"\n📊 Estado atual: {current_count} itens ativos na base")

        if clear_first and current_count > 0:
            if not dry_run:
                self.stdout.write(f"\n🧹 Limpando base atual...")
                KnowledgeItem.objects.filter(active=True).delete()
                self.stdout.write(f"   ✅ {current_count} itens removidos")
            else:
                self.stdout.write(f"\n🔍 DRY-RUN: {current_count} itens seriam removidos")

        # Base de conhecimento estruturada
        knowledge_base = self._get_structured_knowledge()

        self.stdout.write(f"\n📋 Preparando para adicionar {len(knowledge_base)} itens...")

        if dry_run:
            self._show_preview(knowledge_base)
        else:
            self._populate_database(knowledge_base)

        self.stdout.write(f"\n" + "=" * 60)
        self.stdout.write(f"🏁 RECONSTRUÇÃO CONCLUÍDA")
        self.stdout.write(f"=" * 60)

    def _get_structured_knowledge(self):
        """Retorna a base de conhecimento estruturada e limpa."""

        knowledge_base = []

        # ===== SEÇÃO 1: LITERATURA CLÁSSICA E POPULAR =====
        literature_data = [
            # Harry Potter
            {
                "question": "Quem escreveu Harry Potter?",
                "answer": "Harry Potter foi escrito por J.K. Rowling.",
                "category": "Literatura",
                "source": "conhecimento_geral"
            },
            {
                "question": "Quem é J.K. Rowling?",
                "answer": "J.K. Rowling é uma escritora britânica, autora da famosa série Harry Potter. Seu nome completo é Joanne Rowling.",
                "category": "Autores",
                "source": "conhecimento_geral"
            },
            {
                "question": "Quais livros J.K. Rowling escreveu?",
                "answer": "J.K. Rowling escreveu a série Harry Potter (7 livros), Os Contos de Beedle, o Bardo, Animais Fantásticos e Onde Habitam, e a série Cormoran Strike (sob pseudônimo Robert Galbraith).",
                "category": "Literatura",
                "source": "conhecimento_geral"
            },
            {
                "question": "Qual foi o primeiro livro de Harry Potter?",
                "answer": "O primeiro livro foi 'Harry Potter e a Pedra Filosofal' (ou 'Pedra do Feiticeiro' nos EUA), publicado em 1997.",
                "category": "Literatura",
                "source": "conhecimento_geral"
            },

            # J.R.R. Tolkien
            {
                "question": "Quem escreveu O Senhor dos Anéis?",
                "answer": "O Senhor dos Anéis foi escrito por J.R.R. Tolkien.",
                "category": "Literatura",
                "source": "conhecimento_geral"
            },
            {
                "question": "Quem escreveu O Hobbit?",
                "answer": "O Hobbit foi escrito por J.R.R. Tolkien.",
                "category": "Literatura",
                "source": "conhecimento_geral"
            },
            {
                "question": "Quem é J.R.R. Tolkien?",
                "answer": "J.R.R. Tolkien foi um escritor britânico, professor e filólogo, famoso por criar a Terra-média e escrever O Hobbit e O Senhor dos Anéis.",
                "category": "Autores",
                "source": "conhecimento_geral"
            },
            {
                "question": "Quais livros Tolkien escreveu?",
                "answer": "Tolkien escreveu O Hobbit, a trilogia O Senhor dos Anéis, O Silmarillion, Contos Inacabados, e muitas outras obras sobre a Terra-média.",
                "category": "Literatura",
                "source": "conhecimento_geral"
            },

            # Literatura Brasileira
            {
                "question": "Quem escreveu Dom Casmurro?",
                "answer": "Dom Casmurro foi escrito por Machado de Assis.",
                "category": "Literatura Brasileira",
                "source": "conhecimento_geral"
            },
            {
                "question": "Quem é Machado de Assis?",
                "answer": "Machado de Assis foi um escritor brasileiro, considerado um dos maiores nomes da literatura brasileira. Escreveu Dom Casmurro, O Cortiço, e muitas outras obras clássicas.",
                "category": "Autores Brasileiros",
                "source": "conhecimento_geral"
            },
            {
                "question": "Quais livros Machado de Assis escreveu?",
                "answer": "Machado de Assis escreveu Dom Casmurro, O Cortiço, Memórias Póstumas de Brás Cubas, Quincas Borba, Helena, A Mão e a Luva, entre outros.",
                "category": "Literatura Brasileira",
                "source": "conhecimento_geral"
            },

            # Outros Clássicos
            {
                "question": "Quem escreveu 1984?",
                "answer": "1984 foi escrito por George Orwell.",
                "category": "Literatura",
                "source": "conhecimento_geral"
            },
            {
                "question": "Quem escreveu Os Miseráveis?",
                "answer": "Os Miseráveis foi escrito por Victor Hugo.",
                "category": "Literatura",
                "source": "conhecimento_geral"
            },
        ]

        # ===== SEÇÃO 2: NAVEGAÇÃO DO SITE =====
        navigation_data = [
            {
                "question": "Como encontrar livros no site?",
                "answer": "Você pode encontrar livros usando a barra de pesquisa no topo da página, navegando pelas categorias, ou visitando a seção 'Catálogo' no menu principal.",
                "category": "Navegação",
                "source": "site_features"
            },
            {
                "question": "Como funciona a pesquisa de livros?",
                "answer": "A pesquisa permite buscar por título, autor, gênero ou palavras-chave. Use a barra de pesquisa e os filtros para refinar seus resultados.",
                "category": "Navegação",
                "source": "site_features"
            },
            {
                "question": "Onde encontro as recomendações?",
                "answer": "As recomendações personalizadas estão disponíveis na página inicial, na seção 'Recomendado para Você', e também na sua página de perfil.",
                "category": "Recomendações",
                "source": "site_features"
            },
            {
                "question": "Como organizar minha estante?",
                "answer": "Acesse sua página de perfil e use as abas 'Lendo', 'Quero Ler', 'Lidos' e 'Favoritos' para organizar seus livros. Você pode adicionar livros clicando no ícone da estante em cada livro.",
                "category": "Perfil",
                "source": "site_features"
            },
            {
                "question": "Como criar uma conta?",
                "answer": "Clique em 'Cadastrar' no menu superior, preencha seus dados (nome, email, senha) e confirme seu cadastro. Você também pode fazer login com redes sociais.",
                "category": "Conta",
                "source": "site_features"
            },
            {
                "question": "Como editar meu perfil?",
                "answer": "Acesse sua página de perfil clicando no seu nome no menu superior, depois clique em 'Editar Perfil' para alterar suas informações e preferências.",
                "category": "Perfil",
                "source": "site_features"
            },
            {
                "question": "Onde vejo meu histórico de leitura?",
                "answer": "Seu histórico de leitura está na sua página de perfil, na aba 'Lidos', onde você pode ver todos os livros que marcou como lidos.",
                "category": "Perfil",
                "source": "site_features"
            },
        ]

        # ===== SEÇÃO 3: FUNCIONALIDADES DO CHATBOT =====
        chatbot_data = [
            {
                "question": "O que você pode fazer?",
                "answer": "Posso ajudar com informações sobre livros e autores, orientar sobre como usar o site, dar recomendações de leitura e responder dúvidas sobre navegação e funcionalidades.",
                "category": "Ajuda",
                "source": "chatbot_features"
            },
            {
                "question": "Como você funciona?",
                "answer": "Sou um assistente literário que usa inteligência artificial para entender suas perguntas e fornecer respostas relevantes sobre livros, autores e o funcionamento do site.",
                "category": "Ajuda",
                "source": "chatbot_features"
            },
            {
                "question": "Pode recomendar livros?",
                "answer": "Sim! Posso recomendar livros baseados em seus gostos. Me diga que gêneros você gosta, autores favoritos, ou que tipo de história está procurando.",
                "category": "Recomendações",
                "source": "chatbot_features"
            },
            {
                "question": "Como fazer uma pergunta?",
                "answer": "É simples! Apenas digite sua pergunta naturalmente. Posso entender perguntas sobre livros específicos, autores, gêneros, ou como usar o site.",
                "category": "Ajuda",
                "source": "chatbot_features"
            },
        ]

        # ===== SEÇÃO 4: RECOMENDAÇÕES POR GÊNERO =====
        recommendations_data = [
            {
                "question": "Recomende livros de fantasia",
                "answer": "Ótimas opções de fantasia: O Senhor dos Anéis (Tolkien), Harry Potter (J.K. Rowling), As Crônicas de Nárnia (C.S. Lewis), A Roda do Tempo (Robert Jordan), e O Nome do Vento (Patrick Rothfuss).",
                "category": "Recomendações",
                "source": "genre_recommendations"
            },
            {
                "question": "Recomende livros de ficção científica",
                "answer": "Excelentes livros de ficção científica: Duna (Frank Herbert), 1984 (George Orwell), Fundação (Isaac Asimov), Neuromancer (William Gibson), e O Guia do Mochileiro das Galáxias (Douglas Adams).",
                "category": "Recomendações",
                "source": "genre_recommendations"
            },
            {
                "question": "Recomende livros de romance",
                "answer": "Romances imperdíveis: Orgulho e Preconceito (Jane Austen), Como Eu Era Antes de Você (Jojo Moyes), O Morro dos Ventos Uivantes (Emily Brontë), A Culpa é das Estrelas (John Green).",
                "category": "Recomendações",
                "source": "genre_recommendations"
            },
            {
                "question": "Recomende literatura brasileira",
                "answer": "Clássicos brasileiros: Dom Casmurro (Machado de Assis), Grande Sertão: Veredas (Guimarães Rosa), Capitães da Areia (Jorge Amado), O Cortiço (Aluísio Azevedo), e Cidade de Deus (Paulo Lins).",
                "category": "Recomendações",
                "source": "genre_recommendations"
            },
        ]

        # ===== SEÇÃO 5: AJUDA E SUPORTE =====
        help_data = [
            {
                "question": "Preciso de ajuda",
                "answer": "Estou aqui para ajudar! Posso responder sobre livros, autores, como usar o site, criar conta, organizar sua estante, ou qualquer dúvida sobre navegação. O que você gostaria de saber?",
                "category": "Ajuda",
                "source": "support"
            },
            {
                "question": "Como entrar em contato?",
                "answer": "Você pode usar este chat para tirar dúvidas imediatamente, ou acessar a página 'Contato' no menu para enviar uma mensagem mais detalhada para nossa equipe.",
                "category": "Suporte",
                "source": "support"
            },
            {
                "question": "Esqueci minha senha",
                "answer": "Na página de login, clique em 'Esqueci minha senha', digite seu email cadastrado e você receberá instruções para criar uma nova senha.",
                "category": "Conta",
                "source": "support"
            },
            {
                "question": "O site não está funcionando",
                "answer": "Tente atualizar a página ou limpar o cache do navegador. Se o problema persistir, entre em contato conosco através da página de contato com detalhes do erro.",
                "category": "Suporte",
                "source": "support"
            },
        ]

        # Combinar todas as seções
        knowledge_base.extend(literature_data)
        knowledge_base.extend(navigation_data)
        knowledge_base.extend(chatbot_data)
        knowledge_base.extend(recommendations_data)
        knowledge_base.extend(help_data)

        return knowledge_base

    def _show_preview(self, knowledge_base):
        """Mostra preview do que seria adicionado."""
        self.stdout.write(f"\n🔍 PREVIEW - DRY RUN")
        self.stdout.write("-" * 40)

        # Contar por categoria
        categories = {}
        for item in knowledge_base:
            cat = item['category']
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1

        self.stdout.write(f"\n📊 Itens por categoria:")
        for category, count in categories.items():
            self.stdout.write(f"   📚 {category}: {count} itens")

        self.stdout.write(f"\n📋 Primeiros 5 itens que seriam adicionados:")
        for i, item in enumerate(knowledge_base[:5], 1):
            self.stdout.write(f"\n   {i}. [{item['category']}]")
            self.stdout.write(f"      P: {item['question']}")
            self.stdout.write(f"      R: {item['answer'][:60]}...")

        if len(knowledge_base) > 5:
            self.stdout.write(f"   ... e mais {len(knowledge_base) - 5} itens")

    def _populate_database(self, knowledge_base):
        """Popula o banco com os dados da base de conhecimento."""
        self.stdout.write(f"\n🏗️ Adicionando itens à base de dados...")

        added_count = 0
        failed_count = 0

        with transaction.atomic():
            for i, item_data in enumerate(knowledge_base, 1):
                try:
                    # Verificar se já existe
                    existing = KnowledgeItem.objects.filter(
                        question=item_data['question'],
                        active=True
                    ).first()

                    if existing:
                        self.stdout.write(f"   ⚠️  Item {i} já existe: {item_data['question'][:40]}...")
                        continue

                    # Criar novo item
                    knowledge_item = KnowledgeItem.objects.create(
                        question=item_data['question'],
                        answer=item_data['answer'],
                        category=item_data['category'],
                        source=item_data['source'],
                        active=True
                    )

                    added_count += 1

                    if added_count <= 5:  # Mostrar apenas os primeiros 5
                        self.stdout.write(f"   ✅ Adicionado: {item_data['question'][:50]}...")

                except Exception as e:
                    failed_count += 1
                    self.stdout.write(f"   ❌ Erro item {i}: {e}")

        if added_count > 5:
            self.stdout.write(f"   ... e mais {added_count - 5} itens adicionados")

        self.stdout.write(f"\n📊 Resultado:")
        self.stdout.write(f"   ✅ {added_count} itens adicionados com sucesso")
        if failed_count > 0:
            self.stdout.write(f"   ❌ {failed_count} itens falharam")

        # Atualizar embeddings
        self.stdout.write(f"\n🔄 Atualizando embeddings...")
        try:
            # Reinicializar serviço de treinamento
            training_service.initialized = False
            training_service.initialize()
            self.stdout.write(f"   ✅ Embeddings atualizados com sucesso")
        except Exception as e:
            self.stdout.write(f"   ⚠️  Erro ao atualizar embeddings: {e}")
            self.stdout.write(f"   💡 Execute manualmente: python manage.py update_embeddings")

        # Status final
        final_count = KnowledgeItem.objects.filter(active=True).count()
        self.stdout.write(f"\n📊 Base de conhecimento atual: {final_count} itens ativos")

        # Instruções finais
        self.stdout.write(f"\n💡 Próximos passos:")
        self.stdout.write(f"   1. Reinicie o servidor: Ctrl+C, depois python manage.py runserver")
        self.stdout.write(f"   2. Teste o chatbot: python manage.py verify_chatbot_version --user-id 2")
        self.stdout.write(f"   3. Teste conversas contextuais com Harry Potter e J.K. Rowling")