import pytest

from module_guild.entity.vo.battle_registration_vo import PublicBattleJoinApplicationModel
from module_guild.service.battle_registration_service import BattleRegistrationService


@pytest.mark.parametrize(
    'fields, expected',
    [
        ({}, []),
        ({'applicant_name': None, 'applicant_contact': None, 'remark': None}, []),
        ({'applicant_name': '  ', 'applicant_contact': '\t', 'remark': '\n'}, []),
        (
            {'applicant_name': ' 小张 ', 'applicant_contact': ' wx-001 ', 'remark': ' 申请加入 '},
            ['申请人：小张', '联系方式：wx-001', '申请加入'],
        ),
    ],
)
def test_join_remark_is_non_recursive_and_ignores_blank_fields(fields, expected):
    data = PublicBattleJoinApplicationModel(player_name='玩家甲', **fields)
    assert BattleRegistrationService._build_join_remark(data) == expected
