"""Unit tests for Stage-0 instrument HIL bring-up helpers."""

from __future__ import annotations

from pathlib import Path

from sdl.hil.bringup import (
    default_camera_out,
    extract_json_object,
    first_glob_match,
    ls55_identity_detail,
    ls55_identity_ok,
    marlin_reply_ok,
    resolve_ls55_port,
    resolve_marlin_port,
    resolve_video_device,
    run_hil_bringup,
)


def test_marlin_reply_ok_firmware_name():
    assert marlin_reply_ok("FIRMWARE_NAME:Marlin 2.1.2\nok\n")
    assert marlin_reply_ok("echo:Marlin bugfix ...\n")
    assert not marlin_reply_ok("ok\n")
    assert not marlin_reply_ok("")


def test_resolve_marlin_port_explicit_and_env(tmp_path: Path, monkeypatch):
    port = tmp_path / "ttyACM1"
    port.write_text("")
    assert resolve_marlin_port(str(port)) == str(port)
    monkeypatch.setenv("MARLIN_PORT", str(port))
    assert resolve_marlin_port(None) == str(port)


def test_resolve_ls55_port_env(monkeypatch, tmp_path: Path):
    port = tmp_path / "ttyUSB0"
    port.write_text("")
    monkeypatch.setenv("LS55_PORT", str(port))
    assert resolve_ls55_port(None) == str(port)


def test_resolve_video_device_env(monkeypatch, tmp_path: Path):
    dev = tmp_path / "video0"
    dev.write_text("")
    monkeypatch.setenv("VIDEO_DEVICE", str(dev))
    assert resolve_video_device(None) == str(dev)


def test_first_glob_match(tmp_path: Path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.write_text("")
    b.write_text("")
    assert first_glob_match([str(tmp_path / "missing*"), str(tmp_path / "*")]) in {
        str(a),
        str(b),
    }
    assert first_glob_match([str(tmp_path / "nope*")]) is None


def test_extract_json_object_and_ls55_identity():
    sample = {
        "ok": True,
        "status": {"model": "55", "revision": "F1"},
        "es_position": 1,
        "errors": [],
    }
    raw = json_dumps_with_noise(sample)
    parsed = extract_json_object(raw)
    assert ls55_identity_ok(parsed)
    detail = ls55_identity_detail("/dev/ttyUSB0", parsed)
    assert "firmware=55.F1" in detail
    assert "es_position=1" in detail

    assert not ls55_identity_ok({"ok": False, "errors": ["timeout"]})


def json_dumps_with_noise(obj: dict) -> str:
    import json

    return json.dumps(obj, indent=2) + "\nraw_log=/tmp/x.log\n"


def test_default_camera_out_under_runs(tmp_path: Path):
    out = default_camera_out(tmp_path)
    assert out.parent.parent == tmp_path / "runs"
    assert out.parent.name.startswith("hil_")
    assert out.name == "c310.jpg"


def test_fixture_mode_passes():
    report = run_hil_bringup(fixture=True)
    assert report.ok
    assert [r.name for r in report.results] == ["ls55", "marlin", "camera"]
    assert all(r.ok and not r.skipped for r in report.results)


def test_fixture_mode_skip():
    report = run_hil_bringup(fixture=True, skip=["marlin"])
    assert report.ok
    by_name = {r.name: r for r in report.results}
    assert by_name["marlin"].skipped
    assert by_name["ls55"].ok and not by_name["ls55"].skipped
