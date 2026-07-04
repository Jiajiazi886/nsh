from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.internal_power_panel_setting_do import PersonalInternalPowerPanelSetting


class InternalPowerPanelSettingDao:
    """
    个人内功PVP收益面板设置数据库操作层
    """

    @classmethod
    async def get_setting(cls, db: AsyncSession, user_id: int) -> PersonalInternalPowerPanelSetting | None:
        result = await db.execute(
            select(PersonalInternalPowerPanelSetting).where(PersonalInternalPowerPanelSetting.user_id == user_id)
        )
        return result.scalars().first()

    @classmethod
    async def upsert_setting(cls, db: AsyncSession, setting: PersonalInternalPowerPanelSetting) -> None:
        await db.merge(setting)
        await db.flush()
