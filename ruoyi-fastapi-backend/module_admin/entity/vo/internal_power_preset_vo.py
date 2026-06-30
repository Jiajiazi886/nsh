from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from module_admin.entity.vo.internal_power_vo import InternalPowerElementsModel, InternalPowerEntryModel


class InternalPowerPresetModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    preset_id: int | None = Field(default=None, description='预设ID')
    name: str = Field(description='内功名称')
    element_key: Literal['metal', 'wood', 'water', 'fire', 'earth', 'mixed'] = Field(description='元素标识')
    elements: InternalPowerElementsModel | dict[str, int] = Field(description='五行')
    bonus_percent: float = Field(default=0, ge=0, le=100, description='基础百分比增益')
    lingyun_bonus_percent: float = Field(default=0, ge=0, le=100, description='灵韵百分比提升')
    bonus_type: str | None = Field(default='', description='增益类型')
    bonus_desc: str | None = Field(default='', description='增益描述')
    image_url: str | None = Field(default='', description='内功图片地址')
    entries: list[InternalPowerEntryModel | dict[str, Any]] = Field(default_factory=list, description='词条')
    status: Literal['0', '1'] = Field(default='0', description='状态')
    remark: str | None = Field(default='', description='备注')
    display_name: str | None = Field(default=None, description='展示名称')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_time: datetime | None = Field(default=None, description='更新时间')

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = (value or '').strip()
        if not value:
            raise ValueError('内功名称不能为空')
        if len(value) > 64:
            raise ValueError('内功名称不能超过64个字符')
        return value

    def validate_fields(self) -> None:
        self.validate_name(self.name)


class InternalPowerPresetQueryModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str | None = Field(default=None, description='内功名称')
    element_key: str | None = Field(default=None, description='元素标识')
    status: str | None = Field(default=None, description='状态')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class InternalPowerPresetListModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    presets: list[InternalPowerPresetModel] = Field(default_factory=list, description='启用内功预设列表')


class DeleteInternalPowerPresetModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    preset_ids: str = Field(description='需要删除的预设ID')
