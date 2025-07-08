# Guia de Teste do Chatbot Literário

Este guia fornece instruções para testar o funcionamento do chatbot literário.

## Pré-requisitos

1. **Ambiente Django configurado e ativo**
2. **Dependências instaladas** (especialmente `colorama` para cores no terminal):
   ```bash
   pip install colorama
   ```

## Preparação da Base de Conhecimento

Antes de testar o chatbot, é necessário popular a base de conhecimento:

### Opção 1: Popular com dados do sistema
```bash
python manage.py populate_knowledge_base
```

### Opção 2: Popular com dados de exemplo (JSON)
```bash
python manage.py populate_knowledge_base --json cgbookstore/apps/chatbot_literario/fixtures/sample_knowledge.json
```

### Opção 3: Popular com dados externos
```bash
# Com arquivo CSV
python manage.py populate_knowledge_base --csv caminho/para/arquivo.csv

# Com arquivo JSON
python manage.py populate_knowledge_base --json caminho/para/arquivo.json
```

## Testando o Chatbot

### 1. Modo de Teste Automático (Todos os Cenários)
```bash
python manage.py test_chatbot
```

### 2. Cenários Específicos
```bash
# Testar apenas conversação básica
python manage.py test_chatbot --scenario basic

# Testar apenas consultas sobre livros
python manage.py test_chatbot --scenario books

# Testar apenas navegação no site
python manage.py test_chatbot --scenario navigation

# Testar apenas perguntas contextuais
python manage.py test_chatbot --scenario context
```

### 3. Modo Interativo
```bash
python manage.py test_chatbot --interactive
```

No modo interativo:
- Digite suas mensagens e pressione Enter
- Digite `limpar` para limpar o contexto da conversa
- Digite `sair` para encerrar

### 4. Teste com Usuário Específico
```bash
# Teste automático com usuário
python manage.py test_chatbot --user nome_usuario

# Modo interativo com usuário
python manage.py test_chatbot --interactive --user nome_usuario
```

## Exemplos de Perguntas para Testar

### Perguntas sobre Livros
- "Quem escreveu O Senhor dos Anéis?"
- "Quando foi publicado 1984?"
- "Me fale sobre Dom Casmurro"
- "Quais livros George Orwell escreveu?"

### Perguntas Contextuais
- "Fale sobre O Hobbit"
- "Quem escreveu?" (referindo-se ao livro anterior)
- "E quando foi publicado?"
- "O autor escreveu outros livros?"

### Navegação no Site
- "Como encontro meus livros favoritos?"
- "Onde vejo os livros que estou lendo?"
- "Como adiciono um livro ao carrinho?"
- "Como faço para avaliar um livro?"

### Recomendações
- "Pode me recomendar livros de fantasia?"
- "Quais são os livros mais populares?"
- "Quero um livro de ficção científica"

## Verificando a Base de Conhecimento

### Ver estatísticas da base
```bash
python manage.py fix_knowledge_base --fix-all
```

### Corrigir problemas de embeddings
```bash
python manage.py fix_knowledge_base --convert-embeddings --update-embeddings
```

## Estrutura de Arquivos CSV para Importação

Se você quiser criar um arquivo CSV para importar conhecimento adicional:

```csv
question,answer,category,source
"Quem escreveu Memórias Póstumas de Brás Cubas?","Machado de Assis escreveu Memórias Póstumas de Brás Cubas, publicado em 1881.","autores","manual"
"O que é um e-book?","Um e-book é um livro em formato digital que pode ser lido em dispositivos eletrônicos como tablets, e-readers e smartphones.","tecnologia","manual"
```

## Estrutura de Arquivos JSON para Importação

Exemplo de arquivo JSON para importar conhecimento:

```json
[
    {
        "question": "Quem é Clarice Lispector?",
        "answer": "Clarice Lispector foi uma das mais importantes escritoras brasileiras do século XX.",
        "category": "autores",
        "source": "manual"
    },
    {
        "question": "Como criar uma conta no site?",
        "answer": "Para criar uma conta, clique em 'Registrar' no canto superior direito e preencha o formulário.",
        "category": "navegacao",
        "source": "manual"
    }
]
```

## Troubleshooting

### Erro: "Base de conhecimento vazia!"
Execute o comando `populate_knowledge_base` antes de testar.

### Erro: "ModuleNotFoundError: No module named 'colorama'"
Instale o colorama: `pip install colorama`

### Chatbot não encontra respostas
1. Verifique se a base de conhecimento foi populada
2. Tente reformular a pergunta
3. Verifique os logs para mais detalhes

### Problemas com contexto
Use o comando `limpar` no modo interativo ou chame `chatbot.clear_user_context(user)` programaticamente.

## Logs e Debug

Para ver logs detalhados durante os testes, configure o nível de log no settings.py:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'cgbookstore.apps.chatbot_literario': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```