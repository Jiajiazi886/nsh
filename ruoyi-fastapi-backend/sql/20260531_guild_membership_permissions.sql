-- Menu, permission, and role bindings for guild membership review flow.
-- Safe to run more than once against the local MySQL development database.

SET @guild_root_menu_id := COALESCE(
  (SELECT parent_id FROM sys_menu WHERE menu_id = 2006 LIMIT 1),
  (SELECT parent_id FROM sys_menu WHERE component = 'guild/member/index' LIMIT 1),
  (SELECT menu_id FROM sys_menu WHERE path = 'guild' AND menu_type = 'M' LIMIT 1),
  2000
);
SET @guild_member_page_id := COALESCE(
  (SELECT menu_id FROM sys_menu WHERE component = 'guild/member/index' LIMIT 1),
  (SELECT menu_id FROM sys_menu WHERE menu_name = '成员管理' AND menu_type = 'C' LIMIT 1),
  2002
);
SET @guild_review_page_id := COALESCE(
  (SELECT menu_id FROM sys_menu WHERE component = 'guild/review/member' LIMIT 1),
  (SELECT menu_id FROM sys_menu WHERE menu_name = '成员报名审核' AND menu_type = 'C' LIMIT 1),
  3020
);

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3000, '个人管理', 0, 5, 'personal', 'Layout', '', '', 1, 0, 'M', '0', '0', '', 'user', 'admin', NOW(), '', NULL, '个人管理目录'),
  (3001, '加入帮会', 3000, 1, 'join', 'personal/coming-soon/index', '', 'PersonalJoinGuild', 1, 0, 'C', '0', '0', 'personal:join:list', 'people', 'admin', NOW(), '', NULL, '加入帮会菜单')
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

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3020, '成员报名审核', @guild_root_menu_id, 3, 'review/member', 'guild/review/member', '', 'GuildMemberReview', 1, 0, 'C', '0', '0', 'guild:review:member:list', 'finished', 'admin', NOW(), '', NULL, '成员报名审核菜单'),
  (3021, '主动退会', 3001, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'personal:join:quit', '#', 'admin', NOW(), '', NULL, '主动退会按钮'),
  (3022, '成员新增', @guild_member_page_id, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:member:add', '#', 'admin', NOW(), '', NULL, '成员新增按钮'),
  (3023, '成员编辑', @guild_member_page_id, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:member:edit', '#', 'admin', NOW(), '', NULL, '成员编辑按钮'),
  (3024, '成员删除', @guild_member_page_id, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:member:remove', '#', 'admin', NOW(), '', NULL, '成员删除按钮'),
  (3025, '成员导入', @guild_member_page_id, 5, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:member:import', '#', 'admin', NOW(), '', NULL, '成员导入按钮'),
  (3026, '审核通过', @guild_review_page_id, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:review:member:approve', '#', 'admin', NOW(), '', NULL, '审核通过按钮'),
  (3027, '审核拒绝', @guild_review_page_id, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:review:member:reject', '#', 'admin', NOW(), '', NULL, '审核拒绝按钮')
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
SELECT role_id, menu_id
FROM (
  SELECT r.role_id, m.menu_id
  FROM sys_role r
  JOIN sys_menu m ON m.menu_id IN (3000, 3001, 3021)
  WHERE r.role_key IN ('admin', 'user')

  UNION ALL

  SELECT r.role_id, mapped.menu_id
  FROM sys_role r
  JOIN (
    SELECT @guild_member_page_id AS menu_id
    UNION ALL SELECT @guild_review_page_id
    UNION ALL SELECT 3020
    UNION ALL SELECT 3022
    UNION ALL SELECT 3023
    UNION ALL SELECT 3024
    UNION ALL SELECT 3025
    UNION ALL SELECT 3026
    UNION ALL SELECT 3027
  ) mapped
  WHERE r.role_key IN ('admin', 'common')
) role_menu_pairs;
