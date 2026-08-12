from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.dao.pvp_defense_profession_bonus_dao import PvpDefenseProfessionBonusDao
from module_admin.entity.do.pvp_defense_profession_bonus_do import SystemPvpDefenseProfessionBonus
from module_admin.entity.vo.pvp_defense_profession_bonus_vo import ProfessionBonusModel, ProfessionBonusUpdateModel
from module_guild.dao.profession_dao import ProfessionDao


class PvpDefenseProfessionBonusService:
    @classmethod
    async def list_services(cls, db: AsyncSession) -> list[ProfessionBonusModel]:
        professions = await ProfessionDao.get_enabled_profession_list(db)
        bonuses = {item.profession_id: item for item in await PvpDefenseProfessionBonusDao.list_all(db)}
        result = []
        for profession in professions:
            configured = bonuses.get(profession.profession_id)
            defense_default = 20 if profession.profession_name == '铁衣' else 0
            hp_default = 40 if profession.profession_name == '铁衣' else 0
            result.append(ProfessionBonusModel(
                professionId=profession.profession_id,
                professionName=profession.profession_name,
                orderNum=profession.order_num or 0,
                defenseBonusPct=configured.defense_bonus_pct if configured else defense_default,
                hpBonusPct=configured.hp_bonus_pct if configured else hp_default,
                updateBy=configured.update_by if configured else '',
                updateTime=configured.update_time if configured else None,
            ))
        return result

    @classmethod
    async def update_services(
        cls,
        db: AsyncSession,
        profession_id: int,
        payload: ProfessionBonusUpdateModel,
        operator: str,
    ) -> CrudResponseModel:
        profession = await ProfessionDao.get_profession_detail_by_id(db, profession_id)
        if profession is None:
            raise ServiceException(message='职业不存在')
        await PvpDefenseProfessionBonusDao.upsert(db, SystemPvpDefenseProfessionBonus(
            profession_id=profession_id,
            defense_bonus_pct=payload.defense_bonus_pct,
            hp_bonus_pct=payload.hp_bonus_pct,
            update_by=operator,
            update_time=datetime.now(),
        ))
        await db.commit()
        return CrudResponseModel(is_success=True, message='职业加成已保存')
