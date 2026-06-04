-- Permission for applying a saved schedule history snapshot.

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3018, 'Apply Schedule History', 2006, 9, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:apply', '#', 'admin', NOW(), '', NULL, '')
ON DUPLICATE KEY UPDATE
  menu_name = VALUES(menu_name),
  parent_id = VALUES(parent_id),
  order_num = VALUES(order_num),
  perms = VALUES(perms),
  update_by = 'admin',
  update_time = NOW();

INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
  (1, 3018),
  (2, 3018);
