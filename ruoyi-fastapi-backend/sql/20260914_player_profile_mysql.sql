-- Apply only to nsh_activity_dev_20260914 using tools/migrate_player_profile_dev.py.
CREATE TABLE IF NOT EXISTS integration_account_player_profile (
 account_id BIGINT NOT NULL PRIMARY KEY,
 name VARCHAR(30) NOT NULL,
 player_uid VARCHAR(64) NOT NULL DEFAULT '',
 wechat_id VARCHAR(64) NOT NULL DEFAULT '',
 has_orange_weapon BOOLEAN NOT NULL DEFAULT FALSE,
 profession VARCHAR(20) NOT NULL DEFAULT '',
 secondary_profession VARCHAR(20) NOT NULL DEFAULT '',
 remark VARCHAR(500) NOT NULL DEFAULT '',
 updated_at DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
