from fastapi.encoders import jsonable_encoder

from module_admin.entity.do.notice_do import NoticeContentType, decode_notice_content
from module_admin.entity.vo.notice_vo import NoticeModel


def test_notice_content_decodes_normal_utf8_blob() -> None:
    assert decode_notice_content('<p>公告</p>'.encode()) == '<p>公告</p>'


def test_notice_content_repairs_surrogatepass_migration_bytes() -> None:
    migrated = bytes.fromhex('3C703EEDB3A6EDB2B5EDB28BEDB3A8EDB2AFEDB2953C2F703E')

    assert decode_notice_content(migrated) == '<p>测试</p>'


def test_notice_content_repairs_mixed_legacy_text() -> None:
    migrated = bytes.fromhex('E7BC96E8BE91E5AD97E6AEB5EDB3A6EDB2B5EDB28BEDB3A8EDB2AFEDB295')

    assert decode_notice_content(migrated) == '编辑字段测试'


def test_notice_content_keeps_irrecoverable_data_json_serializable() -> None:
    text = decode_notice_content(b'prefix-\xff-suffix')

    assert text == 'prefix-�-suffix'
    assert jsonable_encoder(NoticeModel(noticeContent=text))['noticeContent'] == text


def test_notice_content_type_encodes_new_text_as_utf8() -> None:
    field_type = NoticeContentType()

    assert field_type.process_bind_param('测试', None) == '测试'.encode()
