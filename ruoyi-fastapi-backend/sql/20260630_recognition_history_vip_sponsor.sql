-- 持久识别记录、VIP识图次数与帮会赞助字段。

ALTER TABLE sys_user
    ADD COLUMN IF NOT EXISTS vip_ai_image_recognition_count int NOT NULL DEFAULT 0 COMMENT 'VIP AI识图剩余次数' AFTER ai_image_recognition_count,
    ADD COLUMN IF NOT EXISTS sponsor_enabled char(1) NOT NULL DEFAULT '0' COMMENT '赞助开关（0关闭 1开启）' AFTER vip_ai_image_recognition_count,
    ADD COLUMN IF NOT EXISTS sponsored_vip char(1) NOT NULL DEFAULT '0' COMMENT '赞助VIP标识（0非VIP 1VIP）' AFTER sponsor_enabled,
    ADD COLUMN IF NOT EXISTS sponsored_by_user_id bigint NULL COMMENT '赞助来源帮会管理用户ID' AFTER sponsored_vip;

CREATE TABLE IF NOT EXISTS personal_internal_power_recognition_history (
  record_id bigint NOT NULL AUTO_INCREMENT COMMENT '识别记录ID',
  user_id bigint NOT NULL COMMENT '用户ID',
  file_name varchar(255) NOT NULL DEFAULT '' COMMENT '文件名',
  image_base64 longtext NULL COMMENT '图片Base64',
  mime_type varchar(64) NOT NULL DEFAULT 'image/png' COMMENT '图片MIME类型',
  status varchar(20) NOT NULL DEFAULT 'recognizing' COMMENT '状态',
  parsed_json longtext NULL COMMENT '解析JSON',
  raw_text longtext NULL COMMENT '模型原始返回',
  error longtext NULL COMMENT '完整错误',
  preset_candidates_json longtext NULL COMMENT '候选预设JSON',
  saved_power_id bigint NULL COMMENT '已保存内功ID',
  create_time datetime NULL COMMENT '创建时间',
  update_time datetime NULL COMMENT '更新时间',
  PRIMARY KEY (record_id),
  KEY idx_personal_internal_power_recognition_history_user (user_id, create_time, record_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='个人内功图片识别历史表';

SET @user_menu_id := (SELECT menu_id FROM sys_menu WHERE perms = 'system:user:list' LIMIT 1);

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache,
  menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark
)
SELECT 3130, 'VIP授权修改', @user_menu_id, 8, '#', '', '', '', 1, 0, 'F', '0', '0',
       'system:user:vip:edit', '#', 'admin', NOW(), '', NULL, ''
WHERE @user_menu_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'system:user:vip:edit');

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache,
  menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark
)
SELECT 3131, '赞助状态修改', @user_menu_id, 9, '#', '', '', '', 1, 0, 'F', '0', '0',
       'system:user:sponsor:edit', '#', 'admin', NOW(), '', NULL, ''
WHERE @user_menu_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'system:user:sponsor:edit');

INSERT INTO sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache,
  menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark
)
SELECT 3132, 'AI识图次数修改', @user_menu_id, 10, '#', '', '', '', 1, 0, 'F', '0', '0',
       'system:user:ai:edit', '#', 'admin', NOW(), '', NULL, ''
WHERE @user_menu_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'system:user:ai:edit');

INSERT INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, m.menu_id
FROM sys_role r
JOIN sys_menu m ON m.perms IN ('system:user:vip:edit', 'system:user:sponsor:edit', 'system:user:ai:edit')
WHERE r.role_key = 'admin'
  AND NOT EXISTS (
    SELECT 1 FROM sys_role_menu rm WHERE rm.role_id = r.role_id AND rm.menu_id = m.menu_id
  );
