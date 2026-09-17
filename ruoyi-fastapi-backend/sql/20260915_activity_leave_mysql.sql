-- Apply only to the independent development database nsh_activity_dev_20260914.
-- Existing activity, lineup and report rows are not modified.

CREATE TABLE integration_activity_leave_link (
  activity_id VARCHAR(64) NOT NULL,
  org_id VARCHAR(64) NOT NULL,
  code VARCHAR(64) NOT NULL,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (activity_id),
  UNIQUE KEY ix_integration_activity_leave_link_code (code),
  KEY ix_integration_activity_leave_link_org_id (org_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE integration_activity_leave_record (
  record_id VARCHAR(64) NOT NULL,
  activity_id VARCHAR(64) NOT NULL,
  member_id BIGINT NOT NULL,
  account_id BIGINT NULL,
  player JSON NOT NULL,
  remark VARCHAR(500) NOT NULL,
  left_at DATETIME NOT NULL,
  PRIMARY KEY (record_id),
  UNIQUE KEY uq_integration_activity_leave_member (activity_id, member_id),
  KEY ix_integration_activity_leave_record_activity_id (activity_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
