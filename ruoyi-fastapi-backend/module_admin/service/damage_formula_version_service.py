import json
import re
from datetime import datetime
from typing import Any

from sqlalchemy.exc import DataError
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.damage_formula_version_dao import DamageFormulaVersionDao
from module_admin.entity.do.damage_formula_version_do import SystemDamageFormulaVersion
from module_admin.entity.vo.damage_formula_version_vo import (
    FORMULA_SCOPE_INTERNAL_POWER_PVP,
    DamageFormulaVersionModel,
    DamageFormulaVersionQueryModel,
)


class DamageFormulaVersionService:
    """
    系统伤害公式版本服务层
    """

    _FORBIDDEN_EXPR_TOKENS = re.compile(
        r'(;|=>|\{|\}|\[|\]|`|\bfunction\b|\bnew\b|\bthis\b|\bwindow\b|\bdocument\b|'
        r'\bglobalThis\b|\bconstructor\b|\b__proto__\b|\bprototype\b|\beval\b|\bimport\b|'
        r'\brequire\b|\bprocess\b)',
        re.IGNORECASE,
    )
    _ALLOWED_EXPR_CHARS = re.compile(r'^[\s\w\u4e00-\u9fff+\-*/%().,!<>=&|?:,"\'\\]+$')
    _REQUIRED_PACKAGE_KEYS = ('defaults', 'fields', 'fixedCells', 'entryRules', 'benefitPresets', 'outputs')

    @classmethod
    async def get_version_list_services(
        cls, query_db: AsyncSession, query_object: DamageFormulaVersionQueryModel, is_page: bool = False
    ) -> PageModel | list[DamageFormulaVersionModel]:
        result = await DamageFormulaVersionDao.get_list(query_db, query_object, is_page)
        if isinstance(result, PageModel):
            return PageModel(
                rows=[cls.__dict_to_model(row) for row in result.rows],
                pageNum=result.page_num,
                pageSize=result.page_size,
                total=result.total,
                hasNext=result.has_next,
            )
        return [cls.__dict_to_model(row) for row in result]

    @classmethod
    async def version_detail_services(cls, query_db: AsyncSession, version_id: int) -> DamageFormulaVersionModel:
        version = await DamageFormulaVersionDao.get_by_id(query_db, version_id)
        if version is None:
            raise ServiceException(message='公式版本不存在')
        return cls.__to_model(version)

    @classmethod
    async def get_active_version_services(
        cls, query_db: AsyncSession, formula_scope: str = FORMULA_SCOPE_INTERNAL_POWER_PVP
    ) -> DamageFormulaVersionModel:
        cls.__assert_scope(formula_scope)
        version = await DamageFormulaVersionDao.get_published(query_db, formula_scope)
        if version:
            return cls.__to_model(version)
        return cls.__builtin_version()

    @classmethod
    async def add_version_services(
        cls, query_db: AsyncSession, version: DamageFormulaVersionModel, operator: str = ''
    ) -> CrudResponseModel:
        cls.__assert_scope(version.formula_scope)
        cls.__validate_package_shape(version.formula_package, strict=False)
        now = datetime.now()
        db_version = SystemDamageFormulaVersion(
            version_name=version.version_name,
            formula_scope=FORMULA_SCOPE_INTERNAL_POWER_PVP,
            status='draft',
            formula_package_json=cls.__dump_package(version.formula_package),
            remark=version.remark or '',
            create_by=operator,
            update_by=operator,
            create_time=now,
            update_time=now,
        )
        try:
            await DamageFormulaVersionDao.add(query_db, db_version)
            await query_db.commit()
        except DataError as exc:
            await cls.__handle_package_data_error(query_db, exc)
        return CrudResponseModel(is_success=True, message='新增成功', result={'versionId': db_version.version_id})

    @classmethod
    async def edit_version_services(
        cls, query_db: AsyncSession, version: DamageFormulaVersionModel, operator: str = ''
    ) -> CrudResponseModel:
        if version.version_id is None:
            raise ServiceException(message='公式版本ID不能为空')
        existing = await DamageFormulaVersionDao.get_by_id(query_db, version.version_id)
        if existing is None:
            raise ServiceException(message='公式版本不存在')
        if existing.status != 'draft':
            raise ServiceException(message='只能编辑草稿版本，请先复制为草稿')
        cls.__assert_scope(version.formula_scope)
        cls.__validate_package_shape(version.formula_package, strict=False)
        try:
            await DamageFormulaVersionDao.update(
                query_db,
                {
                    'version_id': version.version_id,
                    'version_name': version.version_name,
                    'formula_scope': FORMULA_SCOPE_INTERNAL_POWER_PVP,
                    'status': 'draft',
                    'formula_package_json': cls.__dump_package(version.formula_package),
                    'remark': version.remark or '',
                    'update_by': operator,
                    'update_time': datetime.now(),
                },
            )
            await query_db.commit()
        except DataError as exc:
            await cls.__handle_package_data_error(query_db, exc)
        return CrudResponseModel(is_success=True, message='保存成功')

    @classmethod
    async def copy_version_services(
        cls, query_db: AsyncSession, version_id: int, operator: str = ''
    ) -> CrudResponseModel:
        source = await DamageFormulaVersionDao.get_by_id(query_db, version_id)
        if source is None:
            raise ServiceException(message='公式版本不存在')
        now = datetime.now()
        db_version = SystemDamageFormulaVersion(
            version_name=f'{source.version_name} 副本',
            formula_scope=source.formula_scope,
            status='draft',
            formula_package_json=source.formula_package_json,
            remark=source.remark or '',
            create_by=operator,
            update_by=operator,
            create_time=now,
            update_time=now,
        )
        try:
            await DamageFormulaVersionDao.add(query_db, db_version)
            await query_db.commit()
        except DataError as exc:
            await cls.__handle_package_data_error(query_db, exc)
        return CrudResponseModel(is_success=True, message='复制成功', result={'versionId': db_version.version_id})

    @classmethod
    async def publish_version_services(
        cls, query_db: AsyncSession, version_id: int, operator: str = ''
    ) -> CrudResponseModel:
        version = await DamageFormulaVersionDao.get_by_id(query_db, version_id)
        if version is None:
            raise ServiceException(message='公式版本不存在')
        package = cls.__load_package(version.formula_package_json)
        cls.__validate_package_shape(package, strict=True)
        cls.__validate_formula_expressions(package)
        now = datetime.now()
        await DamageFormulaVersionDao.archive_published(query_db, version.formula_scope, exclude_version_id=version_id)
        await DamageFormulaVersionDao.update(
            query_db,
            {
                'version_id': version_id,
                'status': 'published',
                'publish_time': now,
                'update_by': operator,
                'update_time': now,
            },
        )
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='发布成功')

    @classmethod
    async def rollback_version_services(
        cls, query_db: AsyncSession, version_id: int, operator: str = ''
    ) -> CrudResponseModel:
        source = await DamageFormulaVersionDao.get_by_id(query_db, version_id)
        if source is None:
            raise ServiceException(message='公式版本不存在')
        package = cls.__load_package(source.formula_package_json)
        cls.__validate_package_shape(package, strict=True)
        cls.__validate_formula_expressions(package)
        now = datetime.now()
        await DamageFormulaVersionDao.archive_published(query_db, source.formula_scope)
        db_version = SystemDamageFormulaVersion(
            version_name=f'回滚：{source.version_name}',
            formula_scope=source.formula_scope,
            status='published',
            formula_package_json=source.formula_package_json,
            remark=f'由版本 {source.version_id} 回滚发布',
            publish_time=now,
            create_by=operator,
            update_by=operator,
            create_time=now,
            update_time=now,
        )
        try:
            await DamageFormulaVersionDao.add(query_db, db_version)
            await query_db.commit()
        except DataError as exc:
            await cls.__handle_package_data_error(query_db, exc)
        return CrudResponseModel(is_success=True, message='回滚发布成功', result={'versionId': db_version.version_id})

    @classmethod
    def __validate_package_shape(cls, package: dict[str, Any], strict: bool = False) -> None:
        if not isinstance(package, dict):
            raise ServiceException(message='公式包必须是JSON对象')
        if package.get('scope') and package.get('scope') != FORMULA_SCOPE_INTERNAL_POWER_PVP:
            raise ServiceException(message='公式包scope必须为internal_power_pvp_damage')
        if strict:
            missing = [key for key in cls._REQUIRED_PACKAGE_KEYS if key not in package]
            if missing:
                raise ServiceException(message=f'公式包缺少必要字段：{", ".join(missing)}')
            if not isinstance(package.get('entryRules'), list):
                raise ServiceException(message='entryRules必须是数组')
            if not isinstance(package.get('benefitPresets'), list):
                raise ServiceException(message='benefitPresets必须是数组')
            if not isinstance(package.get('formulas', {}), dict):
                raise ServiceException(message='formulas必须是对象')

    @classmethod
    def __validate_formula_expressions(cls, package: dict[str, Any]) -> None:
        formulas = package.get('formulas') or {}
        for key, expr in formulas.items():
            if not isinstance(expr, str):
                raise ServiceException(message=f'公式 {key} 必须是字符串')
            if cls._FORBIDDEN_EXPR_TOKENS.search(expr) or not cls._ALLOWED_EXPR_CHARS.match(expr):
                raise ServiceException(message=f'公式 {key} 包含不允许的表达式内容')

    @classmethod
    async def __handle_package_data_error(cls, query_db: AsyncSession, exc: DataError) -> None:
        await query_db.rollback()
        message = str(exc)
        if 'formula_package_json' in message or 'Data too long' in message or '1406' in message:
            raise ServiceException(message='公式包内容过长，请先将 system_damage_formula_version.formula_package_json 字段升级为 LONGTEXT 后重试') from exc
        raise exc

    @staticmethod
    def __assert_scope(formula_scope: str) -> None:
        if formula_scope != FORMULA_SCOPE_INTERNAL_POWER_PVP:
            raise ServiceException(message='当前仅支持内功PVP伤害公式')

    @staticmethod
    def __dump_package(package: dict[str, Any]) -> str:
        return json.dumps(package or {}, ensure_ascii=False, separators=(',', ':'))

    @staticmethod
    def __load_package(raw: str | None) -> dict[str, Any]:
        try:
            value = json.loads(raw or '{}')
        except json.JSONDecodeError as exc:
            raise ServiceException(message=f'公式包JSON格式错误：{exc.msg}') from exc
        if not isinstance(value, dict):
            raise ServiceException(message='公式包必须是JSON对象')
        return value

    @classmethod
    def __to_model(cls, version: SystemDamageFormulaVersion) -> DamageFormulaVersionModel:
        return DamageFormulaVersionModel(
            versionId=version.version_id,
            versionName=version.version_name,
            formulaScope=version.formula_scope,
            status=version.status,
            formulaPackage=cls.__load_package(version.formula_package_json),
            remark=version.remark or '',
            publishTime=version.publish_time,
            createBy=version.create_by or '',
            createTime=version.create_time,
            updateBy=version.update_by or '',
            updateTime=version.update_time,
        )

    @classmethod
    def __dict_to_model(cls, row: dict[str, Any]) -> DamageFormulaVersionModel:
        return DamageFormulaVersionModel(
            versionId=row.get('versionId'),
            versionName=row.get('versionName') or '',
            formulaScope=row.get('formulaScope') or FORMULA_SCOPE_INTERNAL_POWER_PVP,
            status=row.get('status') or 'draft',
            formulaPackage=cls.__load_package(row.get('formulaPackageJson') or row.get('formulaPackage') or '{}'),
            remark=row.get('remark') or '',
            publishTime=row.get('publishTime'),
            createBy=row.get('createBy') or '',
            createTime=row.get('createTime'),
            updateBy=row.get('updateBy') or '',
            updateTime=row.get('updateTime'),
        )

    @staticmethod
    def __builtin_version() -> DamageFormulaVersionModel:
        now = datetime.now()
        return DamageFormulaVersionModel(
            versionId=0,
            versionName='内置默认公式',
            formulaScope=FORMULA_SCOPE_INTERNAL_POWER_PVP,
            status='published',
            formulaPackage={
                'scope': FORMULA_SCOPE_INTERNAL_POWER_PVP,
                'builtin': True,
                'description': '数据库未发布公式时使用前端内置默认公式包',
            },
            remark='内置兜底版本',
            publishTime=now,
            createBy='system',
            createTime=now,
            updateBy='system',
            updateTime=now,
        )
