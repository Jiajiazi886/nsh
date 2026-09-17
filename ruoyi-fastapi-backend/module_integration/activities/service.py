import copy
import hashlib
import json
import uuid
from datetime import datetime

from sqlalchemy import select, update, or_
from module_admin.entity.do.user_do import SysUser
from module_guild.entity.do.member_do import GuildMember
from module_guild.entity.do.profession_do import GuildProfession
from module_guild.entity.do.battle_do import GuildBattle, GuildBattleRecord
from module_integration.contract import ApiProblem
from .models import (
    Organization,
    OrganizationMember,
    Activity,
    ActivitySnapshot,
    Participation,
    MutationReceipt,
    ReportLink,
    ActivityLeaveLink,
    ActivityLeaveRecord,
)


def uid(actor):
    return int(actor.user.user_id)


def new_id(prefix):
    return prefix + '_' + uuid.uuid4().hex


def iso(value):
    return value.isoformat(timespec='seconds') if value else None


def fail(status, key, message):
    raise ApiProblem(status, key, message)


def manager_account(actor):
    return bool(
        set(getattr(actor, 'permissions', []) or [])
        & {'*:*:*', 'guild:schedule:list', 'guild:schedule:edit', 'guild:member:list'}
    )


def super_admin_account(actor):
    return bool(
        getattr(getattr(actor, 'user', None), 'admin', False)
        or uid(actor) == 1
        or 'admin' in (getattr(actor, 'roles', []) or [])
    )


def seats(teams):
    for team in teams:
        for squad in team['squads']:
            for seat in squad['seats']:
                yield squad['id'], seat


def activity_ended(activity, now=None):
    return activity.state == 'ended' or activity.ends_at <= (now or datetime.now())


