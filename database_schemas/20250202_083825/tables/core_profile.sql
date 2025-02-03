-- Tabela: core_profile
-- Gerado em: 02/02/2025 08:38:25

CREATE TABLE "core_profile" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "bio" text NOT NULL, "location" varchar(30) NOT NULL, "birth_date" date NULL, "interests" text NOT NULL, "social_links" text NOT NULL CHECK ((JSON_VALID("social_links") OR "social_links" IS NULL)), "updated_at" datetime NOT NULL, "user_id" bigint NOT NULL UNIQUE REFERENCES "user" ("id") DEFERRABLE INITIALLY DEFERRED, "card_style" text NOT NULL CHECK ((JSON_VALID("card_style") OR "card_style" IS NULL)));
