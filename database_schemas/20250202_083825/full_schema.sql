-- Schema completo do banco de dados
-- Gerado em: 02/02/2025 08:38:25


-- Tabela: django_migrations
CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, "applied" datetime NOT NULL);


-- Tabela: django_content_type
CREATE TABLE "django_content_type" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app_label" varchar(100) NOT NULL, "model" varchar(100) NOT NULL);

-- Índices da tabela django_content_type
CREATE UNIQUE INDEX "django_content_type_app_label_model_76bd3d3b_uniq" ON "django_content_type" ("app_label", "model");


-- Tabela: auth_group_permissions
CREATE TABLE "auth_group_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Índices da tabela auth_group_permissions
CREATE UNIQUE INDEX "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" ON "auth_group_permissions" ("group_id", "permission_id");
CREATE INDEX "auth_group_permissions_group_id_b120cbf9" ON "auth_group_permissions" ("group_id");
CREATE INDEX "auth_group_permissions_permission_id_84c5c92e" ON "auth_group_permissions" ("permission_id");


-- Tabela: auth_permission
CREATE TABLE "auth_permission" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "codename" varchar(100) NOT NULL, "name" varchar(255) NOT NULL);

-- Índices da tabela auth_permission
CREATE UNIQUE INDEX "auth_permission_content_type_id_codename_01ab375a_uniq" ON "auth_permission" ("content_type_id", "codename");
CREATE INDEX "auth_permission_content_type_id_2f476e4b" ON "auth_permission" ("content_type_id");


-- Tabela: auth_group
CREATE TABLE "auth_group" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL UNIQUE);

-- Índices da tabela auth_group


-- Tabela: user_groups
CREATE TABLE "user_groups" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" bigint NOT NULL REFERENCES "user" ("id") DEFERRABLE INITIALLY DEFERRED, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Índices da tabela user_groups
CREATE UNIQUE INDEX "core_user_groups_user_id_group_id_c82fcad1_uniq" ON "user_groups" ("user_id", "group_id");
CREATE INDEX "core_user_groups_user_id_70b4d9b8" ON "user_groups" ("user_id");
CREATE INDEX "core_user_groups_group_id_fe8c697f" ON "user_groups" ("group_id");


-- Tabela: user_user_permissions
CREATE TABLE "user_user_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" bigint NOT NULL REFERENCES "user" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);

-- Índices da tabela user_user_permissions
CREATE UNIQUE INDEX "core_user_user_permissions_user_id_permission_id_73ea0daa_uniq" ON "user_user_permissions" ("user_id", "permission_id");
CREATE INDEX "core_user_user_permissions_user_id_085123d3" ON "user_user_permissions" ("user_id");
CREATE INDEX "core_user_user_permissions_permission_id_35ccf601" ON "user_user_permissions" ("permission_id");


-- Tabela: django_admin_log
CREATE TABLE "django_admin_log" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "object_id" text NULL, "object_repr" varchar(200) NOT NULL, "action_flag" smallint unsigned NOT NULL CHECK ("action_flag" >= 0), "change_message" text NOT NULL, "content_type_id" integer NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" bigint NOT NULL REFERENCES "user" ("id") DEFERRABLE INITIALLY DEFERRED, "action_time" datetime NOT NULL);

-- Índices da tabela django_admin_log
CREATE INDEX "django_admin_log_content_type_id_c4bce8eb" ON "django_admin_log" ("content_type_id");
CREATE INDEX "django_admin_log_user_id_c564eba6" ON "django_admin_log" ("user_id");


-- Tabela: user
CREATE TABLE "user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "first_name" varchar(150) NOT NULL, "last_name" varchar(150) NOT NULL, "email" varchar(254) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "cpf" varchar(11) NOT NULL UNIQUE, "data_nascimento" date NULL, "foto" varchar(100) NULL, "modified" datetime NOT NULL, "telefone" varchar(15) NULL, "email_verification_token" varchar(100) NULL, "email_verified" bool NOT NULL);

-- Índices da tabela user


-- Tabela: django_session
CREATE TABLE "django_session" ("session_key" varchar(40) NOT NULL PRIMARY KEY, "session_data" text NOT NULL, "expire_date" datetime NOT NULL);

