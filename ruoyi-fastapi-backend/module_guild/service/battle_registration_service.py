from datetime import datetime, timedelta
from secrets import token_urlsafe

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import AuthException, PermissionException, ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_guild.dao.battle_registration_dao import BattleRegistrationDao
from module_guild.dao.join_application_dao import JoinApplicationDao
from module_guild.entity.do.battle_registration_do import GuildBattleInvite, GuildBattleRegistration
from module_guild.entity.vo.battle_registration_vo import (
    BattleInviteCreateModel,
    BattleRegistrationReviewModel,
    PublicBattleJoinApplicationModel,
    PublicBattleLeaveApplicationModel,
    PublicBattleRegistrationModel,
)
from module_guild.entity.vo.join_application_vo import JoinApplicationCreateModel
from module_guild.service.join_application_service import JoinApplicationService
from module_guild.service.profession_service import ProfessionService


class BattleRegistrationService:
    @classmethod
    async def create_invite_service(
        cls, db: AsyncSession, current_user: CurrentUserModel, data: BattleInviteCreateModel
    ) -> dict:
        role_scope = cls._get_role_scope(current_user)
        if role_scope == 'user':
            raise ServiceException(message='当前角色无权创建约战链接')

        battle_name = data.battle_name.strip()
        if not battle_name:
            raise ServiceException(message='约战名称不能为空')

        battle_time = cls._parse_datetime(data.battle_time)
        expire_time = datetime.now() + timedelta(hours=data.expire_hours)
        owner_user_id = current_user.user.user_id
        guild_name = current_user.user.nick_name or current_user.user.user_name or ''
        invite_code = await cls._new_invite_code(db)
        create_time = datetime.now()
        await BattleRegistrationDao.disable_active_invites_for_owner(db, owner_user_id)
        invite = await BattleRegistrationDao.create_invite(
            db,
            {
                'invite_code': invite_code,
                'owner_user_id': owner_user_id,
                'guild_name': guild_name,
                'battle_name': battle_name,
                'battle_time': battle_time,
                'expire_time': expire_time,
                'create_by': current_user.user.user_name or '',
                'create_time': create_time,
                'remark': (data.remark or '').strip(),
            },
        )
        result = {
            'invite_id': invite.invite_id,
            'invite_code': invite_code,
            'owner_user_id': owner_user_id,
            'guild_name': guild_name,
            'battle_name': battle_name,
            'battle_time': battle_time,
            'expire_time': expire_time,
            'status': '0',
            'expired': False,
            'remark': (data.remark or '').strip(),
            'create_time': create_time,
            'public_path': f'/public/battle/{invite_code}',
        }
        await db.commit()
        return result

    @classmethod
    async def list_invites_service(cls, db: AsyncSession, current_user: CurrentUserModel) -> list[dict]:
        role_scope = cls._get_role_scope(current_user)
        owner_user_id = None if role_scope == 'admin' else current_user.user.user_id
        await BattleRegistrationDao.mark_expired_invites(db)
        await db.commit()
        invites = await BattleRegistrationDao.list_invites(db, owner_user_id)
        rows = []
        for invite in invites:
            row = cls._format_invite(invite)
            row['approved_count'] = await BattleRegistrationDao.count_approved_for_invite(db, invite.invite_id)
            row['registration_count'] = await BattleRegistrationDao.count_registrations_for_invite(db, invite.invite_id)
            rows.append(row)
        return rows

    @classmethod
    async def disable_invite_service(
        cls, db: AsyncSession, current_user: CurrentUserModel, invite_id: int
    ) -> CrudResponseModel:
        role_scope = cls._get_role_scope(current_user)
        if role_scope == 'user':
            raise ServiceException(message='当前角色无权停用约战链接')
        invite = await BattleRegistrationDao.get_invite_by_id(db, invite_id)
        if not invite:
            raise ServiceException(message='链接不存在')
        if role_scope == 'common' and invite.owner_user_id != current_user.user.user_id:
            raise ServiceException(message='只能停用自己帮会的约战链接')
        if invite.status == '1':
            return CrudResponseModel(is_success=True, message='链接已是失效状态')
        await BattleRegistrationDao.disable_invite(db, invite_id)
        await db.commit()
        return CrudResponseModel(is_success=True, message='约战链接已失效')

    @classmethod
    async def delete_invite_service(
        cls, db: AsyncSession, current_user: CurrentUserModel, invite_id: int
    ) -> CrudResponseModel:
        role_scope = cls._get_role_scope(current_user)
        if role_scope == 'user':
            raise ServiceException(message='当前角色无权删除约战链接')
        invite = await BattleRegistrationDao.get_invite_by_id(db, invite_id)
        if not invite:
            raise ServiceException(message='链接不存在')
        if role_scope == 'common' and invite.owner_user_id != current_user.user.user_id:
            raise ServiceException(message='只能删除自己帮会的约战链接')
        if invite.status == '0' and invite.expire_time >= datetime.now():
            raise ServiceException(message='生效中的链接不能删除，请先强制失效')
        await BattleRegistrationDao.delete_invite(db, invite_id)
        await db.commit()
        return CrudResponseModel(is_success=True, message='约战链接已删除')

    @classmethod
    async def list_registrations_service(
        cls,
        db: AsyncSession,
        current_user: CurrentUserModel,
        status: str | None = None,
        registration_type: str | None = 'signup',
    ) -> list[dict]:
        role_scope = cls._get_role_scope(current_user)
        if role_scope == 'user':
            raise ServiceException(message='当前角色无权查看约战审核列表')
        owner_user_id = None if role_scope == 'admin' else current_user.user.user_id
        await BattleRegistrationDao.mark_expired_invites(db)
        await db.commit()
        active_invite = await BattleRegistrationDao.get_latest_active_invite(db, owner_user_id)
        if not active_invite:
            return []
        rows = await BattleRegistrationDao.list_registrations(
            db,
            owner_user_id,
            status,
            active_invite.invite_id,
            registration_type=cls._normalize_registration_type(registration_type),
        )
        return [cls._format_registration(item) for item in rows]

    @classmethod
    async def list_leave_registrations_for_schedule_service(
        cls, db: AsyncSession, current_user: CurrentUserModel
    ) -> list[dict]:
        role_scope = cls._get_role_scope(current_user)
        if role_scope == 'user':
            raise ServiceException(message='当前角色无权查看请假排除列表')
        owner_user_id = None if role_scope == 'admin' else current_user.user.user_id
        await BattleRegistrationDao.mark_expired_invites(db)
        await db.commit()
        active_invite = await BattleRegistrationDao.get_latest_active_invite(db, owner_user_id)
        if not active_invite:
            return []
        rows = await BattleRegistrationDao.list_registrations(
            db,
            owner_user_id,
            invite_id=active_invite.invite_id,
            registration_type='leave',
            status_list=['0', '1'],
        )
        return [cls._format_registration(item) for item in rows]

    @classmethod
    async def approve_registration_service(
        cls, db: AsyncSession, current_user: CurrentUserModel, data: BattleRegistrationReviewModel
    ) -> CrudResponseModel:
        registration = await cls._get_scoped_pending_registration(db, current_user, data.registration_id)
        await BattleRegistrationDao.update_registration(
            db,
            registration.registration_id,
            {
                'approval_status': '1',
                'approval_time': datetime.now(),
                'approval_by': current_user.user.user_name or str(current_user.user.user_id),
                'approval_comment': (data.approval_comment or '').strip(),
            },
        )
        await db.commit()
        return CrudResponseModel(is_success=True, message='约战报名审核通过')

    @classmethod
    async def reject_registration_service(
        cls, db: AsyncSession, current_user: CurrentUserModel, data: BattleRegistrationReviewModel
    ) -> CrudResponseModel:
        registration = await cls._get_scoped_pending_registration(db, current_user, data.registration_id)
        await BattleRegistrationDao.update_registration(
            db,
            registration.registration_id,
            {
                'approval_status': '2',
                'approval_time': datetime.now(),
                'approval_by': current_user.user.user_name or str(current_user.user.user_id),
                'approval_comment': (data.approval_comment or '').strip(),
            },
        )
        await db.commit()
        return CrudResponseModel(is_success=True, message='已拒绝约战报名')

    @classmethod
    async def get_public_invite_service(cls, db: AsyncSession, invite_code: str) -> dict:
        invite = await cls._get_invite_or_raise(db, invite_code)
        return cls._format_invite(invite, public=True)

    @classmethod
    async def search_public_members_service(cls, db: AsyncSession, invite_code: str, keyword: str) -> list[dict]:
        invite = await cls._get_active_invite_or_raise(db, invite_code)
        keyword = keyword.strip()
        if not keyword:
            return []
        members = await BattleRegistrationDao.search_members(db, invite.owner_user_id, keyword)
        registrations = await BattleRegistrationDao.list_effective_registrations_for_members(
            db, invite.invite_id, [item.member_id for item in members]
        )
        registration_map: dict[int, GuildBattleRegistration] = {}
        for registration in registrations:
            if registration.member_id not in registration_map:
                registration_map[registration.member_id] = registration
        return [
            {
                'member_id': item.member_id,
                'player_name': item.player_name,
                'player_class': item.player_class or '',
                'secondary_class': item.secondary_class or '',
                'role_in_guild': item.role_in_guild or '',
                'remark': item.remark or '',
                'join_time': item.join_time,
                'current_registration_type': cls._normalize_registration_type(
                    registration_map[item.member_id].registration_type
                )
                if item.member_id in registration_map
                else '',
                'current_registration_status': registration_map[item.member_id].approval_status
                if item.member_id in registration_map
                else '',
            }
            for item in members
        ]

    @classmethod
    async def get_public_profession_options_service(cls, db: AsyncSession, invite_code: str) -> list[dict]:
        await cls._get_active_invite_or_raise(db, invite_code)
        return await ProfessionService.get_enabled_profession_options_service(db)

    @classmethod
    async def submit_public_registration_service(
        cls, db: AsyncSession, invite_code: str, data: PublicBattleRegistrationModel,
        *, current_user: CurrentUserModel | None = None,
    ) -> CrudResponseModel:
        return await cls._submit_member_choice(db, current_user, invite_code, data, 'signup')

    @classmethod
    async def submit_public_leave_service(
        cls, db: AsyncSession, invite_code: str, data: PublicBattleLeaveApplicationModel,
        *, current_user: CurrentUserModel | None = None,
    ) -> CrudResponseModel:
        return await cls._submit_member_choice(db, current_user, invite_code, data, 'leave')

    @classmethod
    async def _submit_member_choice(
        cls, db: AsyncSession, current_user: CurrentUserModel | None, invite_code: str,
        data: PublicBattleRegistrationModel | PublicBattleLeaveApplicationModel, kind: str,
    ) -> CrudResponseModel:
        account_id = getattr(getattr(current_user, 'user', None), 'user_id', None)
        if isinstance(account_id, bool) or not isinstance(account_id, int) or not 0 < account_id <= (1 << 63) - 1:
            raise AuthException(message='用户未登录，请先完成登录')
        try:
            # Every self-service mutation locks invitation first, then member.
            # Never invoke lazy schema migrations inside this transaction.
            invite = await cls._get_active_invite_or_raise(db, invite_code, for_update=True)
            member = await BattleRegistrationDao.lock_member_for_invite(db, invite.owner_user_id, data.member_id)
            if not member or member.user_id != invite.owner_user_id:
                raise PermissionException(data={'errorKey': 'MEMBER_NOT_ALLOWED'}, message='无权操作该邀请中的成员')
            if not member.member_user_id:
                raise PermissionException(data={'errorKey': 'MEMBER_BINDING_REQUIRED'}, message='请先完成账号与帮会成员绑定')
            if member.member_user_id != account_id:
                raise PermissionException(data={'errorKey': 'MEMBER_NOT_OWNER'}, message='只能提交登录账号本人的报名或请假')
            if invite.status != '0' or invite.expire_time <= datetime.now():
                raise ServiceException(data={'errorKey': 'INVITE_INACTIVE'}, message='链接已过期或已停用')
            primary = (member.player_class or '').strip()
            secondary = (member.secondary_class or '').strip()
            if kind == 'signup':
                primary = (data.player_class or '').strip() or primary
                secondary = (data.secondary_class or '').strip() or secondary
                verified = {(member.player_class or '').strip(), (member.secondary_class or '').strip()}
                if primary not in verified or secondary not in verified:
                    raise PermissionException(data={'errorKey': 'PROFESSION_NOT_BOUND'}, message='报名职业必须来自本人已绑定成员资料')
            exists = await BattleRegistrationDao.get_effective_registration(
                db, invite.invite_id, member.member_id, ensure_schema=False,
            )
            label = '请假申请' if kind == 'leave' else '约战报名'
            if exists:
                existing_type = cls._normalize_registration_type(exists.registration_type) or 'signup'
                if existing_type == kind:
                    raise ServiceException(data={'errorKey': 'REGISTRATION_EXISTS'}, message=f'该成员已提交过{label}，请勿重复提交')
                await BattleRegistrationDao.cancel_effective_registration(
                    db, invite.invite_id, member.member_id, existing_type, ensure_schema=False,
                )
                old_label = '约战报名' if kind == 'leave' else '请假申请'
                message = f'{label}已提交，原{old_label}已自动取消'
            else:
                message = f'{label}已提交，请等待审核'
            payload = {
                'invite_id': invite.invite_id,
                'invite_code': invite.invite_code,
                'guild_id': invite.owner_user_id,
                'owner_user_id': invite.owner_user_id,
                'applicant_user_id': account_id,
                'member_id': member.member_id,
                'registration_type': kind,
                'player_name': member.player_name,
                'player_class': primary,
                'secondary_class': secondary,
                'role_in_guild': member.role_in_guild or '',
                'remark': (data.remark or '').strip(),
            }
            if kind == 'signup':
                payload.update(applicant_name=(data.applicant_name or '').strip(), applicant_contact=(data.applicant_contact or '').strip())
            await BattleRegistrationDao.create_registration(db, payload, ensure_schema=False)
            await db.commit()
            return CrudResponseModel(is_success=True, message=message)
        except BaseException:
            await db.rollback()
            raise

    @classmethod
    async def submit_public_join_service(
        cls, db: AsyncSession, invite_code: str, data: PublicBattleJoinApplicationModel
    ) -> CrudResponseModel:
        invite = await cls._get_active_invite_or_raise(db, invite_code)
        player_name = data.player_name.strip()
        if not player_name:
            raise ServiceException(message='玩家角色名不能为空')
        guild = await JoinApplicationDao.get_guild_by_id(db, invite.owner_user_id)
        if not guild:
            raise ServiceException(message='目标帮会不存在')
        remark_parts = cls._build_join_remark(data)
        await JoinApplicationDao.create_application(
            db,
            {
                'applicant_user_id': 0,
                'guild_id': guild.user_id,
                'guild_name': guild.nick_name,
                'player_name': player_name,
                'player_class': (data.player_class or '').strip(),
                'secondary_class': (data.secondary_class or '').strip(),
                'remark': '；'.join(remark_parts),
            },
        )
        await db.commit()
        return CrudResponseModel(is_success=True, message='入会申请已提交，请等待管理员审核')

    @classmethod
    async def submit_authenticated_join_service(
        cls,
        db: AsyncSession,
        current_user: CurrentUserModel,
        invite_code: str,
        data: PublicBattleJoinApplicationModel,
    ) -> CrudResponseModel:
        invite = await cls._get_active_invite_or_raise(db, invite_code)
        remark_parts = cls._build_join_remark(data)
        application = JoinApplicationCreateModel(
            guild_id=invite.owner_user_id,
            player_name=data.player_name,
            player_class=data.player_class or '',
            secondary_class=data.secondary_class or '',
            remark='；'.join(remark_parts),
        )
        return await JoinApplicationService.submit_application_service(db, current_user, application)

    @classmethod
    def _build_join_remark(cls, data: PublicBattleJoinApplicationModel) -> list[str]:
        remark_parts = []
        for value, label in ((data.applicant_name, '申请人：'), (data.applicant_contact, '联系方式：'), (data.remark, '')):
            normalized = (value or '').strip()
            if normalized:
                remark_parts.append(f'{label}{normalized}')
        return remark_parts

    @classmethod
    async def _get_scoped_pending_registration(
        cls, db: AsyncSession, current_user: CurrentUserModel, registration_id: int
    ) -> GuildBattleRegistration:
        role_scope = cls._get_role_scope(current_user)
        if role_scope == 'user':
            raise ServiceException(message='当前角色无权审核约战报名')
        registration = await BattleRegistrationDao.get_pending_registration_by_id(db, registration_id)
        if not registration:
            raise ServiceException(message='报名不存在或已处理')
        if role_scope == 'common' and registration.owner_user_id != current_user.user.user_id:
            raise ServiceException(message='只能处理自己帮会的约战报名')
        invite = await BattleRegistrationDao.get_invite_by_id(db, registration.invite_id or 0)
        if not invite or invite.status != '0' or invite.expire_time < datetime.now():
            raise ServiceException(message='报名链接已失效，不能继续审核')
        if role_scope == 'common' and invite.owner_user_id != current_user.user.user_id:
            raise ServiceException(message='只能处理自己帮会的约战报名')
        return registration

    @classmethod
    async def _get_invite_or_raise(cls, db: AsyncSession, invite_code: str, *, for_update: bool = False) -> GuildBattleInvite:
        getter = BattleRegistrationDao.lock_invite_by_code if for_update else BattleRegistrationDao.get_invite_by_code
        invite = await getter(db, invite_code.strip())
        if not invite:
            raise ServiceException(data={'errorKey': 'INVITE_NOT_FOUND'}, message='链接不存在')
        return invite

    @classmethod
    async def _get_active_invite_or_raise(cls, db: AsyncSession, invite_code: str, *, for_update: bool = False) -> GuildBattleInvite:
        invite = await cls._get_invite_or_raise(db, invite_code, for_update=for_update)
        if invite.status != '0' or invite.expire_time <= datetime.now():
            raise ServiceException(data={'errorKey': 'INVITE_INACTIVE'}, message='链接已过期或已停用')
        return invite

    @classmethod
    async def _new_invite_code(cls, db: AsyncSession) -> str:
        for _ in range(5):
            invite_code = token_urlsafe(12).replace('-', '').replace('_', '')[:16]
            if not await BattleRegistrationDao.get_invite_by_code(db, invite_code):
                return invite_code
        raise ServiceException(message='生成链接失败，请重试')

    @classmethod
    def _format_invite(cls, invite: GuildBattleInvite, public: bool = False) -> dict:
        expired = invite.expire_time < datetime.now()
        data = {
            'invite_id': invite.invite_id,
            'invite_code': invite.invite_code,
            'guild_name': invite.guild_name or '',
            'battle_name': invite.battle_name,
            'battle_time': invite.battle_time,
            'expire_time': invite.expire_time,
            'status': '1' if expired else invite.status,
            'expired': expired,
            'remark': invite.remark or '',
        }
        if not public:
            data.update({
                'owner_user_id': invite.owner_user_id,
                'create_time': invite.create_time,
                'public_path': f'/public/battle/{invite.invite_code}',
            })
        return data

    @classmethod
    def _format_registration(cls, item: GuildBattleRegistration) -> dict:
        return {
            'registration_id': item.registration_id,
            'invite_id': item.invite_id,
            'invite_code': item.invite_code or '',
            'guild_id': item.guild_id,
            'owner_user_id': item.owner_user_id,
            'member_id': item.member_id,
            'registration_type': cls._normalize_registration_type(item.registration_type) or 'signup',
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
    def _parse_datetime(cls, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=None)
        except ValueError:
            raise ServiceException(message='约战时间格式不正确')

    @classmethod
    def _get_role_scope(cls, current_user: CurrentUserModel) -> str:
        role_keys = {str(item).strip() for item in (current_user.roles or []) if str(item).strip()}
        if 'admin' in role_keys:
            return 'admin'
        if 'common' in role_keys:
            return 'common'
        return 'user'

    @classmethod
    def _normalize_registration_type(cls, registration_type: str | None) -> str | None:
        value = (registration_type or '').strip().lower()
        if not value:
            return None
        if value not in {'signup', 'leave'}:
            raise ServiceException(message='申请类型不正确')
        return value

    @classmethod
    def _registration_type_label(cls, registration_type: str | None) -> str:
        value = cls._normalize_registration_type(registration_type) or 'signup'
        return '请假申请' if value == 'leave' else '约战报名'
