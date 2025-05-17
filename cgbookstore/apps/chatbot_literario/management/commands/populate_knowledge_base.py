import csv
import json
import os
from django.core.management.base import BaseCommand
from cgbookstore.apps.chatbot_literario.services.training_service import training_service
from cgbookstore.apps.core.models.book import Book
from cgbookstore.apps.core.models.author import Author


class Command(BaseCommand):
    help = 'Popula a base de conhecimento do chatbot com dados do sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            help='Caminho para arquivo CSV com dados adicionais',
        )
        parser.add_argument(
            '--json',
            type=str,
            help='Caminho para arquivo JSON com dados adicionais',
        )

    def handle(self, *args, **options):
        # Inicializa o serviço de treinamento
        if not training_service.initialized:
            training_service.initialize()

        # Popula com dados dos livros
        self._populate_from_books()

        # Popula com dados dos autores
        self._populate_from_authors()

        # Adiciona informações sobre navegação no site
        self._add_navigation_knowledge()

        # Adiciona conhecimento sobre gêneros literários
        self._add_literary_genres_knowledge()

        # Adiciona perguntas frequentes sobre literatura
        self._add_literary_faq()

        # Processa arquivos externos se fornecidos
        if options['csv']:
            self._process_csv(options['csv'])

        if options['json']:
            self._process_json(options['json'])

        # Remover chamada ao método save_data que não existe
        # training_service.save_data()

        # Exibe estatísticas
        stats = training_service.generate_training_statistics()
        self.stdout.write(self.style.SUCCESS(f"Base de conhecimento populada com sucesso!"))
        self.stdout.write(f"Total de itens: {stats.get('total_knowledge', 0)}")
        self.stdout.write(f"Categorias: {', '.join([c.get('category', '') for c in stats.get('categories', [])])}")

    def _populate_from_books(self):
        """Popula a base de conhecimento com informações dos livros no sistema."""
        books = Book.objects.all()
        count = 0

        self.stdout.write("Adicionando conhecimento sobre livros...")

        for book in books:
            # Pergunta sobre título do livro
            q1 = f"Quem escreveu {book.titulo}?"
            a1 = f"{book.titulo} foi escrito por {book.autor}."
            training_service.add_knowledge_item(q1, a1, category="livros", source="db")

            # Pergunta sobre sinopse
            if book.descricao:
                q2 = f"Qual é a sinopse de {book.titulo}?"
                a2 = f"A sinopse de {book.titulo} é: {book.descricao}"
                training_service.add_knowledge_item(q2, a2, category="livros", source="db")

            # Pergunta sobre gênero/categoria
            if book.categoria:
                q3 = f"Qual é o gênero/categoria de {book.titulo}?"
                a3 = f"{book.titulo} pertence à categoria de {book.categoria}."
                training_service.add_knowledge_item(q3, a3, category="livros", source="db")

            count += 1
            if count % 50 == 0:
                self.stdout.write(f"  {count} livros processados...")

        self.stdout.write(self.style.SUCCESS(f"  {count} livros adicionados à base de conhecimento"))

    def _populate_from_authors(self):
        """Popula a base de conhecimento com informações dos autores no sistema."""
        authors = Author.objects.all()
        count = 0

        self.stdout.write("Adicionando conhecimento sobre autores...")

        for author in authors:
            # Informações básicas sobre o autor
            q1 = f"Quem é {author.nome}?"
            biografia = author.biografia if author.biografia else "Não temos informações detalhadas sobre este autor."
            a1 = f"{author.nome} é um autor conhecido. {biografia}"
            training_service.add_knowledge_item(q1, a1, category="autores", source="db")

            # Livros do autor
            author_books = Book.objects.filter(autor__icontains=author.nome)
            if author_books.exists():
                q2 = f"Quais livros {author.nome} escreveu?"
                book_list = ", ".join([book.titulo for book in author_books])
                a2 = f"{author.nome} escreveu os seguintes livros: {book_list}."
                training_service.add_knowledge_item(q2, a2, category="autores", source="db")

            count += 1
            if count % 20 == 0:
                self.stdout.write(f"  {count} autores processados...")

        self.stdout.write(self.style.SUCCESS(f"  {count} autores adicionados à base de conhecimento"))

    def _add_navigation_knowledge(self):
        """Adiciona informações sobre navegação no site."""
        self.stdout.write("Adicionando conhecimento sobre navegação...")

        navigation_info = [
            {
                "question": "Como encontro meus livros favoritos?",
                "answer": "Seus livros favoritos podem ser encontrados na sua página de perfil. Basta clicar em 'Perfil' no menu superior e você verá a seção 'Favoritos'."
            },
            {
                "question": "Onde vejo os livros que estou lendo?",
                "answer": "Os livros que você está lendo atualmente ficam na sua página de perfil, na seção 'Lendo'."
            },
            {
                "question": "Como adiciono um livro à minha prateleira?",
                "answer": "Para adicionar um livro à sua prateleira, vá para a página de detalhes do livro e clique em um dos botões: 'Adicionar aos Favoritos', 'Lendo', 'Quero Ler' ou 'Lido'."
            },
            {
                "question": "Como busco livros por gênero?",
                "answer": "Você pode buscar livros por gênero usando a barra de pesquisa no topo da página e digitando o gênero, ou navegando pelo 'Catálogo' no menu 'Explorando' e usando os filtros disponíveis."
            },
            {
                "question": "Como edito meu perfil?",
                "answer": "Para editar seu perfil, clique em 'Perfil' no menu superior e depois no botão 'Editar Perfil' que aparece na página."
            },
            {
                "question": "Onde encontro as recomendações de livros?",
                "answer": "As recomendações personalizadas de livros estão disponíveis na página inicial e também em 'Recomendados' no menu 'Explorando'."
            },
            {
                "question": "Como funciona o sistema de conquistas?",
                "answer": "O sistema de conquistas recompensa suas atividades de leitura e interação com a plataforma. Você pode ver suas conquistas na seção 'Conquistas' da sua página de perfil."
            }
        ]

        for item in navigation_info:
            training_service.add_knowledge_item(
                item["question"],
                item["answer"],
                category="navegacao",
                source="manual"
            )

        self.stdout.write(self.style.SUCCESS(f"  {len(navigation_info)} itens de navegação adicionados"))

    def _add_literary_genres_knowledge(self):
        """Adiciona conhecimento sobre gêneros literários."""
        self.stdout.write("Adicionando conhecimento sobre gêneros literários...")

        genres_info = [
            {
                "question": "O que é ficção científica?",
                "answer": "Ficção científica é um gênero literário que explora conceitos imaginativos baseados na ciência, tecnologia, espaço, viagem no tempo, universos paralelos e vida extraterrestre. Autores populares incluem Isaac Asimov, Arthur C. Clarke, e Ursula K. Le Guin."
            },
            {
                "question": "O que é literatura fantástica?",
                "answer": "Literatura fantástica é um gênero que inclui elementos mágicos, sobrenaturais ou impossíveis como parte do mundo da história. Subgêneros incluem alta fantasia, fantasia urbana e realismo mágico. Autores notáveis incluem J.R.R. Tolkien, George R.R. Martin e Neil Gaiman."
            },
            {
                "question": "O que é romance policial?",
                "answer": "Romance policial é um gênero focado na investigação de um crime, geralmente um assassinato, por um detetive ou investigador. Autores clássicos incluem Agatha Christie, Arthur Conan Doyle e contemporâneos como Gillian Flynn e Harlan Coben."
            },
            {
                "question": "O que é literatura de terror?",
                "answer": "Literatura de terror visa provocar medo, pavor ou desconforto nos leitores, explorando temores humanos profundos. Mestres do gênero incluem Stephen King, H.P. Lovecraft e Shirley Jackson."
            },
            {
                "question": "O que é romance histórico?",
                "answer": "Romance histórico é ambientado no passado e incorpora eventos ou personagens históricos, misturando fatos e ficção. Autores notáveis incluem Hilary Mantel, Ken Follett e Philippa Gregory."
            }
        ]

        for item in genres_info:
            training_service.add_knowledge_item(
                item["question"],
                item["answer"],
                category="generos_literarios",
                source="manual"
            )

        self.stdout.write(self.style.SUCCESS(f"  {len(genres_info)} itens sobre gêneros literários adicionados"))

    def _add_literary_faq(self):
        """Adiciona perguntas frequentes sobre literatura."""
        self.stdout.write("Adicionando perguntas frequentes sobre literatura...")

        literature_faq = [
            {
                "question": "Quem é o autor de O Senhor dos Anéis?",
                "answer": "J.R.R. Tolkien é o autor de 'O Senhor dos Anéis', uma obra épica de fantasia publicada entre 1954 e 1955."
            },
            {
                "question": "Qual foi o primeiro livro de Harry Potter?",
                "answer": "'Harry Potter e a Pedra Filosofal' (ou 'Pedra do Feiticeiro' em algumas traduções) foi o primeiro livro da série Harry Potter, escrito por J.K. Rowling e publicado em 1997."
            },
            {
                "question": "O que é o Realismo Mágico?",
                "answer": "Realismo Mágico é um estilo literário que incorpora elementos mágicos ou fantásticos em um ambiente realista. É associado a autores latino-americanos como Gabriel García Márquez e Isabel Allende."
            },
            {
                "question": "Qual é o livro mais vendido de todos os tempos?",
                "answer": "A Bíblia é considerada o livro mais vendido e distribuído de todos os tempos, com estimativas que variam entre 5 e 6 bilhões de cópias."
            },
            {
                "question": "Quem escreveu 1984?",
                "answer": "George Orwell (pseudônimo de Eric Arthur Blair) escreveu '1984', um romance distópico publicado em 1949 que retrata um futuro totalitário."
            }
        ]

        for item in literature_faq:
            training_service.add_knowledge_item(
                item["question"],
                item["answer"],
                category="faq_literatura",
                source="manual"
            )

        self.stdout.write(self.style.SUCCESS(f"  {len(literature_faq)} perguntas frequentes adicionadas"))

    def _process_csv(self, file_path):
        """Processa um arquivo CSV com dados adicionais para a base de conhecimento."""
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Arquivo CSV não encontrado: {file_path}"))
            return

        try:
            count = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'question' in row and 'answer' in row:
                        category = row.get('category', 'importado')
                        source = row.get('source', 'csv')

                        training_service.add_knowledge_item(
                            row['question'],
                            row['answer'],
                            category=category,
                            source=source
                        )
                        count += 1

            self.stdout.write(self.style.SUCCESS(f"  {count} itens importados do CSV"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao processar CSV: {str(e)}"))

    def _process_json(self, file_path):
        """Processa um arquivo JSON com dados adicionais para a base de conhecimento."""
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Arquivo JSON não encontrado: {file_path}"))
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                self.stdout.write(self.style.ERROR("O arquivo JSON deve conter uma lista de itens"))
                return

            count = 0
            for item in data:
                if 'question' in item and 'answer' in item:
                    category = item.get('category', 'importado')
                    source = item.get('source', 'json')

                    training_service.add_knowledge_item(
                        item['question'],
                        item['answer'],
                        category=category,
                        source=source
                    )
                    count += 1

            self.stdout.write(self.style.SUCCESS(f"  {count} itens importados do JSON"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao processar JSON: {str(e)}"))