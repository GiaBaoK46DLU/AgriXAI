"""Hash bằng chứng phải dùng được khi chuyển Windows/Linux qua Git."""

from src.training.adapt_domain import digest


def test_line_endings_are_portable_only_for_text_artifacts(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_bytes(b'{"n": 66}\r\n')
    b.write_bytes(b'{"n": 66}\n')
    assert digest(a) == digest(b)
    a, b = tmp_path / "a.pt", tmp_path / "b.pt"
    a.write_bytes(b"checkpoint\r\n")
    b.write_bytes(b"checkpoint\n")
    assert digest(a) != digest(b)


def test_windows_inventory_paths_resolve_on_other_platforms(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    path = tmp_path / "data/leaf.png"
    path.write_bytes(b"image-bytes\r\n")
    assert digest("data\\leaf.png") == digest("data/leaf.png")
