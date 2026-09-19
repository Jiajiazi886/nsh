CREATE TABLE IF NOT EXISTS system_account_license (
  license_id varchar(64) PRIMARY KEY,
  user_id bigint NOT NULL UNIQUE REFERENCES sys_user(user_id),
  plan_type varchar(16) NOT NULL,
  status varchar(16) NOT NULL DEFAULT 'active',
  valid_from timestamp NOT NULL,
  expires_at timestamp NULL,
  remark varchar(500) NOT NULL DEFAULT '',
  version integer NOT NULL DEFAULT 1,
  create_by varchar(64) NOT NULL DEFAULT 'system',
  create_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_by varchar(64) NOT NULL DEFAULT 'system',
  update_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_system_account_license_user ON system_account_license(user_id);

CREATE TABLE IF NOT EXISTS system_account_license_audit (
  audit_id varchar(64) PRIMARY KEY,
  batch_id varchar(64) NOT NULL,
  request_id varchar(64) NOT NULL,
  user_id bigint NOT NULL REFERENCES sys_user(user_id),
  operator_user_id bigint NOT NULL REFERENCES sys_user(user_id),
  action varchar(32) NOT NULL,
  previous_state jsonb NULL,
  new_state jsonb NULL,
  remark varchar(500) NOT NULL DEFAULT '',
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(request_id, user_id)
);
CREATE INDEX IF NOT EXISTS ix_system_account_license_audit_batch ON system_account_license_audit(batch_id);
CREATE INDEX IF NOT EXISTS ix_system_account_license_audit_user ON system_account_license_audit(user_id);

CREATE TABLE IF NOT EXISTS system_auth_refresh_token (
  token_id varchar(64) PRIMARY KEY,
  token_hash varchar(64) NOT NULL UNIQUE,
  user_id bigint NOT NULL REFERENCES sys_user(user_id),
  client_type varchar(40) NOT NULL DEFAULT '',
  token_family_id varchar(64) NOT NULL,
  device_id varchar(128) NULL,
  issued_at timestamp NOT NULL,
  expires_at timestamp NOT NULL,
  last_used_at timestamp NULL,
  revoked_at timestamp NULL,
  replaced_by_token_id varchar(64) NULL
);
CREATE INDEX IF NOT EXISTS ix_system_auth_refresh_token_user ON system_auth_refresh_token(user_id);
CREATE INDEX IF NOT EXISTS ix_system_auth_refresh_token_family ON system_auth_refresh_token(token_family_id);
CREATE INDEX IF NOT EXISTS ix_system_auth_refresh_token_device ON system_auth_refresh_token(device_id);
