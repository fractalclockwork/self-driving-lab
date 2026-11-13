"""Layered instrument status snapshot for display (attach vs IOP).

Sibling to HIL bring-up: read-mostly rollup for CRT / dashboards. Does not
energize lamps or move axes. Gantry mains is operator-noted until PDUs exist.
"""

from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

from sdl.hil.bringup import (
    DEFAULT_LS55_GLOBS,
    DEFAULT_MARLIN_GLOBS,
    DEFAULT_VIDEO_GLOBS,
    _ssh_first_glob,
    _ssh_prefix,
    check_ls55,
    check_marlin,
    resolve_ls55_port,
    resolve_marlin_port,
    resolve_video_device,
)

DEFAULT_GATEWAY = "pi@cede-pi.local"
DEFAULT_GANTRY_NOTE = "gantry mains off (operator)"


@dataclass
class InstrumentStatus:
    attach: bool
    iop: Optional[bool]
    label: str
    detail: str


@dataclass
class GatewayStatus:
    ok: bool
    host: str
    detail: str = ""


@dataclass
class LabStatus:
    ts: str
    gateway: GatewayStatus
    instruments: dict[str, InstrumentStatus] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "gateway": asdict(self.gateway),
            "instruments": {k: asdict(v) for k, v in self.instruments.items()},
            "notes": list(self.notes),
        }


def label_ls55(*, attach: bool, iop: Optional[bool]) -> str:
    if not attach:
        return "MISSING"
    if iop is True:
        return "OK"
    return "ADAPTER"


def label_marlin(*, attach: bool, iop: Optional[bool]) -> str:
    if not attach:
        return "MISSING"
    if iop is True:
        return "CTRL OK"
    return "CTRL FAIL"


def label_camera(*, attach: bool, iop: Optional[bool] = None) -> str:
    if not attach:
        return "MISSING"
    if iop is True:
        return "OK"
    if iop is False:
        return "CAPTURE FAIL"
    return "ATTACH"


