.
├── .env
├── .gitignore
├── manage.py
├── requirements.txt
├── .idea
│   ├── .gitignore
│   ├── bookstore.iml
│   ├── misc.xml
│   ├── modules.xml
│   ├── vcs.xml
│   ├── workspace.xml
│   └── inspectionProfiles
│       ├── Project_Default.xml
│       └── profiles_settings.xml
├── cgbookstore
│   ├── __init__.py
│   ├── db.sqlite3
│   ├── apps
│   │   ├── __init__.py
│   │   ├── core
│   │       ├── __init__.py
│   │       ├── admin.py
│   │       ├── apps.py
│   │       ├── forms.py
│   │       ├── signals.py
│   │       ├── tests.py
│   │       ├── urls.py
│   │       ├── management
│   │       │   ├── __init__.py
│   │       │   └── commands
│   │       │       ├── __init__.py
│   │       │       ├── create_profiles.py
│   │       │       ├── generate_project_structure.py
│   │       │       └── generate_tables.py
│   │       ├── models
│   │       │   ├── __init__.py
│   │       │   ├── book.py
│   │       │   ├── profile.py
│   │       │   └── user.py
│   │       ├── serializers
│   │       │   ├── __init__.py
│   │       │   └── user_serializer.py
│   │       ├── services
│   │       │   ├── __init__.py
│   │       │   └── google_books_client.py
│   │       ├── utils
│   │       │   ├── __init__.py
│   │       │   └── google_books_cache.py
│   │       ├── templates
│   │       │   ├── admin
│   │       │   │   └── index.html
│   │       │   ├── core
│   │       │       ├── base.html
│   │       │       ├── contato.html
│   │       │       ├── home.html
│   │       │       ├── login.html
│   │       │       ├── politica_privacidade.html
│   │       │       ├── register.html
│   │       │       ├── sobre.html
│   │       │       ├── termos_uso.html
│   │       │       ├── book
│   │       │       │   ├── book_details.html
│   │       │       │   └── search.html
│   │       │       ├── email
│   │       │       │   └── email_verification.html
│   │       │       ├── password
│   │       │       │   ├── password_reset_complete.html
│   │       │       │   ├── password_reset_confirm.html
│   │       │       │   ├── password_reset_done.html
│   │       │       │   ├── password_reset_email.html
│   │       │       │   └── password_reset_form.html
│   │       │       ├── profile
│   │       │       │   ├── profile.html
│   │       │       │   └── profile_form.html
│   │       ├── tests
│   │       │   ├── __init__.py
│   │       │   ├── test_models.py
│   │       │   └── test_views.py
│   │       ├── views
│   │       │   ├── __init__.py
│   │       │   ├── auth.py
│   │       │   ├── book.py
│   │       │   ├── general.py
│   │       │   └── profile.py
│   ├── config
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── docs
│   │   ├── observacoes
│   │   │   └── conversa_01.txt
│   │   ├── status
│   │   │   ├── status_14_01_2025.md
│   │   │   ├── status_15_01_2025.md
│   │   │   ├── status_17_01_2025.md
│   │   │   ├── status_19_01_2025.md
│   │   │   ├── status_22_01_2025.md
│   │   │   ├── status_23_01_2025.md
│   │   │   └── status_25_01_2025.md
│   │   └── structure
│   │       ├── estrutura_14_01_2025.md
│   │       ├── project-structure-17-01-2025.md
│   │       ├── structure-22-01-2025.md
│   │       ├── structure-23-01-2025.md
│   │       └── estrutura_25_01_2025.md
│   ├── static
│   │   ├── css
│   │   │   ├── book-details.css
│   │   │   ├── book-search.css
│   │   │   ├── profile.css
│   │   │   └── styles.css
│   │   ├── images
│   │   │   ├── favicon.svg
│   │   │   ├── logo.png
│   │   │   └── no-cover.svg
│   │   └── js
│   │       ├── book-details.js
│   │       ├── book-search.js
│   │       ├── csrf-setup.js
│   │       └── profile.js