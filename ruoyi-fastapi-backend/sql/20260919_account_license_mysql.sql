-- Account entitlements replace user-entered card strings and machine binding.
CREATE TABLE IF NOT EXISTS system_account_license (
  license_id varchar(64) NOT NULL,
  user_id bigint NOT NULL,
  plan_type varchar(16) NOT NULL,
  status varchar(16) NOT NULL DEFAULT 'active',
  valid_from datetime NOT NULL,
  expires_at datetime NULL,
  remark varchar(500) NOT NULL DEFAULT '',
  version int NOT NULL DEFAULT 1,
  create_by varchar(64) NOT NULL DEFAULT 'system',
  create_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_by varchar(64) NOT NULL DEFAULT 'system',
  update_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (license_id),
  UNIQUE KEY uk_system_account_license_user (user_id),
  KEY ix_system_account_license_user (user_id),
  CONSTRAINT fk_system_account_license_user FOREIGN KEY (user_id) REFERENCES sys_user(user_id)
) ENGINE=InnoDB COMMENT='账号授权';

CREATE TABLE IF NOT EXISTS system_account_license_audit (
  audit_id varchar(64) NOT NULL,
  batch_id varchar(64) NOT NULL,
  request_id varchar(64) NOT NULL,
  user_id bigint NOT NULL,
  operator_user_id bigint NOT NULL,
  action varchar(32) NOT NULL,
  previous_state json NULL,
  new_state json NULL,
  remark varchar(500) NOT NULL DEFAULT '',
  created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (audit_id),
  UNIQUE KEY uk_system_account_license_audit_request_user (request_id, user_id),
  KEY ix_system_account_license_audit_batch (batch_id),
  KEY ix_system_account_license_audit_user (user_id),
  CONSTRAINT fk_system_account_license_audit_user FOREIGN KEY (user_id) REFERENCES sys_user(user_id),
  CONSTRAINT fk_system_account_license_audit_operator FOREIGN KEY (operator_user_id) REFERENCES sys_user(user_id)
) ENGINE=InnoDB COMMENT='账号授权审计';

CREATE TABLE IF NOT EXISTS system_auth_refresh_token (
  token_id varchar(64) NOT NULL,
  token_hash varchar(64) NOT NULL,
  user_id bigint NOT NULL,
  client_type varchar(40) NOT NULL DEFAULT '',
  token_family_id varchar(64) NOT NULL,
  device_id varchar(128) NULL,
  issued_at datetime NOT NULL,
  expires_at datetime NOT NULL,
  last_used_at datetime NULL,
  revoked_at datetime NULL,
  replaced_by_token_id varchar(64) NULL,
  PRIMARY KEY (token_id),
  UNIQUE KEY uk_system_auth_refresh_token_hash (token_hash),
  KEY ix_system_auth_refresh_token_user (user_id),
  KEY ix_system_auth_refresh_token_family (token_family_id),
  KEY ix_system_auth_refresh_token_device (device_id),
  CONSTRAINT fk_system_auth_refresh_token_user FOREIGN KEY (user_id) REFERENCES sys_user(user_id)
) ENGINE=InnoDB COMMENT='持久化刷新令牌';
