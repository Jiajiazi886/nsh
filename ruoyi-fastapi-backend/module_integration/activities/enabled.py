import os
from module_integration.contract import ApiProblem


def activities_enabled():
    return os.environ.get('NSH_ACTIVITIES_ENABLED', 'false').lower() == 'true'


async def require_activities_enabled():
    if not activities_enabled():
        raise ApiProblem(503, 'CAPABILITY_DISABLED', '约战信息尚未启用，请管理员先在独立测试库完成手动迁移和配置')
