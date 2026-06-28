-- 系统内功预设与系统管理菜单。
-- 可重复执行：MySQL 8+ / MariaDB 10.3+。

CREATE TABLE IF NOT EXISTS system_internal_power_preset (
    preset_id bigint NOT NULL AUTO_INCREMENT COMMENT '预设ID',
    name varchar(64) NOT NULL COMMENT '内功名称',
    element_key varchar(16) NOT NULL COMMENT '元素标识',
    elements_json longtext NOT NULL COMMENT '五行JSON',
    bonus_percent double NOT NULL DEFAULT 0 COMMENT '基础百分比增益',
    bonus_type varchar(32) DEFAULT '' COMMENT '增益类型',
    bonus_desc varchar(255) DEFAULT '' COMMENT '增益描述',
    entries_json longtext NULL COMMENT '词条JSON',
    status char(1) NOT NULL DEFAULT '0' COMMENT '状态（0正常 1停用）',
    remark varchar(500) DEFAULT '' COMMENT '备注',
    create_time datetime DEFAULT NULL COMMENT '创建时间',
    update_time datetime DEFAULT NULL COMMENT '更新时间',
    PRIMARY KEY (preset_id),
    UNIQUE KEY uk_system_internal_power_preset_name_element (name, element_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统内功预设表';

INSERT INTO system_internal_power_preset (
  name, element_key, elements_json, bonus_percent, bonus_type, bonus_desc, entries_json,
  status, remark, create_time, update_time
) VALUES
  ('破釜', 'metal', '{"metal":4,"wood":0,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('贯山月', 'metal', '{"metal":4,"wood":0,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('惊羽', 'metal', '{"metal":4,"wood":0,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('击衰', 'metal', '{"metal":4,"wood":0,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('锻寒芒', 'metal', '{"metal":4,"wood":0,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('移星障', 'wood', '{"metal":0,"wood":4,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('凌穹', 'wood', '{"metal":0,"wood":4,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('沧浪行', 'wood', '{"metal":0,"wood":4,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('裁锋', 'wood', '{"metal":0,"wood":4,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('破重云', 'wood', '{"metal":0,"wood":4,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('珠明', 'water', '{"metal":0,"wood":0,"water":4,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('望惊川', 'water', '{"metal":0,"wood":0,"water":4,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('沉浪', 'water', '{"metal":0,"wood":0,"water":4,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('鲸落', 'water', '{"metal":0,"wood":0,"water":4,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('噬汐', 'water', '{"metal":0,"wood":0,"water":4,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('楚狂歌', 'fire', '{"metal":0,"wood":0,"water":0,"fire":4,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('斩精', 'fire', '{"metal":0,"wood":0,"water":0,"fire":4,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('众妙', 'fire', '{"metal":0,"wood":0,"water":0,"fire":4,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('燎原', 'fire', '{"metal":0,"wood":0,"water":0,"fire":4,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('焚刃', 'fire', '{"metal":0,"wood":0,"water":0,"fire":4,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('征袍', 'earth', '{"metal":0,"wood":0,"water":0,"fire":0,"earth":4}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('御千嶂', 'earth', '{"metal":0,"wood":0,"water":0,"fire":0,"earth":4}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('固垒', 'earth', '{"metal":0,"wood":0,"water":0,"fire":0,"earth":4}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('覆沙阙', 'earth', '{"metal":0,"wood":0,"water":0,"fire":0,"earth":4}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('纳百观', 'earth', '{"metal":0,"wood":0,"water":0,"fire":0,"earth":4}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('五韵谣', 'mixed', '{"metal":1,"wood":1,"water":1,"fire":1,"earth":1}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('稀有-日月两仪', 'fire', '{"metal":0,"wood":0,"water":0,"fire":4,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('稀有-日月两仪', 'earth', '{"metal":0,"wood":0,"water":0,"fire":0,"earth":4}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('稀有-不动明王', 'wood', '{"metal":0,"wood":4,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('稀有-不动明王', 'water', '{"metal":0,"wood":0,"water":4,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('稀有-绝电惊沙', 'metal', '{"metal":4,"wood":0,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('稀有-绝电惊沙', 'wood', '{"metal":0,"wood":4,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('稀有-承影锋烁', 'metal', '{"metal":4,"wood":0,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('稀有-承影锋烁', 'fire', '{"metal":0,"wood":0,"water":0,"fire":4,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('稀有-灼星贯日', 'wood', '{"metal":0,"wood":4,"water":0,"fire":0,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW()),
  ('稀有-灼星贯日', 'fire', '{"metal":0,"wood":0,"water":0,"fire":4,"earth":0}', 0, '', '', '[]', '0', '内置预设内功', NOW(), NOW())
ON DUPLICATE KEY UPDATE
  elements_json = VALUES(elements_json),
  entries_json = VALUES(entries_json),
  update_time = NOW();

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3100, '内功信息管理', 1, 10, 'internalPower', 'system/internalPower/index', '', 'SystemInternalPower', 1, 0, 'C', '0', '0', 'system:internal-power:list', 'skill', 'admin', NOW(), '', NULL, '系统内功信息管理菜单'),
  (3101, '内功信息查询', 3100, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power:query', '#', 'admin', NOW(), '', NULL, ''),
  (3102, '内功信息新增', 3100, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power:add', '#', 'admin', NOW(), '', NULL, ''),
  (3103, '内功信息修改', 3100, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power:edit', '#', 'admin', NOW(), '', NULL, ''),
  (3104, '内功信息删除', 3100, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power:remove', '#', 'admin', NOW(), '', NULL, '')
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
  (1, 3100), (1, 3101), (1, 3102), (1, 3103), (1, 3104);
