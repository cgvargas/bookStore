-- Tabela: user
-- Gerado em: 02/02/2025 08:30:47

CREATE TABLE "user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "first_name" varchar(150) NOT NULL, "last_name" varchar(150) NOT NULL, "email" varchar(254) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "cpf" varchar(11) NOT NULL UNIQUE, "data_nascimento" date NULL, "foto" varchar(100) NULL, "modified" datetime NOT NULL, "telefone" varchar(15) NULL, "email_verification_token" varchar(100) NULL, "email_verified" bool NOT NULL);
