from datetime import datetime
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
async def test_mimo_prefers_api_key_configured_in_system_settings(monkeypatch):
    async def fake_get_internal_power_api_key(_query_db):
        return 'configured-key'

    monkeypatch.setattr(
        'module_admin.service.internal_power_mimo_service.AiKeyService.get_internal_power_api_key',
        fake_get_internal_power_api_key,
    )
    monkeypatch.setattr('module_admin.service.internal_power_mimo_service.MimoConfig.mimo_api_key', 'environment-key')

    assert await InternalPowerMimoService._get_api_key(object()) == 'configured-key'


@pytest.mark.asyncio
async def test_mimo_runtime_does_not_fallback_to_environment_key_when_system_key_is_empty(monkeypatch):
    async def fake_get_internal_power_api_key(_query_db):
        return ''

    monkeypatch.setattr(
        'module_admin.service.internal_power_mimo_service.AiKeyService.get_internal_power_api_key',
        fake_get_internal_power_api_key,
    )
    monkeypatch.setattr('module_admin.service.internal_power_mimo_service.MimoConfig.mimo_api_key', 'environment-key')

    assert await InternalPowerMimoService._get_api_key(object()) == ''


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
        self.commit_count = 0

    async def commit(self):
        self.committed = True
        self.commit_count += 1


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


class ExpiringHistory:
    def __init__(self, db, record_id, user_id):
        self._db = db
        self._record_id = record_id
        self._user_id = user_id
        self._loaded_commit_count = db.commit_count

    @property
    def record_id(self):
        if self._db.commit_count > self._loaded_commit_count:
            raise AssertionError('record_id was read after commit expired the ORM object')
        return self._record_id

    @property
    def user_id(self):
        if self._db.commit_count > self._loaded_commit_count:
            raise AssertionError('user_id was read after commit expired the ORM object')
        return self._user_id


class ExpiringUser:
    def __init__(self, db, user_id):
        self._db = db
        self._user_id = user_id
        self._loaded_commit_count = db.commit_count
        self.ai_image_recognition_count = 2
        self.vip_ai_image_recognition_count = 0
        self.is_vip = '0'
        self.vip_expire_time = None
        self.sponsored_vip = '0'

    @property
    def user_id(self):
        if self._db.commit_count > self._loaded_commit_count:
            raise AssertionError('user_id was read after commit expired the ORM object')
        return self._user_id


def install_history_fakes(monkeypatch):
    counter = {'next': 0}

    async def fake_add(db, values):
        counter['next'] += 1
        return SimpleNamespace(record_id=counter['next'], user_id=values['user_id'])

    async def fake_update(db, record_id, user_id, values):
        return None

    async def fake_trim(db, user_id, keep_count=50):
        return None

    monkeypatch.setattr('module_admin.service.internal_power_service.InternalPowerRecognitionHistoryDao.add', fake_add)
    monkeypatch.setattr('module_admin.service.internal_power_service.InternalPowerRecognitionHistoryDao.update', fake_update)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerRecognitionHistoryDao.trim_by_user_id',
        fake_trim,
    )


@pytest.mark.asyncio
async def test_recognize_images_keeps_history_ids_before_commit_to_avoid_async_lazy_load(monkeypatch):
    counter = {'next': 0}
    updates = []

    async def fake_add(db, values):
        counter['next'] += 1
        return ExpiringHistory(db, counter['next'], values['user_id'])

    async def fake_update(db, record_id, user_id, values):
        updates.append((record_id, user_id, values.get('status')))

    async def fake_trim(db, user_id, keep_count=50):
        return None

    async def fake_get_user_detail_by_id(db, user_id):
        return {
            'user_basic_info': SimpleNamespace(
                user_id=user_id,
                ai_image_recognition_count=2,
                vip_ai_image_recognition_count=0,
                is_vip='0',
                vip_expire_time=None,
                sponsored_vip='0',
            )
        }

    async def fake_decrement_ai_recognition_counts(db, user_id, vip_count, normal_count, update_by):
        return True

    async def fake_presets(db):
        return [make_preset(1, '贯山月', 'metal')]

    async def fake_recognize_image(image_bytes, mime_type, prompt, **_kwargs):
        return SimpleNamespace(
            parsed={'内功名': '贯山月', '属性加成': [{'词条': '攻击', '数值': 33}]},
            raw_text='{}',
            error='',
        )

    monkeypatch.setattr('module_admin.service.internal_power_service.InternalPowerRecognitionHistoryDao.add', fake_add)
    monkeypatch.setattr('module_admin.service.internal_power_service.InternalPowerRecognitionHistoryDao.update', fake_update)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerRecognitionHistoryDao.trim_by_user_id',
        fake_trim,
    )
    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_recognition_counts',
        fake_decrement_ai_recognition_counts,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerPresetService.get_personal_enabled_presets_service',
        fake_presets,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerMimoService.recognize_image',
        fake_recognize_image,
    )

    result = await InternalPowerService.recognize_images_services(
        FakeDb(),
        make_current_user(),
        [FakeUpload('ok.png')],
        'prompt',
    )

    assert result.result['items'][0]['recordId'] == 1
    assert updates == [(1, 100, 'recognized')]


