-- 内功灵韵勾选与灵韵百分比提升。
-- 可重复执行：MySQL 8+ / MariaDB 10.3+ 支持 ADD COLUMN IF NOT EXISTS。

ALTER TABLE system_internal_power_preset
    ADD COLUMN IF NOT EXISTS lingyun_bonus_percent double NOT NULL DEFAULT 0 COMMENT '灵韵百分比提升' AFTER bonus_percent;

ALTER TABLE personal_internal_power
    ADD COLUMN IF NOT EXISTS lingyun_enabled char(1) NOT NULL DEFAULT '0' COMMENT '是否启用灵韵（0否 1是）' AFTER bonus_percent;

ALTER TABLE personal_internal_power
    ADD COLUMN IF NOT EXISTS lingyun_bonus_percent double NOT NULL DEFAULT 0 COMMENT '灵韵百分比提升' AFTER lingyun_enabled;
