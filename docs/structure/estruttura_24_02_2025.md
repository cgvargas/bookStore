# Estrutura do Projeto

Data de geração: 24/02/2025 15:14:29

Arquivo CSV: `project_structure_20250224_151429.csv`

## Informações Gerais

- **Total de arquivos:** 232
- **Tipos de arquivo encontrados:**
  - **CSS:** 8
  - **JavaScript:** 10
  - **Markdown:** 41
  - **Outro:** 27
  - **Python:** 112
  - **Template HTML:** 29
  - **Texto:** 5

## Estrutura de Diretórios e Arquivos

### Raiz do Projeto

- `.coverage` (Outro)
- `.env.dev` (Outro)
- `.env.prod` (Outro)
- `.gitignore` (Outro)
- `LICENSE` (Outro)
- `README.md` (Markdown)
- `check_sendgrid_config.py` (Python)
- `core_book.csv` (Outro)
- `core_userbookshelf.csv` (Outro)
- `listar_tabelas.py` (Python)
- `manage.py` (Python)
- `pytest.ini` (Outro)
- `requirements.txt` (Texto)
- `sendgrid_email_test.py` (Python)
- `test_env.py` (Python)
- `test_sendgrid.py` (Python)

### Diretório `.idea`

- `.gitignore` (Outro)
- `bookstore.iml` (Outro)
- `misc.xml` (Outro)
- `modules.xml` (Outro)
- `vcs.xml` (Outro)
- `workspace.xml` (Outro)

#### Subdiretório `.idea/inspectionProfiles`

- `Project_Default.xml` (Outro)
- `profiles_settings.xml` (Outro)

### Diretório `.pytest_cache`

- `.gitignore` (Outro)
- `CACHEDIR.TAG` (Outro)
- `README.md` (Markdown)

#### Subdiretório `.pytest_cache/v/cache`

- `lastfailed` (Outro)
- `nodeids` (Outro)
- `stepwise` (Outro)

### Diretório `cgbookstore`

- `__init__.py` (Python)
- `db.sqlite3` (Outro)
- `debug.log` (Outro)

#### Subdiretório `cgbookstore/apps`

- `__init__.py` (Python)

##### Subdiretório `cgbookstore/apps/core`

- `__init__.py` (Python)
- `admin.py` (Python)
- `apps.py` (Python)
- `forms.py` (Python)
- `signals.py` (Python)
- `tests.py` (Python)
- `urls.py` (Python)

###### Subdiretório `cgbookstore/apps/core/management`

- `__init__.py` (Python)

####### Subdiretório `cgbookstore/apps/core/management/commands`

- `__init__.py` (Python)
- `create_default_shelves.py` (Python)
- `create_profiles.py` (Python)
- `generate_project_structure.py` (Python)
- `generate_tables.py` (Python)

###### Subdiretório `cgbookstore/apps/core/models`

- `__init__.py` (Python)
- `banner.py` (Python)
- `book.py` (Python)
- `home_content.py` (Python)
- `profile.py` (Python)
- `user.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations`

- `__init__.py` (Python)
- `engine.py` (Python)
- `urls.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations/analytics`

- `__init__.py` (Python)
- `apps.py` (Python)
- `endpoints.py` (Python)
- `models.py` (Python)
- `serializers.py` (Python)
- `tracker.py` (Python)
- `urls.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations/analytics/admin_dashboard`

- `__init__.py` (Python)
- `urls.py` (Python)
- `utils.py` (Python)
- `views.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations/analytics/admin_dashboard/templatetags`

- `__init__.py` (Python)
- `dashboard_filters.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations/analytics/management`

- `__init__.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations/analytics/management/commands`

- `__init__.py` (Python)
- `clean_test_data.py` (Python)
- `generate_test_data.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations/analytics/tests`

- `__init__.py` (Python)
- `generate_test_data.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations/analytics/utils`

- `__init__.py` (Python)
- `processors.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations/api`

- `README.md` (Markdown)
- `__init__.py` (Python)
- `endpoints.py` (Python)
- `performance.py` (Python)
- `serializers.py` (Python)
- `urls.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations/management`

- `__init__.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations/management/commands`

