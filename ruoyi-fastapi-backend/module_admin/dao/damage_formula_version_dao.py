from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.damage_formula_version_do import SystemDamageFormulaVersion
from module_admin.entity.vo.damage_formula_version_vo import DamageFormulaVersionQueryModel
from utils.page_util import PageUtil


class DamageFormulaVersionDao:
    """
    系统伤害公式版本数据库操作层
    """

    @classmethod
    async def get_list(
        cls, db: AsyncSession, query_object: DamageFormulaVersionQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        query = (
            select(SystemDamageFormulaVersion)
            .where(
                SystemDamageFormulaVersion.version_name.like(f'%{query_object.version_name}%')
                if query_object.version_name
                else True,
                SystemDamageFormulaVersion.formula_scope == query_object.formula_scope
                if query_object.formula_scope
                else True,
                SystemDamageFormulaVersion.status == query_object.status if query_object.status else True,
            )
            .order_by(SystemDamageFormulaVersion.version_id.desc())
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, version_id: int) -> SystemDamageFormulaVersion | None:
        result = await db.execute(
            select(SystemDamageFormulaVersion).where(SystemDamageFormulaVersion.version_id == version_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_published(cls, db: AsyncSession, formula_scope: str) -> SystemDamageFormulaVersion | None:
        result = await db.execute(
            select(SystemDamageFormulaVersion)
            .where(
                SystemDamageFormulaVersion.formula_scope == formula_scope,
                SystemDamageFormulaVersion.status == 'published',
            )
            .order_by(SystemDamageFormulaVersion.publish_time.desc(), SystemDamageFormulaVersion.version_id.desc())
        )
        return result.scalars().first()

    @classmethod
    async def add(cls, db: AsyncSession, version: SystemDamageFormulaVersion) -> SystemDamageFormulaVersion:
        db.add(version)
        await db.flush()
        return version

    @classmethod
    async def update(cls, db: AsyncSession, values: dict) -> None:
        await db.execute(update(SystemDamageFormulaVersion), [values])

    @classmethod
    async def archive_published(cls, db: AsyncSession, formula_scope: str, exclude_version_id: int | None = None) -> None:
        conditions = [
            SystemDamageFormulaVersion.formula_scope == formula_scope,
            SystemDamageFormulaVersion.status == 'published',
        ]
        if exclude_version_id is not None:
            conditions.append(SystemDamageFormulaVersion.version_id != exclude_version_id)
        await db.execute(
            update(SystemDamageFormulaVersion)
            .where(*conditions)
            .values(status='archived')
        )
