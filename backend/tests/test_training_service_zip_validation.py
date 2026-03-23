from api.services.training_service import _is_zip_deliverable


def test_is_zip_deliverable_missing(tmp_path):
    zip_path = tmp_path / "missing.zip"
    assert _is_zip_deliverable(str(zip_path)) is False


def test_is_zip_deliverable_empty(tmp_path):
    zip_path = tmp_path / "empty.zip"
    zip_path.write_bytes(b"")
    assert _is_zip_deliverable(str(zip_path)) is False


def test_is_zip_deliverable_nonempty(tmp_path):
    zip_path = tmp_path / "nonempty.zip"
    zip_path.write_bytes(b"123")
    assert _is_zip_deliverable(str(zip_path)) is True

