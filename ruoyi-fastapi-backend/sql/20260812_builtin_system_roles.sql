-- 项目内置系统角色。可重复执行，不修改既有菜单权限。
INSERT INTO sys_role (
  role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly,
  status, del_flag, create_by, create_time, update_by, update_time, remark
) VALUES
  (1, '超级管理员', 'admin', 1, '1', 1, 1, '0', '0', 'system', NOW(), 'system', NOW(), '系统内置超级管理员角色'),
  (2, '帮会管理', 'common', 2, '2', 1, 1, '0', '0', 'system', NOW(), 'system', NOW(), '系统内置帮会管理角色'),
  (100, '帮会成员', 'user', 0, '2', 1, 1, '0', '0', 'system', NOW(), 'system', NOW(), '系统内置帮会成员角色')
ON DUPLICATE KEY UPDATE
  role_name = VALUES(role_name), role_key = VALUES(role_key), role_sort = VALUES(role_sort),
  status = '0', del_flag = '0', update_by = 'system', update_time = NOW(), remark = VALUES(remark);
