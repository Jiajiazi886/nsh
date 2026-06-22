-- Permission for editing internal power base value catalog.
-- Safe to run more than once against the local MySQL development database.

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES (
  3004, '内功数值编辑', 3002, 1, '', '', '', '',
  1, 0, 'F', '0', '0', 'personal:skill:value-edit', '#',
  'admin', NOW(), '', NULL, '内功管理按钮权限：编辑内功种类与基础增伤'
)
ON DUPLICATE KEY UPDATE
  menu_name = VALUES(menu_name),
  parent_id = VALUES(parent_id),
  order_num = VALUES(order_num),
  menu_type = VALUES(menu_type),
  visible = VALUES(visible),
  status = VALUES(status),
  perms = VALUES(perms),
  update_by = 'admin',
  update_time = NOW(),
  remark = VALUES(remark);

INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES (1, 3004);
