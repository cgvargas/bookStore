-- Índices da tabela: user_user_permissions
-- Gerado em: 02/02/2025 08:57:18

CREATE UNIQUE INDEX "core_user_user_permissions_user_id_permission_id_73ea0daa_uniq" ON "user_user_permissions" ("user_id", "permission_id");
CREATE INDEX "core_user_user_permissions_user_id_085123d3" ON "user_user_permissions" ("user_id");
CREATE INDEX "core_user_user_permissions_permission_id_35ccf601" ON "user_user_permissions" ("permission_id");
