-- Personal management menu placeholders.
-- Safe to run more than once against the local MySQL development database.

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3000, '个人管理', 0, 5, 'personal', 'Layout', '', '', 1, 0, 'M', '0', '0', '', 'user', 'admin', NOW(), '', NULL, '个人管理目录'),
  (3001, '加入帮会', 3000, 1, 'join', 'personal/coming-soon/index', '', '', 1, 0, 'C', '0', '0', 'personal:join:list', 'people', 'admin', NOW(), '', NULL, '加入帮会占位菜单'),
  (3002, '内功管理', 3000, 2, 'skill', 'personal/coming-soon/index', '', '', 1, 0, 'C', '0', '0', 'personal:skill:list', 'skill', 'admin', NOW(), '', NULL, '内功管理占位菜单'),
  (3003, '个人信息编辑', 3000, 3, 'profile-edit', 'personal/coming-soon/index', '', '', 1, 0, 'C', '0', '0', 'personal:profile:edit', 'edit', 'admin', NOW(), '', NULL, '个人信息编辑占位菜单'),
  (3004, '内功数值编辑', 3002, 1, '', '', '', '', 1, 0, 'F', '0', '0', 'personal:skill:value-edit', '#', 'admin', NOW(), '', NULL, '内功管理按钮权限：编辑内功种类与基础增伤')
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
  (1, 3000), (1, 3001), (1, 3002), (1, 3003),
  (1, 3004),
  (2, 3000), (2, 3001), (2, 3002), (2, 3003);
