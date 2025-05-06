# Implementação de Seções Personalizadas com Layouts Dinâmicos

## Visão Geral do Projeto

Esta implementação visa melhorar a flexibilidade da página inicial do CGBookstore, permitindo que o administrador crie e gerencie seções personalizadas com diferentes tipos de conteúdo e layouts, sem a necessidade de modificar o código a cada nova necessidade.

O sistema permitirá:
1. Criar diferentes tipos de seções personalizadas (eventos, parceiros, depoimentos, etc.)
2. Selecionar layouts específicos para cada tipo de seção
3. Adicionar e gerenciar o conteúdo correspondente
4. Exibir esse conteúdo na página inicial de acordo com o layout escolhido

## Arquivos Envolvidos na Implementação

### Arquivos a Modificar

1. **cgbookstore/apps/core/models/home_content.py**
   - Adicionar modelos `CustomSectionType`, `CustomSectionLayout`, `CustomSection` e `EventItem`
   - Implementar relacionamentos e validações necessárias

2. **cgbookstore/apps/core/admin.py**
   - Registrar novos modelos no painel administrativo
   - Criar classes Admin com interfaces amigáveis para gestão
   - Implementar filtros e ações para facilitar o gerenciamento

3. **cgbookstore/apps/core/views/general.py**
   - Modificar `IndexView.get_context_data()` para processar seções personalizadas
   - Implementar a lógica para carregar o template correto conforme o layout selecionado

4. **cgbookstore/apps/core/templates/core/home.html**
   - Atualizar para renderizar seções personalizadas de acordo com seus layouts

### Novos Arquivos a Criar

1. **Templates para layouts de eventos**
   - `cgbookstore/apps/core/templates/core/layouts/eventos_agenda.html`
   - `cgbookstore/apps/core/templates/core/layouts/eventos_cards.html`
   - `cgbookstore/apps/core/templates/core/layouts/eventos_destaque.html`

2. **Estilos CSS para os novos layouts**
   - `static/css/custom_sections.css`

3. **JavaScript (se necessário)**
   - `static/js/custom_sections.js`

## Funcionalidades a Implementar

1. **Sistema de Tipos de Seção Personalizados**
   - Modelo para armazenar tipos predefinidos (eventos, parceiros, etc.)
   - Interface administrativa para gerenciar esses tipos

2. **Sistema de Layouts**
   - Modelo para definir layouts disponíveis para cada tipo de seção
   - Associação entre tipos de seção e layouts compatíveis

3. **Seções Personalizadas**
   - Conexão entre as seções da home e o sistema personalizado
   - Seleção de tipo e layout via dropdown no admin

4. **Gerenciamento de Conteúdo**
   - Interface para adicionar/editar/remover itens de cada seção
   - Validações específicas para cada tipo de conteúdo

5. **Renderização Dinâmica**
   - Sistema para carregar o template correto baseado no layout selecionado
   - Passagem do conteúdo apropriado para o template

## Implementação Inicial: Eventos Literários

Como prova de conceito, implementaremos primeiro o tipo "Eventos Literários" com três layouts diferentes:

1. **Agenda (Linha do Tempo)**
   - Exibição cronológica dos eventos
   - Formato visual de timeline

2. **Cards**
   - Exibição em formato de cards com imagem, título e descrição
   - Layout responsivo em grid

3. **Destaque**
   - Destaque para um evento principal
   - Exibição dos demais eventos em formato secundário

## Relação com Documentos Analisados

Esta implementação é baseada na análise dos seguintes documentos:

1. **structure-01-03-2025.txt**
   - Mostra a estrutura atual do projeto
   - Identificamos os arquivos que precisam ser modificados

2. **projeto-CGV_BookStore_V.2.md**
   - Destaca a visão de crescimento e expansão comercial
   - Menciona "Eventos online" como parte da visão de futuro

3. **Manual_do_Usuário_Administrador.md**
   - Revela o funcionamento atual do sistema de administração
   - Mostra como o gerenciamento de conteúdo é realizado

4. **home_content.py**
   - Contém a estrutura atual dos modelos relacionados à página inicial
   - Modelo base para as modificações propostas

5. **home.html**
   - Template atual da página inicial
   - Base para implementação da renderização dinâmica

6. **general.py**
   - View responsável pela página inicial
   - Contém a lógica que precisará ser estendida

7. **admin.py**
   - Configuração atual do painel administrativo
   - Base para as novas interfaces de administração

## Próximos Passos

1. Implementar os modelos necessários em `home_content.py`
2. Registrar os modelos no `admin.py`
3. Criar os templates para os layouts de eventos
4. Atualizar a view para processar as seções personalizadas
5. Testar a implementação com a criação de eventos literários

## Expansões Futuras

Após o sucesso da implementação inicial, podemos facilmente expandir o sistema para incluir novos tipos de seção como:

1. Parceiros e Livrarias
2. Depoimentos de Usuários
3. Blog/Notícias
4. Planos e Assinaturas
5. Coleções Temáticas
6. Rankings e Listas

Cada um desses tipos poderia ter seus próprios layouts específicos, todos gerenciáveis através do painel administrativo sem necessidade de alterações no código.