@pytest.mark.asyncio
async def test_recognize_images_keeps_user_scalars_before_commit_to_avoid_async_lazy_load(monkeypatch):
    decrements = []

    async def fake_add(db, values):
        return SimpleNamespace(record_id=1, user_id=values['user_id'])

    async def fake_update(db, record_id, user_id, values):
        return None

    async def fake_trim(db, user_id, keep_count=50):
        return None

    async def fake_get_user_detail_by_id(db, user_id):
        return {'user_basic_info': ExpiringUser(db, user_id)}

    async def fake_decrement_ai_recognition_counts(db, user_id, vip_count, normal_count, update_by):
        decrements.append({'user_id': user_id, 'vip_count': vip_count, 'normal_count': normal_count, 'update_by': update_by})
        return True

    async def fake_presets(db):
        return [make_preset(1, '贯山月', 'metal')]

    async def fake_recognize_image(image_bytes, mime_type, prompt, **_kwargs):
        return SimpleNamespace(
            parsed={'内功名': '贯山月', '属性加成': [{'词条': '攻击', '数值': 33}]},
            raw_text='{}',
            error='',
        )

    monkeypatch.setattr('module_admin.service.internal_power_service.InternalPowerRecognitionHistoryDao.add', fake_add)
    monkeypatch.setattr('module_admin.service.internal_power_service.InternalPowerRecognitionHistoryDao.update', fake_update)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerRecognitionHistoryDao.trim_by_user_id',
        fake_trim,
    )
    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_recognition_counts',
        fake_decrement_ai_recognition_counts,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerPresetService.get_personal_enabled_presets_service',
        fake_presets,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerMimoService.recognize_image',
        fake_recognize_image,
    )

    result = await InternalPowerService.recognize_images_services(
        FakeDb(),
        make_current_user(),
        [FakeUpload('ok.png')],
        'prompt',
    )

    assert result.result['items'][0]['success'] is True
    assert decrements == [{'user_id': 100, 'vip_count': 0, 'normal_count': 1, 'update_by': 'admin'}]


@pytest.mark.asyncio
async def test_recognition_history_marks_stale_recognizing_records_failed(monkeypatch):
    stale_history = SimpleNamespace(
        record_id=9,
        user_id=100,
        file_name='stale.png',
        image_base64='',
        mime_type='image/png',
        status='recognizing',
        parsed_json='{}',
        raw_text='',
        error='',
        preset_candidates_json='[]',
        saved_power_id=None,
        create_time=datetime(2026, 6, 30, 10, 0, 0),
        update_time=datetime(2026, 6, 30, 10, 0, 0),
    )
    fresh_failed_history = SimpleNamespace(**{**stale_history.__dict__, 'status': 'failed', 'error': '识别任务已中断或超时'})
    calls = {'list': 0, 'updates': []}

    async def fake_list_by_user_id(db, user_id, page_num=1, page_size=10):
        calls['list'] += 1
        rows = [stale_history] if calls['list'] == 1 else [fresh_failed_history]
        return SimpleNamespace(rows=rows, total=1, page_num=page_num, page_size=page_size, has_next=False)

    async def fake_update(db, record_id, user_id, values):
        calls['updates'].append((record_id, user_id, values))

    monkeypatch.setattr('module_admin.service.internal_power_service.InternalPowerRecognitionHistoryDao.list_by_user_id', fake_list_by_user_id)
    monkeypatch.setattr('module_admin.service.internal_power_service.InternalPowerRecognitionHistoryDao.update', fake_update)
    monkeypatch.setattr('module_admin.service.internal_power_service.datetime', SimpleNamespace(now=lambda: datetime(2026, 6, 30, 10, 30, 0)))

    db = FakeDb()
    result = await InternalPowerService.get_recognition_history_services(db, make_current_user())

    assert db.committed is True
    assert calls['updates'][0][0] == 9
    assert calls['updates'][0][2]['status'] == 'failed'
    assert result.items[0].status == 'failed'
    assert result.items[0].error == '识别任务已中断或超时'
    assert result.total == 1
    assert result.page_size == 10


