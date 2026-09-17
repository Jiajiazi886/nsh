import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]

def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name+'.py'))
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    return tool

@pytest.mark.parametrize('target',['ruoyi','nsh_activity_dev_20260913','',None])
def test_database_audit_refuses_other_databases(target):
    with pytest.raises(ValueError):
        load_tool('audit_activity_dev_database').audit(target)

def test_index_migration_reuses_existing_covering_indexes():
    tool=load_tool('optimize_player_center_dev')
    assert tool.has_prefix({'existing':['member_user_id','is_active','member_id','guild_id']},['member_user_id','is_active','member_id'])
    assert not tool.has_prefix({'unrelated':['user_id','member_user_id']},['member_user_id','is_active','member_id'])
    assert not tool.has_prefix({'partial':['member_user_id']},['member_user_id','is_active','member_id'])

@pytest.mark.parametrize('target',['ruoyi','nsh_activity_dev_20260913','',None])
def test_index_migration_refuses_other_databases(target):
    with pytest.raises(ValueError):
        load_tool('optimize_player_center_dev').migrate(target)

def test_unused_guild_table_cleanup_accepts_only_the_fixed_empty_allowlist():
    tool=load_tool('cleanup_obsolete_activity_dev_tables')
    assert tool.removable_tables({'guild_info':0,'guild_review':0}) == ['guild_info','guild_review']
    assert tool.removable_tables({'guild_info':None,'guild_review':None}) == []
    with pytest.raises(ValueError,match='not empty'):
        tool.removable_tables({'guild_info':1,'guild_review':0})
    with pytest.raises(ValueError,match='Unexpected table'):
        tool.removable_tables({'guild_info':0,'guild_review':0,'sys_user':0})

@pytest.mark.parametrize('target',['ruoyi','nsh_activity_dev_20260913','',None])
def test_unused_guild_table_cleanup_refuses_other_databases(target):
    with pytest.raises(ValueError):
        load_tool('cleanup_obsolete_activity_dev_tables').migrate(target)
