import base64
import json
import re
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI

from config.env import MimoConfig
from exceptions.exception import ServiceException


@dataclass
class InternalPowerMimoResult:
    parsed: dict[str, Any] | None
    raw_text: str
    error: str = ''


class InternalPowerMimoService:
    """
    Mimo多模态内功图片识别服务。
    """

    SYSTEM_PROMPT = (
        '你是一个严格的图片信息抽取助手。请只根据用户提供的当前图片和提示词输出结果，'
        '不要引用历史上下文，不要解释，不要输出JSON之外的文本。'
    )

    @classmethod
    def build_data_url(cls, image_bytes: bytes, mime_type: str) -> str:
        safe_mime_type = mime_type or 'image/png'
        encoded = base64.b64encode(image_bytes).decode('ascii')
        return f'data:{safe_mime_type};base64,{encoded}'

    @classmethod
    async def recognize_image(
        cls,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        client: AsyncOpenAI | None = None,
    ) -> InternalPowerMimoResult:
        result = await cls.recognize_image_json(image_bytes, mime_type, prompt, client)
        if result.parsed is None:
            return result
        validation_error = cls.validate_parsed_result(result.parsed)
        if validation_error:
            return InternalPowerMimoResult(parsed=None, raw_text=result.raw_text, error=validation_error)
        return result

    @classmethod
    async def recognize_image_json(
        cls,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        client: AsyncOpenAI | None = None,
    ) -> InternalPowerMimoResult:
        """
        调用Mimo并只要求返回可解析JSON，具体业务校验由调用方完成。
        """
        if not MimoConfig.mimo_api_key:
            raise ServiceException(message='Mimo API Key 未配置，请在后端环境变量 MIMO_API_KEY 中配置')
        if not prompt or not prompt.strip():
            raise ServiceException(message='识别提示词不能为空')

        mimo_client = client or AsyncOpenAI(
            api_key=MimoConfig.mimo_api_key,
            base_url=MimoConfig.mimo_base_url,
            timeout=MimoConfig.mimo_timeout_seconds,
        )
        data_url = cls.build_data_url(image_bytes, mime_type)
        try:
            completion = await mimo_client.chat.completions.create(
                model=MimoConfig.mimo_model,
                messages=[
                    {'role': 'system', 'content': cls.SYSTEM_PROMPT},
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'image_url', 'image_url': {'url': data_url}},
                            {'type': 'text', 'text': prompt},
                        ],
                    },
                ],
                max_completion_tokens=MimoConfig.mimo_max_completion_tokens,
                extra_body={'thinking': {'type': 'disabled'}},
            )
        except Exception as exc:
            return InternalPowerMimoResult(parsed=None, raw_text='', error=f'Mimo调用失败：{exc}')

        raw_text = cls.__extract_completion_text(completion)
        parsed = cls.parse_json_response(raw_text)
        if parsed is None:
            return InternalPowerMimoResult(parsed=None, raw_text=raw_text, error='模型未返回可解析JSON')
        return InternalPowerMimoResult(parsed=parsed, raw_text=raw_text)

    @classmethod
    def parse_json_response(cls, text: str) -> dict[str, Any] | None:
        cleaned = (text or '').strip()
        if not cleaned:
            return None
        fenced_match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned, flags=re.IGNORECASE | re.DOTALL)
        if fenced_match:
            cleaned = fenced_match.group(1).strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    @staticmethod
    def validate_parsed_result(parsed: dict[str, Any]) -> str:
        power_name = str(parsed.get('内功名') or '').strip()
        entries = parsed.get('属性加成')
        if not power_name:
            return '识别结果缺少内功名'
        if not isinstance(entries, list):
            return '识别结果缺少属性加成列表'
        for index, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                return f'第{index}条属性加成格式错误'
            if not str(entry.get('词条') or '').strip():
                return f'第{index}条属性加成缺少词条'
            if entry.get('数值') is None or str(entry.get('数值')).strip() == '':
                return f'第{index}条属性加成缺少数值'
        return ''

    @staticmethod
    def __extract_completion_text(completion: Any) -> str:
        try:
            content = completion.choices[0].message.content
        except Exception:
            return ''
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(str(item.get('text') or ''))
                elif hasattr(item, 'text'):
                    parts.append(str(item.text or ''))
            return ''.join(parts)
        return str(content or '')
