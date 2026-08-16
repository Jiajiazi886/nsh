from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_admin.dao.user_dao import UserDao
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.user_service import UserService


@dataclass(frozen=True)
class AiRecognitionQuotaSnapshot:
    user_id: int
    unlimited: bool
    normal_count: int
    vip_count: int

    @property
    def available_count(self) -> int:
        return self.normal_count + self.vip_count

    def allocate(self, count: int) -> tuple[int, int]:
        """Allocate ordinary recognition quota first, then VIP quota."""
        requested = max(0, int(count or 0))
        normal_count = min(self.normal_count, requested)
        vip_count = requested - normal_count
        return normal_count, vip_count


@dataclass(frozen=True)
class AiRecognitionQuotaConsumption:
    success: bool
    normal_count: int
    vip_count: int
    remaining_normal_count: int
    remaining_vip_count: int


class AiRecognitionQuotaService:
    """Shared quota policy for every AI image-recognition feature."""

    @classmethod
    async def require_quota(
        cls,
        query_db: AsyncSession,
        current_user: CurrentUserModel,
        requested_count: int = 1,
    ) -> AiRecognitionQuotaSnapshot:
        requested = max(0, int(requested_count or 0))
        user_id = int(current_user.user.user_id)
        user = (await UserDao.get_user_detail_by_id(query_db, user_id)).get('user_basic_info')
        if user is None:
            raise ServiceException(message='用户不存在')

        snapshot = AiRecognitionQuotaSnapshot(
            user_id=int(user.user_id),
            unlimited=UserService.is_admin_role(current_user),
            normal_count=max(0, int(getattr(user, 'ai_image_recognition_count', 0) or 0)),
            vip_count=max(0, int(getattr(user, 'vip_ai_image_recognition_count', 0) or 0)),
        )
        if not snapshot.unlimited and snapshot.available_count < requested:
            raise ServiceException(
                message=(
                    'AI识图次数不足，'
                    f'普通剩余{snapshot.normal_count}次，VIP剩余{snapshot.vip_count}次'
                )
            )
        return snapshot

    @classmethod
    async def consume_successes(
        cls,
        query_db: AsyncSession,
        snapshot: AiRecognitionQuotaSnapshot,
        success_count: int,
        update_by: str,
    ) -> AiRecognitionQuotaConsumption:
        count = max(0, int(success_count or 0))
        if snapshot.unlimited or count <= 0:
            return AiRecognitionQuotaConsumption(
                success=True,
                normal_count=0,
                vip_count=0,
                remaining_normal_count=snapshot.normal_count,
                remaining_vip_count=snapshot.vip_count,
            )

        normal_count, vip_count = snapshot.allocate(count)
        deducted = await UserDao.decrement_ai_recognition_counts(
            query_db,
            snapshot.user_id,
            vip_count,
            normal_count,
            update_by,
        )
        return AiRecognitionQuotaConsumption(
            success=deducted,
            normal_count=normal_count if deducted else 0,
            vip_count=vip_count if deducted else 0,
            remaining_normal_count=(
                max(0, snapshot.normal_count - normal_count) if deducted else snapshot.normal_count
            ),
            remaining_vip_count=(
                max(0, snapshot.vip_count - vip_count) if deducted else snapshot.vip_count
            ),
        )
