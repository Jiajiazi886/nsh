from typing import Annotated
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_integration.activities.enabled import require_activities_enabled
from module_integration.contract import ApiEnvelope, IntegrationRoute, api_response
from module_integration.player_profile import PlayerProfileInput, PlayerProfileService
from module_guild.service.class_color_service import ClassColorService

player_profile_controller = APIRouterPro(prefix='/api/v1', order_num=92, tags=['账号玩家资料'],
    route_class=IntegrationRoute, dependencies=[Depends(require_activities_enabled)])
CurrentUser = Annotated[CurrentUserModel, CurrentUserDependency()]
Database = Annotated[AsyncSession, DBSessionDependency()]


@player_profile_controller.get('/player-profile/me', response_model=ApiEnvelope)
async def get_me(request: Request, current_user: CurrentUser, db: Database):
    return api_response(request, await PlayerProfileService.get(db, current_user))


@player_profile_controller.put('/player-profile/me', response_model=ApiEnvelope)
async def save_me(request: Request, data: PlayerProfileInput, current_user: CurrentUser, db: Database):
    return api_response(request, await PlayerProfileService.save(db, current_user, data))


@player_profile_controller.get('/organizations/{org_id}/player-profiles/{account_id}', response_model=ApiEnvelope)
async def managed_get(request: Request, org_id: str, account_id: str, current_user: CurrentUser, db: Database):
    return api_response(request, await PlayerProfileService.managed_get(db, current_user, org_id, account_id))


@player_profile_controller.get('/profession-styles', response_model=ApiEnvelope)
async def styles(request: Request, current_user: CurrentUser, db: Database):
    rows = await ClassColorService.get_colors_service(db, current_user, preserve_saved=True)
    return api_response(request, [dict(profession=r['class_name'], backgroundColor=r['bg_color'], textColor=r['text_color']) for r in rows])
