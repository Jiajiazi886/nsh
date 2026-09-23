from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
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


AiProtocol = Literal['chat_completions', 'responses']


class AiConnectionModel(BaseModel):
    """可以返回给管理页面的 AI 连接信息，永不包含密钥明文。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    name: str
    provider: str
    base_url: str
    protocol: AiProtocol
    model: str
    api_key_configured: bool = False
    max_tokens: int = 2048
    temperature: float | None = None
    support_images: bool = True
    active: bool = False
    remark: str = ''
    update_by: str = ''
    update_time: datetime | None = None


class AiConnectionSaveModel(BaseModel):
    """AI 连接新增与编辑公用输入。编辑时 API Key 留空表示保留原值。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str = Field(min_length=1, max_length=100)
    provider: str = Field(min_length=1, max_length=50)
    base_url: str = Field(min_length=1, max_length=255)
    protocol: AiProtocol = 'chat_completions'
    model: str = Field(min_length=1, max_length=100)
    api_key: str | None = Field(default=None, max_length=512)
    max_tokens: int = Field(default=2048, ge=1, le=128000)
    temperature: float | None = Field(default=None, ge=0, le=2)
    support_images: bool = True
    remark: str = Field(default='', max_length=500)

    @field_validator('name', 'provider', 'model', 'api_key', 'remark', mode='before')
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator('base_url', mode='before')
    @classmethod
    def normalize_base_url(cls, value: object) -> object:
        normalized = value.strip().rstrip('/') if isinstance(value, str) else value
        parsed = urlparse(normalized or '')
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
            raise ValueError('Base URL 必须是完整的 http/https 地址')
        return normalized


class AiConnectionProbeModel(BaseModel):
    """上游探测输入；可基于已保存连接并覆盖部分字段。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    connection_id: int | None = None
    base_url: str | None = Field(default=None, max_length=255)
    api_key: str | None = Field(default=None, max_length=512)

    @field_validator('base_url', mode='before')
    @classmethod
    def normalize_optional_base_url(cls, value: object) -> str | None:
        if value is None or not str(value).strip():
            return None
        normalized = str(value).strip().rstrip('/')
        parsed = urlparse(normalized)
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
            raise ValueError('Base URL 必须是完整的 http/https 地址')
        return normalized

    @field_validator('api_key', mode='before')
    @classmethod
    def normalize_optional_key(cls, value: object) -> str | None:
        return (str(value).strip() or None) if value is not None else None

    @model_validator(mode='after')
    def validate_source(self) -> 'AiConnectionProbeModel':
        if self.connection_id is None and (not self.base_url or not self.api_key):
            raise ValueError('未使用已保存连接时，Base URL 和 API Key 必须同时填写')
        return self


class AiTestMessageModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    role: Literal['user', 'assistant']
    content: str = Field(default='', max_length=20000)
    images: list[str] = Field(default_factory=list, max_length=4)

    @model_validator(mode='after')
    def validate_content(self) -> 'AiTestMessageModel':
        if self.role == 'assistant' and self.images:
            raise ValueError('助手消息不能包含图片')
        if not self.content.strip() and not self.images:
            raise ValueError('消息文字和图片不能同时为空')
        return self


class AiConnectionTestModel(AiConnectionProbeModel):
    protocol: AiProtocol | None = None
    model: str | None = Field(default=None, max_length=100)
    max_tokens: int | None = Field(default=None, ge=1, le=128000)
    temperature: float | None = Field(default=None, ge=0, le=2)
    messages: list[AiTestMessageModel] = Field(min_length=1, max_length=30)


class AiModelsResultModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    models: list[str]


class AiTestResultModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    text: str
