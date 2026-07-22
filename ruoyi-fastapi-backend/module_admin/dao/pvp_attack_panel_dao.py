from datetime import datetime
from typing import Any

from sqlalchemy import delete, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.pvp_attack_panel_do import SystemPvpAttackPanel
from module_admin.entity.vo.pvp_attack_panel_vo import PvpAttackPanelQueryModel
from utils.page_util import PageUtil


class PvpAttackPanelDao:
    """系统 PVP 进攻方面板数据库操作。"""

    @classmethod
    async def get_list(
        cls, query_db: AsyncSession, query: PvpAttackPanelQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        statement = (
            select(SystemPvpAttackPanel)
            .where(
                SystemPvpAttackPanel.panel_name.like(f'%{query.panel_name}%') if query.panel_name else True,
                SystemPvpAttackPanel.status == query.status if query.status else True,
            )
            .order_by(desc(SystemPvpAttackPanel.update_time), desc(SystemPvpAttackPanel.panel_id))
        )
        return await PageUtil.paginate(query_db, statement, query.page_num, query.page_size, is_page)

    @classmethod
    async def list_enabled(cls, query_db: AsyncSession) -> list[SystemPvpAttackPanel]:
        result = await query_db.execute(
            select(SystemPvpAttackPanel)
            .where(SystemPvpAttackPanel.status == '0')
            .order_by(desc(SystemPvpAttackPanel.update_time), desc(SystemPvpAttackPanel.panel_id))
        )
        return list(result.scalars().all())

    @classmethod
    async def get_by_id(cls, query_db: AsyncSession, panel_id: int) -> SystemPvpAttackPanel | None:
        result = await query_db.execute(select(SystemPvpAttackPanel).where(SystemPvpAttackPanel.panel_id == panel_id))
        return result.scalars().first()

    @classmethod
    async def add(cls, query_db: AsyncSession, panel: SystemPvpAttackPanel) -> SystemPvpAttackPanel:
        query_db.add(panel)
        await query_db.flush()
        return panel

    @classmethod
    async def update(cls, query_db: AsyncSession, values: dict[str, Any]) -> None:
        await query_db.execute(update(SystemPvpAttackPanel), [values])

    @classmethod
    async def change_status(cls, query_db: AsyncSession, panel_id: int, status: str, operator: str) -> None:
        await query_db.execute(
            update(SystemPvpAttackPanel)
            .where(SystemPvpAttackPanel.panel_id == panel_id)
            .values(status=status, update_by=operator, update_time=datetime.now())
        )

    @classmethod
    async def delete_by_ids(cls, query_db: AsyncSession, panel_ids: list[int]) -> None:
        await query_db.execute(delete(SystemPvpAttackPanel).where(SystemPvpAttackPanel.panel_id.in_(panel_ids)))
