from collections import defaultdict
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.vo.user_vo import CurrentUserModel
from module_guild.dao.dashboard_dao import DashboardDao
from module_guild.entity.do.battle_do import GuildBattle, GuildBattleRecord
from module_guild.entity.do.battle_registration_do import GuildBattleInvite, GuildBattleRegistration
from module_guild.entity.do.join_application_do import GuildJoinApplication
from module_guild.entity.do.member_do import GuildMember
from module_guild.entity.do.schedule_do import GuildSchedule


class DashboardService:
    @classmethod
    async def get_summary_service(cls, db: AsyncSession, current_user: CurrentUserModel) -> dict:
        scope = cls._get_role_scope(current_user)
        user_id = current_user.user.user_id
        professions = await DashboardDao.list_enabled_professions(db)
        profession_names = [item.profession_name for item in professions]
        membership = await DashboardDao.get_active_member_by_user(db, user_id) if scope == 'user' else None

        owner_user_id = cls._get_owner_user_id(scope, user_id)
        guild = await cls._build_guild_payload(db, current_user, scope, membership)
        member_summary = await cls._build_member_summary(db, scope, owner_user_id, user_id, profession_names)
        class_distribution = await cls._build_class_distribution(db, owner_user_id, user_id if scope == 'user' else None, profession_names)
        battle_summary, latest_battles, latest_record_summary, top_records = await cls._build_battle_payload(
            db, scope, owner_user_id
        )
        review_summary = await cls._build_review_summary(db, scope, owner_user_id, user_id)
        schedule_summary = await cls._build_schedule_summary(db, scope, owner_user_id, membership)
        invite_owner_user_id = owner_user_id
        if scope == 'user' and membership:
            invite_owner_user_id = membership.user_id
        active_invite_summary = await cls._build_active_invite_summary(
            db, scope, invite_owner_user_id, profession_names
        )

        return {
            'scope': {
                'type': scope,
                'current_user_id': user_id,
                'owner_user_id': owner_user_id,
                'label': cls._scope_label(scope),
            },
            'guild': guild,
            'battle_summary': battle_summary,
            'latest_battles': latest_battles,
            'latest_battle_record_summary': latest_record_summary,
            'top_records': top_records,
            'member_summary': member_summary,
            'class_distribution': class_distribution,
            'review_summary': review_summary,
            'schedule_summary': schedule_summary,
            'active_invite_summary': active_invite_summary,
            'profession_options': [
                {
                    'profession_id': item.profession_id,
                    'profession_name': item.profession_name,
                    'order_num': item.order_num,
                    'status': item.status,
                }
                for item in professions
            ],
        }

    @classmethod
    def _get_role_scope(cls, current_user: CurrentUserModel) -> str:
        role_keys = {str(item).strip() for item in (current_user.roles or []) if str(item).strip()}
        if getattr(current_user.user, 'admin', False) or 'admin' in role_keys:
            return 'admin'
        if 'common' in role_keys:
            return 'common'
        return 'user'

    @classmethod
    def _get_owner_user_id(cls, scope: str, user_id: int) -> int | None:
        if scope == 'common':
            return user_id
        return None

    @classmethod
    def _scope_label(cls, scope: str) -> str:
        return {'admin': '全局数据', 'common': '当前帮会', 'user': '个人数据'}.get(scope, '个人数据')

    @classmethod
    def _to_int(cls, value: Any) -> int:
        return int(value or 0)

    @classmethod
    def _to_float(cls, value: Any) -> float:
        return float(value or 0)

    @classmethod
    async def _build_guild_payload(
        cls,
        db: AsyncSession,
        current_user: CurrentUserModel,
        scope: str,
        membership: GuildMember | None,
    ) -> dict:
        if scope == 'admin':
            return {
                'guild_id': None,
                'guild_name': '全局帮会数据',
                'owner_user_id': None,
                'guild_count': await DashboardDao.count_guild_owners(db),
            }

        if scope == 'common':
            return {
                'guild_id': current_user.user.user_id,
                'guild_name': current_user.user.nick_name or current_user.user.user_name or '',
                'owner_user_id': current_user.user.user_id,
                'guild_count': 1,
            }

        if not membership:
            return {
                'guild_id': None,
                'guild_name': '',
                'owner_user_id': None,
                'guild_count': 0,
                'membership': None,
            }

        guild_owner = await DashboardDao.get_guild_owner(db, membership.user_id)
        guild_name = guild_owner.nick_name if guild_owner else ''
        return {
            'guild_id': membership.guild_id,
            'guild_name': guild_name,
            'owner_user_id': membership.user_id,
            'guild_count': 1,
            'membership': cls._format_member(membership),
        }

    @classmethod
    async def _build_member_summary(
        cls,
        db: AsyncSession,
        scope: str,
        owner_user_id: int | None,
        current_user_id: int,
        profession_names: list[str],
    ) -> dict:
        member_user_id = current_user_id if scope == 'user' else None
        total_count = await DashboardDao.count_members(db, owner_user_id, member_user_id, active_only=False)
        active_count = await DashboardDao.count_members(db, owner_user_id, member_user_id, active_only=True)
        unmatched_count = await DashboardDao.count_unmatched_profession_members(
            db, profession_names, owner_user_id, member_user_id
        )
        return {
            'total_count': total_count,
            'active_count': active_count,
            'profession_count': len(profession_names),
            'unmatched_profession_count': unmatched_count,
        }

    @classmethod
    async def _build_class_distribution(
        cls,
        db: AsyncSession,
        owner_user_id: int | None,
        member_user_id: int | None,
        profession_names: list[str],
    ) -> list[dict]:
        rows = await DashboardDao.list_class_distribution(db, profession_names, owner_user_id, member_user_id)
        roster = await DashboardDao.list_member_roster_by_class(db, profession_names, owner_user_id, member_user_id)
        players_by_class = defaultdict(list)
        for member in roster:
            players_by_class[member.player_class or ''].append(
                {
                    'member_id': member.member_id,
                    'player_name': member.player_name,
                    'player_class': member.player_class or '',
                    'secondary_class': member.secondary_class or '',
                    'role_in_guild': member.role_in_guild or '',
                }
            )
        total = sum(cls._to_int(row.item_count) for row in rows)
        return [
            {
                'class_name': row.class_name,
                'count': cls._to_int(row.item_count),
                'percent': round((cls._to_float(row.item_count) / total) * 100, 1) if total else 0,
                'players': players_by_class.get(row.class_name or '', []),
            }
            for row in rows
        ]

    @classmethod
    async def _build_active_invite_summary(
        cls,
        db: AsyncSession,
        scope: str,
        owner_user_id: int | None,
        profession_names: list[str],
    ) -> dict | None:
        if scope == 'user' and owner_user_id is None:
            return None

        invite = await DashboardDao.get_latest_active_invite(db, owner_user_id)
        if not invite:
            return None

        registration_total = await DashboardDao.count_registrations_for_invite(db, invite.invite_id, 'signup')
        leave_total = await DashboardDao.count_registrations_for_invite(db, invite.invite_id, 'leave')
        registration_rows = await DashboardDao.list_registration_class_distribution(db, invite.invite_id, 'signup')
        leave_rows = await DashboardDao.list_registration_class_distribution(db, invite.invite_id, 'leave')
        registrations = await DashboardDao.list_registrations_for_invite(db, invite.invite_id, limit=12, registration_type='signup')
        leave_registrations = await DashboardDao.list_registrations_for_invite(
            db, invite.invite_id, limit=12, registration_type='leave'
        )
        registration_roster = await DashboardDao.list_registrations_for_invite(
            db, invite.invite_id, limit=500, registration_type='signup'
        )
        leave_roster = await DashboardDao.list_registrations_for_invite(
            db, invite.invite_id, limit=500, registration_type='leave'
        )
        join_applications = await DashboardDao.list_join_applications(db, guild_id=invite.owner_user_id)
        guild_class_distribution = await cls._build_class_distribution(
            db, invite.owner_user_id, None, profession_names
        )

        registration_class_distribution = cls._build_registration_class_distribution(
            registration_rows, registration_roster, registration_total
        )
        leave_class_distribution = cls._build_registration_class_distribution(leave_rows, leave_roster, leave_total)

        pending_join_count = sum(1 for item in join_applications if item.review_status == '0')
        return {
            **cls._format_invite(invite),
            'registration_count': registration_total,
            'leave_count': leave_total,
            'registration_class_distribution': registration_class_distribution,
            'leave_class_distribution': leave_class_distribution,
            'registrations': [cls._format_registration(item) for item in registrations],
            'leave_registrations': [cls._format_registration(item) for item in leave_registrations],
            'guild_class_distribution': guild_class_distribution,
            'join_application_count': len(join_applications),
            'pending_join_count': pending_join_count,
            'join_applications': [cls._format_application(item) for item in join_applications],
        }

    @classmethod
    def _build_registration_class_distribution(cls, rows: list, roster: list[GuildBattleRegistration], total: int) -> list[dict]:
        distribution = []
        players_by_class = defaultdict(list)
        for registration in roster:
            class_name = (registration.player_class or '').strip() or '未设置'
            players_by_class[class_name].append(
                {
                    'registration_id': registration.registration_id,
                    'player_name': registration.player_name,
                    'player_class': registration.player_class or '',
                    'approval_status': registration.approval_status,
                }
            )
        for row in rows:
            class_name = (row.class_name or '').strip()
            class_label = class_name or '未设置'
            distribution.append(
                {
                    'class_name': class_label,
                    'count': cls._to_int(row.item_count),
                    'percent': round((cls._to_float(row.item_count) / total) * 100, 1) if total else 0,
                    'players': players_by_class.get(class_label, []),
                }
            )
        return distribution

    @classmethod
    async def _build_battle_payload(cls, db: AsyncSession, scope: str, owner_user_id: int | None):
        if scope == 'user':
            empty_summary = {'total': 0, 'completed': 0, 'wins': 0, 'losses': 0, 'win_rate': 0}
            return empty_summary, [], None, []

        battle_summary = await DashboardDao.get_battle_summary(db, owner_user_id)
        battle_summary = {key: cls._to_int(value) for key, value in battle_summary.items()}
        battle_summary['win_rate'] = (
            round((battle_summary['wins'] / battle_summary['completed']) * 100, 1)
            if battle_summary['completed']
            else 0
        )

        battles = await DashboardDao.list_latest_battles(db, owner_user_id, limit=5)
        battle_ids = [battle.battle_id for battle in battles]
        record_rows = await DashboardDao.list_record_summaries(db, battle_ids)
        grouped_records = defaultdict(list)
        for row in record_rows:
            grouped_records[row.battle_id].append(cls._format_record_summary_row(row))

        latest_battles = []
        for battle in battles:
            summaries = grouped_records.get(battle.battle_id, [])
            latest_battles.append(cls._format_battle(battle, summaries))

        latest_battle = battles[0] if battles else None
        latest_record_summary = cls._pick_my_guild_summary(latest_battle, grouped_records.get(latest_battle.battle_id, [])) if latest_battle else None
        top_records = [
            cls._format_top_record(record)
            for record in await DashboardDao.list_top_records(db, latest_battle.battle_id if latest_battle else None)
        ]

        return battle_summary, latest_battles, latest_record_summary, top_records

    @classmethod
    async def _build_review_summary(
        cls,
        db: AsyncSession,
        scope: str,
        owner_user_id: int | None,
        current_user_id: int,
    ) -> dict:
        if scope == 'user':
            applications = await DashboardDao.list_my_applications(db, current_user_id)
            return {
                'pending_join_count': await DashboardDao.count_pending_join_applications(
                    db, applicant_user_id=current_user_id
                ),
                'pending_battle_registration_count': await DashboardDao.count_battle_registrations(
                    db, applicant_user_id=current_user_id, status='0'
                ),
                'my_applications': [cls._format_application(item) for item in applications],
            }

        return {
            'pending_join_count': await DashboardDao.count_pending_join_applications(db, guild_id=owner_user_id),
            'pending_battle_registration_count': await DashboardDao.count_battle_registrations(
                db, owner_user_id=owner_user_id, status='0'
            ),
            'my_applications': [],
        }

    @classmethod
    async def _build_schedule_summary(
        cls,
        db: AsyncSession,
        scope: str,
        owner_user_id: int | None,
        membership: GuildMember | None,
    ) -> dict:
        if scope == 'user':
            if not membership:
                return cls._empty_schedule_summary()
            schedules = await DashboardDao.list_active_schedules(db, membership.user_id, limit=1)
            if not schedules:
                return cls._empty_schedule_summary()
            schedule = schedules[0]
            assignment = await DashboardDao.get_member_schedule_assignment(db, schedule.schedule_id, membership.member_id)
            return {
                **cls._format_schedule_overview(schedule, {'team_count': 0, 'squad_count': 0, 'assignment_count': 0}),
                'active_schedule_count': 1,
                'my_assignment': cls._format_assignment(assignment),
            }

        schedules = await DashboardDao.list_active_schedules(db, owner_user_id, limit=20)
        schedule_ids = [item.schedule_id for item in schedules]
        counts = await DashboardDao.get_schedule_counts(db, schedule_ids)
        current = schedules[0] if schedules else None
        total_counts = {
            'team_count': sum(counts.get(item.schedule_id, {}).get('team_count', 0) for item in schedules),
            'squad_count': sum(counts.get(item.schedule_id, {}).get('squad_count', 0) for item in schedules),
            'assignment_count': sum(counts.get(item.schedule_id, {}).get('assignment_count', 0) for item in schedules),
        }
        return {
            **cls._format_schedule_overview(current, counts.get(current.schedule_id, {}) if current else {}),
            'active_schedule_count': len(schedules),
            'total_team_count': total_counts['team_count'],
            'total_squad_count': total_counts['squad_count'],
            'total_assignment_count': total_counts['assignment_count'],
            'my_assignment': None,
        }

    @classmethod
    def _empty_schedule_summary(cls) -> dict:
        return {
            'schedule_id': None,
            'schedule_name': '',
            'owner_user_id': None,
            'active_schedule_count': 0,
            'team_count': 0,
            'squad_count': 0,
            'assignment_count': 0,
            'total_team_count': 0,
            'total_squad_count': 0,
            'total_assignment_count': 0,
            'my_assignment': None,
        }

    @classmethod
    def _format_schedule_overview(cls, schedule: GuildSchedule | None, counts: dict) -> dict:
        if not schedule:
            return cls._empty_schedule_summary()
        return {
            'schedule_id': schedule.schedule_id,
            'schedule_name': schedule.schedule_name or '',
            'owner_user_id': schedule.user_id,
            'team_count': counts.get('team_count', 0),
            'squad_count': counts.get('squad_count', 0),
            'assignment_count': counts.get('assignment_count', 0),
        }

    @classmethod
    def _format_assignment(cls, row) -> dict | None:
        if not row:
            return None
        assignment = row[0]
        return {
            'assignment_id': assignment.assignment_id,
            'team_id': assignment.team_id,
            'team_name': row.team_name or '',
            'squad_id': assignment.squad_id,
            'squad_name': row.squad_name or '',
            'player_name': assignment.player_name,
            'player_class': assignment.player_class or '',
        }

    @classmethod
    def _format_member(cls, member: GuildMember) -> dict:
        return {
            'member_id': member.member_id,
            'guild_id': member.guild_id,
            'owner_user_id': member.user_id,
            'member_user_id': member.member_user_id,
            'player_name': member.player_name,
            'player_class': member.player_class or '',
            'secondary_class': member.secondary_class or '',
            'role_in_guild': member.role_in_guild or '',
            'join_time': member.join_time,
        }

    @classmethod
    def _format_battle(cls, battle: GuildBattle, record_summaries: list[dict]) -> dict:
        return {
            'battle_id': battle.battle_id,
            'battle_name': battle.battle_name or '',
            'battle_date': battle.battle_date or '',
            'battle_time': battle.battle_time,
            'my_guild_name': battle.my_guild_name or '',
            'opponent_name': battle.opponent_name or '',
            'battle_type': battle.battle_type or '',
            'battle_result': battle.battle_result or '',
            'status': battle.status or '0',
            'create_time': battle.create_time,
            'record_summaries': record_summaries,
            'my_guild_summary': cls._pick_my_guild_summary(battle, record_summaries),
        }

    @classmethod
    def _format_record_summary_row(cls, row) -> dict:
        return {
            'guild_name': row.guild_name or '',
            'participants': cls._to_int(row.participants),
            'kills': cls._to_int(row.kills),
            'assists': cls._to_int(row.assists),
            'resources': cls._to_int(row.resources),
            'damage': cls._to_int(row.damage),
            'healing': cls._to_int(row.healing),
            'deaths': cls._to_int(row.deaths),
            'revives': cls._to_int(row.revives),
        }

    @classmethod
    def _pick_my_guild_summary(cls, battle: GuildBattle, summaries: list[dict]) -> dict | None:
        if not summaries:
            return None
        if battle.my_guild_name:
            for item in summaries:
                if item['guild_name'] == battle.my_guild_name:
                    return item
        return summaries[0]

    @classmethod
    def _format_top_record(cls, record: GuildBattleRecord) -> dict:
        return {
            'record_id': record.record_id,
            'battle_id': record.battle_id,
            'guild_name': record.guild_name or '',
            'player_name': record.player_name,
            'player_class': record.player_class or '',
            'kills': cls._to_int(record.kills),
            'assists': cls._to_int(record.assists),
            'resources': cls._to_int(record.resources),
            'damage': cls._to_int(record.dmg_to_players),
            'healing': cls._to_int(record.healing),
            'deaths': cls._to_int(record.deaths),
            'revives': cls._to_int(record.revives),
        }

    @classmethod
    def _format_application(cls, application: GuildJoinApplication) -> dict:
        return {
            'application_id': application.application_id,
            'guild_id': application.guild_id,
            'guild_name': application.guild_name,
            'player_name': application.player_name,
            'player_class': application.player_class or '',
            'review_status': application.review_status,
            'apply_time': application.apply_time,
            'review_time': application.review_time,
            'remark': application.remark or '',
        }

    @classmethod
    def _format_invite(cls, invite: GuildBattleInvite) -> dict:
        expired = invite.expire_time < datetime.now()
        return {
            'invite_id': invite.invite_id,
            'invite_code': invite.invite_code,
            'owner_user_id': invite.owner_user_id,
            'guild_name': invite.guild_name or '',
            'battle_name': invite.battle_name or '',
            'battle_time': invite.battle_time,
            'expire_time': invite.expire_time,
            'status': '1' if expired else invite.status,
            'expired': expired,
            'remark': invite.remark or '',
            'create_time': invite.create_time,
            'public_path': f'/public/battle/{invite.invite_code}',
        }

    @classmethod
    def _format_registration(cls, item: GuildBattleRegistration) -> dict:
        return {
            'registration_id': item.registration_id,
            'invite_id': item.invite_id,
            'invite_code': item.invite_code or '',
            'guild_id': item.guild_id,
            'owner_user_id': item.owner_user_id,
            'member_id': item.member_id,
            'registration_type': item.registration_type or 'signup',
            'player_name': item.player_name,
            'player_class': item.player_class or '',
            'secondary_class': item.secondary_class or '',
            'role_in_guild': item.role_in_guild or '',
            'applicant_name': item.applicant_name or '',
            'applicant_contact': item.applicant_contact or '',
            'apply_time': item.apply_time,
            'approval_status': item.approval_status,
            'approval_time': item.approval_time,
            'approval_by': item.approval_by or '',
            'approval_comment': item.approval_comment or '',
            'remark': item.remark or '',
        }

    @classmethod
    def _format_datetime(cls, value: datetime | None) -> Any:
        return value
