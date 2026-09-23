from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import and_, case, func, or_, select, update

from common.vo import PageModel
from config.database import AsyncSessionLocal
from exceptions.exception import ServiceException
from module_admin.entity.do.ai_usage_do import AiRequestUsageLog
from module_admin.entity.vo.ai_usage_vo import (
    AiUsagePageQueryModel,
    AiUsageRecordModel,
    AiUsageSummaryModel,
    AiUsageUserModel,
)
from utils.page_util import PageUtil

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from module_admin.entity.vo.user_vo import CurrentUserModel
    from module_admin.service.ai_key_service import ActiveAiConnection


@dataclass(frozen=True)
class AiUsageSnapshot:
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    reported: bool


@dataclass(frozen=True)
class AiUsageContext:
    request_id: str
    started_at: datetime
    started_counter: float
    api_key: str


class AiUsageService:
    """大模型 Token 记录服务。写入使用独立会话，避免业务事务回滚后丢失。"""

    @staticmethod
    def extract_usage(protocol: str, response: Any) -> AiUsageSnapshot:
        usage = getattr(response, 'usage', None)
        if usage is None:
            return AiUsageSnapshot(None, None, None, False)
        if protocol == 'responses':
            input_tokens = getattr(usage, 'input_tokens', None)
            output_tokens = getattr(usage, 'output_tokens', None)
        else:
            input_tokens = getattr(usage, 'prompt_tokens', None)
            output_tokens = getattr(usage, 'completion_tokens', None)
        total_tokens = getattr(usage, 'total_tokens', None)
        values = (input_tokens, output_tokens, total_tokens)
        if all(value is None for value in values):
            return AiUsageSnapshot(None, None, None, False)
        return AiUsageSnapshot(
            int(input_tokens) if input_tokens is not None else None,
            int(output_tokens) if output_tokens is not None else None,
            int(total_tokens) if total_tokens is not None else None,
            True,
        )

    @staticmethod
    def sanitize_error(error: object, secrets: tuple[str, ...] = ()) -> str:
        value = re.sub(r'[\r\n\t]+', ' ', str(error or '')).strip()
        value = re.sub(r'(?i)(authorization\s*:\s*bearer\s+)[^\s,;]+', r'\1***', value)
        value = re.sub(r'(?i)(api[_-]?key\s*[=:]\s*)[^\s,;]+', r'\1***', value)
        for secret in secrets:
            if secret:
                value = value.replace(secret, '***')
        return value[:500]

    @classmethod
    async def start_request(
        cls,
        current_user: CurrentUserModel,
        runtime: ActiveAiConnection,
        scene: str,
    ) -> AiUsageContext:
        request_id = str(uuid4())
        now = datetime.now()
        user = current_user.user
        record = AiRequestUsageLog(
            request_id=request_id,
            user_id=int(user.user_id),
            user_name=user.user_name or '',
            nick_name=user.nick_name or '',
            connection_id=runtime.id,
            connection_name=runtime.name,
            provider=runtime.provider,
            protocol=runtime.protocol,
            model=runtime.model,
            scene=scene,
            status='pending',
            usage_reported='0',
            request_time=now,
        )
        try:
            async with AsyncSessionLocal() as session:
                session.add(record)
                await session.commit()
        except Exception as exc:
            raise ServiceException(message='Token请求记录创建失败，本次未调用大模型') from exc
        return AiUsageContext(request_id, now, perf_counter(), runtime.api_key)

    @classmethod
    async def finish_success(cls, context: AiUsageContext, protocol: str, response: Any) -> None:
        usage = cls.extract_usage(protocol, response)
        await cls._finish(
            context,
            status='success',
            usage=usage,
            error_message='',
        )

    @classmethod
    async def finish_failure(cls, context: AiUsageContext, error: object) -> None:
        await cls._finish(
            context,
            status='failed',
            usage=AiUsageSnapshot(None, None, None, False),
            error_message=cls.sanitize_error(error, (context.api_key,)),
        )

    @classmethod
    async def _finish(
        cls,
        context: AiUsageContext,
        *,
        status: str,
        usage: AiUsageSnapshot,
        error_message: str,
    ) -> None:
        complete_time = datetime.now()
        duration_ms = max(0, round((perf_counter() - context.started_counter) * 1000))
        values = {
            'status': status,
            'input_tokens': usage.input_tokens,
            'output_tokens': usage.output_tokens,
            'total_tokens': usage.total_tokens,
            'usage_reported': '1' if usage.reported else '0',
            'complete_time': complete_time,
            'duration_ms': duration_ms,
            'error_message': error_message,
        }
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(AiRequestUsageLog)
                    .where(AiRequestUsageLog.request_id == context.request_id)
                    .values(**values)
                )
                await session.commit()
        except Exception as exc:
            raise ServiceException(message='Token请求记录更新失败') from exc

    @staticmethod
    def _filters(query: AiUsagePageQueryModel) -> list[Any]:
        filters: list[Any] = []
        keyword = (query.user_keyword or '').strip()
        if keyword:
            keyword_filter = or_(
                AiRequestUsageLog.user_name.like(f'%{keyword}%'),
                AiRequestUsageLog.nick_name.like(f'%{keyword}%'),
            )
            if keyword.isdigit():
                keyword_filter = or_(keyword_filter, AiRequestUsageLog.user_id == int(keyword))
            filters.append(keyword_filter)
        if query.connection_id is not None:
            filters.append(AiRequestUsageLog.connection_id == query.connection_id)
        if query.model:
            filters.append(AiRequestUsageLog.model.like(f'%{query.model.strip()}%'))
        if query.scene:
            filters.append(AiRequestUsageLog.scene == query.scene)
        if query.status:
            filters.append(AiRequestUsageLog.status == query.status)
        if query.begin_time:
            filters.append(AiRequestUsageLog.request_time >= query.begin_time)
        if query.end_time:
            filters.append(AiRequestUsageLog.request_time <= query.end_time)
        return filters

    @classmethod
    async def list_records(
        cls, db: AsyncSession, query: AiUsagePageQueryModel
    ) -> PageModel[AiUsageRecordModel]:
        statement = select(AiRequestUsageLog).where(and_(*cls._filters(query))).order_by(
            AiRequestUsageLog.request_time.desc(), AiRequestUsageLog.record_id.desc()
        )
        page = await PageUtil.paginate(db, statement, query.page_num, query.page_size, True)
        rows = [cls._to_record_model(item) for item in page.rows]
        return PageModel(
            rows=rows,
            page_num=page.page_num,
            page_size=page.page_size,
            total=page.total,
            has_next=page.has_next,
        )

    @classmethod
    async def summary(cls, db: AsyncSession, query: AiUsagePageQueryModel) -> AiUsageSummaryModel:
        row = (
            await db.execute(
                select(
                    func.count(AiRequestUsageLog.record_id),
                    func.sum(case((AiRequestUsageLog.usage_reported == '1', 1), else_=0)),
                    func.sum(case((AiRequestUsageLog.usage_reported == '0', 1), else_=0)),
                    func.coalesce(func.sum(AiRequestUsageLog.total_tokens), 0),
                ).where(and_(*cls._filters(query)))
            )
        ).one()
        return AiUsageSummaryModel(
            request_count=int(row[0] or 0),
            reported_count=int(row[1] or 0),
            unreported_count=int(row[2] or 0),
            total_tokens=int(row[3] or 0),
        )

    @classmethod
    async def search_users(cls, db: AsyncSession, keyword: str = '') -> list[AiUsageUserModel]:
        filters = []
        value = keyword.strip()
        if value:
            condition = or_(
                AiRequestUsageLog.user_name.like(f'%{value}%'),
                AiRequestUsageLog.nick_name.like(f'%{value}%'),
            )
            if value.isdigit():
                condition = or_(condition, AiRequestUsageLog.user_id == int(value))
            filters.append(condition)
        statement = (
            select(
                AiRequestUsageLog.user_id,
                AiRequestUsageLog.user_name,
                AiRequestUsageLog.nick_name,
            )
            .where(and_(*filters))
            .distinct()
            .order_by(AiRequestUsageLog.user_id.asc())
            .limit(50)
        )
        return [AiUsageUserModel(user_id=row[0], user_name=row[1], nick_name=row[2]) for row in (await db.execute(statement)).all()]

    @staticmethod
    def _to_record_model(record: AiRequestUsageLog) -> AiUsageRecordModel:
        return AiUsageRecordModel(
            record_id=int(record.record_id),
            request_id=record.request_id,
            user_id=int(record.user_id),
            user_name=record.user_name,
            nick_name=record.nick_name,
            connection_id=int(record.connection_id) if record.connection_id is not None else None,
            connection_name=record.connection_name,
            provider=record.provider,
            protocol=record.protocol,
            model=record.model,
            scene=record.scene,
            status=record.status,
            input_tokens=record.input_tokens,
            output_tokens=record.output_tokens,
            total_tokens=record.total_tokens,
            usage_reported=record.usage_reported == '1',
            request_time=record.request_time,
            complete_time=record.complete_time,
            duration_ms=record.duration_ms,
            error_message=record.error_message or '',
        )
