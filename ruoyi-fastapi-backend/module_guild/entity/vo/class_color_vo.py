from typing import Optional
from pydantic import BaseModel, Field

class ClassColorItem(BaseModel):
    class_name: str = Field(description='职业名称')
    bg_color: str = Field(description='背景颜色')
    text_color: str = Field(description='文字颜色')

class ClassColorSaveModel(BaseModel):
    colors: list[ClassColorItem] = Field(description='职业颜色配置列表')