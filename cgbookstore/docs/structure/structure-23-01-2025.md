**Estrutura do projeto:**

* **cgbookstore**
    * **apps**
        * **core**
            * **models**
                * book.py
                * profile.py
                * user.py
            * **templates**
                * **core**
                    * base.html
                    * book
                        * search.html
                        * book_details.html       # NOVO
                    * email
                        * email_verification.html
                    * home.html
                    * login.html
                    * password
                        * password_reset_confirm.html
                        * password_reset_done.html
                        * password_reset_email.html
                        * password_reset_form.html
                    * profile
                        * profile.html
                        * profile_form.html
                    * register.html
                    * sobre.html
                    * termos_uso.html
            * **views**
                * __init__.py
                * auth.py
                * book.py
                * general.py
                * profile.py
            * **tests**
                * __init__.py
                * test_models.py
                * test_views.py
            * **management**
                * __init__.py
                * commands
            * **serializers**
                * __init__.py
                * user_serializer.py
            * **forms.py**
            * **signals.py**
        * **__init__.py**
    * **config**
        * __init__.py
        * settings.py
        * urls.py
        * wsgi.py
    * **static**
        * **css**
            * book-search.css
            * profile.css
            * book-details.css         # NOVO
            * styles.css
        * **images**
            * favicon.svg
            * logo.png
            * no-cover.svg
        * **js**
            * book-search.js
            * csrf-setup.js
            * profile.js
            * book-details.js          # NOVO
        
    * **media**
    * **db.sqlite3**
    * **requirements.txt**
    * **manage.py**
    * **.env**
    * **docs**
        * status_23_01_2025.md        # NOVO
    * **.gitignore**

**Observações:**
* Novos arquivos são marcados com # NOVO
* Estrutura mantém compatibilidade com o projeto existente
* Adicionada pasta libs para bibliotecas de terceiros
* Documentação atualizada com novo arquivo de status