-- Apply only to an independent development database.
-- Existing activity, lineup and report rows are not modified.

CREATE TABLE integration_activity_leave_link (
  activity_id VARCHAR(64) PRIMARY KEY,
  org_id VARCHAR(64) NOT NULL,
  code VARCHAR(64) NOT NULL UNIQUE,
  created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);
CREATE INDEX ix_integration_activity_leave_link_org_id ON integration_activity_leave_link (org_id);

CREATE TABLE integration_activity_leave_record (
  record_id VARCHAR(64) PRIMARY KEY,
  activity_id VARCHAR(64) NOT NULL,
  member_id BIGINT NOT NULL,
  account_id BIGINT,
  player JSON NOT NULL,
  remark VARCHAR(500) NOT NULL,
  left_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  CONSTRAINT uq_integration_activity_leave_member UNIQUE (activity_id, member_id)
);
CREATE INDEX ix_integration_activity_leave_record_activity_id ON integration_activity_leave_record (activity_id);
