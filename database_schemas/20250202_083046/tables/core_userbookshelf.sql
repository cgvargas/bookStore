-- Tabela: core_userbookshelf
-- Gerado em: 02/02/2025 08:30:47

CREATE TABLE "core_userbookshelf" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "shelf_type" varchar(20) NOT NULL, "added_at" datetime NOT NULL, "book_id" bigint NOT NULL REFERENCES "core_book" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" bigint NOT NULL REFERENCES "user" ("id") DEFERRABLE INITIALLY DEFERRED, "updated_at" datetime NOT NULL);
