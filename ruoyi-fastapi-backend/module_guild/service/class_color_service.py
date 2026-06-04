from sqlalchemy.ext.asyncio import AsyncSession
from common.vo import CrudResponseModel
from module_guild.dao.class_color_dao import ClassColorDao
from module_guild.dao.profession_dao import ProfessionDao
from module_guild.entity.vo.class_color_vo import ClassColorSaveModel
from utils.log_util import logger

class ClassColorService:
    @classmethod
    async def get_colors_service(cls, db: AsyncSession, current_user) -> list[dict]:
        user_id = current_user.user.user_id
        items = await ClassColorDao.query_by_user(db, user_id)
        saved_map = {i.class_name: i for i in items}
        professions = await ProfessionDao.get_enabled_profession_list(db)
        if not professions:
            return [
                {'class_name': i.class_name, 'bg_color': i.bg_color, 'text_color': i.text_color}
                for i in items
            ]
        return [
            {
                'class_name': profession.profession_name,
                'bg_color': saved_map.get(profession.profession_name).bg_color
                if profession.profession_name in saved_map
                else '#FFFFFF',
                'text_color': saved_map.get(profession.profession_name).text_color
                if profession.profession_name in saved_map
                else '#000000',
            }
            for profession in professions
        ]

    @classmethod
    async def save_colors_service(cls, db: AsyncSession, current_user, data: ClassColorSaveModel) -> CrudResponseModel:
        user_id = current_user.user.user_id
        professions = await ProfessionDao.get_enabled_profession_list(db)
        profession_names = {profession.profession_name for profession in professions}
        await ClassColorDao.delete_by_user(db, user_id)
        colors = [
            color for color in data.colors
            if not profession_names or color.class_name in profession_names
        ]
        if colors:
            await ClassColorDao.batch_insert(db, [
                {
                    'class_name': c.class_name,
                    'bg_color': c.bg_color,
                    'text_color': c.text_color,
                    'user_id': user_id,
                }
                for c in colors
            ])
        await db.commit()
        return CrudResponseModel(is_success=True, message='保存成功')
