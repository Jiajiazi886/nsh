from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size


class ProfessionModel(BaseModel):
    """职业信息模型"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    profession_id: int | None = Field(default=None, description='职业ID')
    profession_name: str | None = Field(default=None, description='职业名称')
    order_num: int | None = Field(default=0, description='显示顺序')
    status: Literal['0', '1'] | None = Field(default='0', description='状态（0正常 1停用）')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default=None, description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')
    remark: str | None = Field(default=None, description='备注')

    @NotBlank(field_name='profession_name', message='职业名称不能为空')
    @Size(field_name='profession_name', min_length=0, max_length=30, message='职业名称长度不能超过30个字符')
    def get_profession_name(self) -> str | None:
        return self.profession_name

    @NotBlank(field_name='order_num', message='显示顺序不能为空')
    def get_order_num(self) -> int | None:
        return self.order_num

    def validate_fields(self) -> None:
        self.get_profession_name()
        self.get_order_num()


class ProfessionQueryModel(ProfessionModel):
    """职业信息查询模型"""

    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')


class ProfessionPageQueryModel(ProfessionQueryModel):
    """职业信息分页查询模型"""

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteProfessionModel(BaseModel):
    """删除职业模型"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    profession_ids: str = Field(description='需要删除的职业ID')