@pytest.mark.asyncio
async def test_recognize_images_deducts_only_successful_images_and_returns_candidates(monkeypatch):
    decrements = []
    install_history_fakes(monkeypatch)

    async def fake_get_user_detail_by_id(db, user_id):
        return {
            'user_basic_info': SimpleNamespace(
                user_id=user_id,
                ai_image_recognition_count=5,
                vip_ai_image_recognition_count=0,
                is_vip='0',
                vip_expire_time=None,
                sponsored_vip='0',
            )
        }

    async def fake_decrement_ai_recognition_counts(db, user_id, vip_count, normal_count, update_by):
        decrements.append(
            {'user_id': user_id, 'vip_count': vip_count, 'normal_count': normal_count, 'update_by': update_by}
        )
        return True

    async def fake_presets(db):
        return [
            make_preset(1, '稀有-灼星贯日', 'wood'),
            make_preset(2, '稀有-灼星贯日', 'fire'),
        ]

    async def fake_recognize_image(image_bytes, mime_type, prompt, **_kwargs):
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
        'module_admin.service.internal_power_service.UserDao.decrement_ai_recognition_counts',
        fake_decrement_ai_recognition_counts,
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
    assert result.consumed_vip_count == 0
    assert result.consumed_normal_count == 1
    assert result.remaining_ai_image_recognition_count == 4
    assert db.committed is True
    assert decrements == [{'user_id': 100, 'vip_count': 0, 'normal_count': 1, 'update_by': 'admin'}]
    assert result.result['items'][0]['success'] is True
    assert result.result['items'][0]['recordId'] == 1
    assert len(result.result['items'][0]['presetCandidates']) == 2
    assert result.result['items'][0]['needsPresetSelection'] is True
    assert result.result['items'][0]['presetSelectionMessage'] == '该内功存在多个元素，请选择元素后再新增'
    assert result.result['items'][1]['success'] is False


@pytest.mark.asyncio
async def test_recognize_images_filters_multi_element_candidates_when_element_is_recognized(monkeypatch):
    install_history_fakes(monkeypatch)

    async def fake_get_user_detail_by_id(db, user_id):
        return {
            'user_basic_info': SimpleNamespace(
                user_id=user_id,
                ai_image_recognition_count=5,
                vip_ai_image_recognition_count=0,
                is_vip='0',
                vip_expire_time=None,
                sponsored_vip='0',
            )
        }

    async def fake_decrement_ai_recognition_counts(db, user_id, vip_count, normal_count, update_by):
        return True

    async def fake_presets(db):
        return [
            make_preset(1, '稀有-不动明王', 'wood'),
            make_preset(2, '稀有-不动明王', 'water'),
        ]

    async def fake_recognize_image(image_bytes, mime_type, prompt, **_kwargs):
        return SimpleNamespace(
            parsed={'内功名': '稀有-不动明王', '元素': '水', '属性加成': [{'词条': '气血上限', '数值': 2084}]},
            raw_text='{}',
            error='',
        )

    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_recognition_counts',
        fake_decrement_ai_recognition_counts,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerPresetService.get_personal_enabled_presets_service',
        fake_presets,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerMimoService.recognize_image',
        fake_recognize_image,
    )

    result = await InternalPowerService.recognize_images_services(
        FakeDb(),
        make_current_user(),
        [FakeUpload('water.png')],
        'prompt',
    )

    item = result.result['items'][0]
    assert item['success'] is True
    assert item['needsPresetSelection'] is False
    assert [candidate['elementKey'] for candidate in item['presetCandidates']] == ['water']


