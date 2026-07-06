-- 玩家面板识别历史与系统面板模板设置

CREATE TABLE IF NOT EXISTS personal_internal_power_panel_recognition_history (
  record_id bigint NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  user_id bigint NOT NULL COMMENT '用户ID',
  file_name varchar(255) DEFAULT '' COMMENT '图片文件名',
  mime_type varchar(64) DEFAULT 'image/png' COMMENT '图片MIME类型',
  image_base64 longtext COMMENT '图片Base64',
  status varchar(20) NOT NULL DEFAULT 'recognizing' COMMENT '识别状态',
  parsed_json longtext COMMENT '识别JSON',
  raw_text longtext COMMENT '模型原始文本',
  error longtext COMMENT '错误信息',
  create_time datetime DEFAULT NULL COMMENT '创建时间',
  update_time datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (record_id),
  KEY idx_personal_panel_recognition_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='个人玩家面板AI识别历史表';

CREATE TABLE IF NOT EXISTS system_internal_power_panel_template (
  template_id bigint NOT NULL AUTO_INCREMENT COMMENT '模板ID',
  template_name varchar(100) NOT NULL COMMENT '模板名称',
  status char(1) NOT NULL DEFAULT '0' COMMENT '启用状态（0启用 1停用）',
  target_panel_json longtext NOT NULL COMMENT '受击方面板JSON',
  attack_panel_json longtext NOT NULL COMMENT '攻击方面板JSON',
  remark varchar(500) DEFAULT '' COMMENT '备注',
  create_by varchar(64) DEFAULT '' COMMENT '创建者',
  create_time datetime DEFAULT NULL COMMENT '创建时间',
  update_by varchar(64) DEFAULT '' COMMENT '更新者',
  update_time datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (template_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统内功PVP收益面板模板表';

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES (
  3150, '面板模板设置', 1, 14, 'internalPowerPanelTemplate', 'system/internalPowerPanelTemplate/index', '',
  'SystemInternalPowerPanelTemplate', 1, 0, 'C', '0', '0',
  'system:internal-power-panel-template:list', 'chart', 'admin', NOW(), '', NULL,
  '系统内功PVP收益面板模板设置菜单'
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
  (3151, '面板模板查询', 3150, 1, '#', '', '', '', 1, 0, 'F', '0', '0',
   'system:internal-power-panel-template:query', '#', 'admin', NOW(), '', NULL, ''),
  (3152, '面板模板新增', 3150, 2, '#', '', '', '', 1, 0, 'F', '0', '0',
   'system:internal-power-panel-template:add', '#', 'admin', NOW(), '', NULL, ''),
  (3153, '面板模板修改', 3150, 3, '#', '', '', '', 1, 0, 'F', '0', '0',
   'system:internal-power-panel-template:edit', '#', 'admin', NOW(), '', NULL, ''),
  (3154, '面板模板删除', 3150, 4, '#', '', '', '', 1, 0, 'F', '0', '0',
   'system:internal-power-panel-template:remove', '#', 'admin', NOW(), '', NULL, ''),
  (3155, '面板模板启停', 3150, 5, '#', '', '', '', 1, 0, 'F', '0', '0',
   'system:internal-power-panel-template:status', '#', 'admin', NOW(), '', NULL, '')
ON DUPLICATE KEY UPDATE
  menu_name = VALUES(menu_name),
  parent_id = VALUES(parent_id),
  perms = VALUES(perms),
  update_by = 'admin',
  update_time = NOW(),
  remark = VALUES(remark);

INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
  (1, 3150), (1, 3151), (1, 3152), (1, 3153), (1, 3154), (1, 3155);
