import io
from datetime import datetime
from typing import Any

import pandas as pd
from fastapi import Request, UploadFile
from sqlalchemy import ColumnElement, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.enums import RedisInitKeyConfig
from common.vo import CrudResponseModel, PageModel
from config.get_scheduler import SchedulerUtil
from exceptions.exception import ServiceException
from module_admin.dao.config_dao import ConfigDao
from module_admin.dao.job_dao import JobDao
from module_admin.dao.user_dao import UserDao
from module_admin.entity.do.user_do import SysUser, SysUserRole
from module_admin.entity.vo.config_vo import ConfigModel
from module_admin.entity.vo.job_vo import JobModel
from module_admin.entity.vo.user_vo import (
    AddUserModel,
    CrudUserRoleModel,
    CurrentUserModel,
    DeleteUserModel,
    EditUserModel,
    RegisterCleanupRuleModel,
    ResetUserModel,
    SelectedRoleModel,
    UserDetailModel,
    UserInfoModel,
    UserModel,
    UserPageQueryModel,
    UserProfileModel,
    UserRoleModel,
    UserRoleQueryModel,
    UserRoleResponseModel,
    UserRowModel,
)
from module_admin.service.config_service import ConfigService
from module_admin.service.dept_service import DeptService
from module_admin.service.role_service import RoleService
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.pwd_util import PwdUtil