@pytest.mark.asyncio
async def test_recognize_images_normalizes_plain_rare_power_name_and_filters_by_element(monkeypatch):
    install_history_fakes(monkeypatch)

    async def fake_get_user_detail_by_id(db, user_id):
        return {
            'user_basic_info': SimpleNamespace(
                user_id=user_id,
                ai_image_recognition_count=5,
                vip_ai_image_recognition_count=0,
                is_vip='0',
                vip_expire_time=None,
                sponsored_vip='0',
            )
        }

    async def fake_decrement_ai_recognition_counts(db, user_id, vip_count, normal_count, update_by):
        return True

    async def fake_presets(db):
        return [
            make_preset(1, '稀有-不动明王', 'wood'),
            make_preset(2, '稀有-不动明王', 'water'),
        ]

    async def fake_recognize_image(image_bytes, mime_type, prompt, **_kwargs):
        return SimpleNamespace(
            parsed={'内功名': '不动明王', '元素': '水', '属性加成': [{'词条': '气血上限', '数值': 2084}]},
            raw_text='{}',
            error='',
        )

    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_recognition_counts',
        fake_decrement_ai_recognition_counts,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerPresetService.get_personal_enabled_presets_service',
        fake_presets,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerMimoService.recognize_image',
        fake_recognize_image,
    )

    result = await InternalPowerService.recognize_images_services(
        FakeDb(),
        make_current_user(),
        [FakeUpload('rare-water.png')],
        'prompt',
    )

    item = result.result['items'][0]
    assert item['success'] is True
    assert item['parsed']['内功名'] == '稀有-不动明王'
    assert item['needsPresetSelection'] is False
    assert [candidate['elementKey'] for candidate in item['presetCandidates']] == ['water']


@pytest.mark.asyncio
async def test_recognize_images_normalizes_trial_rare_power_name(monkeypatch):
    install_history_fakes(monkeypatch)

    async def fake_get_user_detail_by_id(db, user_id):
        return {
            'user_basic_info': SimpleNamespace(
                user_id=user_id,
                ai_image_recognition_count=5,
                vip_ai_image_recognition_count=0,
                is_vip='0',
                vip_expire_time=None,
                sponsored_vip='0',
            )
        }

    async def fake_decrement_ai_recognition_counts(db, user_id, vip_count, normal_count, update_by):
        return True

    async def fake_presets(db):
        return [
            make_preset(1, '稀有-绝电惊沙', 'metal'),
            make_preset(2, '稀有-绝电惊沙', 'wood'),
        ]

    async def fake_recognize_image(image_bytes, mime_type, prompt, **_kwargs):
        return SimpleNamespace(
            parsed={'内功名': '绝电惊沙·试用', '元素': '金', '属性加成': [{'词条': '会心', '数值': 57}]},
            raw_text='{}',
            error='',
        )

    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_recognition_counts',
        fake_decrement_ai_recognition_counts,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerPresetService.get_personal_enabled_presets_service',
        fake_presets,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerMimoService.recognize_image',
        fake_recognize_image,
    )

    result = await InternalPowerService.recognize_images_services(
        FakeDb(),
        make_current_user(),
        [FakeUpload('trial-metal.png')],
        'prompt',
    )

    item = result.result['items'][0]
    assert item['success'] is True
    assert item['parsed']['内功名'] == '稀有-绝电惊沙'
    assert item['needsPresetSelection'] is False
    assert [candidate['elementKey'] for candidate in item['presetCandidates']] == ['metal']


