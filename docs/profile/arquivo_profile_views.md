# Documentação Técnica: Módulo profile.py
**Arquivo:** cgbookstore/apps/core/views/profile.py
**Última atualização:** Documentação gerada em 2024
**Projeto:** CGBookstore
## Sumário
1. [Visão Geral](#1-vis%C3%A3o-geral)
2. [Dependências](#2-depend%C3%AAncias)
3. [Estrutura do Módulo](#3-estrutura-do-m%C3%B3dulo)
4. [Classes Detalhadas](#4-classes-detalhadas)
    - [4.1. ProfileView](#41-profileview)
    - [4.2. ProfileUpdateView](#42-profileupdateview)
    - [4.3. ProfileCardStyleView](#43-profilecardstyleview)
    - [4.4. ProfilePhotoUpdateView](#44-profilephotoupdateview)

5. [Fluxos de Dados](#5-fluxos-de-dados)
6. [Pontos Críticos](#6-pontos-cr%C3%ADticos)
7. [Recomendações](#7-recomenda%C3%A7%C3%B5es)
8. [Apêndices](#8-ap%C3%AAndices)

## 1. Visão Geral
O módulo implementa as views relacionadas ao gerenciamento de perfil de usuários no sistema CGBookstore, seguindo o padrão MVT (Model-View-Template) do Django. Este componente é responsável por todas as funcionalidades relacionadas ao perfil de usuário, incluindo visualização, edição, personalização de aparência e gestão de fotografia. `profile.py`
**Funcionalidades principais:**
- Visualização de perfil com estatísticas de leitura e conquistas
- Atualização de informações pessoais
- Personalização do estilo visual do card de perfil
- Upload e gerenciamento de foto de perfil

**Contexto técnico:**
- Parte do aplicativo `core` do projeto CGBookstore
- Implementado como um conjunto de class-based views do Django
- Integra-se com múltiplos modelos para apresentar dados consolidados

## 2. Dependências
### 2.1. Dependências do Django
``` python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
```
### 2.2. Dependências da Biblioteca Padrão
``` python
import json
import os
```
### 2.3. Dependências Internas
``` python
from ..forms import UserProfileForm
from ..models import Profile, UserBookShelf, UserAchievement, ReadingStats, Achievement
```
## 3. Estrutura do Módulo
O módulo está organizado em quatro classes principais, cada uma responsável por uma funcionalidade específica do gerenciamento de perfil:
1. **ProfileView** - Visualização de perfil e estatísticas (DetailView)
2. **ProfileUpdateView** - Atualização de dados do perfil (UpdateView)
3. **ProfileCardStyleView** - Personalização visual do card (View)
4. **ProfilePhotoUpdateView** - Gerenciamento de foto de perfil (View)

Todas as classes implementam para garantir que apenas usuários autenticados possam acessar as funcionalidades. `LoginRequiredMixin`
## 4. Classes Detalhadas
### 4.1. ProfileView
**Propósito:** Renderizar a página de perfil do usuário com todas as informações relevantes.
**Características:**
- Herda de e `LoginRequiredMixin``DetailView`
- Cria automaticamente um perfil caso o usuário não possua
- Agrega dados de múltiplas fontes (prateleiras, estatísticas, conquistas)

#### 4.1.1. Atributos
``` python
model = Profile
template_name = 'core/profile/profile.html'
context_object_name = 'profile'
```
#### 4.1.2. Métodos
**get_object**
``` python
def get_object(self, queryset=None):
    """
    Retorna o perfil do usuário logado.

    Para DetailView, precisamos sobrescrever get_object
    para retornar o perfil do usuário atual em vez de
    tentar buscar por pk ou slug.
    """
    # Verificar se o usuário tem um perfil
    try:
        return self.request.user.profile
    except Profile.DoesNotExist:
        # Se não existir, cria um perfil para o usuário
        return Profile.objects.create(user=self.request.user)
```
**Função:** Recupera ou cria o perfil do usuário atual.
**Pontos críticos:**
- Criação automática de perfil é um comportamento implícito
- Se a criação falhar, pode causar erro 500 não tratado

**get_context_data**
``` python
def get_context_data(self, **kwargs):
    """
    Prepara dados de contexto do perfil, incluindo estatísticas e conquistas.
    """
    context = super().get_context_data(**kwargs)
    user = self.request.user
    
    # Buscar livros por tipo de prateleira
    context.update({
        'favoritos': UserBookShelf.get_shelf_books(user, 'favorito'),
        'lendo': UserBookShelf.get_shelf_books(user, 'lendo'),
        'vou_ler': UserBookShelf.get_shelf_books(user, 'vou_ler'),
        'lidos': UserBookShelf.get_shelf_books(user, 'lido'),
        'recomendacoes': [],  # Substituir quando o sistema de recomendação estiver pronto
        'total_livros': UserBookShelf.objects.filter(user=user).count(),
    })
    
    # Obter ou criar estatísticas do usuário
    stats, created = ReadingStats.objects.get_or_create(user=user)
    
    # Se as estatísticas foram criadas agora, atualizá-las
    if created:
        stats.update_stats()
    
    # Adicionar estatísticas ao contexto
    context['stats'] = {
        'total_lidos': stats.total_books_read,
        'total_paginas': stats.total_pages_read,
        'sequencia_atual': stats.reading_streak,
        'maior_sequencia': stats.longest_streak,
        'genero_favorito': stats.favorite_genre or 'Não definido',
        'velocidade_leitura': stats.reading_velocity or 0,
        'livros_por_mes': stats.books_by_month or {}
    }
    
    # Obter conquistas do usuário
    user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement')
    
    # Adicionar conquistas ao contexto
    context['achievements'] = {
        'total': user_achievements.count(),
        'unlocked': list(user_achievements.values('achievement__name', 'achievement__description',
                                               'achievement__icon', 'achievement__tier',
                                               'achievement__points', 'achieved_at')),
        'in_progress': self.get_in_progress_achievements(user)
    }
    
    # Calcular pontuação total
    total_points = sum(achievement.achievement.points for achievement in user_achievements)
    context['total_points'] = total_points
    
    return context
```
**Função:** Prepara todos os dados necessários para a renderização do template.
**Pontos críticos:**
- Múltiplas consultas ao banco de dados que podem impactar o desempenho
- Sistema de recomendações pendente (representado por lista vazia)
- Criação implícita de estatísticas se não existirem

**get_in_progress_achievements**
``` python
def get_in_progress_achievements(self, user):
    """
    Retorna as próximas conquistas que o usuário está perto de alcançar.
    """
    # Obter todas as conquistas
    all_achievements = Achievement.objects.all()

    # Obter conquistas que o usuário já tem
    user_achievement_ids = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)

    # Conquistas que o usuário ainda não tem
    pending_achievements = all_achievements.exclude(id__in=user_achievement_ids)

    # Implementação básica - poderia ser expandida para calcular progresso real
    in_progress = []

    # Verificar conquistas relacionadas a quantidade de livros
    total_books = UserBookShelf.objects.filter(user=user).count()
    books_read = UserBookShelf.objects.filter(user=user, shelf_type='lido').count()

    for achievement in pending_achievements:
        progress_info = {
            'id': achievement.id,
            'name': achievement.name,
            'description': achievement.description,
            'progress': 0,
            'icon': achievement.icon,
            'tier': achievement.tier
        }

        # Calcular progresso com base no código da conquista
        if achievement.code == 'book_collector_i' and total_books < 5:
            progress_info['progress'] = min(int(total_books / 5 * 100), 99)
            in_progress.append(progress_info)

        elif achievement.code == 'book_collector_ii' and total_books < 25:
            progress_info['progress'] = min(int(total_books / 25 * 100), 99)
            in_progress.append(progress_info)

        elif achievement.code == 'bookworm_i' and books_read < 5:
            progress_info['progress'] = min(int(books_read / 5 * 100), 99)
            in_progress.append(progress_info)

        elif achievement.code == 'bookworm_ii' and books_read < 15:
            progress_info['progress'] = min(int(books_read / 15 * 100), 99)
            in_progress.append(progress_info)

    # Limitar a 3 conquistas em progresso
    return sorted(in_progress, key=lambda x: x['progress'], reverse=True)[:3]
```
**Função:** Calcula e retorna conquistas que o usuário está perto de completar.
**Pontos críticos:**
- Implementação hardcoded para tipos específicos de conquistas
- Várias consultas adicionais ao banco de dados
- Lógica de cálculo de progresso difícil de expandir
- Limita retorno a 3 conquistas independente do total

### 4.2. ProfileUpdateView
**Propósito:** Permitir que o usuário atualize os dados de seu perfil.
**Características:**
- Herda de e `LoginRequiredMixin``UpdateView`
- Utiliza formulário dedicado para validação de dados
- Implementa mensagens de feedback para o usuário

#### 4.2.1. Atributos
``` python
model = Profile
form_class = UserProfileForm
template_name = 'core/profile/profile_form.html'
success_url = reverse_lazy('profile')
```
#### 4.2.2. Métodos
**get_object**
``` python
def get_object(self, queryset=None):
    """
    Retorna o perfil do usuário logado para edição.

    Returns:
        Profile: Perfil do usuário atual
    """
    return self.request.user.profile
```
**Função:** Recupera o perfil do usuário para edição.
**Pontos críticos:**
- Não trata o caso de perfil inexistente (pode gerar AttributeError)
- Inconsistente com ProfileView que cria perfil automaticamente

**form_valid**
``` python
def form_valid(self, form):
    """
    Processa atualização de perfil bem-sucedida.

    Args:
        form: Formulário de perfil validado

    Returns:
        HttpResponse: Redireciona com mensagem de sucesso
    """
    messages.success(self.request, 'Perfil atualizado com sucesso!')
    return super().form_valid(form)
```
**Função:** Processa formulário válido e adiciona mensagem de sucesso.
**Pontos críticos:**
- Comportamento padrão do UpdateView sem lógica adicional

**form_invalid**
``` python
def form_invalid(self, form):
    """
    Trata erros na atualização do perfil.

    Args:
        form: Formulário de perfil inválido

    Returns:
        HttpResponse: Renderiza formulário com mensagem de erro
    """
    messages.error(self.request, 'Erro ao atualizar perfil. Por favor, verifique os dados.')
    return super().form_invalid(form)
```
**Função:** Processa formulário inválido e adiciona mensagem de erro.
**Pontos críticos:**
- Mensagem genérica não especifica quais campos têm problemas

### 4.3. ProfileCardStyleView
**Propósito:** Permitir personalização visual do card de perfil.
**Características:**
- Herda de e `LoginRequiredMixin``View`
- Implementa interface RESTful (GET/POST)
- Manipula dados em formato JSON

#### 4.3.1. Métodos
**get**
``` python
def get(self, request, *args, **kwargs):
    """
    Recupera o estilo atual do card do perfil.

    Returns:
        JsonResponse: Estilo do card em formato JSON
    """
    return JsonResponse(request.user.profile.get_card_style())
```
**Função:** Retorna o estilo atual do card.
**Pontos críticos:**
- Dependência do método get_card_style() no modelo Profile
- Não verifica se o perfil existe antes de tentar acessá-lo

**post**
``` python
def post(self, request, *args, **kwargs):
    """
    Atualiza o estilo do card do perfil.

    Etapas:
    1. Decodifica dados JSON
    2. Valida campos obrigatórios
    3. Atualiza estilo do perfil

    Returns:
        JsonResponse: Resultado da atualização
    """
    try:
        # Decodificar dados JSON
        data = json.loads(request.body.decode('utf-8'))
        profile = request.user.profile

        # Campos obrigatórios para estilo do card
        required_fields = ['background_color', 'text_color', 'border_color',
                          'image_style', 'hover_effect', 'icon_style']

        # Preencher campos ausentes com valores padrão
        for field in required_fields:
            if field not in data:
                data[field] = profile.get_card_style().get(field)

        # Salvar novo estilo
        profile.card_style = data
        profile.save()

        return JsonResponse({
            'success': True,
            'styles': profile.get_card_style()
        })
    except json.JSONDecodeError as e:
        # Tratamento de erro de decodificação JSON
        return JsonResponse({
            'success': False,
            'error': 'Erro ao decodificar JSON: ' + str(e)
        }, status=400)
    except Exception as e:
        # Tratamento de erros gerais
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
```
**Função:** Atualiza o estilo do card com dados recebidos via JSON.
**Pontos críticos:**
- Bom tratamento de erros com blocos try/except específicos
- Implementa solução para campos ausentes (fallback para valores atuais)
- Não valida o conteúdo dos campos (apenas presença)
- Duas chamadas para `get_card_style()` podem ser otimizadas

### 4.4. ProfilePhotoUpdateView
**Propósito:** Gerenciar o upload e atualização da foto de perfil.
**Características:**
- Herda de e `LoginRequiredMixin``View`
- Implementa apenas o método POST
- Valida os arquivos de imagem enviados

#### 4.4.1. Métodos
**post**
``` python
def post(self, request, *args, **kwargs):
    """
    Atualiza a foto de perfil do usuário.

    Etapas:
    1. Valida existência de arquivo
    2. Verifica tipo de imagem
    3. Valida tamanho do arquivo
    4. Remove foto anterior (se existir)
    5. Salva nova foto

    Returns:
        JsonResponse: Resultado da atualização
    """
    try:
        # Verificar se foto foi enviada
        if 'profile_photo' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Nenhuma foto enviada'
            }, status=400)

        photo = request.FILES['profile_photo']

        # Validar tipo do arquivo
        if not photo.content_type.startswith('image/'):
            return JsonResponse({
                'success': False,
                'error': 'O arquivo deve ser uma imagem'
            }, status=400)

        # Validar tamanho (max 5MB)
        if photo.size > 5 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'A imagem deve ter no máximo 5MB'
            }, status=400)

        # Se já existir uma foto, remover
        if request.user.foto:
            if os.path.exists(request.user.foto.path):
                os.remove(request.user.foto.path)

        # Salvar nova foto
        request.user.foto = photo
        request.user.save()

        return JsonResponse({
            'success': True,
            'message': 'Foto atualizada com sucesso'
        })

    except Exception as e:
        # Tratamento de erros gerais
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
```
**Função:** Processa o upload de nova foto de perfil.
**Pontos críticos:**
- Implementa validações importantes (existência, tipo, tamanho)
- Gerencia arquivos no sistema de arquivos (remove fotos antigas)
- Depende do campo `foto` no modelo User, não no Profile
- Validação de tipo baseada apenas em content_type (pode ser falsificada)
- Não implementa redimensionamento ou otimização de imagens

## 5. Fluxos de Dados
### 5.1. Fluxo de Visualização de Perfil
``` 
1. Usuário acessa URL de perfil
2. LoginRequiredMixin verifica autenticação
   └── Se não autenticado: redireciona para login
3. ProfileView.get_object() busca perfil do usuário
   ├── Se perfil existe: retorna perfil existente
   └── Se perfil não existe: cria novo perfil
4. ProfileView.get_context_data() prepara dados
   ├── Busca livros nas prateleiras
   ├── Busca ou cria estatísticas
   ├── Busca conquistas desbloqueadas
   └── Calcula conquistas em progresso
5. Django renderiza o template com os dados
6. Página de perfil é exibida ao usuário
```
### 5.2. Fluxo de Atualização de Perfil
``` 
1. Usuário acessa formulário de edição ou envia formulário
2. LoginRequiredMixin verifica autenticação
   └── Se não autenticado: redireciona para login
3. ProfileUpdateView.get_object() busca perfil
4. Se GET: formulário é exibido com dados atuais
5. Se POST:
   ├── Formulário é validado
   │   ├── Se válido: atualiza perfil e mostra mensagem de sucesso
   │   └── Se inválido: renderiza formulário com erros e mensagem
   └── Redireciona para página de perfil ou exibe formulário com erros
```
### 5.3. Fluxo de Personalização de Card
``` 
1. Usuário interage com interface de personalização
2. Frontend envia requisição AJAX
3. LoginRequiredMixin verifica autenticação
   └── Se não autenticado: retorna erro 401/403
4. Se GET: retorna estilo atual como JSON
5. Se POST:
   ├── Decodifica dados JSON
   │   └── Se falhar: retorna erro 400
   ├── Verifica campos obrigatórios
   │   └── Se faltarem: preenche com valores atuais
   ├── Atualiza estilo no banco de dados
   └── Retorna resultado como JSON
```
### 5.4. Fluxo de Atualização de Foto
``` 
1. Usuário seleciona nova foto e confirma upload
2. Frontend envia requisição multipart/form-data
3. LoginRequiredMixin verifica autenticação
   └── Se não autenticado: retorna erro 401/403
4. ProfilePhotoUpdateView verifica arquivo
   ├── Se arquivo não enviado: retorna erro 400
   ├── Se não for imagem: retorna erro 400
   └── Se tamanho > 5MB: retorna erro 400
5. Se foto anterior existe, remove do sistema
6. Salva nova foto e atualiza banco de dados
7. Retorna resultado como JSON
```
## 6. Pontos Críticos
### 6.1. Segurança

| Item | Descrição | Severidade |
| --- | --- | --- |
| Autenticação | LoginRequiredMixin usado em todas as views | ✅ Adequado |
| Validação de Input | Validação básica para imagens e JSON | ⚠️ Média |
| Manipulação de Arquivos | Remoção direta de arquivos no sistema | ⚠️ Média |
| Verificação de MIME | Baseada apenas em content_type | ⚠️ Média |
| Cross-Site Request Forgery | Django CSRF protection implícita | ✅ Adequado |
### 6.2. Desempenho

| Item | Descrição | Severidade |
| --- | --- | --- |
| Consultas ao Banco | Múltiplas consultas em `get_context_data` | ⚠️ Alta |
| Otimização de Consultas | Uso de `select_related` para conquistas | ✅ Adequado |
| Caching | Ausente para dados frequentemente acessados | ⚠️ Média |
| Gerenciamento de Imagens | Sem redimensionamento ou otimização | ⚠️ Média |
| Carregamento de Recursos | Carrega todas as conquistas em cada visualização | ⚠️ Alta |
### 6.3. Manutenibilidade

| Item | Descrição | Severidade |
| --- | --- | --- |
| Estrutura do Código | Bem organizado em classes com responsabilidades definidas | ✅ Adequado |
| Documentação | Boa documentação de classes e métodos | ✅ Adequado |
| Conquistas | Lógica hardcoded com códigos específicos | ⚠️ Alta |
| Tratamento de Exceções | Implementado para JSON e upload de arquivo | ✅ Adequado |
| Consistência | Inconsistência no tratamento de perfil inexistente | ⚠️ Média |
| Testes | Não visíveis no código analisado | ❓ Desconhecido |
### 6.4. Funcionalidade

| Item | Descrição | Severidade |
| --- | --- | --- |
| Completude | Sistema com visualização, edição, estilos e foto | ✅ Adequado |
| Recomendações | Sistema pendente de implementação | ⚠️ Média |
| Consistência de UI | Aparentemente consistente (baseado no código) | ✅ Adequado |
| Gerenciamento de Perfil | Funcional mas com pequenas inconsistências | ⚠️ Baixa |
| Gamificação | Sistema de conquistas implementado | ✅ Adequado |
## 7. Recomendações
### 7.1. Segurança
1. **Validação de Imagens**
    - Implementar validação mais robusta (verificação de conteúdo real)
    - Usar bibliotecas como Pillow para verificar se o arquivo é realmente uma imagem

2. **Proteção contra Ataques de Path Traversal**
    - Validar caminhos de arquivo com `os.path.abspath` e comparar com diretório base
    - Evitar manipulação direta de caminhos baseados em input do usuário

3. **Validação de Estilo de Card**
    - Implementar validação para valores de estilo (cores válidas, etc.)
    - Limitar tamanho e complexidade do objeto JSON de estilo

### 7.2. Desempenho
1. **Otimização de Consultas**
    - Consolidar múltiplas consultas usando `prefetch_related`
    - Implementar Select N+1 Query Detector durante desenvolvimento

2. **Implementar Caching**
    - Cachear estatísticas que não mudam com frequência
    - Utilizar Django cache framework para resultados de conquistas

3. **Otimização de Imagens**
    - Implementar redimensionamento automático para diferentes usos
    - Comprimir imagens para reduzir tamanho de armazenamento e transferência

4. **Lazy Loading**
    - Carregar conquistas e estatísticas via AJAX após carregar a página principal
    - Implementar paginação para listas de livros em prateleiras

### 7.3. Manutenibilidade
1. **Refatoração do Sistema de Conquistas**
    - Criar um serviço dedicado para lógica de conquistas
    - Definir interface declarativa para cálculo de progresso de conquistas
    - Implementar sistema baseado em regras em vez de código hardcoded

2. **Padronização de Comportamentos**
    - Uniformizar tratamento de perfil inexistente entre as views
    - Centralizar lógica de criação/recuperação de perfil

3. **Separação de Responsabilidades**
    - Mover lógica de validação e processamento para serviços dedicados
    - Usar forms para validação de dados em todas as views

4. **Testes Automatizados**
    - Implementar testes unitários para lógica de negócios
    - Implementar testes de integração para fluxos completos
    - Criar testes de regressão para bugs já corrigidos

### 7.4. Funcionalidade
1. **Implementar Sistema de Recomendações**
    - Substituir a lista vazia por recomendações reais
    - Considerar algoritmos simples baseados em gêneros favoritos inicialmente

2. **Melhorar Feedback ao Usuário**
    - Adicionar mensagens mais específicas para erros de validação
    - Implementar feedback visual para operações assíncronas

3. **Internacionalização**
    - Preparar o sistema para suportar múltiplos idiomas
    - Usar o sistema de tradução do Django para mensagens

4. **Conformidade com GDPR**
    - Adicionar endpoint para download dos dados pessoais
    - Implementar funcionalidade de exclusão de conta

## 8. Apêndices
### 8.1. Diagrama de Classes Simplificado
``` 
┌───────────────────────┐
│ LoginRequiredMixin    │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐      ┌───────────────────────┐
│ ProfileView           │─────▶│ Profile               │
│                       │      │                       │
│ +get_object()         │      │ +user                 │
│ +get_context_data()   │      │ +bio                  │
│ +get_in_progress_...  │      │ +card_style           │
└───────────────────────┘      │ +get_card_style()     │
                               └───────────────────────┘
┌───────────────────────┐              ▲
│ ProfileUpdateView     │──────────────┘
│                       │
│ +get_object()         │      ┌───────────────────────┐
│ +form_valid()         │─────▶│ UserProfileForm       │
│ +form_invalid()       │      └───────────────────────┘
└───────────────────────┘
            
┌───────────────────────┐      ┌───────────────────────┐
│ ProfileCardStyleView  │─────▶│ JsonResponse          │
│                       │      └───────────────────────┘
│ +get()                │
│ +post()               │
└───────────────────────┘

┌───────────────────────┐      ┌───────────────────────┐
│ ProfilePhotoUpdateView│─────▶│ User                  │
│                       │      │                       │
│ +post()               │      │ +foto                 │
└───────────────────────┘      └───────────────────────┘
```
### 8.2. Histórico de Atualizações da Documentação

| Data | Versão | Descrição |
| --- | --- | --- |
| 2024 | 1.0 | Criação da documentação inicial |
Este documento deve ser atualizado conforme o código evolui para garantir que continue a refletir com precisão o estado atual do módulo . `profile.py`
