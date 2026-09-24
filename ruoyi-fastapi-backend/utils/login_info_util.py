from datetime import datetime

import httpx
from async_lru import alru_cache
from fastapi import Request
from user_agents import parse

from config.env import AppConfig
from utils.client_ip_util import ClientIPUtil


@alru_cache()
async def get_ip_location(ipaddr: str) -> str:
    if ipaddr in {'127.0.0.1', '::1', 'localhost'}:
        return '内网IP'
    if not AppConfig.app_ip_location_query:
        return '未知'
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(f'https://qifu-api.baidubce.com/ip/geo/v1/district?ip={ipaddr}')
        if response.status_code == 200:
            data = response.json().get('data', {})
            province = data.get('prov') or ''
            city = data.get('city') or ''
            return '-'.join(item for item in (province, city) if item) or '未知'
    except Exception:
        pass
    return '未知'


async def build_login_info(request: Request) -> dict[str, str]:
    """生成在线会话所需信息，不写入登录审计表。"""

    ipaddr = ClientIPUtil.get_client_ip(request)
    agent = parse(request.headers.get('User-Agent') or '')
    browser = agent.browser.family or 'Unknown'
    system_os = agent.os.family or 'Unknown'
    if agent.browser.version:
        browser += f' {agent.browser.version[0]}'
    if agent.os.version:
        system_os += f' {agent.os.version[0]}'
    return {
        'ipaddr': ipaddr,
        'loginLocation': await get_ip_location(ipaddr),
        'browser': browser,
        'os': system_os,
        'loginTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
