# Instruções para Correção do Chatbot

## 1. Aplicar as Correções no chatbot_service.py

### Passo 1: Adicionar novos métodos na classe ConversationContext

Localize a classe `ConversationContext` no arquivo `chatbot_service.py` e adicione estes métodos após o método `get_last_mentioned_book()`:

```python
def should_clear_context(self, message):
    # Código fornecido no arquivo de correções
    
def _extract_entities_preview(self, message):
    # Código fornecido no arquivo de correções
```

### Passo 2: Substituir métodos na classe ChatbotService

Substitua os seguintes métodos pelos fornecidos no arquivo de correções:

1. `_is_contextual_question()`
2. `_answer_contextual_question()`
3. `_load_intent_patterns()`
4. `get_response()`

## 2. Adicionar Conhecimento de Ajuda

Execute o comando para popular a base com respostas sobre as capacidades do chatbot:

```bash
python manage.py add_help_knowledge
```

## 3. Atualizar Embeddings (Opcional mas Recomendado)

Se você tem o modelo de embeddings instalado:

```bash
python manage.py fix_knowledge_base --update-embeddings
```

## 4. Testar as Correções

### Teste Rápido
```bash
python manage.py test_chatbot --scenario basic
```

### Teste Completo
```bash
python manage.py test_chatbot
```

### Teste Interativo
```bash
python manage.py test_chatbot --interactive
```

## 5. Verificar Melhorias Esperadas

Após aplicar as correções, você deve observar:

✅ **Pergunta "O que você pode fazer?"** - Agora retorna uma resposta detalhada
✅ **Contexto mais inteligente** - Não mistura informações de livros diferentes
✅ **Menos fallbacks** - Threshold ajustado para melhor cobertura
✅ **Detecção de mudança de tópico** - Limpa contexto quando necessário
✅ **Respostas contextuais corretas** - "Quem escreveu?" se refere ao livro correto

## 6. Problemas Comuns e Soluções

### Problema: ImportError ou ModuleNotFoundError
**Solução**: Verifique se todos os imports estão corretos no início do arquivo

### Problema: Ainda muitos fallbacks
**Solução**: 
1. Verifique se a base de conhecimento foi populada
2. Execute: `python manage.py populate_knowledge_base`
3. Adicione conhecimento específico do seu domínio

### Problema: Contexto ainda confuso
**Solução**: 
1. Verifique se o método `should_clear_context` foi adicionado corretamente
2. Teste com `python manage.py test_chatbot --scenario context`

## 7. Logs para Debug

Para ativar logs detalhados, adicione no seu settings.py:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
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

## 8. Validação Final

Execute este teste para validar todas as correções:

```python
# No modo interativo, teste estas sequências:

# Teste 1: Capacidades
"O que você pode fazer?"
# Deve retornar lista detalhada de capacidades

# Teste 2: Mudança de contexto
"Quem escreveu O Senhor dos Anéis?"
"E quando foi publicado?"
"Quem escreveu Dom Casmurro?"  # Mudança de contexto
"E quando foi publicado?"  # Deve se referir a Dom Casmurro

# Teste 3: Recomendações
"Pode me recomendar livros de fantasia?"
# Deve retornar lista de recomendações

# Teste 4: Navegação
"Como adiciono um livro ao carrinho?"
# Deve retornar instruções passo a passo
```

## 9. Próximos Passos (Opcional)

1. **Adicionar mais conhecimento específico do seu catálogo**:
   ```bash
   python manage.py populate_knowledge_base
   ```

2. **Treinar com conversas reais**:
   - Exporte conversas: `python manage.py export_chatbot_data`
   - Analise padrões de perguntas não respondidas
   - Adicione conhecimento específico

3. **Melhorar a qualidade das respostas**:
   - Revise e edite respostas na base de conhecimento via admin
   - Adicione variações de perguntas para o mesmo conhecimento

## Resultado Esperado

Após implementar todas as correções, o chatbot deve:

- ✅ Responder corretamente sobre suas capacidades
- ✅ Manter contexto sem confundir informações
- ✅ Ter menos respostas de fallback
- ✅ Responder perguntas contextuais corretamente
- ✅ Detectar e adaptar-se a mudanças de tópico

Se algum problema persistir, verifique os logs de debug para mais informações.