-- 系统内功词条与系统管理菜单。
-- 可重复执行：MySQL 8+ / MariaDB 10.3+。

CREATE TABLE IF NOT EXISTS system_internal_power_entry (
    entry_id bigint NOT NULL AUTO_INCREMENT COMMENT '词条ID',
    entry_name varchar(64) NOT NULL COMMENT '词条名称',
    conversion_percent double DEFAULT NULL COMMENT '数值转换百分比',
    conversion_desc varchar(255) DEFAULT '' COMMENT '转换说明',
    status char(1) NOT NULL DEFAULT '0' COMMENT '状态（0正常 1停用）',
    remark varchar(500) DEFAULT '' COMMENT '备注',
    create_time datetime DEFAULT NULL COMMENT '创建时间',
    update_time datetime DEFAULT NULL COMMENT '更新时间',
    PRIMARY KEY (entry_id),
    UNIQUE KEY uk_system_internal_power_entry_name (entry_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统内功词条表';

INSERT INTO system_internal_power_entry (
  entry_name, conversion_percent, conversion_desc, status, remark, create_time, update_time
) VALUES
  ('攻击', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('力量/气海', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('赛年伤害/治疗提高', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('最小攻击', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('最大攻击', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('流派克制', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('破防', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('会心', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('耐力', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('根骨', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('身法', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('内功防御', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('首领抵御', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('流派抵御', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('抗会心', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('防御', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('气血上限', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('首领克制', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('抗内功会心', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('抗外功会心', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('外功防御', NULL, '', '0', '内置内功词条', NOW(), NOW()),
  ('灵韵', NULL, '', '0', '内置内功词条', NOW(), NOW())
ON DUPLICATE KEY UPDATE
  update_time = NOW();

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3110, '内功词条管理', 1, 11, 'internalPowerEntry', 'system/internalPowerEntry/index', '', 'SystemInternalPowerEntry', 1, 0, 'C', '0', '0', 'system:internal-power-entry:list', 'list', 'admin', NOW(), '', NULL, '系统内功词条管理菜单'),
  (3111, '内功词条查询', 3110, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-entry:query', '#', 'admin', NOW(), '', NULL, ''),
  (3112, '内功词条新增', 3110, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-entry:add', '#', 'admin', NOW(), '', NULL, ''),
  (3113, '内功词条修改', 3110, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-entry:edit', '#', 'admin', NOW(), '', NULL, ''),
  (3114, '内功词条删除', 3110, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-entry:remove', '#', 'admin', NOW(), '', NULL, '')
ON DUPLICATE KEY UPDATE
  menu_name = VALUES(menu_name),
  parent_id = VALUES(parent_id),
  order_num = VALUES(order_num),
  path = VALUES(path),
  component = VALUES(component),
  route_name = VALUES(route_name),
  menu_type = VALUES(menu_type),
  visible = VALUES(visible),
  status = VALUES(status),
  perms = VALUES(perms),
  icon = VALUES(icon),
  update_by = 'admin',
  update_time = NOW(),
  remark = VALUES(remark);

INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
  (1, 3110), (1, 3111), (1, 3112), (1, 3113), (1, 3114);
