-- Índices da tabela: user_groups
-- Gerado em: 02/02/2025 08:57:18

CREATE UNIQUE INDEX "core_user_groups_user_id_group_id_c82fcad1_uniq" ON "user_groups" ("user_id", "group_id");
CREATE INDEX "core_user_groups_user_id_70b4d9b8" ON "user_groups" ("user_id");
CREATE INDEX "core_user_groups_group_id_fe8c697f" ON "user_groups" ("group_id");