def check_gateway(host: str) -> GatewayStatus:
    proc = subprocess.run(
        [*_ssh_prefix(host), "true"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if proc.returncode == 0:
        return GatewayStatus(ok=True, host=host, detail="ssh ok")
    err = (proc.stderr or proc.stdout or "").strip() or f"exit {proc.returncode}"
    return GatewayStatus(ok=False, host=host, detail=err[:200])


def _resolve_port(
    *,
    explicit: Optional[str],
    ssh_gateway: Optional[str],
    local_resolve,
    globs: Sequence[str],
) -> Optional[str]:
    if explicit or not ssh_gateway:
        return local_resolve(explicit)
    return _ssh_first_glob(ssh_gateway, globs)


def collect_lab_status(
    *,
    ssh_gateway: Optional[str] = None,
    ls55_port: Optional[str] = None,
    marlin_port: Optional[str] = None,
    video_device: Optional[str] = None,
    spectrometer_lab_root: Optional[Path] = None,
    marlin_baud: int = 250000,
    probe_camera_capture: bool = False,
    notes: Optional[Sequence[str]] = None,
    skip: Optional[Sequence[str]] = None,
    fixture: bool = False,
) -> LabStatus:
    """Probe gateway + cohort attach/IOP and return a display-oriented snapshot."""
    skip_set = {s.lower() for s in (skip or ())}
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    note_list = list(notes) if notes is not None else []

    if fixture:
        return LabStatus(
            ts=ts,
            gateway=GatewayStatus(ok=True, host=ssh_gateway or "fixture", detail="fixture"),
            instruments={
                "ls55": InstrumentStatus(True, False, "ADAPTER", "fixture: adapter present"),
                "marlin": InstrumentStatus(True, True, "CTRL OK", "fixture: M115 ok"),
                "camera": InstrumentStatus(True, None, "ATTACH", "fixture: by-id present"),
            },
            notes=note_list,
        )

    if ssh_gateway:
        gateway = check_gateway(ssh_gateway)
    else:
        gateway = GatewayStatus(ok=True, host="local", detail="no --ssh-gateway")

    instruments: dict[str, InstrumentStatus] = {}

    if "ls55" not in skip_set:
        port = _resolve_port(
            explicit=ls55_port,
            ssh_gateway=ssh_gateway if gateway.ok else None,
            local_resolve=resolve_ls55_port,
            globs=DEFAULT_LS55_GLOBS,
        )
        attach = bool(port)
        iop: Optional[bool] = None
        detail = "port not found"
        if attach and (not ssh_gateway or gateway.ok):
            result = check_ls55(
                port,
                ssh_gateway=ssh_gateway,
                spectrometer_lab_root=spectrometer_lab_root,
            )
            iop = result.ok
            detail = result.detail
        elif attach and ssh_gateway and not gateway.ok:
            detail = f"{port}: gateway unreachable"
        instruments["ls55"] = InstrumentStatus(
            attach=attach,
            iop=iop if attach else None,
            label=label_ls55(attach=attach, iop=iop),
            detail=detail,
        )

    if "marlin" not in skip_set:
        port = _resolve_port(
            explicit=marlin_port,
            ssh_gateway=ssh_gateway if gateway.ok else None,
            local_resolve=resolve_marlin_port,
            globs=DEFAULT_MARLIN_GLOBS,
        )
        attach = bool(port)
        iop = None
        detail = "port not found"
        if attach and (not ssh_gateway or gateway.ok):
            result = check_marlin(port, ssh_gateway=ssh_gateway, baud=marlin_baud)
            iop = result.ok
            detail = result.detail
        elif attach and ssh_gateway and not gateway.ok:
            detail = f"{port}: gateway unreachable"
        instruments["marlin"] = InstrumentStatus(
            attach=attach,
            iop=iop if attach else None,
            label=label_marlin(attach=attach, iop=iop),
            detail=detail,
        )

    if "camera" not in skip_set:
        device = _resolve_port(
            explicit=video_device,
            ssh_gateway=ssh_gateway if gateway.ok else None,
            local_resolve=resolve_video_device,
            globs=DEFAULT_VIDEO_GLOBS,
        )
        attach = bool(device)
        iop = None
        detail = device or "device not found"
        if attach and probe_camera_capture and (not ssh_gateway or gateway.ok):
            from sdl.hil.bringup import check_camera, default_camera_out

            result = check_camera(
                device, out=default_camera_out(), ssh_gateway=ssh_gateway
            )
            iop = result.ok
            detail = result.detail
        elif not attach:
            detail = "device not found"
        instruments["camera"] = InstrumentStatus(
            attach=attach,
            iop=iop,
            label=label_camera(attach=attach, iop=iop),
            detail=detail,
        )

    return LabStatus(
        ts=ts,
        gateway=gateway,
        instruments=instruments,
        notes=note_list,
    )


def format_status_lines(status: LabStatus) -> list[str]:
    """Human-readable lines suitable for VTTY TEXT or CLI."""
    lines: list[str] = []
    gw = status.gateway
    gw_label = "OK" if gw.ok else "DOWN"
    host_short = gw.host.split("@")[-1] if gw.host else ""
    lines.append(f"GATEWAY  {gw_label:<8} {host_short}".rstrip())

    display_keys = (("ls55", "LS55"), ("marlin", "MARLIN"), ("camera", "C310"))
    for name, key in display_keys:
        inst = status.instruments.get(name)
        if inst is None:
            continue
        extra = ""
        if name == "marlin" and any("gantry" in n.lower() for n in status.notes):
            extra = " gantry mains off"
        elif name == "ls55" and inst.label == "ADAPTER":
            extra = " no reply"
        lines.append(f"{key:<8} {inst.label:<8}{extra}".rstrip())

    for note in status.notes:
        if "gantry" in note.lower():
            continue  # already folded into MARLIN line
        lines.append(f"NOTE     {note}")
    return lines
