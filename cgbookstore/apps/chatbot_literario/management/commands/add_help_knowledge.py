# cgbookstore/apps/chatbot_literario/management/commands/add_help_knowledge.py

from django.core.management.base import BaseCommand
from cgbookstore.apps.chatbot_literario.services import training_service
from cgbookstore.apps.chatbot_literario.models import KnowledgeItem


class Command(BaseCommand):
    help = 'Adiciona ou atualiza o conhecimento essencial (ajuda, recomendações, navegação) do chatbot.'

    def handle(self, *args, **options):
        if not training_service or not hasattr(training_service, 'initialized'):
            self.stdout.write(self.style.ERROR("ERRO: TrainingService não foi inicializado corretamente."))
            return

        if not training_service.initialized:
            training_service.initialize()

        self.stdout.write("Adicionando/atualizando conhecimento sobre capacidades do chatbot...")

        # ✅ RESPOSTAS COMPLETAS RESTAURADAS AQUI
        help_knowledge = [
            {
                "question": "O que você pode fazer?",
                "answer": "Posso ajudar você com várias coisas! Aqui estão minhas principais capacidades:\n\n• 📚 Informações sobre livros: posso falar sobre autores, datas de publicação, sinopses e detalhes de obras\n• 🔍 Recomendações de leitura: sugiro livros baseados em seus interesses\n• 🧭 Navegação no site: ajudo a encontrar funcionalidades como favoritos, carrinho, avaliações\n• 📖 Dúvidas sobre literatura: respondo perguntas sobre gêneros literários, autores famosos e obras clássicas\n• 💬 Conversa contextual: lembro do que conversamos e posso responder perguntas de acompanhamento\n\nÉ só me perguntar!",
                "category": "ajuda"
            },
            {
                "question": "Como você funciona?",
                "answer": "Sou um assistente virtual especializado em literatura! Funciono assim:\n\n• Analiso suas perguntas para entender o que você precisa\n• Busco informações em minha base de conhecimento sobre livros e autores\n• Mantenho o contexto da nossa conversa para respostas mais precisas\n• Posso ajudar tanto com informações sobre obras quanto com a navegação no site\n\nPode me fazer perguntas naturalmente, como faria com um amigo que entende de livros!",
                "category": "ajuda"
            },
            {
                "question": "O que você sabe fazer?",
                "answer": "Minhas especialidades incluem:\n\n📚 **Sobre Livros**: Informações sobre autores, datas de publicação, sinopses, gêneros\n🎯 **Recomendações**: Sugiro leituras baseadas em seus gostos\n🔍 **Busca**: Ajudo a encontrar livros específicos ou por categoria\n🧭 **Site**: Explico como usar favoritos, carrinho, avaliações e outras funcionalidades\n💡 **Literatura**: Respondo sobre movimentos literários, autores clássicos e contemporâneos\n\nExperimente me perguntar algo!",
                "category": "ajuda"
            },
            {
                "question": "Você pode me ajudar?",
                "answer": "Claro! Estou aqui para ajudar com tudo relacionado a livros e ao uso do site. Posso:\n\n• Dar informações sobre livros e autores\n• Fazer recomendações de leitura\n• Explicar como usar as funcionalidades do site\n• Responder dúvidas sobre literatura\n• Ajudar a encontrar o que você procura\n\nO que você gostaria de saber?",
                "category": "ajuda"
            },
            {
                "question": "Quais são suas funcionalidades?",
                "answer": "Minhas principais funcionalidades são:\n\n1. **Informações Literárias**: Dados sobre livros, autores, publicações e sinopses\n2. **Sistema de Recomendações**: Sugestões personalizadas de leitura\n3. **Suporte à Navegação**: Ajuda para usar o site (favoritos, perfil, carrinho)\n4. **Contexto Inteligente**: Lembro de nossa conversa para respostas mais relevantes\n5. **Base de Conhecimento**: Acesso a informações sobre literatura brasileira e mundial\n\nComo posso ajudar você hoje?",
                "category": "ajuda"
            },
            {
                "question": "Me ajuda",
                "answer": "Com certeza! Estou aqui para ajudar. Você pode:\n\n• Me perguntar sobre qualquer livro ou autor\n• Pedir recomendações de leitura\n• Tirar dúvidas sobre como usar o site\n• Buscar informações sobre gêneros literários\n• Saber mais sobre obras clássicas ou contemporâneas\n\nQual é sua dúvida ou o que você está procurando?",
                "category": "ajuda"
            },
            {
                "question": "Como posso usar você?",
                "answer": "É muito simples me usar! Basta conversar comigo naturalmente:\n\n💬 **Exemplos de perguntas**:\n• 'Quem escreveu Dom Casmurro?'\n• 'Me recomenda um livro de ficção científica'\n• 'Como adiciono livros aos favoritos?'\n• 'Quando foi publicado 1984?'\n• 'Onde vejo meus livros salvos?'\n\n🔄 **Dicas**: Posso lembrar do contexto, então após perguntar sobre um livro, você pode perguntar 'E quando foi publicado?' que entenderei a referência!\n\nExperimente fazer uma pergunta!",
                "category": "ajuda"
            },
            {
                "question": "Ajuda",
                "answer": "Olá! Vejo que precisa de ajuda. Aqui está um guia rápido:\n\n**O que posso fazer por você:**\n• 📖 Informações sobre livros e autores\n• 🎁 Recomendações de leitura\n• 🛒 Ajuda com o site (carrinho, favoritos, perfil)\n• 📚 Dúvidas sobre literatura em geral\n\n**Como me usar:**\nApenas faça sua pergunta naturalmente! Por exemplo:\n- 'Quais são os livros mais populares?'\n- 'Como encontro meus favoritos?'\n- 'Me fale sobre Machado de Assis'\n\nO que você gostaria de saber?",
                "category": "ajuda"
            }
        ]

        recommendation_knowledge = [
            {
                "question": "Pode me recomendar livros de fantasia?",
                "answer": "Claro! Aqui estão algumas excelentes recomendações de fantasia:\n\n📚 **Clássicos da Fantasia**:\n• O Senhor dos Anéis - J.R.R. Tolkien\n• As Crônicas de Nárnia - C.S. Lewis\n• O Hobbit - J.R.R. Tolkien\n\n🌟 **Fantasia Moderna**:\n• O Nome do Vento - Patrick Rothfuss\n• A Roda do Tempo - Robert Jordan\n• Mistborn - Brandon Sanderson\n\n🇧🇷 **Fantasia Nacional**:\n• A Batalha do Apocalipse - Eduardo Spohr\n• O Espadachim de Carvão - Affonso Solano\n\nQuer saber mais sobre algum desses livros?",
                "category": "recomendacao"
            },
            {
                "question": "Me recomenda um livro de ficção científica",
                "answer": "Ótima escolha! Aqui vão algumas recomendações de ficção científica:\n\n🚀 **Clássicos Essenciais**:\n• 1984 - George Orwell\n• Admirável Mundo Novo - Aldous Huxley\n• Fundação - Isaac Asimov\n• Duna - Frank Herbert\n\n⭐ **Modernos Imperdíveis**:\n• O Problema dos Três Corpos - Liu Cixin\n• Perdido em Marte - Andy Weir\n• Ready Player One - Ernest Cline\n\n🇧🇷 **Ficção Científica Brasileira**:\n• Não Verás País Nenhum - Ignácio de Loyola Brandão\n• O Conto da Aia Brasileira - autores diversos\n\nPosso dar mais detalhes sobre qualquer um deles!",
                "category": "recomendacao"
            },
            {
                "question": "Quais livros você recomenda?",
                "answer": "Posso recomendar livros de acordo com seus interesses! Aqui estão algumas sugestões por categoria:\n\n📚 **Literatura Brasileira**: Dom Casmurro, Grande Sertão: Veredas, Capitães da Areia\n🔮 **Fantasia**: O Senhor dos Anéis, Harry Potter, As Crônicas de Nárnia\n🤖 **Ficção Científica**: 1984, Duna, Neuromancer\n🔍 **Mistério/Suspense**: Sherlock Holmes, Agatha Christie, O Código Da Vinci\n❤️ **Romance**: Orgulho e Preconceito, Como Eu Era Antes de Você, O Morro dos Ventos Uivantes\n\nQue gênero mais te interessa? Posso ser mais específico!",
                "category": "recomendacao"
            }
        ]

        navigation_knowledge = [
            {
                "question": "Como adiciono um livro ao carrinho?",
                "answer": "Para adicionar um livro ao carrinho:\n\n1. 🔍 Encontre o livro que deseja (use a busca ou navegue pelo catálogo)\n2. 📖 Clique no livro para ver os detalhes\n3. 🛒 Clique no botão 'Adicionar ao Carrinho' (geralmente em destaque na página)\n4. ✅ O livro será adicionado e você verá uma confirmação\n\nDica: Você também pode adicionar livros ao carrinho direto da lista de resultados, procurando pelo ícone do carrinho!",
                "category": "navegacao"
            },
            {
                "question": "Como faço para avaliar um livro?",
                "answer": "Para avaliar um livro no site:\n\n1. 📚 Acesse a página do livro que deseja avaliar\n2. ⭐ Procure a seção de avaliações (geralmente abaixo da sinopse)\n3. 🌟 Clique nas estrelas para dar sua nota (1 a 5 estrelas)\n4. 💬 Escreva seu comentário sobre o livro (opcional mas recomendado!)\n5. ✅ Clique em 'Enviar Avaliação'\n\n⚠️ Importante: Você precisa estar logado e ter lido o livro para avaliar!",
                "category": "navegacao"
            }
        ]

        all_knowledge = help_knowledge + recommendation_knowledge + navigation_knowledge

        created_count = 0
        updated_count = 0

        for item_data in all_knowledge:
            result = training_service.add_knowledge(
                question=item_data["question"],
                answer=item_data["answer"],
                category=item_data["category"],
                source="manual"
            )

            if result.get('created'):
                created_count += 1
            elif result.get('success'):
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Processo concluído. {created_count} novos itens adicionados, {updated_count} itens atualizados."
        ))

        self.stdout.write(f"\n📊 Estatísticas atuais da base:")
        self.stdout.write(f"  - Total de itens: {KnowledgeItem.objects.count()}")
        self.stdout.write(f"  - Categoria 'ajuda': {KnowledgeItem.objects.filter(category='ajuda').count()}")
        self.stdout.write(
            f"  - Categoria 'recomendacao': {KnowledgeItem.objects.filter(category='recomendacao').count()}")
        self.stdout.write(f"  - Categoria 'navegacao': {KnowledgeItem.objects.filter(category='navegacao').count()}")