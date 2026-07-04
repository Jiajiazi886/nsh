-- 个人内功PVP收益面板设置。
-- 可重复执行：MySQL 8+ / MariaDB 10.3+。

CREATE TABLE IF NOT EXISTS personal_internal_power_panel_setting (
    user_id bigint NOT NULL COMMENT '用户ID',
    target_panel_json longtext NOT NULL COMMENT '受击方面板JSON',
    attack_panel_json longtext NOT NULL COMMENT '攻击方无内功基础面板JSON',
    create_time datetime DEFAULT NULL COMMENT '创建时间',
    update_time datetime DEFAULT NULL COMMENT '更新时间',
    PRIMARY KEY (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='个人内功PVP收益面板设置表';

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3115, '面板设置', 3000, 7, 'internal-power-panel', 'personal/internalPowerPanel/index', '', 'PersonalInternalPowerPanel', 1, 0, 'C', '0', '0', 'personal:internal-power-panel:list', 'chart', 'admin', NOW(), '', NULL, '个人内功PVP收益面板设置菜单'),
  (3116, '面板设置保存', 3115, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'personal:internal-power-panel:edit', '#', 'admin', NOW(), '', NULL, '')
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
  (1, 3115), (1, 3116),
  (2, 3115), (2, 3116);
