from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class InternalPowerEntryConversionRowModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    entry_name: str = Field(description='词条名称')
    limit_text: str = Field(default='', description='固定上限展示值')
    limit_value: float = Field(default=0, ge=0, description='固定上限数值')
    value_type: Literal['number', 'percent'] = Field(default='number', description='数值类型')
    entry_value: float = Field(default=0, ge=0, description='用户内功数值')
    attack_power: float = Field(default=0, ge=0, description='进攻能力')
    attack_percent: float = Field(default=0, ge=0, description='进攻能力百分比')

    @field_validator('entry_name')
    @classmethod
    def validate_entry_name(cls, value: str) -> str:
        value = (value or '').strip()
        if not value:
            raise ValueError('词条名称不能为空')
        return value


class InternalPowerEntryConversionModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    base_attack_power: float = Field(default=0, ge=0, description='基准进攻能力')
    base_percent: float = Field(default=0, ge=0, description='基准百分比')
    unit_percent: float = Field(default=0, ge=0, description='1点进攻能力对应百分比')
    entries: list[InternalPowerEntryConversionRowModel] = Field(default_factory=list, description='词条换算行')
    update_time: datetime | None = Field(default=None, description='更新时间')


class InternalPowerEntryConversionSaveModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    base_attack_power: float = Field(default=0, ge=0, description='基准进攻能力')
    base_percent: float = Field(default=0, ge=0, description='基准百分比')
    entries: list[InternalPowerEntryConversionRowModel] = Field(default_factory=list, description='词条换算行')
