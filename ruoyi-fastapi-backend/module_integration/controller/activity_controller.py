from typing import Annotated, Literal
from fastapi import Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_integration.contract import ApiEnvelope, IntegrationRoute, api_response
from module_integration.activities.service import ActivityService
from module_integration.activities.schema import (
    CreateOrganization,
    GrantMember,
    CreateActivity,
    SaveLineup,
    ChangeActivity,
    SignupSeat,
    LeaveSeat,
    LinkReport,
    ImportActivityReport,
    ActivityLeaveRequest,
)
from module_integration.activities.enabled import require_activities_enabled

activity_controller = APIRouterPro(
    prefix='/api/v1',
    order_num=91,
    tags=['约战信息'],
    route_class=IntegrationRoute,
    dependencies=[Depends(require_activities_enabled)],
    responses={c: {'model': ApiEnvelope} for c in (401, 403, 404, 409, 422, 500, 503)},
)
CurrentUser = Annotated[CurrentUserModel, CurrentUserDependency()]
Database = Annotated[AsyncSession, DBSessionDependency()]
Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


@activity_controller.get('/organizations', response_model=ApiEnvelope, operation_id='v1Organizations')
async def organizations(request: Request, current_user: CurrentUser, db: Database):
    return api_response(request, await ActivityService.organizations(db, current_user))


@activity_controller.post('/organizations', response_model=ApiEnvelope, operation_id='v1CreateOrganization')
async def create_organization(request: Request, data: CreateOrganization, current_user: CurrentUser, db: Database):
    return api_response(request, await ActivityService.create_organization(db, current_user, data.org_type, data.name))


@activity_controller.post(
    '/organizations/{org_id}/members', response_model=ApiEnvelope, operation_id='v1GrantOrganizationMember'
)
async def grant_member(request: Request, org_id: str, data: GrantMember, current_user: CurrentUser, db: Database):
    return api_response(
        request, await ActivityService.grant_member(db, current_user, org_id, data.member_id, data.role)
    )


@activity_controller.get('/activity-profiles', response_model=ApiEnvelope, operation_id='v1ActivityProfiles')
async def profiles(
    request: Request,
    current_user: CurrentUser,
    db: Database,
    org_id: Annotated[str | None, Query(alias='orgId')] = None,
    activity_id: Annotated[str | None, Query(alias='activityId')] = None,
):
    return api_response(request, await ActivityService.profiles(db, current_user, org_id, activity_id))


@activity_controller.get('/activity-leave/{code}', response_model=ApiEnvelope, operation_id='v1ActivityLeaveInfo')
async def leave_link_info(request: Request, code: str, db: Database):
    return api_response(request, await ActivityService.leave_link_info(db, code))


@activity_controller.get(
    '/activity-leave/{code}/members', response_model=ApiEnvelope, operation_id='v1ActivityLeaveMembers'
)
async def leave_link_members(request: Request, code: str, db: Database, keyword: str = ''):
    return api_response(request, await ActivityService.leave_members_by_code(db, code, keyword))


@activity_controller.post('/activity-leave/{code}', response_model=ApiEnvelope, operation_id='v1ActivityLeave')
async def leave_by_link(request: Request, code: str, data: ActivityLeaveRequest, db: Database):
    return api_response(
        request,
        await ActivityService.leave_by_code(db, code, data.member_id, data.remark),
    )


@activity_controller.get('/activity-professions', response_model=ApiEnvelope, operation_id='v1ActivityProfessions')
async def professions(request: Request, current_user: CurrentUser, db: Database):
    from sqlalchemy import select
    from module_guild.entity.do.profession_do import GuildProfession

    return api_response(
        request,
        list(
            (
                await db.execute(
                    select(GuildProfession.profession_name)
                    .where(GuildProfession.status == '0')
                    .order_by(GuildProfession.order_num, GuildProfession.profession_id)
                )
            )
            .scalars()
            .all()
        ),
    )


@activity_controller.get(
    '/activity-lineup-templates', response_model=ApiEnvelope, operation_id='v1ActivityLineupTemplates'
)
async def lineup_templates(
    request: Request,
    current_user: CurrentUser,
    db: Database,
    org_id: Annotated[str, Query(alias='orgId')],
):
    return api_response(request, await ActivityService.lineup_templates(db, current_user, org_id))


@activity_controller.get('/activities', response_model=ApiEnvelope, operation_id='v1Activities')
async def activities(
    request: Request,
    current_user: CurrentUser,
    db: Database,
    kind: Literal['mine', 'public', 'history'] = 'mine',
    page: Page = 1,
    page_size: Annotated[int, Query(alias='pageSize', ge=1, le=100)] = 20,
    profession: str = '',
    vacant_only: Annotated[bool, Query(alias='vacantOnly')] = False,
    org_type: Annotated[Literal['guild', 'club'] | None, Query(alias='orgType')] = None,
    participating_only: Annotated[bool, Query(alias='participatingOnly')] = False,
):
    return api_response(
        request,
        await ActivityService.list(
            db,
            current_user,
            kind,
            page,
            page_size,
            profession,
            vacant_only,
            org_type,
            participating_only,
        ),
    )


