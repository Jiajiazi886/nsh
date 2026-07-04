from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TargetPanelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    defense: float = Field(default=2550, ge=0, description='防御')
    resist: float = Field(default=400, ge=0, description='抵御')
    crit_resist: float = Field(default=0, ge=0, description='会心抵抗')
    resist_pct: float = Field(default=0, ge=0, description='抵御百分比')
    hp: float = Field(default=100000, ge=0, description='血量')
    crit_defense: float = Field(default=0, ge=0, description='会心防御')
    skill_resist: float = Field(default=0, ge=0, description='技能抵御')
    skill_reduction_pct: float = Field(default=0, ge=0, description='技能减免百分比')
    technique_resist: float = Field(default=0, ge=0, description='受击方技巧克制')
    damage_reduction_pct: float = Field(default=0, ge=0, description='减伤百分比（日月区）')


class AttackPanelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    attack: float = Field(default=1750, ge=0, description='攻击')
    break_defense: float = Field(default=1100, ge=0, description='破防')
    restraint_value: float = Field(default=285, ge=0, description='克制数值')
    crit: float = Field(default=1100, ge=0, description='会心')
    crit_dmg: float = Field(default=0.575, ge=0, description='会伤-100%')
    extra_crit_rate: float = Field(default=0.10, ge=0, description='额外会心率')
    restraint_pct: float = Field(default=0, ge=0, description='克制百分比')
    skill_bonus_pct: float = Field(default=0, ge=0, description='技能增强百分比')
    skill_bonus: float = Field(default=0, ge=0, description='技能增强')
    gear_bonus: float = Field(default=0.25, ge=0, description='装备增伤比')
    internal_bonus: float = Field(default=0.15, ge=0, description='内功增伤比')
    element_bonus: float = Field(default=0, ge=0, description='元素增伤百分比')
    technique_restraint: float = Field(default=0, ge=0, description='攻击方技巧克制')


class InternalPowerPanelSettingModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    target_panel: TargetPanelModel = Field(default_factory=TargetPanelModel, description='受击方面板')
    attack_panel: AttackPanelModel = Field(default_factory=AttackPanelModel, description='攻击方无内功基础面板')
    update_time: datetime | None = Field(default=None, description='更新时间')
