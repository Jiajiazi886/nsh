-- PostgreSQL version of the single internal-power API Key menu migration.

DELETE FROM sys_role_menu WHERE menu_id IN (3051, 3052, 3053, 3054);
DELETE FROM sys_menu WHERE menu_id IN (3051, 3052, 3053, 3054);

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3050, 'AIKey管理', 1, 11, 'aiKey', 'system/aiKey/index', '', 'SystemAiKey', 1, 0, 'C', '0', '0', 'system:aikey:edit', 'lock', 'admin', CURRENT_TIMESTAMP, '', NULL, '维护内功图片识别 API Key')
ON CONFLICT (menu_id) DO UPDATE SET
  menu_name = EXCLUDED.menu_name, parent_id = EXCLUDED.parent_id, order_num = EXCLUDED.order_num,
  path = EXCLUDED.path, component = EXCLUDED.component, route_name = EXCLUDED.route_name,
  is_frame = EXCLUDED.is_frame, is_cache = EXCLUDED.is_cache, menu_type = EXCLUDED.menu_type,
  visible = EXCLUDED.visible, status = EXCLUDED.status, perms = EXCLUDED.perms, icon = EXCLUDED.icon,
  update_by = 'admin', update_time = CURRENT_TIMESTAMP, remark = EXCLUDED.remark;

DELETE FROM sys_role_menu rm
USING sys_role r
WHERE rm.role_id = r.role_id AND rm.menu_id = 3050 AND r.role_key <> 'admin';

INSERT INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, 3050
FROM sys_role r
WHERE r.role_key = 'admin'
ON CONFLICT DO NOTHING;
