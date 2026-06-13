from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_guild.dao.battle_dao import BattleDao
from module_guild.service.schedule_service import ScheduleService


class AnalysisService:
    NUMERIC_FIELDS = [
        'kills',
        'qingquan_kills',
        'assists',
        'resources',
        'dmg_to_players',
        'armor_break_players',
        'dmg_to_buildings',
        'armor_break_buildings',
        'healing',
        'dmg_taken',
        'deaths',
        'revives',
        'burn_bones',
    ]

    @classmethod
    async def query_schedule_battle_analysis_service(
        cls,
        db: AsyncSession,
        current_user,
        battle_id: int,
        schedule_id: int | None = None,
    ) -> dict:
        battle = await BattleDao.get_battle_by_id(db, battle_id)
        if not battle:
            raise ServiceException(message='历史数据不存在')
        if battle.user_id != current_user.user.user_id:
            raise ServiceException(message='无权分析该历史数据')

        schedule = None
        if schedule_id:
            schedule = await ScheduleService.get_schedule_detail_service(db, current_user, schedule_id)

        records = await BattleDao.query_battle_records(db, battle_id)
        return cls.build_schedule_battle_analysis(schedule, battle, records)

    @classmethod
    def build_schedule_battle_analysis(cls, schedule: dict | None, battle: Any, records: list[Any]) -> dict:
        my_guild_name = cls._get_value(battle, 'my_guild_name', '') or ''
        scoped_records = [
            record for record in records
            if not my_guild_name or cls._get_value(record, 'guild_name', '') == my_guild_name
        ]
        record_by_name = {
            cls._normalize_name(cls._get_value(record, 'player_name', '')): record
            for record in scoped_records
            if cls._normalize_name(cls._get_value(record, 'player_name', ''))
        }

        if not schedule:
            summary = cls._build_summary(
                source_records=scoped_records,
                scheduled_count=0,
                matched_count=len(scoped_records),
                unmatched_schedule_count=0,
                unscheduled_record_count=0,
                record_scope_guild_name=my_guild_name,
            )
            return {
                'battle': cls._serialize_battle(battle),
                'schedule': None,
                'summary': summary,
                'teams': [],
                'class_summary': cls._build_class_summary(scoped_records),
                'top_records': cls._build_top_records(scoped_records),
                'unmatched_schedule_members': [],
                'unscheduled_records': [],
            }

        matched_record_names: set[str] = set()
        unmatched_schedule_members = []
        scheduled_count = 0
        matched_count = 0
        matched_records = []
        teams = []

        for team in schedule.get('teams', []):
            team_records = []
            team_scheduled_count = 0
            team_matched_count = 0
            squads = []

            for squad in team.get('squads', []):
                squad_records = []
                squad_scheduled_count = 0
                squad_matched_count = 0
                members = []

                for member in squad.get('members', []):
                    scheduled_count += 1
                    team_scheduled_count += 1
                    squad_scheduled_count += 1
                    member_name = cls._normalize_name(member.get('player_name', ''))
                    record = record_by_name.get(member_name)
                    matched = record is not None
                    if matched:
                        matched_count += 1
                        team_matched_count += 1
                        squad_matched_count += 1
                        matched_record_names.add(member_name)
                        matched_records.append(record)
                        team_records.append(record)
                        squad_records.append(record)
                    else:
                        unmatched_schedule_members.append(cls._serialize_schedule_member(member, team, squad))

                    members.append({
                        **cls._serialize_schedule_member(member, team, squad),
                        'matched': matched,
                        'record': cls._serialize_record(record) if record else None,
                    })

                squads.append({
                    'squad_id': squad.get('squad_id'),
                    'squad_name': squad.get('squad_name', ''),
                    'scheduled_count': squad_scheduled_count,
                    'matched_count': squad_matched_count,
                    'match_rate': cls._safe_rate(squad_matched_count, squad_scheduled_count),
                    'metrics': cls._sum_records(squad_records),
                    'members': members,
                })

            teams.append({
                'team_id': team.get('team_id'),
                'team_name': team.get('team_name', ''),
                'scheduled_count': team_scheduled_count,
                'matched_count': team_matched_count,
                'match_rate': cls._safe_rate(team_matched_count, team_scheduled_count),
                'metrics': cls._sum_records(team_records),
                'squads': squads,
            })

        unscheduled_records = [
            cls._serialize_record(record)
            for record in scoped_records
            if cls._normalize_name(cls._get_value(record, 'player_name', '')) not in matched_record_names
        ]
        summary = cls._build_summary(
            source_records=matched_records,
            scheduled_count=scheduled_count,
            matched_count=matched_count,
            unmatched_schedule_count=len(unmatched_schedule_members),
            unscheduled_record_count=len(unscheduled_records),
            record_scope_guild_name=my_guild_name,
        )

        return {
            'battle': cls._serialize_battle(battle),
            'schedule': {
                'schedule_id': schedule.get('schedule_id'),
                'schedule_name': schedule.get('schedule_name', ''),
                'create_time': schedule.get('create_time', ''),
            },
            'summary': summary,
            'teams': teams,
            'class_summary': cls._build_class_summary(matched_records),
            'top_records': cls._build_top_records(matched_records),
            'unmatched_schedule_members': unmatched_schedule_members,
            'unscheduled_records': unscheduled_records,
        }

    @classmethod
    def _build_summary(
        cls,
        source_records: list[Any],
        scheduled_count: int,
        matched_count: int,
        unmatched_schedule_count: int,
        unscheduled_record_count: int,
        record_scope_guild_name: str,
    ) -> dict:
        metrics = cls._sum_records(source_records)
        return {
            **metrics,
            'scheduled_count': scheduled_count,
            'matched_count': matched_count,
            'unmatched_schedule_count': unmatched_schedule_count,
            'unscheduled_record_count': unscheduled_record_count,
            'match_rate': cls._safe_rate(matched_count, scheduled_count) if scheduled_count else 100,
            'record_scope_guild_name': record_scope_guild_name,
        }

    @classmethod
    def _build_class_summary(cls, records: list[Any]) -> list[dict]:
        groups: dict[str, list[Any]] = defaultdict(list)
        for record in records:
            class_name = cls._get_value(record, 'player_class', '') or '未设置'
            groups[class_name].append(record)

        return sorted(
            [
                {
                    'player_class': class_name,
                    'count': len(group_records),
                    'metrics': cls._sum_records(group_records),
                }
                for class_name, group_records in groups.items()
            ],
            key=lambda item: item['metrics']['dmg_to_players'],
            reverse=True,
        )

    @classmethod
    def _build_top_records(cls, records: list[Any]) -> dict:
        serialized = [cls._serialize_record(record) for record in records]
        return {
            'kills': cls._top_by(serialized, 'kills'),
            'dmg_to_players': cls._top_by(serialized, 'dmg_to_players'),
            'healing': cls._top_by(serialized, 'healing'),
            'dmg_taken': cls._top_by(serialized, 'dmg_taken'),
        }

    @staticmethod
    def _top_by(records: list[dict], field: str, limit: int = 5) -> list[dict]:
        return sorted(records, key=lambda item: item.get(field, 0) or 0, reverse=True)[:limit]

    @classmethod
    def _sum_records(cls, records: list[Any]) -> dict:
        result = {field: 0 for field in cls.NUMERIC_FIELDS}
        for record in records:
            for field in cls.NUMERIC_FIELDS:
                result[field] += cls._to_int(cls._get_value(record, field, 0))
        result['total_kills'] = result['kills'] + result['qingquan_kills']
        return result

    @classmethod
    def _serialize_battle(cls, battle: Any) -> dict:
        return {
            'battle_id': cls._get_value(battle, 'battle_id'),
            'battle_name': cls._get_value(battle, 'battle_name', ''),
            'battle_date': cls._get_value(battle, 'battle_date', ''),
            'battle_type': cls._get_value(battle, 'battle_type', ''),
            'battle_result': cls._get_value(battle, 'battle_result', ''),
            'my_guild_name': cls._get_value(battle, 'my_guild_name', '') or '',
            'opponent_name': cls._get_value(battle, 'opponent_name', '') or '',
        }

    @classmethod
    def _serialize_record(cls, record: Any) -> dict:
        data = {
            'record_id': cls._get_value(record, 'record_id'),
            'guild_name': cls._get_value(record, 'guild_name', ''),
            'player_name': cls._get_value(record, 'player_name', ''),
            'player_class': cls._get_value(record, 'player_class', ''),
        }
        data.update({field: cls._to_int(cls._get_value(record, field, 0)) for field in cls.NUMERIC_FIELDS})
        data['total_kills'] = data['kills'] + data['qingquan_kills']
        return data

    @staticmethod
    def _serialize_schedule_member(member: dict, team: dict, squad: dict) -> dict:
        return {
            'member_id': member.get('member_id'),
            'player_name': member.get('player_name', ''),
            'player_class': member.get('player_class', ''),
            'secondary_class': member.get('secondary_class', ''),
            'team_id': team.get('team_id'),
            'team_name': team.get('team_name', ''),
            'squad_id': squad.get('squad_id'),
            'squad_name': squad.get('squad_name', ''),
        }

    @staticmethod
    def _get_value(source: Any, key: str, default: Any = None) -> Any:
        if source is None:
            return default
        if isinstance(source, dict):
            return source.get(key, default)
        return getattr(source, key, default)

    @staticmethod
    def _normalize_name(value: str) -> str:
        return str(value or '').strip()

    @staticmethod
    def _to_int(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _safe_rate(value: int, total: int) -> int:
        if not total:
            return 0
        return round(value / total * 100)
