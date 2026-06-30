from types import SimpleNamespace

import pytest

from module_admin.service.internal_power_mimo_service import InternalPowerMimoService
from module_admin.service.internal_power_service import InternalPowerService


def test_mimo_build_data_url_includes_mime_prefix():
    data_url = InternalPowerMimoService.build_data_url(b'abc', 'image/png')

    assert data_url == 'data:image/png;base64,YWJj'


def test_mimo_parse_json_response_supports_plain_and_fenced_json():
    plain = '{"内功名":"贯山月","属性加成":[]}'
    fenced = '```json\n{"内功名":"贯山月","属性加成":[]}\n```'

    assert InternalPowerMimoService.parse_json_response(plain)['内功名'] == '贯山月'
    assert InternalPowerMimoService.parse_json_response(fenced)['内功名'] == '贯山月'


@pytest.mark.asyncio
async def test_mimo_request_uses_openai_compatible_image_payload_and_disabled_thinking(monkeypatch):
    captured = {}

    class FakeCompletions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content='{"内功名":"贯山月","属性加成":[{"词条":"攻击","数值":33}]}')
                    )
                ]
            )

    class FakeClient:
        chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr('module_admin.service.internal_power_mimo_service.MimoConfig.mimo_api_key', 'test-key')
    monkeypatch.setattr('module_admin.service.internal_power_mimo_service.MimoConfig.mimo_model', 'mimo-v2.5')
    monkeypatch.setattr('module_admin.service.internal_power_mimo_service.MimoConfig.mimo_max_completion_tokens', 128)

    result = await InternalPowerMimoService.recognize_image(
        b'abc',
        'image/jpeg',
        '固定提示词',
        client=FakeClient(),
    )

    assert result.error == ''
    assert captured['model'] == 'mimo-v2.5'
    assert captured['extra_body'] == {'thinking': {'type': 'disabled'}}
    user_content = captured['messages'][1]['content']
    assert user_content[0]['type'] == 'image_url'
    assert user_content[0]['image_url']['url'].startswith('data:image/jpeg;base64,')
    assert user_content[1] == {'type': 'text', 'text': '固定提示词'}


class FakeDb:
    def __init__(self):
        self.committed = False

    async def commit(self):
        self.committed = True


class FakeUpload:
    def __init__(self, filename, content_type='image/png'):
        self.filename = filename
        self.content_type = content_type

    async def read(self):
        return b'fake-image'


def make_current_user(roles=None):
    return SimpleNamespace(user=SimpleNamespace(user_id=100, user_name='admin'), roles=roles or [])


def make_preset(preset_id, name, element_key):
    return SimpleNamespace(
        preset_id=preset_id,
        name=name,
        display_name=f'{name}（{element_key}）',
        element_key=element_key,
        elements={'metal': 4 if element_key == 'metal' else 0, 'wood': 4 if element_key == 'wood' else 0},
        bonus_percent=0,
        bonus_type='',
        bonus_desc='',
        image_url='',
        entries=[],
    )


@pytest.mark.asyncio
async def test_recognize_images_deducts_only_successful_images_and_returns_candidates(monkeypatch):
    decrements = []

    async def fake_get_user_detail_by_id(db, user_id):
        return {'user_basic_info': SimpleNamespace(user_id=user_id, ai_image_recognition_count=5)}

    async def fake_decrement_ai_image_recognition_count(db, user_id, count, update_by):
        decrements.append({'user_id': user_id, 'count': count, 'update_by': update_by})
        return True

    async def fake_presets(db):
        return [
            make_preset(1, '稀有-灼星贯日', 'wood'),
            make_preset(2, '稀有-灼星贯日', 'fire'),
        ]

    async def fake_recognize_image(image_bytes, mime_type, prompt):
        if prompt == 'bad':
            raise AssertionError('unexpected prompt')
        if len(calls := getattr(fake_recognize_image, 'calls', [])) == 0:
            fake_recognize_image.calls = ['first']
            return SimpleNamespace(
                parsed={'内功名': '稀有-灼星贯日', '属性加成': [{'词条': '灵韵', '数值': 1}]},
                raw_text='{}',
                error='',
            )
        calls.append('second')
        return SimpleNamespace(parsed=None, raw_text='not json', error='模型未返回可解析JSON')

    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_image_recognition_count',
        fake_decrement_ai_image_recognition_count,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerPresetService.get_personal_enabled_presets_service',
        fake_presets,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerMimoService.recognize_image',
        fake_recognize_image,
    )

    db = FakeDb()
    result = await InternalPowerService.recognize_images_services(
        db,
        make_current_user(),
        [FakeUpload('ok.png'), FakeUpload('fail.png')],
        'prompt',
    )

    assert result.consumed_count == 1
    assert result.remaining_ai_image_recognition_count == 4
    assert db.committed is True
    assert decrements == [{'user_id': 100, 'count': 1, 'update_by': 'admin'}]
    assert result.result['items'][0]['success'] is True
    assert len(result.result['items'][0]['presetCandidates']) == 2
    assert result.result['items'][1]['success'] is False


