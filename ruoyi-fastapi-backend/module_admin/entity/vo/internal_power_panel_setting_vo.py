from datetime import datetime

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
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
    extra_crit_rate: float = Field(default=0, ge=0, description='额外会心率')
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


class PanelRecognitionHistoryModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    record_id: int | None = Field(default=None, description='记录ID')
    file_name: str = Field(default='', description='图片文件名')
    image_base64: str = Field(default='', description='图片Base64')
    mime_type: str = Field(default='image/png', description='图片MIME类型')
    status: str = Field(default='recognizing', description='识别状态')
    parsed: dict[str, Any] | None = Field(default=None, description='识别JSON')
    raw_text: str = Field(default='', description='模型原始文本')
    error: str = Field(default='', description='错误信息')
    create_time: datetime | None = Field(default=None, description='创建时间')


class PanelRecognitionResultModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    success: bool = Field(default=False, description='是否识别成功')
    record_id: int | None = Field(default=None, description='识别历史ID')
    parsed: dict[str, Any] | None = Field(default=None, description='识别JSON')
    raw_text: str = Field(default='', description='模型原始文本')
    error: str = Field(default='', description='错误信息')
    consumed_count: int = Field(default=0, description='本次消耗总次数')
    consumed_vip_count: int = Field(default=0, description='本次消耗VIP次数')
    consumed_normal_count: int = Field(default=0, description='本次消耗普通次数')
    remaining_vip_ai_image_recognition_count: int = Field(default=0, description='剩余VIP AI识图次数')
    remaining_ai_image_recognition_count: int = Field(default=0, description='剩余普通AI识图次数')


class PanelRecognitionHistoryListModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    rows: list[PanelRecognitionHistoryModel] = Field(default_factory=list, description='识别历史')
    visible_limit: int = Field(default=5, description='当前用户可查看条数')
    max_history_count: int = Field(default=10, description='系统最多保留条数')


class InternalPowerPanelTemplateModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    template_id: int | None = Field(default=None, description='模板ID')
    template_name: str = Field(default='', min_length=1, max_length=100, description='模板名称')
    status: str = Field(default='0', description='状态（0启用 1停用）')
    target_panel: TargetPanelModel = Field(default_factory=TargetPanelModel, description='受击方面板')
    attack_panel: AttackPanelModel = Field(default_factory=AttackPanelModel, description='攻击方面板')
    remark: str | None = Field(default='', max_length=500, description='备注')
    create_by: str | None = Field(default='', description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default='', description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')

    @field_validator('status')
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in {'0', '1'}:
            raise ValueError('状态只能为0或1')
        return value

    @model_validator(mode='after')
    def validate_template_id_for_edit(self):
        return self


class InternalPowerPanelTemplateQueryModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    template_name: str | None = Field(default=None, description='模板名称')
    status: str | None = Field(default=None, description='状态')
    page_num: int = Field(default=1, ge=1, description='当前页码')
    page_size: int = Field(default=10, ge=1, le=100, description='每页条数')


class InternalPowerPanelTemplateStatusModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    template_id: int = Field(description='模板ID')
    status: str = Field(description='状态（0启用 1停用）')

    @field_validator('status')
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in {'0', '1'}:
            raise ValueError('状态只能为0或1')
        return value
