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
 ┃ ┃ ┃ ┃ ┣ user.py
 ┃ ┃ ┃ ┃ ┗ profile.py  # Novo arquivo
 ┃ ┃ ┃ ┣ 📂 serializers
 ┃ ┃ ┃ ┃ ┣ __init__.py
 ┃ ┃ ┃ ┃ ┗ user_serializer.py
 ┃ ┃ ┃ ┣ 📂 templates
 ┃ ┃ ┃ ┃ ┗ 📂 core
 ┃ ┃ ┃ ┃ ┃ ┣ base.html
 ┃ ┃ ┃ ┃ ┃ ┣ home.html
 ┃ ┃ ┃ ┃ ┃ ┣ profile  # Nova pasta
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ profile.html
 ┃ ┃ ┃ ┃ ┃ ┃ ┗ profile_form.html
 ┃ ┃ ┃ ┃ ┃ ┣ politica_privacidade.html
 ┃ ┃ ┃ ┃ ┃ ┣ register.html
 ┃ ┃ ┃ ┃ ┃ ┣ sobre.html
 ┃ ┃ ┃ ┃ ┃ ┣ termos_uso.html
 ┃ ┃ ┃ ┃ ┃ ┣ login.html
 ┃ ┃ ┃ ┃ ┃ ┣ 📂 email
 ┃ ┃ ┃ ┃ ┃ ┃ ┗ email_verification.html
 ┃ ┃ ┃ ┃ ┃ ┗ 📂 password
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ [arquivos de password mantidos]
 ┃ ┃ ┃ ┣ 📂 views
 ┃ ┃ ┃ ┃ ┣ __init__.py
 ┃ ┃ ┃ ┃ ┣ general.py
 ┃ ┃ ┃ ┃ ┣ auth.py
 ┃ ┃ ┃ ┃ ┗ profile.py  # Novo arquivo
 ┃ ┃ ┃ ┣ __init__.py
 ┃ ┃ ┃ ┣ admin.py
 ┃ ┃ ┃ ┣ apps.py
 ┃ ┃ ┃ ┣ forms.py
 ┃ ┃ ┃ ┗ urls.py
 ┃ ┃ ┗ __init__.py
[resto da estrutura mantida]

## Observações sobre alterações:
- Template base.html: Revertido para versão estável anterior após tentativa de modificação do navbar
- Adicionados arquivos relacionados ao Profile
- Mantida estrutura original do projeto
- Migrations do Profile precisam ser aplicadas