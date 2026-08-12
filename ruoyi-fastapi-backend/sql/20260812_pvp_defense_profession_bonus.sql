-- 防守计算器职业默认加成及管理员菜单。

CREATE TABLE IF NOT EXISTS system_pvp_defense_profession_bonus (
  profession_id BIGINT NOT NULL COMMENT '职业ID',
  defense_bonus_pct DOUBLE NOT NULL DEFAULT 0 COMMENT '内功防御增量加成百分比',
  hp_bonus_pct DOUBLE NOT NULL DEFAULT 0 COMMENT '内功气血增量加成百分比',
  update_by VARCHAR(64) DEFAULT '' COMMENT '更新者',
  update_time DATETIME NULL COMMENT '更新时间',
  PRIMARY KEY (profession_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='PVP防守职业默认加成表';

INSERT INTO system_pvp_defense_profession_bonus (profession_id, defense_bonus_pct, hp_bonus_pct, update_by, update_time)
SELECT profession_id, 20, 40, 'system', NOW()
FROM guild_profession
WHERE profession_name = '铁衣'
ON DUPLICATE KEY UPDATE profession_id = VALUES(profession_id);

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3165, '职业加成设置', 1, 15, 'pvpDefenseProfessionBonus', 'system/pvpDefenseProfessionBonus/index', '', 'SystemPvpDefenseProfessionBonus', 1, 0, 'C', '0', '0', 'system:pvp-defense-profession-bonus:list', 'setting', 'admin', NOW(), '', NULL, '管理员维护防守计算器职业默认加成'),
  (3166, '职业加成修改', 3165, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:pvp-defense-profession-bonus:edit', '#', 'admin', NOW(), '', NULL, '')
ON DUPLICATE KEY UPDATE
  menu_name = VALUES(menu_name), parent_id = VALUES(parent_id), order_num = VALUES(order_num),
  path = VALUES(path), component = VALUES(component), route_name = VALUES(route_name),
  menu_type = VALUES(menu_type), visible = VALUES(visible), status = VALUES(status), perms = VALUES(perms),
  icon = VALUES(icon), update_by = 'admin', update_time = NOW(), remark = VALUES(remark);

DELETE rm
FROM sys_role_menu rm
JOIN sys_role r ON r.role_id = rm.role_id
WHERE rm.menu_id IN (3165, 3166) AND r.role_key <> 'admin';

INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, m.menu_id
FROM sys_role r
JOIN sys_menu m ON m.menu_id IN (3165, 3166)
WHERE r.role_key = 'admin';
