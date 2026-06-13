-- Add registration_type to guild battle registrations for signup/leave workflows.
-- Safe to run repeatedly against the local MySQL development database.

SET @guild_battle_registration_type_exists := (
  SELECT COUNT(*)
  FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'guild_battle_registration'
    AND column_name = 'registration_type'
);

SET @guild_battle_registration_type_sql := IF(
  @guild_battle_registration_type_exists = 0,
  "ALTER TABLE guild_battle_registration ADD COLUMN registration_type varchar(20) DEFAULT 'signup' COMMENT '申请类型(signup/leave)' AFTER team_id",
  "SELECT 1"
);

PREPARE guild_battle_registration_type_stmt FROM @guild_battle_registration_type_sql;
EXECUTE guild_battle_registration_type_stmt;
DEALLOCATE PREPARE guild_battle_registration_type_stmt;

UPDATE guild_battle_registration
SET registration_type = 'signup'
WHERE registration_type IS NULL OR registration_type = '';
