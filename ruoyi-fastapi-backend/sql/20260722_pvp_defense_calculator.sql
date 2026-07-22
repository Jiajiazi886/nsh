-- PVP 防守计算器：管理员维护多套进攻方面板，普通用户在个人管理中选择并计算承伤收益。

CREATE TABLE IF NOT EXISTS system_pvp_attack_panel (
  panel_id BIGINT NOT NULL AUTO_INCREMENT COMMENT '面板主键',
  panel_name VARCHAR(100) NOT NULL COMMENT '面板名称',
  panel_json LONGTEXT NOT NULL COMMENT '进攻方面板JSON',
  status CHAR(1) NOT NULL DEFAULT '0' COMMENT '状态（0启用 1停用）',
  remark VARCHAR(500) DEFAULT '' COMMENT '备注',
  create_by VARCHAR(64) DEFAULT '' COMMENT '创建者',
  create_time DATETIME NULL COMMENT '创建时间',
  update_by VARCHAR(64) DEFAULT '' COMMENT '更新者',
  update_time DATETIME NULL COMMENT '更新时间',
  PRIMARY KEY (panel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统PVP进攻方面板表';

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3160, '进攻方面板设置', 1, 14, 'pvpAttackPanel', 'system/pvpAttackPanel/index', '', 'SystemPvpAttackPanel', 1, 0, 'C', '0', '0', 'system:pvp-attack-panel:list', 'histogram', 'admin', NOW(), '', NULL, '管理员维护防守计算器进攻方面板'),
  (3161, '进攻方面板查询', 3160, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:pvp-attack-panel:query', '#', 'admin', NOW(), '', NULL, ''),
  (3162, '进攻方面板新增', 3160, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:pvp-attack-panel:add', '#', 'admin', NOW(), '', NULL, ''),
  (3163, '进攻方面板修改', 3160, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:pvp-attack-panel:edit', '#', 'admin', NOW(), '', NULL, ''),
  (3164, '进攻方面板删除', 3160, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:pvp-attack-panel:remove', '#', 'admin', NOW(), '', NULL, '')
ON DUPLICATE KEY UPDATE
  menu_name = VALUES(menu_name), parent_id = VALUES(parent_id), order_num = VALUES(order_num),
  path = VALUES(path), component = VALUES(component), route_name = VALUES(route_name),
  menu_type = VALUES(menu_type), visible = VALUES(visible), status = VALUES(status), perms = VALUES(perms),
  icon = VALUES(icon), update_by = 'admin', update_time = NOW(), remark = VALUES(remark);

DELETE rm
FROM sys_role_menu rm
JOIN sys_role r ON r.role_id = rm.role_id
WHERE rm.menu_id IN (3160, 3161, 3162, 3163, 3164) AND r.role_key <> 'admin';

INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, m.menu_id
FROM sys_role r
JOIN sys_menu m ON m.menu_id IN (3160, 3161, 3162, 3163, 3164)
WHERE r.role_key = 'admin';
