# 🧪 Documentação de Testes - CG.BookStore.Online

**Projeto:** Sistema de Livraria Online com Chatbot Literário  
**Framework:** Django 4.x  
**Ambiente:** Python 3.x + PyCharm + PowerShell (Windows)

---

## 📋 Índice

1. [Configuração Inicial](#configuração-inicial)
2. [Tipos de Testes](#tipos-de-testes)
3. [Executando Testes](#executando-testes)
4. [Testes por Módulo](#testes-por-módulo)
5. [Scripts Utilitários](#scripts-utilitários)
6. [Troubleshooting](#troubleshooting)
7. [Boas Práticas](#boas-práticas)

---

## ⚙️ Configuração Inicial

### **Verificar Ambiente**
```powershell
# No terminal do PyCharm (PowerShell)
cd cgbookstore
python manage.py check
```

### **Configuração do Pytest** ✅
O projeto já possui configuração em `pytest.ini`:
```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = cgbookstore.config.settings
python_files = tests.py test_*.py *_tests.py
addopts = --tb=short --strict-markers
```

### **Instalar Dependências de Teste**
```powershell
pip install pytest-django pytest-cov
```

---

## 🎯 Tipos de Testes

### **1. Testes Unitários** (Django TestCase)
- Testam funcionalidades isoladas
- Localização: `*/tests/test_*.py`

### **2. Testes de Integração** (Pytest)
- Testam interação entre módulos
- Localização: `*/tests/test_integration.py`

### **3. Scripts de Verificação**
- Utilitários para debug e manutenção
- Localização: `/tests/*.py`

### **4. Testes de Performance**
- Benchmarks e análise de desempenho
- Localização: `*/tests/test_performance.py`

---

## 🚀 Executando Testes

### **Executar TODOS os Testes**
```powershell
# Usando Django (método padrão)
python manage.py test

# Usando Pytest (recomendado)
pytest

# Com coverage
pytest --cov=cgbookstore --cov-report=html
```

### **Executar Testes Específicos**

#### **Por Aplicação:**
```powershell
# Testes do Chatbot
python manage.py test cgbookstore.apps.chatbot_literario

# Testes do Core
python manage.py test cgbookstore.apps.core
```

#### **Por Arquivo:**
```powershell
# Teste específico do chatbot
pytest cgbookstore/apps/chatbot_literario/tests/test_chat_conversation.py

# Teste de recomendações
pytest cgbookstore/apps/core/recommendations/tests/test_engine.py
```

#### **Por Função:**
```powershell
# Função específica
pytest cgbookstore/apps/chatbot_literario/tests/test_chat_conversation.py::test_conversation_creation

# Com verbose
pytest -v cgbookstore/apps/core/recommendations/tests/test_api.py::test_api_endpoints
```

---

## 📂 Testes por Módulo

### **🤖 Chatbot Literário**

#### **Localização:**
- `cgbookstore/apps/chatbot_literario/tests/`

#### **Executar:**
```powershell
# Todos os testes do chatbot
pytest cgbookstore/apps/chatbot_literario/tests/

# Teste específico de conversação
pytest cgbookstore/apps/chatbot_literario/tests/test_chat_conversation.py -v

# Teste via management command
python manage.py test_chatbot --query "teste do sistema"
```

#### **Principais Testes:**
- ✅ `test_chat_conversation.py` - Conversações e mensagens
- ✅ Testes de treinamento e base de conhecimento
- ✅ Testes de embeddings e similarity

---

### **📚 Sistema de Recomendações**

#### **Localização:**
- `cgbookstore/apps/core/recommendations/tests/`

#### **Executar:**
```powershell
# Todos os testes de recomendação
pytest cgbookstore/apps/core/recommendations/tests/ -v

# Engine de recomendação
pytest cgbookstore/apps/core/recommendations/tests/test_engine.py

# API de recomendações
pytest cgbookstore/apps/core/recommendations/tests/test_api.py

# Performance
pytest cgbookstore/apps/core/recommendations/tests/test_performance.py
```

#### **Principais Testes:**
- ✅ `test_engine.py` - Motor de recomendações
- ✅ `test_api.py` - Endpoints da API
- ✅ `test_cache.py` - Sistema de cache
- ✅ `test_similarity_provider.py` - Algoritmos de similaridade
- ✅ `test_integration.py` - Testes integrados

---

### **🔧 Analytics**

#### **Localização:**
- `cgbookstore/apps/core/recommendations/analytics/tests/`

#### **Executar:**
```powershell
# Testes de analytics
pytest cgbookstore/apps/core/recommendations/analytics/tests/

# Geração de dados de teste
python manage.py generate_test_data

# Limpeza de dados de teste
python manage.py clean_test_data
```

---

## 🛠️ Scripts Utilitários

### **Localização:** `/tests/`

#### **Scripts de Verificação:**
```powershell
# Verificar banco de dados
python tests/check_database.py

# Verificar tabelas
python tests/listar_tabelas.py

# Verificar configuração SendGrid
python tests/check_sendgrid_config.py

# Teste de performance
python tests/test_performance.py
```

#### **Scripts de Manutenção:**
```powershell
# Backup SQLite
python tests/backup_sqlite.py

# Verificar PostgreSQL
python tests/verify_postgres.py

# Criar tipos de conteúdo
python tests/create_content_types.py
```

#### **Scripts de Ambiente:**
```powershell
# Testar variáveis de ambiente
python tests/test_env.py

# Criar arquivos .env
python tests/create_env_files.py
```

---

## 🎯 Comandos de Management

### **Chatbot:**
```powershell
# Debug do chatbot
python manage.py debug_chatbot --query "O Hobbit"

# Adicionar datas específicas
python manage.py add_specific_dates

# Testar chatbot
python manage.py test_chatbot

# Atualizar embeddings
python manage.py update_embeddings
```

### **Recomendações:**
```powershell
# Benchmark de recomendações
python manage.py benchmark_recommendations

# Gerar dados de teste para analytics
python manage.py generate_test_data

# Limpar dados de teste
python manage.py clean_test_data
```

### **Sistema:**
```powershell
# Gerar estrutura do projeto
python manage.py generate_project_structure

# Gerar tabelas do banco
python manage.py generate_tables

# Criar perfis padrão
python manage.py create_profiles
```

---

## 🐛 Troubleshooting

### **Problemas Comuns:**

#### **1. Erro de Database Lock (SQLite)**
```powershell
# Parar o servidor
Ctrl+C

# Executar testes
python manage.py test

# Reiniciar servidor
python manage.py runserver
```

#### **2. Imports não Encontrados**
```powershell
# Verificar PYTHONPATH
echo $env:PYTHONPATH

# Executar do diretório correto
cd cgbookstore
python manage.py test
```

#### **3. Dependências Faltando**
```powershell
# Instalar requirements
pip install -r requirements.txt

# Verificar instalação
pip list
```

#### **4. Problema com Migrações**
```powershell
# Aplicar migrações antes dos testes
python manage.py migrate

# Verificar status
python manage.py showmigrations
```

---

## 📊 Executando com Coverage

### **Coverage Básico:**
```powershell
# Instalar coverage
pip install coverage

# Executar com coverage
coverage run --source='.' manage.py test

# Gerar relatório
coverage report

# Relatório HTML
coverage html
```

### **Coverage Avançado:**
```powershell
# Coverage específico por app
coverage run --source='cgbookstore.apps.chatbot_literario' manage.py test chatbot_literario

# Coverage de performance
pytest --cov=cgbookstore --cov-report=term-missing

# Relatório detalhado
coverage report --show-missing
```

---

## ✅ Boas Práticas

### **Antes de Executar Testes:**
1. **Verificar migrações:** `python manage.py migrate`
2. **Ativar ambiente virtual:** Sempre usar `.venv1`
3. **Verificar configurações:** `python manage.py check`
4. **Parar servidor:** Se rodando em desenvolvimento

### **Executando Testes:**
1. **Começar com smoke tests:** Testes básicos primeiro
2. **Executar por módulo:** Isoladamente para debug
3. **Usar verbose:** `-v` para output detalhado
4. **Monitorar tempo:** Identificar testes lentos

### **Após os Testes:**
1. **Revisar cobertura:** Identificar código não testado
2. **Verificar logs:** Procurar warnings ou erros
3. **Limpar dados de teste:** Se necessário
4. **Documentar falhas:** Para correção posterior

---

## 🎛️ Comandos Úteis do PyCharm

### **Terminal Integrado:**
```powershell
# Navegar para o projeto
cd cgbookstore

# Ativar ambiente virtual (se não ativo)
.\.venv1\Scripts\Activate.ps1

# Executar testes com output colorido
python -m pytest --color=yes
```

### **Configuração do PyCharm:**
1. **Run/Debug Configurations** → **Django Tests**
2. **Environment Variables** → Configurar variáveis necessárias
3. **Python Interpreter** → Selecionar `.venv1`

---

## 📈 Monitoramento e Logs

### **Logs de Teste:**
```powershell
# Executar com logs detalhados
python manage.py test --verbosity=2

# Logs específicos do chatbot
python manage.py test chatbot_literario --debug-mode

# Capturar output em arquivo
python manage.py test > test_results.txt 2>&1
```

### **Debugging:**
```powershell
# Executar com PDB
python manage.py test --pdb

# Debug específico
pytest --pdb cgbookstore/apps/chatbot_literario/tests/
```

---

## 🚀 Integração Contínua (CI/CD)

### **Preparação para CI:**
```powershell
# Testar em ambiente limpo
python -m venv test_env
test_env\Scripts\activate
pip install -r requirements.txt
python manage.py test
```

### **Scripts de Automação:**
```powershell
# Criar script de teste completo
# test_all.ps1
python manage.py migrate
python manage.py test
pytest --cov=cgbookstore
coverage report
```

---

## 📞 Suporte

### **Em caso de problemas:**
1. Verificar logs em `cgbookstore/debug.log`
2. Executar `python manage.py check --deploy`
3. Consultar documentação específica de cada módulo
4. Usar comandos de debug específicos do projeto

### **Comandos de Diagnóstico:**
```powershell
# Status do sistema
python manage.py comprehensive_chatbot_fix

# Verificar estrutura
python tests/check_project_paths.py

# Status das tabelas
python tests/check_table_names.py
```

---

*Documentação atualizada em: Junho 2025*  
*Projeto: CG.BookStore.Online*