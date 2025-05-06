# Manual do Usuário Administrador: CGBookstore

## Índice
1. [Introdução ao Painel Administrativo](#1-introdução-ao-painel-administrativo)
2. [Gerenciamento de Livros](#2-gerenciamento-de-livros)
3. [Sistema de Prateleiras](#3-sistema-de-prateleiras)
4. [Criação Rápida de Prateleira](#4-criação-rápida-de-prateleira)
5. [Gerenciamento Visual de Prateleiras](#5-gerenciamento-visual-de-prateleiras)
6. [Administração de Usuários](#6-administração-de-usuários)
7. [Ferramentas do Sistema](#7-ferramentas-do-sistema)
8. [Solução de Problemas Comuns](#8-solução-de-problemas-comuns)

## 1. Introdução ao Painel Administrativo

### 1.1 Acessando o Painel
Para acessar o painel administrativo do CGBookstore, navegue até:
```
http://[seu-domínio]/admin/
```

Entre com seu nome de usuário e senha de administrador. Se você não lembra suas credenciais, entre em contato com o administrador do sistema.

### 1.2 Visão Geral
Após o login, você verá o painel principal dividido em duas seções principais:
- **Autenticação e Autorização**: Gerenciamento de usuários e permissões
- **Core**: Gerenciamento de conteúdo do site (livros, prateleiras, banners, etc.)

### 1.3 Interface
A interface administrativa está dividida em:
- **Barra lateral**: Mostra todas as seções e modelos disponíveis
- **Área de conteúdo**: Mostra os detalhes do item selecionado
- **Barra superior**: Fornece acesso rápido às ferramentas e opções do sistema

## 2. Gerenciamento de Livros

### 2.1 Acessando a Lista de Livros
Clique em "Livros" no menu Core para acessar a lista completa de livros cadastrados.

### 2.2 Adicionando um Novo Livro
1. Clique no botão "ADICIONAR" ao lado de "Livros"
2. Preencha todos os campos do formulário
3. Para adicionar uma imagem de capa, clique em "Escolher arquivo" no campo "Capa"
4. Selecione uma imagem do seu computador (tamanho recomendado: 400x600px)
5. Clique em "SALVAR" para finalizar

### 2.3 Campos Importantes
- **Título**: Nome do livro (obrigatório)
- **Autor**: Nome do autor (obrigatório)
- **Capa**: Imagem da capa do livro
- **Tipo de prateleira especial**: Define a prateleira onde o livro aparecerá

### 2.4 Categorização do Livro
Na seção "Configurações da Home", você pode definir como o livro aparecerá na página inicial:
- **É lançamento**: Marca o livro como lançamento
- **Em destaque**: Destaca o livro na página principal
- **Adaptado para filme/série**: Marca para aparecer na prateleira de livros adaptados
- **É mangá**: Marca como mangá
- **Tipo de prateleira especial**: Seleciona uma prateleira específica
- **Ordem de exibição**: Define a ordem de exibição dentro da prateleira

## 3. Sistema de Prateleiras

### 3.1 Conceitos Básicos
O sistema de prateleiras é composto por três elementos principais:
- **Tipos de Prateleiras Padrão (DefaultShelfType)**: Define as regras de filtragem dos livros
- **Seções da Home (HomeSection)**: Define onde a prateleira aparece na página inicial
- **Prateleiras de Livros (BookShelfSection)**: Conecta um tipo de prateleira a uma seção

### 3.2 Tipos de Prateleiras Padrão
Para acessar, clique em "Tipos de Prateleiras Padrão" no menu Core.

#### Adicionando um Novo Tipo de Prateleira
1. Clique em "ADICIONAR"
2. Preencha os campos:
   - **Nome**: Nome da prateleira (ex: "Mais Vendidos")
   - **Identificador**: Identificador único (ex: "mais_vendidos")
   - **Campo do Filtro**: Critério para selecionar livros
   - **Valor do Filtro**: Valor para o filtro escolhido
   - **Ordem**: Posição de exibição
   - **Ativo**: Marque para tornar visível

### 3.3 Seções da Home
Para acessar, clique em "Seções da Home" no menu Core.

#### Adicionando uma Nova Seção
1. Clique em "ADICIONAR"
2. Preencha os campos:
   - **Título**: Título da seção
   - **Tipo**: Selecione "shelf" para prateleiras de livros
   - **Ordem**: Posição na página inicial
   - **Ativo**: Marque para tornar visível

### 3.4 Prateleiras de Livros
Para acessar, clique em "Prateleiras de Livros" no menu Core.

#### Adicionando uma Nova Prateleira
1. Clique em "ADICIONAR"
2. Preencha os campos:
   - **Seção**: Selecione a seção da home
   - **Tipo de Prateleira**: Selecione o tipo de prateleira
   - **Máximo de Livros**: Número máximo de livros a exibir

## 4. Criação Rápida de Prateleira

A função de Criação Rápida permite criar todos os elementos necessários (tipo, seção e prateleira) em um único passo.

### 4.1 Acessando a Criação Rápida
1. Vá para "Gerenciamento de Prateleiras" nas ferramentas do sistema
2. Clique no botão "Nova Prateleira"

### 4.2 Preenchendo o Formulário
1. **Informações Básicas**:
   - **Nome da Prateleira**: Nome que será exibido na página inicial
   - **Identificador**: Código único (gerado automaticamente se não informado)
   - **Ativo**: Marque para tornar visível

2. **Configurações de Filtro**:
   - **Campo do Filtro**: Selecione o critério para filtrar livros
   - **Valor do Filtro**: Informe o valor para o filtro (necessário apenas para alguns tipos)

3. **Exibição**:
   - **Ordem de Exibição**: Posição na página inicial
   - **Máximo de Livros**: Número máximo de livros a serem exibidos

4. Clique em "Criar Prateleira" para finalizar

### 4.3 Importante
- Cada tipo de prateleira precisa de um identificador único
- Para prateleiras baseadas em "Tipo de Prateleira Especial", o identificador será usado como valor do filtro automaticamente

## 5. Gerenciamento Visual de Prateleiras

O Gerenciador Visual permite arrastar e soltar livros entre prateleiras, proporcionando uma experiência mais intuitiva.

### 5.1 Acessando o Gerenciador Visual
1. Vá para "Gerenciamento de Prateleiras" nas ferramentas do sistema
2. Clique no botão "Gerenciador Visual"

### 5.2 Interface
- **Painel Esquerdo**: Mostra todas as prateleiras existentes e seus livros
- **Painel Direito**: Mostra livros não associados a nenhuma prateleira

### 5.3 Operações Principais
- **Adicionar Livro**: Arraste um livro do painel direito para a prateleira desejada
- **Remover Livro**: Clique no botão "X" ao lado do livro ou arraste-o para o painel direito
- **Reordenar Livros**: Arraste os livros dentro da mesma prateleira para alterá-los de posição

### 5.4 Buscas
- Use a caixa de busca no topo para filtrar prateleiras
- Use a caixa de busca no painel direito para filtrar livros disponíveis

## 6. Administração de Usuários

### 6.1 Acessando Usuários
Clique em "Usuários" no menu Autenticação e Autorização.

### 6.2 Adicionando Novo Usuário
1. Clique em "ADICIONAR"
2. Preencha os campos obrigatórios:
   - **Nome de usuário**
   - **Senha**
   - **Confirmação de senha**
3. Defina permissões conforme necessário
4. Clique em "SALVAR"

### 6.3 Permissões
Para dar a um usuário permissões administrativas:
1. Marque "Status de equipe" para acesso ao painel administrativo
2. Marque "Status de superusuário" para acesso completo
3. Ou selecione permissões específicas na lista de permissões disponíveis

## 7. Ferramentas do Sistema

### 7.1 Gerenciamento de Prateleiras
Ferramenta central para visualizar e gerenciar todas as prateleiras do sistema.

### 7.2 Outras Ferramentas
- **Gerar Schema do Banco**: Gera documentação do banco de dados
- **Gerar Estrutura do Projeto**: Documenta a estrutura do projeto
- **Visualizar Banco de Dados**: Fornece uma visão completa dos dados
- **Dashboard de Analytics**: Mostra estatísticas de uso
- **Configurar Modalidades de Livros**: Define configurações para tipos de livros

## 8. Solução de Problemas Comuns

### 8.1 Problemas de Permissão
Se você vir a mensagem "Você não tem permissão para ver ou editar nada":
1. Verifique se você está logado como administrador
2. Confirme se sua conta tem:
   - Status de equipe ativado
   - Status de superusuário OU permissões específicas necessárias
3. Peça ao administrador principal para verificar suas permissões

### 8.2 Livros Não Aparecem nas Prateleiras
Se os livros não estão aparecendo nas prateleiras:
1. Verifique se o tipo de prateleira está configurado corretamente
2. Confirme se a seção da home está ativa
3. Verifique se o livro tem o "Tipo de prateleira especial" correto
4. Certifique-se de que o livro está marcado como ativo

### 8.3 Duplicação de Título na Criação Rápida de Prateleira
Se os títulos aparecerem duplicados na tela de criação rápida:
1. Isso é um problema de exibição e não afeta a funcionalidade
2. Prossiga normalmente com o preenchimento do formulário

### 8.4 Upload de Imagem Falha
Se o upload de imagem não funcionar:
1. Verifique o tamanho do arquivo (limite geralmente é 5MB)
2. Certifique-se de que o formato é suportado (JPEG, PNG, GIF)
3. Verifique se as pastas de mídia têm permissões de escrita

### 8.5 Contato para Suporte
Em caso de problemas persistentes, entre em contato com o suporte técnico através do email: [endereço de email de suporte].

---

Este manual foi desenvolvido para ajudar administradores do sistema CGBookstore a gerenciar eficientemente o conteúdo do site, com foco especial no sistema de prateleiras. Para informações adicionais, consulte a documentação técnica completa do sistema.