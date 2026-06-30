ELEMENT_KEYS = ('metal', 'wood', 'water', 'fire', 'earth')

ELEMENT_LABEL_TO_KEY = {
    '金': 'metal',
    '木': 'wood',
    '水': 'water',
    '火': 'fire',
    '土': 'earth',
}

ELEMENT_KEY_TO_LABEL = {value: key for key, value in ELEMENT_LABEL_TO_KEY.items()}

_RAW_INTERNAL_POWER_PRESETS = [
    ('破釜', '金'),
    ('贯山月', '金'),
    ('惊羽', '金'),
    ('击衰', '金'),
    ('锻寒芒', '金'),
    ('移星障', '木'),
    ('凌穹', '木'),
    ('沧浪行', '木'),
    ('裁锋', '木'),
    ('破重云', '木'),
    ('珠明', '水'),
    ('望惊川', '水'),
    ('沉浪', '水'),
    ('鲸落', '水'),
    ('噬汐', '水'),
    ('楚狂歌', '火'),
    ('斩精', '火'),
    ('众妙', '火'),
    ('燎原', '火'),
    ('焚刃', '火'),
    ('征袍', '土'),
    ('御千嶂', '土'),
    ('固垒', '土'),
    ('覆沙阙', '土'),
    ('纳百观', '土'),
    ('五韵谣', '金木水火土'),
    ('稀有-日月两仪', '火'),
    ('稀有-日月两仪', '土'),
    ('稀有-不动明王', '木'),
    ('稀有-不动明王', '水'),
    ('稀有-绝电惊沙', '金'),
    ('稀有-绝电惊沙', '木'),
    ('稀有-承影锋烁', '金'),
    ('稀有-承影锋烁', '火'),
    ('稀有-灼星贯日', '木'),
    ('稀有-灼星贯日', '火'),
]


def build_elements(element_text: str) -> dict[str, int]:
    elements = {key: 0 for key in ELEMENT_KEYS}
    if element_text == '金木水火土':
        return {key: 1 for key in ELEMENT_KEYS}
    element_key = ELEMENT_LABEL_TO_KEY[element_text]
    elements[element_key] = 4
    return elements


def build_element_key(element_text: str) -> str:
    if element_text == '金木水火土':
        return 'mixed'
    return ELEMENT_LABEL_TO_KEY[element_text]


def build_image_url(index: int, name: str, element_text: str) -> str:
    return f'/neigong/{index:02d}_{name}_{element_text}.png'


DEFAULT_INTERNAL_POWER_PRESETS = [
    {
        'name': name,
        'element_key': build_element_key(element_text),
        'elements': build_elements(element_text),
        'bonus_percent': 0,
        'lingyun_bonus_percent': 0,
        'bonus_type': '',
        'bonus_desc': '',
        'image_url': build_image_url(index, name, element_text),
        'entries': [],
        'status': '0',
        'remark': '内置预设内功',
    }
    for index, (name, element_text) in enumerate(_RAW_INTERNAL_POWER_PRESETS, start=1)
]
