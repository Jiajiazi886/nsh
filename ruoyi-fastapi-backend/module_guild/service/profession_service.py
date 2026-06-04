from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_guild.dao.profession_dao import ProfessionDao
from module_guild.entity.vo.profession_vo import DeleteProfessionModel, ProfessionModel, ProfessionPageQueryModel
from utils.common_util import CamelCaseUtil


class ProfessionService:
    @classmethod
    async def get_profession_list_service(cls, db: AsyncSession, query_object: ProfessionPageQueryModel, is_page=True):
        return await ProfessionDao.get_profession_list(db, query_object, is_page)

    @classmethod
    async def get_enabled_profession_options_service(cls, db: AsyncSession) -> list[dict]:
        professions = await ProfessionDao.get_enabled_profession_list(db)
        return [
            {
                'professionId': item.profession_id,
                'professionName': item.profession_name,
                'orderNum': item.order_num,
            }
            for item in professions
        ]

    @classmethod
    async def check_profession_name_unique(cls, db: AsyncSession, profession: ProfessionModel) -> bool:
        profession_id = -1 if profession.profession_id is None else profession.profession_id
        existing = await ProfessionDao.get_profession_detail_by_name(db, profession.profession_name or '')
        return not existing or existing.profession_id == profession_id

    @classmethod
    async def add_profession_service(cls, db: AsyncSession, profession: ProfessionModel) -> CrudResponseModel:
        if not await cls.check_profession_name_unique(db, profession):
            raise ServiceException(message=f'新增职业 {profession.profession_name} 失败，职业名称已存在')
        await ProfessionDao.add_profession(db, profession)
        await db.commit()
        return CrudResponseModel(is_success=True, message='新增成功')

    @classmethod
    async def edit_profession_service(cls, db: AsyncSession, profession: ProfessionModel) -> CrudResponseModel:
        if profession.profession_id is None:
            raise ServiceException(message='职业ID不能为空')
        profession_info = await ProfessionDao.get_profession_detail_by_id(db, profession.profession_id)
        if not profession_info:
            raise ServiceException(message='职业不存在')
        if not await cls.check_profession_name_unique(db, profession):
            raise ServiceException(message=f'修改职业 {profession.profession_name} 失败，职业名称已存在')
        edit_profession = profession.model_dump(exclude_unset=True)
        await ProfessionDao.edit_profession(db, edit_profession)
        await db.commit()
        return CrudResponseModel(is_success=True, message='修改成功')

    @classmethod
    async def delete_profession_service(cls, db: AsyncSession, delete_model: DeleteProfessionModel) -> CrudResponseModel:
        if delete_model.profession_ids:
            for profession_id in delete_model.profession_ids.split(','):
                await ProfessionDao.delete_profession(db, int(profession_id))
            await db.commit()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def profession_detail_service(cls, db: AsyncSession, profession_id: int) -> ProfessionModel:
        profession = await ProfessionDao.get_profession_detail_by_id(db, profession_id)
        return ProfessionModel(**CamelCaseUtil.transform_result(profession)) if profession else ProfessionModel()
