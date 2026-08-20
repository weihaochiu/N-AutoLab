from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_windows_launcher_is_cmd_compatible_and_launches_qt_module() -> None:
    data = (ROOT / "run_windows.bat").read_bytes()
    assert b"\r\n" in data
    assert b"\n" not in data.replace(b"\r\n", b"")
    assert b"-m nautolab.gui" in data
    assert b"Phase 2" not in data
