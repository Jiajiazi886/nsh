-- 仅在确认已备份并停止新版服务后执行；该脚本会删除账号授权与刷新令牌数据。
DROP TABLE IF EXISTS system_auth_refresh_token;
DROP TABLE IF EXISTS system_account_license_audit;
DROP TABLE IF EXISTS system_account_license;