- `__init__.py` (Python)
- `benchmark_recommendations.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations/providers`

- `__init__.py` (Python)
- `category.py` (Python)
- `exclusion.py` (Python)
- `external_api.py` (Python)
- `history.py` (Python)
- `mapping.py` (Python)
- `similarity.py` (Python)
- `temporal.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations/services`

- `__init__.py` (Python)
- `calculator.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations/tests`

- `__init__.py` (Python)
- `conftest.py` (Python)
- `test_api.py` (Python)
- `test_cache.py` (Python)
- `test_category.py` (Python)
- `test_engine.py` (Python)
- `test_exclusions.py` (Python)
- `test_history_temporal.py` (Python)
- `test_load.py` (Python)
- `test_logging.py` (Python)
- `test_processors.py` (Python)
- `test_providers.py` (Python)
- `test_recommendation_cache.py` (Python)
- `test_recommendation_system.py` (Python)
- `test_search_tracking.py` (Python)
- `test_similarity_provider.py` (Python)

###### Subdiretório `cgbookstore/apps/core/recommendations/utils`

- `__init__.py` (Python)
- `cache_manager.py` (Python)
- `google_books_cache.py` (Python)
- `processors.py` (Python)
- `search_tracker.py` (Python)

###### Subdiretório `cgbookstore/apps/core/serializers`

- `__init__.py` (Python)
- `user_serializer.py` (Python)

###### Subdiretório `cgbookstore/apps/core/services`

- `__init__.py` (Python)
- `google_books_client.py` (Python)

###### Subdiretório `cgbookstore/apps/core/templates`

- `__init__.py` (Python)

###### Subdiretório `cgbookstore/apps/core/templates/admin`

- `database_overview.html` (Template HTML)
- `database_table_view.html` (Template HTML)
- `index.html` (Template HTML)

###### Subdiretório `cgbookstore/apps/core/templates/core`

- `__init__.py` (Python)
- `base.html` (Template HTML)
- `contato.html` (Template HTML)
- `home.html` (Template HTML)
- `login.html` (Template HTML)
- `politica_privacidade.html` (Template HTML)
- `register.html` (Template HTML)
- `sobre.html` (Template HTML)
- `termos_uso.html` (Template HTML)

###### Subdiretório `cgbookstore/apps/core/templates/core/admin_dashboard`

- `dashboard.html` (Template HTML)
- `metrics.html` (Template HTML)

###### Subdiretório `cgbookstore/apps/core/templates/core/book`

- `book_details.html` (Template HTML)
- `search.html` (Template HTML)

###### Subdiretório `cgbookstore/apps/core/templates/core/components`

- `recommendation_widget.html` (Template HTML)

###### Subdiretório `cgbookstore/apps/core/templates/core/email`

- `contato_confirmacao.html` (Template HTML)
- `contato_email.html` (Template HTML)
- `email_verification.html` (Template HTML)

###### Subdiretório `cgbookstore/apps/core/templates/core/includes`

- `book_card.html` (Template HTML)

###### Subdiretório `cgbookstore/apps/core/templates/core/password`

- `password_reset_complete.html` (Template HTML)
- `password_reset_confirm.html` (Template HTML)
- `password_reset_done.html` (Template HTML)
- `password_reset_email.html` (Template HTML)
- `password_reset_form.html` (Template HTML)
- `password_reset_subject.txt` (Texto)

###### Subdiretório `cgbookstore/apps/core/templates/core/profile`

- `profile.html` (Template HTML)
- `profile_form.html` (Template HTML)

###### Subdiretório `cgbookstore/apps/core/templates/core/recommendations`

- `mixed_recommendations.html` (Template HTML)
- `personalized_shelf.html` (Template HTML)

###### Subdiretório `cgbookstore/apps/core/templatetags`

- `__init__.py` (Python)
- `custom_tags.py` (Python)

###### Subdiretório `cgbookstore/apps/core/utils`

- `__init__.py` (Python)
- `google_books_cache.py` (Python)
- `image_processor.py` (Python)

###### Subdiretório `cgbookstore/apps/core/views`

