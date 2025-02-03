-- Tabela: core_banner
-- Gerado em: 02/02/2025 08:57:18

CREATE TABLE "core_banner" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "titulo" varchar(200) NOT NULL, "subtitulo" varchar(300) NOT NULL, "descricao" text NOT NULL, "imagem" varchar(100) NOT NULL, "imagem_mobile" varchar(100) NULL, "link" varchar(500) NOT NULL, "ordem" integer NOT NULL, "ativo" bool NOT NULL, "data_inicio" datetime NOT NULL, "data_fim" datetime NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL);
