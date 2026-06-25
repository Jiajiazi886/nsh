-- 个人内功后端化、VIP到期和内功容量控制
-- 可重复执行：MySQL 8+ / MariaDB 10.3+ 支持 ADD COLUMN IF NOT EXISTS。

ALTER TABLE sys_user
    ADD COLUMN IF NOT EXISTS vip_expire_time datetime NULL COMMENT 'VIP到期时间' AFTER is_vip;

ALTER TABLE sys_user
    ADD COLUMN IF NOT EXISTS max_internal_power_count int NOT NULL DEFAULT 20 COMMENT '最大内功数' AFTER vip_expire_time;

UPDATE sys_user
SET max_internal_power_count = 20
WHERE max_internal_power_count IS NULL OR max_internal_power_count < 20;

-- 兼容旧版VIP开关：已开通但没有期限的账号默认给远期授权，避免升级后瞬间失效。
UPDATE sys_user
SET vip_expire_time = '2099-12-31 23:59:59'
WHERE is_vip = '1' AND vip_expire_time IS NULL;

CREATE TABLE IF NOT EXISTS personal_internal_power (
    power_id bigint NOT NULL AUTO_INCREMENT COMMENT '内功ID',
    user_id bigint NOT NULL COMMENT '用户ID',
    name varchar(64) NOT NULL COMMENT '内功名称',
    category varchar(64) DEFAULT '' COMMENT '内功种类',
    category_trait varchar(128) DEFAULT '' COMMENT '种类特性',
    bonus_percent double NOT NULL DEFAULT 0 COMMENT '基础百分比加成',
    entries_json longtext NULL COMMENT '词条JSON',
    elements_json longtext NULL COMMENT '五行JSON',
    remark varchar(500) DEFAULT '' COMMENT '备注',
    create_time datetime DEFAULT NULL COMMENT '创建时间',
    update_time datetime DEFAULT NULL COMMENT '更新时间',
    PRIMARY KEY (power_id),
    KEY idx_personal_internal_power_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='个人内功表';

INSERT INTO sys_job (
    job_name,
    job_group,
    job_executor,
    invoke_target,
    cron_expression,
    misfire_policy,
    concurrent,
    status,
    create_by,
    create_time,
    update_by,
    update_time,
    remark
)
SELECT
    'VIP到期自动清理',
    'default',
    'default',
    'module_task.user_vip.expire_user_vip',
    '0 0 * * * ?',
    '3',
    '1',
    '0',
    'system',
    NOW(),
    'system',
    NOW(),
    '每小时清理已过期VIP授权'
WHERE NOT EXISTS (
    SELECT 1 FROM sys_job WHERE invoke_target = 'module_task.user_vip.expire_user_vip'
);
