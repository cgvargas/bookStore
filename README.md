# 📚 CG.BookStore Online - Sua Estante Virtual Inteligente

![Status do Projeto](https://img.shields.io/badge/status-em%20desenvolvimento-yellowgreen)
![Linguagem](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Framework](https://img.shields.io/badge/Django-4.2+-green.svg)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-MIT-blue)

CG.BookStore Online é uma plataforma web robusta e moderna para amantes de livros, construída com Django. Mais do que um simples catálogo, o projeto se destaca por ser uma ferramenta de engajamento para leitores, oferecendo uma experiência rica e personalizada através de funcionalidades avançadas como um sistema de recomendações adaptativo e um chatbot literário alimentado por Inteligência Artificial.

---

## ✨ Principais Funcionalidades

-   **📚 Gestão de Estantes Virtuais:** Crie e gerencie estantes personalizadas como "Lendo", "Quero Ler", "Lidos" e "Abandonados".
-   **🤖 Chatbot Literário com IA:** Converse com um assistente inteligente que conhece os livros do catálogo, responde a perguntas contextuais e ajuda a descobrir novas obras. Integração com **Ollama** para processamento de linguagem natural local.
-   **🧠 Sistema de Recomendações Adaptativo:** Receba sugestões de leitura personalizadas com base no seu histórico, livros favoritos e interações na plataforma.
-   **👤 Perfis de Leitor Personalizáveis:** Customize seu perfil com temas, estatísticas de leitura, conquistas e citações favoritas.
-   **⚙️ Painel de Administração Avançado:** Um painel de controle poderoso que vai além do Django Admin padrão, incluindo uma interface de treinamento para o chatbot e um dashboard de diagnósticos do sistema.
-   **🔍 Busca Inteligente:** Encontre livros e autores de forma rápida e eficiente, com suporte a Full-Text Search para resultados mais relevantes (em PostgreSQL).
-   **⚡ Cache Otimizado com Redis:** Performance aprimorada através do uso de Redis para cache de recomendações, sessões e outras consultas frequentes.

---

## 📸 Screenshots

*(Recomendação: Substitua os links abaixo por screenshots reais do seu projeto para um grande impacto visual!)*

| Tela Principal                                       | Perfil do Leitor                                   | Chatbot em Ação                                     |
| ------------------------------------------------------ | -------------------------------------------------- | --------------------------------------------------- |
| ![Tela Principal](https://via.placeholder.com/400x250) | ![Perfil](https://via.placeholder.com/400x250)     | ![Chatbot](https://via.placeholder.com/400x250)     |

---

## 🛠️ Tecnologias Utilizadas

Este projeto foi construído com as seguintes tecnologias:

-   **Backend:** Python, Django
-   **Banco de Dados:** PostgreSQL (produção) / SQLite3 (desenvolvimento)
-   **Inteligência Artificial:** Ollama (para o Chatbot)
-   **Cache:** Redis
-   **Frontend:** HTML5, CSS3, JavaScript
-   **Testes:** Pytest

---

## 🚀 Como Começar

Siga os passos abaixo para configurar e rodar o projeto em seu ambiente local.

### Pré-requisitos

-   Python 3.11+
-   Git
-   Ollama instalado e rodando (para a funcionalidade completa do chatbot)
-   Redis instalado e rodando (para cache)

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/cgvargas/bookStore.git
    cd bookStore
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv .venv
    # No Windows
    .\.venv\Scripts\activate
    # No macOS/Linux
    source .venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**
    -   Copie o arquivo de exemplo: `cp .env.example .env.dev`
    -   Abra o arquivo `.env.dev` e preencha as variáveis necessárias (chave secreta, configurações de banco de dados, Redis, etc.).

5.  **Aplique as migrações do banco de dados:**
    ```bash
    python manage.py migrate
    ```

6.  **Crie um superusuário para acessar o painel de administração:**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Inicie o servidor de desenvolvimento:**
    ```bash
    python manage.py runserver
    ```

Acesse `http://127.0.0.1:8000/` em seu navegador para ver o projeto em ação!

---

## 📂 Estrutura do Projeto

O projeto segue uma estrutura modular para facilitar a manutenção e escalabilidade.
Use code with caution.
Markdown
.
├── cgbookstore/ # Configurações centrais do projeto Django
│ ├── apps/ # Contêiner para todas as aplicações do projeto
│ │ ├── core/ # App principal (modelos de Livro, Autor, Perfil, etc.)
│ │ └── chatbot_literario/ # App autocontido para toda a lógica do chatbot
│ ├── config/ # Arquivos de settings, urls e wsgi do projeto
│ └── static/ # Arquivos estáticos globais (CSS, JS, Imagens)
├── docs/ # Documentação do projeto (relatórios, diagramas)
├── tests/ # Scripts de diagnóstico e testes standalone
├── manage.py # Utilitário de linha de comando do Django
└── requirements.txt # Dependências do projeto
Generated code
---

## 🤝 Como Contribuir

Contribuições são o que tornam a comunidade de código aberto um lugar incrível para aprender, inspirar e criar. Qualquer contribuição que você fizer será **muito bem-vinda**.

1.  Faça um **Fork** do projeto.
2.  Crie uma **Branch** para sua Feature (`git checkout -b feature/AmazingFeature`).
3.  Faça o **Commit** de suas mudanças (`git commit -m 'feat: Add some AmazingFeature'`).
4.  Faça o **Push** para a Branch (`git push origin feature/AmazingFeature`).
5.  Abra um **Pull Request**.

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<div align="center">
    Feito com ❤️ por <a href="https://github.com/cgvargas">C.G. Vargas</a>
</div>