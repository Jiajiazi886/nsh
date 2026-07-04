from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

FORMULA_SCOPE_INTERNAL_POWER_PVP = 'internal_power_pvp_damage'


class DamageFormulaVersionModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    version_id: int | None = Field(default=None, description='公式版本ID')
    version_name: str = Field(description='版本名称')
    formula_scope: str = Field(default=FORMULA_SCOPE_INTERNAL_POWER_PVP, description='公式作用域')
    status: Literal['draft', 'published', 'archived'] = Field(default='draft', description='状态')
    formula_package: dict[str, Any] = Field(default_factory=dict, description='公式包')
    remark: str | None = Field(default='', description='备注')
    publish_time: datetime | None = Field(default=None, description='发布时间')
    create_by: str | None = Field(default='', description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default='', description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')

    @field_validator('version_name')
    @classmethod
    def validate_version_name(cls, value: str) -> str:
        value = (value or '').strip()
        if not value:
            raise ValueError('版本名称不能为空')
        if len(value) > 100:
            raise ValueError('版本名称不能超过100个字符')
        return value

    @field_validator('formula_scope')
    @classmethod
    def validate_formula_scope(cls, value: str) -> str:
        value = (value or '').strip() or FORMULA_SCOPE_INTERNAL_POWER_PVP
        if value != FORMULA_SCOPE_INTERNAL_POWER_PVP:
            raise ValueError('当前仅支持内功PVP伤害公式')
        return value

    def validate_fields(self) -> None:
        self.validate_version_name(self.version_name)
        self.validate_formula_scope(self.formula_scope)
        if not isinstance(self.formula_package, dict):
            raise ValueError('公式包必须是JSON对象')


class DamageFormulaVersionQueryModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    version_name: str | None = Field(default=None, description='版本名称')
    formula_scope: str | None = Field(default=FORMULA_SCOPE_INTERNAL_POWER_PVP, description='公式作用域')
    status: str | None = Field(default=None, description='状态')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
