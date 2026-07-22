from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class PvpAttackPanelFields(BaseModel):
    """来自 PVP 计算器的进攻方核心面板。百分比字段使用小数，例如 0.15 表示 15%。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    attack: float = Field(default=1750, ge=0, description='攻击')
    break_defense: float = Field(default=1100, ge=0, description='破防')
    restraint_value: float = Field(default=285, ge=0, description='克制数值')
    crit: float = Field(default=1100, ge=0, description='会心')
    crit_dmg: float = Field(default=0.575, ge=0, description='会伤增幅')
    extra_crit_rate: float = Field(default=0, ge=0, description='额外会心率')
    restraint_pct: float = Field(default=0, ge=0, description='流派克制百分比')
    skill_bonus: float = Field(default=0, ge=0, description='技能增强')
    skill_bonus_pct: float = Field(default=0, ge=0, description='技能增强百分比')
    internal_bonus: float = Field(default=0, ge=0, description='内功增伤比')
    gear_bonus: float = Field(default=0, ge=0, description='装备增伤比')
    martial_bonus: float = Field(default=0, ge=0, description='武蕴增伤比')
    other_bonus: float = Field(default=0, ge=0, description='其他增伤比')
    technique_restraint: float = Field(default=0, ge=0, description='攻击方技巧克制')


class PvpAttackPanelModel(PvpAttackPanelFields):
    panel_id: int | None = Field(default=None, description='面板主键')
    panel_name: str = Field(min_length=1, max_length=100, description='面板名称')
    status: Literal['0', '1'] = Field(default='0', description='状态')
    remark: str | None = Field(default='', max_length=500, description='备注')
    create_by: str | None = Field(default='', description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default='', description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')

    @field_validator('panel_name')
    @classmethod
    def strip_panel_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError('面板名称不能为空')
        return value


class PvpAttackPanelQueryModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    panel_name: str | None = Field(default=None, max_length=100, description='面板名称')
    status: Literal['0', '1'] | None = Field(default=None, description='状态')
    page_num: int = Field(default=1, ge=1, description='当前页码')
    page_size: int = Field(default=10, ge=1, le=100, description='每页条数')


class PvpAttackPanelStatusModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: Literal['0', '1'] = Field(description='状态')
