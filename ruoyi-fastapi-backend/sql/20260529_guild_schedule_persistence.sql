-- Persistent schedule board structure and RuoYi permissions.
-- Safe to run more than once against the local MySQL development database.

CREATE TABLE IF NOT EXISTS guild_schedule (
  schedule_id bigint NOT NULL AUTO_INCREMENT COMMENT '排表ID',
  schedule_name varchar(100) NOT NULL DEFAULT '' COMMENT '排表名称',
  user_id bigint NOT NULL DEFAULT 0 COMMENT '所属用户ID',
  is_active char(1) NOT NULL DEFAULT '0' COMMENT '是否当前排表(0否 1是)',
  source_schedule_id bigint DEFAULT NULL COMMENT '来源排表ID',
  create_time datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  del_flag char(1) NOT NULL DEFAULT '0' COMMENT '删除标志(0正常 1删除)',
  PRIMARY KEY (schedule_id),
  KEY idx_guild_schedule_user_active (user_id, is_active, del_flag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='约战排表主表';

CREATE TABLE IF NOT EXISTS guild_schedule_team (
  team_id bigint NOT NULL AUTO_INCREMENT COMMENT '排表团队ID',
  schedule_id bigint NOT NULL DEFAULT 0 COMMENT '排表ID',
  team_name varchar(50) NOT NULL DEFAULT '' COMMENT '团队名称',
  order_num int NOT NULL DEFAULT 0 COMMENT '显示顺序',
  create_time datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (team_id),
  KEY idx_guild_schedule_team_schedule (schedule_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='约战排表团队表';

CREATE TABLE IF NOT EXISTS guild_schedule_squad (
  squad_id bigint NOT NULL AUTO_INCREMENT COMMENT '排表小队ID',
  team_id bigint NOT NULL DEFAULT 0 COMMENT '排表团队ID',
  squad_name varchar(50) NOT NULL DEFAULT '' COMMENT '小队名称',
  max_members int NOT NULL DEFAULT 6 COMMENT '小队人数上限',
  order_num int NOT NULL DEFAULT 0 COMMENT '显示顺序',
  create_time datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (squad_id),
  KEY idx_guild_schedule_squad_team (team_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='约战排表小队表';

CREATE TABLE IF NOT EXISTS guild_schedule_assignment (
  assignment_id bigint NOT NULL AUTO_INCREMENT COMMENT '分配ID',
  schedule_id bigint NOT NULL DEFAULT 0 COMMENT '排表ID',
  team_id bigint NOT NULL DEFAULT 0 COMMENT '排表团队ID',
  squad_id bigint NOT NULL DEFAULT 0 COMMENT '排表小队ID',
  member_id bigint NOT NULL DEFAULT 0 COMMENT '成员ID',
  player_name varchar(30) NOT NULL DEFAULT '' COMMENT '玩家角色名快照',
  player_class varchar(20) DEFAULT '' COMMENT '主职业快照',
  secondary_class varchar(20) DEFAULT '' COMMENT '副职快照',
  order_num int NOT NULL DEFAULT 0 COMMENT '显示顺序',
  create_time datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (assignment_id),
  UNIQUE KEY uk_guild_schedule_assignment_member (schedule_id, member_id),
  KEY idx_guild_schedule_assignment_squad (squad_id),
  KEY idx_guild_schedule_assignment_team (team_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='约战排表成员分配表';

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) VALUES
  (3010, '排表详情查询', 2006, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:query', '#', 'admin', NOW(), '', NULL, ''),
  (3011, '创建排表团队', 2006, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:team:add', '#', 'admin', NOW(), '', NULL, ''),
  (3012, '删除排表团队', 2006, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:team:remove', '#', 'admin', NOW(), '', NULL, ''),
  (3013, '创建排表小队', 2006, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:squad:add', '#', 'admin', NOW(), '', NULL, ''),
  (3014, '删除排表小队', 2006, 5, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:squad:remove', '#', 'admin', NOW(), '', NULL, ''),
  (3015, '保存排表成员', 2006, 6, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:edit', '#', 'admin', NOW(), '', NULL, ''),
  (3016, '排表历史查询', 2006, 7, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:history', '#', 'admin', NOW(), '', NULL, ''),
  (3017, '保存排表历史', 2006, 8, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:snapshot', '#', 'admin', NOW(), '', NULL, '')
ON DUPLICATE KEY UPDATE
  menu_name = VALUES(menu_name),
  parent_id = VALUES(parent_id),
  order_num = VALUES(order_num),
  perms = VALUES(perms),
  update_by = 'admin',
  update_time = NOW();

INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
  (1, 3010), (1, 3011), (1, 3012), (1, 3013), (1, 3014), (1, 3015), (1, 3016), (1, 3017),
  (2, 3010), (2, 3011), (2, 3012), (2, 3013), (2, 3014), (2, 3015), (2, 3016), (2, 3017);
