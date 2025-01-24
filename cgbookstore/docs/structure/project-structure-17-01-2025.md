# Estrutura do Projeto Django Bookstore

```
bookstore/
│
├── .venv/
├── .env
├── .gitignore
├── manage.py
├── requirements.txt
│
└── cgbookstore/
    ├── apps/
    │   └── core/
    │       ├── management/
    │       │   └── commands/
    │       │       ├── create_profiles.py
    │       │       ├── generate_project_structure.py
    │       │       └── generate_tables.py
    │       │
    │       ├── migrations/
    │       │
    │       ├── models/
    │       │   ├── book.py
    │       │   ├── profile.py
    │       │   └── user.py
    │       │
    │       ├── serializers/
    │       │   └── user_serializer.py
    │       │
    │       ├── templates/
    │       │   ├── admin/
    │       │   │   └── index.html
    │       │   │
    │       │   └── core/
    │       │       ├── book/            # Novo
    │       │       │   └── search.html  # Novo
    │       │       │
    │       │       ├── email/
    │       │       ├── password/
    │       │       │   ├── password_reset_complete.html
    │       │       │   ├── password_reset_confirm.html
    │       │       │   ├── password_reset_done.html
    │       │       │   ├── password_reset_email.html
    │       │       │   ├── password_reset_form.html
    │       │       │   
    │       │       ├── profile/
    │       │       │   ├── profile.html
    │       │       │   └── profile_form.html
    │       │       │      
    │       │       ├── base.html
    │       │       ├── contato.html
    │       │       ├── home.html
    │       │       ├── login.html
    │       │       ├── register.html
    │       │       ├── sobre.html
    │       │       ├── politica_privacidade.html
    │       │       └── termos_uso.html
    │       │
    │       ├── tests/
    │       │   ├── test_models.py
    │       │   └── test_views.py
    │       │
    │       ├── views/
    │       │   ├── auth.py
    │       │   ├── book.py             # Novo
    │       │   ├── general.py
    │       │   └── profile.py
    │       │
    │       ├── admin.py
    │       ├── apps.py
    │       ├── forms.py
    │       ├── signals.py
    │       └── urls.py
    │
    ├── config/
    │   ├── settings.py
    │   ├── urls.py
    │   ├── wsgi.py
    │   └── asgi.py
    │
    ├── docs/
    │   ├── structure.md
    │   └── status_17_01_2025.md       # Novo
    │
    ├── media/
    │   ├── livros/
    │   └── users/
    │
    ├── static/
    │   ├── css/
    │   │   ├── book-search.css        # Novo
    │   │   ├── profile.css
    │   │   └── styles.css
    │   │
    │   ├── images/
    │   │   ├── logo.png
    │   │   └── no-cover.svg           # Novo
    │   │
    │   └── js/
    │       ├── book-search.js         # Novo
    │       └── csrf-setup.js
    │
    ├── db.sqlite3
    └── requirements.txt
```