@pytest.mark.asyncio
async def test_recognize_images_keeps_old_json_without_element_when_single_candidate(monkeypatch):
    install_history_fakes(monkeypatch)

    async def fake_get_user_detail_by_id(db, user_id):
        return {
            'user_basic_info': SimpleNamespace(
                user_id=user_id,
                ai_image_recognition_count=5,
                vip_ai_image_recognition_count=0,
                is_vip='0',
                vip_expire_time=None,
                sponsored_vip='0',
            )
        }

    async def fake_decrement_ai_recognition_counts(db, user_id, vip_count, normal_count, update_by):
        return True

    async def fake_presets(db):
        return [make_preset(1, '贯山月', 'metal')]

    async def fake_recognize_image(image_bytes, mime_type, prompt, **_kwargs):
        return SimpleNamespace(
            parsed={'内功名': '贯山月', '属性加成': [{'词条': '攻击', '数值': 33}]},
            raw_text='{}',
            error='',
        )

    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_recognition_counts',
        fake_decrement_ai_recognition_counts,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerPresetService.get_personal_enabled_presets_service',
        fake_presets,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerMimoService.recognize_image',
        fake_recognize_image,
    )

    result = await InternalPowerService.recognize_images_services(
        FakeDb(),
        make_current_user(),
        [FakeUpload('old-json.png')],
        'prompt',
    )

    item = result.result['items'][0]
    assert item['success'] is True
    assert item['needsPresetSelection'] is False
    assert [candidate['elementKey'] for candidate in item['presetCandidates']] == ['metal']


@pytest.mark.asyncio
async def test_recognize_images_keeps_multi_element_candidates_when_element_is_unknown(monkeypatch):
    install_history_fakes(monkeypatch)

    async def fake_get_user_detail_by_id(db, user_id):
        return {
            'user_basic_info': SimpleNamespace(
                user_id=user_id,
                ai_image_recognition_count=5,
                vip_ai_image_recognition_count=0,
                is_vip='0',
                vip_expire_time=None,
                sponsored_vip='0',
            )
        }

    async def fake_decrement_ai_recognition_counts(db, user_id, vip_count, normal_count, update_by):
        return True

    async def fake_presets(db):
        return [
            make_preset(1, '稀有-不动明王', 'wood'),
            make_preset(2, '稀有-不动明王', 'water'),
        ]

    async def fake_recognize_image(image_bytes, mime_type, prompt, **_kwargs):
        return SimpleNamespace(
            parsed={'内功名': '稀有-不动明王', '元素': '看不清', '属性加成': [{'词条': '气血上限', '数值': 2084}]},
            raw_text='{}',
            error='',
        )

    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_recognition_counts',
        fake_decrement_ai_recognition_counts,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerPresetService.get_personal_enabled_presets_service',
        fake_presets,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerMimoService.recognize_image',
        fake_recognize_image,
    )

    result = await InternalPowerService.recognize_images_services(
        FakeDb(),
        make_current_user(),
        [FakeUpload('unknown.png')],
        'prompt',
    )

    item = result.result['items'][0]
    assert item['success'] is True
    assert item['needsPresetSelection'] is True
    assert [candidate['elementKey'] for candidate in item['presetCandidates']] == ['wood', 'water']


@pytest.mark.asyncio
async def test_recognize_images_does_not_deduct_when_all_images_fail(monkeypatch):
    decrements = []
    install_history_fakes(monkeypatch)

    async def fake_get_user_detail_by_id(db, user_id):
        return {
            'user_basic_info': SimpleNamespace(
                user_id=user_id,
                ai_image_recognition_count=3,
                vip_ai_image_recognition_count=0,
                is_vip='0',
                vip_expire_time=None,
                sponsored_vip='0',
            )
        }

    async def fake_decrement_ai_recognition_counts(db, user_id, vip_count, normal_count, update_by):
        decrements.append({'user_id': user_id, 'vip_count': vip_count, 'normal_count': normal_count, 'update_by': update_by})
        return True

    async def fake_presets(db):
        return [make_preset(1, '贯山月', 'metal')]

    async def fake_recognize_image(image_bytes, mime_type, prompt, **_kwargs):
        return SimpleNamespace(parsed=None, raw_text='oops', error='模型未返回可解析JSON')

    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_recognition_counts',
        fake_decrement_ai_recognition_counts,
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
    assert db.committed is True


