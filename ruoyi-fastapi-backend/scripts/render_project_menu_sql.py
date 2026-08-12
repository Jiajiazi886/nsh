import json
import re
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = BACKEND_ROOT / 'config' / 'project_menu_baseline.json'
SQL_FILES = (
    (BACKEND_ROOT / 'sql' / 'ruoyi-fastapi.sql', 'mysql'),
    (BACKEND_ROOT / 'sql' / 'ruoyi-fastapi-pg.sql', 'postgresql'),
)


def _literal(value: Any, dialect: str) -> str:
    if value is None:
        return 'null'
    if isinstance(value, int):
        return str(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def _menu_seed(baseline: dict, dialect: str) -> str:
    timestamp = 'sysdate()' if dialect == 'mysql' else 'current_timestamp'
    rows = []
    for menu in baseline['menus']:
        values = [
            menu['menu_id'],
            menu['menu_name'],
            menu['parent_id'],
            menu['order_num'],
            menu['path'],
            menu['component'],
            menu['query'],
            menu['route_name'],
            menu['is_frame'],
            menu['is_cache'],
            menu['menu_type'],
            menu['visible'],
            menu['status'],
            menu['perms'],
            menu['icon'],
            'system',
        ]
        rendered = ', '.join(_literal(value, dialect) for value in values)
        rendered += f", {timestamp}, 'system', {timestamp}, {_literal(menu['remark'], dialect)}"
        rows.append(f'insert into sys_menu values({rendered});')
    if dialect == 'postgresql':
        rows.append(
            "select setval(pg_get_serial_sequence('sys_menu', 'menu_id'), (select max(menu_id) from sys_menu), true);"
        )
    return '\n'.join(rows)


def _role_menu_seed(baseline: dict) -> str:
    return '\n'.join(
        f'insert into sys_role_menu values ({int(role_id)}, {menu_id});'
        for role_id, menu_ids in baseline['role_menus'].items()
        for menu_id in menu_ids
    )


def _replace_seed(sql: str, start_marker: str, end_marker: str, seed: str) -> str:
    pattern = rf'({re.escape(start_marker)}\s*)(.*?)({re.escape(end_marker)})'
    replacement = rf'\1{seed}\n\n\3'
    updated, count = re.subn(pattern, replacement, sql, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f'could not replace SQL block after marker: {start_marker}')
    return updated


def main() -> None:
    baseline = json.loads(BASELINE_PATH.read_text(encoding='utf-8'))
    for path, dialect in SQL_FILES:
        sql = path.read_text(encoding='utf-8')
        sql = _replace_seed(
            sql,
            '-- 初始化-菜单信息表数据\n-- ----------------------------',
            '-- 6、用户和角色关联表  用户N-1角色',
            _menu_seed(baseline, dialect),
        )
        sql = _replace_seed(
            sql,
            '-- 初始化-角色和菜单关联表数据\n-- ----------------------------',
            '-- 8、角色和部门关联表  角色1-N部门',
            _role_menu_seed(baseline),
        )
        sql = re.sub(
            r'\n-- ----------------------------\n-- \d+、AI对话配置表.*?(?=\n-- ----------------------------\n-- \d+、|\Z)',
            '\n',
            sql,
            flags=re.DOTALL,
        )
        path.write_text(sql, encoding='utf-8', newline='\n')
        print(f'rendered {path}')


if __name__ == '__main__':
    main()
