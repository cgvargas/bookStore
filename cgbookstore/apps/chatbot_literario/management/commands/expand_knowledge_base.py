# cgbookstore/apps/chatbot_literario/management/commands/expand_knowledge_base.py

from django.core.management.base import BaseCommand
from cgbookstore.apps.chatbot_literario.services import training_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Expande a base de conhecimento com novos autores e obras da literatura brasileira'

    def handle(self, *args, **options):
        """
        ✅ EXPANSÃO: Adiciona conhecimento essencial de literatura brasileira
        """
        self.stdout.write('🚀 Iniciando expansão da base de conhecimento...')

        # Novos itens de conhecimento para adicionar
        knowledge_items = [
            # AUTORES BRASILEIROS ESSENCIAIS
            {
                'question': 'Quem foi Guimarães Rosa?',
                'answer': 'João Guimarães Rosa (1908-1967) foi um escritor brasileiro, considerado um dos maiores nomes da literatura nacional. Médico e diplomata, Rosa revolucionou a linguagem literária brasileira com obras como "Grande Sertão: Veredas" (1956) e "Sagarana" (1946). Sua escrita inovadora mistura linguagem erudita com fala sertaneja, criando neologismos e explorando temas universais através do sertão mineiro. É considerado um dos precursores do realismo mágico na literatura brasileira.',
                'category': 'author',
                'source': 'literatura_brasileira'
            },
            {
                'question': 'Quem foi Clarice Lispector?',
                'answer': 'Clarice Lispector (1920-1977) foi uma das mais importantes escritoras brasileiras do século XX. Nascida na Ucrânia e criada no Brasil, desenvolveu uma prosa introspectiva e filosófica única. Suas principais obras incluem "A Hora da Estrela" (1977), "A Paixão Segundo G.H." (1964), "Água Viva" (1973) e "Perto do Coração Selvagem" (1943). Sua literatura explora a condição humana, a existência feminina e a busca pela identidade, influenciando profundamente a literatura contemporânea.',
                'category': 'author',
                'source': 'literatura_brasileira'
            },
            {
                'question': 'Quem foi Graciliano Ramos?',
                'answer': 'Graciliano Ramos (1892-1953) foi um romancista brasileiro, considerado o maior representante da segunda fase do modernismo brasileiro. Suas obras principais incluem "São Bernardo" (1934), "Angústia" (1936), "Vidas Secas" (1938) e as memórias "Infância" (1945). Conhecido pela precisão da linguagem e crítica social contundente, retratou a realidade nordestina com realismo impressionante. Também foi preso político durante o Estado Novo, experiência narrada em "Memórias do Cárcere" (póstumo, 1953).',
                'category': 'author',
                'source': 'literatura_brasileira'
            },
            {
                'question': 'Quem foi Carlos Drummond de Andrade?',
                'answer': 'Carlos Drummond de Andrade (1902-1987) é considerado um dos maiores poetas brasileiros de todos os tempos. Mineiro de Itabira, foi um dos principais nomes do modernismo brasileiro. Suas obras mais conhecidas incluem "Alguma Poesia" (1930), "Brejo das Almas" (1934), "A Rosa do Povo" (1945) e "Claro Enigma" (1951). Sua poesia aborda temas como o cotidiano, questões sociais, amor e a condição humana, sempre com linguagem acessível e profundidade filosófica. O poema "No Meio do Caminho" é um dos mais conhecidos da literatura brasileira.',
                'category': 'author',
                'source': 'literatura_brasileira'
            },

            # OBRAS FUNDAMENTAIS
            {
                'question': 'O que é Grande Sertão: Veredas?',
                'answer': 'Grande Sertão: Veredas (1956) é a obra-prima de Guimarães Rosa, considerada um dos maiores romances da literatura brasileira. Narrado por Riobaldo, ex-jagunço que conta sua história a um interlocutor silencioso, o livro mistura aventura, filosofia e linguagem inovadora. A narrativa explora temas como bem e mal, amor e amizade (a relação com Diadorim), e a condição humana através do sertão mineiro. Rosa criou uma linguagem única, misturando português arcaico, regionalismos e neologismos, revolucionando a prosa brasileira.',
                'category': 'book',
                'source': 'literatura_brasileira'
            },
            {
                'question': 'O que é A Hora da Estrela?',
                'answer': 'A Hora da Estrela (1977) é a última obra publicada em vida por Clarice Lispector, considerada uma de suas mais importantes. O romance conta a história de Macabéa, uma jovem nordestina que vive precariamente no Rio de Janeiro. Através da narrativa de Rodrigo S.M., Clarice explora temas como pobreza, alienação social e a condição feminina. A obra é uma reflexão sobre a literatura, a realidade social brasileira e a dificuldade de representar o outro. O final trágico de Macabéa simboliza a invisibilidade dos marginalizados na sociedade.',
                'category': 'book',
                'source': 'literatura_brasileira'
            },
            {
                'question': 'O que é Vidas Secas?',
                'answer': 'Vidas Secas (1938) é considerada a obra-prima de Graciliano Ramos e um dos maiores romances da literatura brasileira. A narrativa acompanha a família de Fabiano, sertanejo que migra com a esposa Sinha Vitória e os dois filhos em busca de melhores condições de vida durante a seca. Estruturado em 13 capítulos quase independentes, o livro retrata com realismo brutal a miséria, a exploração social e a luta pela sobrevivência no Nordeste. A linguagem enxuta e precisa de Graciliano dá voz aos marginalizados, tornando-se um clássico do realismo social brasileiro.',
                'category': 'book',
                'source': 'literatura_brasileira'
            },

            # MOVIMENTOS LITERÁRIOS
            {
                'question': 'O que foi o Modernismo brasileiro?',
                'answer': 'O Modernismo brasileiro foi um movimento cultural que revolucionou as artes no país, iniciado oficialmente com a Semana de Arte Moderna de 1922. Dividido em três fases principais: 1ª fase (1922-1930) - fase heroica com Mário de Andrade, Oswald de Andrade; 2ª fase (1930-1945) - consolidação com Graciliano Ramos, José Lins do Rego, Érico Veríssimo; 3ª fase (1945-1960) - geração de 45 com Guimarães Rosa, Clarice Lispector. O movimento buscou uma identidade nacional, rompeu com padrões clássicos, valorizou a linguagem coloquial e temas brasileiros.',
                'category': 'movement',
                'source': 'literatura_brasileira'
            },
            {
                'question': 'O que foi a Semana de Arte Moderna?',
                'answer': 'A Semana de Arte Moderna (11-18 de fevereiro de 1922) foi um evento cultural realizado no Theatro Municipal de São Paulo que marcou o início oficial do Modernismo brasileiro. Organizada por intelectuais como Mário de Andrade, Oswald de Andrade, Graça Aranha e artistas como Anita Malfatti, Di Cavalcanti e Victor Brecheret. O evento propôs a renovação estética e cultural do país, rompendo com padrões acadêmicos e europeizantes, buscando uma arte genuinamente brasileira. Apesar da recepção hostil inicial, tornou-se marco fundamental da cultura nacional.',
                'category': 'movement',
                'source': 'literatura_brasileira'
            },

            # ANÁLISES LITERÁRIAS
            {
                'question': 'Quais são as características do estilo machadiano?',
                'answer': 'O estilo machadiano se caracteriza por: 1) Ironia refinada e pessimismo elegante; 2) Narrador intruso que conversa com o leitor; 3) Análise psicológica profunda dos personagens; 4) Crítica social sutil mas contundente; 5) Linguagem erudita e precisa; 6) Uso de recursos como metalepse e digressões; 7) Ceticismo quanto à natureza humana; 8) Influências de Sterne, Schopenhauer e moralistas franceses; 9) Técnica realista com toques de humor negro; 10) Exploração de temas universais através da sociedade carioca do século XIX.',
                'category': 'analysis',
                'source': 'literatura_brasileira'
            },
            {
                'question': 'Como funciona o realismo mágico em Guimarães Rosa?',
                'answer': 'O realismo mágico em Guimarães Rosa manifesta-se através da fusão entre elementos realistas e fantásticos no sertão mineiro. Características: 1) Linguagem inventiva que cria uma realidade própria; 2) Elementos sobrenaturais tratados como naturais (pactos, assombrações); 3) Tempo circular e mítico sobrepondo-se ao cronológico; 4) Paisagem sertaneja transfigurada em espaço universal; 5) Personagens arquetípicos com dimensões míticas; 6) Oralidade recriada literariamente; 7) Filosofia popular misturada à erudição; 8) Realidade social transformada em alegoria universal.',
                'category': 'analysis',
                'source': 'literatura_brasileira'
            },

            # CONTEXTO HISTÓRICO
            {
                'question': 'Como o contexto histórico influenciou a literatura brasileira do século XX?',
                'answer': 'A literatura brasileira do século XX foi profundamente influenciada por transformações históricas: 1) República Velha (1889-1930): literatura pré-modernista retrata problemas sociais (Euclides da Cunha, Lima Barreto); 2) Era Vargas (1930-1945): literatura social e regional (Rachel de Queiroz, José Lins do Rego); 3) Democratização (1945-1964): experimentação estética (Clarice Lispector, Guimarães Rosa); 4) Ditadura Militar (1964-1985): literatura de resistência e introspecção. Eventos como industrialização, urbanização, guerras mundiais e movimentos sociais moldaram temas e estilos dos escritores brasileiros.',
                'category': 'analysis',
                'source': 'literatura_brasileira'
            }
        ]

        # Adicionar cada item à base de conhecimento
        success_count = 0
        error_count = 0

        for item in knowledge_items:
            try:
                result = training_service.add_knowledge(
                    question=item['question'],
                    answer=item['answer'],
                    category=item['category'],
                    source=item['source']
                )

                if result['success']:
                    success_count += 1
                    action = "criado" if result['created'] else "atualizado"
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {action}: {item["question"][:50]}...')
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'❌ Erro: {item["question"][:50]}... - {result["message"]}')
                    )

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Exceção: {item["question"][:50]}... - {str(e)}')
                )

        # Relatório final
        total_items = len(knowledge_items)
        self.stdout.write('\n📊 RELATÓRIO FINAL:')
        self.stdout.write(f'📚 Total de itens processados: {total_items}')
        self.stdout.write(self.style.SUCCESS(f'✅ Sucessos: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Erros: {error_count}'))

        # Gerar embeddings para os novos itens
        if success_count > 0:
            self.stdout.write('\n🧠 Gerando embeddings para novos itens...')
            try:
                embeddings_result = training_service.update_all_embeddings()
                if embeddings_result['success']:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Embeddings atualizados: {embeddings_result["updated_count"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Problemas nos embeddings: {embeddings_result["message"]}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao gerar embeddings: {str(e)}')
                )

        # Status final da base
        try:
            stats = training_service.get_knowledge_stats()
            self.stdout.write('\n📈 STATUS ATUAL DA BASE:')
            self.stdout.write(f'📖 Itens ativos: {stats.get("active_items", 0)}')
            self.stdout.write(f'🧠 Com embeddings: {stats.get("with_embeddings", 0)}')

            categories = stats.get("categories", {})
            if categories:
                self.stdout.write('📂 Por categoria:')
                for category, count in categories.items():
                    self.stdout.write(f'   • {category}: {count} itens')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao obter estatísticas: {str(e)}')
            )

        self.stdout.write('\n🎉 Expansão da base de conhecimento concluída!')

        if success_count == total_items:
            self.stdout.write(
                self.style.SUCCESS('✅ Todos os itens foram adicionados com sucesso!')
            )
        elif success_count > 0:
            self.stdout.write(
                self.style.WARNING(f'⚠️ {success_count}/{total_items} itens adicionados. Verifique os erros acima.')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Nenhum item foi adicionado. Verifique a configuração do sistema.')
            )