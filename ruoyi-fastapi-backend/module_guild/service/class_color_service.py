from sqlalchemy.ext.asyncio import AsyncSession
from common.vo import CrudResponseModel
from module_guild.constants.class_color_defaults import DEFAULT_GUILD_CLASS_COLORS, DEFAULT_GUILD_CLASS_COLOR_MAP
from module_guild.dao.class_color_dao import ClassColorDao
from module_guild.dao.profession_dao import ProfessionDao
from module_guild.entity.vo.class_color_vo import ClassColorSaveModel
from utils.log_util import logger

class ClassColorService:
    @classmethod
    def _is_legacy_empty_color(cls, saved, default: dict) -> bool:
        return (
            saved.bg_color.upper() == '#FFFFFF'
            and saved.text_color.upper() == '#000000'
            and default.get('bg_color', '#FFFFFF').upper() != '#FFFFFF'
        )

    @classmethod
    def _resolve_color(cls, class_name: str, saved_map: dict) -> dict:
        saved = saved_map.get(class_name)
        default = DEFAULT_GUILD_CLASS_COLOR_MAP.get(class_name, {})
        if saved and not cls._is_legacy_empty_color(saved, default):
            return {
                'class_name': class_name,
                'bg_color': saved.bg_color,
                'text_color': saved.text_color,
            }

        return {
            'class_name': class_name,
            'bg_color': default.get('bg_color', '#FFFFFF'),
            'text_color': default.get('text_color', '#000000'),
        }

    @classmethod
    async def get_colors_service(cls, db: AsyncSession, current_user) -> list[dict]:
        user_id = current_user.user.user_id
        items = await ClassColorDao.query_by_user(db, user_id)
        saved_map = {i.class_name: i for i in items}
        professions = await ProfessionDao.get_enabled_profession_list(db)
        if not professions:
            result_map = {item['class_name']: dict(item) for item in DEFAULT_GUILD_CLASS_COLORS}
            for item in items:
                result_map[item.class_name] = {
                    'class_name': item.class_name,
                    'bg_color': item.bg_color,
                    'text_color': item.text_color,
                }
            return list(result_map.values())

        return [
            cls._resolve_color(profession.profession_name, saved_map)
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
