-- ----------------------------
-- 1、部门表
-- ----------------------------
drop table if exists sys_dept;
create table sys_dept (
    dept_id bigserial,
    parent_id bigint default 0,
    ancestors varchar(50) default '',
    dept_name varchar(30) default '',
    order_num int4 default 0,
    leader varchar(20) default null,
    phone varchar(11) default null,
    email varchar(50) default null,
    status char(1) default '0',
    del_flag char(1) default '0',
    create_by varchar(64) default '',
    create_time timestamp(0),
    update_by varchar(64) default '',
    update_time timestamp(0),
    primary key (dept_id)
);
alter sequence sys_dept_dept_id_seq restart 200;
comment on column sys_dept.dept_id is '部门id';
comment on column sys_dept.parent_id is '父部门id';
comment on column sys_dept.ancestors is '祖级列表';
comment on column sys_dept.dept_name is '部门名称';
comment on column sys_dept.order_num is '显示顺序';
comment on column sys_dept.leader is '负责人';
comment on column sys_dept.phone is '联系电话';
comment on column sys_dept.email is '邮箱';
comment on column sys_dept.status is '部门状态（0正常 1停用）';
comment on column sys_dept.del_flag is '删除标志（0代表存在 2代表删除）';
comment on column sys_dept.create_by is '创建者';
comment on column sys_dept.create_time is '创建时间';
comment on column sys_dept.update_by is '更新者';
comment on column sys_dept.update_time is '更新时间';
comment on table sys_dept is '部门表';

