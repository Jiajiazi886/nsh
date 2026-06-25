import json
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.dao.internal_power_dao import InternalPowerDao
from module_admin.dao.user_dao import UserDao
from module_admin.entity.do.internal_power_do import PersonalInternalPower
from module_admin.entity.vo.internal_power_vo import (
    InternalPowerImportModel,
    InternalPowerListModel,
    InternalPowerModel,
    InternalPowerQuotaModel,
    InternalPowerRecognizeResultModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.user_service import UserService


class InternalPowerService:
    """
    个人内功服务层
    """

    @classmethod
    async def get_list_services(cls, query_db: AsyncSession, current_user: CurrentUserModel) -> InternalPowerListModel:
        user_id = current_user.user.user_id
        rows = await InternalPowerDao.list_by_user_id(query_db, user_id)
        return InternalPowerListModel(
            powers=[cls.__to_model(row) for row in rows],
            quota=await cls.__build_quota(query_db, current_user, len(rows)),
        )

    @classmethod
    async def add_power_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, power: InternalPowerModel
    ) -> InternalPowerModel:
        await cls.__assert_can_add(query_db, current_user)
        now = datetime.now()
        db_power = PersonalInternalPower(
            user_id=current_user.user.user_id,
            name=power.name,
            category=power.category or '',
            category_trait=power.category_trait or '',
            bonus_percent=float(power.bonus_percent or 0),
            entries_json=cls.__json_dumps(power.entries),
            elements_json=cls.__json_dumps(cls.__model_dump(power.elements)),
            remark=power.remark or '',
            create_time=now,
            update_time=now,
        )
        await InternalPowerDao.add(query_db, db_power)
        result = cls.__to_model(db_power)
        await query_db.commit()
        return result

    @classmethod
    async def edit_power_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, power_id: int, power: InternalPowerModel
    ) -> InternalPowerModel:
        existing = await InternalPowerDao.get_by_id(query_db, power_id, current_user.user.user_id)
        if existing is None:
            raise ServiceException(message='内功不存在')
        values = {
            'name': power.name,
            'category': power.category or '',
            'category_trait': power.category_trait or '',
            'bonus_percent': float(power.bonus_percent or 0),
            'entries_json': cls.__json_dumps(power.entries),
            'elements_json': cls.__json_dumps(cls.__model_dump(power.elements)),
            'remark': power.remark or '',
            'update_time': datetime.now(),
        }
        await InternalPowerDao.update(query_db, power_id, current_user.user.user_id, values)
        await query_db.commit()
        updated = await InternalPowerDao.get_by_id(query_db, power_id, current_user.user.user_id)
        return cls.__to_model(updated)

    @classmethod
    async def delete_power_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, power_id: int
    ) -> CrudResponseModel:
        existing = await InternalPowerDao.get_by_id(query_db, power_id, current_user.user.user_id)
        if existing is None:
            raise ServiceException(message='内功不存在')
        await InternalPowerDao.delete(query_db, power_id, current_user.user.user_id)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def import_local_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, import_data: InternalPowerImportModel
    ) -> InternalPowerListModel:
        now = datetime.now()
        for power in import_data.powers:
            db_power = PersonalInternalPower(
                user_id=current_user.user.user_id,
                name=power.name,
                category=power.category or '',
                category_trait=power.category_trait or '',
                bonus_percent=float(power.bonus_percent or 0),
                entries_json=cls.__json_dumps(power.entries),
                elements_json=cls.__json_dumps(cls.__model_dump(power.elements)),
                remark=power.remark or '',
                create_time=now,
                update_time=now,
            )
            await InternalPowerDao.add(query_db, db_power)
        await query_db.commit()
        return await cls.get_list_services(query_db, current_user)

    @classmethod
    async def recognize_images_services(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, image_count: int
    ) -> InternalPowerRecognizeResultModel:
        if image_count <= 0:
            raise ServiceException(message='请至少上传一张图片')
        user = (await UserDao.get_user_detail_by_id(query_db, current_user.user.user_id)).get('user_basic_info')
        if user is None:
            raise ServiceException(message='用户不存在')
        current_count = max(0, int(user.ai_image_recognition_count or 0))
        if current_count < image_count:
            raise ServiceException(message=f'AI识图次数不足，当前剩余{current_count}次')
        remaining_count = current_count - image_count
        await UserDao.edit_user_dao(
            query_db,
            {
                'user_id': user.user_id,
                'ai_image_recognition_count': remaining_count,
                'update_by': current_user.user.user_name,
                'update_time': datetime.now(),
            },
        )
        await query_db.commit()
        return InternalPowerRecognizeResultModel(
            result={},
            consumedCount=image_count,
            remainingAiImageRecognitionCount=remaining_count,
        )

    @classmethod
    async def __assert_can_add(cls, query_db: AsyncSession, current_user: CurrentUserModel) -> None:
        quota = await cls.__build_quota(query_db, current_user)
        if quota.unlimited:
            return
        if quota.max_count is not None and quota.count >= quota.max_count:
            raise ServiceException(message='已超过当前内功上限，请删除后再新增或联系管理员调整上限')

    @classmethod
    async def __build_quota(
        cls, query_db: AsyncSession, current_user: CurrentUserModel, count: int | None = None
    ) -> InternalPowerQuotaModel:
        user = (await UserDao.get_user_detail_by_id(query_db, current_user.user.user_id)).get('user_basic_info')
        current_count = count if count is not None else await InternalPowerDao.count_by_user_id(query_db, user.user_id)
        is_admin = UserService.is_admin_role(current_user)
        is_effective_vip = UserService.is_effective_vip(user)
        unlimited = is_admin or is_effective_vip
        max_count = None if unlimited else max(20, int(user.max_internal_power_count or 20))
        return InternalPowerQuotaModel(
            count=current_count,
            maxCount=max_count,
            unlimited=unlimited,
            isVip='1' if is_effective_vip else '0',
            vipExpireTime=user.vip_expire_time,
        )

    @classmethod
    def __to_model(cls, power: PersonalInternalPower | None) -> InternalPowerModel:
        if power is None:
            raise ServiceException(message='内功不存在')
        return InternalPowerModel(
            id=str(power.power_id),
            powerId=power.power_id,
            userId=power.user_id,
            name=power.name,
            category=power.category or '',
            categoryTrait=power.category_trait or '',
            bonusPercent=power.bonus_percent or 0,
            entries=cls.__json_loads(power.entries_json, []),
            elements=cls.__json_loads(power.elements_json, {}),
            remark=power.remark or '',
            updatedAt=power.update_time,
        )

    @staticmethod
    def __model_dump(value: Any) -> Any:
        if hasattr(value, 'model_dump'):
            return value.model_dump()
        if isinstance(value, list):
            return [InternalPowerService.__model_dump(item) for item in value]
        if isinstance(value, tuple):
            return [InternalPowerService.__model_dump(item) for item in value]
        if isinstance(value, dict):
            return {key: InternalPowerService.__model_dump(item) for key, item in value.items()}
        return value

    @classmethod
    def __json_dumps(cls, value: Any) -> str:
        return json.dumps(cls.__model_dump(value), ensure_ascii=False)

    @staticmethod
    def __json_loads(value: str | None, default: Any) -> Any:
        if not value:
            return default
        try:
            return json.loads(value)
        except Exception:
            return default
