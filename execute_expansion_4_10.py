#!/usr/bin/env python
"""
Execução direta da expansão - Itens 4-10
Execução: execute_expansion_4_10.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from cgbookstore.apps.chatbot_literario.services import training_service


def main():
    print("🚀 EXECUÇÃO IMEDIATA - EXPANSÃO ITENS 4-10")
    print("=" * 60)

    print("📊 Status inicial:")
    stats = training_service.get_knowledge_stats()
    print(f"   📚 Itens ativos: {stats.get('active_items', 0)}")
    print(f"   🧠 Com embeddings: {stats.get('with_embeddings', 0)}")

    # Lista de itens a adicionar
    items_to_add = [
        {
            "question": "Quem foi José de Alencar?",
            "answer": """José Martiniano de Alencar (1829-1877) foi um dos principais escritores do Romantismo brasileiro, considerado o criador do romance brasileiro e grande defensor da literatura nacional.

BIOGRAFIA:
• Nascimento: 1º de maio de 1829, Messejana, Ceará
• Formação: Direito em São Paulo e Olinda
• Carreiras: Advogado, jornalista, político, escritor
• Atuação política: Deputado, Ministro da Justiça
• Morte: 12 de dezembro de 1877, Rio de Janeiro

CARACTERÍSTICAS LITERÁRIAS:
• Criador do romance de temática brasileira
• Exaltação da natureza e do índio brasileiro
• Linguagem adaptada ao português brasileiro
• Defesa da independência literária nacional
• Estilo romântico com cor local

OBRAS PRINCIPAIS:
• Indianistas: "O Guarani", "Iracema", "Ubirajara"
• Urbanos: "Senhora", "Lucíola", "Diva"
• Regionais: "O Gaúcho", "O Sertanejo"
• Teatro: "O Demônio Familiar", "Mãe"

IMPORTÂNCIA:
José de Alencar foi fundamental para estabelecer uma identidade própria à literatura brasileira, criando personagens e temas genuinamente nacionais, especialmente através da idealização do índio como herói romântico.""",
            "category": "author"
        },
        {
            "question": "O que é Iracema de José de Alencar?",
            "answer": """Iracema é um romance indianista de José de Alencar, publicado em 1865, considerado uma das obras-primas do Romantismo brasileiro. Subtitulado "Lenda do Ceará", narra a história de amor entre a índia Iracema e o português Martim.

ENREDO CENTRAL:
• Iracema: índia tabajara, guardiã do segredo da jurema
• Martim: guerreiro português que se perde na floresta
• Romance proibido entre os dois personagens
• Nascimento de Moacir, primeiro cearense
• Alegoria da formação do povo brasileiro

CARACTERÍSTICAS LITERÁRIAS:
• Linguagem poética e musical
• Fusão de lenda indígena com história
• Exaltação da natureza brasileira
• Idealização do índio e do amor
• Nacionalismo romântico

SIMBOLISMO:
• Iracema = anagrama de "América"
• Moacir = "filho da dor" (primeiro mestiço)
• Martim = elemento colonizador europeu
• União = símbolo da miscigenação brasileira

FRASES FAMOSAS:
"Iracema, a virgem dos lábios de mel"
"Onde vai a afoita jandaia?"

LEGADO:
Iracema tornou-se símbolo do Ceará e da literatura brasileira, representando o mito fundador da nacionalidade através do encontro entre culturas.""",
            "category": "book"
        },
        {
            "question": "O que foi o Romantismo no Brasil?",
            "answer": """O Romantismo brasileiro (1836-1881) foi um movimento literário que marcou a independência cultural do Brasil, coincidindo com a independência política e a formação da identidade nacional.

MARCO INICIAL:
• 1836: "Suspiros Poéticos e Saudades" de Gonçalves de Magalhães
• Revista Niterói: manifesto romântico brasileiro
• Influência: Romantismo europeu adaptado ao Brasil

CARACTERÍSTICAS GERAIS:
• Nacionalismo e exaltação da pátria
• Valorização da natureza tropical
• Idealização do índio como herói nacional
• Sentimentalismo e subjetivismo
• Escapismo e medievalismo
• Linguagem emocional e popular

GERAÇÕES/FASES:
1ª GERAÇÃO (Nacionalista/Indianista):
• Gonçalves Dias, José de Alencar
• Temas: pátria, natureza, índio

2ª GERAÇÃO (Ultrarromântica/Byroniana):
• Álvares de Azevedo, Casimiro de Abreu
• Temas: morte, amor impossível, melancolia

3ª GERAÇÃO (Condoreira/Social):
• Castro Alves, Tobias Barreto
• Temas: abolição, república, justiça social

