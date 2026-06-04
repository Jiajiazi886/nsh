from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_guild.dao.join_application_dao import JoinApplicationDao
from module_guild.dao.member_dao import MemberDao
from module_guild.entity.do.join_application_do import GuildJoinApplication
from module_guild.entity.do.member_do import GuildMember
from module_guild.entity.vo.join_application_vo import JoinApplicationCreateModel, JoinApplicationReviewModel


class JoinApplicationService:
    @classmethod
    async def search_guilds_service(cls, db: AsyncSession, keyword: str) -> list[dict]:
        keyword = keyword.strip()
        if not keyword:
            return []
        rows = await JoinApplicationDao.search_guilds(db, keyword)
        return [{'guild_id': row.user_id, 'guild_name': row.nick_name, 'owner_user_name': row.user_name} for row in rows]

    @classmethod
    async def submit_application_service(
        cls, db: AsyncSession, current_user: CurrentUserModel, data: JoinApplicationCreateModel
    ) -> CrudResponseModel:
        role_scope = cls._get_role_scope(current_user)
        if role_scope == 'common':
            raise ServiceException(message='帮会大当家不通过个人入会流程提交申请')

        applicant_user_id = current_user.user.user_id
        player_name = data.player_name.strip()
        if not player_name:
            raise ServiceException(message='玩家角色名不能为空')
        if role_scope == 'user':
            await cls._ensure_user_can_apply(db, applicant_user_id)

        guild = await JoinApplicationDao.get_guild_by_id(db, data.guild_id)
        if not guild:
            raise ServiceException(message='目标帮会不存在')
        if guild.user_id == applicant_user_id:
            raise ServiceException(message='不能申请加入自己的帮会')

        await JoinApplicationDao.create_application(
            db,
            {
                'applicant_user_id': applicant_user_id,
                'guild_id': guild.user_id,
                'guild_name': guild.nick_name,
                'player_name': player_name,
                'player_class': (data.player_class or '').strip(),
                'secondary_class': (data.secondary_class or '').strip(),
                'remark': (data.remark or '').strip(),
            },
        )
        await db.commit()
        return CrudResponseModel(is_success=True, message='申请已提交，等待审核')

    @classmethod
    async def get_my_status_service(cls, db: AsyncSession, current_user: CurrentUserModel) -> dict:
        applicant_user_id = current_user.user.user_id
        membership = await MemberDao.get_member_by_member_user(db, applicant_user_id)
        effective_application = await JoinApplicationDao.get_latest_effective_application(db, applicant_user_id)
        applications = await JoinApplicationDao.list_my_applications(db, applicant_user_id)

        guild_name = None
        if membership:
            guild = await JoinApplicationDao.get_guild_by_id(db, membership.user_id)
            guild_name = guild.nick_name if guild else ''

        return {
            'current_membership': cls._format_membership(membership, guild_name),
            'current_application': cls._format_application(effective_application),
            'applications': [cls._format_application(item) for item in applications],
        }

    @classmethod
    async def quit_guild_service(cls, db: AsyncSession, current_user: CurrentUserModel) -> CrudResponseModel:
        role_scope = cls._get_role_scope(current_user)
        if role_scope == 'common':
            raise ServiceException(message='帮会大当家不能通过该接口退会')

        applicant_user_id = current_user.user.user_id
        membership = await MemberDao.get_member_by_member_user(db, applicant_user_id)
        if not membership:
            raise ServiceException(message='当前未加入任何帮会')

        await MemberDao.delete_member_by_member_user(db, applicant_user_id)
        await JoinApplicationDao.archive_effective_applications(db, applicant_user_id)
        await db.commit()
        return CrudResponseModel(is_success=True, message='退会成功')

    @classmethod
    async def list_pending_applications_service(cls, db: AsyncSession, current_user: CurrentUserModel) -> list[dict]:
        role_scope = cls._get_role_scope(current_user)
        if role_scope == 'user':
            raise ServiceException(message='当前角色无权查看审核列表')

        guild_id = None if role_scope == 'admin' else current_user.user.user_id
        rows = await JoinApplicationDao.list_pending_applications(db, guild_id)
        result = []
        for row in rows:
            application = row[0]
            result.append(
                {
                    'application_id': application.application_id,
                    'applicant_user_id': application.applicant_user_id,
                    'applicant_user_name': row.applicant_user_name or 'public',
                    'applicant_nick_name': row.applicant_nick_name or '公开链接',
                    'guild_id': application.guild_id,
                    'guild_name': application.guild_name,
                    'player_name': application.player_name,
                    'player_class': application.player_class or '',
                    'secondary_class': application.secondary_class or '',
                    'remark': application.remark or '',
                    'review_status': application.review_status,
                    'apply_time': application.apply_time,
                }
            )
        return result

    @classmethod
    async def approve_application_service(
        cls, db: AsyncSession, current_user: CurrentUserModel, data: JoinApplicationReviewModel
    ) -> CrudResponseModel:
        role_scope = cls._get_role_scope(current_user)
        if role_scope == 'user':
            raise ServiceException(message='当前角色无权审核入会申请')

        application = await JoinApplicationDao.get_pending_application_by_id(db, data.application_id)
        if not application:
            raise ServiceException(message='申请不存在或已处理')
        cls._ensure_review_scope(application.guild_id, current_user, role_scope)

        existing_member = None
        if application.applicant_user_id:
            applicant_membership = await MemberDao.get_member_by_member_user(db, application.applicant_user_id)
            if applicant_membership and applicant_membership.user_id != application.guild_id:
                raise ServiceException(message='该账号已加入其他帮会，无法重复通过')

            existing_member = await MemberDao.get_member_by_guild_and_member_user(
                db, application.guild_id, application.applicant_user_id
            )
        else:
            exists = await MemberDao.check_member_exists(db, application.guild_id, application.player_name)
            if exists:
                raise ServiceException(message='该玩家已在成员管理中')
        member_payload = {
            'guild_id': application.guild_id,
            'user_id': application.guild_id,
            'member_user_id': application.applicant_user_id,
            'player_name': application.player_name,
            'player_class': application.player_class or '',
            'secondary_class': application.secondary_class or '',
            'remark': application.remark or '',
            'role_in_guild': '成员',
            'join_time': datetime.now(),
            'is_active': '1',
            'source_type': 'application',
            'team_id': None,
            'squad_number': None,
        }
        if existing_member:
            await MemberDao.update_member(db, existing_member.member_id, member_payload)
        else:
            await MemberDao.create_member(db, member_payload)

        await JoinApplicationDao.update_application(
            db,
            application.application_id,
            {
                'review_status': '1',
                'review_time': datetime.now(),
                'reviewer_user_id': current_user.user.user_id,
            },
        )
        await db.commit()
        return CrudResponseModel(is_success=True, message='审核通过')

    @classmethod
    async def reject_application_service(
        cls, db: AsyncSession, current_user: CurrentUserModel, data: JoinApplicationReviewModel
    ) -> CrudResponseModel:
        role_scope = cls._get_role_scope(current_user)
        if role_scope == 'user':
            raise ServiceException(message='当前角色无权审核入会申请')

        application = await JoinApplicationDao.get_pending_application_by_id(db, data.application_id)
        if not application:
            raise ServiceException(message='申请不存在或已处理')
        cls._ensure_review_scope(application.guild_id, current_user, role_scope)

        await JoinApplicationDao.update_application(
            db,
            application.application_id,
            {
                'review_status': '2',
                'review_time': datetime.now(),
                'reviewer_user_id': current_user.user.user_id,
            },
        )
        await db.commit()
        return CrudResponseModel(is_success=True, message='已拒绝该申请')

    @classmethod
    async def _ensure_user_can_apply(cls, db: AsyncSession, applicant_user_id: int) -> None:
        membership = await MemberDao.get_member_by_member_user(db, applicant_user_id)
        if membership:
            raise ServiceException(message='一个账号只能申请一个帮会，且同一时间只能加入一个帮会')

        effective_application = await JoinApplicationDao.get_latest_effective_application(db, applicant_user_id)
        if effective_application:
            raise ServiceException(message='一个账号只能申请一个帮会，且同一时间只能加入一个帮会')

    @classmethod
    def _ensure_review_scope(cls, guild_id: int, current_user: CurrentUserModel, role_scope: str) -> None:
        if role_scope == 'common' and guild_id != current_user.user.user_id:
            raise ServiceException(message='只能处理自己帮会的入会申请')

    @classmethod
    def _get_role_scope(cls, current_user: CurrentUserModel) -> str:
        role_keys = {str(item).strip() for item in (current_user.roles or []) if str(item).strip()}
        if 'admin' in role_keys:
            return 'admin'
        if 'common' in role_keys:
            return 'common'
        return 'user'

    @classmethod
    def _format_application(cls, application: GuildJoinApplication | None) -> dict | None:
        if not application:
            return None
        return {
            'application_id': application.application_id,
            'applicant_user_id': application.applicant_user_id,
            'guild_id': application.guild_id,
            'guild_name': application.guild_name,
            'player_name': application.player_name,
            'player_class': application.player_class or '',
            'secondary_class': application.secondary_class or '',
            'remark': application.remark or '',
            'review_status': application.review_status,
            'del_flag': application.del_flag,
            'apply_time': application.apply_time,
            'review_time': application.review_time,
            'reviewer_user_id': application.reviewer_user_id,
        }

    @classmethod
    def _format_membership(cls, membership: GuildMember | None, guild_name: str | None) -> dict | None:
        if not membership:
            return None
        return {
            'member_id': membership.member_id,
            'guild_id': membership.guild_id,
            'guild_name': guild_name or '',
            'guild_owner_user_id': membership.user_id,
            'member_user_id': membership.member_user_id,
            'player_name': membership.player_name,
            'player_class': membership.player_class or '',
            'secondary_class': membership.secondary_class or '',
            'remark': membership.remark or '',
            'source_type': membership.source_type or 'manual',
            'join_time': membership.join_time,
        }
