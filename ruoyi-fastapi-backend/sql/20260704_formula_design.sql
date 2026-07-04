CREATE TABLE IF NOT EXISTS system_damage_formula_version (
  version_id bigint NOT NULL AUTO_INCREMENT COMMENT '公式版本ID',
  version_name varchar(100) NOT NULL COMMENT '版本名称',
  formula_scope varchar(64) NOT NULL COMMENT '公式作用域',
  status varchar(16) NOT NULL DEFAULT 'draft' COMMENT '状态（draft草稿 published已发布 archived历史）',
  formula_package_json longtext NOT NULL COMMENT '公式包JSON',
  remark varchar(500) DEFAULT '' COMMENT '备注',
  publish_time datetime DEFAULT NULL COMMENT '发布时间',
  create_by varchar(64) DEFAULT '' COMMENT '创建者',
  create_time datetime DEFAULT NULL COMMENT '创建时间',
  update_by varchar(64) DEFAULT '' COMMENT '更新者',
  update_time datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (version_id),
  KEY idx_formula_scope_status (formula_scope, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统伤害公式版本表';

ALTER TABLE system_damage_formula_version
  MODIFY COLUMN formula_package_json LONGTEXT NOT NULL COMMENT '公式包JSON';

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES (
  3140, '公式设计', 1, 13, 'formulaDesign', 'system/formulaDesign/index', '',
  'SystemFormulaDesign', 1, 0, 'C', '0', '0', 'system:formula-design:list',
  'edit', 'admin', NOW(), '', NULL, '系统内功PVP收益公式设计菜单'
)
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

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3141, '公式版本查询', 3140, 1, '#', '', '', '', 1, 0, 'F', '0', '0',
   'system:formula-design:query', '#', 'admin', NOW(), '', NULL, ''),
  (3142, '公式版本新增', 3140, 2, '#', '', '', '', 1, 0, 'F', '0', '0',
   'system:formula-design:add', '#', 'admin', NOW(), '', NULL, ''),
  (3143, '公式版本修改', 3140, 3, '#', '', '', '', 1, 0, 'F', '0', '0',
   'system:formula-design:edit', '#', 'admin', NOW(), '', NULL, ''),
  (3144, '公式版本发布', 3140, 4, '#', '', '', '', 1, 0, 'F', '0', '0',
   'system:formula-design:publish', '#', 'admin', NOW(), '', NULL, '')
ON DUPLICATE KEY UPDATE
  menu_name = VALUES(menu_name),
  parent_id = VALUES(parent_id),
  perms = VALUES(perms),
  update_by = 'admin',
  update_time = NOW(),
  remark = VALUES(remark);

INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
  (1, 3140), (1, 3141), (1, 3142), (1, 3143), (1, 3144);
