from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.constants.internal_power_entry_limits import INTERNAL_POWER_ENTRY_LIMIT_MAP
from module_admin.dao.internal_power_entry_dao import InternalPowerEntryDao
from module_admin.entity.do.internal_power_entry_do import SystemInternalPowerEntry
from module_admin.entity.vo.internal_power_entry_vo import (
    DeleteInternalPowerEntryModel,
    InternalPowerEntryConfigModel,
    InternalPowerEntryQueryModel,
)


class InternalPowerEntryService:
    """
    系统内功词条服务层
    """

    @classmethod
    async def get_entry_list_services(
        cls, query_db: AsyncSession, query_object: InternalPowerEntryQueryModel, is_page: bool = False
    ) -> PageModel | list[InternalPowerEntryConfigModel]:
        result = await InternalPowerEntryDao.get_list(query_db, query_object, is_page)
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
    async def get_personal_enabled_entries_service(cls, query_db: AsyncSession) -> list[InternalPowerEntryConfigModel]:
        rows = await InternalPowerEntryDao.list_enabled(query_db)
        return [cls.__to_model(row) for row in rows if row.entry_name in INTERNAL_POWER_ENTRY_LIMIT_MAP]

    @classmethod
    async def get_enabled_entry_names_service(cls, query_db: AsyncSession) -> set[str]:
        rows = await InternalPowerEntryDao.list_enabled(query_db)
        return {row.entry_name for row in rows if row.entry_name in INTERNAL_POWER_ENTRY_LIMIT_MAP}

    @classmethod
    async def entry_detail_services(cls, query_db: AsyncSession, entry_id: int) -> InternalPowerEntryConfigModel:
        entry = await InternalPowerEntryDao.get_by_id(query_db, entry_id)
        if entry is None:
            raise ServiceException(message='内功词条不存在')
        return cls.__to_model(entry)

    @classmethod
    async def add_entry_services(
        cls, query_db: AsyncSession, entry: InternalPowerEntryConfigModel
    ) -> CrudResponseModel:
        await cls.__assert_unique(query_db, entry)
        now = datetime.now()
        db_entry = SystemInternalPowerEntry(
            entry_name=entry.entry_name,
            conversion_percent=entry.conversion_percent,
            conversion_desc=entry.conversion_desc or '',
            status=entry.status or '0',
            remark=entry.remark or '',
            create_time=now,
            update_time=now,
        )
        await InternalPowerEntryDao.add(query_db, db_entry)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='新增成功')

    @classmethod
    async def edit_entry_services(
        cls, query_db: AsyncSession, entry: InternalPowerEntryConfigModel
    ) -> CrudResponseModel:
        if entry.entry_id is None:
            raise ServiceException(message='词条ID不能为空')
        existing = await InternalPowerEntryDao.get_by_id(query_db, entry.entry_id)
        if existing is None:
            raise ServiceException(message='内功词条不存在')
        await cls.__assert_unique(query_db, entry)
        await InternalPowerEntryDao.update(
            query_db,
            {
                'entry_id': entry.entry_id,
                'entry_name': entry.entry_name,
                'conversion_percent': entry.conversion_percent,
                'conversion_desc': entry.conversion_desc or '',
                'status': entry.status or '0',
                'remark': entry.remark or '',
                'update_time': datetime.now(),
            },
        )
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='更新成功')

    @classmethod
    async def delete_entry_services(
        cls, query_db: AsyncSession, delete_entry: DeleteInternalPowerEntryModel
    ) -> CrudResponseModel:
        if not delete_entry.entry_ids:
            raise ServiceException(message='传入词条ID为空')
        for entry_id in delete_entry.entry_ids.split(','):
            await cls.entry_detail_services(query_db, int(entry_id))
            await InternalPowerEntryDao.delete(query_db, int(entry_id))
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def __assert_unique(cls, query_db: AsyncSession, entry: InternalPowerEntryConfigModel) -> None:
        existing = await InternalPowerEntryDao.get_by_name(query_db, entry.entry_name)
        if existing and existing.entry_id != entry.entry_id:
            raise ServiceException(message=f'内功词条「{entry.entry_name}」已存在')

    @staticmethod
    def __to_model(entry: SystemInternalPowerEntry) -> InternalPowerEntryConfigModel:
        limit = INTERNAL_POWER_ENTRY_LIMIT_MAP.get(entry.entry_name, {})
        return InternalPowerEntryConfigModel(
            entryId=entry.entry_id,
            entryName=entry.entry_name,
            conversionPercent=entry.conversion_percent,
            conversionDesc=entry.conversion_desc or '',
            limitText=limit.get('limit_text', ''),
            limitValue=limit.get('limit_value'),
            valueType=limit.get('value_type', 'number'),
            status=entry.status or '0',
            remark=entry.remark or '',
            createTime=entry.create_time,
            updateTime=entry.update_time,
        )

    @staticmethod
    def __dict_to_model(row: dict[str, Any]) -> InternalPowerEntryConfigModel:
        entry_name = row.get('entryName') or ''
        limit = INTERNAL_POWER_ENTRY_LIMIT_MAP.get(entry_name, {})
        return InternalPowerEntryConfigModel(
            entryId=row.get('entryId'),
            entryName=entry_name,
            conversionPercent=row.get('conversionPercent'),
            conversionDesc=row.get('conversionDesc') or '',
            limitText=limit.get('limit_text', ''),
            limitValue=limit.get('limit_value'),
            valueType=limit.get('value_type', 'number'),
            status=row.get('status') or '0',
            remark=row.get('remark') or '',
            createTime=row.get('createTime'),
            updateTime=row.get('updateTime'),
        )
