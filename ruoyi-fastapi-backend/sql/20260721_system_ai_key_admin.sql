-- 系统管理 / AIKey管理：仅供管理员维护项目AI图片识别共用的一个 API Key。
-- 密钥保存到既有 ai_models 表，后端以 Fernet 加密保存且接口不返回明文。

DELETE FROM sys_role_menu WHERE menu_id IN (3051, 3052, 3053, 3054);
DELETE FROM sys_menu WHERE menu_id IN (3051, 3052, 3053, 3054);

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3050, 'AIKey管理', 1, 11, 'aiKey', 'system/aiKey/index', '', 'SystemAiKey', 1, 0, 'C', '0', '0', 'system:aikey:edit', 'lock', 'admin', NOW(), '', NULL, '维护项目AI图片识别共用 API Key')
ON DUPLICATE KEY UPDATE
  menu_name = VALUES(menu_name), parent_id = VALUES(parent_id), order_num = VALUES(order_num),
  path = VALUES(path), component = VALUES(component), route_name = VALUES(route_name),
  is_frame = VALUES(is_frame), is_cache = VALUES(is_cache), menu_type = VALUES(menu_type),
  visible = VALUES(visible), status = VALUES(status), perms = VALUES(perms), icon = VALUES(icon),
  update_by = 'admin', update_time = NOW(), remark = VALUES(remark);

DELETE rm
FROM sys_role_menu rm
JOIN sys_role r ON r.role_id = rm.role_id
WHERE rm.menu_id = 3050 AND r.role_key <> 'admin';

INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, 3050
FROM sys_role r
WHERE r.role_key = 'admin';
