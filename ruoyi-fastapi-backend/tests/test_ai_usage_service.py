from types import SimpleNamespace

import pytest

from common.vo import PageModel
from module_admin.entity.vo.ai_usage_vo import AiUsagePageQueryModel
from module_admin.service.ai_usage_service import AiUsageService
from utils.page_util import PageUtil


def test_extract_chat_completions_usage_uses_provider_values():
    response = SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=123, completion_tokens=45, total_tokens=168)
    )

    usage = AiUsageService.extract_usage('chat_completions', response)

    assert usage.reported is True
    assert usage.input_tokens == 123
    assert usage.output_tokens == 45
    assert usage.total_tokens == 168


def test_extract_responses_usage_uses_provider_values():
    response = SimpleNamespace(
        usage=SimpleNamespace(input_tokens=321, output_tokens=54, total_tokens=375)
    )

    usage = AiUsageService.extract_usage('responses', response)

    assert usage.reported is True
    assert usage.input_tokens == 321
    assert usage.output_tokens == 54
    assert usage.total_tokens == 375


def test_missing_usage_is_not_reported_and_is_not_estimated():
    usage = AiUsageService.extract_usage('chat_completions', SimpleNamespace())

    assert usage.reported is False
    assert usage.input_tokens is None
    assert usage.output_tokens is None
    assert usage.total_tokens is None


def test_error_summary_redacts_secrets_and_content():
    summary = AiUsageService.sanitize_error(
        'Authorization: Bearer secret-key api_key=second-secret\n' + ('x' * 900),
        secrets=('secret-key', 'second-secret'),
    )

    assert 'secret-key' not in summary
    assert 'second-secret' not in summary
    assert '***' in summary
    assert len(summary) <= 500


@pytest.mark.asyncio
async def test_list_records_returns_camel_case_page_model(monkeypatch):
    async def fake_paginate(*_args, **_kwargs):
        return PageModel(rows=[], pageNum=1, pageSize=20, total=0, hasNext=False)

    monkeypatch.setattr(PageUtil, 'paginate', fake_paginate)

    page = await AiUsageService.list_records(SimpleNamespace(), AiUsagePageQueryModel())

    assert page.model_dump(by_alias=True) == {
        'rows': [],
        'pageNum': 1,
        'pageSize': 20,
        'total': 0,
        'hasNext': False,
    }
