-- Manual MySQL TEST-database menu migration, not registered for automatic startup.
-- Before applying: verify menu_id 47000..47007 are reserved for this feature, and parent paths guild/personal exist.
-- Grants ONLY activity read menus and existing directory ancestors; no schedule edit permissions.
START TRANSACTION;
SET @guild_parent = (SELECT menu_id FROM sys_menu WHERE parent_id=0 AND path='guild' LIMIT 1);
SET @personal_parent = (SELECT menu_id FROM sys_menu WHERE parent_id=0 AND path='personal' LIMIT 1);
-- Remove the obsolete guild-side “找约战” entry and make this manual migration re-runnable.
DELETE FROM sys_role_menu WHERE menu_id BETWEEN 47000 AND 47007;
DELETE FROM sys_menu WHERE menu_id=47002;
DELETE FROM sys_menu WHERE parent_id IN (47000,47004);
DELETE FROM sys_menu WHERE menu_id IN (47000,47004);
INSERT INTO sys_menu(menu_id,menu_name,parent_id,order_num,path,component,query,route_name,is_frame,is_cache,menu_type,visible,status,perms,icon,create_by,create_time)
SELECT 47000,'约战信息',@guild_parent,20,'battle-information','ParentView','','GuildBattleInformation',1,1,'M','0','0','activities:read','date','system',NOW() WHERE @guild_parent IS NOT NULL;
INSERT INTO sys_menu(menu_id,menu_name,parent_id,order_num,path,component,query,route_name,is_frame,is_cache,menu_type,visible,status,perms,icon,create_by,create_time)
SELECT 47004,'约战信息',@personal_parent,20,'battle-information','ParentView','','PersonalBattleInformation',1,1,'M','0','0','activities:read','date','system',NOW() WHERE @personal_parent IS NOT NULL;
INSERT INTO sys_menu(menu_id,menu_name,parent_id,order_num,path,component,query,route_name,is_frame,is_cache,menu_type,visible,status,perms,icon,create_by,create_time)
SELECT 47001,'我的约战',47000,1,'mine','battle-information/mine','','GuildMyBattles',1,1,'C','0','0','activities:read','peoples','system',NOW() WHERE @guild_parent IS NOT NULL UNION ALL
SELECT 47003,'历史约战',47000,2,'history','battle-information/history','','GuildBattleHistory',1,1,'C','0','0','activities:read','documentation','system',NOW() WHERE @guild_parent IS NOT NULL UNION ALL
SELECT 47005,'我的约战',47004,1,'mine','battle-information/mine','','PersonalMyBattles',1,1,'C','0','0','activities:read','peoples','system',NOW() WHERE @personal_parent IS NOT NULL UNION ALL
SELECT 47006,'找约战',47004,2,'public','battle-information/public','','PersonalFindBattles',1,1,'C','0','0','activities:read','search','system',NOW() WHERE @personal_parent IS NOT NULL UNION ALL
SELECT 47007,'历史约战',47004,3,'history','battle-information/history','','PersonalBattleHistory',1,1,'C','0','0','activities:read','documentation','system',NOW() WHERE @personal_parent IS NOT NULL;
INSERT IGNORE INTO sys_role_menu(role_id,menu_id)
SELECT r.role_id,m.menu_id FROM sys_role r JOIN sys_menu m ON (m.menu_id IN (47000,47001,47003,47004,47005,47006,47007) OR m.menu_id IN (@guild_parent,@personal_parent))
WHERE (r.role_id = 1 OR r.role_key IN ('common','user')) AND r.status='0' AND r.del_flag='0';
COMMIT;
-- Clear router/permission caches and re-login after applying; do not grant other guild children to user role.
