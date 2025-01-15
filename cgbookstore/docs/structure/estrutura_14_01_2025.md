# Estrutura do Projeto

📦 bookstore
 ┣ 📂 .venv
 ┣ 📂 cgbookstore
 ┃ ┣ 📂 apps
 ┃ ┃ ┣ 📂 core
 ┃ ┃ ┃ ┣ 📂 migrations
 ┃ ┃ ┃ ┃ ┗ __init__.py
 ┃ ┃ ┃ ┣ 📂 models
 ┃ ┃ ┃ ┃ ┣ __init__.py
 ┃ ┃ ┃ ┃ ┗ user.py
 ┃ ┃ ┃ ┣ 📂 serializers
 ┃ ┃ ┃ ┃ ┣ __init__.py
 ┃ ┃ ┃ ┃ ┗ user_serializer.py
 ┃ ┃ ┃ ┣ 📂 templates
 ┃ ┃ ┃ ┃ ┗ 📂 core
 ┃ ┃ ┃ ┃ ┃ ┣ base.html
 ┃ ┃ ┃ ┃ ┃ ┣ home.html
 ┃ ┃ ┃ ┃ ┃ ┣ politica_privacidade.html
 ┃ ┃ ┃ ┃ ┃ ┣ register.html
 ┃ ┃ ┃ ┃ ┃ ┣ sobre.html
 ┃ ┃ ┃ ┃ ┃ ┣ termos_uso.html
 ┃ ┃ ┃ ┃ ┃ ┣ login.html
 ┃ ┃ ┃ ┃ ┃ ┗ 📂 password
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ password_reset_form.html
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ password_reset_done.html
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ password_reset_confirm.html
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ password_reset_complete.html
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ password_reset_email.html
 ┃ ┃ ┃ ┃ ┃ ┃ ┗ password_reset_subject.txt
 ┃ ┃ ┃ ┣ 📂 tests
 ┃ ┃ ┃ ┣ 📂 views
 ┃ ┃ ┃ ┃ ┣ __init__.py
 ┃ ┃ ┃ ┃ ┣ general.py
 ┃ ┃ ┃ ┃ ┗ auth.py
 ┃ ┃ ┃ ┣ __init__.py
 ┃ ┃ ┃ ┣ admin.py
 ┃ ┃ ┃ ┣ apps.py
 ┃ ┃ ┃ ┣ forms.py
 ┃ ┃ ┃ ┣ tests.py
 ┃ ┃ ┃ ┗ urls.py
 ┃ ┃ ┗ __init__.py
 ┃ ┣ 📂 config
 ┃ ┃ ┣ __init__.py
 ┃ ┃ ┣ asgi.py
 ┃ ┃ ┣ settings.py
 ┃ ┃ ┣ urls.py
 ┃ ┃ ┗ wsgi.py
 ┃ ┣ 📂 docs
 ┃ ┣ 📂 media
 ┃ ┣ 📂 static
 ┃ ┃ ┣ 📂 css
 ┃ ┃ ┃ ┗ styles.css
 ┃ ┃ ┣ 📂 images
 ┃ ┃ ┃ ┗ logo.png
 ┃ ┃ ┗ 📂 js
 ┃ ┃ ┃ ┗ csrf-setup.js
 ┃ ┣ __init__.py
 ┃ ┗ requirements.txt
 ┣ .env
 ┣ manage.py
 ┗ requirements.txt