class ActivityService:
    @staticmethod
    async def scalar(db, statement):
        return (await db.execute(statement)).scalars().first()

    @classmethod
    async def organization(cls, db, actor, org_id):
        org = await cls.scalar(db, select(Organization).where(Organization.org_id == org_id))
        if not org and org_id.startswith('guild-'):
            suffix = org_id[6:]
            if suffix.isdecimal() and len(suffix) < 20:
                owner = await cls.scalar(
                    db,
                    select(SysUser).where(
                        SysUser.user_id == int(suffix), SysUser.status == '0', SysUser.del_flag == '0'
                    ),
                )
                if owner:
                    org = Organization(
                        org_id=org_id,
                        org_type='guild',
                        name=owner.nick_name or owner.user_name,
                        owner_user_id=int(suffix),
                        source_owner_id=int(suffix),
                    )
        if not org:
            fail(404, 'NOT_FOUND', '组织不存在或不可见')
        return org

    @classmethod
    async def role(cls, db, actor, org):
        if uid(actor) == org.owner_user_id:
            # Stored organizations already have explicitly verified ownership.
            from sqlalchemy import inspect

            return 'owner' if inspect(org).persistent or manager_account(actor) else None
        if org.org_type == 'guild':
            member = await cls.scalar(
                db,
                select(GuildMember).where(
                    GuildMember.user_id == org.source_owner_id,
                    GuildMember.member_user_id == uid(actor),
                    GuildMember.is_active == '1',
                ),
            )
            if member:
                return 'assistant' if member.role_in_guild in {'管理员', '助手', '助理', '管理'} else 'member'
        else:
            member = await cls.scalar(
                db,
                select(OrganizationMember).where(
                    OrganizationMember.org_id == org.org_id, OrganizationMember.account_id == uid(actor)
                ),
            )
            if member:
                return member.role
        return None

    @classmethod
    async def require_manager(cls, db, actor, org):
        if await cls.role(db, actor, org) not in {'owner', 'assistant'}:
            fail(403, 'FORBIDDEN', '只有所属组织管理员或助手可以操作')

    @classmethod
    async def organizations(cls, db, actor):
        result = []
        stored = (await db.execute(select(Organization))).scalars().all()
        for org in stored:
            role = await cls.role(db, actor, org)
            if role:
                result.append(cls.org_dto(org, role))
        source_ids = set(
            (
                await db.execute(
                    select(GuildMember.user_id).where(
                        GuildMember.member_user_id == uid(actor), GuildMember.is_active == '1'
                    )
                )
            )
            .scalars()
            .all()
        )
        if manager_account(actor):
            source_ids.add(uid(actor))
        known = {o['orgId'] for o in result}
        for owner in sorted(source_ids):
            org_id = f'guild-{owner}'
            if org_id not in known:
                try:
                    org = await cls.organization(db, actor, org_id)
                except ApiProblem:
                    continue
                role = await cls.role(db, actor, org)
                if role:
                    result.append(cls.org_dto(org, role))
        return result

    @staticmethod
    def org_dto(org, role):
        return {
            'orgId': org.org_id,
            'orgType': org.org_type,
            'name': org.name,
            'role': role,
            'canManage': role in {'owner', 'assistant'},
        }

    @classmethod
    async def create_organization(cls, db, actor, kind, name):
        if not manager_account(actor):
            fail(403, 'FORBIDDEN', '当前账号没有组织管理权限')
        if kind == 'club' and not super_admin_account(actor):
            fail(403, 'SUPER_ADMIN_REQUIRED', '只有超级管理员可以创建俱乐部')
        name = name.strip()
        if kind not in {'guild', 'club'} or not name or len(name) > 80:
            fail(422, 'VALIDATION_FAILED', '组织名称不正确')
        org_id = f'guild-{uid(actor)}' if kind == 'guild' else new_id('club')
        existing = await cls.scalar(db, select(Organization).where(Organization.org_id == org_id))
        if existing:
            return cls.org_dto(existing, 'owner')
        org = Organization(
            org_id=org_id,
            org_type=kind,
            name=name,
            owner_user_id=uid(actor),
            source_owner_id=uid(actor) if kind == 'guild' else None,
        )
        # The production async session expires ORM attributes on commit.
        result = cls.org_dto(org, 'owner')
        try:
            db.add(org)
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        return result

    @classmethod
    async def grant_member(cls, db, actor, org_id, member_id, role):
        org = await cls.organization(db, actor, org_id)
        if org.org_type != 'club' or uid(actor) != org.owner_user_id:
            fail(403, 'FORBIDDEN', '只有俱乐部所有者可以授权成员')
        member = await cls.profile(db, member_id)
        if not member.member_user_id or member.member_user_id == org.owner_user_id:
            fail(422, 'PROFILE_REQUIRED', '成员必须绑定实际账号')
        if role not in {'member', 'assistant'}:
            fail(422, 'VALIDATION_FAILED', '成员权限不正确')
        existing = await cls.scalar(
            db,
            select(OrganizationMember).where(
                OrganizationMember.org_id == org_id, OrganizationMember.account_id == member.member_user_id
            ),
        )
        try:
            if existing:
                existing.role = role
            else:
                db.add(OrganizationMember(org_id=org_id, account_id=member.member_user_id, role=role))
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        return {'orgId': org_id, 'memberId': str(member_id), 'role': role}

    @classmethod
    async def profile(cls, db, member_id):
        if not str(member_id).isdecimal() or int(member_id) > 2**63 - 1:
            fail(422, 'PROFILE_REQUIRED', '成员 ID 不正确')
        member = await cls.scalar(
            db, select(GuildMember).where(GuildMember.member_id == int(member_id), GuildMember.is_active == '1')
        )
        if not member:
            fail(422, 'PROFILE_REQUIRED', '角色资料不存在或已失效')
        if member.member_user_id:
            account = await cls.scalar(
                db,
                select(SysUser).where(
                    SysUser.user_id == member.member_user_id, SysUser.status == '0', SysUser.del_flag == '0'
                ),
            )
            if not account:
                fail(422, 'PROFILE_REQUIRED', '绑定账号已失效')
        return member

    @classmethod
    async def profiles(cls, db, actor, org_id=None, activity_id=None):
        query = select(GuildMember).where(GuildMember.is_active == '1')
        if org_id:
            org = await cls.organization(db, actor, org_id)
            await cls.require_manager(db, actor, org)
            if org.org_type == 'guild':
                query = query.where(GuildMember.user_id == org.source_owner_id)
            else:
                accounts = list(
                    (
                        await db.execute(
                            select(OrganizationMember.account_id).where(OrganizationMember.org_id == org.org_id)
                        )
                    )
                    .scalars()
                    .all()
                ) + [org.owner_user_id]
                query = query.where(GuildMember.member_user_id.in_(accounts))
        else:
            query = query.where(GuildMember.member_user_id == uid(actor))
        if activity_id:
            activity = await cls.scalar(db, select(Activity).where(Activity.activity_id == activity_id))
            if not activity or (org_id and activity.org_id != org_id):
                fail(404, 'NOT_FOUND', '活动不存在或不属于当前组织')
            left_member_ids = select(ActivityLeaveRecord.member_id).where(
                ActivityLeaveRecord.activity_id == activity_id
            )
            query = query.where(~GuildMember.member_id.in_(left_member_ids))
        members = (await db.execute(query.order_by(GuildMember.player_class, GuildMember.member_id))).scalars().all()
        # Only self or verified organization managers reach this endpoint. Account
        # IDs support the separately authorized private profile view; never snapshot them.
        return [{**cls.player_dto(m), 'accountId': str(m.member_user_id) if m.member_user_id else None} for m in members]

    @classmethod
    async def lineup_templates(cls, db, actor, org_id):
        org = await cls.organization(db, actor, org_id)
        await cls.require_manager(db, actor, org)
        rows = (
            await db.execute(
                select(ActivitySnapshot, Activity)
                .join(Activity, Activity.activity_id == ActivitySnapshot.activity_id)
                .where(Activity.org_id == org.org_id)
                .order_by(ActivitySnapshot.created_at.desc(), ActivitySnapshot.version.desc(), ActivitySnapshot.snapshot_id)
                .limit(50)
            )
        ).all()
        return [
            {
                'snapshotId': snapshot.snapshot_id,
                'activityId': activity.activity_id,
                'activityName': activity.name,
                'version': snapshot.version,
                'savedAt': iso(snapshot.created_at),
                'teams': copy.deepcopy(snapshot.teams),
            }
            for snapshot, activity in rows
        ]

    @staticmethod
    def player_dto(m):
        return {
            'memberId': str(m.member_id),
            'name': m.player_name,
            'profession': m.player_class or '',
            'isTemporary': False,
        }

    @classmethod
    async def create(cls, db, actor, data):
        org = await cls.organization(db, actor, data.org_id)
        await cls.require_manager(db, actor, org)
        from sqlalchemy import inspect

        activity = Activity(
            activity_id=new_id('act'),
            org_id=org.org_id,
            name=data.name.strip(),
            starts_at=data.starts_at,
            ends_at=data.ends_at,
            remark=data.remark,
            state='open',
            is_public=0,
            revision=0,
            created_by=uid(actor),
        )
        activity_id = activity.activity_id
        try:
            if not inspect(org).persistent:
                db.add(org)
            db.add(activity)
            if org.org_type == 'guild':
                db.add(
                    ActivityLeaveLink(
                        activity_id=activity_id,
                        org_id=org.org_id,
                        code=new_id('leave').replace('_', '')[:32],
                    )
                )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        return await cls.detail(db, actor, activity_id)

    @classmethod
    async def load(cls, db, actor, activity_id, manage=False):
        activity = await cls.scalar(
            db, select(Activity).where(Activity.activity_id == activity_id).execution_options(populate_existing=True)
        )
        if not activity:
            fail(404, 'NOT_FOUND', '活动不存在或不可见')
        org = await cls.organization(db, actor, activity.org_id)
        role = await cls.role(db, actor, org)
        if manage:
            await cls.require_manager(db, actor, org)
        elif not role and not activity.is_public:
            participated = (
                await cls.scalar(
                    db,
                    select(Participation).where(
                        Participation.activity_id == activity_id, Participation.account_id == uid(actor)
                    ),
                )
                if activity_ended(activity)
                else None
            )
            if not participated:
                fail(404, 'NOT_FOUND', '活动不存在或不可见')
        return activity, org, role

    @classmethod
    async def current_teams(cls, db, activity):
        snapshot = (
            await cls.scalar(
                db, select(ActivitySnapshot).where(ActivitySnapshot.snapshot_id == activity.latest_snapshot_id)
            )
            if activity.latest_snapshot_id
            else None
        )
        if not snapshot:
            return None, []
        teams = copy.deepcopy(snapshot.teams)
        if activity.state != 'ended':
            participants = (
                (await db.execute(select(Participation).where(Participation.activity_id == activity.activity_id)))
                .scalars()
                .all()
            )
            for p in participants:
                if p.state == 'arranged':
                    continue
                for _, seat in seats(teams):
                    if seat['player'] and seat['player'].get('memberId') == str(p.member_id):
                        seat['player'] = None
                if p.state == 'active':
                    for squad_id, seat in seats(teams):
                        if squad_id == p.squad_id and seat['position'] == p.position:
                            seat['player'] = copy.deepcopy(p.player)
            leave_records = (
                (
                    await db.execute(
                        select(ActivityLeaveRecord).where(
                            ActivityLeaveRecord.activity_id == activity.activity_id
                        )
                    )
                )
                .scalars()
                .all()
            )
            left_members = {str(record.member_id) for record in leave_records}
            for _, seat in seats(teams):
                if seat['player'] and seat['player'].get('memberId') in left_members:
                    seat['player'] = None
        return snapshot, teams

    @classmethod
    async def detail(cls, db, actor, activity_id):
        a, org, role = await cls.load(db, actor, activity_id)
        snapshot, teams = await cls.current_teams(db, a)
        reports = (
            (
                await db.execute(
                    select(ReportLink)
                    .join(GuildBattle, ReportLink.battle_id == GuildBattle.battle_id)
                    .where(ReportLink.activity_id == activity_id, GuildBattle.del_flag == '0')
                )
            )
            .scalars()
            .all()
        )
        empty = [seat for _, seat in seats(teams) if not seat['player']]
        shortages = {}
        for seat in empty:
            profession = seat['requiredProfession'] or '不限职业'
            shortages[profession] = shortages.get(profession, 0) + 1
        can_manage = role in {'owner', 'assistant'}
        leave_link = (
            await cls.scalar(
                db,
                select(ActivityLeaveLink).where(ActivityLeaveLink.activity_id == activity_id),
            )
            if can_manage
            else None
        )
        effective_state = 'ended' if activity_ended(a) else a.state
        return {
            'activityId': a.activity_id,
            'orgId': a.org_id,
            'orgType': org.org_type,
            'orgName': org.name,
            'name': a.name,
            'startsAt': iso(a.starts_at),
            'endsAt': iso(a.ends_at),
            'remark': a.remark,
            'state': effective_state,
            'isPublic': bool(a.is_public),
            'revision': a.revision,
            'canManage': can_manage,
            'leaveCode': leave_link.code if leave_link else None,
            'leavePath': f'/public/activity-leave/{leave_link.code}' if leave_link else None,
            'canSignup': bool(a.is_public and effective_state == 'open' and snapshot),
            'hasReport': bool(reports),
            'reportIds': [str(r.battle_id) for r in reports],
            'totalSeats': sum(1 for _ in seats(teams)),
            'emptySeats': len(empty),
            'shortages': shortages,
            'snapshot': {
                'snapshotId': snapshot.snapshot_id,
                'version': snapshot.version,
                'savedAt': iso(snapshot.created_at),
                'teams': teams,
            }
            if snapshot
            else None,
        }

    @classmethod
    async def leave_link_info(cls, db, code):
        link = await cls.scalar(db, select(ActivityLeaveLink).where(ActivityLeaveLink.code == code))
        if not link:
            fail(404, 'LEAVE_LINK_NOT_FOUND', '请假链接不存在')
        activity = await cls.scalar(db, select(Activity).where(Activity.activity_id == link.activity_id))
        org = await cls.scalar(db, select(Organization).where(Organization.org_id == link.org_id))
        if not activity or not org:
            fail(404, 'LEAVE_LINK_NOT_FOUND', '请假链接不存在')
        return {
            'activityId': activity.activity_id,
            'name': activity.name,
            'orgName': org.name,
            'startsAt': iso(activity.starts_at),
            'endsAt': iso(activity.ends_at),
            'state': activity.state,
            'expired': activity.state == 'ended' or activity.ends_at <= datetime.now(),
        }

    @classmethod
    async def leave_members_by_code(cls, db, code, keyword=''):
        link = await cls.scalar(db, select(ActivityLeaveLink).where(ActivityLeaveLink.code == code))
        if not link:
            fail(404, 'LEAVE_LINK_NOT_FOUND', '请假链接不存在')
        activity = await cls.scalar(db, select(Activity).where(Activity.activity_id == link.activity_id))
        org = await cls.scalar(db, select(Organization).where(Organization.org_id == link.org_id))
        if not activity or not org or org.org_type != 'guild':
            fail(404, 'LEAVE_LINK_NOT_FOUND', '请假链接不存在')
        if activity.state == 'ended' or activity.ends_at <= datetime.now():
            fail(409, 'ACTIVITY_EXPIRED', '约战已经结束，不能再请假')
        query = select(GuildMember).where(
            GuildMember.user_id == org.source_owner_id,
            GuildMember.is_active == '1',
        )
        value = keyword.strip()
        if value:
            query = query.where(GuildMember.player_name.like(f'%{value}%'))
        members = (await db.execute(query.order_by(GuildMember.player_name, GuildMember.member_id).limit(20))).scalars().all()
        left_ids = set(
            (
                await db.execute(
                    select(ActivityLeaveRecord.member_id).where(
                        ActivityLeaveRecord.activity_id == activity.activity_id
                    )
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                **cls.player_dto(member),
                'hasLeft': member.member_id in left_ids,
            }
            for member in members
        ]

    @classmethod
    async def leave_by_code(cls, db, code, member_id, remark=''):
        link = await cls.scalar(db, select(ActivityLeaveLink).where(ActivityLeaveLink.code == code))
        if not link:
            fail(404, 'LEAVE_LINK_NOT_FOUND', '请假链接不存在')
        activity = await cls.scalar(
            db,
            select(Activity)
            .where(Activity.activity_id == link.activity_id)
            .with_for_update()
            .execution_options(populate_existing=True),
        )
        org = await cls.scalar(db, select(Organization).where(Organization.org_id == link.org_id))
        if not activity or not org or org.org_type != 'guild':
            fail(404, 'LEAVE_LINK_NOT_FOUND', '请假链接不存在')
        if activity.state == 'ended' or activity.ends_at <= datetime.now():
            fail(409, 'ACTIVITY_EXPIRED', '约战已经结束，不能再请假')
        member = await cls.scalar(
            db,
            select(GuildMember).where(
                GuildMember.member_id == int(member_id),
                GuildMember.user_id == org.source_owner_id,
                GuildMember.is_active == '1',
            ),
        )
        if not member:
            fail(404, 'MEMBER_NOT_FOUND', '没有找到该帮会成员')
        existing = await cls.scalar(
            db,
            select(ActivityLeaveRecord).where(
                ActivityLeaveRecord.activity_id == activity.activity_id,
                ActivityLeaveRecord.member_id == member.member_id,
            ),
        )
        if existing:
            fail(409, 'ALREADY_LEFT', '该成员已经请假')
        player = cls.player_dto(member)
        record = ActivityLeaveRecord(
            record_id=new_id('leave_record'),
            activity_id=activity.activity_id,
            member_id=member.member_id,
            account_id=member.member_user_id or None,
            player=player,
            remark=remark.strip(),
        )
        try:
            await cls.advance(db, activity, activity.revision)
            db.add(record)
            participation = await cls.scalar(
                db,
                select(Participation).where(
                    Participation.activity_id == activity.activity_id,
                    Participation.member_id == member.member_id,
                ),
            )
            if participation:
                participation.state = 'left'
                participation.squad_id = None
                participation.position = None
                participation.player = player
            elif member.member_user_id:
                db.add(
                    Participation(
                        participation_id=new_id('join'),
                        activity_id=activity.activity_id,
                        account_id=member.member_user_id,
                        member_id=member.member_id,
                        state='left',
                        player=player,
                    )
                )
            await db.flush()
            result = {
                'activityId': activity.activity_id,
                'memberId': str(member.member_id),
                'name': member.player_name,
                'remark': record.remark,
                'leftAt': iso(record.left_at),
                'revision': activity.revision,
            }
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        return result

    @classmethod
    async def activity_leaves(cls, db, actor, activity_id):
        activity, _, _ = await cls.load(db, actor, activity_id, True)
        records = (
            (
                await db.execute(
                    select(ActivityLeaveRecord)
                    .where(ActivityLeaveRecord.activity_id == activity.activity_id)
                    .order_by(ActivityLeaveRecord.left_at.desc(), ActivityLeaveRecord.record_id)
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                'memberId': str(record.member_id),
                'name': record.player.get('name', ''),
                'profession': record.player.get('profession', ''),
                'remark': record.remark,
                'leftAt': iso(record.left_at),
            }
            for record in records
        ]

    @classmethod
    async def list(
        cls,
        db,
        actor,
        kind,
        page=1,
        page_size=20,
        profession='',
        vacant_only=False,
        org_type=None,
        participating_only=False,
    ):
        orgs = await cls.organizations(db, actor)
        org_ids = [o['orgId'] for o in orgs]
        query = select(Activity)
        now = datetime.now()
        if org_type:
            if org_type not in {'guild', 'club'}:
                fail(422, 'VALIDATION_FAILED', '组织分类不正确')
            query = query.where(
                Activity.org_id.in_(select(Organization.org_id).where(Organization.org_type == org_type))
            )
        if kind == 'public':
            query = query.where(Activity.is_public == 1, Activity.state == 'open', Activity.ends_at > now)
        elif kind == 'mine':
            if participating_only:
                attended = select(Participation.activity_id).where(
                    Participation.account_id == uid(actor),
                    Participation.state.in_({'active', 'arranged'}),
                )
                query = query.where(
                    Activity.activity_id.in_(attended), Activity.state != 'ended', Activity.ends_at > now
                )
            else:
                query = query.where(Activity.org_id.in_(org_ids), Activity.state != 'ended', Activity.ends_at > now)
        elif kind == 'history':
            attended = select(Participation.activity_id).where(Participation.account_id == uid(actor))
            query = query.where(
                or_(Activity.state == 'ended', Activity.ends_at <= now),
                or_(Activity.org_id.in_(org_ids), Activity.activity_id.in_(attended)),
            )
        else:
            fail(422, 'VALIDATION_FAILED', '活动分类不正确')
        # Stable ordering. Filters use the same resolved seat view as details, including signup overlays.
        activities = (await db.execute(query.order_by(Activity.starts_at.desc(), Activity.activity_id))).scalars().all()
        items = []
        for a in activities:
            d = await cls.detail(db, actor, a.activity_id)
            if vacant_only and not d['emptySeats']:
                continue
            if profession and not (d['shortages'].get(profession, 0) or d['shortages'].get('不限职业', 0)):
                continue
            d.pop('snapshot')
            items.append(d)
        start = (page - 1) * page_size
        return {'items': items[start : start + page_size], 'page': page, 'pageSize': page_size, 'total': len(items)}

    @classmethod
    async def normalize(cls, db, org, data, activity_id=None):
        enabled = set(
            (await db.execute(select(GuildProfession.profession_name).where(GuildProfession.status == '0')))
            .scalars()
            .all()
        )
        teams = []
        team_ids = set()
        squad_ids = set()
        team_names = set()
        players = set()
        accounts = set()
        for team in data.teams:
            if not team.name.strip() or team.id.lower() in team_ids or team.name.strip() in team_names:
                fail(422, 'INVALID_LINEUP', '团队名称或 ID 重复')
            team_ids.add(team.id.lower())
            team_names.add(team.name.strip())
            squads = []
            names = set()
            for squad in team.squads:
                if squad.id.lower() in squad_ids or squad.name.strip() in names:
                    fail(422, 'INVALID_LINEUP', '小队名称或 ID 重复')
                squad_ids.add(squad.id.lower())
                names.add(squad.name.strip())
                normalized = []
                for seat in sorted(squad.seats, key=lambda s: s.position):
                    required = seat.required_profession.strip()
                    player = None
                    if required and required not in enabled:
                        fail(422, 'INVALID_PROFESSION', '指定职业不存在或已停用')
                    if seat.player:
                        p = seat.player
                        if p.temporary_id:
                            if not p.name.strip() or p.profession not in enabled:
                                fail(422, 'INVALID_LINEUP', '临时替补姓名或职业不正确')
                            identity = p.temporary_id
                            player = {
                                'temporaryId': identity,
                                'name': p.name.strip(),
                                'profession': p.profession,
                                'isTemporary': True,
                            }
                        else:
                            member = await cls.profile(db, p.member_id)
                            identity = 'member:' + str(member.member_id)
                            enrolled = (
                                await cls.scalar(
                                    db,
                                    select(Participation).where(
                                        Participation.activity_id == activity_id,
                                        Participation.member_id == member.member_id,
                                        Participation.state == 'active',
                                    ),
                                )
                                if activity_id
                                else None
                            )
                            if org.org_type == 'guild':
                                if member.user_id != org.source_owner_id and not enrolled:
                                    fail(422, 'MEMBER_OUT_OF_SCOPE', '发布前只能安排本组织成员或活动临时替补')
                            else:
                                grant = await cls.scalar(
                                    db,
                                    select(OrganizationMember).where(
                                        OrganizationMember.org_id == org.org_id,
                                        OrganizationMember.account_id == member.member_user_id,
                                    ),
                                )
                                if not member.member_user_id or (
                                    not grant and member.member_user_id != org.owner_user_id and not enrolled
                                ):
                                    fail(422, 'MEMBER_OUT_OF_SCOPE', '玩家不是本俱乐部成员')
                            if p.profession and p.profession != member.player_class:
                                fail(422, 'INVALID_PROFESSION', '不能伪造玩家职业')
                            if member.member_user_id:
                                if member.member_user_id in accounts:
                                    fail(422, 'DUPLICATE_PLAYER', '同一账号不能占多个位置')
                                accounts.add(member.member_user_id)
                            player = cls.player_dto(member)
                        if identity in players:
                            fail(422, 'DUPLICATE_PLAYER', '同一玩家不能占多个位置')
                        players.add(identity)
                        if required and player['profession'] != required:
                            fail(422, 'PROFESSION_MISMATCH', '玩家职业不符合位置要求')
                    normalized.append(
                        {
                            'position': seat.position,
                            'requiredProfession': required,
                            'notes': list(seat.notes),
                            'player': player,
                        }
                    )
                squads.append({'id': squad.id, 'name': squad.name.strip(), 'seats': normalized})
            teams.append({'id': team.id, 'name': team.name.strip(), 'squads': squads})
        if not squad_ids:
            fail(422, 'INVALID_LINEUP', '至少需要一个小队')
        return teams

    @staticmethod
    def digest(action, data):
        return hashlib.sha256(
            json.dumps(
                [action, data.model_dump(mode='json', by_alias=True)],
                sort_keys=True,
                ensure_ascii=False,
                separators=(',', ':'),
            ).encode()
        ).hexdigest()

    @classmethod
    async def receipt(cls, db, actor, a, action, data):
        existing = await cls.scalar(
            db,
            select(MutationReceipt).where(
                MutationReceipt.activity_id == a.activity_id,
                MutationReceipt.actor_id == uid(actor),
                MutationReceipt.operation_key == data.operation_key,
            ),
        )
        if existing:
            if existing.digest != cls.digest(action, data):
                fail(409, 'IDEMPOTENCY_CONFLICT', '同一操作标识不能用于不同请求')
            return existing.result
        return None

    @classmethod
    async def advance(cls, db, a, expected, allow_ended=False):
        now = datetime.now()
        if activity_ended(a, now) and not allow_ended:
            fail(409, 'ACTIVITY_ENDED', '活动已结束，阵容已冻结')
        if a.revision != expected:
            fail(409, 'REVISION_CONFLICT', '活动已被其他用户修改，请刷新后确认')
        condition = [Activity.activity_id == a.activity_id, Activity.revision == expected]
        if not allow_ended:
            condition.extend([Activity.state != 'ended', Activity.ends_at > now])
        result = await db.execute(
            update(Activity)
            .where(*condition)
            .values(revision=expected + 1)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            fail(409, 'REVISION_CONFLICT', '活动已被其他用户修改，请刷新后确认')
        a.revision = expected + 1

    @classmethod
    async def finish(cls, db, actor, a, action, data, result):
        db.add(
            MutationReceipt(
                receipt_id=new_id('op'),
                activity_id=a.activity_id,
                actor_id=uid(actor),
                operation_key=data.operation_key,
                action=action,
                digest=cls.digest(action, data),
                result=result,
            )
        )
        await db.commit()
        return result

    @classmethod
    async def save(cls, db, actor, activity_id, data):
        a, org, _ = await cls.load(db, actor, activity_id, True)
        replay = await cls.receipt(db, actor, a, 'save', data)
        if replay:
            return replay
        teams = await cls.normalize(db, org, data, activity_id)
        active = (
            (
                await db.execute(
                    select(Participation).where(
                        Participation.activity_id == activity_id, Participation.state == 'active'
                    )
                )
            )
            .scalars()
            .all()
        )
        # Administrative saves cannot displace a public signup silently.
        for p in active:
            target = next(
                (seat for squad_id, seat in seats(teams) if squad_id == p.squad_id and seat['position'] == p.position),
                None,
            )
            if (
                not target
                or not target['player']
                or target['player'].get('memberId') != str(p.member_id)
                or (target['requiredProfession'] and target['requiredProfession'] != p.player['profession'])
            ):
                fail(409, 'SIGNUP_CONFLICT', '已公开报名的位置不能被移出、移动、覆盖或改为不符合的职业，请报名者先请假')
        try:
            await cls.advance(db, a, data.expected_revision)
            snapshot = ActivitySnapshot(
                snapshot_id=new_id('snap'),
                activity_id=activity_id,
                version=a.revision,
                teams=teams,
                created_by=uid(actor),
            )
            db.add(snapshot)
            await db.flush()
            a.latest_snapshot_id = snapshot.snapshot_id
            # Preserve actual account participation, including admin-arranged
            # players, independently from future guild membership/name changes.
            for squad_id, seat in seats(teams):
                player = seat['player']
                if player and player.get('memberId'):
                    member = await cls.profile(db, player['memberId'])
                    if member.member_user_id:
                        old = await cls.scalar(
                            db,
                            select(Participation).where(
                                Participation.activity_id == activity_id, Participation.member_id == member.member_id
                            ),
                        )
                        if not old:
                            db.add(
                                Participation(
                                    participation_id=new_id('join'),
                                    activity_id=activity_id,
                                    account_id=member.member_user_id,
                                    member_id=member.member_id,
                                    state='arranged',
                                    player=player,
                                )
                            )
            return await cls.finish(
                db,
                actor,
                a,
                'save',
                data,
                {'activityId': activity_id, 'revision': a.revision, 'snapshotId': snapshot.snapshot_id},
            )
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def change(cls, db, actor, activity_id, action, data):
        a, org, _ = await cls.load(db, actor, activity_id, True)
        replay = await cls.receipt(db, actor, a, action, data)
        if replay:
            return replay
        if action not in {'publish', 'end'}:
            fail(422, 'VALIDATION_FAILED', '操作不正确')
        snapshot, teams = await cls.current_teams(db, a)
        if not snapshot:
            fail(422, 'LINEUP_REQUIRED', '请先保存有效阵容')
        if action == 'publish' and a.ends_at <= datetime.now():
            fail(409, 'ACTIVITY_EXPIRED', '活动时间已过，不能发布')
        try:
            await cls.advance(db, a, data.expected_revision)
            if action == 'publish':
                a.is_public = 1
            else:
                final = ActivitySnapshot(
                    snapshot_id=new_id('snap'),
                    activity_id=activity_id,
                    version=a.revision,
                    teams=teams,
                    created_by=uid(actor),
                )
                db.add(final)
                await db.flush()
                a.latest_snapshot_id = final.snapshot_id
                a.state = 'ended'
            return await cls.finish(
                db,
                actor,
                a,
                action,
                data,
                {'activityId': activity_id, 'revision': a.revision, 'isPublic': bool(a.is_public), 'state': a.state},
            )
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def signup(cls, db, actor, activity_id, data):
        a, org, _ = await cls.load(db, actor, activity_id)
        replay = await cls.receipt(db, actor, a, 'signup', data)
        if replay:
            return replay
        if not a.is_public or a.ends_at <= datetime.now():
            fail(403, 'SIGNUP_CLOSED', '活动未公开或报名已关闭')
        member = await cls.profile(db, data.member_id)
        if member.member_user_id != uid(actor):
            fail(403, 'MEMBER_NOT_BOUND_TO_ACTOR', '只能使用本人绑定的角色报名')
        enabled = await cls.scalar(
            db,
            select(GuildProfession).where(
                GuildProfession.profession_name == member.player_class, GuildProfession.status == '0'
            ),
        )
        if not enabled:
            fail(422, 'PROFILE_REQUIRED', '请先完善有效的职业资料')
        snapshot, teams = await cls.current_teams(db, a)
        target = next(
            (
                seat
                for squad_id, seat in seats(teams)
                if squad_id == data.squad_id and seat['position'] == data.position
            ),
            None,
        )
        if not target:
            fail(404, 'SEAT_NOT_FOUND', '位置不存在')
        if target['player']:
            fail(409, 'SEAT_OCCUPIED', '位置已有玩家，请刷新')
        if target['requiredProfession'] and target['requiredProfession'] != member.player_class:
            fail(422, 'PROFESSION_MISMATCH', '职业不符合位置要求')
        active = await cls.scalar(
            db,
            select(Participation).where(
                Participation.activity_id == activity_id,
                Participation.account_id == uid(actor),
                Participation.state == 'active',
            ),
        )
        if active:
            fail(409, 'ALREADY_SIGNED_UP', '同一账号只能占一个位置，请先请假')
        # Includes admin-arranged profiles; no second seat via a different bound character.
        for _, seat in seats(teams):
            if seat['player'] and seat['player'].get('memberId'):
                planned = await cls.profile(db, seat['player']['memberId'])
                if planned.member_user_id == uid(actor):
                    fail(409, 'ALREADY_ARRANGED', '你已在当前阵容中，请先请假')
        try:
            await cls.advance(db, a, data.expected_revision)
            p = await cls.scalar(
                db,
                select(Participation).where(
                    Participation.activity_id == activity_id, Participation.member_id == member.member_id
                ),
            )
            if not p:
                p = Participation(
                    participation_id=new_id('join'),
                    activity_id=activity_id,
                    account_id=uid(actor),
                    member_id=member.member_id,
                )
                db.add(p)
            p.state = 'active'
            p.squad_id = data.squad_id
            p.position = data.position
            p.player = cls.player_dto(member)
            return await cls.finish(db, actor, a, 'signup', data, {'activityId': activity_id, 'revision': a.revision})
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def leave(cls, db, actor, activity_id, data):
        a, org, _ = await cls.load(db, actor, activity_id)
        replay = await cls.receipt(db, actor, a, 'leave', data)
        if replay:
            return replay
        member = await cls.profile(db, data.member_id)
        if member.member_user_id != uid(actor):
            fail(403, 'MEMBER_NOT_BOUND_TO_ACTOR', '只能为本人绑定角色请假')
        _, teams = await cls.current_teams(db, a)
        if not any(seat['player'] and seat['player'].get('memberId') == data.member_id for _, seat in seats(teams)):
            fail(409, 'NOT_SIGNED_UP', '本人当前没有安排位置')
        try:
            await cls.advance(db, a, data.expected_revision)
            p = await cls.scalar(
                db,
                select(Participation).where(
                    Participation.activity_id == activity_id, Participation.member_id == member.member_id
                ),
            )
            if not p:
                p = Participation(
                    participation_id=new_id('join'),
                    activity_id=activity_id,
                    account_id=uid(actor),
                    member_id=member.member_id,
                )
                db.add(p)
            p.state = 'left'
            p.squad_id = None
            p.position = None
            p.player = cls.player_dto(member)
            return await cls.finish(db, actor, a, 'leave', data, {'activityId': activity_id, 'revision': a.revision})
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def snapshots(cls, db, actor, activity_id):
        a, org, role = await cls.load(db, actor, activity_id)
        if not role:
            fail(403, 'FORBIDDEN', '仅所属组织成员可以查看历史阵容版本')
        items = (
            (
                await db.execute(
                    select(ActivitySnapshot)
                    .where(ActivitySnapshot.activity_id == activity_id)
                    .order_by(ActivitySnapshot.version.desc())
                )
            )
            .scalars()
            .all()
        )
        return [
            {'snapshotId': s.snapshot_id, 'version': s.version, 'savedAt': iso(s.created_at), 'teams': s.teams}
            for s in items
        ]

    @classmethod
    async def link_report(cls, db, actor, activity_id, data):
        a, org, _ = await cls.load(db, actor, activity_id, True)
        replay = await cls.receipt(db, actor, a, 'link-report', data)
        if replay:
            return replay
        battle = await cls.scalar(
            db,
            select(GuildBattle).where(
                GuildBattle.battle_id == int(data.battle_id),
                GuildBattle.user_id.in_({uid(actor), org.owner_user_id}),
                GuildBattle.del_flag == '0',
            ),
        )
        if not battle:
            fail(404, 'REPORT_NOT_FOUND', '战报不存在或不属于当前账号')
        existing = await cls.scalar(db, select(ReportLink).where(ReportLink.battle_id == battle.battle_id))
        if existing:
            fail(409, 'REPORT_ALREADY_LINKED', '战报已关联活动，不能重复关联')
        try:
            await cls.advance(db, a, data.expected_revision, True)
            db.add(ReportLink(battle_id=battle.battle_id, activity_id=activity_id, linked_by=uid(actor)))
            return await cls.finish(
                db,
                actor,
                a,
                'link-report',
                data,
                {'activityId': activity_id, 'revision': a.revision, 'reportId': data.battle_id},
            )
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def import_report(cls, db, actor, activity_id, data):
        a, org, _ = await cls.load(db, actor, activity_id, True)
        replay = await cls.receipt(db, actor, a, 'import-report', data)
        if replay:
            return replay
        filename = data.file_name.strip()
        if not filename.lower().endswith('.csv'):
            fail(422, 'VALIDATION_FAILED', '只支持 CSV 文件')
        duplicate = await cls.scalar(
            db,
            select(GuildBattle).where(
                GuildBattle.user_id == uid(actor),
                GuildBattle.battle_name == filename,
                GuildBattle.del_flag == '0',
            ),
        )
        if duplicate:
            fail(409, 'DUPLICATE_REPORT', '当前账号已经导入过同名 CSV 文件')
        try:
            await cls.advance(db, a, data.expected_revision, True)
            battle = GuildBattle(
                battle_name=filename,
                battle_date=data.battle_date,
                battle_time=a.starts_at,
                battle_type='约战',
                battle_result=data.battle_result,
                opponent_name=data.opponent_name,
                initiator_guild_id=org.source_owner_id or org.owner_user_id,
                user_id=uid(actor),
                my_guild_name=data.my_guild_name,
                status='2',
                remark=data.remark,
                csv_file_url='',
            )
            db.add(battle)
            await db.flush()
            for item in data.records:
                db.add(
                    GuildBattleRecord(
                        battle_id=battle.battle_id,
                        guild_id=org.source_owner_id or org.owner_user_id,
                        battle_date=data.battle_date,
                        guild_name=item.guild_name,
                        player_name=item.player_name,
                        player_class=item.player_class,
                        kills=item.kills,
                        qingquan_kills=item.qingquan_kills,
                        assists=item.assists,
                        resources=item.resources,
                        dmg_to_players=item.dmg_to_players,
                        armor_break_players=item.armor_break_players,
                        dmg_to_buildings=item.dmg_to_buildings,
                        armor_break_buildings=item.armor_break_buildings,
                        healing=item.healing,
                        dmg_taken=item.dmg_taken,
                        deaths=item.deaths,
                        revives=item.revives,
                        burn_bones=item.burn_bones,
                    )
                )
            db.add(ReportLink(battle_id=battle.battle_id, activity_id=activity_id, linked_by=uid(actor)))
            result = {
                'activityId': activity_id,
                'revision': a.revision,
                'reportId': str(battle.battle_id),
                'fileName': filename,
                'importedPlayers': len(data.records),
            }
            return await cls.finish(db, actor, a, 'import-report', data, result)
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def reports(cls, db, actor, page=1, page_size=20):
        history = await cls.list(db, actor, 'history', 1, 100000)
        activity_ids = [a['activityId'] for a in history['items']]
        linked = (
            await db.execute(
                select(GuildBattle, ReportLink)
                .join(ReportLink, GuildBattle.battle_id == ReportLink.battle_id)
                .where(ReportLink.activity_id.in_(activity_ids), GuildBattle.del_flag == '0')
            )
        ).all()
        items = [cls.report_summary(b, r.activity_id) for b, r in linked]
        items.sort(key=lambda i: (i['battleDate'] or '', i['reportId']), reverse=True)
        return {
            'items': items[(page - 1) * page_size : page * page_size],
            'page': page,
            'pageSize': page_size,
            'total': len(items),
        }

    @staticmethod
    def report_summary(b, activity_id):
        return {
            'reportId': str(b.battle_id),
            'activityId': activity_id,
            'name': b.battle_name or '未命名战报',
            'battleDate': b.battle_date,
            'result': b.battle_result or '',
            'association': '已关联活动',
        }

    @classmethod
    async def report(cls, db, actor, report_id):
        link = await cls.scalar(db, select(ReportLink).where(ReportLink.battle_id == int(report_id)))
        if not link:
            fail(404, 'REPORT_NOT_FOUND', '战报不存在或未关联约战')
        battle = await cls.scalar(
            db, select(GuildBattle).where(GuildBattle.battle_id == int(report_id), GuildBattle.del_flag == '0')
        )
        if not battle:
            fail(404, 'REPORT_NOT_FOUND', '战报不存在或不可见')
        a, org, role = await cls.load(db, actor, link.activity_id)
        participant = await cls.scalar(
            db,
            select(Participation).where(
                Participation.activity_id == link.activity_id, Participation.account_id == uid(actor)
            ),
        )
        if not role and not participant:
            fail(404, 'REPORT_NOT_FOUND', '战报仅所属组织成员或本人参战活动可见')
        records = (
            (
                await db.execute(
                    select(GuildBattleRecord)
                    .where(GuildBattleRecord.battle_id == battle.battle_id)
                    .order_by(GuildBattleRecord.record_id)
                )
            )
            .scalars()
            .all()
        )
        metrics = [
            'kills',
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
            'qingquan_kills',
            'qingquan_revives',
            'burn_bones',
        ]
        # Whitelist only gameplay metrics. Do not expose raw file URL/account bindings.
        return {
            **cls.report_summary(battle, link.activity_id),
            'players': [
                {
                    'name': r.player_name,
                    'profession': r.player_class or '',
                    'guildName': r.guild_name or '',
                    'metrics': {m: str(getattr(r, m, 0) or 0) for m in metrics},
                }
                for r in records
            ],
        }
