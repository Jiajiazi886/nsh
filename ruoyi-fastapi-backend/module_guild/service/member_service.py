from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_guild.dao.battle_dao import BattleDao
from module_guild.dao.member_dao import MemberDao
from module_guild.entity.vo.member_vo import (
    MemberBatchDeleteModel,
    MemberCreateModel,
    MemberEditModel,
    MemberImportModel,
    MemberProfileEditModel,
)


class MemberService:
    @classmethod
    async def query_member_list_service(cls, db: AsyncSession, current_user: CurrentUserModel) -> list:
        user_id = current_user.user.user_id
        members = await MemberDao.query_member_list(db, user_id)
        return [
            {
                'member_id': m.member_id,
                'guild_id': m.guild_id,
                'user_id': m.user_id,
                'member_user_id': m.member_user_id,
                'player_name': m.player_name,
                'player_class': m.player_class or '',
                'secondary_class': m.secondary_class or '',
                'role_in_guild': m.role_in_guild,
                'is_active': m.is_active,
                'source_type': m.source_type or 'manual',
                'join_time': m.join_time,
                'remark': m.remark or '',
                'team_id': m.team_id,
                'squad_number': m.squad_number,
            }
            for m in members
        ]

    @classmethod
    async def get_my_profile_service(cls, db: AsyncSession, current_user: CurrentUserModel) -> dict | None:
        user_id = current_user.user.user_id
        member = await MemberDao.get_active_member_profile_by_user(db, user_id)
        if not member:
            return None

        guild_name = ''
        try:
            from module_guild.dao.join_application_dao import JoinApplicationDao

            guild_user = await JoinApplicationDao.get_guild_by_id(db, member.user_id)
            guild_name = guild_user.nick_name if guild_user else ''
        except Exception:
            guild_name = ''

        return {
            'member_id': member.member_id,
            'guild_id': member.guild_id,
            'guild_name': guild_name,
            'guild_owner_user_id': member.user_id,
            'member_user_id': member.member_user_id,
            'player_name': member.player_name,
            'player_class': member.player_class or '',
            'secondary_class': member.secondary_class or '',
            'remark': member.remark or '',
            'role_in_guild': member.role_in_guild or '',
            'source_type': member.source_type or '',
            'join_time': member.join_time,
        }

    @classmethod
    async def update_my_profile_service(
        cls, db: AsyncSession, current_user: CurrentUserModel, data: MemberProfileEditModel
    ) -> CrudResponseModel:
        user_id = current_user.user.user_id
        member = await MemberDao.get_active_member_profile_by_user(db, user_id)
        if not member:
            raise ServiceException(message='当前账号还不是任何帮会的有效成员，无法修改个人帮会信息')

        update_dict = {}
        if data.player_class is not None:
            update_dict['player_class'] = data.player_class.strip()
        if data.secondary_class is not None:
            update_dict['secondary_class'] = data.secondary_class.strip()
        if data.remark is not None:
            update_dict['remark'] = data.remark.strip()

        if not update_dict:
            return CrudResponseModel(is_success=True, message='没有需要修改的内容')

        await MemberDao.update_member(db, member.member_id, update_dict)
        await db.commit()
        return CrudResponseModel(is_success=True, message='个人信息保存成功')

    @classmethod
    async def create_member_service(
        cls, db: AsyncSession, current_user: CurrentUserModel, data: MemberCreateModel
    ) -> CrudResponseModel:
        user_id = current_user.user.user_id
        exists = await MemberDao.check_member_exists(db, user_id, data.player_name)
        if exists:
            raise ServiceException(message=f'玩家 {data.player_name} 已存在')
        await MemberDao.create_member(db, {
            'guild_id': user_id,
            'user_id': user_id,
            'member_user_id': 0,
            'player_name': data.player_name,
            'player_class': data.player_class or '',
            'secondary_class': data.secondary_class or '',
            'is_active': '1',
            'source_type': 'manual',
            'remark': data.remark or '',
        })
        await db.commit()
        return CrudResponseModel(is_success=True, message='添加成功')

    @classmethod
    async def edit_member_service(
        cls, db: AsyncSession, current_user: CurrentUserModel, data: MemberEditModel
    ) -> CrudResponseModel:
        user_id = current_user.user.user_id
        member = await MemberDao.get_member_by_id(db, data.member_id)
        if not member:
            raise ServiceException(message='成员不存在')
        if member.user_id != user_id:
            raise ServiceException(message='无权修改该成员')
        update_dict = {}
        if data.player_class is not None:
            update_dict['player_class'] = data.player_class
        if data.secondary_class is not None:
            update_dict['secondary_class'] = data.secondary_class
        if data.remark is not None:
            update_dict['remark'] = data.remark
        if data.team_id is not None:
            if data.team_id == 0:
                update_dict['team_id'] = None
                update_dict['squad_number'] = None
            else:
                update_dict['team_id'] = data.team_id
        if data.squad_number is not None:
            update_dict['squad_number'] = data.squad_number
        await MemberDao.update_member(db, data.member_id, update_dict)
        await db.commit()
        return CrudResponseModel(is_success=True, message='保存成功')

    @classmethod
    async def batch_delete_service(
        cls, db: AsyncSession, current_user: CurrentUserModel, data: MemberBatchDeleteModel
    ) -> CrudResponseModel:
        if not data.member_ids:
            raise ServiceException(message='请选择要删除的成员')
        user_id = current_user.user.user_id
        count = await MemberDao.batch_delete_members(db, user_id, data.member_ids)
        await db.commit()
        return CrudResponseModel(is_success=True, message=f'成功删除 {count} 条成员')

    @classmethod
    async def import_from_battle_service(
        cls, db: AsyncSession, current_user: CurrentUserModel, data: MemberImportModel
    ) -> CrudResponseModel:
        user_id = current_user.user.user_id
        records = await MemberDao.get_battle_records_by_guild(db, data.battle_id, data.guild_name)
        if not records:
            raise ServiceException(message='该帮会没有战斗记录')

        imported = 0
        skipped = 0
        for row in records:
            player_name = row[0]
            player_class = row[1]
            exists = await MemberDao.check_member_exists(db, user_id, player_name)
            if exists:
                skipped += 1
                continue
            await MemberDao.batch_insert_members(db, [{
                'guild_id': user_id,
                'user_id': user_id,
                'member_user_id': 0,
                'player_name': player_name,
                'player_class': player_class or '',
                'is_active': '1',
                'source_type': 'import',
            }])
            imported += 1
        await db.commit()

        msg = f'成功导入 {imported} 条成员'
        if skipped > 0:
            msg += f'，跳过 {skipped} 条已存在'
        return CrudResponseModel(is_success=True, message=msg)

    @classmethod
    async def get_battle_list_for_import_service(cls, db: AsyncSession, current_user: CurrentUserModel) -> list:
        user_id = current_user.user.user_id
        result = await BattleDao.query_battle_list(db, user_id, 1, 9999)
        return [{'battle_id': b.battle_id, 'battle_name': b.battle_name} for b in result['rows']]

    @classmethod
    async def get_guild_names_for_battle_service(
        cls, db: AsyncSession, current_user: CurrentUserModel, battle_id: int
    ) -> list[str]:
        user_id = current_user.user.user_id
        return await MemberDao.get_battle_guild_names(db, user_id, battle_id)