-- ----------------------------
-- 初始化-部门表数据
-- ----------------------------
insert into sys_dept values(100,  0,   '0',          '集团总公司',   0, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', current_timestamp, '', null);
insert into sys_dept values(101,  100, '0,100',      '深圳分公司', 1, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', current_timestamp, '', null);
insert into sys_dept values(102,  100, '0,100',      '长沙分公司', 2, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', current_timestamp, '', null);
insert into sys_dept values(103,  101, '0,100,101',  '研发部门',   1, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', current_timestamp, '', null);
insert into sys_dept values(104,  101, '0,100,101',  '市场部门',   2, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', current_timestamp, '', null);
insert into sys_dept values(105,  101, '0,100,101',  '测试部门',   3, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', current_timestamp, '', null);
insert into sys_dept values(106,  101, '0,100,101',  '财务部门',   4, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', current_timestamp, '', null);
insert into sys_dept values(107,  101, '0,100,101',  '运维部门',   5, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', current_timestamp, '', null);
insert into sys_dept values(108,  102, '0,100,102',  '市场部门',   1, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', current_timestamp, '', null);
insert into sys_dept values(109,  102, '0,100,102',  '财务部门',   2, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', current_timestamp, '', null);

-- ----------------------------
-- 2、用户信息表
-- ----------------------------
drop table if exists sys_user;
create table sys_user (
    user_id bigserial not null,
    dept_id bigint default null,
    user_name varchar(30) not null,
    nick_name varchar(30) not null,
    user_type varchar(2) default '00',
    email varchar(50) default '',
    phonenumber varchar(11) default '',
    sex char(1) default '0',
    avatar varchar(100) default '',
    password varchar(100) default '',
    status char(1) default '0',
    is_vip char(1) default '0',
    vip_expire_time timestamp(0),
    ai_image_recognition_count int4 default 0 not null,
    max_internal_power_count int4 default 20 not null,
    del_flag char(1) default '0',
    login_ip varchar(128) default '',
    login_date timestamp(0),
    pwd_update_date timestamp(0),
    create_by varchar(64) default '',
    create_time timestamp(0),
    update_by varchar(64) default '',
    update_time timestamp(0),
    remark varchar(500) default null,
    primary key (user_id)
);
alter sequence sys_user_user_id_seq restart 100;
comment on column sys_user.user_id is '用户ID';
comment on column sys_user.dept_id is '部门ID';
comment on column sys_user.user_name is '用户账号';
comment on column sys_user.nick_name is '用户昵称';
comment on column sys_user.user_type is '用户类型（00系统用户）';
comment on column sys_user.email is '用户邮箱';
comment on column sys_user.phonenumber is '手机号码';
comment on column sys_user.sex is '用户性别（0男 1女 2未知）';
comment on column sys_user.avatar is '头像地址';
comment on column sys_user.password is '密码';
comment on column sys_user.status is '帐号状态（0正常 1停用）';
comment on column sys_user.is_vip is 'VIP标识（0非VIP 1VIP）';
comment on column sys_user.vip_expire_time is 'VIP到期时间';
comment on column sys_user.ai_image_recognition_count is 'AI识图剩余次数';
comment on column sys_user.max_internal_power_count is '最大内功数';
comment on column sys_user.del_flag is '删除标志（0代表存在 2代表删除）';
comment on column sys_user.login_ip is '最后登录IP';
comment on column sys_user.login_date is '最后登录时间';
comment on column sys_user.pwd_update_date is '密码最后更新时间';
comment on column sys_user.create_by is '创建者';
comment on column sys_user.create_time is '创建时间';
comment on column sys_user.update_by is '更新者';
comment on column sys_user.update_time is '更新时间';
comment on column sys_user.remark is '备注';
comment on table sys_user is '用户信息表';

-- ----------------------------
-- 初始化-用户信息表数据
-- ----------------------------
insert into sys_user values(1,  103, 'admin',   '超级管理员', '00', 'niangao@163.com', '15888888888', '1', '', '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2', '0', '1', '2099-12-31 23:59:59', 0, 20, '0', '127.0.0.1', current_timestamp, current_timestamp, 'admin', current_timestamp, '', null, '管理员');
insert into sys_user values(2,  105, 'niangao', '年糕', 			'00', 'niangao@qq.com',  '15666666666', '1', '', '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2', '0', '0', null, 0, 20, '0', '127.0.0.1', current_timestamp, current_timestamp, 'admin', current_timestamp, '', null, '测试员');

-- ----------------------------
-- 2-1、个人内功表
-- ----------------------------
drop table if exists personal_internal_power;
create table personal_internal_power (
    power_id bigserial not null,
    user_id bigint not null,
    name varchar(64) not null,
    category varchar(64) default '',
    category_trait varchar(128) default '',
    bonus_percent float8 default 0 not null,
    lingyun_enabled char(1) default '0' not null,
    lingyun_bonus_percent float8 default 0 not null,
    entries_json text,
    elements_json text,
    remark varchar(500) default '',
    create_time timestamp(0),
    update_time timestamp(0),
    primary key (power_id)
);
create index idx_personal_internal_power_user_id on personal_internal_power(user_id);
comment on column personal_internal_power.power_id is '内功ID';
comment on column personal_internal_power.user_id is '用户ID';
comment on column personal_internal_power.name is '内功名称';
comment on column personal_internal_power.category is '内功种类';
comment on column personal_internal_power.category_trait is '种类特性';
comment on column personal_internal_power.bonus_percent is '基础百分比加成';
comment on column personal_internal_power.lingyun_enabled is '是否启用灵韵（0否 1是）';
comment on column personal_internal_power.lingyun_bonus_percent is '灵韵百分比提升';
comment on column personal_internal_power.entries_json is '词条JSON';
comment on column personal_internal_power.elements_json is '五行JSON';
comment on column personal_internal_power.remark is '备注';
comment on column personal_internal_power.create_time is '创建时间';
comment on column personal_internal_power.update_time is '更新时间';
comment on table personal_internal_power is '个人内功表';

-- ----------------------------
-- 3、岗位信息表
-- ----------------------------
drop table if exists sys_post;
create table sys_post (
    post_id bigserial not null,
    post_code varchar(64) not null,
    post_name varchar(50) not null,
    post_sort int4 not null,
    status char(1) not null,
    create_by varchar(64) default '',
    create_time timestamp(0),
    update_by varchar(64) default '',
    update_time timestamp(0),
    remark varchar(500) default null,
    primary key (post_id)
);
alter sequence sys_post_post_id_seq restart 5;
comment on column sys_post.post_id is '岗位ID';
comment on column sys_post.post_code is '岗位编码';
comment on column sys_post.post_name is '岗位名称';
comment on column sys_post.post_sort is '显示顺序';
comment on column sys_post.status is '状态（0正常 1停用）';
comment on column sys_post.create_by is '创建者';
comment on column sys_post.create_time is '创建时间';
comment on column sys_post.update_by is '更新者';
comment on column sys_post.update_time is '更新时间';
comment on column sys_post.remark is '备注';
comment on table sys_post is '岗位信息表';

-- ----------------------------
-- 初始化-岗位信息表数据
-- ----------------------------
insert into sys_post values(1, 'ceo',  '董事长',    1, '0', 'admin', current_timestamp, '', null, '');
insert into sys_post values(2, 'se',   '项目经理',  2, '0', 'admin', current_timestamp, '', null, '');
insert into sys_post values(3, 'hr',   '人力资源',  3, '0', 'admin', current_timestamp, '', null, '');
insert into sys_post values(4, 'user', '普通员工',  4, '0', 'admin', current_timestamp, '', null, '');

-- ----------------------------
-- 4、角色信息表
-- ----------------------------
drop table if exists sys_role;
create table sys_role (
    role_id bigserial not null,
    role_name varchar(30) not null,
    role_key varchar(100) not null,
    role_sort int4 not null,
    data_scope char(1) default '1',
    menu_check_strictly smallint default 1,
    dept_check_strictly smallint default 1,
    status char(1) not null,
    del_flag char(1) default '0',
    create_by varchar(64)  default '',
    create_time timestamp(0),
    update_by varchar(64)  default '',
    update_time timestamp(0),
    remark varchar(500)  default null,
    primary key (role_id)
);
alter sequence sys_role_role_id_seq restart 101;
comment on column sys_role.role_id is '角色ID';
comment on column sys_role.role_name is '角色名称';
comment on column sys_role.role_key is '角色权限字符串';
comment on column sys_role.role_sort is '显示顺序';
comment on column sys_role.data_scope is '数据范围（1：全部数据权限 2：自定数据权限 3：本部门数据权限 4：本部门及以下数据权限）';
comment on column sys_role.menu_check_strictly is '菜单树选择项是否关联显示';
comment on column sys_role.dept_check_strictly is '部门树选择项是否关联显示';
comment on column sys_role.status is '角色状态（0正常 1停用）';
comment on column sys_role.del_flag is '删除标志（0代表存在 2代表删除）';
comment on column sys_role.create_by is '创建者';
comment on column sys_role.create_time is '创建时间';
comment on column sys_role.update_by is '更新者';
comment on column sys_role.update_time is '更新时间';
comment on column sys_role.remark is '备注';
comment on table sys_role is '角色信息表';

-- ----------------------------
-- 初始化-角色信息表数据
-- ----------------------------
insert into sys_role values(1, '超级管理员',  'admin',  1, 1, 1, 1, '0', '0', 'system', current_timestamp, '', null, '系统内置超级管理员角色');
insert into sys_role values(2, '帮会管理',    'common', 2, 2, 1, 1, '0', '0', 'system', current_timestamp, '', null, '系统内置帮会管理角色');
insert into sys_role values(100, '帮会成员',  'user',   0, 2, 1, 1, '0', '0', 'system', current_timestamp, '', null, '系统内置帮会成员角色');

-- ----------------------------
-- 5、菜单权限表
-- ----------------------------
drop table if exists sys_menu;
create table sys_menu (
    menu_id bigserial not null,
    menu_name varchar(50) not null,
    parent_id bigint default 0,
    order_num int4 default 0,
    path varchar(200) default '',
    component varchar(255) default null,
    query varchar(255) default null,
    route_name varchar(50) default '',
    is_frame int4 default 1,
    is_cache int4 default 0,
    menu_type char(1) default '',
    visible char(1) default '0',
    status char(1) default '0',
    perms varchar(100) default null,
    icon varchar(100) default '#',
    create_by varchar(64) default '',
    create_time timestamp(0),
    update_by varchar(64) default '',
    update_time timestamp(0),
    remark varchar(500) default '',
    primary key (menu_id)
);
alter sequence sys_menu_menu_id_seq restart 2000;
comment on column sys_menu.menu_id is '菜单ID';
comment on column sys_menu.menu_name is '菜单名称';
comment on column sys_menu.parent_id is '父菜单ID';
comment on column sys_menu.order_num is '显示顺序';
comment on column sys_menu.path is '路由地址';
comment on column sys_menu.component is '组件路径';
comment on column sys_menu.query is '路由参数';
comment on column sys_menu.route_name is '路由名称';
comment on column sys_menu.is_frame is '是否为外链（0是 1否）';
comment on column sys_menu.is_cache is '是否缓存（0缓存 1不缓存）';
comment on column sys_menu.menu_type is '菜单类型（M目录 C菜单 F按钮）';
comment on column sys_menu.visible is '菜单状态（0显示 1隐藏）';
comment on column sys_menu.status is '菜单状态（0正常 1停用）';
comment on column sys_menu.perms is '权限标识';
comment on column sys_menu.icon is '菜单图标';
comment on column sys_menu.create_by is '创建者';
comment on column sys_menu.create_time is '创建时间';
comment on column sys_menu.update_by is '更新者';
comment on column sys_menu.update_time is '更新时间';
comment on column sys_menu.remark is '备注';
comment on table sys_menu is '菜单权限表';

-- ----------------------------
-- 初始化-菜单信息表数据
-- ----------------------------
insert into sys_menu values(1, '系统管理', 0, 1, 'system', null, '', '', 1, 0, 'M', '0', '0', '', 'system', 'system', current_timestamp, 'system', current_timestamp, '系统管理目录');
insert into sys_menu values(2, '系统监控', 0, 2, 'monitor', null, '', '', 1, 0, 'M', '0', '0', '', 'monitor', 'system', current_timestamp, 'system', current_timestamp, '系统监控目录');
insert into sys_menu values(3, '系统工具', 0, 3, 'tool', null, '', '', 1, 0, 'M', '0', '0', '', 'tool', 'system', current_timestamp, 'system', current_timestamp, '系统工具目录');
insert into sys_menu values(100, '用户管理', 1, 1, 'user', 'system/user/index', '', '', 1, 0, 'C', '0', '0', 'system:user:list', 'user', 'system', current_timestamp, 'system', current_timestamp, '用户管理菜单');
insert into sys_menu values(101, '角色管理', 1, 2, 'role', 'system/role/index', '', '', 1, 0, 'C', '0', '0', 'system:role:list', 'peoples', 'system', current_timestamp, 'system', current_timestamp, '角色管理菜单');
insert into sys_menu values(102, '菜单管理', 1, 3, 'menu', 'system/menu/index', '', '', 1, 0, 'C', '0', '0', 'system:menu:list', 'tree-table', 'system', current_timestamp, 'system', current_timestamp, '菜单管理菜单');
insert into sys_menu values(105, '字典管理', 1, 6, 'dict', 'system/dict/index', '', '', 1, 0, 'C', '0', '0', 'system:dict:list', 'dict', 'system', current_timestamp, 'system', current_timestamp, '字典管理菜单');
insert into sys_menu values(106, '参数设置', 1, 7, 'config', 'system/config/index', '', '', 1, 0, 'C', '0', '0', 'system:config:list', 'edit', 'system', current_timestamp, 'system', current_timestamp, '参数设置菜单');
insert into sys_menu values(107, '通知公告', 1, 8, 'notice', 'system/notice/index', '', '', 1, 0, 'C', '0', '0', 'system:notice:list', 'message', 'system', current_timestamp, 'system', current_timestamp, '通知公告菜单');
insert into sys_menu values(108, '日志管理', 1, 9, 'log', '', '', '', 1, 0, 'M', '0', '0', '', 'log', 'system', current_timestamp, 'system', current_timestamp, '日志管理菜单');
insert into sys_menu values(109, '在线用户', 2, 1, 'online', 'monitor/online/index', '', '', 1, 0, 'C', '0', '0', 'monitor:online:list', 'online', 'system', current_timestamp, 'system', current_timestamp, '在线用户菜单');
insert into sys_menu values(110, '定时任务', 2, 2, 'job', 'monitor/job/index', '', '', 1, 0, 'C', '0', '0', 'monitor:job:list', 'job', 'system', current_timestamp, 'system', current_timestamp, '定时任务菜单');
insert into sys_menu values(111, '数据监控', 2, 3, 'druid', 'monitor/druid/index', '', '', 1, 0, 'C', '0', '0', 'monitor:druid:list', 'druid', 'system', current_timestamp, 'system', current_timestamp, '数据监控菜单');
insert into sys_menu values(112, '服务监控', 2, 4, 'server', 'monitor/server/index', '', '', 1, 0, 'C', '0', '0', 'monitor:server:list', 'server', 'system', current_timestamp, 'system', current_timestamp, '服务监控菜单');
insert into sys_menu values(113, '缓存监控', 2, 5, 'cache', 'monitor/cache/index', '', '', 1, 0, 'C', '0', '0', 'monitor:cache:list', 'redis', 'system', current_timestamp, 'system', current_timestamp, '缓存监控菜单');
insert into sys_menu values(114, '缓存列表', 2, 6, 'cacheList', 'monitor/cache/list', '', '', 1, 0, 'C', '0', '0', 'monitor:cache:list', 'redis-list', 'system', current_timestamp, 'system', current_timestamp, '缓存列表菜单');
insert into sys_menu values(115, '表单构建', 3, 1, 'build', 'tool/build/index', '', '', 1, 0, 'C', '0', '0', 'tool:build:list', 'build', 'system', current_timestamp, 'system', current_timestamp, '表单构建菜单');
insert into sys_menu values(116, '代码生成', 3, 2, 'gen', 'tool/gen/index', '', '', 1, 0, 'C', '0', '0', 'tool:gen:list', 'code', 'system', current_timestamp, 'system', current_timestamp, '代码生成菜单');
insert into sys_menu values(117, '系统接口', 3, 3, 'swagger', 'tool/swagger/index', '', '', 1, 0, 'C', '0', '0', 'tool:swagger:list', 'swagger', 'system', current_timestamp, 'system', current_timestamp, '系统接口菜单');
insert into sys_menu values(120, '传输加密', 2, 7, 'transportCrypto', 'monitor/transportCrypto/index', '', '', 1, 0, 'C', '0', '0', 'monitor:transportCrypto:list', 'chart', 'system', current_timestamp, 'system', current_timestamp, '传输加密监控菜单');
insert into sys_menu values(500, '操作日志', 108, 1, 'operlog', 'monitor/operlog/index', '', '', 1, 0, 'C', '0', '0', 'monitor:operlog:list', 'form', 'system', current_timestamp, 'system', current_timestamp, '操作日志菜单');
insert into sys_menu values(501, '登录日志', 108, 2, 'logininfor', 'monitor/logininfor/index', '', '', 1, 0, 'C', '0', '0', 'monitor:logininfor:list', 'logininfor', 'system', current_timestamp, 'system', current_timestamp, '登录日志菜单');
insert into sys_menu values(1000, '用户查询', 100, 1, '', '', '', '', 1, 0, 'F', '0', '0', 'system:user:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1001, '用户新增', 100, 2, '', '', '', '', 1, 0, 'F', '0', '0', 'system:user:add', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1002, '用户修改', 100, 3, '', '', '', '', 1, 0, 'F', '0', '0', 'system:user:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1003, '用户删除', 100, 4, '', '', '', '', 1, 0, 'F', '0', '0', 'system:user:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1004, '用户导出', 100, 5, '', '', '', '', 1, 0, 'F', '0', '0', 'system:user:export', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1005, '用户导入', 100, 6, '', '', '', '', 1, 0, 'F', '0', '0', 'system:user:import', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1006, '重置密码', 100, 7, '', '', '', '', 1, 0, 'F', '0', '0', 'system:user:resetPwd', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1007, '角色查询', 101, 1, '', '', '', '', 1, 0, 'F', '0', '0', 'system:role:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1008, '角色新增', 101, 2, '', '', '', '', 1, 0, 'F', '0', '0', 'system:role:add', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1009, '角色修改', 101, 3, '', '', '', '', 1, 0, 'F', '0', '0', 'system:role:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1010, '角色删除', 101, 4, '', '', '', '', 1, 0, 'F', '0', '0', 'system:role:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1011, '角色导出', 101, 5, '', '', '', '', 1, 0, 'F', '0', '0', 'system:role:export', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1012, '菜单查询', 102, 1, '', '', '', '', 1, 0, 'F', '0', '0', 'system:menu:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1013, '菜单新增', 102, 2, '', '', '', '', 1, 0, 'F', '0', '0', 'system:menu:add', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1014, '菜单修改', 102, 3, '', '', '', '', 1, 0, 'F', '0', '0', 'system:menu:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1015, '菜单删除', 102, 4, '', '', '', '', 1, 0, 'F', '0', '0', 'system:menu:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1025, '字典查询', 105, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:dict:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1026, '字典新增', 105, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:dict:add', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1027, '字典修改', 105, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:dict:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1028, '字典删除', 105, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:dict:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1029, '字典导出', 105, 5, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:dict:export', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1030, '参数查询', 106, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:config:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1031, '参数新增', 106, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:config:add', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1032, '参数修改', 106, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:config:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1033, '参数删除', 106, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:config:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1034, '参数导出', 106, 5, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:config:export', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1035, '公告查询', 107, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:notice:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1036, '公告新增', 107, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:notice:add', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1037, '公告修改', 107, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:notice:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1038, '公告删除', 107, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:notice:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1039, '操作查询', 500, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:operlog:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1040, '操作删除', 500, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:operlog:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1041, '日志导出', 500, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:operlog:export', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1042, '登录查询', 501, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:logininfor:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1043, '登录删除', 501, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:logininfor:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1044, '日志导出', 501, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:logininfor:export', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1045, '账户解锁', 501, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:logininfor:unlock', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1046, '在线查询', 109, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:online:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1047, '批量强退', 109, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:online:batchLogout', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1048, '单条强退', 109, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:online:forceLogout', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1049, '任务查询', 110, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:job:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1050, '任务新增', 110, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:job:add', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1051, '任务修改', 110, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:job:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1052, '任务删除', 110, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:job:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1053, '状态修改', 110, 5, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:job:changeStatus', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1054, '任务导出', 110, 6, '#', '', '', '', 1, 0, 'F', '0', '0', 'monitor:job:export', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1055, '生成查询', 116, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'tool:gen:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1056, '生成修改', 116, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'tool:gen:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1057, '生成删除', 116, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'tool:gen:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1058, '导入代码', 116, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'tool:gen:import', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1059, '预览代码', 116, 5, '#', '', '', '', 1, 0, 'F', '0', '0', 'tool:gen:preview', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1060, '生成代码', 116, 6, '#', '', '', '', 1, 0, 'F', '0', '0', 'tool:gen:code', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1065, '帮会管理', 0, 4, 'guild', 'Layout', null, '', 1, 0, 'M', '0', '0', '', 'people', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1066, '帮会信息', 1065, 1, 'info', 'guild/info/index', null, '', 1, 0, 'C', '0', '0', 'guild:info:list', 'people', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1067, '成员管理', 1065, 2, 'member', 'guild/member/index', null, '', 1, 0, 'C', '0', '0', 'guild:member:list', 'user', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1068, '分团管理', 1065, 3, 'group', 'ParentView', null, '', 1, 0, 'M', '0', '0', '', 'tree', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1069, '约战管理', 1065, 4, 'battle', 'ParentView', null, '', 1, 0, 'M', '0', '0', '', 'swagger', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1070, '历史数据管理', 1069, 1, 'list', 'guild/battle/list', null, '', 1, 0, 'C', '0', '0', 'guild:battle:list', 'form', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1071, '约战报名', 1069, 2, 'registration', 'guild/battle/registration', null, '', 1, 0, 'C', '0', '0', 'guild:battle:registration:list', 'edit', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1072, '数据导入', 1069, 3, 'import', 'guild/battle/import', null, '', 1, 0, 'C', '0', '0', 'guild:battle:import', 'upload', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1073, '审核管理', 1065, 5, 'review', 'ParentView', null, '', 1, 0, 'M', '0', '0', '', 'checkbox', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1074, '成员审核', 1073, 1, 'member', 'guild/review/member', null, '', 1, 0, 'C', '0', '0', 'guild:review:member:list', 'peoples', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1075, '约战审核', 1073, 2, 'battle', 'guild/review/battle', null, '', 1, 0, 'C', '0', '0', 'guild:review:battle:list', 'eye-open', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(1076, '数据分析', 1065, 6, 'analysis', 'guild/analysis/index', null, '', 1, 0, 'C', '0', '0', 'guild:analysis:list', 'chart', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(2000, '战斗明细查询', 1069, 4, '', '', null, '', 1, 0, 'F', '0', '0', 'guild:battle:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(2001, '战斗记录删除', 1069, 4, '', '', null, '', 1, 0, 'F', '0', '0', 'guild:battle:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(2002, '职业颜色设置', 1065, 7, 'classColor', 'guild/classColor/index', '', '', 1, 0, 'C', '0', '0', 'guild:classColor:list', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(2003, '职业颜色查询', 2002, 1, '', '', null, '', 1, 0, 'F', '0', '0', 'guild:class-color:query', '', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(2004, '职业颜色修改', 2002, 2, '', '', null, '', 1, 0, 'F', '0', '0', 'guild:class-color:edit', '', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(2006, '约战排表', 1068, 2, 'schedule', 'guild/schedule/index', '', '', 1, 0, 'C', '0', '0', 'guild:schedule:list', 'table', 'system', current_timestamp, 'system', current_timestamp, '约战排表占位');
insert into sys_menu values(3000, '个人管理', 0, 5, 'personal', 'Layout', '', '', 1, 0, 'M', '0', '0', '', 'user', 'system', current_timestamp, 'system', current_timestamp, '个人管理目录');
insert into sys_menu values(3001, '加入帮会', 3000, 1, 'join', 'personal/coming-soon/index', '', '', 1, 0, 'C', '0', '0', 'personal:join:list', 'people', 'system', current_timestamp, 'system', current_timestamp, '加入帮会占位菜单');
insert into sys_menu values(3002, '内功管理', 3000, 2, 'skill', 'personal/coming-soon/index', '', '', 1, 0, 'C', '0', '0', 'personal:skill:list', 'skill', 'system', current_timestamp, 'system', current_timestamp, '内功管理占位菜单');
insert into sys_menu values(3003, '个人信息编辑', 3000, 3, 'profile-edit', 'personal/coming-soon/index', '', '', 1, 0, 'C', '0', '0', 'personal:profile:edit', 'edit', 'system', current_timestamp, 'system', current_timestamp, '个人信息编辑占位菜单');
insert into sys_menu values(3004, '内功数值编辑', 3002, 1, '', '', '', '', 1, 0, 'F', '0', '0', 'personal:skill:value-edit', '#', 'system', current_timestamp, 'system', current_timestamp, '内功管理按钮权限：编辑内功种类与基础增伤');
insert into sys_menu values(3005, '防守计算器', 3000, 4, 'defense-calculator', 'personal/calculator/index', '', 'PersonalDefenseCalculator', 1, 0, 'C', '0', '0', 'personal:defense-calculator:list', 'shield', 'system', current_timestamp, 'system', current_timestamp, '防守计算器菜单');
insert into sys_menu values(3006, '拆塔计算器', 3000, 5, 'tower-calculator', 'personal/calculator/index', '', '', 1, 0, 'C', '0', '0', 'personal:tower-calculator:list', 'build', 'system', current_timestamp, 'system', current_timestamp, '拆塔计算器占位菜单');
insert into sys_menu values(3007, '素/鸿计算器', 3000, 6, 'suhong-calculator', 'personal/calculator/index', '', '', 1, 0, 'C', '0', '0', 'personal:suhong-calculator:list', 'calculator', 'system', current_timestamp, 'system', current_timestamp, '素/鸿计算器占位菜单');
insert into sys_menu values(3010, '排表详情查询', 2006, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3011, '创建排表团队', 2006, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:team:add', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3012, '删除排表团队', 2006, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:team:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3013, '创建排表小队', 2006, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:squad:add', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3014, '删除排表小队', 2006, 5, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:squad:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3015, '保存排表成员', 2006, 6, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3016, '排表历史查询', 2006, 7, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:history', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3017, '保存排表历史', 2006, 8, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:snapshot', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3018, 'Apply Schedule History', 2006, 9, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:schedule:apply', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3028, '职业信息', 1065, 8, 'profession', 'guild/profession/index', '', 'GuildProfession', 1, 0, 'C', '0', '0', 'guild:profession:read', 'dict', 'system', current_timestamp, 'system', current_timestamp, '职业信息菜单');
insert into sys_menu values(3029, '职业信息读取', 3028, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:profession:read', '#', 'system', current_timestamp, 'system', current_timestamp, '职业信息读权限');
insert into sys_menu values(3030, '职业信息写入', 3028, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'guild:profession:write', '#', 'system', current_timestamp, 'system', current_timestamp, '职业信息写权限');
insert into sys_menu values(3040, '数据库管理', 1, 10, 'database', 'system/database/index', '', 'SystemDatabase', 1, 0, 'C', '0', '0', 'system:database:list', 'table', 'system', current_timestamp, 'system', current_timestamp, '超级管理员只读数据库浏览器');
insert into sys_menu values(3041, '数据库列表', 3040, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:database:list', '#', 'system', current_timestamp, 'system', current_timestamp, '查看数据库表结构与用户总览');
insert into sys_menu values(3042, '数据库查询', 3040, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:database:query', '#', 'system', current_timestamp, 'system', current_timestamp, '查看数据表分页数据');
insert into sys_menu values(3050, 'AIKey管理', 1, 11, 'aiKey', 'system/aiKey/index', '', 'SystemAiKey', 1, 0, 'C', '0', '0', 'system:aikey:edit', 'lock', 'system', current_timestamp, 'system', current_timestamp, '维护内功图片识别 API Key');
insert into sys_menu values(3100, '内功信息管理', 1, 10, 'internalPower', 'system/internalPower/index', '', 'SystemInternalPower', 1, 0, 'C', '0', '0', 'system:internal-power:list', 'skill', 'system', current_timestamp, 'system', current_timestamp, '系统内功信息管理菜单');
insert into sys_menu values(3101, '内功信息查询', 3100, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3102, '内功信息新增', 3100, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power:add', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3103, '内功信息修改', 3100, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3104, '内功信息删除', 3100, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3110, '内功词条管理', 1, 11, 'internalPowerEntry', 'system/internalPowerEntry/index', '', 'SystemInternalPowerEntry', 1, 0, 'C', '0', '0', 'system:internal-power-entry:list', 'list', 'system', current_timestamp, 'system', current_timestamp, '系统内功词条管理菜单；词条上限由管理员维护');
insert into sys_menu values(3111, '内功词条查询', 3110, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-entry:query', '#', 'system', current_timestamp, 'system', current_timestamp, '已迁移到个人管理，保留旧接口避免兼容问题');
insert into sys_menu values(3112, '内功词条新增', 3110, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-entry:add', '#', 'system', current_timestamp, 'system', current_timestamp, '已迁移到个人管理，保留旧接口避免兼容问题');
insert into sys_menu values(3113, '内功词条修改', 3110, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-entry:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '已迁移到个人管理，保留旧接口避免兼容问题');
insert into sys_menu values(3114, '内功词条删除', 3110, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-entry:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '已迁移到个人管理，保留旧接口避免兼容问题');
insert into sys_menu values(3115, '面板设置', 3000, 7, 'internal-power-panel', 'personal/internalPowerPanel/index', '', 'PersonalInternalPowerPanel', 1, 0, 'C', '0', '0', 'personal:internal-power-panel:list', 'chart', 'system', current_timestamp, 'system', current_timestamp, '个人内功PVP收益面板设置菜单');
insert into sys_menu values(3116, '面板设置保存', 3115, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'personal:internal-power-panel:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3120, '图片显示管理', 1, 12, 'imageDisplay', 'system/imageDisplay/index', '', 'SystemImageDisplay', 1, 0, 'C', '0', '0', 'system:internal-power-image-display:list', 'eye-open', 'system', current_timestamp, 'system', current_timestamp, '内功图片显示全局开关菜单');
insert into sys_menu values(3121, '图片显示查询', 3120, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-image-display:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3122, '图片显示修改', 3120, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-image-display:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3130, 'VIP授权修改', 100, 8, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:user:vip:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3131, '赞助状态修改', 100, 9, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:user:sponsor:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3132, 'AI识图次数修改', 100, 10, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:user:ai:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3140, '公式设计', 1, 13, 'formulaDesign', 'system/formulaDesign/index', '', 'SystemFormulaDesign', 1, 0, 'C', '0', '0', 'system:formula-design:list', 'edit', 'system', current_timestamp, 'system', current_timestamp, '系统内功PVP收益公式设计菜单');
insert into sys_menu values(3141, '公式版本查询', 3140, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:formula-design:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3142, '公式版本新增', 3140, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:formula-design:add', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3143, '公式版本修改', 3140, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:formula-design:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3144, '公式版本发布', 3140, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:formula-design:publish', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3150, '面板模板设置', 1, 14, 'internalPowerPanelTemplate', 'system/internalPowerPanelTemplate/index', '', 'SystemInternalPowerPanelTemplate', 1, 0, 'C', '0', '0', 'system:internal-power-panel-template:list', 'chart', 'system', current_timestamp, 'system', current_timestamp, '系统内功PVP收益面板模板设置菜单');
insert into sys_menu values(3151, '面板模板查询', 3150, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-panel-template:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3152, '面板模板新增', 3150, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-panel-template:add', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3153, '面板模板修改', 3150, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-panel-template:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3154, '面板模板删除', 3150, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-panel-template:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3155, '面板模板启停', 3150, 5, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:internal-power-panel-template:status', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3160, '进攻方面板设置', 1, 14, 'pvpAttackPanel', 'system/pvpAttackPanel/index', '', 'SystemPvpAttackPanel', 1, 0, 'C', '0', '0', 'system:pvp-attack-panel:list', 'histogram', 'system', current_timestamp, 'system', current_timestamp, '管理员维护防守计算器进攻方面板');
insert into sys_menu values(3161, '进攻方面板查询', 3160, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:pvp-attack-panel:query', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3162, '进攻方面板新增', 3160, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:pvp-attack-panel:add', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3163, '进攻方面板修改', 3160, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:pvp-attack-panel:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3164, '进攻方面板删除', 3160, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:pvp-attack-panel:remove', '#', 'system', current_timestamp, 'system', current_timestamp, '');
insert into sys_menu values(3165, '职业加成设置', 1, 15, 'pvpDefenseProfessionBonus', 'system/pvpDefenseProfessionBonus/index', '', 'SystemPvpDefenseProfessionBonus', 1, 0, 'C', '0', '0', 'system:pvp-defense-profession-bonus:list', 'setting', 'system', current_timestamp, 'system', current_timestamp, '管理员维护防守计算器职业默认加成');
insert into sys_menu values(3166, '职业加成修改', 3165, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'system:pvp-defense-profession-bonus:edit', '#', 'system', current_timestamp, 'system', current_timestamp, '');
select setval(pg_get_serial_sequence('sys_menu', 'menu_id'), (select max(menu_id) from sys_menu), true);

-- 6、用户和角色关联表  用户N-1角色
-- ----------------------------
drop table if exists sys_user_role;
create table sys_user_role (
    user_id bigint not null,
    role_id bigint not null,
    primary key (user_id, role_id)
);
comment on column sys_user_role.user_id is '用户ID';
comment on column sys_user_role.role_id is '角色ID';
comment on table sys_user_role is '用户和角色关联表';

-- ----------------------------
-- 初始化-用户和角色关联表数据
-- ----------------------------
insert into sys_user_role values (1, 1);
insert into sys_user_role values (2, 2);

-- ----------------------------
-- 7、角色和菜单关联表  角色1-N菜单
-- ----------------------------
drop table if exists sys_role_menu;
create table sys_role_menu (
    role_id bigint not null,
    menu_id bigint not null,
    primary key (role_id, menu_id)
);
comment on column sys_role_menu.role_id is '角色ID';
comment on column sys_role_menu.menu_id is '菜单ID';
comment on table sys_role_menu is '角色和菜单关联表';

-- ----------------------------
-- 初始化-角色和菜单关联表数据
-- ----------------------------
insert into sys_role_menu values (1, 1);
insert into sys_role_menu values (1, 2);
insert into sys_role_menu values (1, 3);
insert into sys_role_menu values (1, 100);
insert into sys_role_menu values (1, 101);
insert into sys_role_menu values (1, 102);
insert into sys_role_menu values (1, 105);
insert into sys_role_menu values (1, 106);
insert into sys_role_menu values (1, 107);
insert into sys_role_menu values (1, 108);
insert into sys_role_menu values (1, 109);
insert into sys_role_menu values (1, 110);
insert into sys_role_menu values (1, 111);
insert into sys_role_menu values (1, 112);
insert into sys_role_menu values (1, 113);
insert into sys_role_menu values (1, 114);
insert into sys_role_menu values (1, 115);
insert into sys_role_menu values (1, 116);
insert into sys_role_menu values (1, 117);
insert into sys_role_menu values (1, 120);
insert into sys_role_menu values (1, 500);
insert into sys_role_menu values (1, 501);
insert into sys_role_menu values (1, 1000);
insert into sys_role_menu values (1, 1001);
insert into sys_role_menu values (1, 1002);
insert into sys_role_menu values (1, 1003);
insert into sys_role_menu values (1, 1004);
insert into sys_role_menu values (1, 1005);
insert into sys_role_menu values (1, 1006);
insert into sys_role_menu values (1, 1007);
insert into sys_role_menu values (1, 1008);
insert into sys_role_menu values (1, 1009);
insert into sys_role_menu values (1, 1010);
insert into sys_role_menu values (1, 1011);
insert into sys_role_menu values (1, 1012);
insert into sys_role_menu values (1, 1013);
insert into sys_role_menu values (1, 1014);
insert into sys_role_menu values (1, 1015);
insert into sys_role_menu values (1, 1025);
insert into sys_role_menu values (1, 1026);
insert into sys_role_menu values (1, 1027);
insert into sys_role_menu values (1, 1028);
insert into sys_role_menu values (1, 1029);
insert into sys_role_menu values (1, 1030);
insert into sys_role_menu values (1, 1031);
insert into sys_role_menu values (1, 1032);
insert into sys_role_menu values (1, 1033);
insert into sys_role_menu values (1, 1034);
insert into sys_role_menu values (1, 1035);
insert into sys_role_menu values (1, 1036);
insert into sys_role_menu values (1, 1037);
insert into sys_role_menu values (1, 1038);
insert into sys_role_menu values (1, 1039);
insert into sys_role_menu values (1, 1040);
insert into sys_role_menu values (1, 1041);
insert into sys_role_menu values (1, 1042);
insert into sys_role_menu values (1, 1043);
insert into sys_role_menu values (1, 1044);
insert into sys_role_menu values (1, 1045);
insert into sys_role_menu values (1, 1046);
insert into sys_role_menu values (1, 1047);
insert into sys_role_menu values (1, 1048);
insert into sys_role_menu values (1, 1049);
insert into sys_role_menu values (1, 1050);
insert into sys_role_menu values (1, 1051);
insert into sys_role_menu values (1, 1052);
insert into sys_role_menu values (1, 1053);
insert into sys_role_menu values (1, 1054);
insert into sys_role_menu values (1, 1055);
insert into sys_role_menu values (1, 1056);
insert into sys_role_menu values (1, 1057);
insert into sys_role_menu values (1, 1058);
insert into sys_role_menu values (1, 1059);
insert into sys_role_menu values (1, 1060);
insert into sys_role_menu values (1, 1065);
insert into sys_role_menu values (1, 1066);
insert into sys_role_menu values (1, 1067);
insert into sys_role_menu values (1, 1068);
insert into sys_role_menu values (1, 1069);
insert into sys_role_menu values (1, 1070);
insert into sys_role_menu values (1, 1071);
insert into sys_role_menu values (1, 1072);
insert into sys_role_menu values (1, 1073);
insert into sys_role_menu values (1, 1074);
insert into sys_role_menu values (1, 1075);
insert into sys_role_menu values (1, 1076);
insert into sys_role_menu values (1, 2000);
insert into sys_role_menu values (1, 2001);
insert into sys_role_menu values (1, 2002);
insert into sys_role_menu values (1, 2003);
insert into sys_role_menu values (1, 2004);
insert into sys_role_menu values (1, 2006);
insert into sys_role_menu values (1, 3000);
insert into sys_role_menu values (1, 3001);
insert into sys_role_menu values (1, 3002);
insert into sys_role_menu values (1, 3003);
insert into sys_role_menu values (1, 3004);
insert into sys_role_menu values (1, 3005);
insert into sys_role_menu values (1, 3006);
insert into sys_role_menu values (1, 3007);
insert into sys_role_menu values (1, 3010);
insert into sys_role_menu values (1, 3011);
insert into sys_role_menu values (1, 3012);
insert into sys_role_menu values (1, 3013);
insert into sys_role_menu values (1, 3014);
insert into sys_role_menu values (1, 3015);
insert into sys_role_menu values (1, 3016);
insert into sys_role_menu values (1, 3017);
insert into sys_role_menu values (1, 3018);
insert into sys_role_menu values (1, 3028);
insert into sys_role_menu values (1, 3029);
insert into sys_role_menu values (1, 3030);
insert into sys_role_menu values (1, 3040);
insert into sys_role_menu values (1, 3041);
insert into sys_role_menu values (1, 3042);
insert into sys_role_menu values (1, 3050);
insert into sys_role_menu values (1, 3100);
insert into sys_role_menu values (1, 3101);
insert into sys_role_menu values (1, 3102);
insert into sys_role_menu values (1, 3103);
insert into sys_role_menu values (1, 3104);
insert into sys_role_menu values (1, 3110);
insert into sys_role_menu values (1, 3111);
insert into sys_role_menu values (1, 3112);
insert into sys_role_menu values (1, 3113);
insert into sys_role_menu values (1, 3114);
insert into sys_role_menu values (1, 3115);
insert into sys_role_menu values (1, 3116);
insert into sys_role_menu values (1, 3120);
insert into sys_role_menu values (1, 3121);
insert into sys_role_menu values (1, 3122);
insert into sys_role_menu values (1, 3130);
insert into sys_role_menu values (1, 3131);
insert into sys_role_menu values (1, 3132);
insert into sys_role_menu values (1, 3140);
insert into sys_role_menu values (1, 3141);
insert into sys_role_menu values (1, 3142);
insert into sys_role_menu values (1, 3143);
insert into sys_role_menu values (1, 3144);
insert into sys_role_menu values (1, 3150);
insert into sys_role_menu values (1, 3151);
insert into sys_role_menu values (1, 3152);
insert into sys_role_menu values (1, 3153);
insert into sys_role_menu values (1, 3154);
insert into sys_role_menu values (1, 3155);
insert into sys_role_menu values (1, 3160);
insert into sys_role_menu values (1, 3161);
insert into sys_role_menu values (1, 3162);
insert into sys_role_menu values (1, 3163);
insert into sys_role_menu values (1, 3164);
insert into sys_role_menu values (1, 3165);
insert into sys_role_menu values (1, 3166);
insert into sys_role_menu values (2, 1);
insert into sys_role_menu values (2, 107);
insert into sys_role_menu values (2, 1035);
insert into sys_role_menu values (2, 1065);
insert into sys_role_menu values (2, 1066);
insert into sys_role_menu values (2, 1067);
insert into sys_role_menu values (2, 1068);
insert into sys_role_menu values (2, 1069);
insert into sys_role_menu values (2, 1070);
insert into sys_role_menu values (2, 1071);
insert into sys_role_menu values (2, 1072);
insert into sys_role_menu values (2, 1073);
insert into sys_role_menu values (2, 1074);
insert into sys_role_menu values (2, 1075);
insert into sys_role_menu values (2, 1076);
insert into sys_role_menu values (2, 2000);
insert into sys_role_menu values (2, 2001);
insert into sys_role_menu values (2, 2002);
insert into sys_role_menu values (2, 2003);
insert into sys_role_menu values (2, 2004);
insert into sys_role_menu values (2, 2006);
insert into sys_role_menu values (2, 3000);
insert into sys_role_menu values (2, 3002);
insert into sys_role_menu values (2, 3005);
insert into sys_role_menu values (2, 3006);
insert into sys_role_menu values (2, 3007);
insert into sys_role_menu values (2, 3010);
insert into sys_role_menu values (2, 3011);
insert into sys_role_menu values (2, 3012);
insert into sys_role_menu values (2, 3013);
insert into sys_role_menu values (2, 3014);
insert into sys_role_menu values (2, 3015);
insert into sys_role_menu values (2, 3016);
insert into sys_role_menu values (2, 3017);
insert into sys_role_menu values (2, 3018);
insert into sys_role_menu values (2, 3028);
insert into sys_role_menu values (2, 3029);
insert into sys_role_menu values (2, 3110);
insert into sys_role_menu values (2, 3111);
insert into sys_role_menu values (2, 3115);
insert into sys_role_menu values (2, 3116);
insert into sys_role_menu values (100, 1);
insert into sys_role_menu values (100, 107);
insert into sys_role_menu values (100, 1035);
insert into sys_role_menu values (100, 3000);
insert into sys_role_menu values (100, 3001);
insert into sys_role_menu values (100, 3002);
insert into sys_role_menu values (100, 3003);
insert into sys_role_menu values (100, 3004);
insert into sys_role_menu values (100, 3005);
insert into sys_role_menu values (100, 3006);
insert into sys_role_menu values (100, 3007);

-- 8、角色和部门关联表  角色1-N部门
-- ----------------------------
drop table if exists sys_role_dept;
create table sys_role_dept (
    role_id bigint not null,
    dept_id bigint not null,
    primary key (role_id, dept_id)
);
comment on column sys_role_dept.role_id is '角色ID';
comment on column sys_role_dept.dept_id is '部门ID';
comment on table sys_role_dept is '角色和部门关联表';

-- ----------------------------
-- 初始化-角色和部门关联表数据
-- ----------------------------
insert into sys_role_dept values (2, 100);
insert into sys_role_dept values (2, 101);
insert into sys_role_dept values (2, 105);

-- ----------------------------
-- 9、用户与岗位关联表  用户1-N岗位
-- ----------------------------
drop table if exists sys_user_post;
create table sys_user_post (
    user_id bigint not null,
    post_id bigint not null,
    primary key (user_id, post_id)
);
comment on column sys_user_post.user_id is '用户ID';
comment on column sys_user_post.post_id is '岗位ID';
comment on table sys_user_post is '用户与岗位关联表';

-- ----------------------------
-- 初始化-用户与岗位关联表数据
-- ----------------------------
insert into sys_user_post values (1, 1);
insert into sys_user_post values (2, 2);

-- ----------------------------
-- 10、操作日志记录
-- ----------------------------
drop table if exists sys_oper_log;
create table sys_oper_log (
    oper_id bigserial not null,
    title varchar(50) default '',
    business_type int4 default 0,
    method varchar(100) default '',
    request_method varchar(10) default '',
    operator_type int4 default 0,
    oper_name varchar(50) default '',
    dept_name varchar(50) default '',
    oper_url varchar(255) default '',
    oper_ip varchar(128) default '',
    oper_location varchar(255) default '',
    oper_param varchar(2000) default '',
    json_result varchar(2000) default '',
    status int4 default 0,
    error_msg varchar(2000) default '',
    oper_time timestamp(0),
    cost_time bigint default 0,
    primary key (oper_id)
);
alter sequence sys_oper_log_oper_id_seq restart 100;
create index idx_sys_oper_log_bt on sys_oper_log(business_type);  
create index idx_sys_oper_log_s on sys_oper_log(status);  
create index idx_sys_oper_log_ot on sys_oper_log(oper_time);
comment on column sys_oper_log.oper_id is '日志主键';
comment on column sys_oper_log.title is '模块标题';
comment on column sys_oper_log.business_type is '业务类型（0其它 1新增 2修改 3删除）';
comment on column sys_oper_log.method is '方法名称';
comment on column sys_oper_log.request_method is '请求方式';
comment on column sys_oper_log.operator_type is '操作类别（0其它 1后台用户 2手机端用户）';
comment on column sys_oper_log.oper_name is '操作人员';
comment on column sys_oper_log.dept_name is '部门名称';
comment on column sys_oper_log.oper_url is '请求URL';
comment on column sys_oper_log.oper_ip is '主机地址';
comment on column sys_oper_log.oper_location is '操作地点';
comment on column sys_oper_log.oper_param is '请求参数';
comment on column sys_oper_log.json_result is '返回参数';
comment on column sys_oper_log.status is '操作状态（0正常 1异常）';
comment on column sys_oper_log.error_msg is '错误消息';
comment on column sys_oper_log.oper_time is '操作时间';
comment on column sys_oper_log.cost_time is '消耗时间';
comment on table sys_oper_log is '操作日志记录';

-- ----------------------------
-- 11、字典类型表
-- ----------------------------
drop table if exists sys_dict_type;
create table sys_dict_type (
    dict_id bigserial not null,
    dict_name varchar(100) default '',
    dict_type varchar(100) unique default '',
    status char(1) default '0',
    create_by varchar(64) default '',
    create_time timestamp(0),
    update_by varchar(64) default '',
    update_time timestamp(0),
    remark varchar(500) default null,
    primary key (dict_id)
);
alter sequence sys_dict_type_dict_id_seq restart 100;
comment on column sys_dict_type.dict_id is '字典主键';
comment on column sys_dict_type.dict_name is '字典名称';
comment on column sys_dict_type.dict_type is '字典类型';
comment on column sys_dict_type.status is '状态（0正常 1停用）';
comment on column sys_dict_type.create_by is '创建者';
comment on column sys_dict_type.create_time is '创建时间';
comment on column sys_dict_type.update_by is '更新者';
comment on column sys_dict_type.update_time is '更新时间';
comment on column sys_dict_type.remark is '备注';
comment on table sys_dict_type is '字典类型表';

-- ----------------------------
-- 初始化-字典类型表数据
-- ----------------------------
insert into sys_dict_type values(1,  '用户性别',     'sys_user_sex',        '0', 'admin', current_timestamp, '', null, '用户性别列表');
insert into sys_dict_type values(2,  '菜单状态',     'sys_show_hide',       '0', 'admin', current_timestamp, '', null, '菜单状态列表');
insert into sys_dict_type values(3,  '系统开关',     'sys_normal_disable',  '0', 'admin', current_timestamp, '', null, '系统开关列表');
insert into sys_dict_type values(4,  '任务状态',     'sys_job_status',      '0', 'admin', current_timestamp, '', null, '任务状态列表');
insert into sys_dict_type values(5,  '任务分组',     'sys_job_group',       '0', 'admin', current_timestamp, '', null, '任务分组列表');
insert into sys_dict_type values(6,  '任务执行器',   'sys_job_executor',    '0', 'admin', current_timestamp, '', null, '任务执行器列表');
insert into sys_dict_type values(7,  '系统是否',     'sys_yes_no',          '0', 'admin', current_timestamp, '', null, '系统是否列表');
insert into sys_dict_type values(8,  '通知类型',     'sys_notice_type',     '0', 'admin', current_timestamp, '', null, '通知类型列表');
insert into sys_dict_type values(9,  '通知状态', 	 'sys_notice_status',   '0', 'admin', current_timestamp, '', null, '通知状态列表');
insert into sys_dict_type values(10,  '操作类型', 	 'sys_oper_type',       '0', 'admin', current_timestamp, '', null, '操作类型列表');
insert into sys_dict_type values(11, '系统状态',     'sys_common_status',   '0', 'admin', current_timestamp, '', null, '登录状态列表');
insert into sys_dict_type values(12, 'AI模型提供商', 'ai_provider_type',    '0', 'admin', current_timestamp, '', null, 'AI模型提供商列表');

-- ----------------------------
-- 12、字典数据表
-- ----------------------------
drop table if exists sys_dict_data;
create table sys_dict_data (
    dict_code bigserial not null,
    dict_sort int4 default 0,
    dict_label varchar(100) default '',
    dict_value varchar(100) default '',
    dict_type varchar(100) default '',
    css_class varchar(100) default null,
    list_class varchar(100) default null,
    is_default char(1) default 'N',
    status char(1) default '0',
    create_by varchar(64) default '',
    create_time timestamp(0),
    update_by varchar(64) default '',
    update_time timestamp(0),
    remark varchar(500) default null,
    primary key (dict_code)
);
alter sequence sys_dict_data_dict_code_seq restart 100;
comment on column sys_dict_data.dict_code is '字典编码';
comment on column sys_dict_data.dict_sort is '字典排序';
comment on column sys_dict_data.dict_label is '字典标签';
comment on column sys_dict_data.dict_value is '字典键值';
comment on column sys_dict_data.dict_type is '字典类型';
comment on column sys_dict_data.css_class is '样式属性（其他样式扩展）';
comment on column sys_dict_data.list_class is '表格回显样式';
comment on column sys_dict_data.is_default is '是否默认（Y是 N否）';
comment on column sys_dict_data.status is '状态（0正常 1停用）';
comment on column sys_dict_data.create_by is '创建者';
comment on column sys_dict_data.create_time is '创建时间';
comment on column sys_dict_data.update_by is '更新者';
comment on column sys_dict_data.update_time is '更新时间';
comment on column sys_dict_data.remark is '备注';
comment on table sys_dict_data is '字典数据表';

-- ----------------------------
-- 初始化-字典数据表数据
-- ----------------------------
insert into sys_dict_data values(1,  1,  '男',               '0',             'sys_user_sex',        '',   '',        'Y', '0', 'admin', current_timestamp, '', null, '性别男');
insert into sys_dict_data values(2,  2,  '女',               '1',             'sys_user_sex',        '',   '',        'N', '0', 'admin', current_timestamp, '', null, '性别女');
insert into sys_dict_data values(3,  3,  '未知',             '2',             'sys_user_sex',        '',   '',        'N', '0', 'admin', current_timestamp, '', null, '性别未知');
insert into sys_dict_data values(4,  1,  '显示',             '0',             'sys_show_hide',       '',   'primary', 'Y', '0', 'admin', current_timestamp, '', null, '显示菜单');
insert into sys_dict_data values(5,  2,  '隐藏',             '1',             'sys_show_hide',       '',   'danger',  'N', '0', 'admin', current_timestamp, '', null, '隐藏菜单');
insert into sys_dict_data values(6,  1,  '正常',             '0',             'sys_normal_disable',  '',   'primary', 'Y', '0', 'admin', current_timestamp, '', null, '正常状态');
insert into sys_dict_data values(7,  2,  '停用',             '1',             'sys_normal_disable',  '',   'danger',  'N', '0', 'admin', current_timestamp, '', null, '停用状态');
insert into sys_dict_data values(8,  1,  '正常',             '0',              'sys_job_status',      '',   'primary', 'Y', '0', 'admin', current_timestamp, '', null, '正常状态');
insert into sys_dict_data values(9,  2,  '暂停',             '1',              'sys_job_status',      '',   'danger',  'N', '0', 'admin', current_timestamp, '', null, '停用状态');
insert into sys_dict_data values(10, 1,  '默认',             'default',        'sys_job_group',       '',   '',        'Y', '0', 'admin', current_timestamp, '', null, '默认分组');
insert into sys_dict_data values(11, 2,  '数据库',           'sqlalchemy',      'sys_job_group',       '',   '',        'N', '0', 'admin', current_timestamp, '', null, '数据库分组');
insert into sys_dict_data values(12, 3,  'redis',           'redis',  			'sys_job_group',       '',   '',        'N', '0', 'admin', current_timestamp, '', null, 'reids分组');
insert into sys_dict_data values(13, 1,  '默认',             'default',  		'sys_job_executor',    '',   '',        'N', '0', 'admin', current_timestamp, '', null, '线程池');
insert into sys_dict_data values(14, 2,  '进程池',           'processpool',     'sys_job_executor',    '',   '',        'N', '0', 'admin', current_timestamp, '', null, '进程池');
insert into sys_dict_data values(15, 1,  '是',               'Y',       		'sys_yes_no',          '',   'primary', 'Y', '0', 'admin', current_timestamp, '', null, '系统默认是');
insert into sys_dict_data values(16, 2,  '否',               'N',       		'sys_yes_no',          '',   'danger',  'N', '0', 'admin', current_timestamp, '', null, '系统默认否');
insert into sys_dict_data values(17, 1,  '通知',             '1',       		'sys_notice_type',     '',   'warning', 'Y', '0', 'admin', current_timestamp, '', null, '通知');
insert into sys_dict_data values(18, 2,  '公告',             '2',       		'sys_notice_type',     '',   'success', 'N', '0', 'admin', current_timestamp, '', null, '公告');
insert into sys_dict_data values(19, 1,  '正常',             '0',       		'sys_notice_status',   '',   'primary', 'Y', '0', 'admin', current_timestamp, '', null, '正常状态');
insert into sys_dict_data values(20, 2,  '关闭',             '1',       		'sys_notice_status',   '',   'danger',  'N', '0', 'admin', current_timestamp, '', null, '关闭状态');
insert into sys_dict_data values(21, 99, '其他',             '0',       		'sys_oper_type',       '',   'info',    'N', '0', 'admin', current_timestamp, '', null, '其他操作');
insert into sys_dict_data values(22, 1,  '新增',             '1',       		'sys_oper_type',       '',   'info',    'N', '0', 'admin', current_timestamp, '', null, '新增操作');
insert into sys_dict_data values(23, 2,  '修改',             '2',       		'sys_oper_type',       '',   'info',    'N', '0', 'admin', current_timestamp, '', null, '修改操作');
insert into sys_dict_data values(24, 3,  '删除',             '3',       		'sys_oper_type',       '',   'danger',  'N', '0', 'admin', current_timestamp, '', null, '删除操作');
insert into sys_dict_data values(25, 4,  '授权',             '4',       		'sys_oper_type',       '',   'primary', 'N', '0', 'admin', current_timestamp, '', null, '授权操作');
insert into sys_dict_data values(26, 5,  '导出',             '5',       		'sys_oper_type',       '',   'warning', 'N', '0', 'admin', current_timestamp, '', null, '导出操作');
insert into sys_dict_data values(27, 6,  '导入',             '6',       		'sys_oper_type',       '',   'warning', 'N', '0', 'admin', current_timestamp, '', null, '导入操作');
insert into sys_dict_data values(28, 7,  '强退',             '7',       		'sys_oper_type',       '',   'danger',  'N', '0', 'admin', current_timestamp, '', null, '强退操作');
insert into sys_dict_data values(29, 8,  '生成代码',          '8',       		 'sys_oper_type',       '',   'warning', 'N', '0', 'admin', current_timestamp, '', null, '生成操作');
insert into sys_dict_data values(30, 9,  '清空数据',          '9',       		 'sys_oper_type',       '',   'danger',  'N', '0', 'admin', current_timestamp, '', null, '清空操作');
insert into sys_dict_data values(31, 1,  '成功',             '0',       		'sys_common_status',   '',   'primary', 'N', '0', 'admin', current_timestamp, '', null, '正常状态');
insert into sys_dict_data values(32, 2,  '失败',             '1',       		'sys_common_status',   '',   'danger',  'N', '0', 'admin', current_timestamp, '', null, '停用状态');
insert into sys_dict_data values(33, 1,  'AIMLAPI',         'AIMLAPI',          'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'AIMLAPI');
insert into sys_dict_data values(34, 2,  'Anthropic',       'Anthropic',        'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Anthropic');
insert into sys_dict_data values(35, 3,  'Cerebras',        'Cerebras',         'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Cerebras');
insert into sys_dict_data values(36, 4,  'CerebrasOpenAI',  'CerebrasOpenAI',   'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'CerebrasOpenAI');
insert into sys_dict_data values(37, 5,  'Cohere',          'Cohere',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Cohere');
insert into sys_dict_data values(38, 6,  'CometAPI',        'CometAPI',         'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'CometAPI');
insert into sys_dict_data values(39, 7,  'DashScope',       'DashScope',        'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'DashScope');
insert into sys_dict_data values(40, 8,  'DeepInfra',       'DeepInfra',        'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'DeepInfra');
insert into sys_dict_data values(41, 9,  'DeepSeek',        'DeepSeek',         'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'DeepSeek');
insert into sys_dict_data values(42, 10,  'Fireworks',       'Fireworks',        'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Fireworks');
insert into sys_dict_data values(43, 11,  'Google',          'Google',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Google');
insert into sys_dict_data values(44, 12,  'Groq',            'Groq',             'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Groq');
insert into sys_dict_data values(45, 13,  'HuggingFace',     'HuggingFace',      'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'HuggingFace');
insert into sys_dict_data values(46, 14,  'LangDB',          'LangDB',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'LangDB');
insert into sys_dict_data values(47, 15,  'LiteLLM',         'LiteLLM',          'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'LiteLLM');
insert into sys_dict_data values(48, 16,  'LiteLLMOpenAI',   'LiteLLMOpenAI',    'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'LiteLLMOpenAI');
insert into sys_dict_data values(49, 17,  'LlamaCpp',        'LlamaCpp',         'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'LlamaCpp');
insert into sys_dict_data values(50, 18,  'LMStudio',        'LMStudio',         'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'LMStudio');
insert into sys_dict_data values(51, 19,  'Meta',            'Meta',             'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Meta');
insert into sys_dict_data values(52, 20,  'Mistral',         'Mistral',          'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Mistral');
insert into sys_dict_data values(53, 21,  'N1N',             'N1N',              'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'N1N');
insert into sys_dict_data values(54, 22,  'Nebius',          'Nebius',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Nebius');
insert into sys_dict_data values(55, 23,  'Nexus',           'Nexus',            'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Nexus');
insert into sys_dict_data values(56, 24,  'Nvidia',          'Nvidia',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Nvidia');
insert into sys_dict_data values(57, 25,  'Ollama',          'Ollama',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Ollama');
insert into sys_dict_data values(58, 26,  'OpenAI',          'OpenAI',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'OpenAI');
insert into sys_dict_data values(59, 27,  'OpenAIResponses', 'OpenAIResponses',  'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'OpenAIResponses');
insert into sys_dict_data values(60, 28,  'OpenRouter',      'OpenRouter',       'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'OpenRouter');
insert into sys_dict_data values(61, 29,  'Perplexity',      'Perplexity',       'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Perplexity');
insert into sys_dict_data values(62, 30,  'Portkey',         'Portkey',          'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Portkey');
insert into sys_dict_data values(63, 31,  'Requesty',        'Requesty',         'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Requesty');
insert into sys_dict_data values(64, 32,  'Sambanova',       'Sambanova',        'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Sambanova');
insert into sys_dict_data values(65, 33,  'SiliconFlow',     'SiliconFlow',      'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'SiliconFlow');
insert into sys_dict_data values(66, 34,  'Together',        'Together',         'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Together');
insert into sys_dict_data values(67, 35,  'Vercel',          'Vercel',           'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'Vercel');
insert into sys_dict_data values(68, 36,  'VLLM',            'VLLM',             'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'VLLM');
insert into sys_dict_data values(69, 37,  'xAI',             'xAI',              'ai_provider_type',    '',   'info',    'N', '0', 'admin', current_timestamp, '', null, 'xAI');

-- ----------------------------
-- 13、参数配置表
-- ----------------------------
drop table if exists sys_config;
create table sys_config (
    config_id serial not null,
    config_name varchar(100) default '',
    config_key varchar(100) default '',
    config_value varchar(500) default '',
    config_type char(1) default 'N',
    create_by varchar(64) default '',
    create_time timestamp(0),
    update_by varchar(64) default '',
    update_time timestamp(0),
    remark varchar(500) default null,
    primary key (config_id)
);
alter sequence sys_config_config_id_seq restart 100;
comment on column sys_config.config_id is '参数主键';
comment on column sys_config.config_name is '参数名称';
comment on column sys_config.config_key is '参数键名';
comment on column sys_config.config_value is '参数键值';
comment on column sys_config.config_type is '系统内置（Y是 N否）';
comment on column sys_config.create_by is '创建者';
comment on column sys_config.create_time is '创建时间';
comment on column sys_config.update_by is '更新者';
comment on column sys_config.update_time is '更新时间';
comment on column sys_config.remark is '备注';
comment on table sys_config is '参数配置表';

-- ----------------------------
-- 初始化-参数配置表数据
-- ----------------------------
insert into sys_config values(1, '主框架页-默认皮肤样式名称',     'sys.index.skinName',            'skin-blue',     'Y', 'admin', current_timestamp, '', null, '蓝色 skin-blue、绿色 skin-green、紫色 skin-purple、红色 skin-red、黄色 skin-yellow' );
insert into sys_config values(2, '用户管理-账号初始密码',         'sys.user.initPassword',         '123456',        'Y', 'admin', current_timestamp, '', null, '初始化密码 123456' );
insert into sys_config values(3, '主框架页-侧边栏主题',           'sys.index.sideTheme',           'theme-dark',    'Y', 'admin', current_timestamp, '', null, '深色主题theme-dark，浅色主题theme-light' );
insert into sys_config values(4, '账号自助-验证码开关',           'sys.account.captchaEnabled',    'false',         'Y', 'admin', current_timestamp, '', null, '是否开启验证码功能（true开启，false关闭）');
insert into sys_config values(5, '账号自助-是否开启用户注册功能', 'sys.account.registerUser',      'false',         'Y', 'admin', current_timestamp, '', null, '是否开启注册用户功能（true开启，false关闭）');
insert into sys_config values(6, '用户登录-黑名单列表',           'sys.login.blackIPList',         '',              'Y', 'admin', current_timestamp, '', null, '设置登录IP黑名单限制，多个匹配项以;分隔，支持匹配（*通配、网段）');
insert into sys_config values(7, '用户管理-初始密码修改策略',     'sys.account.initPasswordModify',  '1',             'Y', 'admin', current_timestamp, '', null, '0：初始密码修改策略关闭，没有任何提示，1：提醒用户，如果未修改初始密码，则在登录时就会提醒修改密码对话框');
insert into sys_config values(8, '用户管理-账号密码更新周期',     'sys.account.passwordValidateDays', '0',             'Y', 'admin', current_timestamp, '', null, '密码更新周期（填写数字，数据初始化值为0不限制，若修改必须为大于0小于365的正整数），如果超过这个周期登录系统时，则在登录时就会提醒修改密码对话框');

-- ----------------------------
-- 14、系统访问记录
-- ----------------------------
drop table if exists sys_logininfor;
create table sys_logininfor (
    info_id bigserial not null,
    user_name varchar(50) default '',
    ipaddr varchar(128) default '',
    login_location varchar(255) default '',
    browser varchar(50) default '',
    os varchar(50) default '',
    status char(1) default '0',
    msg varchar(255) default '',
    login_time timestamp(0),
    primary key (info_id)
);
alter sequence sys_logininfor_info_id_seq restart 100;
create index idx_sys_logininfor_s on sys_logininfor(status);  
create index idx_sys_logininfor_lt on sys_logininfor(login_time);
comment on column sys_logininfor.info_id is '访问ID';
comment on column sys_logininfor.user_name is '用户账号';
comment on column sys_logininfor.ipaddr is '登录IP地址';
comment on column sys_logininfor.login_location is '登录地点';
comment on column sys_logininfor.browser is '浏览器类型';
comment on column sys_logininfor.os is '操作系统';
comment on column sys_logininfor.status is '登录状态（0成功 1失败）';
comment on column sys_logininfor.msg is '提示消息';
comment on column sys_logininfor.login_time is '访问时间';
comment on table sys_logininfor is '系统访问记录';

-- ----------------------------
-- 15、定时任务调度表
-- ----------------------------
drop table if exists sys_job;
create table sys_job (
    job_id bigserial not null,
    job_name varchar(64) default '',
    job_group varchar(64) default 'default',
    job_executor varchar(64) default 'default',
    invoke_target varchar(500) not null,
    job_args varchar(255) default '',
    job_kwargs varchar(255) default '',
    cron_expression varchar(255) default '',
    misfire_policy varchar(20) default '3',
    concurrent char(1) default '1',
    status char(1) default '0',
    create_by varchar(64) default '',
    create_time timestamp(0),
    update_by varchar(64) default '',
    update_time timestamp(0),
    remark varchar(500) default '',
    primary key (job_id, job_name, job_group)
);
alter sequence sys_job_job_id_seq restart 100;
comment on column sys_job.job_id is '任务ID';
comment on column sys_job.job_name is '任务名称';
comment on column sys_job.job_group is '任务组名';
comment on column sys_job.job_executor is '任务执行器';
comment on column sys_job.invoke_target is '调用目标字符串';
comment on column sys_job.job_args is '位置参数';
comment on column sys_job.job_kwargs is '关键字参数';
comment on column sys_job.cron_expression is 'cron执行表达式';
comment on column sys_job.misfire_policy is '计划执行错误策略（1立即执行 2执行一次 3放弃执行）';
comment on column sys_job.concurrent is '是否并发执行（0允许 1禁止）';
comment on column sys_job.status is '状态（0正常 1暂停）';
comment on column sys_job.create_by is '创建者';
comment on column sys_job.create_time is '创建时间';
comment on column sys_job.update_by is '更新者';
comment on column sys_job.update_time is '更新时间';
comment on column sys_job.remark is '备注信息';
comment on table sys_job is '定时任务调度表';

-- ----------------------------
-- 初始化-定时任务调度表数据
-- ----------------------------
insert into sys_job values(1, '系统默认（无参）', 'default', 'default', 'module_task.scheduler_test.job', null,   null, '0/10 * * * * ?', '3', '1', '1', 'admin', current_timestamp, '', null, '');
insert into sys_job values(2, '系统默认（有参）', 'default', 'default', 'module_task.scheduler_test.job', 'test', null, '0/15 * * * * ?', '3', '1', '1', 'admin', current_timestamp, '', null, '');
insert into sys_job values(3, '系统默认（多参）', 'default', 'default', 'module_task.scheduler_test.job', 'new',  '{test: 111}', '0/20 * * * * ?', '3', '1', '1', 'admin', current_timestamp, '', null, '');
insert into sys_job values(4, 'VIP到期自动清理', 'default', 'default', 'module_task.user_vip.expire_user_vip', null, null, '0 0 * * * ?', '3', '1', '0', 'admin', current_timestamp, '', null, '每小时清理已过期VIP授权');

-- ----------------------------
-- 16、定时任务调度日志表
-- ----------------------------
drop table if exists sys_job_log;
create table sys_job_log (
    job_log_id bigserial not null,
    job_name varchar(64) not null,
    job_group varchar(64) not null,
    job_executor varchar(64) not null,
    invoke_target varchar(500) not null,
    job_args varchar(255) default '',
    job_kwargs varchar(255) default '',
    job_trigger varchar(255) default '',
    job_message varchar(500),
    status char(1) default '0',
    exception_info varchar(2000) default '',
    create_time timestamp(0),
    primary key (job_log_id)
);
comment on column sys_job_log.job_log_id is '任务日志ID';
comment on column sys_job_log.job_name is '任务名称';
comment on column sys_job_log.job_group is '任务组名';
comment on column sys_job_log.job_executor is '任务执行器';
comment on column sys_job_log.invoke_target is '调用目标字符串';
comment on column sys_job_log.job_args is '位置参数';
comment on column sys_job_log.job_kwargs is '关键字参数';
comment on column sys_job_log.job_trigger is '任务触发器';
comment on column sys_job_log.job_message is '日志信息';
comment on column sys_job_log.status is '执行状态（0正常 1失败）';
comment on column sys_job_log.exception_info is '异常信息';
comment on column sys_job_log.create_time is '创建时间';
comment on table sys_job_log is '定时任务调度日志表';

-- ----------------------------
-- 17、通知公告表
-- ----------------------------
drop table if exists sys_notice;
create table sys_notice (
    notice_id serial not null,
    notice_title varchar(50) not null,
    notice_type char(1) not null,
    notice_content bytea default null,
    status char(1) default '0',
    create_by varchar(64) default '',
    create_time timestamp(0),
    update_by varchar(64) default '',
    update_time timestamp(0),
    remark varchar(255) default null,
    primary key (notice_id)
);
alter sequence sys_notice_notice_id_seq restart 10;
comment on column sys_notice.notice_id is '公告ID';
comment on column sys_notice.notice_title is '公告标题';
comment on column sys_notice.notice_type is '公告类型（1通知 2公告）';
comment on column sys_notice.notice_content is '公告内容';
comment on column sys_notice.status is '公告状态（0正常 1关闭）';
comment on column sys_notice.create_by is '创建者';
comment on column sys_notice.create_time is '创建时间';
comment on column sys_notice.update_by is '更新者';
comment on column sys_notice.update_time is '更新时间';
comment on column sys_notice.remark is '备注';
comment on table sys_notice is '通知公告表';

-- ----------------------------
-- 初始化-公告信息表数据
-- ----------------------------
insert into sys_notice values(1, '温馨提醒：2018-07-01 vfadmin新版本发布啦', '2', '新版本内容', '0', 'admin', current_timestamp, '', null, '管理员');
insert into sys_notice values(2, '维护通知：2018-07-01 vfadmin系统凌晨维护', '1', '维护内容',   '0', 'admin', current_timestamp, '', null, '管理员');

-- ----------------------------
-- 18、代码生成业务表
-- ----------------------------
drop table if exists gen_table;
create table gen_table (
    table_id bigserial not null,
    table_name varchar(200) default '',
    table_comment varchar(500) default '',
    sub_table_name varchar(64) default null,
    sub_table_fk_name varchar(64) default null,
    class_name varchar(100) default '',
    tpl_category varchar(200) default 'crud',
    tpl_web_type varchar(30)  default '',
    package_name varchar(100),
    module_name varchar(30),
    business_name varchar(30),
    function_name varchar(50),
    function_author varchar(50),
    gen_type char(1) default '0',
    gen_path varchar(200) default '/',
    options varchar(1000),
    create_by varchar(64) default '',
    create_time timestamp(0),
    update_by varchar(64) default '',
    update_time timestamp(0),
    remark varchar(500) default null,
    primary key (table_id)
);
comment on column gen_table.table_id is '编号';
comment on column gen_table.table_name is '表名称';
comment on column gen_table.table_comment is '表描述';
comment on column gen_table.sub_table_name is '关联子表的表名';
comment on column gen_table.sub_table_fk_name is '子表关联的外键名';
comment on column gen_table.class_name is '实体类名称';
comment on column gen_table.tpl_category is '使用的模板（crud单表操作 tree树表操作）';
comment on column gen_table.tpl_web_type is '前端模板类型（element-ui模版 element-plus模版）';
comment on column gen_table.package_name is '生成包路径';
comment on column gen_table.module_name is '生成模块名';
comment on column gen_table.business_name is '生成业务名';
comment on column gen_table.function_name is '生成功能名';
comment on column gen_table.function_author is '生成功能作者';
comment on column gen_table.gen_type is '生成代码方式（0zip压缩包 1自定义路径）';
comment on column gen_table.gen_path is '生成路径（不填默认项目路径）';
comment on column gen_table.options is '其它生成选项';
comment on column gen_table.create_by is '创建者';
comment on column gen_table.create_time is '创建时间';
comment on column gen_table.update_by is '更新者';
comment on column gen_table.update_time is '更新时间';
comment on column gen_table.remark is '备注';
comment on table gen_table is '代码生成业务表';

-- ----------------------------
-- 19、代码生成业务表字段
-- ----------------------------
drop table if exists gen_table_column;
create table gen_table_column (
    column_id bigserial not null,
    table_id bigint,
    column_name varchar(200),
    column_comment varchar(500),
    column_type varchar(100),
    python_type varchar(500),
    python_field varchar(200),
    is_pk char(1),
    is_increment char(1),
    is_required char(1),
    is_unique char(1),
    is_insert char(1),
    is_edit char(1),
    is_list char(1),
    is_query char(1),
    query_type varchar(200) default 'EQ',
    html_type varchar(200),
    dict_type varchar(200) default '',
    sort int4,
    create_by varchar(64) default '',
    create_time timestamp(0),
    update_by varchar(64) default '',
    update_time timestamp(0),
    primary key (column_id)
);
comment on column gen_table_column.column_id is '编号';
comment on column gen_table_column.table_id is '归属表编号';
comment on column gen_table_column.column_name is '列名称';
comment on column gen_table_column.column_comment is '列描述';
comment on column gen_table_column.column_type is '列类型';
comment on column gen_table_column.python_type is 'PYTHON类型';
comment on column gen_table_column.python_field is 'PYTHON字段名';
comment on column gen_table_column.is_pk is '是否主键（1是）';
comment on column gen_table_column.is_increment is '是否自增（1是）';
comment on column gen_table_column.is_required is '是否必填（1是）';
comment on column gen_table_column.is_unique is '是否唯一（1是）';
comment on column gen_table_column.is_insert is '是否为插入字段（1是）';
comment on column gen_table_column.is_edit is '是否编辑字段（1是）';
comment on column gen_table_column.is_list is '是否列表字段（1是）';
comment on column gen_table_column.is_query is '是否查询字段（1是）';
comment on column gen_table_column.query_type is '查询方式（等于、不等于、大于、小于、范围）';
comment on column gen_table_column.html_type is '显示类型（文本框、文本域、下拉框、复选框、单选框、日期控件）';
comment on column gen_table_column.dict_type is '字典类型';
comment on column gen_table_column.sort is '排序';
comment on column gen_table_column.create_by is '创建者';
comment on column gen_table_column.create_time is '创建时间';
comment on column gen_table_column.update_by is '更新者';
comment on column gen_table_column.update_time is '更新时间';
comment on table gen_table_column is '代码生成业务表字段';

-- ----------------------------
-- 20、AI模型表
-- ----------------------------
drop table if exists ai_models;
create table ai_models (
  model_id          bigserial       not null,
  model_code        varchar(100)    not null,
  model_name        varchar(100)    default null,
  provider          varchar(50)     not null,
  model_sort        int4            not null,
  api_key           varchar(255)    default null,
  base_url          varchar(255)    default null,
  model_type        varchar(50)     default null,
  max_tokens        integer         default null,
  temperature       float           default null,
  support_reasoning char(1)         default 'N',
  support_images    char(1)         default 'N',
  status            char(1)         default '0',
  user_id           bigint,
  dept_id           bigint,
  create_by         varchar(64)     default '',
  create_time       timestamp(0),
  update_by         varchar(64)     default '',
  update_time       timestamp(0),
  remark            varchar(500)    default null,
  primary key (model_id)
);
comment on table ai_models is 'AI模型表';
comment on column ai_models.model_id is '模型主键';
comment on column ai_models.model_code is '模型编码';
comment on column ai_models.model_name is '模型名称';
comment on column ai_models.provider is '提供商';
comment on column ai_models.model_sort is '显示顺序';
comment on column ai_models.api_key is 'API Key';
comment on column ai_models.base_url is 'Base URL';
comment on column ai_models.model_type is '模型类型';
comment on column ai_models.max_tokens is '最大输出token';
comment on column ai_models.temperature is '默认温度';
comment on column ai_models.support_reasoning is '是否支持推理';
comment on column ai_models.support_images is '是否支持图片';
comment on column ai_models.status is '模型状态';
comment on column ai_models.user_id is '用户ID';
comment on column ai_models.dept_id is '部门ID';
comment on column ai_models.create_by is '创建者';
comment on column ai_models.create_time is '创建时间';
comment on column ai_models.update_by is '更新者';
comment on column ai_models.update_time is '更新时间';
comment on column ai_models.remark is '备注';
