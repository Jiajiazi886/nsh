from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class InternalPowerAiKeyModel(BaseModel):
    """项目AI图片识别 API Key 的公开状态，不包含密钥明文。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    api_key_configured: bool = Field(default=False, description='是否已配置 API Key')
    update_by: str | None = Field(default='', description='最后修改人')
    update_time: datetime | None = Field(default=None, description='最后修改时间')


class InternalPowerAiKeyUpdateModel(BaseModel):
    """用于更新项目所有AI图片识别功能共用的 API Key。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    api_key: str | None = Field(default=None, max_length=128, description='新的 API Key')
    clear_api_key: bool = Field(default=False, description='是否清除当前 API Key')

    @model_validator(mode='after')
    def validate_update(self) -> 'InternalPowerAiKeyUpdateModel':
        has_api_key = bool((self.api_key or '').strip())
        if self.clear_api_key and has_api_key:
            raise ValueError('不能同时设置新的 API Key 和清除当前 API Key')
        if not self.clear_api_key and not has_api_key:
            raise ValueError('请输入 API Key，或选择清除当前 API Key')
        return self
