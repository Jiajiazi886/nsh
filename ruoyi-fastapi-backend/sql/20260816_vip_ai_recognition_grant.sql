-- VIP开通时自动赠送AI识图次数。次数为余额，VIP取消或到期后不清零。
INSERT INTO sys_config (
  config_name, config_key, config_value, config_type,
  create_by, create_time, update_by, update_time, remark
)
SELECT '用户管理-VIP开通赠送识图次数', 'sys.user.vipAiImageRecognitionGrantCount', '0', 'Y',
       'system', NOW(), 'system', NOW(), '用户从非VIP变为有效VIP时一次性追加的VIP AI识图次数'
FROM DUAL
WHERE NOT EXISTS (
  SELECT 1 FROM sys_config WHERE config_key = 'sys.user.vipAiImageRecognitionGrantCount'
);
