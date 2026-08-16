from module_admin.service.ai_recognition_quota_service import AiRecognitionQuotaSnapshot


def test_quota_allocation_consumes_normal_before_vip() -> None:
    snapshot = AiRecognitionQuotaSnapshot(
        user_id=7,
        unlimited=False,
        normal_count=3,
        vip_count=4,
    )

    assert snapshot.allocate(2) == (2, 0)
    assert snapshot.allocate(5) == (3, 2)


def test_quota_allocation_falls_back_to_vip_when_normal_is_empty() -> None:
    snapshot = AiRecognitionQuotaSnapshot(
        user_id=7,
        unlimited=False,
        normal_count=0,
        vip_count=4,
    )

    assert snapshot.allocate(2) == (0, 2)
