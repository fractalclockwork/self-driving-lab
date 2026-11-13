"""Instrument HIL bring-up: LS 55 RS-232 identity, Marlin M115, C310 capture."""

from __future__ import annotations

import glob
import json
import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

# CEDE Phase 7 first-cohort globs (LS 55 Prolific, Marlin Mega CDC, Logitech C310).
DEFAULT_LS55_GLOBS: tuple[str, ...] = (
    "/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller*",
)
DEFAULT_MARLIN_GLOBS: tuple[str, ...] = (
    "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0042_*",
)
DEFAULT_VIDEO_GLOBS: tuple[str, ...] = (
    "/dev/v4l/by-id/*046d*",
    "/dev/v4l/by-id/*C310*",
    "/dev/v4l/by-id/*Logitech*",
    "/dev/video0",
)
@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    skipped: bool = False


@dataclass
class HilReport:
    results: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(r.ok or r.skipped for r in self.results)

    def summary_lines(self) -> list[str]:
        lines = []
        for r in self.results:
            if r.skipped:
                status = "SKIP"
            else:
                status = "PASS" if r.ok else "FAIL"
            lines.append(f"[{status}] {r.name}: {r.detail}")
        return lines


def first_glob_match(patterns: Sequence[str]) -> Optional[str]:
    for pat in patterns:
        matches = sorted(glob.glob(pat))
        if matches:
            return matches[0]
    return None


def resolve_ls55_port(
    explicit: Optional[str] = None,
    *,
    env: Optional[dict[str, str]] = None,
) -> Optional[str]:
    env = env if env is not None else os.environ
    if explicit:
        return explicit
    if env.get("LS55_PORT"):
        return env["LS55_PORT"]
    return first_glob_match(DEFAULT_LS55_GLOBS)


def resolve_marlin_port(
    explicit: Optional[str] = None,
    *,
    env: Optional[dict[str, str]] = None,
) -> Optional[str]:
    env = env if env is not None else os.environ
    if explicit:
        return explicit
    if env.get("MARLIN_PORT"):
        return env["MARLIN_PORT"]
    return first_glob_match(DEFAULT_MARLIN_GLOBS)


def resolve_video_device(
    explicit: Optional[str] = None,
    *,
    env: Optional[dict[str, str]] = None,
) -> Optional[str]:
    env = env if env is not None else os.environ
    if explicit:
        return explicit
    if env.get("VIDEO_DEVICE"):
        return env["VIDEO_DEVICE"]
    return first_glob_match(DEFAULT_VIDEO_GLOBS)


def marlin_reply_ok(text: str) -> bool:
    lower = text.lower()
    return "firmware_name" in lower or "marlin" in lower


def _ssh_prefix(gateway: str) -> list[str]:
    return ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", gateway]


