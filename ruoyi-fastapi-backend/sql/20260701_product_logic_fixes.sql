-- 产品逻辑漏洞修复：个人菜单真实入口、管理员专属权限备注、内功词条兼容字段。
-- 可重复执行；不删除现有角色菜单绑定。

UPDATE sys_menu
SET component = 'personal/join/index',
    route_name = 'PersonalJoinGuild',
    remark = '加入帮会菜单',
    update_by = 'admin',
    update_time = NOW()
WHERE menu_id = 3001 OR perms = 'personal:join:list';

UPDATE sys_menu
SET component = 'personal/skill/index',
    route_name = 'PersonalSkill',
    remark = '内功管理菜单',
    update_by = 'admin',
    update_time = NOW()
WHERE menu_id = 3002 OR perms = 'personal:skill:list';

UPDATE sys_menu
SET component = 'personal/profileEdit/index',
    route_name = 'PersonalProfileEdit',
    remark = '个人信息编辑菜单',
    update_by = 'admin',
    update_time = NOW()
WHERE menu_id = 3003 OR perms = 'personal:profile:edit';

UPDATE sys_menu
SET menu_name = '管理员VIP授权修改',
    remark = '管理员用户管理能力：VIP授权修改，仅admin用户可实际操作',
    update_by = 'admin',
    update_time = NOW()
WHERE perms = 'system:user:vip:edit';

UPDATE sys_menu
SET menu_name = '管理员赞助状态修改',
    remark = '管理员用户管理能力：赞助状态修改，仅admin用户可实际操作',
    update_by = 'admin',
    update_time = NOW()
WHERE perms = 'system:user:sponsor:edit';

UPDATE sys_menu
SET menu_name = '管理员AI识图次数修改',
    remark = '管理员用户管理能力：AI识图次数修改，仅admin用户可实际操作',
    update_by = 'admin',
    update_time = NOW()
WHERE perms = 'system:user:ai:edit';

SET @schema_name := DATABASE();

SET @sql := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE system_internal_power_entry ADD COLUMN conversion_percent double DEFAULT NULL COMMENT ''数值转换百分比'' AFTER entry_name',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @schema_name
    AND TABLE_NAME = 'system_internal_power_entry'
    AND COLUMN_NAME = 'conversion_percent'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE system_internal_power_entry ADD COLUMN conversion_desc varchar(255) DEFAULT '''' COMMENT ''转换说明'' AFTER conversion_percent',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @schema_name
    AND TABLE_NAME = 'system_internal_power_entry'
    AND COLUMN_NAME = 'conversion_desc'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE system_internal_power_entry ADD COLUMN limit_text varchar(32) DEFAULT '''' COMMENT ''固定上限展示值'' AFTER conversion_desc',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @schema_name
    AND TABLE_NAME = 'system_internal_power_entry'
    AND COLUMN_NAME = 'limit_text'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE system_internal_power_entry ADD COLUMN limit_value double DEFAULT NULL COMMENT ''固定上限数值'' AFTER limit_text',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @schema_name
    AND TABLE_NAME = 'system_internal_power_entry'
    AND COLUMN_NAME = 'limit_value'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE system_internal_power_entry ADD COLUMN value_type varchar(16) NOT NULL DEFAULT ''number'' COMMENT ''数值类型（number数值 percent百分比）'' AFTER limit_value',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @schema_name
    AND TABLE_NAME = 'system_internal_power_entry'
    AND COLUMN_NAME = 'value_type'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