PRINCIPAIS AUTORES:
• Poesia: Gonçalves Dias, Castro Alves, Álvares de Azevedo
• Prosa: José de Alencar, Manuel Antônio de Almeida
• Teatro: Martins Pena, José de Alencar

IMPORTÂNCIA:
O Romantismo consolidou a literatura brasileira como expressão autônoma, criando uma identidade cultural nacional.""",
            "category": "movement"
        },
        {
            "question": "Como analisar personagens na literatura?",
            "answer": """A análise de personagens é fundamental para compreender uma obra literária. Os personagens são os elementos que vivenciam os conflitos e desenvolvem os temas da narrativa.

TIPOS DE PERSONAGENS:
• Protagonista: personagem principal
• Antagonista: opositor do protagonista
• Secundários: apoiam a trama principal
• Figurantes: aparecem ocasionalmente

CLASSIFICAÇÃO POR COMPLEXIDADE:
• Planos/Simples: uma característica dominante
• Redondos/Complexos: múltiplas características, evoluem
• Estáticos: não mudam durante a narrativa
• Dinâmicos: transformam-se ao longo da história

MÉTODOS DE CARACTERIZAÇÃO:
• Direta: narrador descreve explicitamente
• Indireta: revelação através de ações, falas, pensamentos
• Autocaracterização: personagem se revela
• Heterocaracterização: outros personagens o descrevem

ASPECTOS A ANALISAR:
• Físicos: aparência, gestos, vestimentas
• Psicológicos: personalidade, motivações, conflitos internos
• Sociais: classe, profissão, relacionamentos
• Morais: valores, princípios, comportamentos

EXEMPLOS CLÁSSICOS:
• Capitu (Dom Casmurro): complexidade psicológica
• Bentinho: narrador não-confiável
• Rita Baiana (O Cortiço): determinismo social

FUNÇÃO NARRATIVA:
Os personagens são veículos dos temas e valores da obra, representando diferentes aspectos da condição humana e social.""",
            "category": "analysis"
        },
        {
            "question": "O que foi o Realismo no Brasil?",
            "answer": """O Realismo brasileiro (1881-1893) foi um movimento literário que rompeu com o idealismo romântico, retratando a realidade social brasileira com objetividade e senso crítico.

MARCO INICIAL:
• 1881: "Memórias Póstumas de Brás Cubas" (Machado de Assis)
• "O Mulato" (Aluísio Azevedo)
• Fim do Romantismo, início da análise social

CARACTERÍSTICAS GERAIS:
• Objetividade e imparcialidade narrativa
• Crítica social e política
• Análise psicológica dos personagens
• Retrato fiel da realidade contemporânea
• Linguagem clara e direta
• Determinismo social (Naturalismo)

PRINCIPAIS TEMAS:
• Hipocrisia da sociedade burguesa
• Corrupção política e social
• Conflitos psicológicos
• Relações amorosas realistas
• Crítica ao casamento por interesse
• Questão racial e escravidão

VERTENTES:
• Realismo propriamente dito: análise psicológica (Machado)
• Naturalismo: determinismo científico (Aluísio Azevedo)

PRINCIPAIS AUTORES:
• Machado de Assis: mestre da análise psicológica
• Aluísio Azevedo: principal naturalista
• Raul Pompéia: "O Ateneu" (realismo memorialista)

OBRAS FUNDAMENTAIS:
• "Dom Casmurro", "Quincas Borba" (Machado)
• "O Cortiço" (Aluísio Azevedo)
• "O Ateneu" (Raul Pompéia)

LEGADO:
O Realismo trouxe maturidade à literatura brasileira, estabelecendo a crítica social como função da arte.""",
            "category": "movement"
        },
        {
            "question": "Quais são as principais técnicas narrativas na literatura?",
            "answer": """As técnicas narrativas são recursos utilizados pelos escritores para contar suas histórias, influenciando diretamente a percepção do leitor e a construção do sentido da obra.

TIPOS DE NARRADOR:
• 1ª pessoa (protagonista): "Eu" conta sua própria história
• 1ª pessoa (testemunha): "Eu" narra história de outro
• 3ª pessoa (onisciente): sabe tudo sobre personagens
• 3ª pessoa (observador): limitado ao que vê
• Narrador não-confiável: versão questionável dos fatos

FOCO NARRATIVO:
• Interno: dentro da mente dos personagens
• Externo: observação de comportamentos
• Múltiplo: alternância entre diferentes perspectivas
• Câmera: registro objetivo sem interpretação

TEMPO NARRATIVO:
• Cronológico: sequência linear dos eventos
• Psicológico: tempo subjetivo da consciência
• Flashback: volta ao passado
• Fluxo de consciência: pensamentos livres

