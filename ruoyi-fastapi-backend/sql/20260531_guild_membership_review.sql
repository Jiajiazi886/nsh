-- Guild membership review flow for join/apply/review/quit/member linkage.
-- Safe to run more than once against the local MySQL development database.

CREATE TABLE IF NOT EXISTS guild_join_application (
  application_id bigint NOT NULL AUTO_INCREMENT COMMENT '申请ID',
  applicant_user_id bigint NOT NULL DEFAULT 0 COMMENT '申请用户ID',
  guild_id bigint NOT NULL DEFAULT 0 COMMENT '目标帮会ID（最小实现：common 角色用户ID）',
  guild_name varchar(30) NOT NULL DEFAULT '' COMMENT '目标帮会名称快照（common 角色用户昵称）',
  player_name varchar(30) NOT NULL DEFAULT '' COMMENT '玩家角色名',
  player_class varchar(20) DEFAULT '' COMMENT '主职业',
  secondary_class varchar(20) DEFAULT '' COMMENT '副职',
  remark varchar(500) DEFAULT '' COMMENT '备注',
  review_status char(1) NOT NULL DEFAULT '0' COMMENT '审核状态（0待审核 1已通过 2已拒绝）',
  del_flag char(1) NOT NULL DEFAULT '0' COMMENT '删除标志（0有效 1归档）',
  apply_time datetime DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
  review_time datetime DEFAULT NULL COMMENT '审核时间',
  reviewer_user_id bigint DEFAULT NULL COMMENT '审核人用户ID',
  PRIMARY KEY (application_id),
  KEY idx_guild_join_application_applicant (applicant_user_id, del_flag, review_status),
  KEY idx_guild_join_application_guild (guild_id, del_flag, review_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帮会入会申请表';

CREATE TABLE IF NOT EXISTS guild_member (
  member_id bigint NOT NULL AUTO_INCREMENT COMMENT '成员ID',
  guild_id bigint NOT NULL DEFAULT 0 COMMENT '所属帮会ID',
  user_id bigint NOT NULL DEFAULT 0 COMMENT '所属用户ID',
  member_user_id bigint NOT NULL DEFAULT 0 COMMENT '成员账号用户ID',
  player_name varchar(30) NOT NULL DEFAULT '' COMMENT '玩家角色名',
  player_class varchar(20) DEFAULT '' COMMENT '职业',
  secondary_class varchar(20) DEFAULT '' COMMENT '副职',
  role_in_guild varchar(20) DEFAULT '成员' COMMENT '帮会身份',
  join_time datetime DEFAULT NULL COMMENT '加入时间',
  is_active char(1) DEFAULT '0' COMMENT '活跃状态',
  source_type varchar(20) DEFAULT 'manual' COMMENT '成员来源',
  remark varchar(500) DEFAULT '' COMMENT '备注',
  team_id bigint DEFAULT NULL COMMENT '团队ID',
  squad_number int DEFAULT NULL COMMENT '队编号',
  PRIMARY KEY (member_id),
  KEY idx_guild_member_user_active (user_id, is_active),
  KEY idx_guild_member_member_user (member_user_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帮会成员表';

SET @db_name := DATABASE();

SET @ddl := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = @db_name
        AND TABLE_NAME = 'guild_member'
        AND COLUMN_NAME = 'member_user_id'
    ),
    'SELECT 1',
    "ALTER TABLE guild_member ADD COLUMN member_user_id bigint NOT NULL DEFAULT 0 COMMENT '成员账号用户ID' AFTER user_id"
  )
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @ddl := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = @db_name
        AND TABLE_NAME = 'guild_member'
        AND COLUMN_NAME = 'source_type'
    ),
    'SELECT 1',
    "ALTER TABLE guild_member ADD COLUMN source_type varchar(20) DEFAULT 'manual' COMMENT '成员来源' AFTER is_active"
  )
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @ddl := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.STATISTICS
      WHERE TABLE_SCHEMA = @db_name
        AND TABLE_NAME = 'guild_member'
        AND INDEX_NAME = 'idx_guild_member_user_active'
    ),
    'SELECT 1',
    'CREATE INDEX idx_guild_member_user_active ON guild_member (user_id, is_active)'
  )
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @ddl := (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM information_schema.STATISTICS
      WHERE TABLE_SCHEMA = @db_name
        AND TABLE_NAME = 'guild_member'
        AND INDEX_NAME = 'idx_guild_member_member_user'
    ),
    'SELECT 1',
    'CREATE INDEX idx_guild_member_member_user ON guild_member (member_user_id, is_active)'
  )
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE guild_member
SET member_user_id = COALESCE(member_user_id, 0)
WHERE member_user_id IS NULL;

UPDATE guild_member
SET source_type = 'manual'
WHERE source_type IS NULL OR source_type = '';
