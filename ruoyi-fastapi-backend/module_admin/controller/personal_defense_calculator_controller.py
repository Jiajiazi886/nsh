from typing import Annotated

from fastapi import File, Path, Request, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, DynamicResponseModel, ResponseBaseModel
from module_admin.entity.vo.internal_power_panel_setting_vo import PanelRecognitionResultModel
from module_admin.entity.vo.personal_defense_calculator_vo import (
    DefenseCalculatorSettingModel,
    PersonalPvpAttackPanelModel,
    PersonalPvpAttackPanelPayload,
)
from module_admin.entity.vo.pvp_attack_panel_vo import PvpAttackPanelModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.internal_power_panel_recognition_service import InternalPowerPanelRecognitionService
from module_admin.service.personal_defense_calculator_service import PersonalDefenseCalculatorService
from module_admin.service.pvp_attack_panel_service import PvpAttackPanelService
from utils.response_util import ResponseUtil

personal_defense_calculator_controller = APIRouterPro(
    prefix='/personal/defense-calculator',
    order_num=92,
    tags=['个人管理-防守计算器'],
    dependencies=[PreAuthDependency()],
)


@personal_defense_calculator_controller.get(
    '/attack-panels',
    response_model=DataResponseModel[list[PvpAttackPanelModel]],
    dependencies=[UserInterfaceAuthDependency('personal:defense-calculator:list')],
)
async def get_enabled_pvp_attack_panels(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await PvpAttackPanelService.get_enabled_services(query_db))


@personal_defense_calculator_controller.get(
    '/personal-attack-panels',
    response_model=DataResponseModel[list[PersonalPvpAttackPanelModel]],
    dependencies=[UserInterfaceAuthDependency('personal:defense-calculator:list')],
)
async def get_personal_pvp_attack_panels(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    return ResponseUtil.success(data=await PersonalDefenseCalculatorService.list_panels_services(query_db, current_user))


@personal_defense_calculator_controller.post(
    '/personal-attack-panels',
    response_model=DataResponseModel[PersonalPvpAttackPanelModel],
    dependencies=[UserInterfaceAuthDependency('personal:defense-calculator:list')],
)
@Log(title='个人进攻方面板', business_type=BusinessType.INSERT)
async def add_personal_pvp_attack_panel(
    request: Request,
    payload: PersonalPvpAttackPanelPayload,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await PersonalDefenseCalculatorService.add_panel_services(query_db, current_user, payload)
    return ResponseUtil.success(msg=result.message, data=result.result)


@personal_defense_calculator_controller.put(
    '/personal-attack-panels/{panel_id}',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('personal:defense-calculator:list')],
)
@Log(title='个人进攻方面板', business_type=BusinessType.UPDATE)
async def update_personal_pvp_attack_panel(
    request: Request,
    panel_id: Annotated[int, Path(description='个人进攻方面板ID')],
    payload: PersonalPvpAttackPanelPayload,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await PersonalDefenseCalculatorService.update_panel_services(query_db, current_user, panel_id, payload)
    return ResponseUtil.success(msg=result.message)


@personal_defense_calculator_controller.delete(
    '/personal-attack-panels/{panel_id}',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('personal:defense-calculator:list')],
)
@Log(title='个人进攻方面板', business_type=BusinessType.DELETE)
async def delete_personal_pvp_attack_panel(
    request: Request,
    panel_id: Annotated[int, Path(description='个人进攻方面板ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await PersonalDefenseCalculatorService.delete_panel_services(query_db, current_user, panel_id)
    return ResponseUtil.success(msg=result.message)


@personal_defense_calculator_controller.get(
    '/setting',
    response_model=DynamicResponseModel[DefenseCalculatorSettingModel],
    dependencies=[UserInterfaceAuthDependency('personal:defense-calculator:list')],
)
async def get_personal_defense_calculator_setting(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await PersonalDefenseCalculatorService.get_setting_services(query_db, current_user)
    return ResponseUtil.success(model_content=result)


@personal_defense_calculator_controller.put(
    '/setting',
    response_model=DynamicResponseModel[DefenseCalculatorSettingModel],
    dependencies=[UserInterfaceAuthDependency('personal:defense-calculator:list')],
)
@Log(title='个人防守计算器设置', business_type=BusinessType.UPDATE)
async def save_personal_defense_calculator_setting(
    request: Request,
    payload: DefenseCalculatorSettingModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await PersonalDefenseCalculatorService.save_setting_services(query_db, current_user, payload)
    return ResponseUtil.success(model_content=result, msg='保存成功')


@personal_defense_calculator_controller.post(
    '/recognize-panel-image',
    summary='识别防守面板图片',
    response_model=DataResponseModel[PanelRecognitionResultModel],
    dependencies=[UserInterfaceAuthDependency('personal:defense-calculator:list')],
)
@Log(title='防守面板图片识别', business_type=BusinessType.INSERT)
async def recognize_defense_panel_image(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    file: Annotated[UploadFile, File(description='逆水寒手游防守属性面板图片')],
) -> Response:
    result = await InternalPowerPanelRecognitionService.recognize_defense_image_services(
        query_db,
        current_user,
        file,
    )
    return ResponseUtil.success(data=result, msg='识别成功' if result.success else '识别失败')


@personal_defense_calculator_controller.post(
    '/recognize-internal-power-benefits',
    summary='识别内功防御词条总体收益图片',
    response_model=DataResponseModel[PanelRecognitionResultModel],
    dependencies=[UserInterfaceAuthDependency('personal:defense-calculator:list')],
)
@Log(title='内功防御词条图片识别', business_type=BusinessType.INSERT)
async def recognize_internal_power_benefit_image(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    file: Annotated[UploadFile, File(description='逆水寒手游内功词条总体收益图片')],
) -> Response:
    result = await InternalPowerPanelRecognitionService.recognize_internal_power_benefit_image_services(
        query_db,
        current_user,
        file,
    )
    return ResponseUtil.success(data=result, msg='识别成功' if result.success else '识别失败')