def _ssh_first_glob(gateway: str, patterns: Sequence[str]) -> Optional[str]:
    remote = (
        "python3 - <<'PY'\n"
        "import glob\n"
        f"patterns={list(patterns)!r}\n"
        "for pat in patterns:\n"
        "    m=sorted(glob.glob(pat))\n"
        "    if m:\n"
        "        print(m[0])\n"
        "        break\n"
        "PY"
    )
    proc = subprocess.run(
        [*_ssh_prefix(gateway), remote],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if proc.returncode != 0:
        return None
    path = proc.stdout.strip().splitlines()
    return path[0] if path else None


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse first JSON object from CLI stdout (ignores trailing log lines)."""
    text = text.strip()
    if not text:
        raise ValueError("empty stdout")
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("no JSON object in stdout")
    data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("JSON root is not an object")
    return data


def ls55_identity_detail(port: str, identity: dict[str, Any]) -> str:
    status = identity.get("status") or {}
    model = status.get("model")
    revision = status.get("revision")
    fw = f"{model}.{revision}" if model is not None and revision is not None else "unknown"
    es = identity.get("es_position")
    return f"{port}: identity ok firmware={fw} es_position={es}"


def ls55_identity_ok(identity: dict[str, Any]) -> bool:
    return bool(identity.get("ok"))


def _spectrometer_lab_root(explicit: Optional[Path]) -> Path:
    if explicit is not None:
        return explicit.expanduser()
    return Path(
        os.path.expanduser(os.environ.get("SPECTROMETER_LAB_ROOT", "~/src/spectrometer-lab"))
    )


def _run_ls55_identity_local(
    port: str,
    *,
    root: Path,
    timeout_s: float = 60.0,
) -> tuple[int, str, str]:
    script = root / "scripts" / "dump_instrument_identity.py"
    if not script.is_file():
        raise RuntimeError(
            f"spectrometer-lab dump script not found: {script} "
            "(set --spectrometer-lab-root or SPECTROMETER_LAB_ROOT)"
        )
    cmd = [
        "uv",
        "run",
        "--directory",
        str(root),
        "python",
        str(script),
        "--port",
        port,
        "--gate-a-pass",
        "--compartment-closed",
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _run_ls55_identity_ssh(
    gateway: str,
    port: str,
    *,
    root: Path,
    timeout_s: float = 90.0,
) -> tuple[int, str, str]:
    # Expand ~ on the remote via bash -lc; quote paths for the remote shell.
    remote_root = str(root)
    remote_cmd = (
        f"cd {shlex.quote(remote_root)} && "
        f"uv run python scripts/dump_instrument_identity.py "
        f"--port {shlex.quote(port)} --gate-a-pass --compartment-closed"
    )
    proc = subprocess.run(
        [*_ssh_prefix(gateway), "bash", "-lc", remote_cmd],
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def check_ls55(
    port: Optional[str],
    *,
    ssh_gateway: Optional[str] = None,
    spectrometer_lab_root: Optional[Path] = None,
    timeout_s: float = 60.0,
) -> CheckResult:
    if not port:
        return CheckResult(
            "ls55",
            False,
            "port not found (set LS55_PORT / --ls55-port or attach Prolific by-id)",
        )
    root = _spectrometer_lab_root(spectrometer_lab_root)
    try:
        if ssh_gateway:
            code, stdout, stderr = _run_ls55_identity_ssh(
                ssh_gateway, port, root=root, timeout_s=max(timeout_s, 90.0)
            )
        else:
            code, stdout, stderr = _run_ls55_identity_local(
                port, root=root, timeout_s=timeout_s
            )
        identity = extract_json_object(stdout)
    except Exception as exc:  # noqa: BLE001
        return CheckResult("ls55", False, f"{port}: {exc}")

    if code != 0 or not ls55_identity_ok(identity):
        err = (stderr or "").strip() or f"exit {code}"
        errors = identity.get("errors") if isinstance(identity, dict) else None
        return CheckResult(
            "ls55",
            False,
            f"{port}: identity FAIL ({err}); errors={errors!r}",
        )
    return CheckResult("ls55", True, ls55_identity_detail(port, identity))


def _read_marlin_local(port: str, *, baud: int = 250000, timeout_s: float = 3.0) -> str:
    try:
        import serial  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "pyserial required for Marlin probe; install with: uv sync --extra hil"
        ) from exc

    ser = serial.Serial(port, baudrate=baud, timeout=timeout_s)
    try:
        ser.reset_input_buffer()
        ser.write(b"M115\n")
        ser.flush()
        chunks: list[bytes] = []
        # Marlin often ACKs with multiple lines; read until quiet timeout.
        while True:
            line = ser.readline()
            if not line:
                break
            chunks.append(line)
            if len(chunks) > 40:
                break
        return b"".join(chunks).decode("utf-8", errors="replace")
    finally:
        ser.close()


def _read_marlin_ssh(gateway: str, port: str, *, baud: int = 250000) -> str:
    # Prefer pyserial on the remote via python3 -c to avoid local USB.
    remote = (
        "python3 - <<'PY'\n"
        "import serial\n"
        f"ser=serial.Serial({port!r}, baudrate={baud}, timeout=3)\n"
        "ser.reset_input_buffer()\n"
        "ser.write(b'M115\\n')\n"
        "ser.flush()\n"
        "chunks=[]\n"
        "while True:\n"
        "    line=ser.readline()\n"
        "    if not line: break\n"
        "    chunks.append(line)\n"
        "    if len(chunks)>40: break\n"
        "ser.close()\n"
        "print(b''.join(chunks).decode('utf-8','replace'))\n"
        "PY"
    )
    proc = subprocess.run(
        [*_ssh_prefix(gateway), remote],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"ssh exit {proc.returncode}")
    return proc.stdout


def check_marlin(
    port: Optional[str],
    *,
    ssh_gateway: Optional[str] = None,
    baud: int = 250000,
) -> CheckResult:
    if not port:
        return CheckResult(
            "marlin",
            False,
            "port not found (set MARLIN_PORT / --marlin-port or attach Mega by-id)",
        )
    try:
        if ssh_gateway:
            reply = _read_marlin_ssh(ssh_gateway, port, baud=baud)
        else:
            reply = _read_marlin_local(port, baud=baud)
    except Exception as exc:  # noqa: BLE001
        return CheckResult("marlin", False, f"{port}: {exc}")

    compact = " ".join(reply.split())
    if not marlin_reply_ok(reply):
        return CheckResult(
            "marlin",
            False,
            f"{port}: unexpected M115 reply: {compact[:160]!r}",
        )
    return CheckResult("marlin", True, f"{port}: M115 ok ({compact[:120]})")


def _capture_local(device: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("fswebcam"):
        cmd = [
            "fswebcam",
            "-d",
            device,
            "-r",
            "640x480",
            "--jpeg",
            "85",
            "-D",
            "1",
            str(out),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
        if proc.returncode == 0 and out.is_file() and out.stat().st_size > 0:
            return
        err = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"fswebcam failed: {err}")

    if shutil.which("v4l2-ctl"):
        # Raw dump then accept non-empty file as evidence the device streamed.
        raw = out.with_suffix(".raw")
        cmd = [
            "v4l2-ctl",
            f"--device={device}",
            "--stream-mmap",
            "--stream-count=1",
            f"--stream-to={raw}",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
        if proc.returncode == 0 and raw.is_file() and raw.stat().st_size > 0:
            raw.replace(out)
            return
        err = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"v4l2-ctl failed: {err}")

    raise RuntimeError("need fswebcam or v4l2-ctl on PATH for camera capture")


def _capture_ssh(gateway: str, device: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    remote_out = f"/tmp/sdl_hil_cam_{os.getpid()}.jpg"
    remote = (
        f"if command -v fswebcam >/dev/null; then "
        f"fswebcam -d {device} -r 640x480 --jpeg 85 -D 1 {remote_out}; "
        f"elif command -v v4l2-ctl >/dev/null; then "
        f"v4l2-ctl --device={device} --stream-mmap --stream-count=1 "
        f"--stream-to={remote_out}; "
        f"else echo 'need fswebcam or v4l2-ctl' >&2; exit 1; fi"
    )
    proc = subprocess.run(
        [*_ssh_prefix(gateway), remote],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"ssh capture exit {proc.returncode}")
    scp = subprocess.run(
        ["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", f"{gateway}:{remote_out}", str(out)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if scp.returncode != 0 or not out.is_file() or out.stat().st_size == 0:
        raise RuntimeError(scp.stderr.strip() or "scp of capture failed")
    subprocess.run(
        [*_ssh_prefix(gateway), f"rm -f {remote_out}"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def default_camera_out(repo_root: Optional[Path] = None) -> Path:
    """Durable Dev-Host path under runs/hil_<utc>/ (gateway must not keep frames)."""
    root = repo_root or Path.cwd()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return root / "runs" / f"hil_{stamp}" / "c310.jpg"


def check_camera(
    device: Optional[str],
    *,
    out: Path,
    ssh_gateway: Optional[str] = None,
) -> CheckResult:
    if not device:
        return CheckResult(
            "camera",
            False,
            "device not found (set VIDEO_DEVICE / --video-device or attach C310)",
        )
    try:
        if ssh_gateway:
            _capture_ssh(ssh_gateway, device, out)
        else:
            _capture_local(device, out)
    except Exception as exc:  # noqa: BLE001
        return CheckResult("camera", False, f"{device}: {exc}")
    size = out.stat().st_size
    return CheckResult("camera", True, f"{device}: captured {out} ({size} bytes)")


def run_hil_bringup(
    *,
    ls55_port: Optional[str] = None,
    spectrometer_lab_root: Optional[Path] = None,
    marlin_port: Optional[str] = None,
    video_device: Optional[str] = None,
    camera_out: Optional[Path] = None,
    ssh_gateway: Optional[str] = None,
    skip: Optional[Sequence[str]] = None,
    fixture: bool = False,
    marlin_baud: int = 250000,
) -> HilReport:
    skip_set = {s.lower() for s in (skip or ())}
    report = HilReport()

    if fixture:
        for name in ("ls55", "marlin", "camera"):
            if name in skip_set:
                report.results.append(CheckResult(name, True, "skipped", skipped=True))
            else:
                report.results.append(CheckResult(name, True, "fixture pass"))
        return report

    if "ls55" in skip_set:
        report.results.append(CheckResult("ls55", True, "skipped", skipped=True))
    else:
        if ls55_port or not ssh_gateway:
            port = resolve_ls55_port(ls55_port)
        else:
            port = _ssh_first_glob(ssh_gateway, DEFAULT_LS55_GLOBS)
        report.results.append(
            check_ls55(
                port,
                ssh_gateway=ssh_gateway,
                spectrometer_lab_root=spectrometer_lab_root,
            )
        )

    if "marlin" in skip_set:
        report.results.append(CheckResult("marlin", True, "skipped", skipped=True))
    else:
        if marlin_port or not ssh_gateway:
            port = resolve_marlin_port(marlin_port)
        else:
            port = _ssh_first_glob(ssh_gateway, DEFAULT_MARLIN_GLOBS)
        report.results.append(
            check_marlin(port, ssh_gateway=ssh_gateway, baud=marlin_baud)
        )

    if "camera" in skip_set:
        report.results.append(CheckResult("camera", True, "skipped", skipped=True))
    else:
        if video_device or not ssh_gateway:
            device = resolve_video_device(video_device)
        else:
            device = _ssh_first_glob(ssh_gateway, DEFAULT_VIDEO_GLOBS)
        out = camera_out or default_camera_out()
        report.results.append(
            check_camera(device, out=out, ssh_gateway=ssh_gateway)
        )

    return report
