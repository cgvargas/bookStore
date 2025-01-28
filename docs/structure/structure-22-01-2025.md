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
            * styles.css
        * **images**
            * favicon.svg
            * logo.png
            * no-cover.svg
        * **js**
            * book-search.js
            * csrf-setup.js
            * profile.js
    * **media**
    * **db.sqlite3**
    * **requirements.txt**
    * **manage.py**
    * **.env**
    * **docs**
    * **.gitignore**

**Observações:**

* O arquivo `manage.py` é o ponto de entrada para executar comandos Django.
* O arquivo `settings.py` contém as configurações do projeto.
* O arquivo `urls.py` define as URLs para acessar as diferentes páginas da aplicação.
* O arquivo `wsgi.py` é usado para deployar a aplicação em um servidor web.
* Os arquivos `.py` contêm o código Python do projeto, como modelos, views e controladores.
* Os arquivos `.html` são os templates HTML que definem a interface do usuário.
* Os arquivos `.css` e `.js` são os arquivos de estilo e JavaScript que definem o layout e comportamento da interface.
* A pasta `media` é usada para armazenar arquivos de mídia, como imagens e vídeos.
* A pasta `static` é usada para armazenar arquivos estáticos, como arquivos CSS, JavaScript e imagens.