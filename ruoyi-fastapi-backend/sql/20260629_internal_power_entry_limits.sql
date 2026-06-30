-- 系统内功词条上限迁移。
-- 可重复执行：使用 information_schema 判断字段，兼容不支持 ADD COLUMN IF NOT EXISTS 的 MySQL 版本。

SET @column_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'system_internal_power_entry'
    AND COLUMN_NAME = 'limit_text'
);
SET @ddl := IF(
  @column_exists = 0,
  'ALTER TABLE system_internal_power_entry ADD COLUMN limit_text varchar(32) DEFAULT '''' COMMENT ''固定上限展示值'' AFTER conversion_desc',
  'SELECT 1'
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @column_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'system_internal_power_entry'
    AND COLUMN_NAME = 'limit_value'
);
SET @ddl := IF(
  @column_exists = 0,
  'ALTER TABLE system_internal_power_entry ADD COLUMN limit_value double DEFAULT NULL COMMENT ''固定上限数值'' AFTER limit_text',
  'SELECT 1'
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @column_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'system_internal_power_entry'
    AND COLUMN_NAME = 'value_type'
);
SET @ddl := IF(
  @column_exists = 0,
  'ALTER TABLE system_internal_power_entry ADD COLUMN value_type varchar(16) NOT NULL DEFAULT ''number'' COMMENT ''数值类型（number数值 percent百分比）'' AFTER limit_value',
  'SELECT 1'
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE system_internal_power_entry
SET
  limit_text = CASE entry_name
    WHEN '攻击' THEN '33'
    WHEN '力量/气海' THEN '10'
    WHEN '赛年伤害/治疗提高' THEN '1.7%'
    WHEN '最小攻击' THEN '36'
    WHEN '最大攻击' THEN '36'
    WHEN '流派克制' THEN '1.2%'
    WHEN '破防' THEN '33'
    WHEN '会心' THEN '66'
    WHEN '耐力' THEN '10'
    WHEN '根骨' THEN '10'
    WHEN '身法' THEN '10'
    WHEN '内功防御' THEN '36'
    WHEN '首领抵御' THEN '1.2%'
    WHEN '流派抵御' THEN '1.2%'
    WHEN '抗会心' THEN '66'
    WHEN '防御' THEN '33'
    WHEN '气血上限' THEN '991'
    WHEN '首领克制' THEN '1.2%'
    WHEN '抗内功会心' THEN '72'
    WHEN '抗外功会心' THEN '72'
    WHEN '外功防御' THEN '36'
    ELSE limit_text
  END,
  limit_value = CASE entry_name
    WHEN '攻击' THEN 33
    WHEN '力量/气海' THEN 10
    WHEN '赛年伤害/治疗提高' THEN 1.7
    WHEN '最小攻击' THEN 36
    WHEN '最大攻击' THEN 36
    WHEN '流派克制' THEN 1.2
    WHEN '破防' THEN 33
    WHEN '会心' THEN 66
    WHEN '耐力' THEN 10
    WHEN '根骨' THEN 10
    WHEN '身法' THEN 10
    WHEN '内功防御' THEN 36
    WHEN '首领抵御' THEN 1.2
    WHEN '流派抵御' THEN 1.2
    WHEN '抗会心' THEN 66
    WHEN '防御' THEN 33
    WHEN '气血上限' THEN 991
    WHEN '首领克制' THEN 1.2
    WHEN '抗内功会心' THEN 72
    WHEN '抗外功会心' THEN 72
    WHEN '外功防御' THEN 36
    ELSE limit_value
  END,
  value_type = CASE entry_name
    WHEN '赛年伤害/治疗提高' THEN 'percent'
    WHEN '流派克制' THEN 'percent'
    WHEN '首领抵御' THEN 'percent'
    WHEN '流派抵御' THEN 'percent'
    WHEN '首领克制' THEN 'percent'
    ELSE value_type
  END,
  update_time = NOW()
WHERE (limit_value IS NULL OR limit_text IS NULL OR limit_text = '')
  AND entry_name IN (
    '攻击', '力量/气海', '赛年伤害/治疗提高', '最小攻击', '最大攻击', '流派克制',
    '破防', '会心', '耐力', '根骨', '身法', '内功防御', '首领抵御', '流派抵御',
    '抗会心', '防御', '气血上限', '首领克制', '抗内功会心', '抗外功会心', '外功防御'
  );

UPDATE sys_menu
SET visible = '0',
    status = '0',
    update_by = 'admin',
    update_time = NOW(),
    remark = CASE
      WHEN menu_id = 3110 THEN '系统内功词条管理菜单；词条上限由管理员维护'
      ELSE remark
    END
WHERE menu_id IN (3110, 3111, 3112, 3113, 3114)
   OR perms LIKE 'system:internal-power-entry:%';

INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
  (1, 3110), (1, 3111), (1, 3112), (1, 3113), (1, 3114),
  (2, 3110), (2, 3111);
