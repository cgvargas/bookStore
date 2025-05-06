# Módulo Administrativo CGBookstore

Este diretório contém a implementação modular do sistema administrativo do projeto CGBookstore.

## Estrutura

A estrutura foi organizada para melhorar a manutenção, legibilidade e escalabilidade do código:

```
admin/
├── __init__.py            # Importa e registra todos os admins
├── site.py                # DatabaseAdminSite - site administrativo customizado
├── user_admin.py          # CustomUserAdmin e ProfileAdmin
├── book_admin.py          # BookAdmin e BookCategoryAdmin
├── shelf_admin.py         # DefaultShelfTypeAdmin, BookShelfManagerAdmin, etc.
├── content_admin.py       # BannerAdmin, VideoItemAdmin, etc.
├── custom_section_admin.py # CustomSectionAdmin e classes relacionadas
├── views.py               # Views administrativas personalizadas
├── forms.py               # Formulários específicos do admin
├── mixins.py              # Mixins reutilizáveis
└── README.md              # Esta documentação
```

## Componentes

### Site Administrativo
- `site.py`: Contém a classe `DatabaseAdminSite` que estende a `AdminSite` do Django
- Implementa funcionalidades personalizadas como geração de schema, exportação de dados, gerenciamento de prateleiras

### Mixins Reutilizáveis
- `mixins.py`: Contém classes mixin para adicionar funcionalidades comuns:
  - `LoggingAdminMixin`: Adiciona logs detalhados
  - `CachedCountersMixin`: Implementa cache em contadores
  - `BookShelfManagerMixin`: Funcionalidades para gerenciamento de prateleiras
  - `OptimizedQuerysetMixin`: Otimiza consultas ao banco de dados
  - `PermissionControlledAdmin`: Controle granular de permissões
  - `HelpTextAdminMixin`: Adiciona textos de ajuda contextuais

### Classes de Administração
- `user_admin.py`: Configurações para administração de usuários
- `book_admin.py`: Configurações para administração de livros
- `shelf_admin.py`: Configurações para administração de prateleiras
- `content_admin.py`: Configurações para administração de conteúdos diversos
- `custom_section_admin.py`: Configurações para administração de seções customizadas

### Formulários
- `forms.py`: Formulários usados pelas classes administrativas
  - `BookAdminForm`: Formulário customizado para livros
  - `BookShelfSectionAdminForm`: Formulário para seções de prateleira
  - `AdminBulkActionForm`: Formulário para ações em massa
  - `CustomAdminImportForm`: Formulário para importação de dados

### Views
- `views.py`: Views administrativas personalizadas
  - `dashboard_view`: Dashboard administrativo principal
  - `export_model_data`: Exportação de dados
  - `book_statistics_view`: Estatísticas de livros
  - `user_activity_view`: Atividades de usuários
  - `cache_management_view`: Gerenciamento de cache
  - `admin_log_view`: Visualização de logs administrativos

## Uso

O módulo é importado automaticamente em `apps/core/admin.py`, que agora apenas importa e expõe o `admin_site` deste pacote.

Para adicionar uma nova classe administrativa:

1. Adicionar a classe no arquivo apropriado (ou criar um novo se necessário)
2. Importar a classe em `__init__.py`
3. Registrar o modelo com a classe em `__init__.py`

## Otimizações

Este módulo implementa diversas otimizações:

- Uso de `select_related` e `prefetch_related` para reduzir consultas ao banco
- Cache para operações custosas
- Organização modular para facilitar manutenção
- Separação clara de responsabilidades
- Reuso de código através de mixins

## Segurança

Melhorias de segurança implementadas:

- Controle granular de permissões
- Logs detalhados de ações administrativas
- Validação adequada em formulários
- Verificações de permissão em views personalizadas

---

Última atualização: Março/2025