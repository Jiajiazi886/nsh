-- Remove the legacy "分团管理" feature page from the sidebar.
-- The "约战排表" page remains under the "分团管理" directory.

DELETE FROM sys_role_menu WHERE menu_id = 2005;
DELETE FROM sys_menu WHERE menu_id = 2005;
