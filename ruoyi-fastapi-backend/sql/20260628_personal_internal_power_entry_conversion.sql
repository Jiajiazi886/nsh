-- 个人内功词条换算管理。
-- 可重复执行：MySQL 8+ / MariaDB 10.3+。

CREATE TABLE IF NOT EXISTS personal_internal_power_entry_setting (
    user_id bigint NOT NULL COMMENT '用户ID',
    base_attack_power double NOT NULL DEFAULT 0 COMMENT '基准进攻能力',
    base_percent double NOT NULL DEFAULT 0 COMMENT '基准百分比',
    unit_percent double NOT NULL DEFAULT 0 COMMENT '1点进攻能力对应百分比',
    create_time datetime DEFAULT NULL COMMENT '创建时间',
    update_time datetime DEFAULT NULL COMMENT '更新时间',
    PRIMARY KEY (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='个人内功词条换算基准表';

CREATE TABLE IF NOT EXISTS personal_internal_power_entry_value (
    value_id bigint NOT NULL AUTO_INCREMENT COMMENT '数值ID',
    user_id bigint NOT NULL COMMENT '用户ID',
    entry_name varchar(64) NOT NULL COMMENT '词条名称',
    entry_value double NOT NULL DEFAULT 0 COMMENT '用户内功数值',
    attack_power double NOT NULL DEFAULT 0 COMMENT '进攻能力',
    create_time datetime DEFAULT NULL COMMENT '创建时间',
    update_time datetime DEFAULT NULL COMMENT '更新时间',
    PRIMARY KEY (value_id),
    UNIQUE KEY uk_personal_internal_power_entry_user_name (user_id, entry_name),
    KEY idx_personal_internal_power_entry_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='个人内功词条数值表';

UPDATE sys_menu
SET visible = '1',
    status = '1',
    update_by = 'admin',
    update_time = NOW(),
    remark = '已迁移到个人管理，保留旧接口避免兼容问题'
WHERE menu_id IN (3110, 3111, 3112, 3113, 3114)
   OR perms LIKE 'system:internal-power-entry:%';

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3115, '内功词条管理', 3000, 7, 'internal-power-entry', 'personal/internalPowerEntry/index', '', 'PersonalInternalPowerEntry', 1, 0, 'C', '0', '0', 'personal:internal-power-entry:list', 'list', 'admin', NOW(), '', NULL, '个人内功词条换算管理菜单'),
  (3116, '内功词条保存', 3115, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'personal:internal-power-entry:edit', '#', 'admin', NOW(), '', NULL, '')
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
  (1, 3115), (1, 3116),
  (2, 3115), (2, 3116);
