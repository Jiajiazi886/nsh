-- Self registration and inactive registered user cleanup rule.
-- Safe to run more than once against the local MySQL development database.

INSERT INTO sys_role (
  role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly,
  status, del_flag, create_by, create_time, update_by, update_time, remark
)
SELECT '帮会成员', 'user', 100, '2', 1, 1, '0', '0', 'admin', NOW(), '', NULL, '自助注册默认角色'
WHERE NOT EXISTS (
  SELECT 1 FROM sys_role WHERE role_key = 'user' AND del_flag = '0'
);

UPDATE sys_config
SET config_value = 'true',
    update_by = 'admin',
    update_time = NOW()
WHERE config_key = 'sys.account.registerUser';

UPDATE sys_config
SET config_value = 'false',
    update_by = 'admin',
    update_time = NOW()
WHERE config_key = 'sys.account.captchaEnabled';

INSERT INTO sys_config (
  config_name, config_key, config_value, config_type,
  create_by, create_time, update_by, update_time, remark
)
SELECT
  '账号自助-是否清理24小时未登录注册用户',
  'sys.account.cleanupInactiveRegisteredUsers',
  'false',
  'Y',
  'admin',
  NOW(),
  '',
  NULL,
  '开启后，定时任务会软删除注册后24小时仍未登录的自助注册账号'
WHERE NOT EXISTS (
  SELECT 1 FROM sys_config WHERE config_key = 'sys.account.cleanupInactiveRegisteredUsers'
);

INSERT INTO sys_job (
  job_name, job_group, job_executor, invoke_target, job_args, job_kwargs,
  cron_expression, misfire_policy, concurrent, status,
  create_by, create_time, update_by, update_time, remark
)
SELECT
  '注册用户24小时未登录自动清理',
  'default',
  'default',
  'module_task.user_cleanup.cleanup_inactive_registered_users',
  NULL,
  NULL,
  '0 0 * * * ?',
  '3',
  '1',
  '1',
  'admin',
  NOW(),
  '',
  NULL,
  '清理注册后24小时仍未登录的自助注册账号'
WHERE NOT EXISTS (
  SELECT 1 FROM sys_job WHERE invoke_target = 'module_task.user_cleanup.cleanup_inactive_registered_users'
);

INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, m.menu_id
FROM sys_role r
JOIN sys_menu m ON m.menu_id IN (3000, 3001)
WHERE r.role_key = 'user';

INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, m.menu_id
FROM sys_role r
JOIN sys_menu m ON m.path = 'profile-edit'
WHERE r.role_key = 'user';
