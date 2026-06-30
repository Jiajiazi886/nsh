-- 内功图片显示全局开关与系统管理菜单。
-- 可重复执行：MySQL 8+ / MariaDB 10.3+。

INSERT INTO sys_config (
  config_name, config_key, config_value, config_type,
  create_by, create_time, update_by, update_time, remark
)
SELECT
  '内功图片显示开关',
  'sys.internalPower.imageDisplayEnabled',
  'true',
  'Y',
  'admin',
  NOW(),
  '',
  NULL,
  '全局控制网页是否显示内功图片，关闭后所有用户页面不渲染内功图片'
WHERE NOT EXISTS (
  SELECT 1 FROM sys_config WHERE config_key = 'sys.internalPower.imageDisplayEnabled'
);

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3120, '图片显示管理', 1, 12, 'imageDisplay', 'system/imageDisplay/index', '', 'SystemImageDisplay', 1, 0, 'C', '0', '0', 'system:internal-power-image-display:list', 'eye-open', 'admin', NOW(), '', NULL, '内功图片显示全局开关菜单'),
  (3121, '图片显示查询', 3120, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-image-display:query', '#', 'admin', NOW(), '', NULL, ''),
  (3122, '图片显示修改', 3120, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-image-display:edit', '#', 'admin', NOW(), '', NULL, '')
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
  (1, 3120), (1, 3121), (1, 3122);
