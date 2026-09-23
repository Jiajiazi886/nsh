from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class AiUsageRecordModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    record_id: int
    request_id: str
    user_id: int
    user_name: str
    nick_name: str
    connection_id: int | None = None
    connection_name: str
    provider: str
    protocol: str
    model: str
    scene: str
    status: Literal['pending', 'success', 'failed']
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    usage_reported: bool
    request_time: datetime
    complete_time: datetime | None = None
    duration_ms: int | None = None
    error_message: str = ''


class AiUsagePageQueryModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    user_keyword: str | None = None
    connection_id: int | None = None
    model: str | None = None
    scene: str | None = None
    status: Literal['pending', 'success', 'failed'] | None = None
    begin_time: datetime | None = None
    end_time: datetime | None = None
    page_num: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)


class AiUsageSummaryModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    request_count: int = 0
    reported_count: int = 0
    unreported_count: int = 0
    total_tokens: int = 0


class AiUsageUserModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    user_id: int
    user_name: str
    nick_name: str