class UserService:
    """
    用户管理模块服务层
    """

    REGISTER_CLEANUP_CONFIG_KEY = 'sys.account.cleanupInactiveRegisteredUsers'
    REGISTER_CLEANUP_JOB_NAME = '注册用户24小时未登录自动清理'
    REGISTER_CLEANUP_JOB_TARGET = 'module_task.user_cleanup.cleanup_inactive_registered_users'
    REGISTER_CLEANUP_CRON = '0 0 * * * ?'

    @classmethod
    async def get_user_list_services(
        cls,
        query_db: AsyncSession,
        query_object: UserPageQueryModel,
        data_scope_sql: ColumnElement,
        is_page: bool = False,
    ) -> PageModel[UserRowModel] | list[dict[str, Any]]:
        """
        获取用户列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 用户列表信息对象
        """
        query_result = await UserDao.get_user_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            user_rows = [{**row, 'dept': None} for row in query_result.rows]
            await cls._attach_roles_to_user_rows(query_db, user_rows)
            cls._decorate_user_rows(user_rows)
            user_list_result = PageModel[UserRowModel](
                **{
                    **query_result.model_dump(by_alias=True),
                    'rows': user_rows,
                }
            )
        else:
            user_list_result = []
            if query_result:
                user_list_result = [{**row, 'dept': None} for row in query_result]
                await cls._attach_roles_to_user_rows(query_db, user_list_result)
                cls._decorate_user_rows(user_list_result)

        return user_list_result

    @classmethod
    async def _attach_roles_to_user_rows(cls, query_db: AsyncSession, rows: list[dict[str, Any]]) -> None:
        user_ids = [row.get('userId') for row in rows if row.get('userId')]
        role_map = await UserDao.get_roles_by_user_ids(query_db, user_ids)
        for row in rows:
            row['role'] = CamelCaseUtil.transform_result(role_map.get(row.get('userId'), []))

    @staticmethod
    def is_admin_role(current_user: CurrentUserModel) -> bool:
        """
        判断当前用户是否拥有admin角色。
        """
        return 'admin' in (current_user.roles or [])

    @staticmethod
    def is_effective_vip(user: Any) -> bool:
        """
        判断用户VIP授权是否仍然有效。
        """
        expire_time = getattr(user, 'vip_expire_time', None)
        return getattr(user, 'is_vip', '0') == '1' and expire_time is not None and expire_time > datetime.now()

    @staticmethod
    def decorate_user_model(
        user: UserInfoModel | UserModel, roles: list[str] | None = None
    ) -> UserInfoModel | UserModel:
        """
        补充前端展示用的有效VIP和有效内功额度字段。
        """
        is_admin = bool(getattr(user, 'admin', False)) or 'admin' in (roles or [])
        is_effective_vip = UserService.is_effective_vip(user)
        user.is_vip_effective = is_effective_vip
        user.effective_internal_power_limit = None if is_admin or is_effective_vip else max(
            20, int(getattr(user, 'max_internal_power_count', 20) or 20)
        )
        return user

    @classmethod
    def _decorate_user_rows(cls, rows: list[dict[str, Any]]) -> None:
        for row in rows:
            role_keys = [role.get('roleKey') for role in row.get('role', []) if isinstance(role, dict)]
            is_admin = row.get('admin') or 'admin' in role_keys
            expire_time = row.get('vipExpireTime')
            is_effective_vip = row.get('isVip') == '1' and isinstance(expire_time, datetime) and expire_time > datetime.now()
            row['isVipEffective'] = bool(is_effective_vip)
            row['effectiveInternalPowerLimit'] = None if is_admin or is_effective_vip else max(
                20, int(row.get('maxInternalPowerCount') or 20)
            )

    @classmethod
    async def get_register_cleanup_rule_services(
        cls, request: Request, query_db: AsyncSession
    ) -> RegisterCleanupRuleModel:
        """
        Get the self-registered inactive user cleanup rule.
        """
        config, job = await cls.__ensure_register_cleanup_rule(query_db)
        enabled = config.config_value == 'true'
        config_value = config.config_value
        job_id = job.job_id if job else None
        await query_db.commit()
        await request.app.state.redis.set(
            f'{RedisInitKeyConfig.SYS_CONFIG.key}:{cls.REGISTER_CLEANUP_CONFIG_KEY}', config_value
        )
        return RegisterCleanupRuleModel(enabled=enabled, jobId=job_id)

    @classmethod
    async def set_register_cleanup_rule_services(
        cls, request: Request, query_db: AsyncSession, rule: RegisterCleanupRuleModel, update_by: str
    ) -> RegisterCleanupRuleModel:
        """
        Enable or disable the self-registered inactive user cleanup rule.
        """
        config, job = await cls.__ensure_register_cleanup_rule(query_db)
        enabled_value = 'true' if rule.enabled else 'false'
        job_status = '0' if rule.enabled else '1'
        job_id = job.job_id if job else None
        now = datetime.now()

        await ConfigDao.edit_config_dao(
            query_db,
            {
                'config_id': config.config_id,
                'config_name': config.config_name,
                'config_key': config.config_key,
                'config_value': enabled_value,
                'config_type': config.config_type,
                'update_by': update_by,
                'update_time': now,
            },
        )
        if job:
            await JobDao.edit_job_dao(
                query_db,
                {
                    'job_id': job.job_id,
                    'status': job_status,
                    'update_by': update_by,
                    'update_time': now,
                },
                JobModel(**CamelCaseUtil.transform_result(job)),
            )
        await query_db.commit()
        await request.app.state.redis.set(
            f'{RedisInitKeyConfig.SYS_CONFIG.key}:{cls.REGISTER_CLEANUP_CONFIG_KEY}', enabled_value
        )
        await SchedulerUtil.request_scheduler_sync()
        return RegisterCleanupRuleModel(enabled=rule.enabled, jobId=job_id)

    @classmethod
    async def __ensure_register_cleanup_rule(cls, query_db: AsyncSession) -> tuple[Any, Any]:
        config = await ConfigDao.get_config_detail_by_info(
            query_db, ConfigModel(configKey=cls.REGISTER_CLEANUP_CONFIG_KEY)
        )
        if config is None:
            config = await ConfigDao.add_config_dao(
                query_db,
                ConfigModel(
                    configName='账号自助-是否清理24小时未登录注册用户',
                    configKey=cls.REGISTER_CLEANUP_CONFIG_KEY,
                    configValue='false',
                    configType='Y',
                    createBy='system',
                    createTime=datetime.now(),
                    updateBy='system',
                    updateTime=datetime.now(),
                    remark='开启后，定时任务会软删除注册后24小时仍未登录的自助注册账号',
                ),
            )

        job = await JobDao.get_job_detail_by_invoke_target(query_db, cls.REGISTER_CLEANUP_JOB_TARGET)
        if job is None:
            job = await JobDao.add_job_dao(
                query_db,
                JobModel(
                    jobName=cls.REGISTER_CLEANUP_JOB_NAME,
                    jobGroup='default',
                    jobExecutor='default',
                    invokeTarget=cls.REGISTER_CLEANUP_JOB_TARGET,
                    cronExpression=cls.REGISTER_CLEANUP_CRON,
                    misfirePolicy='3',
                    concurrent='1',
                    status='1',
                    createBy='system',
                    createTime=datetime.now(),
                    updateBy='system',
                    updateTime=datetime.now(),
                    remark='清理注册后24小时仍未登录的自助注册账号',
                ),
            )
        return config, job

    @classmethod
    async def check_user_allowed_services(cls, check_user: UserModel) -> CrudResponseModel:
        """
        校验用户是否允许操作service

        :param check_user: 用户信息
        :return: 校验结果
        """
        if check_user.admin:
            raise ServiceException(message='不允许操作超级管理员用户')
        return CrudResponseModel(is_success=True, message='校验通过')

    @classmethod
    async def check_user_data_scope_services(
        cls, query_db: AsyncSession, user_id: int, data_scope_sql: ColumnElement
    ) -> CrudResponseModel:
        """
        校验用户数据权限service

        :param query_db: orm对象
        :param user_id: 用户id
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 校验结果
        """
        users = await UserDao.get_user_list(query_db, UserPageQueryModel(userId=user_id), data_scope_sql, is_page=False)
        if users:
            return CrudResponseModel(is_success=True, message='校验通过')
        raise ServiceException(message='没有权限访问用户数据')

    @classmethod
    async def check_user_name_unique_services(cls, query_db: AsyncSession, page_object: UserModel) -> bool:
        """
        校验用户名是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        user_id = -1 if page_object.user_id is None else page_object.user_id
        user = await UserDao.get_user_by_info(query_db, UserModel(userName=page_object.user_name))
        if user and user.user_id != user_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def check_phonenumber_unique_services(cls, query_db: AsyncSession, page_object: UserModel) -> bool:
        """
        校验用户手机号是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        user_id = -1 if page_object.user_id is None else page_object.user_id
        user = await UserDao.get_user_by_info(query_db, UserModel(phonenumber=page_object.phonenumber))
        if user and user.user_id != user_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def check_email_unique_services(cls, query_db: AsyncSession, page_object: UserModel) -> bool:
        """
        校验用户邮箱是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        user_id = -1 if page_object.user_id is None else page_object.user_id
        user = await UserDao.get_user_by_info(query_db, UserModel(email=page_object.email))
        if user and user.user_id != user_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_user_services(cls, query_db: AsyncSession, page_object: AddUserModel) -> CrudResponseModel:
        """
        新增用户信息service

        :param query_db: orm对象
        :param page_object: 新增用户对象
        :return: 新增用户校验结果
        """
        add_user = UserModel(**page_object.model_dump(by_alias=True))
        if not await cls.check_user_name_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增用户{page_object.user_name}失败，登录账号已存在')
        if page_object.phonenumber and not await cls.check_phonenumber_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增用户{page_object.user_name}失败，手机号码已存在')
        if page_object.email and not await cls.check_email_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增用户{page_object.user_name}失败，邮箱账号已存在')
        try:
            add_result = await UserDao.add_user_dao(query_db, add_user)
            user_id = add_result.user_id
            if page_object.role_ids:
                for role in page_object.role_ids:
                    await UserDao.add_user_role_dao(query_db, UserRoleModel(userId=user_id, roleId=role))
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    def _deal_edit_user(cls, page_object: EditUserModel, edit_user: dict[str, Any]) -> None:
        """
        处理编辑用户字典

        :param page_object: 编辑用户对象
        :param edit_user: 编辑用户字典
        :return: None
        """
        if page_object.type not in ['status', 'avatar', 'pwd', 'vip', 'limit', 'aiRecognition']:
            edit_user.pop('role_ids', None)
            edit_user.pop('role', None)
        else:
            edit_user.pop('type', None)

    @classmethod
    async def edit_user_services(cls, query_db: AsyncSession, page_object: EditUserModel) -> CrudResponseModel:
        """
        编辑用户信息service

        :param query_db: orm对象
        :param page_object: 编辑用户对象
        :return: 编辑用户校验结果
        """
        edit_user = page_object.model_dump(exclude_unset=True, exclude={'admin'})
        cls._deal_edit_user(page_object, edit_user)
        user_info = await cls.user_detail_services(query_db, edit_user.get('user_id'))
        if user_info.data and user_info.data.user_id:
            if page_object.type not in ['status', 'avatar', 'pwd', 'vip', 'limit', 'aiRecognition']:
                if not await cls.check_user_name_unique_services(query_db, page_object):
                    raise ServiceException(message=f'修改用户{page_object.user_name}失败，登录账号已存在')
                if page_object.phonenumber and not await cls.check_phonenumber_unique_services(query_db, page_object):
                    raise ServiceException(message=f'修改用户{page_object.user_name}失败，手机号码已存在')
                if page_object.email and not await cls.check_email_unique_services(query_db, page_object):
                    raise ServiceException(message=f'修改用户{page_object.user_name}失败，邮箱账号已存在')
            try:
                await UserDao.edit_user_dao(query_db, edit_user)
                if page_object.type not in {'status', 'avatar', 'pwd', 'vip', 'limit', 'aiRecognition'}:
                    await UserDao.delete_user_role_dao(query_db, UserRoleModel(userId=page_object.user_id))
                    if page_object.role_ids:
                        for role in page_object.role_ids:
                            await UserDao.add_user_role_dao(
                                query_db, UserRoleModel(userId=page_object.user_id, roleId=role)
                            )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='用户不存在')

    @classmethod
    async def delete_user_services(cls, query_db: AsyncSession, page_object: DeleteUserModel) -> CrudResponseModel:
        """
        删除用户信息service

        :param query_db: orm对象
        :param page_object: 删除用户对象
        :return: 删除用户校验结果
        """
        if page_object.user_ids:
            user_id_list = page_object.user_ids.split(',')
            try:
                for user_id in user_id_list:
                    user_id_dict = {
                        'userId': user_id,
                        'updateBy': page_object.update_by,
                        'updateTime': page_object.update_time,
                    }
                    await UserDao.delete_user_role_dao(query_db, UserRoleModel(**user_id_dict))
                    await UserDao.delete_user_dao(query_db, UserModel(**user_id_dict))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入用户id为空')

    @classmethod
    async def user_detail_services(cls, query_db: AsyncSession, user_id: int | str) -> UserDetailModel:
        """
        获取用户详细信息service

        :param query_db: orm对象
        :param user_id: 用户id
        :return: 用户id对应的信息
        """
        roles = await RoleService.get_role_select_option_services(query_db)
        if user_id != '':
            query_user = await UserDao.get_user_detail_by_id(query_db, user_id=user_id)
            role_ids = ','.join([str(row.role_id) for row in query_user.get('user_role_info')])
            role_ids_list = [row.role_id for row in query_user.get('user_role_info')]

            data = UserInfoModel(
                **CamelCaseUtil.transform_result(query_user.get('user_basic_info')),
                postIds='',
                roleIds=role_ids,
                dept=CamelCaseUtil.transform_result(query_user.get('user_dept_info')),
                role=CamelCaseUtil.transform_result(query_user.get('user_role_info')),
            )
            cls.decorate_user_model(data, [row.role_key for row in query_user.get('user_role_info')])
            return UserDetailModel(
                data=data,
                postIds=[],
                roleIds=role_ids_list,
                roles=roles,
            )

        return UserDetailModel(postIds=[], roles=roles)

    @classmethod
    async def user_profile_services(cls, query_db: AsyncSession, user_id: int) -> UserProfileModel:
        """
        获取用户个人详细信息service

        :param query_db: orm对象
        :param user_id: 用户id
        :return: 用户id对应的信息
        """
        query_user = await UserDao.get_user_detail_by_id(query_db, user_id=user_id)
        role_ids = ','.join([str(row.role_id) for row in query_user.get('user_role_info')])
        role_group = ','.join([row.role_name for row in query_user.get('user_role_info')])

        data = UserInfoModel(
            **CamelCaseUtil.transform_result(query_user.get('user_basic_info')),
            postIds='',
            roleIds=role_ids,
            dept=CamelCaseUtil.transform_result(query_user.get('user_dept_info')),
            role=CamelCaseUtil.transform_result(query_user.get('user_role_info')),
        )
        cls.decorate_user_model(data, [row.role_key for row in query_user.get('user_role_info')])

        return UserProfileModel(
            data=data,
            postGroup='',
            roleGroup=role_group,
        )

    @classmethod
    async def reset_user_services(cls, query_db: AsyncSession, page_object: ResetUserModel) -> CrudResponseModel:
        """
        重置用户密码service

        :param query_db: orm对象
        :param page_object: 重置用户对象
        :return: 重置用户校验结果
        """
        reset_user = page_object.model_dump(exclude_unset=True, exclude={'admin'})
        if page_object.old_password:
            user = (await UserDao.get_user_detail_by_id(query_db, user_id=page_object.user_id)).get('user_basic_info')
            if not PwdUtil.verify_password(page_object.old_password, user.password):
                raise ServiceException(message='修改密码失败，旧密码错误')
            if PwdUtil.verify_password(page_object.password, user.password):
                raise ServiceException(message='新密码不能与旧密码相同')
            del reset_user['old_password']
        if page_object.sms_code and page_object.session_id:
            del reset_user['sms_code']
            del reset_user['session_id']
        try:
            reset_user['password'] = PwdUtil.get_password_hash(page_object.password)
            await UserDao.edit_user_dao(query_db, reset_user)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='重置成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def change_internal_power_limit_services(
        cls, query_db: AsyncSession, user_id: int, max_count: int, update_by: str
    ) -> CrudResponseModel:
        """
        修改单个用户最大内功数。
        """
        if max_count < 20:
            raise ServiceException(message='最大内功数不能低于20')
        await UserDao.edit_user_dao(
            query_db,
            {
                'user_id': user_id,
                'max_internal_power_count': max_count,
                'update_by': update_by,
                'update_time': datetime.now(),
            },
        )
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='内功上限已更新')

    @classmethod
    async def change_ai_recognition_count_services(
        cls, query_db: AsyncSession, user_id: int, count: int, update_by: str
    ) -> CrudResponseModel:
        """
        修改单个用户AI识图剩余次数。
        """
        if count < 0:
            raise ServiceException(message='AI识图次数不能小于0')
        await UserDao.edit_user_dao(
            query_db,
            {
                'user_id': user_id,
                'ai_image_recognition_count': count,
                'update_by': update_by,
                'update_time': datetime.now(),
            },
        )
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='AI识图次数已更新')

    @classmethod
    async def batch_change_internal_power_limit_services(
        cls, query_db: AsyncSession, user_ids: list[int], max_count: int, update_by: str
    ) -> CrudResponseModel:
        """
        批量修改用户最大内功数。
        """
        if not user_ids:
            raise ServiceException(message='请选择需要修改的用户')
        if max_count < 20:
            raise ServiceException(message='最大内功数不能低于20')
        now = datetime.now()
        for user_id in user_ids:
            await UserDao.edit_user_dao(
                query_db,
                {
                    'user_id': user_id,
                    'max_internal_power_count': max_count,
                    'update_by': update_by,
                    'update_time': now,
                },
            )
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='批量内功上限已更新')

    @classmethod
    async def expire_vip_users_services(cls, query_db: AsyncSession) -> int:
        """
        将已过期VIP实时落库为非VIP。
        """
        result = await query_db.execute(
            update(SysUser)
            .where(SysUser.is_vip == '1', SysUser.vip_expire_time.is_not(None), SysUser.vip_expire_time <= datetime.now())
            .values(is_vip='0', update_by='system', update_time=datetime.now())
        )
        await query_db.commit()
        return result.rowcount or 0

    @classmethod
    def _set_row_sex_value(cls, row: pd.Series) -> None:
        """
        设置行性别值

        :param row: 行数据
        :return: None
        """
        if row['sex'] == '男':
            row['sex'] = '0'
        if row['sex'] == '女':
            row['sex'] = '1'
        if row['sex'] == '未知':
            row['sex'] = '2'

    @classmethod
    def _set_row_status_value(cls, row: pd.Series) -> None:
        """
        设置行状态值

        :param row: 行数据
        :return: None
        """
        if row['status'] == '正常':
            row['status'] = '0'
        if row['status'] == '停用':
            row['status'] = '1'

    @classmethod
    async def batch_import_user_services(
        cls,
        request: Request,
        query_db: AsyncSession,
        file: UploadFile,
        update_support: bool,
        current_user: CurrentUserModel,
        user_data_scope_sql: ColumnElement,
    ) -> CrudResponseModel:
        """
        批量导入用户service

        :param request: Request对象
        :param query_db: orm对象
        :param file: 用户导入文件对象
        :param update_support: 用户存在时是否更新
        :param current_user: 当前用户对象
        :param user_data_scope_sql: 用户数据权限sql
        :return: 批量导入用户结果
        """
        header_dict = {
            '部门编号': 'dept_id',
            '登录名称': 'user_name',
            '用户名称': 'nick_name',
            '用户邮箱': 'email',
            '手机号码': 'phonenumber',
            '用户性别': 'sex',
            '帐号状态': 'status',
        }
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        await file.close()
        df.rename(columns=header_dict, inplace=True)
        add_error_result = []
        count = 0
        try:
            for _index, row in df.iterrows():
                count = count + 1
                cls._set_row_sex_value(row)
                cls._set_row_status_value(row)
                add_user = UserModel(
                    deptId=row['dept_id'],
                    userName=row['user_name'],
                    password=PwdUtil.get_password_hash(
                        await ConfigService.query_config_list_from_cache_services(
                            request.app.state.redis, 'sys.user.initPassword'
                        )
                    ),
                    nickName=row['nick_name'],
                    email=row['email'],
                    phonenumber=str(row['phonenumber']),
                    sex=row['sex'],
                    status=row['status'],
                    createBy=current_user.user.user_name,
                    createTime=datetime.now(),
                    updateBy=current_user.user.user_name,
                    updateTime=datetime.now(),
                )
                user_info = await UserDao.get_user_by_info(query_db, UserModel(userName=row['user_name']))
                if user_info:
                    if update_support:
                        edit_user_model = UserModel(
                            userId=user_info.user_id,
                            deptId=row['dept_id'],
                            userName=row['user_name'],
                            nickName=row['nick_name'],
                            email=row['email'],
                            phonenumber=str(row['phonenumber']),
                            sex=row['sex'],
                            status=row['status'],
                            updateBy=current_user.user.user_name,
                            updateTime=datetime.now(),
                        )
                        edit_user_model.validate_fields()
                        await cls.check_user_allowed_services(edit_user_model)
                        if not current_user.user.admin:
                            await cls.check_user_data_scope_services(
                                query_db, edit_user_model.user_id, user_data_scope_sql
                            )
                        edit_user = edit_user_model.model_dump(exclude_unset=True)
                        await UserDao.edit_user_dao(query_db, edit_user)
                    else:
                        add_error_result.append(f'{count}.用户账号{row["user_name"]}已存在')
                else:
                    add_user.validate_fields()
                    await UserDao.add_user_dao(query_db, add_user)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='\n'.join(add_error_result))
        except Exception as e:
            await query_db.rollback()
            raise e

    @staticmethod
    async def get_user_import_template_services() -> bytes:
        """
        获取用户导入模板service

        :return: 用户导入模板excel的二进制数据
        """
        header_list = ['登录名称', '用户名称', '用户邮箱', '手机号码', '用户性别', '帐号状态']
        selector_header_list = ['用户性别', '帐号状态']
        option_list = [{'用户性别': ['男', '女', '未知']}, {'帐号状态': ['正常', '停用']}]
        binary_data = ExcelUtil.get_excel_template(
            header_list=header_list, selector_header_list=selector_header_list, option_list=option_list
        )

        return binary_data

    @staticmethod
    async def export_user_list_services(user_list: list) -> bytes:
        """
        导出用户信息service

        :param user_list: 用户信息列表
        :return: 用户信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'userId': '用户编号',
            'userName': '用户名称',
            'nickName': '用户昵称',
            'email': '邮箱地址',
            'phonenumber': '手机号码',
            'sex': '性别',
            'status': '状态',
            'createBy': '创建者',
            'createTime': '创建时间',
            'updateBy': '更新者',
            'updateTime': '更新时间',
            'remark': '备注',
        }

        for item in user_list:
            if item.get('status') == '0':
                item['status'] = '正常'
            else:
                item['status'] = '停用'
            if item.get('sex') == '0':
                item['sex'] = '男'
            elif item.get('sex') == '1':
                item['sex'] = '女'
            else:
                item['sex'] = '未知'
        binary_data = ExcelUtil.export_list2excel(user_list, mapping_dict)

        return binary_data

    @classmethod
    async def get_user_role_allocated_list_services(
        cls, query_db: AsyncSession, page_object: UserRoleQueryModel
    ) -> UserRoleResponseModel:
        """
        根据用户id获取已分配角色列表

        :param query_db: orm对象
        :param page_object: 用户关联角色对象
        :return: 已分配角色列表
        """
        query_user = await UserDao.get_user_detail_by_id(query_db, page_object.user_id)
        role_ids = ','.join([str(row.role_id) for row in query_user.get('user_role_info')])
        user = UserInfoModel(
            **CamelCaseUtil.transform_result(query_user.get('user_basic_info')),
            postIds='',
            roleIds=role_ids,
            dept=CamelCaseUtil.transform_result(query_user.get('user_dept_info')),
            role=CamelCaseUtil.transform_result(query_user.get('user_role_info')),
        )
        query_role_list = [
            SelectedRoleModel(**row) for row in await RoleService.get_role_select_option_services(query_db)
        ]
        for model_a in query_role_list:
            for model_b in user.role:
                if model_a.role_id == model_b.role_id:
                    model_a.flag = True
        result = UserRoleResponseModel(roles=query_role_list, user=user)

        return result

    @classmethod
    async def add_user_role_services(cls, query_db: AsyncSession, page_object: CrudUserRoleModel) -> CrudResponseModel:
        """
        新增用户关联角色信息service

        :param query_db: orm对象
        :param page_object: 新增用户关联角色对象
        :return: 新增用户关联角色校验结果
        """
        if page_object.user_id and page_object.role_ids:
            role_id_list = page_object.role_ids.split(',')
            try:
                await UserDao.delete_user_role_by_user_and_role_dao(query_db, UserRoleModel(userId=page_object.user_id))
                for role_id in role_id_list:
                    await UserDao.add_user_role_dao(query_db, UserRoleModel(userId=page_object.user_id, roleId=role_id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='分配成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        elif page_object.user_id and not page_object.role_ids:
            try:
                await UserDao.delete_user_role_by_user_and_role_dao(query_db, UserRoleModel(userId=page_object.user_id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='分配成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        elif page_object.user_ids and page_object.role_id:
            user_id_list = page_object.user_ids.split(',')
            try:
                for user_id in user_id_list:
                    user_role = await cls.detail_user_role_services(
                        query_db, UserRoleModel(userId=user_id, roleId=page_object.role_id)
                    )
                    if user_role:
                        continue
                    await UserDao.add_user_role_dao(query_db, UserRoleModel(userId=user_id, roleId=page_object.role_id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='新增成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='不满足新增条件')

    @classmethod
    async def delete_user_role_services(
        cls, query_db: AsyncSession, page_object: CrudUserRoleModel
    ) -> CrudResponseModel:
        """
        删除用户关联角色信息service

        :param query_db: orm对象
        :param page_object: 删除用户关联角色对象
        :return: 删除用户关联角色校验结果
        """
        if (page_object.user_id and page_object.role_id) or (page_object.user_ids and page_object.role_id):
            if page_object.user_id and page_object.role_id:
                try:
                    await UserDao.delete_user_role_by_user_and_role_dao(
                        query_db, UserRoleModel(userId=page_object.user_id, roleId=page_object.role_id)
                    )
                    await query_db.commit()
                    return CrudResponseModel(is_success=True, message='删除成功')
                except Exception as e:
                    await query_db.rollback()
                    raise e
            elif page_object.user_ids and page_object.role_id:
                user_id_list = page_object.user_ids.split(',')
                try:
                    for user_id in user_id_list:
                        await UserDao.delete_user_role_by_user_and_role_dao(
                            query_db, UserRoleModel(userId=user_id, roleId=page_object.role_id)
                        )
                    await query_db.commit()
                    return CrudResponseModel(is_success=True, message='删除成功')
                except Exception as e:
                    await query_db.rollback()
                    raise e
            else:
                raise ServiceException(message='不满足删除条件')
        else:
            raise ServiceException(message='传入用户角色关联信息为空')

    @classmethod
    async def detail_user_role_services(cls, query_db: AsyncSession, page_object: UserRoleModel) -> SysUserRole | None:
        """
        获取用户关联角色详细信息service

        :param query_db: orm对象
        :param page_object: 用户关联角色对象
        :return: 用户关联角色详细信息
        """
        user_role = await UserDao.get_user_role_detail(query_db, page_object)

        return user_role
