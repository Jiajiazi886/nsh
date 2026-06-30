import json
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.constants.internal_power_presets import ELEMENT_KEY_TO_LABEL
from module_admin.dao.internal_power_preset_dao import InternalPowerPresetDao
from module_admin.entity.do.internal_power_preset_do import SystemInternalPowerPreset
from module_admin.entity.vo.internal_power_vo import InternalPowerElementsModel
from module_admin.entity.vo.internal_power_preset_vo import (
    DeleteInternalPowerPresetModel,
    InternalPowerPresetModel,
    InternalPowerPresetQueryModel,
)


class InternalPowerPresetService:
    """
    系统内功预设服务层
    """

    @classmethod
    async def get_preset_list_services(
        cls, query_db: AsyncSession, query_object: InternalPowerPresetQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        result = await InternalPowerPresetDao.get_list(query_db, query_object, is_page)
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
    async def get_personal_enabled_presets_service(cls, query_db: AsyncSession) -> list[InternalPowerPresetModel]:
        rows = await InternalPowerPresetDao.list_enabled(query_db)
        return [cls.__to_model(row) for row in rows]

    @classmethod
    async def preset_detail_services(cls, query_db: AsyncSession, preset_id: int) -> InternalPowerPresetModel:
        preset = await InternalPowerPresetDao.get_by_id(query_db, preset_id)
        if preset is None:
            raise ServiceException(message='内功预设不存在')
        return cls.__to_model(preset)

    @classmethod
    async def add_preset_services(
        cls, query_db: AsyncSession, preset: InternalPowerPresetModel
    ) -> CrudResponseModel:
        await cls.__assert_unique(query_db, preset)
        now = datetime.now()
        db_preset = SystemInternalPowerPreset(
            name=preset.name,
            element_key=preset.element_key,
            elements_json=cls.__json_dumps(cls.__model_dump(preset.elements)),
            bonus_percent=float(preset.bonus_percent or 0),
            lingyun_bonus_percent=float(preset.lingyun_bonus_percent or 0),
            bonus_type=preset.bonus_type or '',
            bonus_desc=preset.bonus_desc or '',
            image_url=preset.image_url or '',
            entries_json=cls.__json_dumps(preset.entries),
            status=preset.status or '0',
            remark=preset.remark or '',
            create_time=now,
            update_time=now,
        )
        await InternalPowerPresetDao.add(query_db, db_preset)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='新增成功')

    @classmethod
    async def edit_preset_services(
        cls, query_db: AsyncSession, preset: InternalPowerPresetModel
    ) -> CrudResponseModel:
        if preset.preset_id is None:
            raise ServiceException(message='预设ID不能为空')
        existing = await InternalPowerPresetDao.get_by_id(query_db, preset.preset_id)
        if existing is None:
            raise ServiceException(message='内功预设不存在')
        await cls.__assert_unique(query_db, preset)
        await InternalPowerPresetDao.update(
            query_db,
            {
                'preset_id': preset.preset_id,
                'name': preset.name,
                'element_key': preset.element_key,
                'elements_json': cls.__json_dumps(cls.__model_dump(preset.elements)),
                'bonus_percent': float(preset.bonus_percent or 0),
                'lingyun_bonus_percent': float(preset.lingyun_bonus_percent or 0),
                'bonus_type': preset.bonus_type or '',
                'bonus_desc': preset.bonus_desc or '',
                'image_url': preset.image_url or '',
                'entries_json': cls.__json_dumps(preset.entries),
                'status': preset.status or '0',
                'remark': preset.remark or '',
                'update_time': datetime.now(),
            },
        )
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='更新成功')

    @classmethod
    async def delete_preset_services(
        cls, query_db: AsyncSession, delete_preset: DeleteInternalPowerPresetModel
    ) -> CrudResponseModel:
        if not delete_preset.preset_ids:
            raise ServiceException(message='传入预设ID为空')
        for preset_id in delete_preset.preset_ids.split(','):
            await cls.preset_detail_services(query_db, int(preset_id))
            await InternalPowerPresetDao.delete(query_db, int(preset_id))
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def __assert_unique(cls, query_db: AsyncSession, preset: InternalPowerPresetModel) -> None:
        existing = await InternalPowerPresetDao.get_by_name_element(query_db, preset.name, preset.element_key)
        if existing and existing.preset_id != preset.preset_id:
            raise ServiceException(message=f'{preset.name}的该元素预设已存在')

    @classmethod
    def __to_model(cls, preset: SystemInternalPowerPreset) -> InternalPowerPresetModel:
        return InternalPowerPresetModel(
            presetId=preset.preset_id,
            name=preset.name,
            elementKey=preset.element_key,
            elements=InternalPowerElementsModel(**cls.__json_loads(preset.elements_json, {})),
            bonusPercent=preset.bonus_percent or 0,
            lingyunBonusPercent=getattr(preset, 'lingyun_bonus_percent', 0) or 0,
            bonusType=preset.bonus_type or '',
            bonusDesc=preset.bonus_desc or '',
            imageUrl=preset.image_url or '',
            entries=cls.__json_loads(preset.entries_json, []),
            status=preset.status or '0',
            remark=preset.remark or '',
            displayName=cls.__display_name(preset.name, preset.element_key),
            createTime=preset.create_time,
            updateTime=preset.update_time,
        )

    @classmethod
    def __dict_to_model(cls, row: dict[str, Any]) -> InternalPowerPresetModel:
        return InternalPowerPresetModel(
            presetId=row.get('presetId'),
            name=row.get('name') or '',
            elementKey=row.get('elementKey') or 'metal',
            elements=InternalPowerElementsModel(**cls.__json_loads(row.get('elementsJson'), {})),
            bonusPercent=row.get('bonusPercent') or 0,
            lingyunBonusPercent=row.get('lingyunBonusPercent') or row.get('lingyun_bonus_percent') or 0,
            bonusType=row.get('bonusType') or '',
            bonusDesc=row.get('bonusDesc') or '',
            imageUrl=row.get('imageUrl') or '',
            entries=cls.__json_loads(row.get('entriesJson'), []),
            status=row.get('status') or '0',
            remark=row.get('remark') or '',
            displayName=cls.__display_name(row.get('name') or '', row.get('elementKey') or 'metal'),
            createTime=row.get('createTime'),
            updateTime=row.get('updateTime'),
        )

    @staticmethod
    def __display_name(name: str, element_key: str) -> str:
        if element_key == 'mixed':
            return f'{name}（全元素）'
        return f'{name}（{ELEMENT_KEY_TO_LABEL.get(element_key, element_key)}）'

    @staticmethod
    def __model_dump(value: Any) -> Any:
        if hasattr(value, 'model_dump'):
            return value.model_dump()
        if isinstance(value, list):
            return [InternalPowerPresetService.__model_dump(item) for item in value]
        if isinstance(value, tuple):
            return [InternalPowerPresetService.__model_dump(item) for item in value]
        if isinstance(value, dict):
            return {key: InternalPowerPresetService.__model_dump(item) for key, item in value.items()}
        return value

    @classmethod
    def __json_dumps(cls, value: Any) -> str:
        return json.dumps(cls.__model_dump(value), ensure_ascii=False)

    @staticmethod
    def __json_loads(value: str | None, default: Any) -> Any:
        if not value:
            return default
        try:
            return json.loads(value)
        except Exception:
            return default
