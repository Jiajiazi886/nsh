from types import SimpleNamespace

import pytest

from module_admin.entity.vo.ai_key_vo import AiTestMessageModel
from module_admin.service.ai_connection_client import AiConnectionClientService
from module_admin.service.ai_key_service import ActiveAiConnection


def runtime(protocol='chat_completions'):
    return ActiveAiConnection(
        id=1,
        name='test',
        provider='Custom',
        base_url='https://example.com/v1',
        api_key='secret',
        protocol=protocol,
        model='vision-model',
        max_tokens=500,
        temperature=0.3,
        support_images=True,
    )


@pytest.mark.asyncio
async def test_list_models_returns_sorted_unique_ids():
    class FakeModels:
        async def list(self):
            return SimpleNamespace(data=[SimpleNamespace(id='z-model'), SimpleNamespace(id='a-model'), SimpleNamespace(id='a-model')])

    client = SimpleNamespace(models=FakeModels())

    result = await AiConnectionClientService.list_models(runtime(), client=client)

    assert result == ['a-model', 'z-model']


@pytest.mark.asyncio
async def test_chat_completions_uses_selected_runtime_and_image_payload():
    captured = {}

    class FakeCompletions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='ok'))])

    client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    messages = [
        AiTestMessageModel(
            role='user',
            content='describe',
            images=['data:image/png;base64,YWJj'],
        )
    ]

    result = await AiConnectionClientService.chat(runtime(), messages, client=client)

    assert result == 'ok'
    assert captured['model'] == 'vision-model'
    assert captured['max_completion_tokens'] == 500
    assert captured['temperature'] == 0.3
    assert captured['messages'][0]['content'][0]['type'] == 'image_url'


@pytest.mark.asyncio
async def test_responses_protocol_uses_responses_input_shape():
    captured = {}

    class FakeResponses:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_text='response-ok')

    client = SimpleNamespace(responses=FakeResponses())
    messages = [AiTestMessageModel(role='user', content='hello')]

    result = await AiConnectionClientService.chat(runtime('responses'), messages, client=client)

    assert result == 'response-ok'
    assert captured['model'] == 'vision-model'
    assert captured['max_output_tokens'] == 500
    assert captured['input'][0]['content'] == [{'type': 'input_text', 'text': 'hello'}]


@pytest.mark.asyncio
async def test_chat_rejects_images_when_connection_does_not_support_them():
    disabled = runtime()
    disabled = ActiveAiConnection(**{**disabled.__dict__, 'support_images': False})
    messages = [AiTestMessageModel(role='user', content='', images=['data:image/png;base64,YWJj'])]

    with pytest.raises(Exception) as exc_info:
        await AiConnectionClientService.chat(disabled, messages, client=object())

    assert '未启用图片能力' in exc_info.value.message
