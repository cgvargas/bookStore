## 📚 **Informações sobre Treinamento e Base de Dados**

### 🗄️ **Base de Dados Atual:**

#### **Estrutura da Base de Conhecimento:**
- **Modelo:** `KnowledgeItem` 
- **Localização:** `cgbookstore/apps/chatbot_literario/models.py`
- **Campos:**
  - `question` - Pergunta/entrada do usuário
  - `answer` - Resposta do chatbot
  - `category` - Categoria (Literatura, Navegação, etc.)
  - `source` - Origem dos dados
  - `active` - Se o item está ativo
  - `embedding` - Vetor de embedding para busca semântica

#### **Estado Atual (após limpeza):**
- **~233 itens ativos** (após remoção de 147 dados contaminados)
- **32 itens novos** adicionados via `rebuild_knowledge_base`
- **Embeddings atualizados** e sincronizados

---

### 🧠 **Sistema de Treinamento:**

#### **Modelo de Embeddings:**
- **Modelo:** `all-MiniLM-L6-v2` (Sentence Transformers)
- **Dimensões:** 384 dimensões por embedding
- **Função:** Converter texto em vetores para busca semântica

#### **Pipeline de Busca:**
```python
1. Normalização da mensagem
2. Extração de entidades (livros, autores)
3. Busca por mapeamento direto (conhecimento embutido)
4. Busca semântica na base (se necessário)
5. Ajuste de score contextual
6. Retorno da melhor resposta
```

---

### 🎯 **Como Adicionar Novos Dados:**

#### **1. Via Interface Admin:**
- **URL:** `/admin/chatbot/treinamento/`
- **Funcionalidade:** Adicionar itens manualmente
- **Campos:** Pergunta, Resposta, Categoria, Fonte

#### **2. Via Comando de Management:**
```powershell
# Reconstruir base completa
python manage.py rebuild_knowledge_base

# Adicionar dados específicos
python manage.py populate_knowledge_base
```

#### **3. Via Importação de Arquivos:**
- **Formatos:** CSV, JSON
- **Interface:** Admin → Importar Conhecimento
- **Estrutura CSV:**
  ```csv
  question,answer,category,source
  "Quem escreveu Dom Casmurro?","Machado de Assis","Literatura Brasileira","manual"
  ```

---

### 🔧 **Comandos de Manutenção:**

#### **Embeddings:**
```powershell
# Atualizar embeddings
python manage.py update_embeddings

# Verificar estatísticas
python manage.py verify_chatbot_version
```

#### **Limpeza:**
```powershell
# Limpeza direcionada
python manage.py clean_contaminated_data

# Backup antes da limpeza
python manage.py clean_contaminated_data --dry-run
```

#### **Debug:**
```powershell
# Testar consultas específicas
python manage.py debug_chatbot --query "Harry Potter"

# Verificar contexto
python manage.py verify_chatbot_version --verbose
```

---

### 📊 **Estatísticas e Monitoramento:**

#### **Interface de Estatísticas:**
- **URL:** `/admin/chatbot/treinamento/statistics/`
- **Métricas:**
  - Total de itens na base
  - Distribuição por categoria
  - Itens adicionados recentemente
  - Conversas por dia
  - Feedback positivo/negativo

#### **Categorias Atuais:**
- **Literatura:** Livros e autores clássicos
- **Autores:** Informações biográficas
- **Navegação:** Como usar o site
- **Recomendações:** Sugestões de leitura
- **Ajuda:** Suporte e orientações
- **Perfil:** Gestão de conta

---

### 🎯 **Estratégias de Treinamento:**

#### **1. Dados Estruturados (Atual):**
- ✅ **Vantagens:** Controle total, dados limpos
- ✅ **Uso:** Conhecimento específico do domínio
- **Exemplo:** Mapeamento Harry Potter → J.K. Rowling

#### **2. Aprendizado por Conversas:**
- **Funcionalidade:** Adicionar conversas reais à base
- **Interface:** Admin → Adicionar da Conversa
- **Processo:** Moderação → Aprovação → Inclusão

#### **3. Importação de Catálogo:**
- **Fonte:** Base de livros existente
- **Automatização:** Script para converter dados do catálogo
- **Comando potencial:** `python manage.py import_catalog_data`

---

### 🚀 **Melhorias Possíveis:**

#### **Curto Prazo:**
1. **Expandir mapeamentos diretos** (mais autores/livros)
2. **Adicionar sinônimos** (Tolkien = J.R.R. Tolkien)
3. **Categorizar melhor** por gêneros literários

#### **Médio Prazo:**
1. **Integração com catálogo** do site
2. **Aprendizado automático** de conversas
3. **Feedback loop** para melhorias

#### **Longo Prazo:**
1. **Modelo customizado** treinado no domínio
2. **RAG avançado** com múltiplas fontes
3. **Personalização** por usuário

---

### 💡 **Boas Práticas Implementadas:**

#### **Qualidade dos Dados:**
- ✅ Validação de duplicatas
- ✅ Categorização consistente
- ✅ Fonte rastreável
- ✅ Versionamento via timestamps

#### **Performance:**
- ✅ Cache de embeddings
- ✅ Busca otimizada por score
- ✅ Fallbacks inteligentes
- ✅ Contexto preservado

#### **Manutenibilidade:**
- ✅ Paradigma funcional
- ✅ Logs detalhados
- ✅ Comandos de debug
- ✅ Interface administrativa

---

### CGVargas Informática - CG.BookStore.Online 