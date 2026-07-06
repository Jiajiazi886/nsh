import json
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.internal_power_panel_template_dao import InternalPowerPanelTemplateDao
from module_admin.entity.do.internal_power_panel_setting_do import SystemInternalPowerPanelTemplate
from module_admin.entity.vo.internal_power_panel_setting_vo import (
    AttackPanelModel,
    InternalPowerPanelTemplateModel,
    InternalPowerPanelTemplateQueryModel,
    InternalPowerPanelTemplateStatusModel,
    TargetPanelModel,
)


class InternalPowerPanelTemplateService:
    """
    系统内功PVP收益面板模板服务层
    """

    @classmethod
    async def get_template_list_services(
        cls, query_db: AsyncSession, query_object: InternalPowerPanelTemplateQueryModel, is_page: bool = False
    ) -> PageModel | list[InternalPowerPanelTemplateModel]:
        result = await InternalPowerPanelTemplateDao.get_list(query_db, query_object, is_page)
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
    async def get_enabled_templates_services(cls, query_db: AsyncSession) -> list[InternalPowerPanelTemplateModel]:
        rows = await InternalPowerPanelTemplateDao.list_enabled(query_db)
        return [cls.__to_model(row) for row in rows]

    @classmethod
    async def template_detail_services(
        cls, query_db: AsyncSession, template_id: int
    ) -> InternalPowerPanelTemplateModel:
        template = await InternalPowerPanelTemplateDao.get_by_id(query_db, template_id)
        if template is None:
            raise ServiceException(message='面板模板不存在')
        return cls.__to_model(template)

    @classmethod
    async def add_template_services(
        cls, query_db: AsyncSession, template: InternalPowerPanelTemplateModel, operator: str
    ) -> CrudResponseModel:
        now = datetime.now()
        db_template = SystemInternalPowerPanelTemplate(
            template_name=template.template_name.strip(),
            status=template.status or '0',
            target_panel_json=cls.__json_dumps(template.target_panel.model_dump()),
            attack_panel_json=cls.__json_dumps(template.attack_panel.model_dump()),
            remark=template.remark or '',
            create_by=operator,
            create_time=now,
            update_by=operator,
            update_time=now,
        )
        await InternalPowerPanelTemplateDao.add(query_db, db_template)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='新增成功', result={'templateId': db_template.template_id})

    @classmethod
    async def edit_template_services(
        cls, query_db: AsyncSession, template: InternalPowerPanelTemplateModel, operator: str
    ) -> CrudResponseModel:
        if template.template_id is None:
            raise ServiceException(message='模板ID不能为空')
        existing = await InternalPowerPanelTemplateDao.get_by_id(query_db, int(template.template_id))
        if existing is None:
            raise ServiceException(message='面板模板不存在')
        await InternalPowerPanelTemplateDao.update(
            query_db,
            {
                'template_id': int(template.template_id),
                'template_name': template.template_name.strip(),
                'status': template.status or '0',
                'target_panel_json': cls.__json_dumps(template.target_panel.model_dump()),
                'attack_panel_json': cls.__json_dumps(template.attack_panel.model_dump()),
                'remark': template.remark or '',
                'update_by': operator,
                'update_time': datetime.now(),
            },
        )
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='更新成功')

    @classmethod
    async def delete_template_services(cls, query_db: AsyncSession, template_ids: str) -> CrudResponseModel:
        ids = [int(item) for item in str(template_ids or '').split(',') if str(item).strip()]
        if not ids:
            raise ServiceException(message='传入模板ID为空')
        for template_id in ids:
            await cls.template_detail_services(query_db, template_id)
        await InternalPowerPanelTemplateDao.delete_by_ids(query_db, ids)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def change_status_services(
        cls,
        query_db: AsyncSession,
        payload: InternalPowerPanelTemplateStatusModel,
        operator: str,
    ) -> CrudResponseModel:
        await cls.template_detail_services(query_db, payload.template_id)
        await InternalPowerPanelTemplateDao.change_status(query_db, payload.template_id, payload.status, operator)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='状态更新成功')

    @classmethod
    def __to_model(cls, template: SystemInternalPowerPanelTemplate) -> InternalPowerPanelTemplateModel:
        return InternalPowerPanelTemplateModel(
            templateId=template.template_id,
            templateName=template.template_name or '',
            status=template.status or '0',
            targetPanel=TargetPanelModel(**cls.__json_loads(template.target_panel_json)),
            attackPanel=AttackPanelModel(**cls.__json_loads(template.attack_panel_json)),
            remark=template.remark or '',
            createBy=template.create_by or '',
            createTime=template.create_time,
            updateBy=template.update_by or '',
            updateTime=template.update_time,
        )

    @classmethod
    def __dict_to_model(cls, row: dict[str, Any]) -> InternalPowerPanelTemplateModel:
        return InternalPowerPanelTemplateModel(
            templateId=row.get('templateId'),
            templateName=row.get('templateName') or '',
            status=row.get('status') or '0',
            targetPanel=TargetPanelModel(**cls.__json_loads(row.get('targetPanelJson'))),
            attackPanel=AttackPanelModel(**cls.__json_loads(row.get('attackPanelJson'))),
            remark=row.get('remark') or '',
            createBy=row.get('createBy') or '',
            createTime=row.get('createTime'),
            updateBy=row.get('updateBy') or '',
            updateTime=row.get('updateTime'),
        )

    @staticmethod
    def __json_dumps(value: Any) -> str:
        return json.dumps(value or {}, ensure_ascii=False, separators=(',', ':'))

    @staticmethod
    def __json_loads(value: str | None) -> dict[str, Any]:
        if not value:
            return {}
        try:
            loaded = json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        return loaded if isinstance(loaded, dict) else {}
