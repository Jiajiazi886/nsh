-- 清理非admin角色用户被自动导入的内功数据。
-- 背景：旧前端会在每个用户首次进入内功管理时自动导入同一套示例内功，
-- 导致普通用户看起来共享同一套内功库。本脚本只保留admin角色用户的内功。

DELETE FROM personal_internal_power
WHERE user_id NOT IN (
    SELECT DISTINCT ur.user_id
    FROM sys_user_role ur
    INNER JOIN sys_role r ON r.role_id = ur.role_id
    WHERE r.role_key = 'admin'
);