- `__init__.py` (Python)
- `auth.py` (Python)
- `book.py` (Python)
- `general.py` (Python)
- `profile.py` (Python)
- `recommendation_views.py` (Python)

### Diretório `cgbookstore/config`

- `__init__.py` (Python)
- `asgi.py` (Python)
- `settings.py` (Python)
- `urls.py` (Python)
- `wsgi.py` (Python)

### Diretório `cgbookstore/static`

#### Subdiretório `cgbookstore/static/css`

- `book-details.css` (CSS)
- `book-search.css` (CSS)
- `contato.css` (CSS)
- `profile.css` (CSS)
- `styles.css` (CSS)
- `swiper-custom.css` (CSS)

##### Subdiretório `cgbookstore/static/css/admin`

- `dashboard.css` (CSS)
- `metrics.css` (CSS)

#### Subdiretório `cgbookstore/static/images`

- `favicon.svg` (Outro)
- `logo.png` (Outro)
- `no-cover.svg` (Outro)

#### Subdiretório `cgbookstore/static/js`

- `book-details.js` (JavaScript)
- `book-search.js` (JavaScript)
- `csrf-setup.js` (JavaScript)
- `profile-customization.js` (JavaScript)
- `profile.js` (JavaScript)
- `recommendations.js` (JavaScript)
- `swiper-config.js` (JavaScript)
- `video-section.js` (JavaScript)

##### Subdiretório `cgbookstore/static/js/admin`

- `dashboard.js` (JavaScript)
- `metrics.js` (JavaScript)

### Diretório `docs`

#### Subdiretório `docs/leiames`

- `LEIAME.md` (Markdown)

#### Subdiretório `docs/observacoes`

- `chat_padrao_conciso.md` (Markdown)
- `chat_padronizado.txt` (Texto)
- `chat_padronizado_01_02_2025.md` (Markdown)
- `chat_padronizado_03_02_2025.md` (Markdown)
- `upgrades_diarios_03_02_25.md` (Markdown)
- `upgrades_diarios_10_02_25.md` (Markdown)
- `upgrades_diarios_11_02_25.md` (Markdown)
- `upgrades_diarios_12_02_25.md` (Markdown)

#### Subdiretório `docs/projeto_base`

- `projeto-0702-2025.md` (Markdown)
- `sistema_de_recomendações.md` (Markdown)

#### Subdiretório `docs/status`

- `status_01_02_2025.md` (Markdown)
- `status_14_01_2025.md` (Markdown)
- `status_15_01_2025.md` (Markdown)
- `status_17_01_2025.md` (Markdown)
- `status_17_02_2025.md` (Markdown)
- `status_19_01_2025.md` (Markdown)
- `status_20_02_2025.md` (Markdown)
- `status_22_01_2025.md` (Markdown)
- `status_23_01_2025.md` (Markdown)
- `status_25_01_2025.md` (Markdown)
- `status_26_01_2025.md` (Markdown)
- `status_27_01_2025.md` (Markdown)
- `status_28_01_2025.md` (Markdown)

#### Subdiretório `docs/structure`

- `estrutura_14_01_2025.md` (Markdown)
- `estrutura_remodelada-25-01-25.jsx` (Outro)
- `project-structure-17-01-2025.md` (Markdown)
- `structure-07-02-2025.txt` (Texto)
- `structure-22-01-2025.md` (Markdown)
- `structure-23-01-2025.md` (Markdown)
- `structure-28-01-2025.txt` (Texto)

#### Subdiretório `docs/ultimos_chats`

- `ultimo_chat_03_02_25.md` (Markdown)
- `ultimo_chat_10_02_25.md` (Markdown)
- `ultimo_chat_11_02_25.md` (Markdown)
- `ultimo_chat_12_02_25.md` (Markdown)
- `ultimo_chat_18_02_25.md` (Markdown)
- `ultimo_chat_19_02_25.md` (Markdown)
- `ultimo_chat_20_02_25.md` (Markdown)
- `ultimo_chat_21_02_25.md` (Markdown)
- `ultimo_chat_22_02_25.md` (Markdown)
- `ultimo_chat_22_02_25_v2.md` (Markdown)
- `ultimo_chat_24_02_25.md` (Markdown)