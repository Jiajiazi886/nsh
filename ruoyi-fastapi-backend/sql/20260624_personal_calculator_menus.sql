-- Personal calculator placeholder menus.
-- Safe to run more than once against the local MySQL development database.

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3005, '防守计算器', 3000, 4, 'defense-calculator', 'personal/calculator/index', '', '', 1, 0, 'C', '0', '0', 'personal:defense-calculator:list', 'shield', 'admin', NOW(), '', NULL, '防守计算器占位菜单'),
  (3006, '拆塔计算器', 3000, 5, 'tower-calculator', 'personal/calculator/index', '', '', 1, 0, 'C', '0', '0', 'personal:tower-calculator:list', 'build', 'admin', NOW(), '', NULL, '拆塔计算器占位菜单'),
  (3007, '素/鸿计算器', 3000, 6, 'suhong-calculator', 'personal/calculator/index', '', '', 1, 0, 'C', '0', '0', 'personal:suhong-calculator:list', 'calculator', 'admin', NOW(), '', NULL, '素/鸿计算器占位菜单')
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
  update_by = 'admin',
  update_time = NOW(),
  remark = VALUES(remark);

INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
  (1, 3005), (1, 3006), (1, 3007),
  (2, 3005), (2, 3006), (2, 3007);
