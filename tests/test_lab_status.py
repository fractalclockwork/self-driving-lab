"""Unit tests for layered lab status labels and fixture snapshot."""

from __future__ import annotations

from sdl.hil.status import (
    DEFAULT_GANTRY_NOTE,
    collect_lab_status,
    format_status_lines,
    label_camera,
    label_ls55,
    label_marlin,
)


def test_label_ls55_attach_iop_matrix():
    assert label_ls55(attach=False, iop=None) == "MISSING"
    assert label_ls55(attach=True, iop=True) == "OK"
    assert label_ls55(attach=True, iop=False) == "ADAPTER"
    assert label_ls55(attach=True, iop=None) == "ADAPTER"


def test_label_marlin_attach_iop_matrix():
    assert label_marlin(attach=False, iop=None) == "MISSING"
    assert label_marlin(attach=True, iop=True) == "CTRL OK"
    assert label_marlin(attach=True, iop=False) == "CTRL FAIL"


def test_label_camera_attach_only_default():
    assert label_camera(attach=False) == "MISSING"
    assert label_camera(attach=True) == "ATTACH"
    assert label_camera(attach=True, iop=True) == "OK"
    assert label_camera(attach=True, iop=False) == "CAPTURE FAIL"


def test_fixture_snapshot_no_default_gantry_note():
    status = collect_lab_status(fixture=True, ssh_gateway="pi@cede-pi.local")
    assert status.gateway.ok
    assert status.instruments["ls55"].label == "ADAPTER"
    assert status.instruments["ls55"].attach is True
    assert status.instruments["ls55"].iop is False
    assert status.instruments["marlin"].label == "CTRL OK"
    assert status.instruments["camera"].label == "ATTACH"
    assert status.notes == []

    lines = format_status_lines(status)
    joined = "\n".join(lines)
    assert "GATEWAY" in joined and "OK" in joined
    assert "ADAPTER" in joined and "no reply" in joined
    assert "CTRL OK" in joined
    assert "gantry mains off" not in joined
    assert "C310" in joined and "ATTACH" in joined


def test_fixture_explicit_gantry_note():
    status = collect_lab_status(fixture=True, notes=[DEFAULT_GANTRY_NOTE])
    assert DEFAULT_GANTRY_NOTE in status.notes
    joined = "\n".join(format_status_lines(status))
    assert "gantry mains off" in joined


def test_fixture_custom_notes():
    status = collect_lab_status(fixture=True, notes=["custom note"])
    assert status.notes == ["custom note"]
    d = status.to_dict()
    assert d["instruments"]["marlin"]["label"] == "CTRL OK"
    assert "ts" in d
