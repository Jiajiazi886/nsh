-- REVIEW ONLY: apply manually to an independent TEST database first. No USE ruoyi statement.

CREATE TABLE integration_organization (
	org_id VARCHAR(64) NOT NULL, 
	org_type VARCHAR(10) NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	owner_user_id BIGINT NOT NULL, 
	source_owner_id BIGINT, 
	PRIMARY KEY (org_id), 
	UNIQUE (org_type, source_owner_id)
);

CREATE INDEX ix_integration_organization_owner_user_id ON integration_organization (owner_user_id);

CREATE TABLE integration_organization_member (
	org_id VARCHAR(64) NOT NULL, 
	account_id BIGINT NOT NULL, 
	role VARCHAR(12) NOT NULL, 
	PRIMARY KEY (org_id, account_id)
);

CREATE TABLE integration_activity (
	activity_id VARCHAR(64) NOT NULL, 
	org_id VARCHAR(64) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	starts_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	ends_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	remark VARCHAR(500) NOT NULL, 
	state VARCHAR(12) NOT NULL, 
	is_public INTEGER NOT NULL, 
	revision INTEGER NOT NULL, 
	latest_snapshot_id VARCHAR(64), 
	created_by BIGINT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (activity_id)
);

CREATE INDEX ix_integration_activity_org_id ON integration_activity (org_id);

CREATE INDEX ix_integration_activity_public_state ON integration_activity (is_public, state);

CREATE TABLE integration_activity_snapshot (
	snapshot_id VARCHAR(64) NOT NULL, 
	activity_id VARCHAR(64) NOT NULL, 
	version INTEGER NOT NULL, 
	teams JSON NOT NULL, 
	created_by BIGINT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (snapshot_id), 
	UNIQUE (activity_id, version)
);

CREATE INDEX ix_integration_activity_snapshot_activity_id ON integration_activity_snapshot (activity_id);

CREATE TABLE integration_activity_participation (
	participation_id VARCHAR(64) NOT NULL, 
	activity_id VARCHAR(64) NOT NULL, 
	account_id BIGINT NOT NULL, 
	member_id BIGINT NOT NULL, 
	squad_id VARCHAR(100), 
	position INTEGER, 
	state VARCHAR(10) NOT NULL, 
	player JSON NOT NULL, 
	PRIMARY KEY (participation_id), 
	UNIQUE (activity_id, member_id), 
	UNIQUE (activity_id, squad_id, position)
);

CREATE INDEX ix_integration_activity_participation_account_id ON integration_activity_participation (account_id);

CREATE INDEX ix_integration_activity_participation_activity_id ON integration_activity_participation (activity_id);

CREATE TABLE integration_activity_receipt (
	receipt_id VARCHAR(64) NOT NULL, 
	activity_id VARCHAR(64) NOT NULL, 
	actor_id BIGINT NOT NULL, 
	operation_key VARCHAR(100) NOT NULL, 
	action VARCHAR(20) NOT NULL, 
	digest VARCHAR(64) NOT NULL, 
	result JSON NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (receipt_id), 
	UNIQUE (activity_id, actor_id, operation_key)
);

CREATE TABLE integration_activity_report (
	battle_id BIGSERIAL NOT NULL, 
	activity_id VARCHAR(64) NOT NULL, 
	linked_by BIGINT NOT NULL, 
	linked_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (battle_id)
);

CREATE INDEX ix_integration_activity_report_activity_id ON integration_activity_report (activity_id);

CREATE TABLE integration_activity_leave_link (
	activity_id VARCHAR(64) NOT NULL,
	org_id VARCHAR(64) NOT NULL,
	code VARCHAR(64) NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (activity_id)
);

CREATE UNIQUE INDEX ix_integration_activity_leave_link_code ON integration_activity_leave_link (code);

CREATE INDEX ix_integration_activity_leave_link_org_id ON integration_activity_leave_link (org_id);

CREATE TABLE integration_activity_leave_record (
	record_id VARCHAR(64) NOT NULL,
	activity_id VARCHAR(64) NOT NULL,
	member_id BIGINT NOT NULL,
	account_id BIGINT,
	player JSON NOT NULL,
	remark VARCHAR(500) NOT NULL,
	left_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (record_id),
	UNIQUE (activity_id, member_id)
);

CREATE INDEX ix_integration_activity_leave_record_activity_id ON integration_activity_leave_record (activity_id);
