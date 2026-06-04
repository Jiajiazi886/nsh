-- 个人信息编辑菜单改为真实页面，并确保普通 user 角色拥有该菜单权限。

UPDATE sys_menu
SET component = 'personal/profileEdit/index',
    perms = 'personal:profile:edit',
    status = '0',
    visible = '0'
WHERE path = 'profile-edit'
  AND menu_name = '个人信息编辑';

INSERT INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, m.menu_id
FROM sys_role r
JOIN sys_menu m ON m.path = 'profile-edit' AND m.menu_name = '个人信息编辑'
WHERE r.role_key = 'user'
  AND NOT EXISTS (
    SELECT 1
    FROM sys_role_menu rm
    WHERE rm.role_id = r.role_id
      AND rm.menu_id = m.menu_id
  );
