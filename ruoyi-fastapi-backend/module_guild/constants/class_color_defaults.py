import json
from pathlib import Path

_DEFAULT_CONFIG_PATH = Path(__file__).with_suffix('.json')


def _load_default_class_colors() -> list[dict]:
    with _DEFAULT_CONFIG_PATH.open('r', encoding='utf-8') as file:
        payload = json.load(file)
    colors = payload.get('colors', [])
    return [
        {
            'class_name': str(item.get('class_name', '')),
            'bg_color': str(item.get('bg_color', '#FFFFFF')),
            'text_color': str(item.get('text_color', '#000000')),
        }
        for item in colors
        if item.get('class_name')
    ]


DEFAULT_GUILD_CLASS_COLORS = _load_default_class_colors()

DEFAULT_GUILD_CLASS_COLOR_MAP = {
    item['class_name']: item
    for item in DEFAULT_GUILD_CLASS_COLORS
}
