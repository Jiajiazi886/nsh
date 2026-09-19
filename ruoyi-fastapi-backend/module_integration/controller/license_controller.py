from datetime import datetime
from typing import Annotated

from fastapi import Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_integration.contract import ApiEnvelope, IntegrationRoute, api_response
from module_integration.license import LicenseGrantInput, LicenseRemarkInput, LicenseRevokeInput, LicenseService

license_controller = APIRouterPro(prefix='/api/v1', order_num=93, tags=['账号授权'], route_class=IntegrationRoute)
CurrentUser = Annotated[CurrentUserModel, CurrentUserDependency()]
Database = Annotated[AsyncSession, DBSessionDependency()]


@license_controller.get('/license/me', response_model=ApiEnvelope, operation_id='v1LicenseMe')
async def license_me(request: Request, current_user: CurrentUser, db: Database):
    return api_response(request, await LicenseService.me(db, current_user))


@license_controller.post('/license-admin/grants', response_model=ApiEnvelope, operation_id='v1LicenseGrant')
async def license_grant(request: Request, data: LicenseGrantInput, current_user: CurrentUser, db: Database):
    return api_response(request, await LicenseService.grant(db, current_user, data), message='账号授权成功')


@license_controller.post('/license-admin/revocations', response_model=ApiEnvelope, operation_id='v1LicenseRevoke')
async def license_revoke(request: Request, data: LicenseRevokeInput, current_user: CurrentUser, db: Database):
    return api_response(request, await LicenseService.revoke(db, current_user, data), message='账号授权已撤销')


@license_controller.get('/license-admin/accounts', response_model=ApiEnvelope, operation_id='v1LicenseAccounts')
async def license_accounts(
    request: Request,
    current_user: CurrentUser,
    db: Database,
    page: int = Query(default=1, alias='pageNum', ge=1),
    page_size: int = Query(default=20, alias='pageSize', ge=1, le=100),
    keyword: str | None = Query(default=None, max_length=50),
    account_status: str | None = Query(default=None, alias='accountStatus'),
    authorization_status: str | None = Query(default=None, alias='authorizationStatus'),
    plan_type: str | None = Query(default=None, alias='planType'),
):
    return api_response(request, await LicenseService.accounts(db, current_user, page, page_size, keyword, account_status, authorization_status, plan_type))


@license_controller.put('/license-admin/accounts/{user_id}/remark', response_model=ApiEnvelope, operation_id='v1LicenseRemark')
async def license_remark(request: Request, user_id: int, data: LicenseRemarkInput, current_user: CurrentUser, db: Database):
    return api_response(request, await LicenseService.update_remark(db, current_user, user_id, data), message='备注已更新')


@license_controller.get('/license-admin/audit', response_model=ApiEnvelope, operation_id='v1LicenseAudit')
async def license_audit(
    request: Request,
    current_user: CurrentUser,
    db: Database,
    page: int = Query(default=1, alias='pageNum', ge=1),
    page_size: int = Query(default=50, alias='pageSize', ge=1, le=100),
    user_id: int | None = Query(default=None, alias='userId', ge=1),
    account_keyword: str | None = Query(default=None, alias='accountKeyword', max_length=50),
    operator_keyword: str | None = Query(default=None, alias='operatorKeyword', max_length=50),
    action: str | None = Query(default=None, pattern='^(grant|extend|revoke|remark_update)$'),
    batch_id: str | None = Query(default=None, alias='batchId', max_length=64),
    start_time: datetime | None = Query(default=None, alias='startTime'),
    end_time: datetime | None = Query(default=None, alias='endTime'),
):
    return api_response(
        request,
        await LicenseService.audit(
            db, current_user, page, page_size, user_id, account_keyword, operator_keyword,
            action, batch_id, start_time, end_time,
        ),
    )