@activity_controller.post('/activities', response_model=ApiEnvelope, operation_id='v1CreateActivity')
async def create_activity(request: Request, data: CreateActivity, current_user: CurrentUser, db: Database):
    return api_response(request, await ActivityService.create(db, current_user, data))


@activity_controller.get('/activities/{activity_id}', response_model=ApiEnvelope, operation_id='v1ActivityDetail')
async def detail(request: Request, activity_id: str, current_user: CurrentUser, db: Database):
    return api_response(request, await ActivityService.detail(db, current_user, activity_id))


@activity_controller.get(
    '/activities/{activity_id}/snapshots', response_model=ApiEnvelope, operation_id='v1ActivitySnapshots'
)
async def snapshots(request: Request, activity_id: str, current_user: CurrentUser, db: Database):
    return api_response(request, await ActivityService.snapshots(db, current_user, activity_id))


@activity_controller.get(
    '/activities/{activity_id}/leaves', response_model=ApiEnvelope, operation_id='v1ActivityLeaves'
)
async def activity_leaves(request: Request, activity_id: str, current_user: CurrentUser, db: Database):
    return api_response(request, await ActivityService.activity_leaves(db, current_user, activity_id))


@activity_controller.put(
    '/activities/{activity_id}/lineup', response_model=ApiEnvelope, operation_id='v1SaveActivityLineup'
)
async def save_lineup(request: Request, activity_id: str, data: SaveLineup, current_user: CurrentUser, db: Database):
    return api_response(request, await ActivityService.save(db, current_user, activity_id, data))


@activity_controller.post(
    '/activities/{activity_id}/publish', response_model=ApiEnvelope, operation_id='v1PublishActivity'
)
async def publish(request: Request, activity_id: str, data: ChangeActivity, current_user: CurrentUser, db: Database):
    return api_response(request, await ActivityService.change(db, current_user, activity_id, 'publish', data))


@activity_controller.post('/activities/{activity_id}/end', response_model=ApiEnvelope, operation_id='v1EndActivity')
async def end(request: Request, activity_id: str, data: ChangeActivity, current_user: CurrentUser, db: Database):
    return api_response(request, await ActivityService.change(db, current_user, activity_id, 'end', data))


@activity_controller.post(
    '/activities/{activity_id}/signup', response_model=ApiEnvelope, operation_id='v1SignupActivitySeat'
)
async def signup(request: Request, activity_id: str, data: SignupSeat, current_user: CurrentUser, db: Database):
    return api_response(request, await ActivityService.signup(db, current_user, activity_id, data))


@activity_controller.post(
    '/activities/{activity_id}/leave', response_model=ApiEnvelope, operation_id='v1LeaveActivitySeat'
)
async def leave(request: Request, activity_id: str, data: LeaveSeat, current_user: CurrentUser, db: Database):
    return api_response(request, await ActivityService.leave(db, current_user, activity_id, data))


@activity_controller.post(
    '/activities/{activity_id}/reports', response_model=ApiEnvelope, operation_id='v1LinkActivityReport'
)
async def link_report(request: Request, activity_id: str, data: LinkReport, current_user: CurrentUser, db: Database):
    return api_response(request, await ActivityService.link_report(db, current_user, activity_id, data))


@activity_controller.post(
    '/activities/{activity_id}/reports/import',
    response_model=ApiEnvelope,
    operation_id='v1ImportActivityReport',
)
async def import_report(
    request: Request,
    activity_id: str,
    data: ImportActivityReport,
    current_user: CurrentUser,
    db: Database,
):
    return api_response(request, await ActivityService.import_report(db, current_user, activity_id, data))


@activity_controller.get('/activity-reports', response_model=ApiEnvelope, operation_id='v1ActivityReports')
async def reports(
    request: Request,
    current_user: CurrentUser,
    db: Database,
    page: Page = 1,
    page_size: Annotated[int, Query(alias='pageSize', ge=1, le=100)] = 20,
):
    return api_response(request, await ActivityService.reports(db, current_user, page, page_size))


@activity_controller.get(
    '/activity-reports/{report_id}', response_model=ApiEnvelope, operation_id='v1ActivityReportDetail'
)
async def report(request: Request, report_id: str, current_user: CurrentUser, db: Database):
    from module_integration.contract import ApiProblem

    if not report_id.isdecimal() or len(report_id) > 19 or int(report_id) > 2**63 - 1:
        raise ApiProblem(422, 'VALIDATION_FAILED', '战报 ID 不正确')
    return api_response(request, await ActivityService.report(db, current_user, report_id))
