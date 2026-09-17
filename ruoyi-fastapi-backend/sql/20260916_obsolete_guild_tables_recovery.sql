-- Recovery DDL for the two empty tables removed only from nsh_activity_dev_20260914.
-- Review before running. No rows existed at cleanup time.

CREATE TABLE IF NOT EXISTS guild_info (
  guild_id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  guild_name VARCHAR(50) DEFAULT NULL,
  member_count INT DEFAULT 0,
  status CHAR(1) DEFAULT '0',
  del_flag CHAR(1) DEFAULT '0',
  update_time DATETIME DEFAULT NULL,
  remark VARCHAR(500) DEFAULT NULL,
  PRIMARY KEY (guild_id),
  UNIQUE KEY uk_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帮会信息表';

CREATE TABLE IF NOT EXISTS guild_review (
  review_id BIGINT NOT NULL AUTO_INCREMENT,
  review_type VARCHAR(30) NOT NULL,
  target_id BIGINT NOT NULL,
  guild_id BIGINT NOT NULL,
  applicant_id BIGINT NOT NULL,
  reviewer_id BIGINT DEFAULT NULL,
  review_status CHAR(1) DEFAULT '0',
  review_comment VARCHAR(500) DEFAULT NULL,
  apply_time DATETIME DEFAULT NULL,
  review_time DATETIME DEFAULT NULL,
  PRIMARY KEY (review_id),
  KEY idx_review_type (review_type),
  KEY idx_target_id (target_id),
  KEY idx_guild_id (guild_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审核记录表';

DELETE FROM app_schema_migration
WHERE version='20260916_remove_obsolete_guild_tables';
