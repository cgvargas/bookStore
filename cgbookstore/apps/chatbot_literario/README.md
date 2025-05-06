# Chatbot Literário - CG.BookStore.Online

O Chatbot Literário é um assistente virtual para ajudar os usuários da plataforma CG.BookStore.Online com recomendações de livros, informações literárias e navegação no site.

## Funcionalidades

- **Recomendações Personalizadas**: Sugere livros com base no histórico e preferências do usuário
- **Recomendações por Gênero**: Fornece sugestões de leitura por categoria
- **Informações sobre Livros**: Fornece sinopses e detalhes sobre obras específicas
- **Assistência na Navegação**: Ajuda o usuário a encontrar funcionalidades no site
- **Conversa Natural**: Interface conversacional amigável e intuitiva

## Tecnologias Utilizadas

- **Microsoft DialoGPT**: Modelo de linguagem para geração de respostas naturais
- **Django REST Framework**: Para endpoints de comunicação
- **WebSockets (Implementação Futura)**: Para comunicação em tempo real
- **Integração com Sistema de Recomendação**: Conexão com o motor de recomendação existente

## Arquitetura

O chatbot segue uma arquitetura modular:

1. **Interface de Usuário**:
   - Widget flutuante para acesso rápido
   - Página dedicada para conversas estendidas

2. **Gerenciamento de Estado**:
   - Armazenamento de histórico de conversas
   - Rastreamento de contexto para respostas coerentes

3. **Processamento de Linguagem Natural**:
   - Reconhecimento de intenções
   - Extração de entidades relevantes

4. **Integração com Sistemas**:
   - Sistema de recomendação de livros
   - Catálogo de livros e autores
   - Perfil do usuário

## Instalação e Configuração

### Dependências