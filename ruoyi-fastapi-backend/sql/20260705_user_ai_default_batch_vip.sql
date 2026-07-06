-- 用户管理：新用户默认普通AI识图次数配置与批量VIP设置支持。

INSERT INTO sys_config (
  config_name, config_key, config_value, config_type,
  create_by, create_time, update_by, update_time, remark
)
SELECT '用户管理-新用户默认普通AI识图次数', 'sys.user.defaultAiImageRecognitionCount', '0', 'Y',
       'system', NOW(), 'system', NOW(), '后台新增、注册和导入新增用户时默认发放的普通AI识图次数'
WHERE NOT EXISTS (
  SELECT 1 FROM sys_config WHERE config_key = 'sys.user.defaultAiImageRecognitionCount'
);
