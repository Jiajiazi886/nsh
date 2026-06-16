import json

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_guild.dao.schedule_dao import ScheduleDao
from module_guild.entity.do.schedule_do import GuildSchedule, GuildScheduleTeam
from module_guild.entity.vo.schedule_vo import (
    ScheduleAssignmentModel,
    ScheduleHistoryRenameModel,
    ScheduleSnapshotModel,
    ScheduleSquadCreateModel,
    ScheduleTeamCreateModel,
    ScheduleWorkbookModel,
)


class ScheduleService:
    @classmethod
    async def get_current_schedule_service(cls, db: AsyncSession, current_user) -> dict:
        schedule = await cls._ensure_active_schedule(db, current_user.user.user_id)
        schedule_id = schedule.schedule_id
        await db.commit()
        return await cls._build_schedule_detail(db, current_user.user.user_id, schedule_id)

    @classmethod
    async def get_schedule_detail_service(cls, db: AsyncSession, current_user, schedule_id: int) -> dict:
        schedule = await ScheduleDao.get_schedule_by_id(db, current_user.user.user_id, schedule_id)
        if not schedule:
            raise ServiceException(message='排表不存在')
        return await cls._build_schedule_detail(db, current_user.user.user_id, schedule_id)

    @classmethod
    async def get_current_workbook_service(cls, db: AsyncSession, current_user) -> dict:
        schedule = await cls._ensure_active_schedule(db, current_user.user.user_id)
        schedule_id = schedule.schedule_id
        workbook = await ScheduleDao.get_workbook(db, schedule_id)
        if not workbook:
            await db.commit()
            return {'schedule_id': schedule_id, 'workbook': None}
        try:
            workbook_data = json.loads(workbook.workbook_json or '{}')
        except json.JSONDecodeError:
            workbook_data = None
        await db.commit()
        return {'schedule_id': schedule_id, 'workbook': workbook_data}

    @classmethod
    async def save_current_workbook_service(
        cls, db: AsyncSession, current_user, data: ScheduleWorkbookModel
    ) -> CrudResponseModel:
        schedule = await cls._ensure_active_schedule(db, current_user.user.user_id)
        schedule_id = schedule.schedule_id
        await ScheduleDao.upsert_workbook(
            db,
            schedule_id,
            json.dumps(data.workbook or {}, ensure_ascii=False, separators=(',', ':')),
        )
        await db.commit()
        return CrudResponseModel(is_success=True, message='表格已保存')

    @classmethod
    async def list_history_service(cls, db: AsyncSession, current_user) -> list[dict]:
        rows = await ScheduleDao.list_history(db, current_user.user.user_id)
        return [
            {
                'schedule_id': item.schedule_id,
                'schedule_name': item.schedule_name,
                'source_schedule_id': item.source_schedule_id,
                'create_time': str(item.create_time) if item.create_time else '',
            }
            for item in rows
        ]

    @classmethod
    async def rename_history_service(
        cls, db: AsyncSession, current_user, schedule_id: int, data: ScheduleHistoryRenameModel
    ) -> CrudResponseModel:
        schedule_name = data.schedule_name.strip()
        if not schedule_name:
            raise ServiceException(message='请输入历史名称')
        schedule = await ScheduleDao.get_schedule_by_id(db, current_user.user.user_id, schedule_id)
        if not schedule:
            raise ServiceException(message='历史排表不存在')
        if schedule.is_active == '1':
            raise ServiceException(message='当前排表不能作为历史重命名')
        await ScheduleDao.update_schedule_name(db, schedule_id, schedule_name)
        await db.commit()
        return CrudResponseModel(is_success=True, message='历史名称已更新')

    @classmethod
    async def delete_history_service(cls, db: AsyncSession, current_user, schedule_id: int) -> CrudResponseModel:
        schedule = await ScheduleDao.get_schedule_by_id(db, current_user.user.user_id, schedule_id)
        if not schedule:
            raise ServiceException(message='历史排表不存在')
        if schedule.is_active == '1':
            raise ServiceException(message='当前排表不能删除')
        await ScheduleDao.delete_history_schedule(db, schedule_id)
        await db.commit()
        return CrudResponseModel(is_success=True, message='历史排表已删除')

    @classmethod
    async def create_team_service(
        cls, db: AsyncSession, current_user, data: ScheduleTeamCreateModel
    ) -> CrudResponseModel:
        user_id = current_user.user.user_id
        schedule = await cls._ensure_active_schedule(db, user_id)
        team_name = data.team_name.strip()
        if not team_name:
            raise ServiceException(message='请输入团队名称')

        teams = await ScheduleDao.list_schedule_teams(db, schedule.schedule_id)
        if any(team.team_name == team_name for team in teams):
            raise ServiceException(message=f'团队 {team_name} 已存在')
        await ScheduleDao.create_team(db, {
            'schedule_id': schedule.schedule_id,
            'team_name': team_name,
            'order_num': len(teams) + 1,
        })
        await db.commit()
        return CrudResponseModel(is_success=True, message='团队创建成功')

    @classmethod
    async def create_squad_service(
        cls, db: AsyncSession, current_user, team_id: int, data: ScheduleSquadCreateModel
    ) -> CrudResponseModel:
        user_id = current_user.user.user_id
        schedule = await cls._ensure_active_schedule(db, user_id)
        team = await cls._get_owned_team(db, schedule, team_id)
        squad_count = await ScheduleDao.count_squads(db, team.team_id)
        squad_name = (data.squad_name or f'第 {squad_count + 1} 小队').strip()
        if not squad_name:
            raise ServiceException(message='请输入小队名称')
        await ScheduleDao.create_squad(db, {
            'team_id': team.team_id,
            'squad_name': squad_name,
            'max_members': 6,
            'order_num': squad_count + 1,
        })
        await db.commit()
        return CrudResponseModel(is_success=True, message='小队创建成功')

    @classmethod
    async def delete_team_service(cls, db: AsyncSession, current_user, team_id: int) -> CrudResponseModel:
        user_id = current_user.user.user_id
        schedule = await cls._ensure_active_schedule(db, user_id)
        team = await cls._get_owned_team(db, schedule, team_id)
        await ScheduleDao.delete_team(db, schedule.schedule_id, team.team_id)
        await db.commit()
        return CrudResponseModel(is_success=True, message='团队删除成功')

    @classmethod
    async def delete_squad_service(cls, db: AsyncSession, current_user, team_id: int, squad_id: int) -> CrudResponseModel:
        user_id = current_user.user.user_id
        schedule = await cls._ensure_active_schedule(db, user_id)
        team = await cls._get_owned_team(db, schedule, team_id)
        squad = await ScheduleDao.get_squad(db, squad_id)
        if not squad or squad.team_id != team.team_id:
            raise ServiceException(message='小队不存在')
        await ScheduleDao.delete_squad(db, team.team_id, squad.squad_id)
        await db.commit()
        return CrudResponseModel(is_success=True, message='小队删除成功')

    @classmethod
    async def assign_member_service(
        cls, db: AsyncSession, current_user, data: ScheduleAssignmentModel
    ) -> CrudResponseModel:
        user_id = current_user.user.user_id
        schedule = await cls._ensure_active_schedule(db, user_id)
        team = await cls._get_owned_team(db, schedule, data.team_id)
        squad = await ScheduleDao.get_squad(db, data.squad_id)
        if not squad or squad.team_id != team.team_id:
            raise ServiceException(message='小队不存在')
        member = await ScheduleDao.get_member(db, user_id, data.member_id)
        if not member:
            raise ServiceException(message='成员不存在')

        current_assignment = await ScheduleDao.get_assignment_by_member(db, schedule.schedule_id, member.member_id)
        current_size = await ScheduleDao.count_squad_assignments(
            db, squad.squad_id, exclude_member_id=member.member_id
        )
        requested_order_num = data.order_num or current_size + 1
        if requested_order_num < 1 or requested_order_num > squad.max_members:
            raise ServiceException(message=f'位置必须在 1-{squad.max_members} 之间')

        target_assignment = await ScheduleDao.get_assignment_by_slot(
            db, schedule.schedule_id, squad.squad_id, requested_order_num
        )
        if target_assignment and target_assignment.member_id != member.member_id and not current_assignment:
            raise ServiceException(message='目标位置已有成员')
        if current_size >= squad.max_members and not current_assignment and not target_assignment:
            raise ServiceException(message='每个小队最多 6 人')

        if target_assignment and target_assignment.member_id != member.member_id and current_assignment:
            await ScheduleDao.update_assignment_slot(
                db,
                target_assignment.assignment_id,
                current_assignment.team_id,
                current_assignment.squad_id,
                current_assignment.order_num,
            )

        await ScheduleDao.upsert_assignment(db, {
            'schedule_id': schedule.schedule_id,
            'team_id': team.team_id,
            'squad_id': squad.squad_id,
            'member_id': member.member_id,
            'player_name': member.player_name,
            'player_class': member.player_class or '',
            'secondary_class': member.secondary_class or '',
            'order_num': requested_order_num,
        })
        await db.commit()
        return CrudResponseModel(is_success=True, message='排表已保存')

    @classmethod
    async def clear_assignment_service(cls, db: AsyncSession, current_user, member_id: int) -> CrudResponseModel:
        schedule = await cls._ensure_active_schedule(db, current_user.user.user_id)
        await ScheduleDao.clear_assignment(db, schedule.schedule_id, member_id)
        await db.commit()
        return CrudResponseModel(is_success=True, message='已移出排表')

    @classmethod
    async def create_snapshot_service(
        cls, db: AsyncSession, current_user, data: ScheduleSnapshotModel
    ) -> CrudResponseModel:
        user_id = current_user.user.user_id
        source = await cls._ensure_active_schedule(db, user_id)
        schedule_name = data.schedule_name.strip()
        if not schedule_name:
            raise ServiceException(message='请输入历史名称')

        snapshot = await ScheduleDao.create_schedule(db, {
            'schedule_name': schedule_name,
            'user_id': user_id,
            'is_active': '0',
            'source_schedule_id': source.schedule_id,
        })
        team_id_map: dict[int, int] = {}
        squad_id_map: dict[int, int] = {}
        source_teams = await ScheduleDao.list_schedule_teams(db, source.schedule_id)
        for team in source_teams:
            new_team = await ScheduleDao.create_team(db, {
                'schedule_id': snapshot.schedule_id,
                'team_name': team.team_name,
                'order_num': team.order_num,
            })
            team_id_map[team.team_id] = new_team.team_id

        source_squads = await ScheduleDao.list_schedule_squads(db, list(team_id_map.keys()))
        for squad in source_squads:
            new_squad = await ScheduleDao.create_squad(db, {
                'team_id': team_id_map[squad.team_id],
                'squad_name': squad.squad_name,
                'max_members': squad.max_members,
                'order_num': squad.order_num,
            })
            squad_id_map[squad.squad_id] = new_squad.squad_id

        source_assignments = await ScheduleDao.list_schedule_assignments(db, source.schedule_id)
        for item in source_assignments:
            if item.team_id in team_id_map and item.squad_id in squad_id_map:
                await ScheduleDao.upsert_assignment(db, {
                    'schedule_id': snapshot.schedule_id,
                    'team_id': team_id_map[item.team_id],
                    'squad_id': squad_id_map[item.squad_id],
                    'member_id': item.member_id,
                    'player_name': item.player_name,
                    'player_class': item.player_class or '',
                    'secondary_class': item.secondary_class or '',
                    'order_num': item.order_num,
                })
        await ScheduleDao.copy_workbook(db, source.schedule_id, snapshot.schedule_id)
        await db.commit()
        return CrudResponseModel(is_success=True, message='历史已保存')

    @classmethod
    async def apply_history_service(cls, db: AsyncSession, current_user, schedule_id: int) -> CrudResponseModel:
        user_id = current_user.user.user_id
        source = await ScheduleDao.get_schedule_by_id(db, user_id, schedule_id)
        if not source:
            raise ServiceException(message='历史排表不存在')
        if source.is_active == '1':
            raise ServiceException(message='请选择历史排表')

        active = await cls._ensure_active_schedule(db, user_id)
        await ScheduleDao.clear_schedule_structure(db, active.schedule_id)

        team_id_map: dict[int, int] = {}
        squad_id_map: dict[int, int] = {}
        source_teams = await ScheduleDao.list_schedule_teams(db, source.schedule_id)
        for team in source_teams:
            new_team = await ScheduleDao.create_team(db, {
                'schedule_id': active.schedule_id,
                'team_name': team.team_name,
                'order_num': team.order_num,
            })
            team_id_map[team.team_id] = new_team.team_id

        source_squads = await ScheduleDao.list_schedule_squads(db, list(team_id_map.keys()))
        for squad in source_squads:
            new_squad = await ScheduleDao.create_squad(db, {
                'team_id': team_id_map[squad.team_id],
                'squad_name': squad.squad_name,
                'max_members': squad.max_members,
                'order_num': squad.order_num,
            })
            squad_id_map[squad.squad_id] = new_squad.squad_id

        source_assignments = await ScheduleDao.list_schedule_assignments(db, source.schedule_id)
        for item in source_assignments:
            if item.team_id in team_id_map and item.squad_id in squad_id_map:
                await ScheduleDao.upsert_assignment(db, {
                    'schedule_id': active.schedule_id,
                    'team_id': team_id_map[item.team_id],
                    'squad_id': squad_id_map[item.squad_id],
                    'member_id': item.member_id,
                    'player_name': item.player_name,
                    'player_class': item.player_class or '',
                    'secondary_class': item.secondary_class or '',
                    'order_num': item.order_num,
                })
        await ScheduleDao.copy_workbook(db, source.schedule_id, active.schedule_id)
        await db.commit()
        return CrudResponseModel(is_success=True, message='历史配置已应用')

    @classmethod
    async def _ensure_active_schedule(cls, db: AsyncSession, user_id: int) -> GuildSchedule:
        schedule = await ScheduleDao.get_active_schedule(db, user_id)
        if schedule:
            return schedule

        schedule = await ScheduleDao.create_schedule(db, {
            'schedule_name': '当前约战排表',
            'user_id': user_id,
            'is_active': '1',
        })
        return schedule

    @classmethod
    async def _get_owned_team(cls, db: AsyncSession, schedule: GuildSchedule, team_id: int) -> GuildScheduleTeam:
        team = await ScheduleDao.get_team(db, team_id)
        if not team or team.schedule_id != schedule.schedule_id:
            raise ServiceException(message='团队不存在')
        return team

    @classmethod
    async def _build_schedule_detail(cls, db: AsyncSession, user_id: int, schedule_id: int) -> dict:
        schedule = await ScheduleDao.get_schedule_by_id(db, user_id, schedule_id)
        if not schedule:
            raise ServiceException(message='排表不存在')

        teams = await ScheduleDao.list_schedule_teams(db, schedule_id)
        squads = await ScheduleDao.list_schedule_squads(db, [team.team_id for team in teams])
        assignments = await ScheduleDao.list_schedule_assignments(db, schedule_id)
        assignment_map: dict[int, list[dict]] = {}
        for item in assignments:
            assignment_map.setdefault(item.squad_id, []).append({
                'assignment_id': item.assignment_id,
                'member_id': item.member_id,
                'player_name': item.player_name,
                'player_class': item.player_class or '',
                'secondary_class': item.secondary_class or '',
                'order_num': item.order_num,
            })

        squad_map: dict[int, list[dict]] = {}
        for squad in squads:
            squad_map.setdefault(squad.team_id, []).append({
                'squad_id': squad.squad_id,
                'squad_name': squad.squad_name,
                'max_members': squad.max_members,
                'order_num': squad.order_num,
                'members': assignment_map.get(squad.squad_id, []),
            })

        return {
            'schedule_id': schedule.schedule_id,
            'schedule_name': schedule.schedule_name,
            'is_active': schedule.is_active,
            'create_time': str(schedule.create_time) if schedule.create_time else '',
            'teams': [
                {
                    'team_id': team.team_id,
                    'team_name': team.team_name,
                    'order_num': team.order_num,
                    'squads': squad_map.get(team.team_id, []),
                }
                for team in teams
            ],
        }
