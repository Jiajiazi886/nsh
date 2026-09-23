from __future__ import annotations

import base64
import binascii
import re
from typing import TYPE_CHECKING, Any, NoReturn

from openai import AsyncOpenAI

from config.env import MimoConfig
from exceptions.exception import ServiceException

if TYPE_CHECKING:
    from module_admin.entity.vo.ai_key_vo import AiTestMessageModel
    from module_admin.service.ai_key_service import ActiveAiConnection


class AiConnectionClientService:
    """受控的 OpenAI 兼容上游客户端，供模型发现和管理页测试使用。"""

    IMAGE_PATTERN = re.compile(
        r'^data:(image/(?:png|jpeg|webp|gif));base64,([A-Za-z0-9+/=\r\n]+)$',
        flags=re.IGNORECASE,
    )
    MAX_IMAGE_BYTES = 5 * 1024 * 1024

    @classmethod
    def make_client(cls, runtime: ActiveAiConnection) -> AsyncOpenAI:
        cls._validate_runtime(runtime, require_model=False)
        return AsyncOpenAI(
            api_key=runtime.api_key,
            base_url=runtime.base_url,
            timeout=MimoConfig.mimo_timeout_seconds,
            max_retries=1,
        )

    @classmethod
    async def list_models(cls, runtime: ActiveAiConnection, client: Any = None) -> list[str]:
        cls._validate_runtime(runtime, require_model=False)
        upstream = client or cls.make_client(runtime)
        try:
            result = await upstream.models.list()
            ids = {str(item.id).strip() for item in (getattr(result, 'data', None) or []) if getattr(item, 'id', None)}
            return sorted(ids, key=str.lower)
        except Exception as exc:
            cls._raise_upstream_error(exc, runtime)

    @classmethod
    async def chat(
        cls,
        runtime: ActiveAiConnection,
        messages: list[AiTestMessageModel],
        client: Any = None,
    ) -> str:
        cls._validate_runtime(runtime, require_model=True)
        has_images = any(message.images for message in messages)
        if has_images and not runtime.support_images:
            raise ServiceException(message='该连接未启用图片能力')
        for message in messages:
            for image in message.images:
                cls._validate_image(image)
        upstream = client or cls.make_client(runtime)
        try:
            if runtime.protocol == 'responses':
                result = await upstream.responses.create(
                    model=runtime.model,
                    input=[cls._responses_message(message) for message in messages],
                    max_output_tokens=runtime.max_tokens,
                    **({'temperature': runtime.temperature} if runtime.temperature is not None else {}),
                )
                text = cls._extract_response_text(result)
            else:
                options = {
                    'model': runtime.model,
                    'messages': [cls._chat_message(message) for message in messages],
                    'max_completion_tokens': runtime.max_tokens,
                }
                if runtime.temperature is not None:
                    options['temperature'] = runtime.temperature
                if runtime.provider.lower() == 'mimo':
                    options['extra_body'] = {'thinking': {'type': 'disabled'}}
                result = await upstream.chat.completions.create(**options)
                text = cls._extract_completion_text(result)
        except ServiceException:
            raise
        except Exception as exc:
            cls._raise_upstream_error(exc, runtime)
        if not text.strip():
            raise ServiceException(message='上游模型未返回文本内容')
        return text

    @staticmethod
    def _chat_message(message: AiTestMessageModel) -> dict:
        if not message.images:
            return {'role': message.role, 'content': message.content}
        content = [
            {'type': 'image_url', 'image_url': {'url': image}}
            for image in message.images
        ]
        if message.content.strip():
            content.append({'type': 'text', 'text': message.content})
        return {'role': message.role, 'content': content}

    @staticmethod
    def _responses_message(message: AiTestMessageModel) -> dict:
        content = [
            {'type': 'input_image', 'image_url': image}
            for image in message.images
        ]
        if message.content.strip():
            content.append({'type': 'input_text', 'text': message.content})
        return {'role': message.role, 'content': content}

    @classmethod
    def _validate_image(cls, value: str) -> None:
        match = cls.IMAGE_PATTERN.fullmatch(value or '')
        if not match:
            raise ServiceException(message='图片必须是 PNG、JPEG、WebP 或 GIF 的 base64 数据 URL')
        try:
            decoded = base64.b64decode(match.group(2), validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ServiceException(message='图片 base64 数据无效') from exc
        if not decoded or len(decoded) > cls.MAX_IMAGE_BYTES:
            raise ServiceException(message='每张图片必须大于 0 且不超过 5 MB')

    @staticmethod
    def _validate_runtime(runtime: ActiveAiConnection, *, require_model: bool) -> None:
        if not runtime.base_url:
            raise ServiceException(message='请先填写 Base URL')
        if not runtime.api_key:
            raise ServiceException(message='请先填写 API Key')
        if require_model and not runtime.model:
            raise ServiceException(message='请先选择或填写模型 ID')

    @staticmethod
    def _extract_completion_text(completion: Any) -> str:
        try:
            content = completion.choices[0].message.content
        except Exception:
            return ''
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return ''.join(
                str(item.get('text') or '') if isinstance(item, dict) else str(getattr(item, 'text', '') or '')
                for item in content
            )
        return str(content or '')

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        output_text = getattr(response, 'output_text', None)
        if isinstance(output_text, str):
            return output_text
        parts = []
        for item in getattr(response, 'output', []) or []:
            for content in getattr(item, 'content', []) or []:
                text = getattr(content, 'text', None)
                if text:
                    parts.append(str(text))
        return ''.join(parts)

    @staticmethod
    def _raise_upstream_error(exc: Exception, runtime: ActiveAiConnection) -> NoReturn:
        safe_message = str(exc).replace(runtime.api_key, '***') if runtime.api_key else str(exc)
        raise ServiceException(message=f'上游 AI 请求失败：{safe_message[:500]}') from exc
