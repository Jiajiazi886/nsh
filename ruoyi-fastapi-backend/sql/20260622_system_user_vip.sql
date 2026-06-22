-- VIP marker for system users.
-- Safe to run more than once against the local MySQL development database.

SET @db_name := DATABASE();

SET @ddl := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = @db_name
        AND TABLE_NAME = 'sys_user'
        AND COLUMN_NAME = 'is_vip'
    ),
    'SELECT 1',
    "ALTER TABLE sys_user ADD COLUMN is_vip char(1) NOT NULL DEFAULT '0' COMMENT 'VIP标识（0非VIP 1VIP）' AFTER status"
  )
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE sys_user
SET is_vip = '0'
WHERE is_vip IS NULL OR is_vip NOT IN ('0', '1');

UPDATE sys_user u
SET u.is_vip = '1'
WHERE u.del_flag = '0'
  AND EXISTS (
    SELECT 1
    FROM sys_user_role ur
    JOIN sys_role r ON r.role_id = ur.role_id
    WHERE ur.user_id = u.user_id
      AND r.role_key = 'admin'
      AND r.del_flag = '0'
  );
