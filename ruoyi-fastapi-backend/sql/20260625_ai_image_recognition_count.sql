-- AI识图次数：用户当前剩余可用次数。
ALTER TABLE sys_user
    ADD COLUMN IF NOT EXISTS ai_image_recognition_count int NOT NULL DEFAULT 0 COMMENT 'AI识图剩余次数' AFTER vip_expire_time;

UPDATE sys_user
SET ai_image_recognition_count = 0
WHERE ai_image_recognition_count IS NULL OR ai_image_recognition_count < 0;
