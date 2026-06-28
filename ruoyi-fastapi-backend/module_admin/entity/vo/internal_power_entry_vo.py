from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class InternalPowerEntryConfigModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    entry_id: int | None = Field(default=None, description='词条ID')
    entry_name: str = Field(description='词条名称')
    conversion_percent: float | None = Field(default=None, ge=0, le=100, description='数值转换百分比')
    conversion_desc: str | None = Field(default='', description='转换说明')
    status: Literal['0', '1'] = Field(default='0', description='状态')
    remark: str | None = Field(default='', description='备注')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_time: datetime | None = Field(default=None, description='更新时间')

    @field_validator('entry_name')
    @classmethod
    def validate_entry_name(cls, value: str) -> str:
        value = (value or '').strip()
        if not value:
            raise ValueError('词条名称不能为空')
        if len(value) > 64:
            raise ValueError('词条名称不能超过64个字符')
        return value

    def validate_fields(self) -> None:
        self.validate_entry_name(self.entry_name)


class InternalPowerEntryQueryModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    entry_name: str | None = Field(default=None, description='词条名称')
    status: str | None = Field(default=None, description='状态')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class InternalPowerEntryListModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    entries: list[InternalPowerEntryConfigModel] = Field(default_factory=list, description='启用内功词条列表')


class DeleteInternalPowerEntryModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    entry_ids: str = Field(description='需要删除的词条ID')