@pytest.mark.asyncio
async def test_recognize_images_does_not_deduct_when_all_images_fail(monkeypatch):
    decrements = []

    async def fake_get_user_detail_by_id(db, user_id):
        return {'user_basic_info': SimpleNamespace(user_id=user_id, ai_image_recognition_count=3)}

    async def fake_decrement_ai_image_recognition_count(db, user_id, count, update_by):
        decrements.append({'user_id': user_id, 'count': count, 'update_by': update_by})
        return True

    async def fake_presets(db):
        return [make_preset(1, '贯山月', 'metal')]

    async def fake_recognize_image(image_bytes, mime_type, prompt):
        return SimpleNamespace(parsed=None, raw_text='oops', error='模型未返回可解析JSON')

    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_image_recognition_count',
        fake_decrement_ai_image_recognition_count,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerPresetService.get_personal_enabled_presets_service',
        fake_presets,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerMimoService.recognize_image',
        fake_recognize_image,
    )

    db = FakeDb()
    result = await InternalPowerService.recognize_images_services(
        db,
        make_current_user(),
        [FakeUpload('fail.png')],
        'prompt',
    )

    assert result.consumed_count == 0
    assert result.remaining_ai_image_recognition_count == 3
    assert decrements == []
    assert db.committed is False


@pytest.mark.asyncio
async def test_recognize_images_admin_can_use_without_remaining_count_and_does_not_deduct(monkeypatch):
    decrements = []

    async def fake_get_user_detail_by_id(db, user_id):
        return {'user_basic_info': SimpleNamespace(user_id=user_id, ai_image_recognition_count=0)}

    async def fake_decrement_ai_image_recognition_count(db, user_id, count, update_by):
        decrements.append({'user_id': user_id, 'count': count, 'update_by': update_by})
        return True

    async def fake_presets(db):
        return [make_preset(1, '贯山月', 'metal')]

    async def fake_recognize_image(image_bytes, mime_type, prompt):
        return SimpleNamespace(
            parsed={'内功名': '贯山月', '属性加成': [{'词条': '攻击', '数值': 33}]},
            raw_text='{}',
            error='',
        )

    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_image_recognition_count',
        fake_decrement_ai_image_recognition_count,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerPresetService.get_personal_enabled_presets_service',
        fake_presets,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerMimoService.recognize_image',
        fake_recognize_image,
    )

    db = FakeDb()
    result = await InternalPowerService.recognize_images_services(
        db,
        make_current_user(roles=['admin']),
        [FakeUpload('ok.png')],
        'prompt',
    )

    assert result.consumed_count == 0
    assert result.remaining_ai_image_recognition_count == 0
    assert result.result['items'][0]['success'] is True
    assert decrements == []
    assert db.committed is False


@pytest.mark.asyncio
async def test_recognize_images_marks_success_items_failed_when_atomic_deduct_fails(monkeypatch):
    async def fake_get_user_detail_by_id(db, user_id):
        return {'user_basic_info': SimpleNamespace(user_id=user_id, ai_image_recognition_count=1)}

    async def fake_decrement_ai_image_recognition_count(db, user_id, count, update_by):
        return False

    async def fake_presets(db):
        return [make_preset(1, '贯山月', 'metal')]

    async def fake_recognize_image(image_bytes, mime_type, prompt):
        return SimpleNamespace(
            parsed={'内功名': '贯山月', '属性加成': [{'词条': '攻击', '数值': 33}]},
            raw_text='{}',
            error='',
        )

    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_image_recognition_count',
        fake_decrement_ai_image_recognition_count,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerPresetService.get_personal_enabled_presets_service',
        fake_presets,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerMimoService.recognize_image',
        fake_recognize_image,
    )

    db = FakeDb()
    result = await InternalPowerService.recognize_images_services(
        db,
        make_current_user(),
        [FakeUpload('ok.png')],
        'prompt',
    )

    assert result.consumed_count == 0
    assert result.remaining_ai_image_recognition_count == 1
    assert result.result['items'][0]['success'] is False
    assert result.result['items'][0]['error'] == 'AI识图次数不足，未扣次'
    assert result.result['items'][0]['presetCandidates'] == []
    assert db.committed is False
