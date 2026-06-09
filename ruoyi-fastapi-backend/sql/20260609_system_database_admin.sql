-- 超级管理员数据库管理菜单与权限（只读）
-- 作用：在“系统管理”下新增“数据库管理”，并把菜单和权限绑定给 admin 角色。

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3040, '数据库管理', 1, 10, 'database', 'system/database/index', '', 'SystemDatabase', 1, 0, 'C', '0', '0', 'system:database:list', 'table', 'admin', NOW(), '', NULL, '超级管理员只读数据库浏览器'),
  (3041, '数据库列表', 3040, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:database:list', '#', 'admin', NOW(), '', NULL, '查看数据库表结构与用户总览'),
  (3042, '数据库查询', 3040, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:database:query', '#', 'admin', NOW(), '', NULL, '查看数据表分页数据')
ON DUPLICATE KEY UPDATE
  menu_name = VALUES(menu_name),
  parent_id = VALUES(parent_id),
  order_num = VALUES(order_num),
  path = VALUES(path),
  component = VALUES(component),
  route_name = VALUES(route_name),
  perms = VALUES(perms),
  icon = VALUES(icon),
  update_by = 'admin',
  update_time = NOW(),
  remark = VALUES(remark);

INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, m.menu_id
FROM sys_role r
JOIN sys_menu m ON m.menu_id IN (3040, 3041, 3042)
WHERE r.role_key = 'admin';
