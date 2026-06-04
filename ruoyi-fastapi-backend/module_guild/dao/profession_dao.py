from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_guild.entity.do.profession_do import GuildProfession
from module_guild.entity.vo.profession_vo import ProfessionModel, ProfessionPageQueryModel
from utils.page_util import PageUtil


class ProfessionDao:
    @classmethod
    async def get_profession_list(
        cls, db: AsyncSession, query_object: ProfessionPageQueryModel, is_page: bool = False
    ) -> Any:
        stmt = (
            select(GuildProfession)
            .where(
                GuildProfession.profession_name.like(f'%{query_object.profession_name}%')
                if query_object.profession_name
                else True,
                GuildProfession.status == query_object.status if query_object.status else True,
            )
            .order_by(GuildProfession.order_num, GuildProfession.profession_id)
        )
        return await PageUtil.paginate(db, stmt, query_object.page_num, query_object.page_size, is_page)

    @classmethod
    async def get_enabled_profession_list(cls, db: AsyncSession) -> list[GuildProfession]:
        stmt = (
            select(GuildProfession)
            .where(GuildProfession.status == '0')
            .order_by(GuildProfession.order_num, GuildProfession.profession_id)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_profession_detail_by_id(cls, db: AsyncSession, profession_id: int) -> GuildProfession | None:
        result = await db.execute(select(GuildProfession).where(GuildProfession.profession_id == profession_id))
        return result.scalars().first()

    @classmethod
    async def get_profession_detail_by_name(cls, db: AsyncSession, profession_name: str) -> GuildProfession | None:
        result = await db.execute(select(GuildProfession).where(GuildProfession.profession_name == profession_name))
        return result.scalars().first()

    @classmethod
    async def add_profession(cls, db: AsyncSession, profession: ProfessionModel) -> GuildProfession:
        db_profession = GuildProfession(**profession.model_dump(exclude_unset=True))
        db.add(db_profession)
        await db.flush()
        return db_profession

    @classmethod
    async def edit_profession(cls, db: AsyncSession, profession: dict) -> None:
        profession_id = profession.pop('profession_id')
        await db.execute(
            update(GuildProfession).where(GuildProfession.profession_id == profession_id).values(**profession)
        )
        await db.flush()

    @classmethod
    async def delete_profession(cls, db: AsyncSession, profession_id: int) -> None:
        await db.execute(delete(GuildProfession).where(GuildProfession.profession_id == profession_id))
        await db.flush()
