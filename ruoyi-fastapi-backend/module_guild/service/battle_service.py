from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_guild.dao.battle_dao import BattleDao
from module_guild.entity.vo.battle_vo import BattleImportModel


class BattleService:
    @classmethod
    async def import_battle_service(
        cls, db: AsyncSession, current_user, import_data: BattleImportModel
    ) -> CrudResponseModel:
        if not import_data.records:
            raise ServiceException(message='请至少上传一条数据')

        user_id = current_user.user.user_id

        battle_dict = {
            'battle_name': import_data.csv_filename or f"{import_data.battle_date}_{current_user.user.user_name}_{import_data.opponent_name or '未知'}",
            'battle_date': import_data.battle_date,
            'battle_type': import_data.battle_type,
            'battle_result': import_data.battle_result,
            'opponent_name': import_data.opponent_name,
            'initiator_guild_id': 1,
            'user_id': user_id,
            'my_guild_name': import_data.my_guild_name or '',
            'status': '2',
            'remark': import_data.remark,
        }
        battle_id = await BattleDao.create_battle(db, battle_dict)

        records = []
        for item in import_data.records:
            records.append({
                'battle_id': battle_id,
                'guild_id': 1,
                'battle_date': import_data.battle_date,
                'guild_name': item.guild_name,
                'player_name': item.player_name,
                'player_class': item.player_class,
                'kills': item.kills,
                'qingquan_kills': item.qingquan_kills,
                'assists': item.assists,
                'resources': item.resources,
                'dmg_to_players': item.dmg_to_players,
                'armor_break_players': item.armor_break_players,
                'dmg_to_buildings': item.dmg_to_buildings,
                'armor_break_buildings': item.armor_break_buildings,
                'healing': item.healing,
                'dmg_taken': item.dmg_taken,
                'deaths': item.deaths,
                'revives': item.revives,
                'burn_bones': item.burn_bones,
            })
        await BattleDao.batch_create_records(db, records)
        await db.commit()

        return CrudResponseModel(is_success=True, message=f'导入成功，共 {len(records)} 条记录')

    @classmethod
    async def query_history_service(cls, db: AsyncSession, current_user, page: int = 1, size: int = 10) -> dict:
        user_id = current_user.user.user_id
        result = await BattleDao.query_battle_list(db, user_id, page, size)
        guild_names = await BattleDao.get_distinct_guild_names(db, user_id)
        rows = []
        for b in result['rows']:
            rows.append({
                'battle_id': b.battle_id,
                'battle_name': b.battle_name,
                'battle_date': b.battle_date,
                'battle_type': b.battle_type,
                'battle_result': b.battle_result,
                'opponent_name': b.opponent_name,
                'status': b.status,
                'remark': b.remark,
                'my_guild_name': b.my_guild_name or '',
                'create_time': str(b.create_time) if b.create_time else '',
            })
        return {'rows': rows, 'total': result['total'], 'guild_names': guild_names}

    @classmethod
    async def query_records_service(cls, db: AsyncSession, battle_id: int) -> list:
        records = await BattleDao.query_battle_records(db, battle_id)
        return [
            {
                'record_id': r.record_id,
                'guild_name': r.guild_name,
                'player_name': r.player_name,
                'player_class': r.player_class,
                'kills': r.kills,
                'qingquan_kills': r.qingquan_kills,
                'assists': r.assists,
                'resources': r.resources,
                'dmg_to_players': r.dmg_to_players,
                'armor_break_players': r.armor_break_players,
                'dmg_to_buildings': r.dmg_to_buildings,
                'armor_break_buildings': r.armor_break_buildings,
                'healing': r.healing,
                'dmg_taken': r.dmg_taken,
                'deaths': r.deaths,
                'revives': r.revives,
                'burn_bones': r.burn_bones,
            }
            for r in records
        ]

    @classmethod
    async def soft_delete_service(cls, db: AsyncSession, current_user, battle_id: int) -> CrudResponseModel:
        user_id = current_user.user.user_id
        battle = await BattleDao.get_battle_by_id(db, battle_id)
        if not battle:
            raise ServiceException(message='记录不存在')
        if battle.user_id != user_id:
            raise ServiceException(message='无权删除该记录')
        await BattleDao.soft_delete_battle(db, battle_id)
        await db.commit()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def check_duplicate_filename_service(cls, db: AsyncSession, current_user, filename: str) -> dict:
        exists = await BattleDao.check_filename_exists(db, current_user.user.user_id, filename)
        return {'exists': exists}