-- Índices da tabela django_session
CREATE INDEX "django_session_expire_date_a5c62663" ON "django_session" ("expire_date");


-- Tabela: core_userbookshelf
CREATE TABLE "core_userbookshelf" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "shelf_type" varchar(20) NOT NULL, "added_at" datetime NOT NULL, "book_id" bigint NOT NULL REFERENCES "core_book" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" bigint NOT NULL REFERENCES "user" ("id") DEFERRABLE INITIALLY DEFERRED, "updated_at" datetime NOT NULL);

-- Índices da tabela core_userbookshelf
CREATE INDEX "cgbookstore_bookshelf_book_id_3df67bdb" ON "core_userbookshelf" ("book_id");
CREATE INDEX "cgbookstore_bookshelf_user_id_b1a1c76f" ON "core_userbookshelf" ("user_id");


-- Tabela: core_profile
CREATE TABLE "core_profile" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "bio" text NOT NULL, "location" varchar(30) NOT NULL, "birth_date" date NULL, "interests" text NOT NULL, "social_links" text NOT NULL CHECK ((JSON_VALID("social_links") OR "social_links" IS NULL)), "updated_at" datetime NOT NULL, "user_id" bigint NOT NULL UNIQUE REFERENCES "user" ("id") DEFERRABLE INITIALLY DEFERRED, "card_style" text NOT NULL CHECK ((JSON_VALID("card_style") OR "card_style" IS NULL)));

-- Índices da tabela core_profile


-- Tabela: core_banner
CREATE TABLE "core_banner" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "titulo" varchar(200) NOT NULL, "subtitulo" varchar(300) NOT NULL, "descricao" text NOT NULL, "imagem" varchar(100) NOT NULL, "imagem_mobile" varchar(100) NULL, "link" varchar(500) NOT NULL, "ordem" integer NOT NULL, "ativo" bool NOT NULL, "data_inicio" datetime NOT NULL, "data_fim" datetime NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL);


-- Tabela: core_book
CREATE TABLE "core_book" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "titulo" varchar(200) NOT NULL, "autor" varchar(200) NOT NULL, "descricao" text NOT NULL, "data_publicacao" date NULL, "capa" varchar(100) NULL, "editora" varchar(100) NOT NULL, "categoria" varchar(100) NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "adaptacoes" text NOT NULL, "apendices" text NOT NULL, "bibliografia" text NOT NULL, "citacoes" text NOT NULL, "classificacao" varchar(50) NOT NULL, "colecao" varchar(200) NOT NULL, "curiosidades" text NOT NULL, "dimensoes" varchar(50) NOT NULL, "edicao" varchar(50) NOT NULL, "enredo" text NOT NULL, "formato" varchar(50) NOT NULL, "genero" varchar(100) NOT NULL, "glossario" text NOT NULL, "idioma" varchar(50) NOT NULL, "ilustrador" varchar(200) NOT NULL, "indice" text NOT NULL, "isbn" varchar(13) NOT NULL, "localizacao" varchar(100) NOT NULL, "notas" text NOT NULL, "numero_paginas" integer NULL, "personagens" text NOT NULL, "peso" varchar(20) NOT NULL, "posfacio" text NOT NULL, "prefacio" text NOT NULL, "premios" text NOT NULL, "publico_alvo" varchar(100) NOT NULL, "redes_sociais" text NOT NULL CHECK ((JSON_VALID("redes_sociais") OR "redes_sociais" IS NULL)), "subtitulo" varchar(200) NOT NULL, "temas" text NOT NULL, "tradutor" varchar(200) NOT NULL, "website" varchar(200) NOT NULL, "capa_preview" varchar(100) NULL, "adaptado_filme" bool NOT NULL, "e_destaque" bool NOT NULL, "e_lancamento" bool NOT NULL, "e_manga" bool NOT NULL, "ordem_exibicao" integer NOT NULL, "quantidade_acessos" integer NOT NULL, "quantidade_vendida" integer NOT NULL, "tipo_shelf_especial" varchar(50) NOT NULL, "preco_promocional" decimal NULL, "preco" decimal NULL);

