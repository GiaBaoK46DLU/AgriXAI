"""Ngăn cảnh báo hash giả khi Git đổi xuống dòng giữa Linux và Windows."""
import hashlib

from src.evaluation.verify_xai_comparison import text_hash_matches


def test_text_hash_accepts_lf_and_crlf(tmp_path):
    source = tmp_path / "source.py"
    lf = 'print("lá cà chua")\nvalue = 1\n'.encode("utf-8")
    crlf = lf.replace(b"\n", b"\r\n")
    for actual in (lf, crlf):
        source.write_bytes(actual)
        for recorded in (lf, crlf):
            assert text_hash_matches(source, hashlib.sha256(recorded).hexdigest())


def test_text_hash_rejects_content_changes(tmp_path):
    source = tmp_path / "source.py"
    expected = hashlib.sha256(b"value = 1\r\n").hexdigest()
    source.write_bytes(b"value = 2\n")
    assert not text_hash_matches(source, expected)
    source.write_bytes(b"value  = 1\n")
    assert not text_hash_matches(source, expected)
