from sqlalchemy.ext.asyncio import AsyncSession
from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_guild.dao.team_dao import TeamDao
from module_guild.entity.vo.team_vo import TeamCreateModel
from utils.log_util import logger

class TeamService:
    @classmethod
    async def list_teams_service(cls, db: AsyncSession, current_user) -> list:
        user_id = current_user.user.user_id
        teams = await TeamDao.query_teams_by_user(db, user_id)
        return [
            {
                'id': t.id,
                'team_name': t.team_name,
                'team_type': t.team_type,
                'user_id': t.user_id,
                'create_time': t.create_time,
                'update_time': t.update_time,
            }
            for t in teams
        ]

    @classmethod
    async def create_team_service(cls, db: AsyncSession, current_user, data: TeamCreateModel) -> CrudResponseModel:
        user_id = current_user.user.user_id
        team_type = data.team_type or ''
        teams = await TeamDao.query_teams_by_user(db, user_id)
        for t in teams:
            if t.team_name == data.team_name:
                raise ServiceException(message=f'团队 {data.team_name} 已存在')
        await TeamDao.create_team(db, {
            'team_name': data.team_name,
            'team_type': team_type,
            'user_id': user_id,
        })
        await db.commit()
        return CrudResponseModel(is_success=True, message='创建成功')

    @classmethod
    async def delete_team_service(cls, db: AsyncSession, current_user, team_id: int) -> CrudResponseModel:
        user_id = current_user.user.user_id
        await TeamDao.clear_team_members(db, team_id)
        await TeamDao.delete_team(db, user_id, team_id)
        await db.commit()
        return CrudResponseModel(is_success=True, message='删除成功')