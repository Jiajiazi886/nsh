-- Ensure common guild owners can manage members in their own guild.
-- Safe to run repeatedly against the local MySQL development database.

SET @guild_member_page_id := COALESCE(
  (SELECT menu_id FROM sys_menu WHERE component = 'guild/member/index' LIMIT 1),
  (SELECT menu_id FROM sys_menu WHERE menu_name = '成员管理' AND menu_type = 'C' LIMIT 1),
  1067
);

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3050, '成员新增', @guild_member_page_id, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:member:add', '#', 'admin', NOW(), '', NULL, '成员新增按钮'),
  (3051, '成员编辑', @guild_member_page_id, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:member:edit', '#', 'admin', NOW(), '', NULL, '成员编辑按钮'),
  (3052, '成员删除', @guild_member_page_id, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:member:remove', '#', 'admin', NOW(), '', NULL, '成员删除按钮'),
  (3053, '成员导入', @guild_member_page_id, 5, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:member:import', '#', 'admin', NOW(), '', NULL, '成员导入按钮')
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
  remark = VALUES(remark),
  update_by = 'admin',
  update_time = NOW();

INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, m.menu_id
FROM sys_role r
JOIN sys_menu m ON m.perms IN (
  'guild:member:list',
  'guild:member:add',
  'guild:member:edit',
  'guild:member:remove',
  'guild:member:import'
)
WHERE r.role_key IN ('admin', 'common');