@pytest.mark.asyncio
async def test_recognize_images_admin_can_use_without_remaining_count_and_does_not_deduct(monkeypatch):
    decrements = []
    install_history_fakes(monkeypatch)

    async def fake_get_user_detail_by_id(db, user_id):
        return {
            'user_basic_info': SimpleNamespace(
                user_id=user_id,
                ai_image_recognition_count=0,
                vip_ai_image_recognition_count=0,
                is_vip='0',
                vip_expire_time=None,
                sponsored_vip='0',
            )
        }

    async def fake_decrement_ai_recognition_counts(db, user_id, vip_count, normal_count, update_by):
        decrements.append({'user_id': user_id, 'vip_count': vip_count, 'normal_count': normal_count, 'update_by': update_by})
        return True

    async def fake_presets(db):
        return [make_preset(1, '贯山月', 'metal')]

    async def fake_recognize_image(image_bytes, mime_type, prompt, **_kwargs):
        return SimpleNamespace(
            parsed={'内功名': '贯山月', '属性加成': [{'词条': '攻击', '数值': 33}]},
            raw_text='{}',
            error='',
        )

    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_recognition_counts',
        fake_decrement_ai_recognition_counts,
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
    assert db.committed is True


@pytest.mark.asyncio
async def test_recognize_images_marks_success_items_failed_when_atomic_deduct_fails(monkeypatch):
    install_history_fakes(monkeypatch)

    async def fake_get_user_detail_by_id(db, user_id):
        return {
            'user_basic_info': SimpleNamespace(
                user_id=user_id,
                ai_image_recognition_count=1,
                vip_ai_image_recognition_count=0,
                is_vip='0',
                vip_expire_time=None,
                sponsored_vip='0',
            )
        }

    async def fake_decrement_ai_recognition_counts(db, user_id, vip_count, normal_count, update_by):
        return False

    async def fake_presets(db):
        return [make_preset(1, '贯山月', 'metal')]

    async def fake_recognize_image(image_bytes, mime_type, prompt, **_kwargs):
        return SimpleNamespace(
            parsed={'内功名': '贯山月', '属性加成': [{'词条': '攻击', '数值': 33}]},
            raw_text='{}',
            error='',
        )

    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_recognition_counts',
        fake_decrement_ai_recognition_counts,
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
    assert db.committed is True


@pytest.mark.asyncio
async def test_recognize_images_deducts_vip_count_before_normal_count(monkeypatch):
    install_history_fakes(monkeypatch)
    decrements = []

    async def fake_get_user_detail_by_id(db, user_id):
        return {
            'user_basic_info': SimpleNamespace(
                user_id=user_id,
                ai_image_recognition_count=5,
                vip_ai_image_recognition_count=1,
                is_vip='1',
                vip_expire_time=datetime(2099, 1, 1),
                sponsored_vip='0',
            )
        }

    async def fake_decrement_ai_recognition_counts(db, user_id, vip_count, normal_count, update_by):
        decrements.append({'vip_count': vip_count, 'normal_count': normal_count})
        return True

    async def fake_presets(db):
        return [make_preset(1, '贯山月', 'metal')]

    async def fake_recognize_image(image_bytes, mime_type, prompt, **_kwargs):
        return SimpleNamespace(
            parsed={'内功名': '贯山月', '属性加成': [{'词条': '攻击', '数值': 33}]},
            raw_text='{}',
            error='',
        )

    monkeypatch.setattr('module_admin.service.internal_power_service.UserDao.get_user_detail_by_id', fake_get_user_detail_by_id)
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.UserDao.decrement_ai_recognition_counts',
        fake_decrement_ai_recognition_counts,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerPresetService.get_personal_enabled_presets_service',
        fake_presets,
    )
    monkeypatch.setattr(
        'module_admin.service.internal_power_service.InternalPowerMimoService.recognize_image',
        fake_recognize_image,
    )

    result = await InternalPowerService.recognize_images_services(
        FakeDb(),
        make_current_user(),
        [FakeUpload('one.png'), FakeUpload('two.png')],
        'prompt',
    )

    assert result.consumed_count == 2
    assert result.consumed_vip_count == 1
    assert result.consumed_normal_count == 1
    assert result.remaining_vip_ai_image_recognition_count == 0
    assert result.remaining_ai_image_recognition_count == 4
    assert decrements == [{'vip_count': 1, 'normal_count': 1}]
