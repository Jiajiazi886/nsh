from datetime import datetime
from typing import Any

from sqlalchemy import delete, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.internal_power_panel_setting_do import SystemInternalPowerPanelTemplate
from module_admin.entity.vo.internal_power_panel_setting_vo import InternalPowerPanelTemplateQueryModel
from utils.page_util import PageUtil


class InternalPowerPanelTemplateDao:
    """
    系统面板模板数据库操作层
    """

    @classmethod
    async def get_list(
        cls, db: AsyncSession, query_object: InternalPowerPanelTemplateQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        query = (
            select(SystemInternalPowerPanelTemplate)
            .where(
                SystemInternalPowerPanelTemplate.template_name.like(f'%{query_object.template_name}%')
                if query_object.template_name
                else True,
                SystemInternalPowerPanelTemplate.status == query_object.status if query_object.status else True,
            )
            .order_by(desc(SystemInternalPowerPanelTemplate.template_id))
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

    @classmethod
    async def list_enabled(cls, db: AsyncSession) -> list[SystemInternalPowerPanelTemplate]:
        result = await db.execute(
            select(SystemInternalPowerPanelTemplate)
            .where(SystemInternalPowerPanelTemplate.status == '0')
            .order_by(desc(SystemInternalPowerPanelTemplate.update_time), desc(SystemInternalPowerPanelTemplate.template_id))
        )
        return list(result.scalars().all())

    @classmethod
    async def get_by_id(cls, db: AsyncSession, template_id: int) -> SystemInternalPowerPanelTemplate | None:
        result = await db.execute(
            select(SystemInternalPowerPanelTemplate).where(
                SystemInternalPowerPanelTemplate.template_id == template_id
            )
        )
        return result.scalars().first()

    @classmethod
    async def add(
        cls, db: AsyncSession, template: SystemInternalPowerPanelTemplate
    ) -> SystemInternalPowerPanelTemplate:
        db.add(template)
        await db.flush()
        return template

    @classmethod
    async def update(cls, db: AsyncSession, values: dict) -> None:
        await db.execute(update(SystemInternalPowerPanelTemplate), [values])

    @classmethod
    async def delete_by_ids(cls, db: AsyncSession, template_ids: list[int]) -> None:
        await db.execute(
            delete(SystemInternalPowerPanelTemplate).where(
                SystemInternalPowerPanelTemplate.template_id.in_(template_ids)
            )
        )

    @classmethod
    async def change_status(cls, db: AsyncSession, template_id: int, status: str, operator: str) -> None:
        await db.execute(
            update(SystemInternalPowerPanelTemplate)
            .where(SystemInternalPowerPanelTemplate.template_id == template_id)
            .values(status=status, update_by=operator, update_time=datetime.now())
        )
