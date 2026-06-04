-- Profession info table, menu entry, and read/write permissions.
-- Safe to run more than once against the local MySQL development database.

CREATE TABLE IF NOT EXISTS guild_profession (
  profession_id bigint NOT NULL AUTO_INCREMENT COMMENT '职业ID',
  profession_name varchar(30) NOT NULL COMMENT '职业名称',
  order_num int NOT NULL DEFAULT 0 COMMENT '显示顺序',
  status char(1) NOT NULL DEFAULT '0' COMMENT '状态（0正常 1停用）',
  create_by varchar(64) DEFAULT '' COMMENT '创建者',
  create_time datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_by varchar(64) DEFAULT '' COMMENT '更新者',
  update_time datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  remark varchar(500) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (profession_id),
  UNIQUE KEY uk_guild_profession_name (profession_name),
  KEY idx_guild_profession_status_order (status, order_num)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职业信息表';

INSERT INTO guild_profession (profession_name, order_num, status, create_by, create_time, update_by, update_time, remark)
VALUES
  ('九灵', 1, '0', 'admin', NOW(), 'admin', NOW(), '系统预置职业'),
  ('沧澜', 2, '0', 'admin', NOW(), 'admin', NOW(), '系统预置职业'),
  ('潮光', 3, '0', 'admin', NOW(), 'admin', NOW(), '系统预置职业'),
  ('玄机', 4, '0', 'admin', NOW(), 'admin', NOW(), '系统预置职业'),
  ('碎梦', 5, '0', 'admin', NOW(), 'admin', NOW(), '系统预置职业'),
  ('神相', 6, '0', 'admin', NOW(), 'admin', NOW(), '系统预置职业'),
  ('素问', 7, '0', 'admin', NOW(), 'admin', NOW(), '系统预置职业'),
  ('血河', 8, '0', 'admin', NOW(), 'admin', NOW(), '系统预置职业'),
  ('铁衣', 9, '0', 'admin', NOW(), 'admin', NOW(), '系统预置职业'),
  ('鸿音', 10, '0', 'admin', NOW(), 'admin', NOW(), '系统预置职业'),
  ('龙吟', 11, '0', 'admin', NOW(), 'admin', NOW(), '系统预置职业')
ON DUPLICATE KEY UPDATE
  order_num = VALUES(order_num),
  status = VALUES(status),
  update_by = 'admin',
  update_time = NOW();

INSERT INTO guild_profession (profession_name, order_num, status, create_by, create_time, update_by, update_time, remark)
SELECT class_name, 100, '0', 'admin', NOW(), 'admin', NOW(), '从职业颜色配置迁移'
FROM guild_class_color
WHERE class_name IS NOT NULL AND class_name <> ''
GROUP BY class_name
ON DUPLICATE KEY UPDATE update_time = NOW();

DELETE duplicate_profession
FROM guild_profession duplicate_profession
JOIN guild_profession kept_profession
  ON kept_profession.profession_name = duplicate_profession.profession_name
 AND kept_profession.profession_id < duplicate_profession.profession_id;

SET @guild_profession_name_index_exists := (
  SELECT COUNT(1)
  FROM information_schema.statistics
  WHERE table_schema = DATABASE()
    AND table_name = 'guild_profession'
    AND index_name = 'uk_guild_profession_name'
);
SET @guild_profession_name_index_sql := IF(
  @guild_profession_name_index_exists = 0,
  'ALTER TABLE guild_profession ADD UNIQUE KEY uk_guild_profession_name (profession_name)',
  'SELECT 1'
);
PREPARE guild_profession_name_index_stmt FROM @guild_profession_name_index_sql;
EXECUTE guild_profession_name_index_stmt;
DEALLOCATE PREPARE guild_profession_name_index_stmt;

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3028, '职业信息', 1065, 8, 'profession', 'guild/profession/index', '', 'GuildProfession', 1, 0, 'C', '0', '0', 'guild:profession:read', 'dict', 'admin', NOW(), '', NULL, '职业信息菜单'),
  (3029, '职业信息读取', 3028, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:profession:read', '#', 'admin', NOW(), '', NULL, '职业信息读权限'),
  (3030, '职业信息写入', 3028, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:profession:write', '#', 'admin', NOW(), '', NULL, '职业信息写权限')
ON DUPLICATE KEY UPDATE
  menu_name = VALUES(menu_name),
  parent_id = VALUES(parent_id),
  order_num = VALUES(order_num),
  path = VALUES(path),
  component = VALUES(component),
  query = VALUES(query),
  route_name = VALUES(route_name),
  is_frame = VALUES(is_frame),
  is_cache = VALUES(is_cache),
  menu_type = VALUES(menu_type),
  visible = VALUES(visible),
  status = VALUES(status),
  perms = VALUES(perms),
  icon = VALUES(icon),
  remark = VALUES(remark),
  update_by = 'admin',
  update_time = NOW();

INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, m.menu_id
FROM sys_role r
JOIN sys_menu m ON m.menu_id IN (3028, 3029, 3030)
WHERE r.role_key IN ('admin', 'common');
