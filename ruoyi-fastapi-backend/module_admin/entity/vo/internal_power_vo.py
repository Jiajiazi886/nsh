from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class InternalPowerEntryModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str | None = Field(default=None, description='词条前端ID')
    name: str | None = Field(default='', description='词条名称')
    value: str | None = Field(default='', description='词条值')


class InternalPowerElementsModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    metal: int = Field(default=0, ge=0, description='金')
    wood: int = Field(default=0, ge=0, description='木')
    water: int = Field(default=0, ge=0, description='水')
    fire: int = Field(default=0, ge=0, description='火')
    earth: int = Field(default=0, ge=0, description='土')


class InternalPowerModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str | None = Field(default=None, description='前端兼容ID')
    power_id: int | None = Field(default=None, description='内功ID')
    user_id: int | None = Field(default=None, description='用户ID')
    name: str = Field(description='内功名称')
    category: str | None = Field(default='', description='内功种类')
    category_trait: str | None = Field(default='', description='种类特性')
    bonus_percent: float = Field(default=0, ge=0, le=100, description='基础百分比增伤')
    lingyun_enabled: bool = Field(default=False, description='是否启用灵韵')
    lingyun_bonus_percent: float = Field(default=0, ge=0, le=100, description='灵韵百分比提升')
    entry_attack_power: float = Field(default=0, ge=0, description='词条折算总进攻能力')
    entry_attack_percent: float = Field(default=0, ge=0, description='词条折算总百分比')
    total_bonus_percent: float = Field(default=0, ge=0, description='基础加成与词条加成总百分比')
    entries: list[InternalPowerEntryModel | dict[str, Any]] = Field(default_factory=list, description='词条')
    elements: InternalPowerElementsModel | dict[str, int] = Field(default_factory=InternalPowerElementsModel, description='五行')
    remark: str | None = Field(default='', description='备注')
    updated_at: datetime | str | None = Field(default=None, description='更新时间')

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = (value or '').strip()
        if not value:
            raise ValueError('内功名称不能为空')
        if len(value) > 64:
            raise ValueError('内功名称不能超过64个字符')
        return value


class InternalPowerQuotaModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    count: int = Field(default=0, description='当前数量')
    max_count: int | None = Field(default=20, description='最大数量，null表示不限')
    unlimited: bool = Field(default=False, description='是否不限量')
    is_vip: str = Field(default='0', description='有效VIP标识')
    vip_expire_time: datetime | None = Field(default=None, description='VIP到期时间')


class InternalPowerListModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    powers: list[InternalPowerModel] = Field(default_factory=list, description='内功列表')
    quota: InternalPowerQuotaModel = Field(default_factory=InternalPowerQuotaModel, description='额度信息')


class InternalPowerRecognizeResultModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    result: dict[str, Any] = Field(default_factory=dict, description='AI识图结果占位')
    consumed_count: int = Field(default=0, description='本次消耗次数')
    remaining_ai_image_recognition_count: int = Field(default=0, ge=0, description='剩余AI识图次数')


class InternalPowerImportModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    powers: list[InternalPowerModel] = Field(default_factory=list, description='待导入内功')


class InternalPowerLimitModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    user_id: int | None = Field(default=None, description='用户ID')
    user_ids: list[int] | None = Field(default=None, description='用户ID列表')
    max_internal_power_count: int = Field(default=20, ge=20, description='最大内功数')
