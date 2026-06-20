from types import SimpleNamespace

import pytest

from module_guild.constants.class_color_defaults import DEFAULT_GUILD_CLASS_COLORS
from module_guild.service.class_color_service import ClassColorService


def make_current_user(user_id=101):
    return SimpleNamespace(user=SimpleNamespace(user_id=user_id))


def test_class_color_default_uses_configured_palette():
    result = ClassColorService._resolve_color('九灵', {})

    assert result == {
        'class_name': '九灵',
        'bg_color': '#ff0000',
        'text_color': '#ffffff',
    }


def test_class_color_default_palette_matches_designed_config():
    assert DEFAULT_GUILD_CLASS_COLORS == [
        {'class_name': '九灵', 'bg_color': '#ff0000', 'text_color': '#ffffff'},
        {'class_name': '沧澜', 'bg_color': '#002fff', 'text_color': '#000000'},
        {'class_name': '潮光', 'bg_color': '#0073ff', 'text_color': '#000000'},
        {'class_name': '玄机', 'bg_color': '#ddff00', 'text_color': '#000000'},
        {'class_name': '碎梦', 'bg_color': '#00ffe5', 'text_color': '#000000'},
        {'class_name': '神相', 'bg_color': '#002fff', 'text_color': '#000000'},
        {'class_name': '素问', 'bg_color': '#ea00ff', 'text_color': '#000000'},
        {'class_name': '血河', 'bg_color': '#ff0000', 'text_color': '#000000'},
        {'class_name': '铁衣', 'bg_color': '#ff8c00', 'text_color': '#000000'},
        {'class_name': '鸿音', 'bg_color': '#ff7b00', 'text_color': '#000000'},
        {'class_name': '龙吟', 'bg_color': '#00f846', 'text_color': '#000000'},
        {'class_name': '刺客', 'bg_color': '#FFFFFF', 'text_color': '#000000'},
    ]


def test_class_color_saved_value_overrides_default():
    saved_map = {
        '九灵': SimpleNamespace(bg_color='#123456', text_color='#abcdef')
    }

    result = ClassColorService._resolve_color('九灵', saved_map)

    assert result == {
        'class_name': '九灵',
        'bg_color': '#123456',
        'text_color': '#abcdef',
    }


def test_class_color_legacy_empty_saved_value_uses_new_default():
    saved_map = {
        '九灵': SimpleNamespace(bg_color='#FFFFFF', text_color='#000000')
    }

    result = ClassColorService._resolve_color('九灵', saved_map)

    assert result == {
        'class_name': '九灵',
        'bg_color': '#ff0000',
        'text_color': '#ffffff',
    }


@pytest.mark.asyncio
async def test_class_color_list_fills_enabled_professions_with_defaults(monkeypatch):
    async def fake_query_by_user(db, user_id):
        assert user_id == 101
        return []

    async def fake_get_enabled_profession_list(db):
        return [
            SimpleNamespace(profession_name='九灵'),
            SimpleNamespace(profession_name='铁衣'),
            SimpleNamespace(profession_name='自定义'),
        ]

    monkeypatch.setattr(
        'module_guild.service.class_color_service.ClassColorDao.query_by_user',
        fake_query_by_user,
    )
    monkeypatch.setattr(
        'module_guild.service.class_color_service.ProfessionDao.get_enabled_profession_list',
        fake_get_enabled_profession_list,
    )

    result = await ClassColorService.get_colors_service(None, make_current_user())

    assert result == [
        {'class_name': '九灵', 'bg_color': '#ff0000', 'text_color': '#ffffff'},
        {'class_name': '铁衣', 'bg_color': '#ff8c00', 'text_color': '#000000'},
        {'class_name': '自定义', 'bg_color': '#FFFFFF', 'text_color': '#000000'},
    ]