TÉCNICAS ESPECIAIS:
• Metalinguagem: narrativa que se discute
• Discurso indireto livre: fusão narrador/personagem
• Monólogo interior: pensamentos diretos
• Intertextualidade: diálogo com outras obras

EXEMPLOS BRASILEIROS:
• Dom Casmurro: narrador não-confiável
• Memórias Póstumas: narrador defunto
• O Cortiço: foco múltiplo
• Grande Sertão: monólogo

FUNÇÃO:
Essas técnicas determinam como a história é contada e interpretada, sendo essenciais para a análise literária.""",
            "category": "analysis"
        },
        {
            "question": "Quem foi Lima Barreto?",
            "answer": """Afonso Henriques de Lima Barreto (1881-1922) foi um escritor brasileiro do Pré-Modernismo, conhecido por sua crítica social contundente e por retratar a marginalização social no início do século XX.

BIOGRAFIA:
• Nascimento: 13 de maio de 1881, Rio de Janeiro
• Origem: família humilde, pai tipógrafo, descendente de escravos
• Formação: Escola Politécnica (não concluiu)
• Profissão: funcionário público, jornalista
• Problemas: alcoolismo, internações psiquiátricas
• Morte: 1º de novembro de 1922, Rio de Janeiro

CARACTERÍSTICAS LITERÁRIAS:
• Crítica social direta e militante
• Denúncia do preconceito racial
• Retrato da vida urbana carioca
• Linguagem simples e popular
• Ironia e humor amargo
• Protagonistas marginalizados

OBRAS PRINCIPAIS:
• "Triste Fim de Policarpo Quaresma": crítica ao nacionalismo ingênuo
• "O Cortiço": vida nos subúrbios cariocas
• "Recordações do Escrivão Isaías Caminha": semi-autobiográfica
• Contos: "Clara dos Anjos"

TEMAS CENTRAIS:
• Racismo e preconceito social
• Crítica à República Velha
• Modernização excludente do Rio
• Loucura e marginalização
• Burocracy e corrupção

IMPORTÂNCIA:
Lima Barreto antecipou temas do Modernismo, sendo precursor da literatura social brasileira. Sua obra denuncia as injustiças sociais com realismo cru e humanidade profunda.""",
            "category": "author"
        }
    ]

    # Executar adições
    results = []
    for i, item in enumerate(items_to_add, 4):
        print(f"\n📚 ITEM {i}/10 - {item['question'][:50]}...")
        try:
            result = training_service.add_knowledge(
                question=item['question'],
                answer=item['answer'],
                category=item['category'],
                source="expansion_literatura_brasileira_2025"
            )
            results.append(result)
            print(f"   ✅ Resultado: {result}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            results.append({'success': False, 'error': str(e)})

    # Resumo
    print("\n" + "=" * 60)
    print("📊 EXPANSÃO COMPLETA!")
    print("=" * 60)

    successful = sum(1 for r in results if r.get('success'))
    print(f"✅ Itens adicionados com sucesso: {successful}/7")
    print(f"❌ Falhas: {7 - successful}")

    # Status final
    print("\n📈 STATUS FINAL:")
    final_stats = training_service.get_knowledge_stats()
    print(f"   📚 Total de itens: {final_stats.get('total_items', 0)}")
    print(f"   ✅ Itens ativos: {final_stats.get('active_items', 0)}")
    print(f"   🧠 Com embeddings: {final_stats.get('with_embeddings', 0)}")
    print(f"   📂 Categorias: {final_stats.get('categories', {})}")

    expected_total = 6 + successful  # 6 existentes + novos
    actual_total = final_stats.get('active_items', 0)

    if actual_total >= expected_total:
        print(f"\n🎉 EXPANSÃO CONCLUÍDA COM SUCESSO!")
        print(f"📊 Base expandida de 6 para {actual_total} itens")
        print(f"🚀 Sistema híbrido com {actual_total} itens de conhecimento!")

        # Testar busca
        print(f"\n🧪 TESTE RÁPIDO DE BUSCA:")
        try:
            test_results = training_service.search_knowledge("José de Alencar", limit=3, threshold=0.3)
            print(f"   🔍 Busca 'José de Alencar': {len(test_results)} resultado(s)")
            for i, result in enumerate(test_results, 1):
                confidence = getattr(result, 'confidence', 0)
                question = getattr(result, 'question_found', 'N/A')
                print(f"     {i}. {question[:50]}... (conf: {confidence:.2f})")
        except Exception as e:
            print(f"   ❌ Erro na busca: {e}")

        return True
    else:
        print(f"\n⚠️ EXPANSÃO PARCIAL")
        print(f"📊 Esperado: {expected_total}, Atual: {actual_total}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)