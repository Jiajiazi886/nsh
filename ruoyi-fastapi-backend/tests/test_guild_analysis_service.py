from types import SimpleNamespace

from module_guild.service.analysis_service import AnalysisService


def test_schedule_battle_analysis_matches_records_by_player_name():
    schedule = {
        'schedule_id': 10,
        'schedule_name': '周六约战排表',
        'create_time': '2026-06-01 20:00:00',
        'teams': [
            {
                'team_id': 1,
                'team_name': '一团',
                'order_num': 1,
                'squads': [
                    {
                        'squad_id': 11,
                        'squad_name': '第一小队',
                        'members': [
                            {'member_id': 101, 'player_name': '张三', 'player_class': '碎梦'},
                            {'member_id': 102, 'player_name': '李四', 'player_class': '素问'},
                        ],
                    }
                ],
            }
        ],
    }
    battle = SimpleNamespace(
        battle_id=20,
        battle_name='20260601_帮会A_帮会B.csv',
        battle_date='20260601',
        battle_type='约战',
        battle_result='胜利',
        my_guild_name='帮会A',
        opponent_name='帮会B',
    )
    records = [
        SimpleNamespace(
            record_id=1,
            guild_name='帮会A',
            player_name='张三',
            player_class='碎梦',
            kills=8,
            qingquan_kills=1,
            assists=2,
            resources=300,
            dmg_to_players=1000,
            armor_break_players=200,
            dmg_to_buildings=50,
            armor_break_buildings=20,
            healing=0,
            dmg_taken=500,
            deaths=1,
            revives=0,
            burn_bones=0,
        ),
        SimpleNamespace(
            record_id=2,
            guild_name='帮会A',
            player_name='王五',
            player_class='铁衣',
            kills=3,
            qingquan_kills=0,
            assists=4,
            resources=100,
            dmg_to_players=800,
            armor_break_players=100,
            dmg_to_buildings=0,
            armor_break_buildings=0,
            healing=0,
            dmg_taken=1200,
            deaths=2,
            revives=0,
            burn_bones=1,
        ),
        SimpleNamespace(
            record_id=3,
            guild_name='帮会B',
            player_name='对手甲',
            player_class='血河',
            kills=12,
            qingquan_kills=0,
            assists=0,
            resources=0,
            dmg_to_players=0,
            armor_break_players=0,
            dmg_to_buildings=0,
            armor_break_buildings=0,
            healing=0,
            dmg_taken=0,
            deaths=0,
            revives=0,
            burn_bones=0,
        ),
    ]

    result = AnalysisService.build_schedule_battle_analysis(schedule, battle, records)

    assert result['summary']['scheduled_count'] == 2
    assert result['summary']['matched_count'] == 1
    assert result['summary']['unscheduled_record_count'] == 1
    assert result['summary']['unmatched_schedule_count'] == 1
    assert result['summary']['kills'] == 8
    assert result['summary']['qingquan_kills'] == 1
    assert result['teams'][0]['matched_count'] == 1
    assert result['teams'][0]['squads'][0]['members'][0]['matched'] is True
    assert result['teams'][0]['squads'][0]['members'][1]['matched'] is False
    assert result['unmatched_schedule_members'][0]['player_name'] == '李四'
    assert result['unscheduled_records'][0]['player_name'] == '王五'


def test_schedule_battle_analysis_uses_all_records_when_my_guild_is_missing():
    schedule = {
        'schedule_id': 10,
        'schedule_name': '临时排表',
        'teams': [
            {
                'team_id': 1,
                'team_name': '一团',
                'squads': [
                    {
                        'squad_id': 11,
                        'squad_name': '第一小队',
                        'members': [{'member_id': 101, 'player_name': '张三', 'player_class': '碎梦'}],
                    }
                ],
            }
        ],
    }
    battle = SimpleNamespace(
        battle_id=20,
        battle_name='battle.csv',
        battle_date='20260601',
        battle_type='约战',
        battle_result='',
        my_guild_name='',
        opponent_name='',
    )
    records = [
        SimpleNamespace(
            record_id=1,
            guild_name='任意帮会',
            player_name='张三',
            player_class='碎梦',
            kills=1,
            qingquan_kills=0,
            assists=0,
            resources=0,
            dmg_to_players=0,
            armor_break_players=0,
            dmg_to_buildings=0,
            armor_break_buildings=0,
            healing=0,
            dmg_taken=0,
            deaths=0,
            revives=0,
            burn_bones=0,
        )
    ]

    result = AnalysisService.build_schedule_battle_analysis(schedule, battle, records)

    assert result['summary']['matched_count'] == 1
    assert result['summary']['record_scope_guild_name'] == ''
